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

from rest_framework import mixins, viewsets, status as http_status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView

from academico.models import AlunoPerfil, CategoriaAACC, Certificado
from academico.serializers import CategoriaAACCSerializer, CertificadoSerializer
from rule_engine.validator import ValidadorCertificado

logger = logging.getLogger(__name__)


class CategoriaAACCViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet somente-leitura para CategoriaAACC.

    Endpoints:
        GET /api/academico/categorias/         → lista todas as categorias
        GET /api/academico/categorias/{id}/    → detalhe de uma categoria
    """

    queryset = CategoriaAACC.objects.exclude(codigo_slug__startswith="obsoleta_").order_by("eixo", "nome")
    serializer_class = CategoriaAACCSerializer


class CertificadoViewSet(viewsets.ModelViewSet):
    """
    ViewSet completo para Certificado.

    Segurança e isolamento de dados:
        - Aluno: vê apenas os seus próprios certificados.
        - Coordenador: vê todos os certificados.
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

        if user.is_coordenador:
            # Coordenador tem visibilidade total — necessária para fila de revisão
            return Certificado.objects.select_related("aluno", "categoria").all()

        # Aluno vê apenas os seus próprios documentos
        return (
            Certificado.objects
            .select_related("aluno", "categoria")
            .filter(aluno__usuario=user)
        )

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

        certificado.save(update_fields=[
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

        return Response(
            {"detail": "Certificado rejeitado com sucesso.", "justificativa": justificativa},
            status=http_status.HTTP_200_OK,
        )



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
        .values("categoria__eixo")
        .annotate(total=Sum("horas_computadas_final"))
    )

    horas_por_eixo = {eixo: 0 for eixo in EIXOS}
    for row in qs:
        eixo_db = row["categoria__eixo"]  # ex: 'Extensao'
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

        if not user.is_coordenador:
            return Response(
                {"detail": "Apenas coordenadores podem consultar extratos de outros alunos."},
                status=http_status.HTTP_403_FORBIDDEN,
            )

        perfil = get_object_or_404(AlunoPerfil, pk=perfil_id)
        return Response(_calcular_extrato(perfil))


class ListaAlunosView(APIView):
    """
    GET /api/academico/alunos/

    Devolve a lista de todos os AlunoPerfis do sistema.
    Acessível apenas por coordenadores.
    """

    def get(self, request):
        user = request.user
        if not user.is_coordenador:
            return Response(
                {"detail": "Apenas coordenadores podem listar os alunos."},
                status=http_status.HTTP_403_FORBIDDEN,
            )

        from django.db.models import Count, Sum, Q

        perfis = (
            AlunoPerfil.objects
            .select_related("usuario", "curso")
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
                "total_certs":    p.total_certs,
                "horas_aprovadas": p.horas_aprovadas or 0,
            }
            for p in perfis
        ]

        return Response(data)
