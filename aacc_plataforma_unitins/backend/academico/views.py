"""
Views — App: academico

Expõe os recursos da plataforma via Django REST Framework.
O CertificadoViewSet integra o rule_engine no perform_create para que
o status e as horas computadas sejam calculados automaticamente na
submissão do certificado pelo aluno.
"""

import logging

from rest_framework import mixins, viewsets

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

    Endpoints disponíveis:
        GET /api/academico/categorias/         -> lista todas as categorias
        GET /api/academico/categorias/{id}/    -> detalhe de uma categoria
    """

    queryset = CategoriaAACC.objects.all().order_by("eixo", "nome")
    serializer_class = CategoriaAACCSerializer


class CertificadoViewSet(viewsets.ModelViewSet):
    """
    ViewSet completo para Certificado.

    Na criação (POST), o motor de regras é invocado automaticamente:
        1. Lê as horas declaradas pelo aluno.
        2. Consulta o saldo atual do aluno nesta categoria.
        3. Chama ValidadorCertificado.processar_certificado().
        4. Persiste o resultado (status e horas_computadas_final) no banco.

    Endpoints disponíveis:
        GET    /api/academico/certificados/          -> lista
        POST   /api/academico/certificados/          -> submissão (dispara o motor)
        GET    /api/academico/certificados/{id}/     -> detalhe
        PATCH  /api/academico/certificados/{id}/     -> atualização parcial
        DELETE /api/academico/certificados/{id}/     -> remoção
    """

    queryset = Certificado.objects.select_related("aluno", "categoria").all()
    serializer_class = CertificadoSerializer

    def _calcular_saldo_atual(
        self, aluno: AlunoPerfil, categoria: CategoriaAACC
    ) -> float:
        """
        Soma as horas já computadas pelo aluno nesta categoria,
        desconsiderando certificados rejeitados ou ainda pendentes.
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

    def perform_create(self, serializer: CertificadoSerializer) -> None:
        """
        Hook de criação: integra o rule_engine antes de persistir o certificado.

        Fluxo:
            1. Salva o certificado com status padrão ('pendente_ocr').
            2. Recupera os dados necessários para o motor de regras.
            3. Chama ValidadorCertificado.processar_certificado().
            4. Atualiza o certificado com o resultado calculado.
        """
        # 1. Salva com dados do usuário (status padrão: pendente_ocr)
        certificado: Certificado = serializer.save()

        try:
            aluno = certificado.aluno
            categoria = certificado.categoria
            horas_declaradas = float(certificado.horas_declaradas)
            limite_categoria = float(categoria.limite_maximo_horas)

            # 2. Calcula o saldo atual do aluno nesta categoria
            saldo_atual = self._calcular_saldo_atual(aluno, categoria)

            # 3. Invoca o motor de regras (Python puro — sem acesso ao DB)
            validador = ValidadorCertificado()
            resultado = validador.processar_certificado(
                horas_informadas=horas_declaradas,
                limite_cat=limite_categoria,
                saldo_cat=saldo_atual,
            )

            # 4. Persiste o resultado no banco
            certificado.status = resultado["status_sugerido"]
            certificado.horas_validadas_ocr = int(horas_declaradas)
            certificado.horas_computadas_final = int(resultado["horas_finais"])
            certificado.horas_descartadas = int(resultado["horas_descartadas"])
            certificado.indice_confianca_ocr = resultado["confianca_ocr"]
            certificado.texto_extraido_ocr = resultado["texto_extraido"]
            certificado.motivo_status = resultado["motivo"]
            
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
                horas_descartadas=int(resultado["horas_descartadas"])
            )

            logger.info(
                "Certificado %s processado: status=%s, horas_finais=%s",
                certificado.id,
                resultado["status_sugerido"],
                resultado["horas_finais"],
            )

        except Exception as exc:  # noqa: BLE001
            # Em caso de falha no motor, mantém o certificado como pendente_ocr
            # para que um coordenador possa revisá-lo manualmente.
            logger.exception(
                "Erro ao processar certificado %s: %s", certificado.id, exc
            )
