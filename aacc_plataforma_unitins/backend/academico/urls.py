"""
URLs — App: academico

Registra as rotas dos ViewSets usando o DefaultRouter do DRF,
que gera automaticamente as URLs RESTful para cada recurso.

Prefixo base (configurado em aacc_core/urls.py): /api/academico/

Rotas geradas automaticamente (Router):
    /api/academico/categorias/              -> CategoriaAACCViewSet (GET list/retrieve)
    /api/academico/certificados/            -> CertificadoViewSet   (GET/POST/PATCH/DELETE)
    /api/academico/certificados/<id>/avaliar/ -> CertificadoViewSet.avaliar (PATCH)

Rotas manuais (APIViews):
    /api/academico/alunos/meu-extrato/      -> ExtratoAlunoMeView        (GET)
    /api/academico/alunos/<id>/extrato/     -> ExtratoAlunoCoordenadorView (GET)
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from academico.views import (
    CategoriaAACCViewSet,
    CertificadoViewSet,
    ExtratoAlunoMeView,
    ExtratoAlunoCoordenadorView,
)

router = DefaultRouter()
router.register(r"categorias",   CategoriaAACCViewSet, basename="categoria")
router.register(r"certificados", CertificadoViewSet,   basename="certificado")

urlpatterns = [
    path("", include(router.urls)),

    # ── Extrato do Aluno (RN02 — Diversidade de Eixos) ──────────────────────
    # Aluno autenticado: GET /api/academico/alunos/meu-extrato/
    path("alunos/meu-extrato/", ExtratoAlunoMeView.as_view(), name="extrato-aluno-me"),
    # Coordenador: GET /api/academico/alunos/<id>/extrato/
    path("alunos/<int:perfil_id>/extrato/", ExtratoAlunoCoordenadorView.as_view(), name="extrato-aluno-coordenador"),
]
