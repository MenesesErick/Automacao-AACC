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

    queryset = CategoriaAACC.objects.all().order_by("eixo", "nome")
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
        Hook de criação: associa o certificado ao AlunoPerfil do utilizador
        logado e invoca o motor de regras antes de persistir.

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

        # 1. Salva com o aluno correto (sobrepõe qualquer dado do frontend)
        certificado: Certificado = serializer.save(aluno=aluno)

        try:
            categoria = certificado.categoria
            horas_declaradas  = float(certificado.horas_declaradas)
            limite_categoria  = float(categoria.limite_maximo_horas)

            # 2. Saldo atual do aluno nesta categoria
            saldo_atual = self._calcular_saldo_atual(aluno, categoria)

            # 3. Motor de regras (Python puro — zero acesso ao DB)
            validador = ValidadorCertificado()
            resultado = validador.processar_certificado(
                horas_informadas=horas_declaradas,
                limite_cat=limite_categoria,
                saldo_cat=saldo_atual,
            )

            # 4. Persiste resultado e gera log de auditoria
            certificado.status               = resultado["status_sugerido"]
            certificado.horas_validadas_ocr  = int(horas_declaradas)
            certificado.horas_computadas_final = int(resultado["horas_finais"])
            certificado.horas_descartadas    = int(resultado["horas_descartadas"])
            certificado.indice_confianca_ocr = resultado["confianca_ocr"]
            certificado.texto_extraido_ocr   = resultado["texto_extraido"]
            certificado.motivo_status        = resultado["motivo"]

            certificado.save(
                update_fields=[
                    "status",
                    "horas_validadas_ocr",
                    "horas_computadas_final",
                    "horas_descartadas",
                    "indice_confianca_ocr",
                    "texto_extraido_ocr",
                    "motivo_status",
                ]
            )

            from academico.models import RuleValidationLog
            RuleValidationLog.objects.create(
                certificado=certificado,
                usuario_responsavel=None,
                regra_aplicada=f"Teto: {limite_categoria}h ({categoria.nome})",
                justificativa=resultado["motivo"],
                horas_enviadas=int(horas_declaradas),
                horas_computadas=int(resultado["horas_finais"]),
                horas_descartadas=int(resultado["horas_descartadas"]),
            )

            logger.info(
                "Certificado %s processado: status=%s, horas_finais=%s, aluno=%s",
                certificado.id,
                resultado["status_sugerido"],
                resultado["horas_finais"],
                aluno.matricula,
            )

        except Exception as exc:  # noqa: BLE001
            # Falha no motor mantém o certificado como pendente_ocr
            # para revisão manual pelo coordenador.
            logger.exception(
                "Erro ao processar certificado %s: %s", certificado.id, exc
            )

    # ── Auditoria / Human-in-the-Loop ───────────────────────────────────────
    @action(detail=True, methods=["patch"])
    def avaliar(self, request, pk=None):
        """
        Permite ao Coordenador deferir/indeferir certificados que caíram
        em revisao_manual ou pendente_ocr.
        """
        user = request.user
        if not user.is_coordenador:
            raise PermissionDenied("Apenas coordenadores podem avaliar certificados.")

        certificado = self.get_object()
        data = request.data

        status = data.get("status")
        if status not in ["aprovado", "rejeitado"]:
            return Response(
                {"detail": "Status inválido. Deve ser 'aprovado' ou 'rejeitado'."},
                status=400,
            )

        try:
            horas_computadas = int(float(data.get("horas_computadas_final", 0)))
        except (ValueError, TypeError):
            return Response(
                {"detail": "horas_computadas_final deve ser um número válido."},
                status=400,
            )

        motivo = data.get("motivo_status", "")
        if status == "rejeitado" and not motivo:
            motivo = "Indeferido pelo coordenador após revisão manual."
        elif status == "aprovado" and not motivo:
            motivo = "Deferido pelo coordenador após revisão manual."

        # Atualiza o certificado
        horas_declaradas = int(certificado.horas_declaradas)
        certificado.status = status
        certificado.horas_computadas_final = horas_computadas if status == "aprovado" else 0
        certificado.horas_descartadas = horas_declaradas - certificado.horas_computadas_final
        certificado.motivo_status = motivo
        
        certificado.save(
            update_fields=[
                "status",
                "horas_computadas_final",
                "horas_descartadas",
                "motivo_status",
                "data_atualizacao",
            ]
        )

        # Gera log de auditoria da ação manual
        from academico.models import RuleValidationLog
        RuleValidationLog.objects.create(
            certificado=certificado,
            usuario_responsavel=user,
            regra_aplicada="Revisão Manual (Coordenador)",
            justificativa=motivo,
            horas_enviadas=horas_declaradas,
            horas_computadas=certificado.horas_computadas_final,
            horas_descartadas=certificado.horas_descartadas,
        )

        logger.info(
            "Certificado %s %s por %s. Horas: %s",
            certificado.id,
            status,
            user.username,
            certificado.horas_computadas_final,
        )

        return Response({"detail": f"Certificado {status} com sucesso."})


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
