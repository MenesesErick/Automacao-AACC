"""
academico/management/commands/gerar_dataset.py

Fábrica de Certificados Sintéticos — para validação do OCR e do Motor de Regras.

Gera PDFs desafiadores com alta variabilidade de texto e layout diretamente
em memória (io.BytesIO), sem qualquer escrita temporária em disco.

Segurança/Idempotência:
    Apaga APENAS certificados com status='pendente_ocr' cujo nome de arquivo
    contenha 'sintetico'. Nunca toca em dados reais ou aprovados.

Uso:
    python manage.py gerar_dataset
    python manage.py gerar_dataset --aluno erick@unitins.br   # apenas 1 aluno
    python manage.py gerar_dataset --qtd 10                    # 10 certs por aluno
"""

import io
import os
import random

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError

from faker import Faker
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm

from academico.models import AlunoPerfil, CategoriaAACC, Certificado

User = get_user_model()

# ── Constantes ────────────────────────────────────────────────────────────────
PAGE_W, PAGE_H = A4  # 595.28 x 841.89 pts
HORAS_POSSIVEIS = [5, 10, 20, 30, 40, 50]

# Categorias mínimas de fallback caso o banco esteja vazio
CATEGORIAS_FALLBACK = [
    {'nome': 'Monitoria e Tutoria',           'eixo': 'Ensino',   'limite_maximo_horas': 40},
    {'nome': 'Iniciação Científica',           'eixo': 'Pesquisa', 'limite_maximo_horas': 40},
    {'nome': 'Projetos de Extensão Comunitária', 'eixo': 'Extensao', 'limite_maximo_horas': 40},
]


# ─────────────────────────────────────────────────────────────────────────────
#  Motor de Desenho — 100% em memória
# ─────────────────────────────────────────────────────────────────────────────

def _frase_certificacao(nome_aluno: str, horas: int, nome_evento: str) -> str:
    """Sorteia uma frase de certificação com variações de estrutura (stress para Regex)."""
    frases = [
        f"Certificamos que {nome_aluno} participou do {nome_evento} "
        f"com carga horária de {horas}h.",

        f"Declaramos para os devidos fins que {nome_aluno} concluiu "
        f"{horas} horas totais no evento {nome_evento}.",

        f"{nome_evento} — Concedido a {nome_aluno}. Total de Horas: {horas} hrs.",
    ]
    return random.choice(frases)


def gerar_pdf_sintetico(nome_aluno: str, horas: int, nome_evento: str) -> bytes:
    """
    Gera um PDF sintético inteiramente em memória (sem I/O em disco).

    Sorteia aleatoriamente entre 3 layouts para estressar o motor de OCR e Regex:
        Layout 1 — Padrão:     Título centralizado, corpo justificado.
        Layout 2 — Caótico:    Fontes mistas, alinhamento à direita.
        Layout 3 — Minimalista: Tudo em letra pequena no rodapé.

    Returns:
        bytes: conteúdo raw do PDF pronto para persistência.
    """
    buffer = io.BytesIO()
    c = rl_canvas.Canvas(buffer, pagesize=A4)

    layout = random.randint(1, 3)
    frase  = _frase_certificacao(nome_aluno, horas, nome_evento)

    # ── Carimbo de organização (presente em todos os layouts) ────────────────
    entidade = random.choice([
        "Universidade Federal do Tocantins — UNITINS",
        "UNITINS / Pró-Reitoria de Extensão",
        "Coordenação de Atividades Acadêmico-Científico-Culturais",
        "Instituto de Inovação e Tecnologia",
    ])

    if layout == 1:
        # ── Layout 1: Padrão / Institucional ─────────────────────────────────
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(PAGE_W / 2, PAGE_H - 4 * cm, "CERTIFICADO DE PARTICIPAÇÃO")

        c.setFont("Helvetica", 11)
        c.drawCentredString(PAGE_W / 2, PAGE_H - 5.5 * cm, entidade)

        c.setFont("Helvetica", 10)
        # Quebra manual de linha para caber na página
        palavras = frase.split()
        linhas, linha_atual = [], []
        for palavra in palavras:
            teste = ' '.join(linha_atual + [palavra])
            if c.stringWidth(teste, "Helvetica", 10) < PAGE_W - 6 * cm:
                linha_atual.append(palavra)
            else:
                linhas.append(' '.join(linha_atual))
                linha_atual = [palavra]
        if linha_atual:
            linhas.append(' '.join(linha_atual))

        y = PAGE_H - 8 * cm
        for linha in linhas:
            c.drawCentredString(PAGE_W / 2, y, linha)
            y -= 0.6 * cm

        c.setFont("Helvetica-Oblique", 9)
        c.drawCentredString(PAGE_W / 2, 3 * cm, f"Carga Horária Total: {horas} horas")

    elif layout == 2:
        # ── Layout 2: Caótico / Fontes mistas, alinhamento à direita ─────────
        c.setFont("Times-Bold", 18)
        c.drawRightString(PAGE_W - 2 * cm, PAGE_H - 3 * cm, "CERTIFICADO")

        c.setFont("Helvetica-Oblique", 9)
        c.drawRightString(PAGE_W - 2 * cm, PAGE_H - 4 * cm, entidade)

        c.setFont("Times-Roman", 11)
        palavras = frase.split()
        linhas, linha_atual = [], []
        for palavra in palavras:
            teste = ' '.join(linha_atual + [palavra])
            if c.stringWidth(teste, "Times-Roman", 11) < PAGE_W - 5 * cm:
                linha_atual.append(palavra)
            else:
                linhas.append(' '.join(linha_atual))
                linha_atual = [palavra]
        if linha_atual:
            linhas.append(' '.join(linha_atual))

        y = PAGE_H - 6 * cm
        for linha in linhas:
            c.drawRightString(PAGE_W - 2 * cm, y, linha)
            y -= 0.65 * cm

        c.setFont("Helvetica-Bold", 10)
        c.drawRightString(PAGE_W - 2 * cm, 5 * cm, f"Horas: {horas}h")

    else:
        # ── Layout 3: Minimalista / Tudo em rodapé com letra pequena ─────────
        c.setFont("Helvetica", 7)
        c.drawString(1.5 * cm, 4 * cm, entidade)
        c.drawString(1.5 * cm, 3.3 * cm, frase[:120])         # trunca para caber
        if len(frase) > 120:
            c.drawString(1.5 * cm, 2.7 * cm, frase[120:240])
        c.drawString(1.5 * cm, 2.1 * cm, f"Horas: {horas}h")

    c.showPage()
    c.save()

    pdf_bytes = buffer.getvalue()
    buffer.close()   # libera memória imediatamente (sem memory leak)
    return pdf_bytes


