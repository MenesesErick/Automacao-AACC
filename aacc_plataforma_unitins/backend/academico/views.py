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

from rest_framework import mixins, viewsets
from rest_framework.exceptions import PermissionDenied

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
