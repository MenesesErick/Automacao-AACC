import logging
from django.core.management.base import BaseCommand
from academico.models import CategoriaAACC

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Popula o banco de dados com eixos e categorias AACC iniciais'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE('Iniciando o povoamento das Categorias AACC...'))

        categorias_iniciais = [
            {
                'nome': 'Disciplinas cursadas em outros cursos',
                'eixo': 'Ensino',
                'codigo_slug': 'disciplinas_outros_cursos',
                'limite_maximo_horas': 90,
            },
            {
                'nome': 'Projetos de pesquisa',
                'eixo': 'Pesquisa',
                'codigo_slug': 'projetos_pesquisa',
                'limite_maximo_horas': 100,
            },
            {
                'nome': 'Cursos de extensão e nivelamento',
                'eixo': 'Extensao',
                'codigo_slug': 'cursos_extensao',
                'limite_maximo_horas': 60,
            },
        ]

        for cat_data in categorias_iniciais:
            cat, created = CategoriaAACC.objects.get_or_create(
                codigo_slug=cat_data['codigo_slug'],
                defaults={
                    'nome': cat_data['nome'],
                    'eixo': cat_data['eixo'],
                    'limite_maximo_horas': cat_data['limite_maximo_horas']
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f"Categoria criada: {cat.nome} ({cat.eixo})"))
            else:
                self.stdout.write(self.style.WARNING(f"Categoria ja existe: {cat.nome} ({cat.eixo})"))

        self.stdout.write(self.style.SUCCESS('Povoamento inicial concluido com sucesso!'))
