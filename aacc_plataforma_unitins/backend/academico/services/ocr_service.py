"""
academico/services/ocr_service.py

Serviço de OCR e Extração de Horas com PyMuPDF + Regex.

Responsabilidades:
    1. Extrair o texto completo de um PDF usando PyMuPDF (fitz).
    2. Aplicar uma cadeia de expressões regulares (em ordem de especificidade)
       para localizar a carga horária informada no documento.
    3. Calcular um índice de confiança baseado no padrão que encontrou a match.
    4. Retornar um OcrResultado com todos os dados para o motor de regras.

Princípio arquitectural:
    "O OCR apenas extrai. O Regex apenas higieniza. O Rule Engine decide."
    Este serviço NUNCA persiste nada — apenas lê e retorna dados.
"""

import re
import logging
from dataclasses import dataclass, field
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
#  Motor de Extração de Texto (PyMuPDF)
# ─────────────────────────────────────────────────────────────────────────────

def _extrair_texto_pdf(caminho_pdf: str) -> str:
    """
    Extrai o texto completo de todas as páginas do PDF usando PyMuPDF (fitz).

    Estratégia:
        - Usa get_text("text") por página, concatenando com separador de linha.
        - Normaliza espaços múltiplos e remove caracteres de controlo problemáticos.

    Returns:
        str: Texto bruto concatenado de todas as páginas.

    Raises:
        RuntimeError: Se o ficheiro não puder ser aberto ou processado.
    """
    import fitz  # PyMuPDF — importado localmente para não quebrar se não estiver instalado

    try:
        doc  = fitz.open(caminho_pdf)
        paginas: list[str] = []

        for num_pag, page in enumerate(doc):
            try:
                texto_pag = page.get_text("text")
                paginas.append(texto_pag)
            except Exception as exc:
                logger.warning("Página %d do PDF '%s' falhou: %s", num_pag, caminho_pdf, exc)
                paginas.append("")  # página problemática → texto vazio, não aborta

        doc.close()
        texto_completo = "\n".join(paginas)

        # Normalização básica — reduz ruído para o Regex
        texto_completo = re.sub(r"[ \t]+", " ", texto_completo)   # spaces múltiplos
        texto_completo = re.sub(r"\n{3,}", "\n\n", texto_completo) # linhas em branco extras

        return texto_completo.strip()

    except Exception as exc:
        raise RuntimeError(f"PyMuPDF não conseguiu abrir '{caminho_pdf}': {exc}") from exc


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
