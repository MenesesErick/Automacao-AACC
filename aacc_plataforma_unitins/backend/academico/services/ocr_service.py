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
import os
import re
import logging
import unicodedata
from difflib import SequenceMatcher
from collections import Counter
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# ── Caminho do executável Tesseract ──────────────────────────────────────────
# Em produção (Docker/Linux): o binário já está no PATH — nenhuma config extra.
# Em desenvolvimento (Windows): defina TESSERACT_CMD no .env apontando para o
#   executável local, ex: C:\Program Files\Tesseract-OCR\tesseract.exe
_tesseract_cmd = os.environ.get("TESSERACT_CMD")
if _tesseract_cmd:
    try:
        import pytesseract as _pyt
        _pyt.pytesseract.tesseract_cmd = _tesseract_cmd
        logger.info("[OCR] Tesseract configurado via TESSERACT_CMD: %s", _tesseract_cmd)
    except ImportError:
        pass



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
    horas_encontradas: float = 0.0
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

# Padrão 1 — Decimal/inteiro simples seguido de unidade de hora.
# Captura: "40h", "2.5 horas", "2,5 hrs", "3 hora(s)"
_PADRAO_CARGA_HORARIA = re.compile(
    r"(\d+(?:[,.]\d+)?)\s*(?:horas?\s*(?:\(s\))?|hrs?|h)\b",
    re.IGNORECASE | re.UNICODE,
)

# Padrão 2 — Composto "X horas e Y minutos" / "X hora(s) e Y minuto(s)".
# Captura: "2 horas e 30 minutos", "1 hora(s) e 45 minuto(s)"
_PADRAO_COMPOSTO = re.compile(
    r"(\d+)\s*(?:horas?\s*(?:\(s\))?|hrs?|h)\s+e\s+(\d+)\s*(?:minutos?\s*(?:\(s\))?|mins?|m(?:in)?)\b",
    re.IGNORECASE | re.UNICODE,
)

# Padrão 3 — Relógio HH:MM (típico em tabelas do verso/conteúdo programático).
# Captura: "2:30" -> 2.5h, "20:00" -> 20.0h
# Limita a 0-99h e 0-59min para evitar datas (2026-08 etc.)
_PADRAO_RELOGIO = re.compile(
    r"\b(\d{1,2}):([0-5]\d)\b",
    re.UNICODE,
)

# Padrão 4 — TOTAL de alta prioridade: "carga horaria total de X" ou
#   "carga horaria de X hora(s)".  Garante precedência máxima (98%).
# Adicionado suporte para "e Y minuto(s)" opcionais.
_PADRAO_TOTAL = re.compile(
    r"carga\s+hor[aá]ri[ao](?:\s+total)?\s+de\s+(\d+(?:[,.]\d+)?)\s*(?:horas?\s*(?:\(s\))?|hrs?|h)?(?:\s+e\s+(\d+)\s*(?:minutos?\s*(?:\(s\))?|mins?|m(?:in)?))?",
    re.IGNORECASE | re.UNICODE,
)

# Padrão contextual de alta precisão — "Carga Horária: Xh" ou "Carga Horaria: 40".
# Usado para bónus de confiança quando o valor coincide com o eleito pelo consenso.
_PADRAO_CONTEXTUAL = re.compile(
    r"carga\s+hor[aá]ri[ao]\s*[:\-]\s*(\d{1,4})",
    re.IGNORECASE | re.UNICODE,
)


