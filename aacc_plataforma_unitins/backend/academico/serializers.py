"""
Serializers — App: academico

Define a camada de serialização/deserialização para os modelos expostos
pela API REST. Os campos preenchidos automaticamente pelo motor de regras
são declarados como read_only para impedir que o cliente os sobrescreva.
"""

from rest_framework import serializers

from academico.models import CategoriaAACC, Certificado, RuleValidationLog, Requerimento


class CategoriaAACCSerializer(serializers.ModelSerializer):
    """
    Serializer de leitura para CategoriaAACC.

    Expõe todas as categorias de atividade definidas pela Resolução 057,
    incluindo o eixo e o teto máximo de horas aproveitáveis por categoria.
    """

    class Meta:
        model = CategoriaAACC
        fields = ["id", "nome", "eixo", "limite_maximo_horas"]


class CertificadoSerializer(serializers.ModelSerializer):
    """
    Serializer para Certificado.

    Campos preenchidos exclusivamente pelo motor de regras (read-only):
        - horas_validadas_ocr: lidas pelo ocr_engine.
        - horas_computadas_final: resultado do CalculadoraAACC.
        - indice_confianca_ocr: confiança retornada pelo OCR.
        - status: determinado pelo ValidadorCertificado.

    O cliente deve enviar apenas:
        - categoria e arquivo_pdf.
        - horas_declaradas é OPCIONAL — preenchido automaticamente pelo OCR.
    """

    # Representa o nome legível da categoria na leitura
    categoria_nome = serializers.CharField(
        source="categoria.nome", read_only=True
    )
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )

    # horas_declaradas é opcional: o OCR preenche automaticamente
    horas_declaradas = serializers.DecimalField(
        max_digits=6, decimal_places=2,
        required=False, allow_null=True, default=0
    )

    class Meta:
        model = Certificado
        fields = [
            "id",
            "aluno",
            "categoria",
            "categoria_nome",
            "arquivo_pdf",
            "horas_declaradas",
            # --- campos controlados pelo motor de regras ---
            "texto_extraido_ocr",
            "horas_validadas_ocr",
            "horas_computadas_final",
            "horas_descartadas",
            "indice_confianca_ocr",
            "horas_sugeridas_ia",
            "confianca_ia",
            "status",
            "status_display",
            "motivo_status",
            # --- timestamps ---
            "data_envio",
            "data_atualizacao",
        ]
        read_only_fields = [
            "texto_extraido_ocr",
            "horas_validadas_ocr",
            "horas_computadas_final",
            "horas_descartadas",
            "indice_confianca_ocr",
            "horas_sugeridas_ia",
            "confianca_ia",
            "status",
            "status_display",
            "motivo_status",
            "data_envio",
            "data_atualizacao",
        ]


class RuleValidationLogSerializer(serializers.ModelSerializer):
    """Serializer somente-leitura para Logs de Auditoria."""
    
    usuario_nome = serializers.CharField(source="usuario_responsavel.get_full_name", read_only=True, default="Sistema")

    class Meta:
        model = RuleValidationLog
        fields = "__all__"


class RequerimentoSerializer(serializers.ModelSerializer):
    """Serializer para Requerimentos de Horas (Anexo I)."""

    class Meta:
        model = Requerimento
        fields = "__all__"