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
    codigo_slug = models.CharField(
        max_length=60,
        unique=True,
        null=True,
        blank=True,
        verbose_name="Código Slug (SEBR)",
        help_text="Chave imutável que referencia a categoria em LIMITES_CATEGORIAS (resolucao_057.py).",
    )
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
    horas_declaradas = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, verbose_name="Horas Declaradas")

    # ── Metadados descritivos (Copiloto / Anexo I) ────────────────────────────
    titulo_atividade = models.CharField(
        max_length=255, null=True, blank=True,
        verbose_name="Título da Atividade",
        help_text="Extraído pelo Copiloto OCR e confirmado pelo aluno. Usado no Anexo I.",
    )
    periodo_realizacao = models.CharField(
        max_length=100, null=True, blank=True,
        verbose_name="Período de Realização",
        help_text="Ex: 'Janeiro/2025' ou '10/01/2025 a 15/03/2025'. Confirmado pelo aluno.",
    )

    texto_extraido_ocr = models.TextField(blank=True, null=True, verbose_name="Texto Bruto Extraído (OCR)")
    horas_validadas_ocr = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Horas Validadas OCR")
    horas_computadas_final = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True,
        verbose_name="Horas Computadas Final",
        help_text="Valor final aprovado pelo SEBR após todos os cortes normativos.",
    )
    horas_descartadas = models.DecimalField(
        max_digits=6, decimal_places=2, default=0,
        verbose_name="Horas Descartadas",
    )
    justificativa_indeferimento = models.TextField(
        blank=True, null=True,
        verbose_name="Justificativa de Indeferimento",
        help_text="Obrigatório quando status=rejeitado (RN03).",
    )
    
    indice_confianca_ocr = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Índice de Confiança OCR (%)")
    
    # Novos campos analíticos da IA
    horas_sugeridas_ia = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Horas Sugeridas IA")
    confianca_ia = models.IntegerField(null=True, blank=True, verbose_name="Confiança IA (%)")
    
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pendente_ocr', verbose_name="Status")
    motivo_status = models.CharField(max_length=255, blank=True, null=True, verbose_name="Motivo/Justificativa do Status")
    
    data_envio = models.DateTimeField(auto_now_add=True, verbose_name="Data de Envio")
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name="Última Atualização")

    class Meta:
        verbose_name = "Certificado"
        verbose_name_plural = "Certificados"
        ordering = ['-data_envio']

    def __str__(self):
        return f"Certificado {self.id} - {self.aluno.matricula} ({self.get_status_display()})"


class RuleValidationLog(models.Model):
    certificado = models.ForeignKey(Certificado, on_delete=models.CASCADE, related_name='logs_auditoria', verbose_name="Certificado")
    usuario_responsavel = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Usuário Responsável")
    
    regra_aplicada = models.CharField(max_length=255, verbose_name="Regra Aplicada")
    artigo_resolucao = models.CharField(max_length=255, default="Resolução CONSUNI nº 057/2025", verbose_name="Artigo/Resolução")
    justificativa = models.TextField(verbose_name="Justificativa")
    
    horas_enviadas = models.IntegerField(verbose_name="Horas Enviadas")
    horas_computadas = models.IntegerField(verbose_name="Horas Computadas")
    horas_descartadas = models.IntegerField(verbose_name="Horas Descartadas")
    
    data_validacao = models.DateTimeField(auto_now_add=True, verbose_name="Data da Validação")

    class Meta:
        verbose_name = "Log de Validação de Regra"
        verbose_name_plural = "Logs de Validação de Regras"
        ordering = ['-data_validacao']

    def __str__(self):
        return f"Log Certificado {self.certificado.id} - {self.regra_aplicada}"


class Requerimento(models.Model):
    aluno = models.ForeignKey(AlunoPerfil, on_delete=models.CASCADE, related_name='requerimentos', verbose_name="Aluno")
    certificados = models.ManyToManyField(Certificado, related_name='requerimentos', verbose_name="Certificados Aprovados")
    data_geracao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Geração")
    arquivo_pdf = models.FileField(upload_to='requerimentos_gerados/', null=True, blank=True, verbose_name="PDF do Anexo I")

    class Meta:
        verbose_name = "Requerimento (Anexo I)"
        verbose_name_plural = "Requerimentos (Anexo I)"
        ordering = ['-data_geracao']

    def __str__(self):
        return f"Requerimento {self.id} - {self.aluno.matricula}"