"""
academico/management/commands/gerar_dataset.py

Fábrica de Documentos Sintéticos Ultra-Realistas — para validação do OCR e do Motor de Regras.

Gera dois tipos de documentos com alta variabilidade visual e textual:
  - Certificado (landscape/A4): Título em destaque, nome grande, texto justificado.
  - Declaração  (portrait/A4) : Papel timbrado, CNPJ falso, texto burocrático longo.

Todos os PDFs são gerados 100% em memória (io.BytesIO) — zero I/O em disco durante o loop.

Segurança/Idempotência:
    Apaga APENAS certificados com status='pendente_ocr' cujo nome de arquivo
    contenha 'sintetico'. Nunca toca em dados reais ou aprovados.

Uso:
    python manage.py gerar_dataset
    python manage.py gerar_dataset --aluno erick@unitins.br   # apenas 1 aluno
    python manage.py gerar_dataset --qtd 10                    # 10 docs por aluno
"""

import io
import os
import random

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError

from faker import Faker
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.platypus import Paragraph, Frame

from academico.models import AlunoPerfil, CategoriaAACC, Certificado

User   = get_user_model()
_fake  = Faker('pt_BR')

# ── Constantes ────────────────────────────────────────────────────────────────
HORAS_POSSIVEIS = [5, 10, 20, 30, 40, 50]

CATEGORIAS_FALLBACK = [
    {'nome': 'Monitoria e Tutoria',              'eixo': 'Ensino',   'limite_maximo_horas': 40},
    {'nome': 'Iniciacao Cientifica',             'eixo': 'Pesquisa', 'limite_maximo_horas': 40},
    {'nome': 'Projetos de Extensao Comunitaria', 'eixo': 'Extensao', 'limite_maximo_horas': 40},
]

ENTIDADES = [
    "Universidade Estadual do Tocantins - UNITINS",
    "UNITINS / Pro-Reitoria de Extensao e Cultura",
    "Coordenacao de Atividades Academico-Cientifico-Culturais - AACC",
    "Instituto de Inovacao e Tecnologia do Tocantins",
    "Nucleo de Pesquisa Aplicada em Sistemas de Informacao",
    "Centro de Desenvolvimento Profissional e Academico",
]

CIDADES = ["Palmas - TO", "Porto Nacional - TO", "Araguaina - TO", "Gurupi - TO"]


# ─────────────────────────────────────────────────────────────────────────────
#  Utilitários de Texto
# ─────────────────────────────────────────────────────────────────────────────

def _wrap_text(c, text: str, font: str, size: float, max_width: float) -> list[str]:
    """Quebra texto em linhas que cabem dentro de max_width (em pontos)."""
    palavras = text.split()
    linhas, linha_atual = [], []
    for palavra in palavras:
        teste = ' '.join(linha_atual + [palavra])
        if c.stringWidth(teste, font, size) < max_width:
            linha_atual.append(palavra)
        else:
            if linha_atual:
                linhas.append(' '.join(linha_atual))
            linha_atual = [palavra]
    if linha_atual:
        linhas.append(' '.join(linha_atual))
    return linhas


def _draw_wrapped(c, text: str, font: str, size: float, x: float, y_start: float,
                  max_width: float, line_gap: float = 0.55, align: str = 'left') -> float:
    """
    Desenha texto com quebra automática de linha.
    Retorna a coordenada Y após o último caractere desenhado.
    align: 'left' | 'center' | 'right'
    """
    c.setFont(font, size)
    linhas = _wrap_text(c, text, font, size, max_width)
    y = y_start
    for linha in linhas:
        if align == 'center':
            c.drawCentredString(x, y, linha)
        elif align == 'right':
            c.drawRightString(x, y, linha)
        else:
            c.drawString(x, y, linha)
        y -= line_gap * cm
    return y


