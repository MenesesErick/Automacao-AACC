"""
academico/management/gerador_certificados.py

Gerador de certificados comprobatórios realistas (ReportLab) para povoamento de testes.

Os PDFs produzidos são compatíveis com os extratores reais do sistema:

  AnalisePreviaView (academico/views.py)
    - Título : gatilho posicional  `participou do(a) "TÍTULO"`,
               `concluiu o curso de "TÍTULO"` ou `evento "TÍTULO"` (aspas retas).
               ⚠ O regex fecha o título no primeiro `"`, `”` ou `'` — nunca usar
               aspas/apóstrofos dentro dos títulos do catálogo.
    - Período: cascata de regex — `dd/mm/aaaa a dd/mm/aaaa`,
               `dd de mês a dd de mês de aaaa`, `dd a dd de mês de aaaa`,
               `dd de mês de aaaa`. O primeiro padrão que casar no texto vence,
               portanto a data de emissão é escrita por extenso e nunca com
               formato de intervalo.

  ocr_service.analisar_carga_horaria
    - Padrão TOTAL de alta prioridade: `carga horária total de X horas` (98%).

Camada textual 100% nativa (PyMuPDF lê direto, sem precisar de Tesseract).
"""

from __future__ import annotations

import datetime
import glob
import hashlib
import html as html_lib
import io
import os
import random
import re
from xml.sax.saxutils import escape

import fitz  # PyMuPDF
from PIL import Image, ImageEnhance, ImageFilter
from django.conf import settings
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import Frame, Paragraph

from academico.rules.resolucao_057 import LIMITES_CATEGORIAS

# ── Templates Base (PNGs de fundo) ───────────────────────────────────────────
def _aplicar_template_fundo(c, tipo_doc: str, page_w: float, page_h: float, rng: random.Random) -> bool:
    """
    Desenha um template PNG da pasta templates_base como plano de fundo.
    tipo_doc: 'certificado' (paisagem) ou 'declaracao' (retrato).
    Retorna True se aplicou imagem com sucesso, False se desenhará moldura vetorial.
    """
    templates_dir = os.path.join(settings.MEDIA_ROOT, 'templates_base')
    prefixo = 'certificado_bg' if tipo_doc == 'certificado' else 'declaracao_bg'
    candidatos = sorted(glob.glob(os.path.join(templates_dir, f"{prefixo}*.png")))
    if not candidatos:
        return False
    caminho = rng.choice(candidatos)
    try:
        c.drawImage(caminho, 0, 0, width=page_w, height=page_h,
                    preserveAspectRatio=False, mask='auto')
        return True
    except Exception:
        return False

# ── Estratificação do dataset (Nível 1/2/3) ──────────────────────────────────
DPI_RASTER = 200


def _aplicar_nivel_dificuldade(pdf_bytes: bytes, nivel: int, rng: random.Random) -> bytes:
    """
    Nível 1: PDF vetorial nativo (retorna inalterado).
    Nível 2: rasteriza a 200 DPI e regrava como PDF achatado (sem camada textual).
    Nível 3: rasteriza, rotaciona (-2°..2°), aplica GaussianBlur(0.8) e regrava achatado.
    """
    if nivel not in (1, 2, 3):
        raise ValueError(f"nivel_dificuldade inválido: {nivel} (use 1, 2 ou 3)")
    if nivel == 1:
        return pdf_bytes

    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        page = doc[0]
        pix = page.get_pixmap(dpi=DPI_RASTER, alpha=False)
        largura_pt, altura_pt = page.rect.width, page.rect.height

        if nivel == 2:
            saida = fitz.open()
            nova = saida.new_page(width=largura_pt, height=altura_pt)
            nova.insert_image(nova.rect, pixmap=pix)
            try:
                return saida.tobytes(deflate=True)
            finally:
                saida.close()

        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

    angulo = rng.uniform(-2, 2)
    img = img.rotate(angulo, resample=Image.BICUBIC, expand=False, fillcolor=(255, 255, 255))
    img = img.filter(ImageFilter.GaussianBlur(radius=0.8))

    # Caos controlado: brilho/contraste drásticos (sorteia lado escuro ou lavado)
    brilho = rng.choice([rng.uniform(0.60, 0.80), rng.uniform(1.20, 1.45)])
    contraste = rng.choice([rng.uniform(0.50, 0.75), rng.uniform(1.30, 1.70)])
    img = ImageEnhance.Brightness(img).enhance(brilho)
    img = ImageEnhance.Contrast(img).enhance(contraste)

    # Artefatos de compressão JPEG extremos (quality=15) e recarga
    jpeg_buf = io.BytesIO()
    img.save(jpeg_buf, format="JPEG", quality=JPEG_QUALITY_N3)
    jpeg_buf.seek(0)
    img = Image.open(jpeg_buf).convert("RGB")

    buf = io.BytesIO()
    img.save(buf, format="PDF", resolution=float(DPI_RASTER))
    return buf.getvalue()


# ── Variabilidade semântica e anomalias (experimento) ────────────────────────────────────
JPEG_QUALITY_N3 = 15
PROB_ANOMALIA_N3 = 0.15
TEMPLATES_HORAS = ("padrao", "direto", "extenso", "armadilha")
_LEET = str.maketrans({"A": "4", "E": "3", "I": "1", "O": "0", "S": "5"})


