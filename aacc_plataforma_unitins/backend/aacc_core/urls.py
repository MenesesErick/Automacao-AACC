from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Adicionaremos as rotas dos apps (accounts, academico) aqui posteriormente
]