def _codigo_validacao() -> str:
    """Gera um código de validação falso no estilo documentos brasileiros."""
    letras = ''.join(random.choices('ABCDEFGHJKLMNPQRSTUVWXYZ', k=3))
    nums   = random.randint(10000, 99999)
    return f"{nums}-{letras}"


def _cnpj_falso() -> str:
    """CNPJ formatado com dígitos aleatórios (não válido, apenas realista visualmente)."""
    d = [random.randint(0, 9) for _ in range(14)]
    return f"{d[0]}{d[1]}.{d[2]}{d[3]}{d[4]}.{d[5]}{d[6]}{d[7]}/{d[8]}{d[9]}{d[10]}{d[11]}-{d[12]}{d[13]}"


def _rodape_codigo(c, page_w: float, codigo: str) -> None:
    """Imprime o código de validação no rodapé em fonte Courier pequena."""
    c.setFont("Courier", 7)
    texto = f"Autenticidade: site.aacc.unitins.br/valida | Codigo: {codigo}"
    c.drawCentredString(page_w / 2, 1.0 * cm, texto)


def _tentar_imagem_fundo(c, tipo_doc: str, page_w: float, page_h: float) -> None:
    """
    Tenta desenhar uma imagem de fundo (watermark) se o asset existir.
    Silencioso em caso de ausência — nunca quebra o script.
    """
    nome_asset = 'certificado_bg.png' if tipo_doc == 'certificado' else 'declaracao_bg.png'
    caminho    = os.path.join(settings.MEDIA_ROOT, 'templates_base', nome_asset)
    try:
        if os.path.isfile(caminho):
            c.drawImage(caminho, 0, 0, width=page_w, height=page_h,
                        preserveAspectRatio=True, mask='auto')
    except Exception:
        pass  # asset ausente ou corrompido — continua sem fundo


# ─────────────────────────────────────────────────────────────────────────────
#  Motor de Desenho: Certificado (Landscape A4)
# ─────────────────────────────────────────────────────────────────────────────