def analisar_carga_horaria(texto: str) -> tuple[float, int, str]:
    """
    Motor de Consenso de Horas — suporte a decimais, hora(s), HH:MM e total prioritário.

    Ordem de avaliação:
        0. Padrão TOTAL ("carga horaria total de Xh") — se encontrado, retorna
           imediatamente com 98% de confiança, ignorando frações soltas do verso.
        1. Padrão COMPOSTO ("X hora(s) e Y minuto(s)") — processa antes do simples.
        2. Padrão SIMPLES decimal/inteiro ("40h", "2,5 horas", "3 hora(s)").
        3. Padrão RELÓGIO HH:MM ("20:00" -> 20.0h, "2:30" -> 2.5h).

    Lógica de Confiança (quando não há padrão total):
        - Nenhum valor            -> (0.0, 0,  "sem_resultado")
        - Um único valor          -> (v,  90,  "unico")
        - Múltiplos, todos iguais -> (v,  95,  "consenso")
        - Múltiplos, domina >=60% -> (v,  75,  "maioria")
        - Múltiplos, ambiguidade  -> (v,  30,  "ambiguo")

    Bónus +5: valor confirmado pelo padrão contextual "Carga Horária: Xh".

    Returns:
        tuple(horas: float, confianca: int, descricao: str)
    """
    # ── Fase 0: Padrão TOTAL — precedência máxima ─────────────────────────────
    # "carga horaria total de 40 horas" ou "carga horaria de 3 hora(s)"
    # Evita que as frações do verso gerem falsa ambiguidade.
    match_total = _PADRAO_TOTAL.search(texto)
    if match_total:
        try:
            horas_parte = float(match_total.group(1).replace(",", "."))
            minutos_parte = float(match_total.group(2)) if match_total.group(2) else 0.0
            valor_total = round(horas_parte + minutos_parte / 60.0, 2)
            if 0.25 <= valor_total <= 999:
                logger.info(
                    "[TOTAL] Padrao de total encontrado: %.2fh (conf=98%%) via '%s'",
                    valor_total, match_total.group(0),
                )
                return valor_total, 98, "total"
        except (ValueError, IndexError):
            pass

    candidatos: list[float] = []
    posicoes_usadas: set[int] = set()

    # ── Fase 1: Padrão COMPOSTO ("X hora(s) e Y minuto(s)") ──────────────────
    for m in _PADRAO_COMPOSTO.finditer(texto):
        try:
            horas_parte   = float(m.group(1))
            minutos_parte = float(m.group(2))
            valor = round(horas_parte + minutos_parte / 60.0, 2)
            if 0.25 <= valor <= 999:
                candidatos.append(valor)
                posicoes_usadas.update(range(m.start(), m.end()))
                logger.debug("[Composto] '%s' -> %.2fh", m.group(0), valor)
        except (ValueError, IndexError):
            continue

    # ── Fase 2: Padrão SIMPLES decimal / inteiro ──────────────────────────────
    for m in _PADRAO_CARGA_HORARIA.finditer(texto):
        if m.start() in posicoes_usadas:
            continue
        try:
            token = m.group(1).replace(",", ".")
            valor = round(float(token), 2)
            if 0.25 <= valor <= 999:
                candidatos.append(valor)
                posicoes_usadas.update(range(m.start(), m.end()))
        except (ValueError, IndexError):
            continue

    # ── Fase 3: Padrão RELÓGIO HH:MM ─────────────────────────────────────────
    for m in _PADRAO_RELOGIO.finditer(texto):
        if m.start() in posicoes_usadas:
            continue
        try:
            h_part = float(m.group(1))
            m_part = float(m.group(2))
            valor  = round(h_part + m_part / 60.0, 2)
            if 0.25 <= valor <= 99:   # relógio não chega a 100h; ano "2024" descartado
                candidatos.append(valor)
                posicoes_usadas.update(range(m.start(), m.end()))
                logger.debug("[Relogio] '%s' -> %.2fh", m.group(0), valor)
        except (ValueError, IndexError):
            continue

    logger.debug("[Consenso] Candidatos: %s", candidatos)

    if not candidatos:
        return 0.0, 0, "sem_resultado"

    contagem = Counter(candidatos)
    valor_dominante, freq_dominante = contagem.most_common(1)[0]
    total_candidatos = len(candidatos)
    valores_unicos   = len(contagem)

    if total_candidatos == 1:
        horas, confianca, descricao = valor_dominante, 90, "unico"
    elif valores_unicos == 1:
        horas, confianca, descricao = valor_dominante, 95, "consenso"
    elif freq_dominante / total_candidatos >= 0.6:
        horas, confianca, descricao = valor_dominante, 75, "maioria"
    else:
        horas, confianca, descricao = valor_dominante, 30, "ambiguo"

    # Bónus contextual
    match_ctx = _PADRAO_CONTEXTUAL.search(texto)
    if match_ctx:
        try:
            ctx_val = round(float(match_ctx.group(1).replace(",", ".")), 2)
            if abs(ctx_val - horas) < 0.01:
                confianca = min(100, confianca + 5)
                descricao += "+contextual"
        except (ValueError, IndexError):
            pass

    logger.info(
        "[Consenso] %.2fh | confianca=%d%% | tipo=%s | votos=%s",
        horas, confianca, descricao, dict(contagem),
    )
    return horas, confianca, descricao




