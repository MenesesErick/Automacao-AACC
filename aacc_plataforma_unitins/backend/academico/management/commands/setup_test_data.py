import logging
import os
import re
from decimal import Decimal
from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model

from academico.models import (
    CategoriaAACC, Curso, Eixo, MatrizCurricular, AlunoPerfil,
    CoordenadorPerfil, Certificado, RuleValidationLog, Requerimento, Notificacao
)
from academico.rules.resolucao_057 import LIMITES_CATEGORIAS
from academico.services.ocr_service import processar_pdf
from academico.management.gerador_certificados import (
    montar_plano_aluno, gerar_periodo, gerar_documento_comprobatorio,
)

logger = logging.getLogger(__name__)


def extrair_metadados_documento(texto: str, titulo_fallback: str, periodo_fallback: str):
    """
    Simula a extração do Copiloto de Metadados (AnalisePreviaView):
    utiliza regex de aspas e cascata de datas sobre o texto extraído do documento.
    """
    texto_limpo = re.sub(r'\s+', ' ', texto or '')

    # 1. Título por gatilho de aspas ou vírgula
    match_aspas = re.search(
        r"(?:participou do\(a\)|concluiu o curso de|evento)\s*[\"“'](.*?)[\"”']",
        texto_limpo,
        re.IGNORECASE,
    )
    match_virgula = re.search(
        r"(?:participou do\(a\)|concluiu o curso de)\s+([A-ZÀ-Úa-zà-ú\s]{10,100})[,(]",
        texto_limpo,
        re.IGNORECASE,
    )

    if match_aspas:
        titulo_sugerido = match_aspas.group(1).strip()
    elif match_virgula:
        titulo_sugerido = match_virgula.group(1).strip()
    else:
        titulo_sugerido = titulo_fallback

    # 2. Período por cascata de 5 níveis
    padroes_data = [
        r"(\d{2}/\d{2}/\d{4}\s*(?:a|à|-)\s*\d{2}/\d{2}/\d{4})",
        r"(\d{1,2}\s+de\s+[a-zA-ZçÇ]+\s+(?:a|à|-)\s+\d{1,2}\s+de\s+[a-zA-ZçÇ]+\s+de\s+\d{4})",
        r"(\d{1,2}\s*(?:a|à|-)\s*\d{1,2}\s+de\s+[a-zA-ZçÇ]+\s+de\s+\d{4})",
        r"(\d{1,2}\s+de\s+[a-zA-ZçÇ]+\s+de\s+\d{4})",
        r"(\d{2}/\d{2}/\d{4})",
    ]

    periodo_sugerido = ""
    for padrao in padroes_data:
        m = re.search(padrao, texto_limpo, re.IGNORECASE)
        if m:
            periodo_sugerido = m.group(1).replace('\n', ' ').strip()
            break

    if not periodo_sugerido:
        periodo_sugerido = periodo_fallback

    return titulo_sugerido[:255], periodo_sugerido[:100]


