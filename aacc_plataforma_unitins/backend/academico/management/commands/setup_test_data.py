import logging
from django.core.management.base import BaseCommand
from academico.models import CategoriaAACC
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

        self.stdout.write(self.style.SUCCESS(f'Povoamento concluído! {criadas} criadas, {atualizadas} atualizadas.'))
