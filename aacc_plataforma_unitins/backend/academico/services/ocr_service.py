"""
academico/services/ocr_service.py

Serviço de OCR e Extração de Horas — Extrator Híbrido com Motor de Consenso.

Fase 1 — Nativa (PyMuPDF):
    Tenta extrair o texto digital embutido diretamente no PDF.
    Se o resultado tiver >= 30 caracteres válidos, retorna imediatamente
    (ganho de performance, sem dependência do Tesseract/Poppler).

Fase 2 — Fallback OCR (PyMuPDF → Pillow → pytesseract):
    Ativada quando o PDF é um documento escaneado (texto nativo insuficiente).
    Cada página é rasterizada a 300 DPI pelo próprio PyMuPDF (sem Poppler),
    convertida para imagem PNG em memória via io.BytesIO + Pillow,
    e processada pelo pytesseract (lang='por').

Motor de Consenso (analisar_carga_horaria):
    Colecta TODAS as menções de horas no documento com re.finditer,
    aplica votação por frequência (Counter) e calcula um Índice de
    Confiança diferenciado: 95% consenso, 90% único, 75% maioria, 30% ambíguo.

Princípio arquitectural:
    "O OCR apenas extrai. O Regex apenas higieniza. O Rule Engine decide."
    Este serviço NUNCA persiste nada — apenas lê e retorna dados.
"""

import io
import re
import logging
from collections import Counter
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
#  Data Class de Resultado
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class OcrResultado:
    """
    Resultado completo do processo de extração OCR + Consenso.

    Attributes:
        texto_extraido:    Texto bruto concatenado de todas as páginas do PDF.
        horas_encontradas: Valor inteiro de horas escolhido pelo motor de consenso.
        indice_confianca:  Confiança em % (0-100) baseada no grau de consenso.
        padrao_usado:      Descrição do tipo de resultado (unico/consenso/maioria/ambiguo).
        sucesso:           True se pelo menos um valor de horas foi encontrado.
        erro:              Mensagem de erro ou alerta de ambiguidade.
    """
    texto_extraido:    str   = ""
    horas_encontradas: int   = 0
    indice_confianca:  float = 0.0
    padrao_usado:      str   = "sem_resultado"
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
        return texto_nativo  # retorna o texto curto; motor de consenso pode ainda encontrar algo


# ─────────────────────────────────────────────────────────────────────────────
#  Motor de Consenso de Horas — colecta TODOS os valores e vota
# ─────────────────────────────────────────────────────────────────────────────

# Padrão abrangente que captura TODAS as menções de carga horária no texto.
# Grupo 1: número inteiro (vírgula/ponto decimal são ignorados).
_PADRAO_CARGA_HORARIA = re.compile(
    r"(\d{1,3})(?:[,.]\d+)?\s*(?:horas?|hrs?|h)\b",
    re.IGNORECASE | re.UNICODE,
)

# Padrão contextual de alta precisão — "Carga Horária: Xh" ou "Carga Horaria: 40".
# Usado para bónus de confiança quando o valor coincide com o eleito pelo consenso.
_PADRAO_CONTEXTUAL = re.compile(
    r"carga\s+hor[aá]ri[ao]\s*[:\-]\s*(\d{1,4})",
    re.IGNORECASE | re.UNICODE,
)


