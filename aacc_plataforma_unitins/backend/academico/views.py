"""
Views — App: academico

Expõe os recursos da plataforma via Django REST Framework.

Segurança:
  - JWTAuthentication: todas as views exigem Bearer token (configurado globalmente).
  - get_queryset blindado: o aluno vê apenas os seus próprios certificados;
    o coordenador vê todos.
  - perform_create: associa o certificado ao AlunoPerfil do utilizador logado,
    ignorando qualquer ID enviado pelo frontend.
"""

import logging

from django.shortcuts import get_object_or_404
from django.db.models import Sum
from django.utils import timezone

from rest_framework import mixins, viewsets, status as http_status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS

from django.contrib.auth import get_user_model

from academico.models import AlunoPerfil, CategoriaAACC, Certificado, Curso, Eixo, Notificacao
from academico.permissions import IsSuperAdmin
from academico.serializers import (
    CategoriaAACCSerializer,
    CertificadoSerializer,
    CoordenadorSerializer,
    CursoSerializer,
    EixoSerializer,
    NotificacaoSerializer,
)
from rule_engine.validator import ValidadorCertificado

logger = logging.getLogger(__name__)


class AdminWriteOrAuthenticatedReadMixin:
    """
    Leitura (GET/HEAD/OPTIONS): qualquer usuário autenticado (aluno preenche formulário).
    Escrita (POST/PUT/PATCH/DELETE): somente o Administrador (is_superuser).

    Obs.: IsAdminUser do DRF checa is_staff, que também é True para coordenadores;
    por isso usamos IsSuperAdmin.
    """

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsSuperAdmin()]


class EixoViewSet(viewsets.ModelViewSet):
    """
    CRUD de Eixos Formativos.

    Endpoints: /api/academico/eixos/ (list/create) e /eixos/{id}/ (retrieve/update/delete).
    """

    queryset = Eixo.objects.all().order_by("id")
    serializer_class = EixoSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]


class CursoViewSet(AdminWriteOrAuthenticatedReadMixin, viewsets.ModelViewSet):
    """
    CRUD de Cursos (com meta de carga horária na matriz curricular).
    Leitura: autenticado. Escrita: somente Admin.
    """

    queryset = Curso.objects.all().order_by("nome")
    serializer_class = CursoSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]


class CoordenadorViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """
    Gestão de Coordenadores (somente Admin): listar e criar.

    Cria Usuario com is_staff=True e is_coordenador=True (não superuser, não aluno).
    """

    serializer_class = CoordenadorSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get_queryset(self):
        return (
            get_user_model().objects
            .select_related("perfil_coordenador__curso")
            .filter(is_staff=True, is_coordenador=True, is_superuser=False)
            .order_by("first_name", "email")
        )


class CategoriaAACCViewSet(AdminWriteOrAuthenticatedReadMixin, viewsets.ModelViewSet):
    """
    CRUD de CategoriaAACC.

    Endpoints:
        GET    /api/academico/categorias/         → lista (qualquer autenticado)
        GET    /api/academico/categorias/{id}/    → detalhe (qualquer autenticado)
        POST/PUT/PATCH/DELETE                     → somente Admin
    """

    queryset = (
        CategoriaAACC.objects.select_related("eixo")
        .exclude(codigo_slug__startswith="obsoleta_")
        .order_by("eixo__id", "nome")
    )
    serializer_class = CategoriaAACCSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]


def _curso_do_coordenador(user):
    """Curso do coordenador logado, ou None se não houver CoordenadorPerfil."""
    perfil = getattr(user, "perfil_coordenador", None)
    return perfil.curso if perfil else None


def _filtrar_por_curso_do_usuario(queryset, user, campo_curso: str):
    """
    RN06 — Isolamento de Visão de Dados:
        - Administrador (is_superuser): vê tudo.
        - Coordenador: apenas registros do curso do seu CoordenadorPerfil
          (queryset vazio se o perfil não existir).
        - Demais usuários: queryset vazio.
    `campo_curso` é o caminho ORM até o curso (ex.: "curso" ou "aluno__curso").
    """
    if user.is_superuser:
        return queryset
    if user.is_coordenador:
        curso = _curso_do_coordenador(user)
        if curso is None:
            return queryset.none()
        return queryset.filter(**{campo_curso: curso})
    return queryset.none()


def _alunos_visiveis(user):
    """AlunoPerfis que o usuário (admin/coordenador) pode enxergar."""
    return _filtrar_por_curso_do_usuario(AlunoPerfil.objects.all(), user, "curso")