def _desenhar_certificado(c, nome_aluno: str, horas: int, nome_evento: str,
                          entidade: str, codigo: str) -> None:
    """
    Certificado horizontal (A4 landscape). Estilo formal e solene.

    Variação aleatória entre 2 sub-layouts:
        Sub-layout A — Times, centralizado, bordas duplas decorativas.
        Sub-layout B — Helvetica, blocos mistos (evento à esquerda, dados à direita).
    """
    PW, PH = landscape(A4)
    margem = 2.5 * cm

    _tentar_imagem_fundo(c, 'certificado', PW, PH)

    sublayout = random.choice(['A', 'B'])

    if sublayout == 'A':
        # ── Borda decorativa dupla ────────────────────────────────────────────
        c.setStrokeColorRGB(0.2, 0.2, 0.5)
        c.setLineWidth(2)
        c.rect(margem, margem, PW - 2 * margem, PH - 2 * margem)
        c.setLineWidth(0.5)
        offset = 0.3 * cm
        c.rect(margem + offset, margem + offset,
               PW - 2 * (margem + offset), PH - 2 * (margem + offset))

        # Título
        c.setFillColorRGB(0.1, 0.1, 0.4)
        c.setFont("Times-Bold", 26)
        c.drawCentredString(PW / 2, PH - 3.5 * cm, "CERTIFICADO DE PARTICIPACAO")

        # Entidade emissora
        c.setFillColorRGB(0.3, 0.3, 0.3)
        c.setFont("Helvetica-Oblique", 10)
        c.drawCentredString(PW / 2, PH - 4.5 * cm, entidade)

        # Linha decorativa
        c.setStrokeColorRGB(0.6, 0.6, 0.8)
        c.setLineWidth(0.8)
        c.line(3.5 * cm, PH - 5.0 * cm, PW - 3.5 * cm, PH - 5.0 * cm)

        # Corpo principal — texto com quebra automática
        corpo = (
            f"Certificamos que o(a) discente "
            f"{nome_aluno.upper()}, "
            f"devidamente inscrito(a) em nossos registros academicos, "
            f"participou e concluiu com exito o(a) {nome_evento}, "
            f"realizado sob a coordenacao desta instituicao, "
            f"totalizando uma carga horaria de {horas} ({"por extenso " + str(horas)}) horas, "
            f"em conformidade com a Resolucao CONSUNI no 057/2025 "
            f"que regulamenta as Atividades Academico-Cientifico-Culturais (AACC)."
        )
        _draw_wrapped(c, corpo, "Times-Roman", 12, PW / 2, PH - 6.5 * cm,
                      PW - 7 * cm, line_gap=0.6, align='center')

        # Rodapé: cidade, data, código
        cidade = random.choice(CIDADES)
        data   = _fake.date_this_decade().strftime('%d de %B de %Y')
        c.setFont("Helvetica", 9)
        c.drawCentredString(PW / 2, 3.5 * cm, f"{cidade}, {data}")

        # Linha de assinatura
        c.setLineWidth(0.5)
        c.setStrokeColorRGB(0, 0, 0)
        c.line(PW / 2 - 4 * cm, 3.0 * cm, PW / 2 + 4 * cm, 3.0 * cm)
        c.setFont("Helvetica-Oblique", 8)
        c.drawCentredString(PW / 2, 2.5 * cm, "Coordenador(a) de AACC")

    else:
        # ── Sub-layout B: Helvetica, dois blocos ─────────────────────────────
        c.setStrokeColorRGB(0.8, 0.1, 0.1)
        c.setLineWidth(3)
        c.line(0, PH - 1.5 * cm, PW, PH - 1.5 * cm)
        c.line(0, 1.5 * cm, PW, 1.5 * cm)

        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 22)
        c.drawString(margem, PH - 3.0 * cm, "CERTIFICADO")
        c.setFont("Helvetica", 11)
        c.drawString(margem, PH - 4.0 * cm, entidade)

        # Coluna esquerda: evento e horas
        c.setFont("Helvetica-Bold", 13)
        c.drawString(margem, PH - 5.5 * cm, "EVENTO / ATIVIDADE:")
        _draw_wrapped(c, nome_evento, "Helvetica", 11, margem, PH - 6.2 * cm,
                      PW / 2 - 3 * cm, line_gap=0.5)

        c.setFont("Helvetica-Bold", 11)
        c.drawString(margem, PH - 8.5 * cm, f"Carga Horaria: {horas}h")

        # Coluna direita: participante
        cx = PW / 2 + 0.5 * cm
        c.setFont("Helvetica-Bold", 13)
        c.drawString(cx, PH - 5.5 * cm, "PARTICIPANTE:")
        c.setFont("Times-Bold", 16)
        _draw_wrapped(c, nome_aluno, "Times-Bold", 16, cx, PH - 6.2 * cm,
                      PW / 2 - 3 * cm, line_gap=0.65)

        # Data e cidade
        data = _fake.date_this_decade().strftime('%d/%m/%Y')
        c.setFont("Helvetica", 9)
        c.drawRightString(PW - margem, 2.0 * cm, f"{random.choice(CIDADES)}, {data}")

    _rodape_codigo(c, PW, codigo)


# ─────────────────────────────────────────────────────────────────────────────
#  Motor de Desenho: Declaração (Portrait A4)
# ─────────────────────────────────────────────────────────────────────────────

