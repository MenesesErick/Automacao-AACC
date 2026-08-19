import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count

from academico.models import CategoriaAACC
from academico.rules.resolucao_057 import LIMITES_CATEGORIAS

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sincroniza as categorias do banco de dados com a Resolução CONSUNI N.º 057/2025 (SEBR).'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('Iniciando sincronização de categorias com o SEBR...'))

        # Mapeamento manual de nomes antigos (substrings) para os novos slugs
        mapeamento_antigo = {
            'monitoria': 'monitoria',
            'disciplinas de outros cursos': 'disciplinas_outros_cursos',
            'projetos e oficinas': 'projetos_extensao',  # Aproximação
            'iniciação científica': 'projetos_pesquisa',  # Aproximação
            'trabalho desenvolvido em eventos': 'trabalhos_cientificos',
            'grupos de pesquisa': 'grupos_pesquisa',
            'seminários, congressos': 'seminarios_congressos',
            'cursos de extensão': 'cursos_extensao',
            'visitas técnicas': 'visitas_tecnicas',
            'organização de eventos': 'organizacao_cursos_eventos',
            'intercâmbios': 'intercambio',
            'campanhas de voluntariado': 'campanhas_voluntariado',
            'jornal informativo': 'organizacao_jornal_incubadora',
            'estágios extracurriculares': 'estagios_extracurriculares',
            'cursos de idiomas': 'idiomas_informatica',
            'campanhas da unitins': 'campanhas_unitins',
        }

        criadas = 0
        atualizadas = 0

        with transaction.atomic():
            todas_categorias = list(CategoriaAACC.objects.all())

            for slug, regra in LIMITES_CATEGORIAS.items():
                categoria_encontrada = None

                # 1. Tentar encontrar por slug (se o script já rodou antes)
                categoria_encontrada = next((c for c in todas_categorias if c.codigo_slug == slug), None)

                # 2. Tentar encontrar por nome exato ou mapeamento manual
                if not categoria_encontrada:
                    for cat in todas_categorias:
                        if cat.codigo_slug:
                            continue  # Já está vinculada a outro slug

                        nome_lower = cat.nome.lower()
                        if regra.nome.lower() == nome_lower:
                            categoria_encontrada = cat
                            break
                        
                        # Verifica mapeamento
                        mapped_slug = next((v for k, v in mapeamento_antigo.items() if k in nome_lower), None)
                        if mapped_slug == slug:
                            categoria_encontrada = cat
                            break

                limite_horas = regra.teto_total if regra.teto_total is not None else 9999

                if categoria_encontrada:
                    # Atualiza a categoria existente
                    categoria_encontrada.codigo_slug = slug
                    categoria_encontrada.nome = regra.nome
                    categoria_encontrada.eixo = regra.eixo
                    categoria_encontrada.limite_maximo_horas = limite_horas
                    categoria_encontrada.save()
                    atualizadas += 1
                    self.stdout.write(self.style.SUCCESS(f'Atualizada: {slug}'))
                else:
                    # Cria nova categoria
                    CategoriaAACC.objects.create(
                        codigo_slug=slug,
                        nome=regra.nome,
                        eixo=regra.eixo,
                        limite_maximo_horas=limite_horas
                    )
                    criadas += 1
                    self.stdout.write(self.style.SUCCESS(f'Criada: {slug}'))

            # Varredura final: O que sobrou sem slug?
            sobras = CategoriaAACC.objects.filter(codigo_slug__isnull=True) | CategoriaAACC.objects.filter(codigo_slug='')
            
            if sobras.exists():
                self.stdout.write(self.style.WARNING(f'\nEncontradas {sobras.count()} categorias antigas sem vínculo com o SEBR:'))
                for cat in sobras:
                    certificados_count = cat.certificados.count()
                    if certificados_count == 0:
                        cat.delete()
                        self.stdout.write(self.style.SUCCESS(f'  - Deletada: "{cat.nome}" (0 certificados)'))
                    else:
                        self.stdout.write(self.style.ERROR(f'  - Preservada: "{cat.nome}" (possui {certificados_count} certificados atrelados)'))

        self.stdout.write(self.style.MIGRATE_HEADING(f'\nResumo: {criadas} criadas, {atualizadas} atualizadas.'))
