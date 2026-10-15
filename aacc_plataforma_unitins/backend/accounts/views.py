"""
accounts/views.py

Views de autenticação da plataforma AACC.
"""

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from accounts.serializers import CustomTokenObtainPairSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Substitui a view padrão do simplejwt para usar o serializer customizado
    que valida o domínio institucional e injeta claims de perfil no JWT.
    """
    serializer_class = CustomTokenObtainPairSerializer


class MeView(APIView):
    """
    GET   /api/accounts/me/ → dados completos do usuário logado + vínculo institucional.
    PATCH /api/accounts/me/ → atualiza SOMENTE `first_name` e, opcionalmente, a senha
                              (`senha_atual` + `nova_senha`).

    E-mail, CPF, matrícula e curso são dados sincronizados do RM (RNF02) e nunca
    são alterados por aqui: qualquer outro campo enviado é ignorado.
    """
    permission_classes = [IsAuthenticated]

    @staticmethod
    def _serializar(user):
        if user.is_superuser:
            role = "admin"
        elif user.is_coordenador:
            role = "coordenador"
        else:
            role = "aluno"

        data = {
            "id": user.id,
            "first_name": user.first_name,
            "email": user.email,
            "cpf": user.cpf,
            "role": role,
        }

        if role == "aluno":
            perfil = getattr(user, "perfil_aluno", None)
            if perfil:
                data.update({
                    "matricula": perfil.matricula,
                    "curso_nome": perfil.curso.nome,
                    "horas_totais_exigidas": perfil.matriz_curricular.horas_totais_exigidas,
                })
        elif role == "coordenador":
            perfil = getattr(user, "perfil_coordenador", None)
            if perfil:
                data["curso_nome"] = perfil.curso.nome
        else:
            data["cargo"] = "Administrador Sistêmico"

        return data

    def get(self, request):
        return Response(self._serializar(request.user))

    def patch(self, request):
        user = request.user
        erros = {}

        nome = request.data.get("first_name")
        if nome is not None:
            nome = str(nome).strip()
            if not nome:
                erros["first_name"] = "O nome não pode ficar em branco."
            elif len(nome) > 150:
                erros["first_name"] = "O nome deve ter no máximo 150 caracteres."

        senha_atual = request.data.get("senha_atual")
        nova_senha = request.data.get("nova_senha")
        trocar_senha = bool(senha_atual or nova_senha)
        if trocar_senha:
            if not senha_atual or not nova_senha:
                erros["nova_senha"] = "Informe a senha atual e a nova senha."
            elif not user.check_password(senha_atual):
                erros["senha_atual"] = "Senha atual incorreta."
            else:
                try:
                    validate_password(nova_senha, user)
                except DjangoValidationError as exc:
                    erros["nova_senha"] = " ".join(exc.messages)

        if erros:
            return Response(
                {"detail": next(iter(erros.values())), **erros},
                status=status.HTTP_400_BAD_REQUEST,
            )

        campos = []
        if nome is not None:
            user.first_name = nome
            campos.append("first_name")
        if trocar_senha:
            user.set_password(nova_senha)
            campos.append("password")
        if campos:
            user.save(update_fields=campos)

        return Response(self._serializar(user))