def _preparar_experimento(nome_aluno: str, nivel: int, rng: random.Random) -> tuple[str, bool, str]:
    """Sorteia template de horas e (só Nível 3, ~15%) a anomalia de nome estilo OCR falho."""
    template = rng.choice(TEMPLATES_HORAS)
    anomalia = nivel == 3 and rng.random() < PROB_ANOMALIA_N3
    nome_exibido = nome_aluno.upper().translate(_LEET) if anomalia else nome_aluno
    if anomalia and nome_exibido == nome_aluno.upper():
        anomalia = False  # nome sem letras trocáveis: nada a corromper
    return nome_exibido, anomalia, template


def _trecho_horas(template: str, horas: int, continuacao: str | None = None) -> str:
    """
    Trecho final da frase (inicia logo após o período). `continuacao` (declaração) vem
    depois das horas; sem ela, a frase termina em ponto.
    """
    if template == "direto":
        base, sep = f". Carga horária: <b>{horas} horas</b>", ". "
        continuacao = continuacao[:1].upper() + continuacao[1:] if continuacao else None
    elif template == "extenso":
        base, sep = f", perfazendo um total de <b>{horas} horas-aula</b>", ", "
    elif template == "armadilha":
        a = max(1, horas // 3)
        b = max(1, (horas - a) // 2)
        c = max(1, horas - a - b)
        base = (
            f", organizado em módulos de {a} horas (Módulo I), {b} horas (Módulo II) "
            f"e {c} horas (Módulo III), perfazendo ao final a carga horária total de "
            f"<b>{horas} horas</b>"
        )
        sep = ", "
    else:  # padrao
        base, sep = f", com carga horária total de <b>{horas} horas</b>", ", "
    return base + (sep + continuacao if continuacao else ".")


def _texto_puro(texto_html: str) -> str:
    return html_lib.unescape(re.sub(r"<[^>]+>", "", texto_html))


def _metadados(nivel: int, anomalia: bool, template: str, texto_gabarito: str,
               nome_exibido: str, horas: int) -> dict:
    return {
        "nivel": nivel,
        "anomalia_texto": anomalia,
        "template_usado": template,
        "texto_gabarito": texto_gabarito,
        "nome_exibido": nome_exibido,
        "horas_gabarito": horas,
        "jpeg_quality": JPEG_QUALITY_N3 if nivel == 3 else None,
    }


# ── Paleta institucional ─────────────────────────────────────────────────────
AZUL = HexColor("#003366")
AZUL_ESCURO = HexColor("#0A2540")
OURO = HexColor("#F5A623")
CINZA = HexColor("#4B5563")
PAPEL = HexColor("#FFFEFA")

MESES = [
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
]
EIXO_EXIBICAO = {"Ensino": "Ensino", "Pesquisa": "Pesquisa", "Extensao": "Extensão"}

# ── Instituições emissoras ───────────────────────────────────────────────────
# chave -> (nome na faixa superior, sigla do brasão, subtítulo, emissor no corpo)
EMISSORES = {
    "unitins": (
        "UNIVERSIDADE ESTADUAL DO TOCANTINS - UNITINS", "UN",
        "Fundação Universidade do Tocantins · Palmas - TO",
        "a Universidade Estadual do Tocantins - UNITINS",
    ),
    "unitins_pesquisa": (
        "UNIVERSIDADE ESTADUAL DO TOCANTINS - UNITINS", "UN",
        "Pró-Reitoria de Pesquisa e Pós-Graduação",
        "a Pró-Reitoria de Pesquisa e Pós-Graduação da UNITINS",
    ),
    "unitins_extensao": (
        "UNIVERSIDADE ESTADUAL DO TOCANTINS - UNITINS", "UN",
        "Pró-Reitoria de Extensão, Cultura e Assuntos Comunitários",
        "a Pró-Reitoria de Extensão, Cultura e Assuntos Comunitários da UNITINS",
    ),
    "escola_linguas": (
        "ESCOLA DE LÍNGUAS UNITINS", "EL",
        "Centro de Idiomas da Universidade Estadual do Tocantins",
        "a Escola de Línguas Unitins",
    ),
    "sbc": (
        "SBC - SOCIEDADE BRASILEIRA DE COMPUTAÇÃO", "SBC",
        "Comissão Organizadora de Eventos Científicos",
        "a Sociedade Brasileira de Computação - SBC",
    ),
    "sebrae": (
        "SEBRAE/TO", "SB",
        "Serviço Brasileiro de Apoio às Micro e Pequenas Empresas - Tocantins",
        "o SEBRAE/TO",
    ),
    "senai": (
        "SENAI - TOCANTINS", "SN",
        "Serviço Nacional de Aprendizagem Industrial",
        "o SENAI - Tocantins",
    ),
    "fiap": (
        "FIAP ONLINE", "FI",
        "Educação Profissional em Tecnologia",
        "a FIAP Online",
    ),
    "cambridge": (
        "CAMBRIDGE ENGLISH LANGUAGE CENTER", "CE",
        "Preparatory Program · Palmas - TO",
        "o Cambridge English Language Center",
    ),
    "prefeitura": (
        "PREFEITURA MUNICIPAL DE PALMAS", "PM",
        "Secretaria Municipal de Desenvolvimento Social",
        "a Prefeitura Municipal de Palmas",
    ),
    "dce": (
        "DIRETÓRIO CENTRAL DOS ESTUDANTES - UNITINS", "DCE",
        "Entidade representativa dos discentes da UNITINS",
        "o Diretório Central dos Estudantes da UNITINS",
    ),
    "cpa": (
        "COMISSÃO PRÓPRIA DE AVALIAÇÃO - CPA/UNITINS", "CPA",
        "Avaliação Institucional da UNITINS",
        "a Comissão Própria de Avaliação da UNITINS",
    ),
}

# ── Catálogo de atividades ───────────────────────────────────────────────────
# (slug da categoria, título, emissor, carga horária, estilo de frase)
#   estilo: 'participou' -> participou do(a) "T"
#           'curso'      -> concluiu o curso de "T"
#           'evento'     -> ... do evento "T"
# Os tetos da Resolução 057/2025 são respeitados em `montar_plano_aluno`.
CATALOGO_ATIVIDADES: list[tuple[str, str, str, int, str]] = [
    # ───────── ENSINO ─────────
    ("monitoria", "Monitoria de Algoritmos e Estruturas de Dados", "unitins", 30, "participou"),
    ("monitoria", "Monitoria de Banco de Dados Relacional", "unitins", 30, "participou"),
    ("cursos_curta_duracao", "Python para Ciência de Dados", "fiap", 30, "curso"),
    ("cursos_curta_duracao", "Fundamentos de Segurança da Informação", "senai", 20, "curso"),
    ("cursos_curta_duracao", "Git e GitHub para Equipes de Desenvolvimento", "sbc", 10, "curso"),
    ("escola_linguas", "Inglês Instrumental para Tecnologia da Informação", "escola_linguas", 40, "curso"),
    ("escola_linguas", "Espanhol Básico - Módulo I", "escola_linguas", 20, "curso"),
    ("escola_linguas", "Inglês Intermediário - Módulo II", "escola_linguas", 40, "curso"),
    ("pibid", "PIBID Unitins 2025 - Iniciação à Docência em Informática", "unitins", 60, "participou"),
    ("pibid", "PIBID Unitins 2026 - Residência Pedagógica em Computação", "unitins", 60, "participou"),
    ("disciplinas_outros_cursos", "Disciplina Eletiva de Empreendedorismo e Inovação", "unitins", 60, "participou"),
    # ───────── PESQUISA ─────────
    ("projetos_pesquisa", "Iniciação Científica: Inteligência Artificial Aplicada à Saúde Pública", "unitins_pesquisa", 40, "participou"),
    ("projetos_pesquisa", "Projeto de Pesquisa em Otimização de Bancos de Dados Distribuídos", "unitins_pesquisa", 30, "participou"),
    ("projetos_pesquisa", "Projeto de Pesquisa em Visão Computacional para Agricultura", "unitins_pesquisa", 30, "participou"),
    ("grupos_pesquisa", "Grupo de Estudos em Computação em Nuvem", "unitins_pesquisa", 30, "participou"),
    ("grupos_pesquisa", "Grupo de Pesquisa em Engenharia de Software Empírica", "unitins_pesquisa", 30, "participou"),
    ("grupos_pesquisa", "Grupo de Trabalho em Ciência de Dados Aplicada", "unitins_pesquisa", 20, "participou"),
    ("trabalhos_cientificos", "Apresentação de Trabalho no Congresso de Iniciação Científica da UNITINS", "unitins_pesquisa", 20, "evento"),
    ("trabalhos_cientificos", "Apresentação de Artigo no Workshop de Computação Aplicada", "sbc", 20, "evento"),
    ("trabalhos_cientificos", "Apresentação de Pôster no Simpósio Regional de Tecnologia", "sbc", 10, "evento"),
    ("publicacoes", "Publicação de Artigo Completo nos Anais do Encontro de Computação do Norte", "sbc", 30, "participou"),
    ("publicacoes", "Publicação de Resumo Expandido na Revista Científica Multidisciplinar da UNITINS", "unitins_pesquisa", 20, "participou"),
    # ───────── EXTENSÃO ─────────
    ("projetos_extensao", "Unitins na Comunidade: Inclusão Digital para Idosos", "unitins_extensao", 20, "participou"),
    ("projetos_extensao", "Projeto Robótica nas Escolas Públicas de Palmas", "unitins_extensao", 20, "participou"),
    ("projetos_extensao", "Projeto de Extensão Horta Comunitária Inteligente com IoT", "unitins_extensao", 20, "participou"),
    ("seminarios_congressos", "Semana Acadêmica de Sistemas de Informação 2025", "unitins", 20, "evento"),
    ("seminarios_congressos", "Congresso Brasileiro de Software: Teoria e Prática", "sbc", 30, "evento"),
    ("seminarios_congressos", "Simpósio Tocantinense de Tecnologia da Informação", "sbc", 20, "evento"),
    ("seminarios_congressos", "Jornada Acadêmica Integrada da UNITINS", "unitins", 20, "evento"),
    ("seminarios_congressos", "Fórum de Inovação e Empreendedorismo do Tocantins", "sebrae", 10, "evento"),
    ("cursos_extensao", "Curso de Extensão em Desenvolvimento Web com JavaScript", "unitins_extensao", 40, "curso"),
    ("cursos_extensao", "Curso de Nivelamento em Matemática para Computação", "unitins_extensao", 40, "curso"),
    ("organizacao_cursos_eventos", "Semana Acadêmica de Sistemas de Informação 2025 - Comissão Organizadora", "unitins", 10, "evento"),
    ("organizacao_cursos_eventos", "Hackathon UNITINS Inovação - Equipe de Organização", "unitins", 10, "evento"),
    ("campanhas_voluntariado", "Campanha Solidária de Arrecadação de Alimentos", "prefeitura", 10, "evento"),
    ("campanhas_voluntariado", "Programa de Ação Social Natal Solidário", "prefeitura", 10, "evento"),
    ("visitas_tecnicas", "Visita Técnica ao Centro de Dados do Governo do Tocantins", "unitins", 10, "evento"),
    ("idiomas_informatica", "Curso de Excel Avançado e Análise de Dados", "senai", 40, "curso"),
    ("idiomas_informatica", "Curso de Comunicação e Expressão Oral", "sebrae", 20, "curso"),
    ("estagios_extracurriculares", "Estágio Extracurricular em Desenvolvimento de Software", "unitins", 60, "participou"),
    ("campanhas_unitins", "Trote Solidário UNITINS 2025", "unitins", 5, "evento"),
    ("representacao_colegiado", "Representação Discente no Colegiado do Curso", "unitins", 30, "participou"),
    ("representacao_estudantil", "Gestão do Diretório Central dos Estudantes - Biênio 2025/2026", "dce", 30, "participou"),
    ("membro_cpa", "Membro Discente da Comissão Própria de Avaliação - CPA", "cpa", 30, "participou"),
    ("intercambio", "Programa de Intercâmbio Acadêmico Nacional - Mobilidade Interinstitucional", "unitins", 60, "participou"),
]

NOMES_COORDENADORES = [
    "Profa. Dra. Helena Cristina Albuquerque",
    "Prof. Dr. Marcelo Antunes Ribeiro",
    "Profa. Ma. Luciana Barros Teixeira",
    "Prof. Me. Rogério Dantas Figueiredo",
    "Profa. Dra. Sandra Maria Moreira",
]
CARGOS = [
    "Coordenação de Atividades Acadêmico-Científico-Culturais",
    "Coordenação Geral do Evento",
    "Coordenação do Projeto",
    "Direção Acadêmica",
]


# ─────────────────────────────────────────────────────────────────────────────
#  Catálogo → plano por aluno
# ─────────────────────────────────────────────────────────────────────────────

def _horas_efetivas(slug: str, horas: int, acumulado: float) -> float:
    """Horas que o SEBR efetivamente computaria para um certificado novo."""
    regra = LIMITES_CATEGORIAS[slug]
    h = float(horas)
    if regra.teto_por_evento is not None:
        h = min(h, float(regra.teto_por_evento))
    if regra.teto_total is not None:
        h = min(h, max(float(regra.teto_total) - acumulado, 0.0))
    return h


def montar_plano_aluno(meta_horas: int, rng: random.Random | None = None,
                       margem: int = 10) -> list[dict]:
    """
    Seleciona atividades do catálogo cuja soma EFETIVA (já com cortes do SEBR)
    atinge `meta_horas + margem`, cobrindo os 3 eixos.

    Só entram certificados que seriam computados integralmente (sem corte), de modo
    que a aprovação manual posterior leve o aluno a 100% da meta.
    """
    rng = rng or random.Random()
    pool = list(CATALOGO_ATIVIDADES)
    rng.shuffle(pool)

    por_eixo: dict[str, list] = {"Ensino": [], "Pesquisa": [], "Extensao": []}
    for item in pool:
        por_eixo[LIMITES_CATEGORIAS[item[0]].eixo].append(item)

    acumulado_cat: dict[str, float] = {}
    plano: list[dict] = []
    total = 0.0
    alvo = meta_horas + margem

    # Round-robin entre eixos para garantir diversidade (RN02: >= 2 eixos).
    while total < alvo and any(por_eixo.values()):
        for eixo in ("Ensino", "Pesquisa", "Extensao", "Extensao"):  # Extensão tem mais itens
            fila = por_eixo[eixo]
            while fila:
                slug, titulo, emissor, horas, estilo = fila.pop()
                efetivas = _horas_efetivas(slug, horas, acumulado_cat.get(slug, 0.0))
                if efetivas >= horas:  # computa 100% — aceita
                    acumulado_cat[slug] = acumulado_cat.get(slug, 0.0) + efetivas
                    total += efetivas
                    plano.append({
                        "slug": slug, "titulo": titulo, "emissor": emissor,
                        "horas": horas, "estilo": estilo,
                        "eixo": LIMITES_CATEGORIAS[slug].eixo,
                        "categoria_nome": LIMITES_CATEGORIAS[slug].nome,
                    })
                    break
            if total >= alvo:
                break
    return plano


# ─────────────────────────────────────────────────────────────────────────────
#  Datas / Períodos (formatos reconhecidos pelo AnalisePreviaView)
# ─────────────────────────────────────────────────────────────────────────────

def _fmt_num(d: datetime.date) -> str:
    return d.strftime("%d/%m/%Y")


def gerar_periodo(horas: int, rng: random.Random) -> tuple[str, datetime.date]:
    """
    Retorna (texto do período, data final). Datas entre 03/2025 e 06/2026.
    Mistura os 4 formatos esperados pelo extrator.
    """
    inicio_base = datetime.date(2025, 3, 3) + datetime.timedelta(days=rng.randint(0, 420))
    if horas <= 8:
        duracao = rng.randint(0, 1)
    elif horas <= 20:
        duracao = rng.randint(1, 4)
    else:
        duracao = rng.randint(20, 120)
    fim = inicio_base + datetime.timedelta(days=duracao)

    # Mantém o evento antes de out/2026 (data corrente do projeto).
    limite = datetime.date(2026, 9, 30)
    if fim > limite:
        shift = (fim - limite).days
        inicio_base -= datetime.timedelta(days=shift)
        fim -= datetime.timedelta(days=shift)

    ini, f = inicio_base, fim
    if ini == f:
        return f"{ini.day:02d} de {MESES[ini.month - 1]} de {ini.year}", f

    mesmo_ano = ini.year == f.year
    mesmo_mes = mesmo_ano and ini.month == f.month
    escolha = rng.random()

    if mesmo_mes and escolha < 0.35:
        return f"{ini.day:02d} a {f.day:02d} de {MESES[f.month - 1]} de {f.year}", f
    if mesmo_ano and not mesmo_mes and escolha < 0.55:
        return (f"{ini.day:02d} de {MESES[ini.month - 1]} a "
                f"{f.day:02d} de {MESES[f.month - 1]} de {f.year}"), f
    return f"{_fmt_num(ini)} a {_fmt_num(f)}", f


# ─────────────────────────────────────────────────────────────────────────────
#  Desenho
# ─────────────────────────────────────────────────────────────────────────────

def _cpf_formatado(cpf: str | None) -> str:
    digits = "".join(ch for ch in (cpf or "") if ch.isdigit())
    if len(digits) == 11:
        return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"
    return cpf or "000.000.000-00"


def _codigo_autenticidade(nome: str, titulo: str, emissao: datetime.date) -> str:
    h = hashlib.sha1(f"{nome}|{titulo}|{emissao.isoformat()}".encode()).hexdigest().upper()
    return f"UNITINS-{emissao.year}-{h[:4]}-{h[4:8]}"


def _subtitulo_tipo(estilo: str, slug: str) -> str:
    if estilo == "curso":
        return "DE CONCLUSÃO"
    if slug in ("monitoria", "pibid", "estagios_extracurriculares"):
        return "DE ATUAÇÃO ACADÊMICA"
    if slug in ("trabalhos_cientificos", "publicacoes"):
        return "DE APRESENTAÇÃO CIENTÍFICA"
    if slug.startswith("organizacao"):
        return "DE ORGANIZAÇÃO"
    return "DE PARTICIPAÇÃO"


def _frase_atividade(estilo: str, titulo: str, slug: str) -> str:
    """Gatilhos exigidos pelo AnalisePreviaView (aspas retas ao redor do título)."""
    t = escape(titulo)
    if estilo == "curso":
        return f"concluiu o curso de <b>\"{t}\"</b>"
    if estilo == "evento":
        if slug.startswith("organizacao"):
            return f"atuou na organização do evento <b>\"{t}\"</b>"
        if slug == "trabalhos_cientificos":
            return f"apresentou trabalho científico no evento <b>\"{t}\"</b>"
        return f"participou do evento <b>\"{t}\"</b>"
    return f"participou do(a) <b>\"{t}\"</b>"


def _moldura(c, PW: float, PH: float) -> None:
    c.setFillColor(PAPEL)
    c.rect(0, 0, PW, PH, fill=1, stroke=0)

    # moldura externa azul marinho + filete dourado interno
    c.setStrokeColor(AZUL)
    c.setLineWidth(5)
    c.rect(0.8 * cm, 0.8 * cm, PW - 1.6 * cm, PH - 1.6 * cm)
    c.setStrokeColor(OURO)
    c.setLineWidth(1.6)
    c.rect(1.2 * cm, 1.2 * cm, PW - 2.4 * cm, PH - 2.4 * cm)
    c.setStrokeColor(AZUL)
    c.setLineWidth(0.5)
    c.rect(1.45 * cm, 1.45 * cm, PW - 2.9 * cm, PH - 2.9 * cm)

    # cantoneiras douradas
    c.setFillColor(OURO)
    s = 0.45 * cm
    for x, y in ((1.2 * cm, 1.2 * cm), (PW - 1.2 * cm - s, 1.2 * cm),
                 (1.2 * cm, PH - 1.2 * cm - s), (PW - 1.2 * cm - s, PH - 1.2 * cm - s)):
        c.rect(x, y, s, s, fill=1, stroke=0)


def _cabecalho(c, PW: float, PH: float, emissor: tuple) -> None:
    nome, sigla, subtitulo, _ = emissor
    faixa_h = 2.6 * cm
    y0 = PH - 1.45 * cm - faixa_h
    c.setFillColor(AZUL)
    c.rect(1.45 * cm, y0, PW - 2.9 * cm, faixa_h, fill=1, stroke=0)
    c.setFillColor(OURO)
    c.rect(1.45 * cm, y0 - 0.12 * cm, PW - 2.9 * cm, 0.12 * cm, fill=1, stroke=0)

    # brasão (círculo com sigla)
    cx, cy, r = 3.5 * cm, y0 + faixa_h / 2, 0.95 * cm
    c.setFillColor(AZUL_ESCURO)
    c.setStrokeColor(OURO)
    c.setLineWidth(2)
    c.circle(cx, cy, r, fill=1, stroke=1)
    c.setFillColor(OURO)
    c.setFont("Times-Bold", 15 if len(sigla) <= 2 else 12)
    c.drawCentredString(cx, cy - 0.2 * cm, sigla)

    c.setFillColor(HexColor("#FFFFFF"))
    tamanho = 17 if len(nome) < 38 else 14
    c.setFont("Helvetica-Bold", tamanho)
    c.drawCentredString(PW / 2 + 0.8 * cm, y0 + faixa_h / 2 + 0.15 * cm, nome)
    c.setFillColor(OURO)
    c.setFont("Helvetica", 9.5)
    c.drawCentredString(PW / 2 + 0.8 * cm, y0 + faixa_h / 2 - 0.55 * cm, subtitulo)


def gerar_certificado_pdf(
    *,
    nome_aluno: str,
    cpf: str | None,
    matricula: str,
    titulo: str,
    slug: str,
    emissor: str,
    horas: int,
    estilo: str = "participou",
    periodo: str,
    data_fim: datetime.date,
    rng: random.Random | None = None,
    nivel_dificuldade: int = 1,
) -> tuple[bytes, dict]:
    """Gera um certificado comprobatório A4 paisagem; devolve (bytes do PDF, metadados do experimento)."""
    rng = rng or random.Random()
    nome_exibido, anomalia, template = _preparar_experimento(nome_aluno, nivel_dificuldade, rng)
    regra = LIMITES_CATEGORIAS[slug]
    emissor_t = EMISSORES[emissor]
    PW, PH = landscape(A4)

    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=(PW, PH))
    c.setTitle(f"Certificado - {titulo}")
    c.setAuthor(emissor_t[0])

    tem_bg = _aplicar_template_fundo(c, 'certificado', PW, PH, rng)
    if not tem_bg:
        _moldura(c, PW, PH)
        _cabecalho(c, PW, PH, emissor_t)
        top_offset = 1.45 * cm + 2.6 * cm + 1.9 * cm
    else:
        # Quando usa o template_bg com cabeçalho/moldura da imagem,
        # posicionamos o título dentro da área nobre de conteúdo do template
        top_offset = 5.2 * cm

    # ── Título do documento ────────────────────────────────────────────────
    y = PH - top_offset
    c.setFillColor(AZUL)
    c.setFont("Times-Bold", 36)
    c.drawCentredString(PW / 2, y, "CERTIFICADO")
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(CINZA)
    c.drawCentredString(PW / 2, y - 0.75 * cm, _subtitulo_tipo(estilo, slug))
    c.setStrokeColor(OURO)
    c.setLineWidth(2)
    c.line(PW / 2 - 3 * cm, y - 1.1 * cm, PW / 2 + 3 * cm, y - 1.1 * cm)

    # ── Corpo ──────────────────────────────────────────────────────────────
    est = ParagraphStyle(
        "corpo", fontName="Times-Roman", fontSize=14, leading=23,
        alignment=TA_CENTER, textColor=HexColor("#111827"),
    )
    def _montar_texto(nome_no_doc: str) -> str:
        return (
            f"Certificamos que <b>{escape(nome_no_doc.upper())}</b>, portador(a) do CPF nº "
            f"{_cpf_formatado(cpf)}, matrícula acadêmica nº {escape(str(matricula))}, "
            f"{_frase_atividade(estilo, titulo, slug)}, "
            f"promovido por {emissor_t[3]}, realizado no período de <b>{periodo}</b>"
            f"{_trecho_horas(template, horas)}"
        )
    texto = _montar_texto(nome_exibido)
    texto_gabarito = _texto_puro(_montar_texto(nome_aluno))
    frame_top = y - 1.7 * cm
    frame = Frame(
        3.2 * cm, 6.3 * cm, PW - 6.4 * cm, frame_top - 6.3 * cm,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, showBoundary=0,
    )
    frame.addFromList([Paragraph(texto, est)], c)

    # ── Faixa normativa (Eixo / Categoria / Resolução) ─────────────────────
    box_y = 5.0 * cm
    box_h = 1.35 * cm
    c.setFillColor(HexColor("#EBF2F7"))
    c.setStrokeColor(AZUL)
    c.setLineWidth(0.8)
    c.rect(3.2 * cm, box_y, PW - 6.4 * cm, box_h, fill=1, stroke=1)
    c.setFillColor(AZUL)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(3.5 * cm, box_y + 0.8 * cm,
                 f"EIXO FORMATIVO: {EIXO_EXIBICAO[regra.eixo].upper()}")
    c.setFont("Helvetica", 8.5)
    c.setFillColor(HexColor("#111827"))
    c.drawString(3.5 * cm, box_y + 0.3 * cm,
                 f"Categoria AACC: {regra.nome[:78]}")
    c.setFont("Helvetica-Oblique", 8.5)
    c.setFillColor(CINZA)
    c.drawRightString(PW - 3.5 * cm, box_y + 0.55 * cm,
                      "Resolução CONSUNI Nº 057/2025")

    # ── Local e data de emissão ────────────────────────────────────────────
    emissao = data_fim + datetime.timedelta(days=rng.randint(3, 30))
    c.setFillColor(HexColor("#111827"))
    c.setFont("Times-Italic", 11)
    c.drawCentredString(
        PW / 2, 4.35 * cm,
        f"Palmas - TO, {emissao.day:02d} de {MESES[emissao.month - 1]} de {emissao.year}",
    )

    # ── Assinaturas ────────────────────────────────────────────────────────
    sig_y = 3.35 * cm
    nome_coord = rng.choice(NOMES_COORDENADORES)
    cargo = rng.choice(CARGOS)
    c.setStrokeColor(HexColor("#111827"))
    c.setLineWidth(0.6)
    c.line(4.0 * cm, sig_y, 11.5 * cm, sig_y)
    c.line(PW - 11.5 * cm, sig_y, PW - 4.0 * cm, sig_y)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(7.75 * cm, sig_y - 0.45 * cm, nome_coord)
    c.setFont("Helvetica", 8)
    c.drawCentredString(7.75 * cm, sig_y - 0.85 * cm, cargo[:60])
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(PW - 7.75 * cm, sig_y - 0.45 * cm, nome_exibido)
    c.setFont("Helvetica", 8)
    c.drawCentredString(PW - 7.75 * cm, sig_y - 0.85 * cm, "Discente")

    # ── Rodapé de autenticidade ────────────────────────────────────────────
    codigo = _codigo_autenticidade(nome_aluno, titulo, emissao)
    c.setFont("Courier", 8)
    c.setFillColor(CINZA)
    c.drawCentredString(PW / 2, 1.85 * cm,
                        f"Código de Autenticidade: {codigo}")
    c.setFont("Courier", 7)
    c.drawCentredString(PW / 2, 1.55 * cm,
                        "Valide este documento em www.unitins.br/validar-certificado")

    c.showPage()
    c.save()
    pdf = _aplicar_nivel_dificuldade(buf.getvalue(), nivel_dificuldade, rng)
    return pdf, _metadados(nivel_dificuldade, anomalia, template, texto_gabarito, nome_exibido, horas)


def gerar_declaracao_pdf(
    *,
    nome_aluno: str,
    cpf: str | None,
    matricula: str,
    titulo: str,
    slug: str,
    emissor: str,
    horas: int,
    estilo: str = "participou",
    periodo: str,
    data_fim: datetime.date,
    rng: random.Random | None = None,
    nivel_dificuldade: int = 1,
) -> tuple[bytes, dict]:
    """Gera uma declaração comprobatória A4 retrato; devolve (bytes do PDF, metadados do experimento)."""
    rng = rng or random.Random()
    nome_exibido, anomalia, template = _preparar_experimento(nome_aluno, nivel_dificuldade, rng)
    regra = LIMITES_CATEGORIAS[slug]
    emissor_t = EMISSORES[emissor]
    PW, PH = A4

    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=(PW, PH))
    c.setTitle(f"Declaração - {titulo}")
    c.setAuthor(emissor_t[0])

    tem_bg = _aplicar_template_fundo(c, 'declaracao', PW, PH, rng)
    if not tem_bg:
        c.setFillColor(PAPEL)
        c.rect(0, 0, PW, PH, fill=1, stroke=0)
        c.setStrokeColor(AZUL)
        c.setLineWidth(4)
        c.rect(1.0 * cm, 1.0 * cm, PW - 2.0 * cm, PH - 2.0 * cm)
        c.setStrokeColor(OURO)
        c.setLineWidth(1.2)
        c.rect(1.3 * cm, 1.3 * cm, PW - 2.6 * cm, PH - 2.6 * cm)
        # Cabeçalho textual
        c.setFillColor(AZUL)
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(PW / 2, PH - 2.8 * cm, emissor_t[0])
        c.setFillColor(OURO)
        c.setFont("Helvetica", 9)
        c.drawCentredString(PW / 2, PH - 3.4 * cm, emissor_t[2])
        top_offset = 5.2 * cm
    else:
        top_offset = 7.8 * cm  # Safe zone do cabeçalho da imagem PNG de declaração

    # Título
    y = PH - top_offset
    c.setFillColor(AZUL)
    c.setFont("Times-Bold", 26)
    c.drawCentredString(PW / 2, y, "DECLARAÇÃO")
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(CINZA)
    c.drawCentredString(PW / 2, y - 0.65 * cm, "COMPROBATÓRIA DE ATIVIDADE COMPLEMENTAR")
    c.setStrokeColor(OURO)
    c.setLineWidth(1.8)
    c.line(PW / 2 - 2.5 * cm, y - 0.95 * cm, PW / 2 + 2.5 * cm, y - 0.95 * cm)

    # Corpo justificado com Paragraph
    est_corpo = ParagraphStyle(
        "declaracao_corpo", fontName="Times-Roman", fontSize=12.5, leading=22,
        alignment=TA_JUSTIFY, textColor=HexColor("#111827"),
    )
    _conformidade = (
        "em conformidade com as diretrizes da Resolução CONSUNI Nº 057/2025 "
        "da Universidade Estadual do Tocantins - UNITINS."
    )

    def _montar_texto(nome_no_doc: str) -> str:
        return (
            f"Declaramos, para os devidos fins de comprovação e cômputo de Atividades "
            f"Acadêmico-Científico-Culturais (AACC), que o(a) discente "
            f"<b>{escape(nome_no_doc.upper())}</b>, portador(a) do CPF nº {_cpf_formatado(cpf)} "
            f"e matrícula acadêmica nº {escape(str(matricula))}, "
            f"{_frase_atividade(estilo, titulo, slug)}, promovido por {emissor_t[3]}, "
            f"no período de <b>{periodo}</b>"
            f"{_trecho_horas(template, horas, _conformidade)}"
        )
    texto = _montar_texto(nome_exibido)
    texto_gabarito = _texto_puro(_montar_texto(nome_aluno))
    frame_top = y - 1.5 * cm
    frame = Frame(
        2.5 * cm, 9.0 * cm, PW - 5.0 * cm, frame_top - 9.0 * cm,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, showBoundary=0,
    )
    frame.addFromList([Paragraph(texto, est_corpo)], c)

    # Faixa normativa (Eixo / Categoria)
    box_y = 7.4 * cm
    box_h = 1.35 * cm
    c.setFillColor(HexColor("#EBF2F7"))
    c.setStrokeColor(AZUL)
    c.setLineWidth(0.8)
    c.rect(2.5 * cm, box_y, PW - 5.0 * cm, box_h, fill=1, stroke=1)
    c.setFillColor(AZUL)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(2.8 * cm, box_y + 0.8 * cm,
                 f"EIXO FORMATIVO: {EIXO_EXIBICAO[regra.eixo].upper()}")
    c.setFont("Helvetica", 8.5)
    c.setFillColor(HexColor("#111827"))
    c.drawString(2.8 * cm, box_y + 0.3 * cm,
                 f"Categoria AACC: {regra.nome[:68]}")
    c.setFont("Helvetica-Oblique", 8)
    c.setFillColor(CINZA)
    c.drawRightString(PW - 2.8 * cm, box_y + 0.55 * cm,
                      "Resolução CONSUNI Nº 057/2025")

    # Local e data
    emissao = data_fim + datetime.timedelta(days=rng.randint(3, 30))
    c.setFillColor(HexColor("#111827"))
    c.setFont("Times-Italic", 10.5)
    c.drawCentredString(
        PW / 2, 6.6 * cm,
        f"Palmas - TO, {emissao.day:02d} de {MESES[emissao.month - 1]} de {emissao.year}",
    )

    # Assinaturas
    sig_y = 5.2 * cm
    nome_coord = rng.choice(NOMES_COORDENADORES)
    cargo = rng.choice(CARGOS)
    c.setStrokeColor(HexColor("#111827"))
    c.setLineWidth(0.6)
    c.line(PW / 2 - 4.5 * cm, sig_y, PW / 2 + 4.5 * cm, sig_y)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(PW / 2, sig_y - 0.45 * cm, nome_coord)
    c.setFont("Helvetica", 8)
    c.drawCentredString(PW / 2, sig_y - 0.85 * cm, f"{cargo} - {emissor_t[0][:40]}")

    # Rodapé autenticidade
    codigo = _codigo_autenticidade(nome_aluno, titulo, emissao)
    c.setFont("Courier", 8)
    c.setFillColor(CINZA)
    c.drawCentredString(PW / 2, 2.5 * cm, f"Código de Autenticidade: {codigo}")
    c.setFont("Courier", 7)
    c.drawCentredString(PW / 2, 2.15 * cm, "Valide este documento em www.unitins.br/validar-certificado")

    c.showPage()
    c.save()
    pdf = _aplicar_nivel_dificuldade(buf.getvalue(), nivel_dificuldade, rng)
    return pdf, _metadados(nivel_dificuldade, anomalia, template, texto_gabarito, nome_exibido, horas)


