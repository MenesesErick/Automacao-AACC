import django.db.models.deletion
from django.db import migrations, models
from django.utils.text import slugify


def migrar_eixos(apps, schema_editor):
    Eixo = apps.get_model("academico", "Eixo")
    Categoria = apps.get_model("academico", "CategoriaAACC")

    nomes = {"Ensino": "Ensino", "Pesquisa": "Pesquisa", "Extensao": "Extensao"}
    eixos = {}
    for chave, rotulo in nomes.items():
        eixos[chave] = Eixo.objects.get_or_create(slug=slugify(chave), defaults={"nome": rotulo})[0]

    for cat in Categoria.objects.all():
        valor = cat.eixo_legado
        eixo = eixos.get(valor) or Eixo.objects.get_or_create(
            slug=slugify(valor), defaults={"nome": valor}
        )[0]
        cat.eixo_novo_id = eixo.id
        cat.save(update_fields=["eixo_novo"])


def reverter_eixos(apps, schema_editor):
    Categoria = apps.get_model("academico", "CategoriaAACC")
    for cat in Categoria.objects.select_related("eixo_novo"):
        cat.eixo_legado = cat.eixo_novo.slug.capitalize() if cat.eixo_novo_id else "Ensino"
        cat.save(update_fields=["eixo_legado"])


class Migration(migrations.Migration):

    # Evita "pending trigger events" no PostgreSQL ao misturar dados + alteração de FK.
    atomic = False

    dependencies = [
        ("academico", "0006_add_titulo_periodo_certificado"),
    ]

    operations = [
        migrations.CreateModel(
            name="Eixo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nome", models.CharField(max_length=50, unique=True, verbose_name="Nome do Eixo")),
                ("slug", models.SlugField(max_length=50, unique=True, verbose_name="Slug")),
            ],
            options={
                "verbose_name": "Eixo Formativo",
                "verbose_name_plural": "Eixos Formativos",
                "ordering": ["id"],
            },
        ),
        migrations.RenameField("categoriaaacc", "eixo", "eixo_legado"),
        migrations.AddField(
            model_name="categoriaaacc",
            name="eixo_novo",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="categorias",
                to="academico.eixo",
            ),
        ),
        migrations.RunPython(migrar_eixos, reverter_eixos),
        migrations.RemoveField("categoriaaacc", "eixo_legado"),
        migrations.RenameField("categoriaaacc", "eixo_novo", "eixo"),
        migrations.AlterField(
            model_name="categoriaaacc",
            name="eixo",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="categorias",
                to="academico.eixo",
                verbose_name="Eixo",
            ),
        ),
    ]
