"""
academico/services/ocr_service.py

Serviço de OCR e Extração de Horas — Extrator Híbrido.

Fase 1 — Nativa (PyMuPDF):
    Tenta extrair o texto digital embutido diretamente no PDF.
    Se o resultado tiver >= 30 caracteres válidos, retorna imediatamente
    (ganho de performance, sem dependência do Tesseract/Poppler).

Fase 2 — Fallback OCR (PyMuPDF → Pillow → pytesseract):
    Ativada quando o PDF é um documento escaneado (texto nativo insuficiente).
    Cada página é rasterizada a 300 DPI pelo próprio PyMuPDF (sem Poppler),
    convertida para imagem PNG em memória via io.BytesIO + Pillow,
    e processada pelo pytesseract (lang='por').

Princípio arquitectural:
    "O OCR apenas extrai. O Regex apenas higieniza. O Rule Engine decide."
    Este serviço NUNCA persiste nada — apenas lê e retorna dados.
"""

import io
import re
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
#  Mapa de números por extenso → inteiros (PT-BR)
# ─────────────────────────────────────────────────────────────────────────────

_EXTENSO: dict[str, int] = {
    "zero": 0, "um": 1, "uma": 1, "dois": 2, "duas": 2, "tres": 3, "quatro": 4,
    "cinco": 5, "seis": 6, "sete": 7, "oito": 8, "nove": 9, "dez": 10,
    "onze": 11, "doze": 12, "treze": 13, "quatorze": 14, "catorze": 14,
    "quinze": 15, "dezesseis": 16, "dezessete": 17, "dezoito": 18, "dezenove": 19,
    "vinte": 20, "trinta": 30, "quarenta": 40, "cinquenta": 50, "sessenta": 60,
    "setenta": 70, "oitenta": 80, "noventa": 90, "cem": 100, "cento": 100,
    "duzentos": 200, "duzentas": 200, "trezentos": 300, "trezentas": 300,
    "quatrocentos": 400, "quinhentos": 500, "seiscentos": 600,
    "setecentos": 700, "oitocentos": 800, "novecentos": 900, "mil": 1000,
}


# ─────────────────────────────────────────────────────────────────────────────
#  Cadeia de Regex — ordem: mais específica → mais genérica
#  Cada padrão recebe uma confiança (0-100) proporcional à sua precisão.
# ─────────────────────────────────────────────────────────────────────────────

_PATTERNS: list[tuple[str, int]] = [
    # Padrão 0 — "Carga Horaria: 5h" / "Carga Horária: 40 horas" (dois-pontos — comum nos templates)
    (
        r"carga\s+hor[aá]ri[ao]\s*[:\-]\s*(\d{1,4})\s*(?:h(?:oras?|rs?)?)?",
        98,
    ),
    # Padrão 1 — "carga horária de 40h" / "carga horaria de 40 horas"
    (
        r"carga\s+hor[aá]ri[ao]\s+(?:de\s+|total\s+de\s+)?(\d{1,4})\s*(?:h(?:oras?|rs?)?)",
        95,
    ),
    # Padrão 2 — "total de 40 horas" / "total de 40h"
    (
        r"total\s+de\s+(\d{1,4})\s*(?:h(?:oras?|rs?)?)",
        90,
    ),
    # Padrão 3 — "40 (quarenta) horas" — dígito + extenso entre parênteses
    (
        r"(\d{1,4})\s*\(\w+\)\s*h(?:oras?|rs?)?",
        88,
    ),
    # Padrão 4 — "quarenta horas" / "quarenta hrs" — só extenso
    (
        r"\b(" + "|".join(_EXTENSO.keys()) + r")\s+h(?:oras?|rs?)",
        80,
    ),
    # Padrão 5 — "40h" / "40 hrs" / "40 horas" (sem contexto de carga)
    (
        r"\b(\d{1,4})\s*h(?:oras?|rs?)\b",
        70,
    ),
    # Padrão 6 — "horas: 40" ou "horas = 40" (tabelas ou rodapés)
    (
        r"h(?:oras?|rs?)[\s:=]+(\d{1,4})\b",
        65,
    ),
    # Padrão 7 — Fallback: qualquer número próximo a "hora"
    (
        r"(\d{1,4})\s*(?:a\s+)?(?:h(?:oras?|rs?))",
        50,
    ),
]

