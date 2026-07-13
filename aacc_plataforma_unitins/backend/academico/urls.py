"""
URLs — App: academico

Registra as rotas dos ViewSets usando o DefaultRouter do DRF,
que gera automaticamente as URLs RESTful para cada recurso.

Prefixo base (configurado em aacc_core/urls.py): /api/academico/

Rotas geradas:
    /api/academico/categorias/          -> CategoriaAACCViewSet (GET list/retrieve)
    /api/academico/certificados/        -> CertificadoViewSet   (GET/POST/PATCH/DELETE)
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from academico.views import CategoriaAACCViewSet, CertificadoViewSet

router = DefaultRouter()
router.register(r"categorias", CategoriaAACCViewSet, basename="categoria")
router.register(r"certificados", CertificadoViewSet, basename="certificado")

urlpatterns = [
    path("", include(router.urls)),
]
