"""
URLs — App: academico

Registra as rotas dos ViewSets usando o DefaultRouter do DRF,
que gera automaticamente as URLs RESTful para cada recurso.

Prefixo base (configurado em aacc_core/urls.py): /api/academico/

Rotas geradas automaticamente (Router):
    /api/academico/eixos/                   -> EixoViewSet           (CRUD, somente Admin)
    /api/academico/cursos/                  -> CursoViewSet          (GET autenticado; escrita Admin)
    /api/academico/coordenadores/           -> CoordenadorViewSet    (GET/POST, somente Admin)
    /api/academico/categorias/              -> CategoriaAACCViewSet (GET autenticado; escrita Admin)
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
    CoordenadorViewSet,
    CursoViewSet,
    EixoViewSet,
    CertificadoViewSet,
    ExtratoAlunoMeView,
    ExtratoAlunoCoordenadorView,
    ListaAlunosView,
    AnalisePreviaView,
    GerarAnexoIView,
    NotificacaoViewSet,
)

router = DefaultRouter()
router.register(r"eixos",        EixoViewSet,         basename="eixo")
router.register(r"cursos",       CursoViewSet,        basename="curso")
router.register(r"coordenadores", CoordenadorViewSet, basename="coordenador")
router.register(r"categorias",   CategoriaAACCViewSet, basename="categoria")
router.register(r"certificados", CertificadoViewSet,   basename="certificado")
router.register(r"notificacoes", NotificacaoViewSet,   basename="notificacao")

urlpatterns = [
    # ── Copiloto de Metadados (Anexo I) ────────────────────────────────────
    path("certificados/analise-previa/",   AnalisePreviaView.as_view(),            name="analise-previa"),

    path("", include(router.urls)),

    # ── Alunos (RN02) ───────────────────────────────────────────────────────
    path("alunos/",                             ListaAlunosView.as_view(),              name="lista-alunos"),
    path("alunos/meu-extrato/",                 ExtratoAlunoMeView.as_view(),           name="extrato-aluno-me"),
    path("alunos/<int:perfil_id>/extrato/",      ExtratoAlunoCoordenadorView.as_view(),  name="extrato-aluno-coordenador"),
    path("alunos/<int:perfil_id>/gerar-anexo-i/", GerarAnexoIView.as_view(),            name="gerar-anexo-i"),
]