def _desenhar_declaracao(c, nome_aluno: str, horas: int, nome_evento: str,
                         entidade: str, codigo: str) -> None:
    """
    Declaração em papel timbrado (A4 portrait). Estilo burocrático/formal.

    Inclui:
      - Cabeçalho com entidade emissora e CNPJ falso
      - Título "DECLARACAO" centralizado
      - Corpo justificado (emulado via frames do ReportLab)
      - Rodapé com assinaturas e código de validação
    """
    PW, PH = A4
    margem = 2.5 * cm

    _tentar_imagem_fundo(c, 'declaracao', PW, PH)

    cnpj = _cnpj_falso()

    # ── Cabeçalho timbrado ────────────────────────────────────────────────────
    c.setFillColorRGB(0.1, 0.1, 0.4)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(PW / 2, PH - 2.0 * cm, entidade)

    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.setFont("Helvetica", 8)
    c.drawCentredString(PW / 2, PH - 2.7 * cm, f"CNPJ: {cnpj}")

    # Linha separadora do timbre
    c.setStrokeColorRGB(0.1, 0.1, 0.4)
    c.setLineWidth(1.5)
    c.line(margem, PH - 3.1 * cm, PW - margem, PH - 3.1 * cm)
    c.setLineWidth(0.5)
    c.line(margem, PH - 3.3 * cm, PW - margem, PH - 3.3 * cm)

    # ── Título ────────────────────────────────────────────────────────────────
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Times-Bold", 16)
    c.drawCentredString(PW / 2, PH - 4.5 * cm, "D E C L A R A C A O")

    # Número do documento fictício
    num_doc = f"{random.randint(100, 999)}/{_fake.date_this_decade().year}"
    c.setFont("Helvetica-Oblique", 8)
    c.drawCentredString(PW / 2, PH - 5.1 * cm, f"Ref.: Doc. no {num_doc}")

    # ── Corpo burocrático com Paragraph (ReportLab) ───────────────────────────
    # Usamos Paragraph + Frame para justificação real de texto longo
    styles = getSampleStyleSheet()
    estilo_corpo = ParagraphStyle(
        'CorpoDeclaracao',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=16,       # espaçamento entre linhas
        alignment=TA_JUSTIFY,
        spaceAfter=8,
    )

    # Sorteia variação textual burocrática (estresse para Regex)
    textos_corpo = [
        (
            f"Declaramos para os devidos fins que o(a) Sr.(a) <b>{nome_aluno}</b>, "
            f"estudante regularmente matriculado(a) no curso vinculado a esta Instituicao, "
            f"participou do evento denominado <i>{nome_evento}</i>, "
            f"no periodo compreendido entre {_fake.date_this_decade().strftime('%d/%m/%Y')} "
            f"e {_fake.date_this_decade().strftime('%d/%m/%Y')}, "
            f"cumprindo integralmente a carga horaria de <b>{horas} ({horas}) horas</b>. "
            f"A atividade esta devidamente registrada no sistema institucional e se enquadra "
            f"nos criterios estabelecidos pela Resolucao CONSUNI no 057/2025."
        ),
        (
            f"Certificamos, para os devidos efeitos legais e academicos, que <b>{nome_aluno}</b> "
            f"concluiu com aproveitamento o(a) {nome_evento}, "
            f"totalizando <b>{horas} horas</b> de atividade. "
            f"O referido documento e emitido pela {entidade}, "
            f"inscrita no CNPJ sob o no {cnpj}, "
            f"e tem plena validade para fins de computo das Atividades Academico-Cientifico-Culturais (AACC) "
            f"conforme normativa vigente."
        ),
        (
            f"Por meio deste instrumento, e em conformidade com os registros institucionais, "
            f"declaramos que <b>{nome_aluno}</b> participou do {nome_evento}, "
            f"atividade classificada na modalidade de extensao universitaria, "
            f"cumprindo um total de <b>{horas} horas</b>. "
            f"O presente documento, emitido em {random.choice(CIDADES)}, "
            f"segue as disposicoes da legislacao educacional vigente e da Resolucao interna no 057/2025."
        ),
    ]

    corpo_html = random.choice(textos_corpo)

    # Adiciona parágrafo extra com informações de contato (ruido textual para OCR)
    rodape_info = (
        f"Informacoes adicionais podem ser obtidas junto a Secretaria Academica. "
        f"Endereco: Quadra {random.randint(100, 999)}, Lote {random.randint(1, 50)}, "
        f"{random.choice(CIDADES)}. Fone: (63) {random.randint(2000, 9999)}-{random.randint(1000, 9999)}."
    )

    paragrafos = [
        Paragraph(corpo_html, estilo_corpo),
        Paragraph("&nbsp;", estilo_corpo),   # linha em branco
        Paragraph(rodape_info, estilo_corpo),
    ]

    # Frame = área de texto com posição e dimensões explícitas
    frame_x = margem
    frame_y = 4.5 * cm   # espaço para assinaturas no rodapé
    frame_w = PW - 2 * margem
    frame_h = PH - 5.5 * cm - 4.5 * cm

    frame = Frame(frame_x, frame_y, frame_w, frame_h, showBoundary=0)
    frame.addFromList(paragrafos, c)

    # ── Bloco de assinatura ───────────────────────────────────────────────────
    sig_y = 3.8 * cm
    c.setLineWidth(0.5)
    c.line(margem, sig_y, PW / 2 - 0.5 * cm, sig_y)
    c.line(PW / 2 + 0.5 * cm, sig_y, PW - margem, sig_y)

    c.setFont("Helvetica", 8)
    c.drawCentredString(PW / 4 + margem / 2, sig_y - 0.4 * cm, "Coordenador(a) de AACC")
    c.drawCentredString(3 * PW / 4 - margem / 2, sig_y - 0.4 * cm, "Pro-Reitor(a) de Extensao")

    # Data e cidade
    data_emissao = _fake.date_this_decade().strftime('%d de %B de %Y')
    c.setFont("Helvetica-Oblique", 8)
    c.drawCentredString(PW / 2, 2.3 * cm,
                        f"{random.choice(CIDADES)}, {data_emissao}")

    _rodape_codigo(c, PW, codigo)


