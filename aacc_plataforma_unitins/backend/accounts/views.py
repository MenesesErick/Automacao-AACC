"""
accounts/views.py

Views de autenticação da plataforma AACC.
"""

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
    GET /api/accounts/me/ → dados completos do usuário logado + vínculo institucional.

    Somente leitura: nome, e-mail, CPF, matrícula, curso e credenciais são dados
    sincronizados da base da universidade (RNF02) e não são editáveis pela plataforma.
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