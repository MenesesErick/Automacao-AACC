"""
academico/management/commands/seed_database.py

Cria uma massa de dados (seed) rica para testes de UI/UX.
Gera multiplos alunos e uma grande variedade de certificados com diferentes
status (aprovado, rejeitado, revisao_manual, pendente_ocr).
"""

import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model

from academico.models import Curso, MatrizCurricular, AlunoPerfil, CategoriaAACC, Certificado

User = get_user_model()


class Command(BaseCommand):
    help = "Popula o banco com multiplos alunos e certificados para teste de UI/UX."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("=== Iniciando Seed do Banco de Dados ==="))

        # -- 1. Garantir Curso e Matriz (Sistemas de Informacao) --
        curso, _ = Curso.objects.get_or_create(
            codigo='SI',
            defaults={'nome': 'Sistemas de Informacao'},
        )
        matriz, _ = MatrizCurricular.objects.get_or_create(
            curso=curso,
            ano_vigencia=2022,
            defaults={'horas_totais_exigidas': 180},
        )
        self.stdout.write(f"  [OK] Curso e Matriz verificados: {curso.nome}")

        # -- 2. Pegar categorias --
        categorias = list(CategoriaAACC.objects.all())
        if not categorias:
            self.stdout.write(self.style.ERROR("  [ERRO] Nenhuma categoria encontrada! Rode 'popular_categorias' primeiro."))
            return

        # -- 3. Alunos Ficticios --
        alunos_data = [
            {'email': 'joao@unitins.br', 'nome': 'Joao', 'sobrenome': 'Silva', 'matricula': '2023001SI'},
            {'email': 'maria@unitins.br', 'nome': 'Maria', 'sobrenome': 'Oliveira', 'matricula': '2023002SI'},
            {'email': 'pedro@unitins.br', 'nome': 'Pedro', 'sobrenome': 'Santos', 'matricula': '2023003SI'},
            {'email': 'ana@unitins.br', 'nome': 'Ana', 'sobrenome': 'Costa', 'matricula': '2023004SI'},
            {'email': 'lucas@unitins.br', 'nome': 'Lucas', 'sobrenome': 'Ferreira', 'matricula': '2023005SI'},
            {'email': 'julia@unitins.br', 'nome': 'Julia', 'sobrenome': 'Almeida', 'matricula': '2023006SI'},
        ]

        # Template para o PDF falso em memoria
        pdf_content = b"%PDF-1.4\n%Fake PDF for UI Testing"

        for ad in alunos_data:
            user, created = User.objects.get_or_create(
                username=ad['email'],
                defaults={
                    'email': ad['email'],
                    'first_name': ad['nome'],
                    'last_name': ad['sobrenome'],
                    'is_aluno': True,
                    'is_coordenador': False,
                    'cpf': f"{random.randint(100,999)}.{random.randint(100,999)}.{random.randint(100,999)}-{random.randint(10,99)}",
                }
            )
            if created:
                user.set_password('aluno123')
                user.save()

            perfil, _ = AlunoPerfil.objects.get_or_create(
                usuario=user,
                defaults={
                    'matricula': ad['matricula'],
                    'curso': curso,
                    'matriz_curricular': matriz,
                }
            )
            self.stdout.write(self.style.SUCCESS(f"  [OK] Aluno processado: {ad['nome']} ({ad['email']})"))

            # -- 4. Certificados Ficticios para o Aluno --
            # Gerar entre 5 a 10 certificados
            qtd_certificados = random.randint(5, 10)
            certificados_criados = 0

            for i in range(qtd_certificados):
                categoria = random.choice(categorias)
                horas_declaradas = Decimal(str(random.choice([10, 20, 30, 40, 50, 60])))
                
                # Sorteio do status para criar variedade
                status_sorteio = random.choices(
                    ['aprovado', 'rejeitado', 'revisao_manual', 'pendente_ocr'],
                    weights=[0.5, 0.2, 0.2, 0.1]
                )[0]

                horas_computadas = None
                horas_descartadas = 0
                motivo = ""
                confianca_ocr = None

                if status_sorteio == 'aprovado':
                    horas_computadas = int(horas_declaradas)
                    confianca_ocr = Decimal(str(random.randint(85, 99)))
                    motivo = "Aprovado via OCR e Motor de Regras."
                elif status_sorteio == 'rejeitado':
                    horas_computadas = 0
                    horas_descartadas = int(horas_declaradas)
                    motivo = "Teto maximo da categoria ja foi atingido."
                    confianca_ocr = Decimal(str(random.randint(85, 99)))
                elif status_sorteio == 'revisao_manual':
                    horas_computadas = None
                    confianca_ocr = Decimal(str(random.randint(40, 65)))
                    motivo = f"Confianca OCR muito baixa ({confianca_ocr}%). Verificacao manual necessaria."
                elif status_sorteio == 'pendente_ocr':
                    horas_computadas = None
                    motivo = ""

                # Salvar via ORM
                certificado = Certificado(
                    aluno=perfil,
                    categoria=categoria,
                    horas_declaradas=horas_declaradas,
                    horas_validadas_ocr=int(horas_declaradas) if status_sorteio != 'pendente_ocr' else None,
                    horas_computadas_final=horas_computadas,
                    horas_descartadas=horas_descartadas,
                    indice_confianca_ocr=confianca_ocr,
                    status=status_sorteio,
                    motivo_status=motivo,
                    texto_extraido_ocr="TEXTO FAKE OCR EXTRAIDO" if status_sorteio != 'pendente_ocr' else "",
                )
                
                # Salvar o arquivo
                file_name = f"dummy_{perfil.matricula}_{i}.pdf"
                certificado.arquivo_pdf.save(file_name, ContentFile(pdf_content), save=False)
                certificado.save()
                
                # Se for aprovado ou revisao manual, gerar log
                if status_sorteio in ['aprovado', 'rejeitado', 'revisao_manual']:
                    from academico.models import RuleValidationLog
                    RuleValidationLog.objects.create(
                        certificado=certificado,
                        usuario_responsavel=None,
                        regra_aplicada=f"Teto: {categoria.limite_maximo_horas}h ({categoria.nome})",
                        justificativa=motivo,
                        horas_enviadas=int(horas_declaradas),
                        horas_computadas=horas_computadas or 0,
                        horas_descartadas=horas_descartadas,
                    )
                
                certificados_criados += 1

            self.stdout.write(f"    -> {certificados_criados} certificados gerados para {ad['nome']}")

        self.stdout.write(self.style.SUCCESS("\n[OK] Banco de dados populado com sucesso para testes de UI/UX!"))
