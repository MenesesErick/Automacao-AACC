"""
Serializers — App: academico

Define a camada de serialização/deserialização para os modelos expostos
pela API REST. Os campos preenchidos automaticamente pelo motor de regras
são declarados como read_only para impedir que o cliente os sobrescreva.
"""

from rest_framework import serializers

import datetime

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction

from academico.models import (
    CategoriaAACC, Certificado, CoordenadorPerfil, Curso, Eixo, MatrizCurricular,
    RuleValidationLog, Requerimento,
)


class CursoSerializer(serializers.ModelSerializer):
    """
    Curso + meta de carga horária (120h, 180h...).

    A meta vive na MatrizCurricular mais recente do curso; ao criar/editar,
    `horas_totais_exigidas` cria/atualiza essa matriz automaticamente.
    """

    horas_totais_exigidas = serializers.IntegerField(min_value=1, required=False)
    ano_vigencia = serializers.IntegerField(required=False, min_value=2000)

    class Meta:
        model = Curso
        fields = ["id", "nome", "codigo", "horas_totais_exigidas", "ano_vigencia"]

    def to_representation(self, instance):
        data = {"id": instance.id, "nome": instance.nome, "codigo": instance.codigo}
        matriz = instance.matrizes.order_by("-ano_vigencia", "-id").first()
        data["horas_totais_exigidas"] = matriz.horas_totais_exigidas if matriz else None
        data["ano_vigencia"] = matriz.ano_vigencia if matriz else None
        return data

    def validate(self, attrs):
        # Na criação a meta de horas é obrigatória.
        if self.instance is None and "horas_totais_exigidas" not in attrs:
            raise serializers.ValidationError(
                {"horas_totais_exigidas": "Este campo é obrigatório."}
            )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        horas = validated_data.pop("horas_totais_exigidas")
        ano = validated_data.pop("ano_vigencia", datetime.date.today().year)
        curso = Curso.objects.create(**validated_data)
        MatrizCurricular.objects.create(curso=curso, ano_vigencia=ano, horas_totais_exigidas=horas)
        return curso

    @transaction.atomic
    def update(self, instance, validated_data):
        horas = validated_data.pop("horas_totais_exigidas", None)
        ano = validated_data.pop("ano_vigencia", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if horas is not None or ano is not None:
            matriz = instance.matrizes.order_by("-ano_vigencia", "-id").first()
            if matriz is None:
                if horas is None:
                    raise serializers.ValidationError(
                        {"horas_totais_exigidas": "Informe a meta de horas para criar a matriz."}
                    )
                MatrizCurricular.objects.create(
                    curso=instance,
                    ano_vigencia=ano or datetime.date.today().year,
                    horas_totais_exigidas=horas,
                )
            else:
                if horas is not None:
                    matriz.horas_totais_exigidas = horas
                if ano is not None:
                    matriz.ano_vigencia = ano
                matriz.save()
        return instance


class CoordenadorSerializer(serializers.ModelSerializer):
    """
    Lista/cria contas de Coordenador vinculadas a um Curso (RN06).

    Na criação: is_staff=True e is_coordenador=True (is_aluno=False, is_superuser=False)
    e criação imediata do CoordenadorPerfil com o `curso_id` recebido.
    O e-mail institucional é usado como username (login do sistema).
    Na listagem retorna `curso_id` e `curso_nome`.
    """

    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    curso_id = serializers.PrimaryKeyRelatedField(
        source="curso", queryset=Curso.objects.all(), write_only=True,
    )
    curso_nome = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = [
            "id", "first_name", "last_name", "email", "cpf", "password",
            "curso_id", "curso_nome", "is_active", "date_joined",
        ]
        read_only_fields = ["id", "date_joined"]
        extra_kwargs = {"email": {"required": True}, "first_name": {"required": True}}

    @staticmethod
    def _curso_do(user):
        perfil = getattr(user, "perfil_coordenador", None)
        return perfil.curso if perfil else None

    def get_curso_nome(self, obj):
        curso = self._curso_do(obj)
        return curso.nome if curso else None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        curso = self._curso_do(instance)
        data["curso_id"] = curso.id if curso else None
        return data

    def validate_email(self, value):
        value = value.strip().lower()
        if not value.endswith("@unitins.br"):
            raise serializers.ValidationError("Apenas e-mails institucionais (@unitins.br) são permitidos.")
        if get_user_model().objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Já existe um usuário com este e-mail.")
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    @transaction.atomic
    def create(self, validated_data):
        password = validated_data.pop("password")
        curso = validated_data.pop("curso")
        User = get_user_model()
        user = User(
            username=validated_data["email"],
            is_staff=True,
            is_superuser=False,
            is_coordenador=True,
            is_aluno=False,
            **validated_data,
        )
        user.set_password(password)
        user.save()
        CoordenadorPerfil.objects.create(usuario=user, curso=curso)
        return user


class EixoSerializer(serializers.ModelSerializer):
    """CRUD de Eixos Formativos (todos os campos)."""

    class Meta:
        model = Eixo
        fields = "__all__"


class CategoriaAACCSerializer(serializers.ModelSerializer):
    """
    Serializer para CategoriaAACC.
    """
    tooltip = serializers.SerializerMethodField()
    # Lê/escreve o eixo pelo ID
    eixo_nome = serializers.CharField(source='eixo.nome', read_only=True)

    class Meta:
        model = CategoriaAACC
        fields = ["id", "nome", "descricao", "eixo", "eixo_nome", "codigo_slug", "limite_maximo_horas", "limite_por_certificado", "tooltip"]

    def get_tooltip(self, obj):
        if not obj.codigo_slug:
            return ""
        from academico.rules.resolucao_057 import calculadora
        try:
            regra = calculadora.get_regra(obj.codigo_slug)
            return regra.tooltip
        except ValueError:
            return ""


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

    # Identidade do aluno (read-only — nunca pode ser alterado pelo cliente)
    aluno_nome = serializers.SerializerMethodField()
    aluno_matricula = serializers.CharField(
        source="aluno.matricula", read_only=True
    )
    aluno_curso = serializers.CharField(
        source="aluno.curso.nome", read_only=True
    )

    def get_aluno_nome(self, obj):
        """Retorna o nome completo ou username do aluno."""
        usuario = obj.aluno.usuario
        return usuario.get_full_name() or usuario.username

    # Objeto completo da categoria (com tooltip e tetos para o painel do coordenador)
    categoria_obj = serializers.SerializerMethodField()

    def get_categoria_obj(self, obj):
        """Retorna os dados completos da categoria, incluindo tooltip do SEBR."""
        cat = obj.categoria
        if not cat:
            return None
        from academico.rules.resolucao_057 import calculadora
        tooltip = ""
        teto_total = None
        teto_por_evento = None
        try:
            if cat.codigo_slug:
                regra = calculadora.get_regra(cat.codigo_slug)
                tooltip = regra.tooltip
                teto_total = regra.teto_total
                teto_por_evento = regra.teto_por_evento
        except (ValueError, AttributeError):
            pass
        return {
            "id": cat.id,
            "nome": cat.nome,
            "eixo": cat.eixo.nome,
            "codigo_slug": cat.codigo_slug,
            "limite_maximo_horas": cat.limite_maximo_horas,
            "teto_total": teto_total,
            "teto_por_evento": teto_por_evento,
            "tooltip": tooltip,
        }

    # Saldo atual do aluno nesta categoria (horas já aprovadas)
    saldo_atual_categoria = serializers.SerializerMethodField()

    def get_saldo_atual_categoria(self, obj):
        """Soma das horas_computadas_final aprovadas pelo aluno nesta categoria."""
        from academico.models import Certificado
        saldo = (
            Certificado.objects
            .filter(
                aluno=obj.aluno,
                categoria=obj.categoria,
                status__in=["aprovado", "requerimento_gerado"],
            )
            .exclude(id=obj.id)  # exclui o próprio certificado em avaliação
            .exclude(horas_computadas_final__isnull=True)
            .values_list("horas_computadas_final", flat=True)
        )
        return float(sum(saldo))

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
            "aluno_nome",
            "aluno_matricula",
            "aluno_curso",
            "categoria",
            "categoria_nome",
            "categoria_obj",
            "arquivo_pdf",
            "horas_declaradas",
            # --- metadados descritivos (Copiloto / Anexo I) ---
            "titulo_atividade",
            "periodo_realizacao",
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
            "justificativa_indeferimento",
            # --- saldo do aluno na categoria ---
            "saldo_atual_categoria",
            # --- timestamps ---
            "data_envio",
            "data_atualizacao",
        ]
        read_only_fields = [
            "aluno",
            "aluno_nome",
            "aluno_matricula",
            "aluno_curso",
            "categoria_obj",
            "saldo_atual_categoria",
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
            "justificativa_indeferimento",
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