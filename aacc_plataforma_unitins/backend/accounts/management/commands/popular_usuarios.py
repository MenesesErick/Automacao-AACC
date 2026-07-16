"""
accounts/management/commands/popular_usuarios.py

Cria os utilizadores de teste da plataforma AACC usando get_or_create
para ser idempotente (pode ser executado várias vezes com segurança).

Uso:
    python manage.py popular_usuarios
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from academico.models import AlunoPerfil, Curso, MatrizCurricular

User = get_user_model()


class Command(BaseCommand):
    help = "Popula utilizadores de teste: 1 coordenador e 1 aluno com AlunoPerfil."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("=== Populando utilizadores de teste ==="))

        # -- 1. Coordenador --------------------------------------------------
        coord, created = User.objects.get_or_create(
            username='coord@unitins.br',
            defaults={
                'email':          'coord@unitins.br',
                'first_name':     'Carlos',
                'last_name':      'Coordenador',
                'is_coordenador': True,
                'is_aluno':       False,
                'cpf':            '000.000.000-00',
            },
        )
        if created:
            coord.set_password('admin123')
            coord.save()
            self.stdout.write(self.style.SUCCESS("  [OK] Coordenador criado: coord@unitins.br / admin123"))
        else:
            self.stdout.write(self.style.WARNING("  [--] Coordenador ja existe, ignorado."))

        # -- 2. Curso e Matriz (dependencia do AlunoPerfil) ------------------
        curso, _ = Curso.objects.get_or_create(
            codigo='SI',
            defaults={'nome': 'Sistemas de Informacao'},
        )
        self.stdout.write(f"  [OK] Curso: {curso.nome} ({curso.codigo})")

        matriz, _ = MatrizCurricular.objects.get_or_create(
            curso=curso,
            ano_vigencia=2022,
            defaults={'horas_totais_exigidas': 180},
        )
        self.stdout.write(f"  [OK] Matriz: {matriz.ano_vigencia} - {matriz.horas_totais_exigidas}h")

        # -- 3. Aluno --------------------------------------------------------
        aluno_user, created = User.objects.get_or_create(
            username='erick@unitins.br',
            defaults={
                'email':      'erick@unitins.br',
                'first_name': 'Erick',
                'last_name':  'Meneses',
                'is_aluno':   True,
                'is_coordenador': False,
                'cpf':        '111.111.111-11',
            },
        )
        if created:
            aluno_user.set_password('aluno123')
            aluno_user.save()
            self.stdout.write(self.style.SUCCESS("  [OK] Aluno criado: erick@unitins.br / aluno123"))
        else:
            self.stdout.write(self.style.WARNING("  [--] Aluno ja existe, ignorado."))

        # -- 4. AlunoPerfil --------------------------------------------------
        perfil, perfil_criado = AlunoPerfil.objects.get_or_create(
            usuario=aluno_user,
            defaults={
                'matricula':         '2022001SI',
                'curso':             curso,
                'matriz_curricular': matriz,
            },
        )
        if perfil_criado:
            self.stdout.write(self.style.SUCCESS(f"  [OK] AlunoPerfil criado: matricula {perfil.matricula}"))
        else:
            self.stdout.write(self.style.WARNING("  [--] AlunoPerfil ja existe, ignorado."))

        self.stdout.write(self.style.SUCCESS("\n[OK] Utilizadores de teste prontos!"))
        self.stdout.write("\n  Login Coordenador: coord@unitins.br  |  Senha: admin123")
        self.stdout.write("  Login Aluno:       erick@unitins.br  |  Senha: aluno123\n")