# ─────────────────────────────────────────────────────────────────────────────
#  Orquestrador: decide tipo de doc e gera o PDF
# ─────────────────────────────────────────────────────────────────────────────

def gerar_pdf_sintetico(nome_aluno: str, horas: int, nome_evento: str) -> tuple[bytes, str]:
    """
    Gera um PDF sintético ultra-realista inteiramente em memória.

    Sorteia aleatoriamente entre:
        'certificado' — A4 Landscape, formal e solene
        'declaracao'  — A4 Portrait,  papel timbrado burocrático

    Returns:
        tuple(bytes, str): (conteúdo raw do PDF, tipo_doc)
    """
    tipo_doc = random.choice(['certificado', 'declaracao'])
    entidade = random.choice(ENTIDADES)
    codigo   = _codigo_validacao()

    buffer = io.BytesIO()

    if tipo_doc == 'certificado':
        pagesize = landscape(A4)
    else:
        pagesize = A4

    c = rl_canvas.Canvas(buffer, pagesize=pagesize)

    if tipo_doc == 'certificado':
        _desenhar_certificado(c, nome_aluno, horas, nome_evento, entidade, codigo)
    else:
        _desenhar_declaracao(c, nome_aluno, horas, nome_evento, entidade, codigo)

    c.showPage()
    c.save()

    pdf_bytes = buffer.getvalue()
    buffer.close()   # libera memória imediatamente — sem memory leak
    return pdf_bytes, tipo_doc


# ─────────────────────────────────────────────────────────────────────────────
#  Comando Django
# ─────────────────────────────────────────────────────────────────────────────

