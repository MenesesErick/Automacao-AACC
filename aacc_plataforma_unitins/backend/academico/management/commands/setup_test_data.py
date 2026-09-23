import logging
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from academico.models import CategoriaAACC, Curso, MatrizCurricular, AlunoPerfil
from academico.rules.resolucao_057 import LIMITES_CATEGORIAS

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Popula o banco de dados com eixos e categorias AACC iniciais a partir da Fonte da Verdade (SEBR)'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE('Iniciando o povoamento das Categorias AACC (Resolução 057/2025)...'))

        criadas = 0
        atualizadas = 0

        for slug, regra in LIMITES_CATEGORIAS.items():
            teto = regra.teto_total if regra.teto_total is not None else 9999
            
            cat, created = CategoriaAACC.objects.update_or_create(
                codigo_slug=slug,
                defaults={
                    'nome': regra.nome,
                    'eixo': regra.eixo,
                    'limite_maximo_horas': teto,
                }
            )
            
            if created:
                criadas += 1
                self.stdout.write(self.style.SUCCESS(f"  [+] CRIADA: {cat.nome} ({cat.eixo})"))
            else:
                atualizadas += 1
                self.stdout.write(self.style.WARNING(f"  [~] ATUALIZADA: {cat.nome} ({cat.eixo})"))

        self.stdout.write(self.style.SUCCESS(f'Povoamento de categorias concluído! {criadas} criadas, {atualizadas} atualizadas.\n'))

        # ── Configurar ambiente de testes (Usuarios, Cursos e Perfis) ────────
        self.stdout.write(self.style.NOTICE('Iniciando criacao do ambiente de testes (Usuarios, Cursos, Matrizes)...'))
        User = get_user_model()

        # 1. Coordenador
        coordenador, coord_created = User.objects.get_or_create(
            username='coord@unitins.br',
            defaults={
                'first_name': 'Carlos',
                'last_name': 'Coordenador',
                'email': 'coord@unitins.br',
                'cpf': '000.000.000-00',
                'is_coordenador': True,
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if coord_created:
            coordenador.set_password('unitins2026')
            coordenador.save()
            self.stdout.write(self.style.SUCCESS('  [+] CRIADO: Usuario Coordenador (Login: coord@unitins.br / Senha: unitins2026)'))
        else:
            self.stdout.write(self.style.WARNING('  [~] MANTIDO: Usuario Coordenador ja existe.'))

        # 2. Curso e Matriz
        curso_si, curso_created = Curso.objects.get_or_create(
            codigo='SI-01',
            defaults={'nome': 'Sistemas de Informação'}
        )
        matriz_120h, matriz_created = MatrizCurricular.objects.get_or_create(
            curso=curso_si,
            ano_vigencia=2023,
            defaults={'horas_totais_exigidas': 120}
        )

        # 3. Alunos
        alunos_dados = [
            {'username': 'joao.silva@unitins.br', 'first_name': 'Joao', 'last_name': 'Silva', 'matricula': '202311001', 'cpf': '111.111.111-11'},
            {'username': 'maria.souza@unitins.br', 'first_name': 'Maria', 'last_name': 'Souza', 'matricula': '202311002', 'cpf': '222.222.222-22'}
        ]

        for dados in alunos_dados:
            user_aluno, u_created = User.objects.get_or_create(
                username=dados['username'],
                defaults={
                    'first_name': dados['first_name'],
                    'last_name': dados['last_name'],
                    'email': dados['username'],
                    'cpf': dados['cpf'],
                    'is_aluno': True,
                    'is_staff': False,
                    'is_superuser': False,
                }
            )
            if u_created:
                user_aluno.set_password('unitins2026')
                user_aluno.save()
            
            perfil, p_created = AlunoPerfil.objects.get_or_create(
                usuario=user_aluno,
                defaults={
                    'matricula': dados['matricula'],
                    'curso': curso_si,
                    'matriz_curricular': matriz_120h
                }
            )

            if u_created or p_created:
                self.stdout.write(self.style.SUCCESS(f"  [+] CRIADO: Aluno {user_aluno.get_full_name()} (Login: {dados['username']} / Senha: unitins2026) - Meta: {matriz_120h.horas_totais_exigidas}h"))
            else:
                self.stdout.write(self.style.WARNING(f"  [~] MANTIDO: Aluno {user_aluno.get_full_name()} ja existe."))

        self.stdout.write(self.style.SUCCESS('\nAmbiente de testes configurado com sucesso!'))
