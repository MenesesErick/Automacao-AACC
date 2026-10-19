import logging
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from academico.models import CategoriaAACC, Curso, Eixo, MatrizCurricular, AlunoPerfil
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
                defaults={'nome': regra.nome, 'eixo': Eixo.obter(regra.eixo), 'limite_maximo_horas': teto},
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
        import random
        from django.core.files.base import ContentFile
        from academico.models import Certificado
        from academico.management.gerador_certificados import (
            montar_plano_aluno, gerar_periodo, gerar_documento_comprobatorio,
        )

        self.stdout.write(self.style.NOTICE('\nGerando certificados pendentes realistas...'))

        total = 0
        for perfil in perfis:
            meta = perfil.matriz_curricular.horas_totais_exigidas if perfil.matriz_curricular_id else 120
            rng = random.Random(perfil.id)

            if perfil.certificados.exists():
                self.stdout.write(self.style.WARNING(
                    f"  [~] {perfil.usuario.get_full_name()} ja tem certificados. Pulando."
                ))
                continue

            plano = montar_plano_aluno(meta_horas=meta, rng=rng)
            soma = 0
            for item in plano:
                slug = item["slug"]
                titulo = item["titulo"]
                horas = item["horas"]
                emissor = item["emissor"]
                estilo = item["estilo"]

                try:
                    categoria = CategoriaAACC.objects.get(codigo_slug=slug)
                except CategoriaAACC.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"  [!] Categoria '{slug}' nao encontrada. Pulando."))
                    continue

                periodo, fim = gerar_periodo(horas, rng)
                pdf_bytes, tipo_doc = gerar_documento_comprobatorio(
                    nome_aluno=perfil.usuario.get_full_name() or perfil.usuario.username,
                    cpf=perfil.usuario.cpf,
                    matricula=perfil.matricula,
                    titulo=titulo,
                    slug=slug,
                    emissor=emissor,
                    horas=horas,
                    estilo=estilo,
                    periodo=periodo,
                    data_fim=fim,
                    formato="auto",
                    rng=rng,
                )

                nome_arquivo = f"{tipo_doc}_{perfil.matricula}_{slug}.pdf"
                cert = Certificado(
                    aluno=perfil,
                    categoria=categoria,
                    titulo_atividade=titulo,
                    periodo_realizacao=periodo,
                    horas_declaradas=horas,
                    status='revisao_manual',
                    motivo_status='Documento comprobatório gerado para testes (com templates_base).',
                )
                cert.arquivo_pdf.save(nome_arquivo, ContentFile(pdf_bytes, name=nome_arquivo), save=False)
                cert.save()
                soma += horas
                total += 1

            self.stdout.write(self.style.SUCCESS(
                f"  [+] {len(plano)} cert(s) | {perfil.usuario.get_full_name()} "
                f"| Declarado: {soma}h / Meta: {meta}h"
            ))

        self.stdout.write(self.style.SUCCESS(f'\n  => {total} certificados pendentes criados.'))
