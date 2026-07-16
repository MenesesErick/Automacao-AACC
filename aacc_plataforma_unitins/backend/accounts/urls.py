"""
accounts/urls.py

Endpoints de autenticação JWT da plataforma AACC.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.views import CustomTokenObtainPairView

urlpatterns = [
    # POST { "username": "coord@unitins.br", "password": "..." }
    # → { access, refresh }  (com claims customizados de perfil)
    path('token/',         CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),

    # POST { "refresh": "..." } → { access }
    path('token/refresh/', TokenRefreshView.as_view(),          name='token_refresh'),
]
