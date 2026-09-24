import logging
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from academico.models import CategoriaAACC, Curso, MatrizCurricular, AlunoPerfil
from academico.rules.resolucao_057 import LIMITES_CATEGORIAS

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Popula o banco com categorias AACC, usuarios e certificados pendentes para testes'

    def handle(self, *args, **kwargs):
        # 1. Categorias (SEBR)
        self.stdout.write(self.style.NOTICE('Sincronizando Categorias AACC (Resolucao 057/2025)...'))
        criadas = atualizadas = 0
        for slug, regra in LIMITES_CATEGORIAS.items():
            teto = regra.teto_total if regra.teto_total is not None else 9999
            _, created = CategoriaAACC.objects.update_or_create(
                codigo_slug=slug,
                defaults={'nome': regra.nome, 'eixo': regra.eixo, 'limite_maximo_horas': teto},
            )
            if created:
                criadas += 1
            else:
                atualizadas += 1
        self.stdout.write(self.style.SUCCESS(f'  -> {criadas} criadas, {atualizadas} atualizadas.\n'))

        # 2. Usuarios e Perfis
        self.stdout.write(self.style.NOTICE('Criando usuarios e perfis de aluno...'))
        User = get_user_model()

        coordenador, coord_created = User.objects.get_or_create(
            username='coord@unitins.br',
            defaults={
                'first_name': 'Carlos', 'last_name': 'Coordenador',
                'email': 'coord@unitins.br', 'cpf': '000.000.000-00',
                'is_coordenador': True, 'is_staff': True, 'is_superuser': True,
            }
        )
        if coord_created:
            coordenador.set_password('unitins2026')
            coordenador.save()
            self.stdout.write(self.style.SUCCESS('  [+] Coordenador: coord@unitins.br / unitins2026'))
        else:
            self.stdout.write(self.style.WARNING('  [~] Coordenador ja existe.'))

        curso_si, _ = Curso.objects.get_or_create(
            codigo='SI-01', defaults={'nome': 'Sistemas de Informacao'}
        )
        matriz_120h, _ = MatrizCurricular.objects.get_or_create(
            curso=curso_si, ano_vigencia=2023, defaults={'horas_totais_exigidas': 120}
        )
        matriz_180h, _ = MatrizCurricular.objects.get_or_create(
            curso=curso_si, ano_vigencia=2024, defaults={'horas_totais_exigidas': 180}
        )

        alunos_seed = [
            {'username': 'joao.silva@unitins.br',     'first_name': 'Joao',  'last_name': 'Silva',    'matricula': '202311001', 'cpf': '111.111.111-11', 'matriz': matriz_120h},
            {'username': 'maria.souza@unitins.br',    'first_name': 'Maria', 'last_name': 'Souza',    'matricula': '202311002', 'cpf': '222.222.222-22', 'matriz': matriz_120h},
            {'username': 'pedro.santos@unitins.br',   'first_name': 'Pedro', 'last_name': 'Santos',   'matricula': '202411001', 'cpf': '333.333.333-33', 'matriz': matriz_180h},
            {'username': 'ana.costa@unitins.br',      'first_name': 'Ana',   'last_name': 'Costa',    'matricula': '202411002', 'cpf': '444.444.444-44', 'matriz': matriz_180h},
            {'username': 'lucas.ferreira@unitins.br', 'first_name': 'Lucas', 'last_name': 'Ferreira', 'matricula': '202411003', 'cpf': '555.555.555-55', 'matriz': matriz_180h},
        ]

        perfis = []
        for d in alunos_seed:
            user, u_created = User.objects.get_or_create(
                username=d['username'],
                defaults={
                    'first_name': d['first_name'], 'last_name': d['last_name'],
                    'email': d['username'], 'cpf': d['cpf'],
                    'is_aluno': True, 'is_staff': False, 'is_superuser': False,
                }
            )
            if u_created:
                user.set_password('unitins2026')
                user.save()

            perfil, p_created = AlunoPerfil.objects.get_or_create(
                usuario=user,
                defaults={'matricula': d['matricula'], 'curso': curso_si, 'matriz_curricular': d['matriz']},
            )
            perfis.append(perfil)

            if u_created or p_created:
                self.stdout.write(self.style.SUCCESS(
                    f"  [+] {user.get_full_name()} | {d['username']} | Meta: {d['matriz'].horas_totais_exigidas}h"
                ))
            else:
                self.stdout.write(self.style.WARNING(f"  [~] {user.get_full_name()} ja existe."))

        # 3. Certificados Pendentes
        self._gerar_certificados(perfis)
        self.stdout.write(self.style.SUCCESS('\nAmbiente de testes pronto!'))

    def _gerar_certificados(self, perfis):
        from django.core.files.base import ContentFile
        from academico.models import Certificado

        self.stdout.write(self.style.NOTICE('\nGerando certificados pendentes...'))

        # PDF mock minimo valido em bytes (sem conteudo visual)
        PDF_MOCK = (
            b"%PDF-1.0\n1 0 obj<</Type /Catalog /Pages 2 0 R>>endobj "
            b"2 0 obj<</Type /Pages /Kids [3 0 R] /Count 1>>endobj "
            b"3 0 obj<</Type /Page /MediaBox [0 0 612 792] /Parent 2 0 R>>endobj "
            b"xref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n"
            b"0000000058 00000 n\n0000000115 00000 n\n"
            b"trailer<</Size 4 /Root 1 0 R>>\nstartxref\n190\n%%EOF"
        )

        # (slug, titulo, periodo, horas_declaradas)
        LOTES = {
            120: [
                ('escola_linguas',        'Ingles Intermediario - Escola de Linguas Unitins',          '01/08/2025 a 30/11/2025',    40),
                ('cursos_curta_duracao',  'Python para Ciencia de Dados - FIAP Online',               'Marco de 2025',              30),
                ('seminarios_congressos', 'Semana Academica de Sistemas de Informacao 2025',           '14 a 17 de outubro de 2025', 20),
                ('projetos_pesquisa',     'IC: Inteligencia Artificial Aplicada a Saude Publica',      '01/03/2025 a 30/06/2025',    20),
                ('grupos_pesquisa',       'Grupo de Estudos em Computacao em Nuvem - UNITINS',         'Fevereiro a Julho de 2025',  20),
            ],
            180: [
                ('escola_linguas',        'Ingles Avancado - Cambridge Online',                        '01/02/2025 a 30/06/2025',    40),
                ('cursos_curta_duracao',  'React e Node.js: Desenvolvimento Full-Stack',               'Abril de 2025',              30),
                ('pibid',                 'PIBID Unitins 2025 - Iniciacao a Docencia',                 '01/03/2025 a 30/11/2025',    40),
                ('projetos_pesquisa',     'Otimizacao de Banco de Dados Distribuidos',                 '01/04/2025 a 31/07/2025',    30),
                ('seminarios_congressos', 'CNMAC 2025 - Congresso Nacional de Matematica Aplicada',   '08 a 12 de setembro de 2025', 20),
                ('projetos_extensao',     'Unitins na Comunidade: Inclusao Digital para Idosos',       '01/05/2025 a 15/08/2025',    20),
            ],
        }

        total = 0
        for perfil in perfis:
            meta = perfil.matriz_curricular.horas_totais_exigidas
            lote = LOTES.get(meta, LOTES[180])

            if perfil.certificados.exists():
                self.stdout.write(self.style.WARNING(
                    f"  [~] {perfil.usuario.get_full_name()} ja tem certificados. Pulando."
                ))
                continue

            soma = 0
            for slug, titulo, periodo, horas in lote:
                try:
                    categoria = CategoriaAACC.objects.get(codigo_slug=slug)
                except CategoriaAACC.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"  [!] Categoria '{slug}' nao encontrada. Pulando."))
                    continue

                nome_arquivo = f"mock_{perfil.matricula}_{slug}.pdf"
                cert = Certificado(
                    aluno=perfil,
                    categoria=categoria,
                    titulo_atividade=titulo,
                    periodo_realizacao=periodo,
                    horas_declaradas=horas,
                    status='revisao_manual',
                    motivo_status='Documento gerado automaticamente para testes.',
                )
                cert.arquivo_pdf.save(nome_arquivo, ContentFile(PDF_MOCK, name=nome_arquivo), save=False)
                cert.save()
                soma += horas
                total += 1

            self.stdout.write(self.style.SUCCESS(
                f"  [+] {len(lote)} cert(s) | {perfil.usuario.get_full_name()} "
                f"| Declarado: {soma}h / Meta: {meta}h"
            ))

        self.stdout.write(self.style.SUCCESS(f'\n  => {total} certificados pendentes criados.'))
