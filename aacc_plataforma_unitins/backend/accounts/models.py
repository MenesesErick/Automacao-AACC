from django.db import models
from django.contrib.auth.models import AbstractUser

class Usuario(AbstractUser):
    is_coordenador = models.BooleanField(default=False, verbose_name="É coordenador?")
    is_aluno = models.BooleanField(default=False, verbose_name="É aluno?")
    cpf = models.CharField(max_length=14, unique=True, verbose_name="CPF")

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    def __str__(self):
        return self.get_full_name() or self.username