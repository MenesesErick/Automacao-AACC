"""
Serializers — App: academico

Define a camada de serialização/deserialização para os modelos expostos
pela API REST. Os campos preenchidos automaticamente pelo motor de regras
são declarados como read_only para impedir que o cliente os sobrescreva.
"""

from rest_framework import serializers

from academico.models import CategoriaAACC, Certificado


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
        - aluno, categoria, arquivo_pdf e horas_declaradas.
    """

    # Representa o nome legível da categoria na leitura
    categoria_nome = serializers.CharField(
        source="categoria.nome", read_only=True
    )
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
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
            "horas_validadas_ocr",
            "horas_computadas_final",
            "indice_confianca_ocr",
            "status",
            "status_display",
            # --- timestamps ---
            "data_envio",
            "data_atualizacao",
        ]
        read_only_fields = [
            "horas_validadas_ocr",
            "horas_computadas_final",
            "indice_confianca_ocr",
            "status",
            "status_display",
            "data_envio",
            "data_atualizacao",
        ]