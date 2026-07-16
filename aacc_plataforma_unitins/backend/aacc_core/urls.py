from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # Autenticação JWT
    path('api/accounts/', include('accounts.urls')),
    # Domínio académico
    path('api/academico/', include('academico.urls')),
]

# Serve ficheiros de media em ambiente de desenvolvimento (DEBUG=True)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)