# Normaliza os padrões compilando-os para performance
_COMPILED: list[tuple[re.Pattern, int]] = [
    (re.compile(pat, re.IGNORECASE | re.UNICODE), conf)
    for pat, conf in _PATTERNS
]

# Padrão para o extenso — separado para evitar compilação a cada chamada
_EXTENSO_KEYS_RE = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in _EXTENSO.keys()) + r")\b",
    re.IGNORECASE,
)


# ─────────────────────────────────────────────────────────────────────────────
#  Data Classes de Resultado
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class OcrResultado:
    """
    Resultado completo do processo de extração OCR + Regex.

    Attributes:
        texto_extraido:   Texto bruto concatenado de todas as páginas do PDF.
        horas_encontradas: Valor inteiro de horas extraído pelo Regex (0 se falhou).
        indice_confianca:  Confiança em % (0-100) do padrão que fez match.
        padrao_usado:      Nome descritivo do padrão Regex vencedor.
        sucesso:           True se pelo menos um padrão encontrou horas > 0.
        erro:              Mensagem de erro, se o OCR falhou completamente.
    """
    texto_extraido:    str   = ""
    horas_encontradas: int   = 0
    indice_confianca:  float = 0.0
    padrao_usado:      str   = "nenhum"
    sucesso:           bool  = False
    erro:              Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
#  Motor de Extração de Texto Híbrido (PyMuPDF native → Tesseract fallback)
# ─────────────────────────────────────────────────────────────────────────────

_LIMIAR_TEXTO_NATIVO = 30  # chars mínimos para confiar na extração nativa


def _normalizar(texto: str) -> str:
    """Normaliza espaços e linhas em branco excessivos."""
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def _extrair_texto_pdf(caminho_pdf: str) -> str:
    """
    Extrator híbrido em duas fases.

    Fase 1 — Nativa (PyMuPDF `get_text`):
        Tenta extrair o texto digital embutido. Se o texto resultante tiver
        pelo menos `_LIMIAR_TEXTO_NATIVO` caracteres, retorna imediatamente.

    Fase 2 — Fallback OCR (Tesseract via rasterização):
        Ativada apenas quando o texto nativo é insuficiente (PDF escaneado).
        Cada página é convertida em imagem PNG a 300 DPI pelo próprio PyMuPDF,
        passada para Pillow e depois ao pytesseract (lang='por').
        Se o Tesseract não estiver instalado no SO, o fallback é capturado
        silenciosamente e o texto nativo (curto) é retornado.

    Returns:
        str: Texto bruto extraído (uma ou ambas as fases).

    Raises:
        RuntimeError: Se o ficheiro não puder ser aberto pelo PyMuPDF.
    """
    import fitz  # PyMuPDF

    try:
        doc = fitz.open(caminho_pdf)
    except Exception as exc:
        raise RuntimeError(f"PyMuPDF não conseguiu abrir '{caminho_pdf}': {exc}") from exc

    # ── Fase 1: Extração nativa ─────────────────────────────────────────────
    paginas_nativas: list[str] = []
    for num_pag, page in enumerate(doc):
        try:
            paginas_nativas.append(page.get_text("text"))
        except Exception as exc:
            logger.warning("[Nativo] Página %d de '%s' falhou: %s", num_pag, caminho_pdf, exc)
            paginas_nativas.append("")

    texto_nativo = _normalizar("\n".join(paginas_nativas))

    if len(texto_nativo) >= _LIMIAR_TEXTO_NATIVO:
        logger.debug("[Nativo] Texto suficiente (%d chars) — OCR Tesseract desnecessário.",
                     len(texto_nativo))
        doc.close()
        return texto_nativo

    logger.info(
        "[Nativo] Texto insuficiente (%d chars) em '%s' — activando Tesseract OCR.",
        len(texto_nativo), caminho_pdf,
    )

    # ── Fase 2: Fallback via Tesseract ────────────────────────────────────────
    try:
        import pytesseract
        from PIL import Image

        paginas_ocr: list[str] = []
        for num_pag, page in enumerate(doc):
            try:
                # Rasteriza a página a 300 DPI sem depender do Poppler
                pix = page.get_pixmap(dpi=300)
                buffer = io.BytesIO(pix.tobytes("png"))
                img = Image.open(buffer)
                texto_pag = pytesseract.image_to_string(img, lang="por")
                paginas_ocr.append(texto_pag)
                logger.debug("[Tesseract] Página %d: %d chars extraídos.",
                             num_pag, len(texto_pag))
            except Exception as exc_pag:
                logger.warning("[Tesseract] Página %d de '%s' falhou: %s",
                               num_pag, caminho_pdf, exc_pag)
                paginas_ocr.append("")

        texto_ocr = _normalizar("\n".join(paginas_ocr))
        doc.close()
        return texto_ocr

    except Exception as exc_tess:
        # Tesseract não instalado ou falha inesperada — não crasha a API
        logger.error(
            "[Tesseract] Fallback falhou para '%s': %s — retornando texto nativo.",
            caminho_pdf, exc_tess,
        )
        doc.close()
        return texto_nativo  # retorna o texto curto; Regex pode ainda encontrar algo