# ─────────────────────────────────────────────────────────────────────────────
#  Comando Django
# ─────────────────────────────────────────────────────────────────────────────

class Command(BaseCommand):
    help = (
        "Gera certificados PDF sintéticos em memória para validação do OCR "
        "e do Motor de Regras. Seguro para execução em ambientes com dados reais "
        "(apaga apenas registos 'sintetico' + 'pendente_ocr')."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--aluno',
            type=str,
            default=None,
            help="Email do aluno específico (omita para processar todos os alunos).",
        )
        parser.add_argument(
            '--qtd',
            type=int,
            default=None,
            help="Quantidade fixa de certificados por aluno (padrão: 5 a 8 aleatórios).",
        )

    def handle(self, *args, **options):
        fake = Faker('pt_BR')

        self.stdout.write(self.style.MIGRATE_HEADING(
            "\n=== Fabrica de Certificados Sinteticos ==="
        ))

        # ── 1. Limpeza segura e idempotente ───────────────────────────────────
        qs_sinteticos = Certificado.objects.filter(
            status='pendente_ocr',
            arquivo_pdf__icontains='sintetico',
        )
        total_apagados = qs_sinteticos.count()
        qs_sinteticos.delete()
        self.stdout.write(f"  [DEL] {total_apagados} certificado(s) sintetico(s) anteriores removidos.")

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
                perfis = AlunoPerfil.objects.filter(usuario=usuario)
            except User.DoesNotExist:
                raise CommandError(f"Aluno com email '{email_filtro}' não encontrado ou não é aluno.")
        else:
            perfis = AlunoPerfil.objects.select_related('usuario').filter(
                usuario__is_aluno=True
            )

        if not perfis.exists():
            raise CommandError("Nenhum aluno encontrado. Execute 'seed_database' primeiro.")

        self.stdout.write(f"  [{perfis.count()} aluno(s) selecionado(s)]\n")

        # ── 4. Geração dos certificados ───────────────────────────────────────
        total_gerados = 0
        qtd_fixa = options.get('qtd')

        for perfil in perfis:
            nome_aluno = perfil.usuario.get_full_name() or perfil.usuario.username
            qtd = qtd_fixa if qtd_fixa else random.randint(5, 8)

            self.stdout.write(f"  [PDF] {nome_aluno} ({perfil.matricula}) -- gerando {qtd} PDF(s)...")

            for _ in range(qtd):
                horas       = random.choice(HORAS_POSSIVEIS)
                categoria   = random.choice(categorias)
                nome_evento = fake.catch_phrase()   # ex: "Inovação Integrada de Plataforma"

                # Geração 100% em memória — sem disco temporário
                pdf_bytes = gerar_pdf_sintetico(nome_aluno, horas, nome_evento)

                nome_arquivo = f"sintetico_{perfil.id}_{random.randint(1000, 9999)}.pdf"

                cert = Certificado(
                    aluno=perfil,
                    categoria=categoria,
                    horas_declaradas=horas,
                    status='pendente_ocr',
                )
                # save=False para não tentar salvar o objeto sem o arquivo ainda
                cert.arquivo_pdf.save(nome_arquivo, ContentFile(pdf_bytes), save=False)
                cert.save()

                total_gerados += 1

            self.stdout.write(self.style.SUCCESS(f"    [OK] {qtd} certificado(s) gerados."))

        # ── 5. Sumário ────────────────────────────────────────────────────────
        self.stdout.write(self.style.SUCCESS(
            f"\n=== Concluido! {total_gerados} certificado(s) sintetico(s) criados. ==="
            f"\n    Status: pendente_ocr  |  Prontos para OCR Pipeline.\n"
        ))