# ─────────────────────────────────────────────────────────────────────────────
#  Titularidade documental (dupla checagem do nome — gatilho da RN04)
# ─────────────────────────────────────────────────────────────────────────────

LIMIAR_TITULARIDADE = 78.0

_PADROES_NOME = [
    r"certificamos\s+que\s+([A-ZÀ-Ÿ\s]{5,80}?)(?:,|\s+inscrit|\s+portador|\s+participou|\s+concluiu|\s+atuou|\s+CPF|\s+matr)",
    r"declaramos.*?que\s+([A-ZÀ-Ÿ\s]{5,80}?)(?:,|\s+inscrit|\s+portador|\s+participou|\s+concluiu|\s+atuou|\s+é\s+alun|\s+cumpr)",
    r"conferido\s+a\s+([A-ZÀ-Ÿ\s]{5,80}?)(?:,|\s+pela|\s+por)",
]


def _normalizar_nome(texto: str) -> str:
    """Remove acentos, converte para MAIÚSCULAS e colapsa espaços."""
    sem_acentos = "".join(
        c for c in unicodedata.normalize("NFKD", texto or "") if not unicodedata.combining(c)
    )
    return re.sub(r"\s+", " ", sem_acentos.upper()).strip()


def extrair_e_validar_titularidade(texto_extraido: str, nome_esperado: str = None) -> dict:
    """
    Extrai o nome do titular do documento e, se `nome_esperado` for informado,
    faz a dupla checagem fuzzy de titularidade.

    Retorna:
        {"nome_extraido": str|None,
         "titularidade_confirmada": bool,
         "similaridade_titularidade": float (0–100)}
    """
    texto = texto_extraido or ""

    # ── 1. Extração via Regex ────────────────────────────────────────────────
    nome_extraido = None
    for padrao in _PADROES_NOME:
        m = re.search(padrao, texto, re.IGNORECASE | re.DOTALL)
        if m:
            candidato = re.sub(r"\s+", " ", m.group(1)).strip()
            if candidato:
                nome_extraido = candidato
                break

    if not nome_esperado or not nome_esperado.strip():
        return {
            "nome_extraido": nome_extraido,
            "titularidade_confirmada": True,
            "similaridade_titularidade": 100.0,
        }

    # ── 2. Dupla checagem fuzzy ──────────────────────────────────────────────
    esperado = _normalizar_nome(nome_esperado)
    sim = 0.0

    if nome_extraido:
        sim = SequenceMatcher(None, esperado, _normalizar_nome(nome_extraido)).ratio() * 100

    # Janela deslizante de palavras sobre o texto completo (fallback p/ ruído severo)
    palavras = _normalizar_nome(texto).split()
    n = len(esperado.split())
    melhor_janela, melhor_sim_janela = None, 0.0
    for tam in {max(1, n - 1), n, n + 1}:
        for i in range(0, max(0, len(palavras) - tam + 1)):
            janela = " ".join(palavras[i:i + tam])
            r = SequenceMatcher(None, esperado, janela).ratio() * 100
            if r > melhor_sim_janela:
                melhor_sim_janela, melhor_janela = r, janela

    if melhor_sim_janela > sim:
        sim = melhor_sim_janela
        if not nome_extraido and sim >= LIMIAR_TITULARIDADE:
            nome_extraido = melhor_janela

    return {
        "nome_extraido": nome_extraido,
        "titularidade_confirmada": sim >= LIMIAR_TITULARIDADE,
        "similaridade_titularidade": round(sim, 1),
    }


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
            "[%s] OCR: %.2fh | conf=%d%% | '%s'",
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
