from django.db import models
from django.conf import settings

class Curso(models.Model):
    nome = models.CharField(max_length=200, verbose_name="Nome do Curso")
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código do Curso")

    class Meta:
        verbose_name = "Curso"
        verbose_name_plural = "Cursos"

    def __str__(self):
        return self.nome


class MatrizCurricular(models.Model):
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='matrizes', verbose_name="Curso")
    ano_vigencia = models.IntegerField(verbose_name="Ano de Vigência")
    horas_totais_exigidas = models.IntegerField(verbose_name="Horas Totais Exigidas")

    class Meta:
        verbose_name = "Matriz Curricular"
        verbose_name_plural = "Matrizes Curriculares"

    def __str__(self):
        return f"{self.curso.nome} - {self.ano_vigencia} ({self.horas_totais_exigidas}h)"


class AlunoPerfil(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='perfil_aluno', verbose_name="Usuário")
    matricula = models.CharField(max_length=50, unique=True, verbose_name="Matrícula")
    curso = models.ForeignKey(Curso, on_delete=models.PROTECT, related_name='alunos', verbose_name="Curso")
    matriz_curricular = models.ForeignKey(MatrizCurricular, on_delete=models.PROTECT, related_name='alunos', verbose_name="Matriz Curricular")

    class Meta:
        verbose_name = "Perfil de Aluno"
        verbose_name_plural = "Perfis de Alunos"

    def __str__(self):
        return f"{self.usuario.get_full_name() or self.usuario.username} - {self.matricula}"


class CategoriaAACC(models.Model):
    EIXO_CHOICES = [
        ('Ensino', 'Ensino'),
        ('Pesquisa', 'Pesquisa'),
        ('Extensao', 'Extensão'),
    ]

    nome = models.CharField(max_length=255, verbose_name="Nome da Categoria")
    eixo = models.CharField(max_length=20, choices=EIXO_CHOICES, verbose_name="Eixo")
    limite_maximo_horas = models.IntegerField(verbose_name="Limite Máximo de Horas")

    class Meta:
        verbose_name = "Categoria AACC"
        verbose_name_plural = "Categorias AACC"

    def __str__(self):
        return f"{self.nome} ({self.eixo})"


class Certificado(models.Model):
    STATUS_CHOICES = [
        ('pendente_ocr', 'Pendente OCR'),
        ('revisao_manual', 'Revisão Manual'),
        ('aprovado', 'Aprovado'),
        ('rejeitado', 'Rejeitado'),
        ('requerimento_gerado', 'Requerimento Gerado'),
    ]

    aluno = models.ForeignKey(AlunoPerfil, on_delete=models.CASCADE, related_name='certificados', verbose_name="Aluno")
    categoria = models.ForeignKey(CategoriaAACC, on_delete=models.PROTECT, related_name='certificados', verbose_name="Categoria")
    
    arquivo_pdf = models.FileField(upload_to='uploads_alunos/', verbose_name="Arquivo PDF")
    horas_declaradas = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Horas Declaradas")
    
    horas_validadas_ocr = models.IntegerField(null=True, blank=True, verbose_name="Horas Validadas OCR")
    horas_computadas_final = models.IntegerField(null=True, blank=True, verbose_name="Horas Computadas Final")
    
    indice_confianca_ocr = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Índice de Confiança OCR (%)")
    
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pendente_ocr', verbose_name="Status")
    
    data_envio = models.DateTimeField(auto_now_add=True, verbose_name="Data de Envio")
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name="Última Atualização")

    class Meta:
        verbose_name = "Certificado"
        verbose_name_plural = "Certificados"
        ordering = ['-data_envio']

    def __str__(self):
        return f"Certificado {self.id} - {self.aluno.matricula} ({self.get_status_display()})"