def _notificar_resultado(certificado, aprovado, horas=None, justificativa=""):
    """UC04.3 — cria a notificação in-app para o aluno dono do certificado."""
    titulo = certificado.titulo_atividade or certificado.categoria.nome
    if aprovado:
        msg = f"Seu certificado \"{titulo}\" foi deferido"
        msg += f" ({horas}h computadas)." if horas is not None else "."
    else:
        msg = f"Seu certificado \"{titulo}\" foi indeferido."
        if justificativa:
            msg += f" Motivo: {justificativa}"
    Notificacao.objects.create(usuario=certificado.aluno.usuario, mensagem=msg)


class CertificadoViewSet(viewsets.ModelViewSet):
    """
    ViewSet completo para Certificado.

    Segurança e isolamento de dados:
        - Aluno: vê apenas os seus próprios certificados.
        - Coordenador: vê apenas certificados de alunos do seu curso (RN06).
        - Administrador: vê todos os certificados.
        - perform_create: associa automaticamente ao AlunoPerfil logado.

    Motor de regras (perform_create):
        1. Recupera o AlunoPerfil do utilizador autenticado.
        2. Consulta o saldo acumulado do aluno na categoria enviada.
        3. Chama ValidadorCertificado.processar_certificado().
        4. Persiste o resultado e gera RuleValidationLog.
    """

    serializer_class = CertificadoSerializer

    # ── Blindagem do queryset (RN privacidade) ──────────────────────────────
    def get_queryset(self):
        user = self.request.user
        base = Certificado.objects.select_related("aluno", "categoria")

        if user.is_superuser or user.is_coordenador:
            return _filtrar_por_curso_do_usuario(base, user, "aluno__curso")

        # Aluno vê apenas os seus próprios documentos
        return base.filter(aluno__usuario=user)

    # ── Cálculo de saldo ────────────────────────────────────────────────────
    def _calcular_saldo_atual(
        self, aluno: AlunoPerfil, categoria: CategoriaAACC
    ) -> float:
        """
        Soma das horas já aprovadas pelo aluno nesta categoria
        (ignora pendentes e rejeitados para não inflar o saldo).
        """
        saldo = (
            Certificado.objects.filter(
                aluno=aluno,
                categoria=categoria,
                status__in=["aprovado", "requerimento_gerado"],
            )
            .exclude(horas_computadas_final__isnull=True)
            .values_list("horas_computadas_final", flat=True)
        )
        return float(sum(saldo))

    # ── Criação blindada ────────────────────────────────────────────────────
    def perform_create(self, serializer: CertificadoSerializer) -> None:
        """
        Hook de criação — Paradigma Human-in-the-Loop.

        Fluxo:
            1. Salva o PDF associado ao AlunoPerfil do utilizador logado.
            2. Invoca o OCR Service (PyMuPDF + Regex) de forma síncrona.
            3. Guarda o texto extraído e as horas encontradas como "sugestão da IA"
               no campo horas_declaradas (reaproveitado como hint para o coordenador).
            4. Define sempre status=revisao_manual — o coordenador tem a palavra final.

        Garante que o frontend nunca pode submeter em nome de outro aluno.
        """
        user = self.request.user

        # Coordenadores não submetem certificados — apenas revisam
        if user.is_coordenador:
            raise PermissionDenied(
                "Coordenadores não podem submeter certificados de alunos."
            )

        # Obtém o perfil do aluno logado — 404 automático se não existir
        try:
            aluno = user.perfil_aluno
        except AlunoPerfil.DoesNotExist:
            raise PermissionDenied(
                "O utilizador autenticado não possui um Perfil de Aluno associado."
            )

        # 1. Persiste o certificado com status inicial pendente_ocr
        #    horas_declaradas pode ser None — o OCR vai preenchê-las a seguir (mantido null pois aluno não declara)
        certificado: Certificado = serializer.save(
            aluno=aluno,
            status="pendente_ocr",
            horas_declaradas=None,
        )

        # 2. Invoca o OCR Service de forma síncrona
        from academico.services.ocr_service import processar_pdf
        from django.conf import settings
        import os

        caminho_pdf = os.path.join(settings.MEDIA_ROOT, certificado.arquivo_pdf.name)
        ocr = processar_pdf(caminho_pdf)

        # 3. Atualiza o certificado com os dados do OCR nos campos analíticos dedicados
        certificado.horas_sugeridas_ia = ocr.horas_encontradas or 0

        # 2b. Dupla checagem de titularidade (nome lido x nome do aluno) — RN04
        from academico.services.ocr_service import extrair_e_validar_titularidade
        nome_aluno = user.get_full_name().strip() or user.first_name or ""
        titularidade = extrair_e_validar_titularidade(ocr.texto_extraido or "", nome_aluno or None)
        certificado.nome_extraido_ocr = (titularidade["nome_extraido"] or "")[:255] or None
        certificado.titularidade_confirmada = titularidade["titularidade_confirmada"]
        certificado.similaridade_titularidade = titularidade["similaridade_titularidade"]
        divergencia_titular = bool(nome_aluno) and not titularidade["titularidade_confirmada"]
        if divergencia_titular:
            # Trava RN04: titularidade falha → confiança <= 65% (revisão manual obrigatória)
            from academico.services.ocr_service import aplicar_trava_titularidade
            ocr.indice_confianca = aplicar_trava_titularidade(ocr.indice_confianca, False)

        certificado.confianca_ia       = int(ocr.indice_confianca) if ocr.indice_confianca else 0
        # Mantendo para compatibilidade/redundância se necessário
        certificado.horas_validadas_ocr = ocr.horas_encontradas or 0
        certificado.texto_extraido_ocr  = ocr.texto_extraido or ""
        certificado.indice_confianca_ocr = ocr.indice_confianca

        # 4. Sempre revisao_manual — Coordenador tem a palavra final (RN05)
        certificado.status = "revisao_manual"
        certificado.motivo_status = (
            f"OCR: {ocr.horas_encontradas}h encontradas via {ocr.padrao_usado} "
            f"(confiança: {ocr.indice_confianca:.0f}%)."
            if ocr.sucesso
            else f"OCR não localizou horas. Erro: {ocr.erro or 'texto insuficiente'}. "
                 "Aguarda revisão manual."
        )
        if divergencia_titular:
            certificado.motivo_status = (
                f"ALERTA RN04: divergência de titularidade (nome lido: "
                f"'{certificado.nome_extraido_ocr or 'não identificado'}', "
                f"similaridade {titularidade['similaridade_titularidade']}%). "
                + (certificado.motivo_status or "")
            )[:255]

        certificado.save(update_fields=[
            "nome_extraido_ocr",
            "titularidade_confirmada",
            "similaridade_titularidade",
            "horas_declaradas",
            "horas_validadas_ocr",
            "texto_extraido_ocr",
            "indice_confianca_ocr",
            "horas_sugeridas_ia",
            "confianca_ia",
            "status",
            "motivo_status",
        ])

        # 5. Log de auditoria — registra a sugestão automática do OCR
        from academico.models import RuleValidationLog
        RuleValidationLog.objects.create(
            certificado=certificado,
            usuario_responsavel=None,
            regra_aplicada="RN01 — Extração OCR (PyMuPDF + Regex)",
            artigo_resolucao="Resolução CONSUNI nº 057/2025 — Art. OCR",
            justificativa=certificado.motivo_status,
            horas_enviadas=ocr.horas_encontradas or 0,
            horas_computadas=ocr.horas_encontradas or 0,
            horas_descartadas=0,
        )

        logger.info(
            "Certificado %s → revisao_manual | OCR=%dh | conf=%.0f%% | aluno=%s",
            certificado.id,
            ocr.horas_encontradas or 0,
            ocr.indice_confianca,
            aluno.matricula,
        )

    # ── UC01.5 — Retificação de submissão pelo aluno ────────────────────────
    STATUS_EDITAVEIS = ("pendente_ocr", "revisao_manual")

    def update(self, request, *args, **kwargs):
        """
        PUT/PATCH /api/academico/certificados/{id}/

        Retificação (UC01.5): somente o aluno dono do certificado pode editar,
        e apenas enquanto o documento não foi auditado (pendente / em análise).
        Deferido/Indeferido/Requerimento gerado → 403 Forbidden.
        """
        user = request.user
        if user.is_superuser or user.is_coordenador:
            raise PermissionDenied(
                "Apenas o aluno autor pode retificar a submissão."
            )

        certificado = self.get_object()  # queryset já restringe ao dono (404 caso contrário)
        if certificado.status not in self.STATUS_EDITAVEIS:
            raise PermissionDenied(
                "Este certificado já foi auditado e não pode mais ser editado."
            )
        return super().update(request, *args, **kwargs)

    def perform_update(self, serializer: CertificadoSerializer) -> None:
        """Salva a retificação e reprocessa o OCR caso o arquivo tenha sido trocado."""
        troca_arquivo = "arquivo_pdf" in serializer.validated_data
        certificado: Certificado = serializer.save()

        if not troca_arquivo:
            return

        from academico.services.ocr_service import processar_pdf
        from django.conf import settings
        import os

        ocr = processar_pdf(os.path.join(settings.MEDIA_ROOT, certificado.arquivo_pdf.name))
        certificado.horas_sugeridas_ia = ocr.horas_encontradas or 0
        certificado.confianca_ia = int(ocr.indice_confianca) if ocr.indice_confianca else 0
        certificado.horas_validadas_ocr = ocr.horas_encontradas or 0
        certificado.texto_extraido_ocr = ocr.texto_extraido or ""
        certificado.indice_confianca_ocr = ocr.indice_confianca
        certificado.status = "revisao_manual"
        certificado.motivo_status = (
            f"Retificado pelo aluno. OCR: {ocr.horas_encontradas}h encontradas via "
            f"{ocr.padrao_usado} (confiança: {ocr.indice_confianca:.0f}%)."
            if ocr.sucesso
            else "Retificado pelo aluno. OCR não localizou horas. Aguarda revisão manual."
        )
        certificado.save(update_fields=[
            "horas_validadas_ocr", "texto_extraido_ocr", "indice_confianca_ocr",
            "horas_sugeridas_ia", "confianca_ia", "status", "motivo_status",
        ])

    # ── Avaliação Human-in-the-Loop com SEBR ────────────────────────────────
    @action(detail=True, methods=["patch"], url_path="avaliar")
    def avaliar(self, request, pk=None):
        """
        PATCH /api/academico/certificados/{id}/avaliar/

        Endpoint exclusivo do Coordenador para deferir ou indeferir um certificado.
        Integra o SEBR (Resolução CONSUNI 057/2025) via avaliacao_service.

        Payload esperado:
            {
                "acao":             "aprovar" | "rejeitar",
                "horas_confirmadas": float,   // obrigatório se acao=="aprovar"
                "justificativa":    string    // obrigatório se acao=="rejeitar" (RN03)
            }

        Resposta (aprovação):
            {
                "detail":               "Certificado aprovado com sucesso.",
                "horas_deferidas":      float,
                "horas_cortadas_evento": float,
                "horas_cortadas_total": float,
                "saldo_apos":           float,
                "atingiu_teto_evento":  bool,
                "atingiu_teto_total":   bool,
                "regra_aplicada":       string
            }
        """
        from decimal import Decimal, InvalidOperation
        from academico.services.avaliacao_service import (
            aprovar_certificado,
            rejeitar_certificado,
        )

        user = request.user
        if not user.is_coordenador:
            raise PermissionDenied("Apenas coordenadores podem avaliar certificados.")

        certificado = self.get_object()

        # ── Validação do payload ──────────────────────────────────────────────
        acao = (request.data.get("acao") or "").strip().lower()
        if acao not in ("aprovar", "rejeitar"):
            return Response(
                {"detail": "Campo 'acao' é obrigatório e deve ser 'aprovar' ou 'rejeitar'."},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        # ── Fluxo de APROVAÇÃO ────────────────────────────────────────────────
        if acao == "aprovar":
            raw_horas = request.data.get("horas_confirmadas")
            if raw_horas is None:
                return Response(
                    {"detail": "Campo 'horas_confirmadas' é obrigatório para aprovação."},
                    status=http_status.HTTP_400_BAD_REQUEST,
                )
            try:
                horas_confirmadas = Decimal(str(raw_horas))
                if horas_confirmadas <= 0:
                    raise ValueError
            except (InvalidOperation, ValueError):
                return Response(
                    {"detail": "'horas_confirmadas' deve ser um número decimal positivo."},
                    status=http_status.HTTP_400_BAD_REQUEST,
                )

            try:
                resultado = aprovar_certificado(
                    certificado          = certificado,
                    horas_confirmadas    = horas_confirmadas,
                    usuario_responsavel  = user,
                )
            except ValueError as exc:
                # Categoria sem slug ou slug inválido no SEBR
                return Response(
                    {"detail": str(exc)},
                    status=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                )

            logger.info(
                "Cert %s APROVADO por %s | deferidas=%.2fh | teto_ev=%s | teto_tot=%s",
                certificado.pk, user.username,
                resultado["horas_deferidas"],
                resultado["atingiu_teto_evento"],
                resultado["atingiu_teto_total"],
            )

            _notificar_resultado(certificado, aprovado=True, horas=resultado["horas_deferidas"])

            return Response(
                {
                    "detail":                "Certificado aprovado com sucesso.",
                    "horas_deferidas":       float(resultado["horas_deferidas"]),
                    "horas_cortadas_evento": float(resultado["horas_cortadas_evento"]),
                    "horas_cortadas_total":  float(resultado["horas_cortadas_total"]),
                    "saldo_apos":            float(resultado["saldo_apos"]),
                    "atingiu_teto_evento":   resultado["atingiu_teto_evento"],
                    "atingiu_teto_total":    resultado["atingiu_teto_total"],
                    "regra_aplicada":        resultado["regra_aplicada"],
                },
                status=http_status.HTTP_200_OK,
            )

        # ── Fluxo de REJEIÇÃO ─────────────────────────────────────────────────
        justificativa = (request.data.get("justificativa") or "").strip()
        try:
            rejeitar_certificado(
                certificado         = certificado,
                justificativa       = justificativa,
                usuario_responsavel = user,
            )
        except ValueError as exc:
            # RN03: justificativa vazia
            return Response(
                {"detail": str(exc)},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        logger.info(
            "Cert %s REJEITADO por %s. Motivo: %.60s",
            certificado.pk, user.username, justificativa,
        )

        _notificar_resultado(certificado, aprovado=False, justificativa=justificativa)

        return Response(
            {"detail": "Certificado rejeitado com sucesso.", "justificativa": justificativa},
            status=http_status.HTTP_200_OK,
        )


class NotificacaoViewSet(
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    UC04.3 — Notificações in-app.

    GET   /api/academico/notificacoes/         → lista as do usuário logado (?lida=false filtra)
    PATCH /api/academico/notificacoes/{id}/    → marca como lida (apenas o campo `lida`)
    """

    serializer_class = NotificacaoSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "head", "options"]
    pagination_class = None

    def get_queryset(self):
        qs = Notificacao.objects.filter(usuario=self.request.user)
        lida = self.request.query_params.get("lida")
        if lida is not None:
            qs = qs.filter(lida=lida.lower() in ("true", "1"))
        return qs.order_by("-criado_em")

    @action(detail=False, methods=["patch"], url_path="marcar-todas-lidas")
    def marcar_todas_lidas(self, request):
        self.get_queryset().filter(lida=False).update(lida=True)
        return Response(status=http_status.HTTP_204_NO_CONTENT)




# ─────────────────────────────────────────────────────────────────────────────
#  RN02 — Extrato do Aluno / Diversidade de Eixos
# ─────────────────────────────────────────────────────────────────────────────

def _calcular_extrato(perfil: AlunoPerfil) -> dict:
    """
    Função pura que calcula o extrato de horas de um AlunoPerfil.
    Reutilizável pelas duas views (aluno e coordenador).

    Regras aplicadas:
        RN02 — Diversidade de Eixos: apto_formatura = True somente se
               total_horas >= meta E eixos_contemplados >= 2.
        RN03 — Apenas certificados com status 'aprovado' contam.
    """
    META = int(
        perfil.matriz_curricular.horas_totais_exigidas
        if perfil.matriz_curricular_id
        else 120
    )

    EIXOS = ["Ensino", "Pesquisa", "Extensao"]

    # Suma de horas agrupadas por eixo usando ORM (um único query)
    qs = (
        Certificado.objects
        .filter(aluno=perfil, status="aprovado")
        .exclude(horas_computadas_final__isnull=True)
        .values("categoria__eixo__nome")
        .annotate(total=Sum("horas_computadas_final"))
    )

    horas_por_eixo = {eixo: 0 for eixo in EIXOS}
    for row in qs:
        eixo_db = row["categoria__eixo__nome"]  # ex: 'Extensao'
        if eixo_db in horas_por_eixo:
            horas_por_eixo[eixo_db] = row["total"]

    total_horas = sum(horas_por_eixo.values())
    eixos_contemplados = sum(1 for h in horas_por_eixo.values() if h > 0)

    # RN02 — necessita pelo menos 2 eixos E atingir a meta
    apto_formatura = (total_horas >= META) and (eixos_contemplados >= 2)

    progresso_percentual = min(round((total_horas / META) * 100), 100) if META else 0

    return {
        "aluno_nome": perfil.usuario.get_full_name() or perfil.usuario.username,
        "matricula": perfil.matricula,
        "curso": perfil.curso.nome if perfil.curso_id else "—",
        "total_horas_aprovadas": total_horas,
        "meta_horas": META,
        "horas_por_eixo": horas_por_eixo,
        "eixos_contemplados": eixos_contemplados,
        "apto_formatura": apto_formatura,
        "progresso_percentual": progresso_percentual,
        # Detalhe útil para o frontend mostrar o que falta
        "faltam_horas": max(META - total_horas, 0),
        "faltam_eixos": max(2 - eixos_contemplados, 0),
    }



class AnalisePreviaView(APIView):
    """
    POST /api/academico/certificados/analise-previa/

    Copiloto de Metadados: recebe um arquivo (PDF/Imagem), extrai o texto
    via PyMuPDF e tenta identificar o título da atividade e o período
    de realização usando heurísticas de regex.

    NÃO salva nada no banco de dados. Retorna apenas sugestões para o aluno
    revisar antes de submeter o formulário completo.

    Retorno:
        {
            "titulo_sugerido": str,
            "periodo_sugerido": str
        }
    """

    def post(self, request):
        import re
        import io
        import os
        import datetime

        arquivo = request.FILES.get("arquivo")
        if not arquivo:
            return Response(
                {"detail": "Nenhum arquivo enviado."},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        titulo_sugerido = ""
        periodo_sugerido = ""
        leitura_por_imagem = False
        nome_sugerido = ""
        titularidade_confirmada = True
        similaridade_titularidade = 100.0
        confianca_ocr = None
        aviso_titularidade = ""

        try:
            import fitz  # PyMuPDF

            conteudo = arquivo.read()
            content_type = arquivo.content_type or ""
            is_image = content_type in ("image/jpeg", "image/png", "image/jpg")

            texto_completo = ""

            if not is_image:
                doc = fitz.open(stream=io.BytesIO(conteudo), filetype="pdf")
                texto_completo = "\n".join(page.get_text() for page in doc)
                doc.close()

            if is_image or len(texto_completo.strip()) < 20:
                try:
                    import pytesseract
                    from PIL import Image
                    if is_image:
                        imagem = Image.open(io.BytesIO(conteudo))
                    else:
                        doc_ocr = fitz.open(stream=io.BytesIO(conteudo), filetype="pdf")
                        page_ocr = doc_ocr[0]
                        pix = page_ocr.get_pixmap(dpi=200)
                        doc_ocr.close()
                        imagem = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    texto_completo = pytesseract.image_to_string(imagem, lang="por")
                    leitura_por_imagem = True
                    print("[Tesseract] Texto extraido:", texto_completo[:200])
                except Exception as ocr_exc:
                    logger.warning("[AnalisePrévia] Tesseract falhou: %s", ocr_exc)
            else:
                print("[PyMuPDF] Texto extraido:", texto_completo[:200])

            texto_limpo_espacos = re.sub(r'\s+', ' ', texto_completo)
            
            # --- TÍTULO: Heurística de Gatilho Posicional ---
            titulo_sugerido = ""
            match_gatilho_aspas = re.search(r"(?:participou do\(a\)|concluiu o curso de|evento)\s*[\"“'](.*?)[\"”']", texto_limpo_espacos, re.IGNORECASE)
            match_gatilho_virgula = re.search(r"(?:participou do\(a\)|concluiu o curso de)\s+([A-ZÀ-Úa-zà-ú\s]{10,100})[,(]", texto_limpo_espacos, re.IGNORECASE)

            if match_gatilho_aspas:
                titulo_sugerido = match_gatilho_aspas.group(1).strip()
            elif match_gatilho_virgula:
                titulo_sugerido = match_gatilho_virgula.group(1).strip()
            
            if not titulo_sugerido and not leitura_por_imagem:
                # --- TITULO: Analise por tamanho de fonte (PDF com camada de texto) ---
                melhor_score = 0.0
                texto_maior_fonte = ""
            
                palavras_ignoradas = {"CERTIFICADO", "DECLARAÇÃO", "DECLARACAO", "ATESTADO", "ATON", "MODALIDADE", "A"}
                termos_bloqueio = ["AUTENTICIDADE", "VERIFICADA", "ENDEREÇO", "CHAVE", "IDENTIFICAÇÃO", "WWW", "VALIDAR", "HTTP"]
                
                # Adiciona o nome do usuário (aluno) na blacklist
                if request.user.is_authenticated:
                    nome_completo = request.user.get_full_name().strip().upper()
                    if nome_completo:
                        partes = nome_completo.split()
                        if partes:
                            palavras_ignoradas.add(re.sub(r'[^A-ZÇÁÉÍÓÚÃÕ]', '', partes[0]))
                            if len(partes) > 1:
                                palavras_ignoradas.add(re.sub(r'[^A-ZÇÁÉÍÓÚÃÕ]', '', partes[-1]))
                    else:
                        palavras_ignoradas.add(re.sub(r'[^A-ZÇÁÉÍÓÚÃÕ]', '', request.user.username.upper()))
                
                gatilhos = ['CURSO', 'EVENTO', 'PALESTRA', 'SEMINÁRIO', 'SEMINARIO', 'OFICINA', 'WORKSHOP', 'JORNADA', 'SIMPÓSIO', 'SIMPOSIO', 'MINICURSO']
                
                doc_font = fitz.open(stream=io.BytesIO(conteudo), filetype="pdf")
                for page in doc_font:
                    blocks = page.get_text("dict").get("blocks", [])
                    for block in blocks:
                        if block.get("type") == 0:  # type 0 é texto
                            for line in block.get("lines", []):
                                for span in line.get("spans", []):
                                    text = span.get("text", "").strip()
                                    size = span.get("size", 0.0)
                                    
                                    # 1. Ignora strings muito curtas
                                    if len(text) >= 8:
                                        texto_upper = text.upper()
                                        texto_limpo = re.sub(r'[^A-ZÇÁÉÍÓÚÃÕ]', '', texto_upper)
                                        
                                        # 2. Pula se for palavra genérica, nome do aluno, ou bloco de rodapé/autenticidade
                                        if texto_upper in palavras_ignoradas or (texto_limpo and texto_limpo in palavras_ignoradas):
                                            continue
                                        if any(tb in texto_upper for tb in termos_bloqueio):
                                            continue
                                        
                                        # 3. Bônus por palavra-chave (peso extra)
                                        score = size
                                        if any(g in texto_upper for g in gatilhos):
                                            score += 20.0  # Pontuação bônus
                                            
                                        if score > melhor_score:
                                            melhor_score = score
                                            texto_maior_fonte = text

                doc_font.close()
                titulo_sugerido = texto_maior_fonte

            # Fallback do Título: nome do arquivo sem extensão
            if not titulo_sugerido:
                titulo_sugerido = os.path.splitext(arquivo.name)[0]

            # --- DATA: Cascata de Regex (5 niveis) ---
            texto_limpo = re.sub(r'\s+', ' ', texto_completo)
            
            padroes_data = [
                # Padrão 1 (Intervalo Numérico): 03/02/2025 a 23/06/2025
                r"(\d{2}/\d{2}/\d{4}\s*(?:a|à|-)\s*\d{2}/\d{2}/\d{4})",
                
                # Padrão 2 (Intervalo Extenso - Meses Diferentes): 03 de fevereiro a 23 de junho de 2025
                r"(\d{1,2}\s+de\s+[a-zA-ZçÇ]+\s+(?:a|à|-)\s+\d{1,2}\s+de\s+[a-zA-ZçÇ]+\s+de\s+\d{4})",
                
                # Padrão 3 (Intervalo Extenso - Mesmo Mês): 26 a 27 de março de 2024
                r"(\d{1,2}\s*(?:a|à|-)\s*\d{1,2}\s+de\s+[a-zA-ZçÇ]+\s+de\s+\d{4})",
                
                # Padrão 4 (Data Única Extensa): 27 de março de 2024
                r"(\d{1,2}\s+de\s+[a-zA-ZçÇ]+\s+de\s+\d{4})",
                
                # Padrão 5 (Data Única Numérica): 10/02/2025
                r"(\d{2}/\d{2}/\d{4})"
            ]

            periodo_sugerido = ""
            for padrao in padroes_data:
                match = re.search(padrao, texto_limpo, re.IGNORECASE)
                if match:
                    periodo_sugerido = match.group(1).replace('\n', ' ').strip()
                    break
            
            if not periodo_sugerido:
                periodo_sugerido = str(datetime.datetime.now().year)

            # --- TITULARIDADE: dupla checagem do nome do aluno (RN04) ---
            from academico.services.ocr_service import (
                extrair_e_validar_titularidade, analisar_carga_horaria,
            )
            nome_aluno = request.user.get_full_name().strip() or request.user.first_name or ""
            titularidade = extrair_e_validar_titularidade(texto_completo, nome_aluno or None)
            nome_sugerido = titularidade["nome_extraido"] or ""
            titularidade_confirmada = titularidade["titularidade_confirmada"]
            similaridade_titularidade = titularidade["similaridade_titularidade"]

            try:
                _, confianca_ocr, _ = analisar_carga_horaria(texto_completo)
            except Exception:
                confianca_ocr = None
            if nome_aluno and not titularidade_confirmada:
                from academico.services.ocr_service import aplicar_trava_titularidade
                confianca_ocr = aplicar_trava_titularidade(confianca_ocr, False)
                aviso_titularidade = (
                    "O nome identificado no documento diverge do nome do aluno. "
                    "O certificado será encaminhado para revisão manual."
                )

        except Exception as exc:
            logger.warning("[AnalisePrévia] Extração falhou para '%s': %s", arquivo.name, exc)
            # Retorna vazio — o aluno preenche manualmente

        return Response({
            "titulo_sugerido": titulo_sugerido[:255] if titulo_sugerido else "",
            "periodo_sugerido": periodo_sugerido[:100] if periodo_sugerido else "",
            "leitura_por_imagem": leitura_por_imagem,
            "nome_sugerido": nome_sugerido,
            "nome_extraido": nome_sugerido,
            "titularidade_confirmada": titularidade_confirmada,
            "similaridade_titularidade": similaridade_titularidade,
            "confianca_ocr": confianca_ocr,
            "aviso_titularidade": aviso_titularidade,
        })


class ExtratoAlunoMeView(APIView):
    """
    GET /api/academico/alunos/meu-extrato/

    Devolve o extrato de horas e aptidão à formatura do ALUNO autenticado.
    Apenas alunos têm acesso — coordenadores usam ExtratoAlunoCoordenadorView.
    """

    def get(self, request):
        user = request.user

        if user.is_coordenador:
            return Response(
                {"detail": "Use o endpoint /api/academico/alunos/<id>/extrato/ para ver o extrato de um aluno."},
                status=http_status.HTTP_403_FORBIDDEN,
            )

        try:
            perfil = user.perfil_aluno
        except AlunoPerfil.DoesNotExist:
            return Response(
                {"detail": "Perfil de aluno não encontrado para este utilizador."},
                status=http_status.HTTP_404_NOT_FOUND,
            )

        return Response(_calcular_extrato(perfil))


class ExtratoAlunoCoordenadorView(APIView):
    """
    GET /api/academico/alunos/<perfil_id>/extrato/

    Permite ao COORDENADOR consultar o extrato de qualquer aluno.
    Alunos não têm acesso a esta rota.
    """

    def get(self, request, perfil_id: int):
        user = request.user

        if not (user.is_coordenador or user.is_superuser):
            return Response(
                {"detail": "Apenas coordenadores podem consultar extratos de outros alunos."},
                status=http_status.HTTP_403_FORBIDDEN,
            )

        # RN06: 404 se o aluno não pertence ao curso do coordenador
        perfil = get_object_or_404(_alunos_visiveis(user), pk=perfil_id)
        return Response(_calcular_extrato(perfil))


class ListaAlunosView(APIView):
    """
    GET /api/academico/alunos/

    Devolve a lista de AlunoPerfis visíveis ao usuário (RN06):
    coordenador → apenas alunos do seu curso; administrador → todos.
    """

    def get(self, request):
        user = request.user
        if not (user.is_coordenador or user.is_superuser):
            return Response(
                {"detail": "Apenas coordenadores podem listar os alunos."},
                status=http_status.HTTP_403_FORBIDDEN,
            )

        from django.db.models import Count, Sum, Q

        perfis = (
            _alunos_visiveis(user)
            .select_related("usuario", "curso", "matriz_curricular")
            .annotate(
                total_certs=Count("certificados"),
                horas_aprovadas=Sum(
                    "certificados__horas_computadas_final",
                    filter=Q(certificados__status="aprovado"),
                    default=0,
                ),
            )
            .order_by("matricula")
        )

        data = [
            {
                "id":             p.pk,
                "aluno_nome":     p.usuario.get_full_name() or p.usuario.username,
                "email":          p.usuario.email,
                "matricula":      p.matricula,
                "curso":          p.curso.nome if p.curso_id else "—",
                "meta_horas":     p.matriz_curricular.horas_totais_exigidas if p.matriz_curricular_id else 120,
                "total_certs":    p.total_certs,
                "horas_aprovadas": p.horas_aprovadas or 0,
            }
            for p in perfis
        ]

        return Response(data)


class GerarAnexoIView(APIView):
    """
    GET /api/academico/alunos/<perfil_id>/gerar-anexo-i/

    Fornecedor de dados JSON para o Anexo I (Requerimento de AACC).

    RN05: Só retorna 200 se o total de horas validadas atingir a meta
    da matriz curricular do aluno (120h ou 180h). Caso contrário, 400.

    Acesso: apenas coordenadores (is_staff=True).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, perfil_id):
        if not request.user.is_staff:
            return Response(
                {"detail": "Apenas coordenadores podem gerar o Anexo I."},
                status=http_status.HTTP_403_FORBIDDEN,
            )

        aluno = get_object_or_404(_alunos_visiveis(request.user), pk=perfil_id)

        certificados = (
            Certificado.objects
            .filter(aluno=aluno, status="aprovado")
            .select_related("categoria")
            .order_by("categoria__eixo__id", "data_envio")
        )

        total_horas = (
            certificados.aggregate(total=Sum("horas_computadas_final"))["total"] or 0
        )

        # ── RN05: meta da matriz deve ser atingida ────────────────────────────
        meta = aluno.matriz_curricular.horas_totais_exigidas
        if total_horas < meta:
            return Response(
                {
                    "detail": (
                        f"Meta não atingida. O aluno possui {total_horas}h validadas "
                        f"de {meta}h exigidas pela matriz curricular."
                    ),
                    "total_horas_validadas": float(total_horas),
                    "meta_horas": meta,
                },
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        # ── Monta payload JSON para o react-to-print ─────────────────────────
        lista_certificados = [
            {
                "titulo_atividade":  cert.titulo_atividade or "",
                "eixo_formativo":    cert.categoria.eixo.nome if cert.categoria else "",
                "periodo_realizacao": cert.periodo_realizacao or "",
                "horas_solicitadas": float(cert.horas_declaradas or 0),
                "horas_validadas":   float(cert.horas_computadas_final or 0),
            }
            for cert in certificados
        ]

        return Response(
            {
                "aluno": {
                    "nome":      aluno.usuario.get_full_name(),
                    "matricula": aluno.matricula,
                    "curso":     aluno.curso.nome if aluno.curso_id else "",
                    "campus":    "Palmas - TO",
                    "semestre":  "",
                    "turno":     "",
                },
                "certificados":           lista_certificados,
                "total_horas_validadas":  float(total_horas),
                "data_emissao":           timezone.now().date().strftime("%d/%m/%Y"),
            },
            status=http_status.HTTP_200_OK,
        )