# ─────────────────────────────────────────────────────────────────────────────
#  Motor de Regex — extrai horas do texto
# ─────────────────────────────────────────────────────────────────────────────

def _resolver_extenso(token: str) -> Optional[int]:
    """Converte uma string por extenso para inteiro. Retorna None se não reconhecer."""
    token_lower = token.lower().strip()
    return _EXTENSO.get(token_lower)


def _extrair_horas_regex(texto: str) -> tuple[int, float, str]:
    """
    Aplica a cadeia de padrões Regex ao texto extraído pelo OCR.

    Itera os padrões em ordem decrescente de confiança. Retorna ao primeiro match
    que produzir um valor > 0 e <= 1000 (limites razoáveis para uma atividade AACC).

    Returns:
        tuple(horas, confianca, padrao_nome)
    """
    for i, (padrao, confianca) in enumerate(_COMPILED, start=1):
        match = padrao.search(texto)
        if not match:
            continue

        grupo = match.group(1).strip()

        # Tenta converter: pode ser dígito ou extenso
        horas: Optional[int] = None
        if grupo.isdigit():
            horas = int(grupo)
        else:
            horas = _resolver_extenso(grupo)

        if horas is not None and 1 <= horas <= 1000:
            logger.debug("Regex Padrão %d matched: '%s' → %dh (confiança: %d%%)",
                         i, match.group(0), horas, confianca)
            return horas, float(confianca), f"Padrão {i}"

    # Nenhum padrão produziu resultado útil
    return 0, 0.0, "nenhum"


# ─────────────────────────────────────────────────────────────────────────────
#  API Pública do Serviço
# ─────────────────────────────────────────────────────────────────────────────

def processar_pdf(caminho_pdf: str) -> OcrResultado:
    """
    Ponto de entrada principal do OCR Service.

    Executa a pipeline completa:
        1. Extrai texto de todas as páginas com PyMuPDF.
        2. Aplica cadeia de Regex para localizar horas.
        3. Retorna OcrResultado completo para o motor de regras.

    Nunca lança exceções — falhas são encapsuladas em OcrResultado.erro.

    Args:
        caminho_pdf: Caminho absoluto no sistema de ficheiros para o PDF.

    Returns:
        OcrResultado com todos os dados de extração.
    """
    resultado = OcrResultado()

    # ── Passo 1: Extracção de texto ──────────────────────────────────────────
    try:
        texto = _extrair_texto_pdf(caminho_pdf)
        resultado.texto_extraido = texto
    except RuntimeError as exc:
        resultado.erro = str(exc)
        logger.error("OCR falhou para '%s': %s", caminho_pdf, exc)
        return resultado  # sem texto, não há o que pesquisar

    if not texto.strip():
        resultado.erro = "PDF sem texto extraível (possivelmente imagem escaneada sem OCR)."
        logger.warning("Texto vazio para '%s'", caminho_pdf)
        return resultado

    # ── Passo 2: Extracção de horas por Regex ────────────────────────────────
    horas, confianca, padrao = _extrair_horas_regex(texto)

    resultado.horas_encontradas = horas
    resultado.indice_confianca  = confianca
    resultado.padrao_usado      = padrao
    resultado.sucesso           = horas > 0

    if resultado.sucesso:
        logger.info("OCR extraiu %dh (conf: %.0f%%) de '%s' via %s",
                    horas, confianca, caminho_pdf, padrao)
    else:
        resultado.erro = "Nenhum padrão de horas encontrado no texto extraído."
        logger.warning("OCR não encontrou horas em '%s'. Texto parcial: %s",
                       caminho_pdf, texto[:300])

    return resultado
