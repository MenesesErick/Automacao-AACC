import os
import sys
import django

# Define o ambiente Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aacc_core.settings')
django.setup()

from academico.models import CategoriaAACC
from academico.rules.resolucao_057 import LIMITES_CATEGORIAS
from django.db.models import ProtectedError

print("--- Iniciando Sincronizacao de Categorias ---")

# 1. Criar ou Atualizar categorias válidas
print("\n[Etapa 1] Sincronizando regras da Resolucao 057...")
for slug, regra in LIMITES_CATEGORIAS.items():
    # Para categorias sem teto total (None), definimos um valor alto figurativo
    # (já que a validação real ocorre no SEBR e não no banco)
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
        print(f"  [+] CRIADA: {regra.nome} ({slug})")
    else:
        pass # print(f"  [~] ATUALIZADA: {regra.nome} ({slug})")

# 2. Remover categorias obsoletas (ex: "Experiência Profissional")
print("\n[Etapa 2] Removendo categorias obsoletas no banco...")
rule_slugs = set(LIMITES_CATEGORIAS.keys())

for cat in CategoriaAACC.objects.all():
    if not cat.codigo_slug or cat.codigo_slug not in rule_slugs:
        try:
            nome_cat = cat.nome
            cat.delete()
            print(f"  [-] REMOVIDA (Obsoleta): {nome_cat}")
        except ProtectedError:
            cat.nome = f"[OBSOLETA] {cat.nome}"
            cat.codigo_slug = f"obsoleta_{cat.id}"
            cat.save()
            print(f"  [!] PROTEGIDA (Desativada): A categoria '{nome_cat}' foi marcada como obsoleta pois há certificados atrelados a ela.")

print("\n--- Sincronizacao Concluida ---")
