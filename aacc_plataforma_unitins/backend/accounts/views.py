"""
accounts/views.py

Views de autenticação da plataforma AACC.
"""

from rest_framework_simplejwt.views import TokenObtainPairView

from accounts.serializers import CustomTokenObtainPairSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Substitui a view padrão do simplejwt para usar o serializer customizado
    que valida o domínio institucional e injeta claims de perfil no JWT.
    """
    serializer_class = CustomTokenObtainPairSerializer