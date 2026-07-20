from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.views.decorators.clickjacking import xframe_options_sameorigin

urlpatterns = [
    path('admin/', admin.site.urls),
    # Autenticação JWT
    path('api/accounts/', include('accounts.urls')),
    # Domínio académico
    path('api/academico/', include('academico.urls')),
]

# Serve ficheiros de media em ambiente de desenvolvimento (DEBUG=True)
if settings.DEBUG:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', xframe_options_sameorigin(serve), {
            'document_root': settings.MEDIA_ROOT,
        }),
    ]