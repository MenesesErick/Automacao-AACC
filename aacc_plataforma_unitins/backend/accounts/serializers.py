"""
accounts/serializers.py

Serializer customizado de JWT que:
  1. Valida que o e-mail é institucional (@unitins.br).
  2. Injeta claims de perfil (is_aluno, is_coordenador, nome) no token.
"""

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Extende o serializer padrão do simplejwt para:
      - Rejeitar e-mails não-institucionais.
      - Enriquecer o payload do JWT com dados de perfil do utilizador.
    """

    @classmethod
    def get_token(cls, user):
        """Adiciona claims customizados ao payload do JWT."""
        token = super().get_token(user)

        # Claims de perfil — consumidos pelo frontend para decidir o layout
        token['is_aluno']        = user.is_aluno
        token['is_coordenador']  = user.is_coordenador
        token['nome']            = user.first_name or user.username
        token['email']           = user.email

        return token

    def validate(self, attrs):
        """
        Validação extra: bloqueia e-mails fora do domínio @unitins.br
        antes mesmo de tentar autenticar contra o banco.
        """
        # O username_field do modelo é 'username', mas usamos email como login
        # O campo enviado pelo frontend é 'username' (campo padrão do simplejwt)
        email = attrs.get(self.username_field, '')

        if not str(email).lower().endswith('@unitins.br'):
            raise serializers.ValidationError(
                {'detail': 'Apenas e-mails institucionais (@unitins.br) são permitidos.'}
            )

        return super().validate(attrs)
