"""
Management Command: popular_categorias
App: academico

Popula a tabela CategoriaAACC com todas as atividades e seus respectivos
tetos de horas, conforme definido pela Resolução CONSUNI N.º 057.

Uso:
    python manage.py popular_categorias
"""

from django.core.management.base import BaseCommand

from academico.models import CategoriaAACC


CATEGORIAS: list[dict] = [
    # ─────────────────────────────── EIXO: ENSINO ────────────────────────────
    {
        "nome": "Monitoria reconhecida pela UNITINS e/ou voluntária",
        "eixo": "Ensino",
        "limite_maximo_horas": 40,
    },
    {
        "nome": "Disciplinas de outros cursos",
        "eixo": "Ensino",
        "limite_maximo_horas": 60,
    },
    {
        "nome": "Projetos e oficinas temáticas",
        "eixo": "Ensino",
        "limite_maximo_horas": 30,
    },
    {
        "nome": "Experiência Profissional",
        "eixo": "Ensino",
        "limite_maximo_horas": 30,
    },
    # ─────────────────────────────── EIXO: PESQUISA ──────────────────────────
    {
        "nome": "Iniciação científica",
        "eixo": "Pesquisa",
        "limite_maximo_horas": 60,
    },
    {
        "nome": "Trabalho desenvolvido em eventos científicos/publicações",
        "eixo": "Pesquisa",
        "limite_maximo_horas": 45,
    },
    {
        "nome": "Participação em grupos de pesquisa",
        "eixo": "Pesquisa",
        "limite_maximo_horas": 60,
    },
    # ─────────────────────────────── EIXO: EXTENSÃO ──────────────────────────
    {
        "nome": "Participação em seminários, congressos, encontros estudantis",
        "eixo": "Extensao",
        "limite_maximo_horas": 60,
    },
    {
        "nome": "Participação em cursos de extensão e atualização",
        "eixo": "Extensao",
        "limite_maximo_horas": 40,
    },
    {
        "nome": "Visitas técnicas programadas ou viagens de estudo",
        "eixo": "Extensao",
        "limite_maximo_horas": 20,
    },
    {
        "nome": "Organização de eventos científicos internos/externos",
        "eixo": "Extensao",
        "limite_maximo_horas": 20,
    },
    {
        "nome": "Intercâmbios institucionais ou culturais",
        "eixo": "Extensao",
        "limite_maximo_horas": 20,
    },
    {
        "nome": "Campanhas de voluntariado ou programas de ação social",
        "eixo": "Extensao",
        "limite_maximo_horas": 20,
    },
    {
        "nome": "Jornal informativo, home page, incubadora",
        "eixo": "Extensao",
        "limite_maximo_horas": 20,
    },
    {
        "nome": "Estágios extracurriculares",
        "eixo": "Extensao",
        "limite_maximo_horas": 40,
    },
    {
        "nome": "Cursos de idiomas, comunicação, expressão e informática",
        "eixo": "Extensao",
        "limite_maximo_horas": 30,
    },
    {
        "nome": "Participação/organização em campanhas da UNITINS",
        "eixo": "Extensao",
        "limite_maximo_horas": 15,
    },
]


class Command(BaseCommand):
    """
    Popula a tabela CategoriaAACC com as atividades definidas pela
    Resolução CONSUNI N.º 057.

    Utiliza get_or_create para garantir idempotência: o comando pode ser
    executado múltiplas vezes sem duplicar registros.
    """

    help = "Popula a tabela CategoriaAACC com as atividades da Resolução CONSUNI 057"

    def handle(self, *args, **options) -> None:
        self.stdout.write(
            self.style.MIGRATE_HEADING(
                "\nPopulando CategoriaAACC - Resolucao CONSUNI N.o 057\n"
            )
        )

        criadas: int = 0
        existentes: int = 0

        for dados in CATEGORIAS:
            obj, created = CategoriaAACC.objects.get_or_create(
                nome=dados["nome"],
                eixo=dados["eixo"],
                defaults={"limite_maximo_horas": dados["limite_maximo_horas"]},
            )

            if created:
                criadas += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  [CRIADO]   [{obj.eixo:8}] {obj.nome} "
                        f"({obj.limite_maximo_horas}h)"
                    )
                )
            else:
                existentes += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"  [JA EXISTE] [{obj.eixo:8}] {obj.nome}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nConcluido: {criadas} categoria(s) criada(s), "
                f"{existentes} ja existia(m).\n"
            )
        )