def gerar_documento_comprobatorio(
    *,
    nome_aluno: str,
    cpf: str | None,
    matricula: str,
    titulo: str,
    slug: str,
    emissor: str,
    horas: int,
    estilo: str = "participou",
    periodo: str,
    data_fim: datetime.date,
    formato: str = "auto",
    rng: random.Random | None = None,
    nivel_dificuldade: int = 1,
) -> tuple[bytes, dict]:
    """
    Despachante inteligente:
    formato: 'auto' (sorteia certificado landscape ou declaração portrait),
             'certificado' (landscape) ou 'declaracao' (portrait).
    Retorna: (pdf_bytes, metadados_experimento) — metadados inclui `tipo_doc`.
    """
    rng = rng or random.Random()
    if formato == "auto":
        tipo_doc = rng.choice(["certificado", "declaracao"])
    else:
        tipo_doc = formato

    if tipo_doc == "declaracao":
        pdf_bytes, metadados = gerar_declaracao_pdf(
            nome_aluno=nome_aluno, cpf=cpf, matricula=matricula, titulo=titulo,
            slug=slug, emissor=emissor, horas=horas, estilo=estilo,
            periodo=periodo, data_fim=data_fim, rng=rng,
            nivel_dificuldade=nivel_dificuldade,
        )
    else:
        pdf_bytes, metadados = gerar_certificado_pdf(
            nome_aluno=nome_aluno, cpf=cpf, matricula=matricula, titulo=titulo,
            slug=slug, emissor=emissor, horas=horas, estilo=estilo,
            periodo=periodo, data_fim=data_fim, rng=rng,
            nivel_dificuldade=nivel_dificuldade,
        )
    metadados["tipo_doc"] = tipo_doc
    return pdf_bytes, metadados
