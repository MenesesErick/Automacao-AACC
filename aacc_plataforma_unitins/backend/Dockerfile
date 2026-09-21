# ─── Imagem base ─────────────────────────────────────────────────────────────
FROM python:3.11-slim

# ─── Variáveis de ambiente ───────────────────────────────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# ─── Dependências do sistema operacional ─────────────────────────────────────
# tesseract-ocr          : motor de OCR
# tesseract-ocr-por      : modelo de idioma português (obrigatório para AACC)
# libpq-dev              : headers da libpq (psycopg2 precisa para compilar)
# gcc                    : compilador C (dependências nativas do pip)
RUN apt-get update && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-por \
        libpq-dev \
        gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ─── Diretório de trabalho ────────────────────────────────────────────────────
WORKDIR /app

# ─── Dependências Python ──────────────────────────────────────────────────────
# Copiamos só o requirements.txt primeiro para aproveitar o cache de camadas
# (evita reinstalar tudo quando só o código-fonte muda).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ─── Código-fonte ─────────────────────────────────────────────────────────────
COPY . .
RUN chmod +x start.sh

# ─── Porta exposta ────────────────────────────────────────────────────────────
EXPOSE 8000

# ─── Comando de inicialização ─────────────────────────────────────────────────
CMD ["./start.sh"]