class Command(BaseCommand):
    help = 'Popula o banco com categorias AACC, usuarios, coordenador vinculado e certificados realistas pendentes'

    def handle(self, *args, **kwargs):
        # 0. Limpeza Prévia de Certificados e Notificações
        self.stdout.write(self.style.NOTICE('Limpando certificados, requerimentos e notificacoes anteriores...'))
        
        # Deleta registros do banco
        num_logs, _ = RuleValidationLog.objects.all().delete()
        num_reqs, _ = Requerimento.objects.all().delete()
        num_certs, _ = Certificado.objects.all().delete()
        num_notifs, _ = Notificacao.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(
            f'  -> Deletados: {num_certs} certificados, {num_logs} logs, {num_reqs} requerimentos, {num_notifs} notificacoes.'
        ))

        # Limpeza física de arquivos PDF de upload (preservando templates_base intacto!)
        for subpasta in ['uploads_alunos', 'certificados', 'requerimentos_gerados']:
            dir_path = os.path.join(settings.MEDIA_ROOT, subpasta)
            if os.path.exists(dir_path):
                removidos = 0
                for arq in os.listdir(dir_path):
                    if arq.lower().endswith('.pdf'):
                        caminho_arq = os.path.join(dir_path, arq)
                        try:
                            os.remove(caminho_arq)
                            removidos += 1
                        except Exception as e:
                            logger.warning(f"Erro ao remover arquivo {arq}: {e}")
                self.stdout.write(self.style.SUCCESS(f'  -> {removidos} arquivos PDF removidos de media/{subpasta}/.'))

        # 1. Categorias (SEBR)
        self.stdout.write(self.style.NOTICE('\nSincronizando Categorias AACC (Resolucao 057/2025)...'))
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

        # 2. Cursos e Matrizes
        curso_si, _ = Curso.objects.get_or_create(
            codigo='SI-01', defaults={'nome': 'Sistemas de Informacao'}
        )
        matriz_120h, _ = MatrizCurricular.objects.get_or_create(
            curso=curso_si, ano_vigencia=2023, defaults={'horas_totais_exigidas': 120}
        )
        matriz_180h, _ = MatrizCurricular.objects.get_or_create(
            curso=curso_si, ano_vigencia=2024, defaults={'horas_totais_exigidas': 180}
        )

        # 3. Usuarios do Sistema (Admin, Coordenador, Alunos)
        self.stdout.write(self.style.NOTICE('Configurando contas e perfis de usuarios...'))
        User = get_user_model()

        # Admin do Sistema
        admin_user, admin_created = User.objects.get_or_create(
            username='admin@unitins.br',
            defaults={
                'first_name': 'Administrador', 'last_name': 'Sistêmico',
                'email': 'admin@unitins.br', 'cpf': '999.999.999-99',
                'is_staff': True, 'is_superuser': True, 'is_coordenador': False, 'is_aluno': False,
            }
        )
        admin_user.set_password('unitins2026')
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.is_coordenador = False
        admin_user.is_aluno = False
        admin_user.save()
        self.stdout.write(self.style.SUCCESS('  [+] Administrador: admin@unitins.br / unitins2026'))

        # Coordenador de Sistemas de Informação (RN06)
        coordenador, coord_created = User.objects.get_or_create(
            username='coord@unitins.br',
            defaults={
                'first_name': 'Carlos', 'last_name': 'Coordenador',
                'email': 'coord@unitins.br', 'cpf': '000.000.000-00',
                'is_coordenador': True, 'is_staff': True, 'is_superuser': False, 'is_aluno': False,
            }
        )
        coordenador.set_password('unitins2026')
        coordenador.is_coordenador = True
        coordenador.is_staff = True
        coordenador.is_superuser = False
        coordenador.is_aluno = False
        coordenador.save()

        # Vinculo obrigatório com o Curso (RN06)
        coord_perfil, _ = CoordenadorPerfil.objects.update_or_create(
            usuario=coordenador,
            defaults={'curso': curso_si}
        )
        self.stdout.write(self.style.SUCCESS(
            f'  [+] Coordenador: coord@unitins.br / unitins2026 (Curso: {coord_perfil.curso.nome})'
        ))

        # Alunos
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
                    'is_aluno': True, 'is_staff': False, 'is_superuser': False, 'is_coordenador': False,
                }
            )
            user.set_password('unitins2026')
            user.is_aluno = True
            user.save()

            perfil, p_created = AlunoPerfil.objects.update_or_create(
                usuario=user,
                defaults={'matricula': d['matricula'], 'curso': curso_si, 'matriz_curricular': d['matriz']},
            )
            perfis.append(perfil)
            self.stdout.write(self.style.SUCCESS(
                f"  [+] Aluno: {user.get_full_name()} ({d['username']}) | Meta: {d['matriz'].horas_totais_exigidas}h"
            ))

        # 4. Certificados Pendentes Realistas via Pipeline de Extração
        self._gerar_certificados_pipeline(perfis)
        self.stdout.write(self.style.SUCCESS('\nPovoamento concluido com sucesso! Todos os certificados estao pendentes para auditoria.'))

    def _gerar_certificados_pipeline(self, perfis):
        import random

        self.stdout.write(self.style.NOTICE('\nGerando certificados realistas e executando pipeline de extracao...'))

        total_certs = 0
        for perfil in perfis:
            meta = perfil.matriz_curricular.horas_totais_exigidas if perfil.matriz_curricular_id else 120
            rng = random.Random(perfil.id)

            plano = montar_plano_aluno(meta_horas=meta, rng=rng)
            soma_horas = 0

            for idx, item in enumerate(plano, start=1):
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

                nome_arquivo = f"{tipo_doc}_{perfil.matricula}_{slug}_{idx}.pdf"

                # Cria a instância inicial
                cert = Certificado(
                    aluno=perfil,
                    categoria=categoria,
                    horas_declaradas=Decimal(str(horas)),
                    status='pendente_ocr',
                )
                cert.arquivo_pdf.save(nome_arquivo, ContentFile(pdf_bytes, name=nome_arquivo), save=True)

                # Executa o extrator real (PyMuPDF + Regex de carga horária)
                caminho_pdf = cert.arquivo_pdf.path
                ocr = processar_pdf(caminho_pdf)

                # Executa a extração do Copiloto de Metadados (título e período)
                titulo_extraido, periodo_extraido = extrair_metadados_documento(
                    ocr.texto_extraido, titulo_fallback=titulo, periodo_fallback=periodo
                )

                # Atualiza com dados extraídos e status inicial estrito de pendente
                cert.titulo_atividade = titulo_extraido
                cert.periodo_realizacao = periodo_extraido
                cert.horas_sugeridas_ia = ocr.horas_encontradas or Decimal(str(horas))
                cert.confianca_ia = int(ocr.indice_confianca) if ocr.indice_confianca else 95
                cert.horas_validadas_ocr = ocr.horas_encontradas or Decimal(str(horas))
                cert.texto_extraido_ocr = ocr.texto_extraido or ""
                cert.indice_confianca_ocr = ocr.indice_confianca or 95.0

                # Status estritamente pendente para auditoria manual do coordenador
                cert.status = 'revisao_manual'
                cert.motivo_status = (
                    f"OCR: {ocr.horas_encontradas}h encontradas via {ocr.padrao_usado} "
                    f"(confiança: {ocr.indice_confianca:.0f}%)."
                    if ocr.sucesso
                    else "OCR não localizou horas de forma conclusiva. Aguarda auditoria da coordenação."
                )
                cert.horas_computadas_final = None
                cert.horas_descartadas = 0
                cert.save()

                # Registra log de auditoria da extração inicial (RN01)
                RuleValidationLog.objects.create(
                    certificado=cert,
                    usuario_responsavel=None,
                    regra_aplicada="RN01 — Extração OCR (PyMuPDF + Regex)",
                    artigo_resolucao="Resolução CONSUNI nº 057/2025 — Art. OCR",
                    justificativa=cert.motivo_status,
                    horas_enviadas=int(ocr.horas_encontradas or horas),
                    horas_computadas=0,
                    horas_descartadas=0,
                )

                soma_horas += horas
                total_certs += 1

            self.stdout.write(self.style.SUCCESS(
                f"  [+] {len(plano)} cert(s) | {perfil.usuario.get_full_name()} "
                f"| Declarado: {soma_horas}h / Meta: {meta}h (Status: revisao_manual)"
            ))

        self.stdout.write(self.style.SUCCESS(f'\n  => Total de {total_certs} certificados gerados e processados pelo pipeline.'))