def analisar_carga_horaria(texto: str) -> tuple[int, int, str]:
    """
    Motor de Consenso de Horas.

    Colecta TODAS as menções de carga horária no documento usando `re.finditer`,
    filtra valores improváveis (fora de [1, 999]) e aplica votação por frequência
    (Counter) para determinar o valor mais provável e o índice de confiança.

    Lógica de Confiança:
        - Nenhum valor encontrado         → (0,  0,  "sem_resultado")
        - Um único valor                  → (v,  90, "unico")
        - Múltiplos valores, todos iguais → (v,  95, "consenso")
        - Múltiplos, um domina (>= 60%)   → (v,  75, "maioria")
        - Múltiplos, distribuição dispersa→ (v,  30, "ambiguo")

    Bónus +5: se o valor escolhido é confirmado pelo padrão contextual de alta
    precisão ("Carga Horária: Xh"), a confiança sobe até ao máximo de 100%.

    Returns:
        tuple(horas: int, confianca: int, descricao: str)
    """
    # 1. Colecta todos os candidatos numéricos válidos
    candidatos: list[int] = []
    for m in _PADRAO_CARGA_HORARIA.finditer(texto):
        try:
            valor = int(m.group(1))
            if 1 <= valor <= 999:  # descarta 0 e valores absurdos (ex: anos "2024")
                candidatos.append(valor)
        except (ValueError, IndexError):
            continue

    logger.debug("[Consenso] Candidatos encontrados: %s", candidatos)

    # 2. Lista vazia → sem resultado
    if not candidatos:
        return 0, 0, "sem_resultado"

    contagem = Counter(candidatos)
    valor_dominante, freq_dominante = contagem.most_common(1)[0]
    total_candidatos = len(candidatos)
    valores_unicos   = len(contagem)

    # 3. Determina confiança pelo padrão de distribuição
    if total_candidatos == 1:
        horas, confianca, descricao = valor_dominante, 90, "unico"

    elif valores_unicos == 1:
        # Todos os matches retornaram o mesmo número — consenso total
        horas, confianca, descricao = valor_dominante, 95, "consenso"

    elif freq_dominante / total_candidatos >= 0.6:
        # Um valor domina com >= 60% das ocorrências
        horas, confianca, descricao = valor_dominante, 75, "maioria"

    else:
        # Ambiguidade: valores diferentes com distribuição dispersa.
        # Escolhe o mais frequente, mas sinaliza para revisão humana.
        horas, confianca, descricao = valor_dominante, 30, "ambiguo"

    # 4. Bónus contextual: valor confirmado por padrão de alta precisão
    match_ctx = _PADRAO_CONTEXTUAL.search(texto)
    if match_ctx:
        try:
            if int(match_ctx.group(1)) == horas:
                confianca = min(100, confianca + 5)
                descricao += "+contextual"
        except (ValueError, IndexError):
            pass

    logger.info(
        "[Consenso] %dh | confiança=%d%% | tipo=%s | votos=%s",
        horas, confianca, descricao, dict(contagem),
    )
    return horas, confianca, descricao


# ─────────────────────────────────────────────────────────────────────────────
#  API Pública do Serviço
# ─────────────────────────────────────────────────────────────────────────────

def processar_pdf(caminho_pdf: str) -> OcrResultado:
    """
    Ponto de entrada principal do OCR Service.

    Pipeline:
        1. Extrai texto via extrator híbrido (nativo PyMuPDF + fallback Tesseract).
        2. Analisa TODAS as menções de horas via `analisar_carga_horaria` (Consenso).
        3. Retorna OcrResultado com índice de confiança diferenciado por ambiguidade.

    Nunca lança excepções — falhas são encapsuladas em OcrResultado.erro.
    """
    resultado = OcrResultado()

    # ── Passo 1: Extracção de texto ──────────────────────────────────────────
    try:
        texto = _extrair_texto_pdf(caminho_pdf)
        resultado.texto_extraido = texto
    except RuntimeError as exc:
        resultado.erro = str(exc)
        logger.error("OCR falhou para '%s': %s", caminho_pdf, exc)
        return resultado

    if not texto.strip():
        resultado.erro = "PDF sem texto extraível (possivelmente imagem escaneada sem OCR)."
        logger.warning("Texto vazio para '%s'", caminho_pdf)
        return resultado

    # ── Passo 2: Motor de Consenso de Horas ──────────────────────────────────
    horas, confianca, descricao = analisar_carga_horaria(texto)

    resultado.horas_encontradas = horas
    resultado.indice_confianca  = float(confianca)
    resultado.padrao_usado      = descricao
    resultado.sucesso           = horas > 0

    if resultado.sucesso:
        logger.info(
            "[%s] OCR: %dh | conf=%d%% | '%s'",
            descricao.upper(), horas, confianca, caminho_pdf,
        )
        # Flag de ambiguidade — coordenador DEVE rever manualmente
        if confianca <= 30:
            resultado.erro = (
                f"Ambiguidade detectada (confiança: {confianca}%): múltiplos valores de horas "
                "foram encontrados no documento. Revisão manual obrigatória."
            )
    else:
        resultado.erro = "Nenhuma menção de carga horária encontrada no texto extraído."
        logger.warning("[SEM_RESULTADO] '%s' | texto parcial: %s",
                       caminho_pdf, texto[:300])

    return resultado