class Command(BaseCommand):
    help = (
        "Fabrica de Documentos Sinteticos Ultra-Realistas para validacao do OCR "
        "e do Motor de Regras. Gera Certificados (landscape) e Declaracoes (portrait). "
        "Seguro: apaga apenas registos 'sintetico' + 'pendente_ocr'."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--aluno',
            type=str,
            default=None,
            help="Email do aluno especifico (omita para processar todos os alunos).",
        )
        parser.add_argument(
            '--qtd',
            type=int,
            default=None,
            help="Quantidade fixa de documentos por aluno (padrao: 5 a 8 aleatorios).",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING(
            "\n=== Fabrica de Documentos Sinteticos Ultra-Realistas ==="
        ))

        # ── 1. Limpeza segura e idempotente ───────────────────────────────────
        qs_sinteticos = Certificado.objects.filter(
            status='pendente_ocr',
            arquivo_pdf__icontains='sintetico',
        )
        total_apagados = qs_sinteticos.count()
        qs_sinteticos.delete()
        self.stdout.write(f"  [DEL] {total_apagados} documento(s) sintetico(s) anteriores removidos.")

        # ── 2. Garantir categorias no banco ───────────────────────────────────
        if not CategoriaAACC.objects.exists():
            self.stdout.write(self.style.WARNING(
                "  [AVISO] Nenhuma CategoriaAACC encontrada. Criando categorias de fallback..."
            ))
            for cat in CATEGORIAS_FALLBACK:
                CategoriaAACC.objects.create(**cat)
            self.stdout.write(self.style.SUCCESS(
                f"  [OK] {len(CATEGORIAS_FALLBACK)} categorias criadas."
            ))

        categorias = list(CategoriaAACC.objects.all())

        # ── 3. Selecionar alunos ──────────────────────────────────────────────
        email_filtro = options.get('aluno')
        if email_filtro:
            try:
                usuario = User.objects.get(email=email_filtro, is_aluno=True)
                perfis  = AlunoPerfil.objects.filter(usuario=usuario)
            except User.DoesNotExist:
                raise CommandError(f"Aluno '{email_filtro}' nao encontrado ou nao e aluno.")
        else:
            perfis = AlunoPerfil.objects.select_related('usuario').filter(
                usuario__is_aluno=True
            )

        if not perfis.exists():
            raise CommandError("Nenhum aluno encontrado. Execute 'seed_database' primeiro.")

        self.stdout.write(f"  [{perfis.count()} aluno(s) selecionado(s)]\n")

        # ── 4. Geracao dos documentos ─────────────────────────────────────────
        total_gerados   = 0
        total_certs     = 0
        total_decls     = 0
        qtd_fixa        = options.get('qtd')

        for perfil in perfis:
            nome_aluno = perfil.usuario.get_full_name() or perfil.usuario.username
            qtd        = qtd_fixa if qtd_fixa else random.randint(5, 8)

            self.stdout.write(f"  [DOC] {nome_aluno} ({perfil.matricula}) -- gerando {qtd} doc(s)...")

            for _ in range(qtd):
                horas       = random.choice(HORAS_POSSIVEIS)
                categoria   = random.choice(categorias)
                nome_evento = _fake.catch_phrase()

                # Geracao 100% em memoria
                pdf_bytes, tipo_doc = gerar_pdf_sintetico(nome_aluno, horas, nome_evento)

                prefixo      = 'cert' if tipo_doc == 'certificado' else 'decl'
                nome_arquivo = f"sintetico_{prefixo}_{perfil.id}_{random.randint(1000, 9999)}.pdf"

                cert = Certificado(
                    aluno=perfil,
                    categoria=categoria,
                    horas_declaradas=horas,
                    status='pendente_ocr',
                )
                cert.arquivo_pdf.save(nome_arquivo, ContentFile(pdf_bytes), save=False)
                cert.save()

                total_gerados += 1
                if tipo_doc == 'certificado':
                    total_certs += 1
                else:
                    total_decls += 1

            self.stdout.write(self.style.SUCCESS(f"    [OK] {qtd} documento(s) gerados."))

        # ── 5. Sumario ────────────────────────────────────────────────────────
        self.stdout.write(self.style.SUCCESS(
            f"\n=== Concluido! {total_gerados} doc(s) criado(s). "
            f"({total_certs} certificados + {total_decls} declaracoes) ==="
            f"\n    Status: pendente_ocr  |  Prontos para OCR Pipeline.\n"
        ))
