"""
academico/management/commands/gerar_experimento_tcc.py

Benchmark estatístico do TCC (Capítulo 4) — 100% em memória.

Gera N documentos comprobatórios sintéticos (padrão: 300), passa cada PDF
(bytes / io.BytesIO) pelo pipeline real de OCR + titularidade + trava RN04 e
exporta apenas o JSON de resultados (`relatorio_dataset_massivo.json`, na raiz
do backend).

NÃO grava Certificado, RuleValidationLog nem arquivos PDF: o aluno é usado
somente como fonte de nome/CPF/matrícula.

Uso: python manage.py gerar_experimento_tcc [--total 300] [--seed 42]
"""
import gc
import io
import json
import os
import random
from collections import Counter

from django.conf import settings
from django.core.management.base import BaseCommand

from academico.management.gerador_certificados import (
    CATALOGO_ATIVIDADES,
    gerar_documento_comprobatorio,
    gerar_periodo,
)
from academico.models import AlunoPerfil
from academico.services.ocr_service import (
    extrair_e_validar_titularidade,
    processar_pdf,
)

NOME_RELATORIO_JSON = "relatorio_dataset_massivo.json"
PESO_NIVEIS = [0.60, 0.25, 0.15]  # 60% Nível 1, 25% Nível 2, 15% Nível 3


class Command(BaseCommand):
    help = (
        "Executa o experimento do TCC em memória (N documentos) e salva apenas "
        f"{NOME_RELATORIO_JSON} na raiz do backend."
    )

    def add_arguments(self, parser):
        parser.add_argument("--total", type=int, default=300, help="Nº de documentos (padrão: 300).")
        parser.add_argument("--seed", type=int, default=42, help="Semente para reprodutibilidade.")

    def handle(self, *args, **options):
        total = options["total"]
        rng = random.Random(options["seed"])

        perfil = (
            AlunoPerfil.objects
            .select_related("usuario")
            .filter(usuario__is_active=True, usuario__first_name__icontains="Erick")
            .first()
            or AlunoPerfil.objects
            .select_related("usuario")
            .filter(usuario__is_active=True)
            .order_by("id")
            .first()
        )

        if perfil is not None:
            nome_aluno = perfil.usuario.get_full_name() or perfil.usuario.username or "Erick Meneses"
            cpf = perfil.usuario.cpf or "000.000.000-00"
            matricula = perfil.matricula or "20250001"
        else:
            nome_aluno = "Erick Meneses"
            cpf = "000.000.000-00"
            matricula = "20250001"

        print(
            f"Iniciando benchmark em memória: {total} documentos | titular: {nome_aluno} | seed={options['seed']}",
            flush=True,
        )

        relatorio = []
        dist = Counter()

        for i in range(1, total + 1):
            slug, titulo, emissor, horas, estilo = rng.choice(CATALOGO_ATIVIDADES)
            periodo, fim = gerar_periodo(horas, rng)
            nivel = rng.choices([1, 2, 3], weights=PESO_NIVEIS)[0]
            dist[nivel] += 1

            pdf_bytes, metadados = gerar_documento_comprobatorio(
                nome_aluno=nome_aluno,
                cpf=cpf,
                matricula=matricula,
                titulo=titulo,
                slug=slug,
                emissor=emissor,
                horas=horas,
                estilo=estilo,
                periodo=periodo,
                data_fim=fim,
                formato="auto",
                rng=rng,
                nivel_dificuldade=nivel,
            )

            # ── Pipeline de OCR 100% em memória (io.BytesIO) ────────────────
            buffer_pdf = io.BytesIO(pdf_bytes)
            ocr = processar_pdf(buffer_pdf)
            buffer_pdf.close()

            titularidade = extrair_e_validar_titularidade(ocr.texto_extraido or "", nome_aluno)
            titularidade_confirmada = titularidade["titularidade_confirmada"]

            confianca_ocr = float(ocr.indice_confianca or 0.0)
            # Trava RN04 do negócio: se titularidade não confirmada, teto de confiança = 65
            if not titularidade_confirmada:
                confianca_ocr = min(confianca_ocr, 65)

            relatorio.append({
                "indice": i,
                "arquivo": f"{metadados['tipo_doc']}_n{nivel}_{i:03d}_{slug}",
                "metadados": metadados,
                "resultado_pipeline": {
                    "horas_extraidas": float(ocr.horas_encontradas) if ocr.horas_encontradas else None,
                    "indice_confianca_ocr": confianca_ocr if confianca_ocr else None,
                    "nome_extraido": (titularidade["nome_extraido"] or None),
                    "titularidade_confirmada": titularidade_confirmada,
                    "similaridade_titularidade": titularidade["similaridade_titularidade"],
                },
            })

            del pdf_bytes, buffer_pdf, ocr

            if i % 10 == 0 or i == total:
                print(
                    f"[{i}/{total}] Documentos processados (N1={dist[1]}, N2={dist[2]}, N3={dist[3]})...",
                    flush=True,
                )
                gc.collect()

        caminho = os.path.join(settings.BASE_DIR, NOME_RELATORIO_JSON)
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(relatorio, f, ensure_ascii=False, indent=2)

        print(f"\nRelatório salvo: {caminho} ({len(relatorio)} registros)", flush=True)
        for n in (1, 2, 3):
            print(f"  Nível {n}: {dist[n]} ({dist[n] / max(total, 1):.0%})", flush=True)
