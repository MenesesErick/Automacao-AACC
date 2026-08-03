"""
academico/management/commands/processar_fila_ocr.py

Comando de varredura em lote (batch) do pipeline de OCR.

Procura todos os Certificados cujo OCR ainda não foi executado
(status='pendente_ocr' ou horas_sugeridas_ia=None) e processa cada um,
gravando os resultados directamente no banco de dados.

Uso:
    python manage.py processar_fila_ocr
    python manage.py processar_fila_ocr --status pendente_ocr
    python manage.py processar_fila_ocr --dry-run   (mostra o que faria, sem alterar BD)
"""

import os
import time

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q


class Command(BaseCommand):
    help = (
        "Processa em lote o OCR de todos os certificados pendentes. "
        "Actualiza horas_sugeridas_ia, confianca_ia e status no banco de dados."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--status",
            default="pendente_ocr",
            choices=["pendente_ocr", "revisao_manual", "todos"],
            help="Filtra os certificados a processar pelo status (padrão: pendente_ocr).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Mostra o que seria processado sem alterar o banco de dados.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limita o número de documentos a processar nesta execução.",
        )

    def handle(self, *args, **options):
        from academico.models import Certificado
        from academico.services.ocr_service import processar_pdf

        status_filtro = options["status"]
        dry_run       = options["dry_run"]
        limit         = options["limit"]

        # ── Construção da QuerySet ───────────────────────────────────────────
        if status_filtro == "todos":
            qs = Certificado.objects.filter(
                Q(horas_sugeridas_ia__isnull=True) | Q(horas_sugeridas_ia=0)
            )
        elif status_filtro == "revisao_manual":
            qs = Certificado.objects.filter(status="revisao_manual")
        else:
            # padrão: pendente_ocr OU sugestão da IA ainda ausente
            qs = Certificado.objects.filter(
                Q(status="pendente_ocr") |
                Q(horas_sugeridas_ia__isnull=True, status="revisao_manual")
            )

        qs = qs.select_related("aluno", "aluno__usuario").order_by("data_envio")

        if limit:
            qs = qs[:limit]

        total = qs.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS("[OK] Nenhum certificado pendente encontrado."))
            return

        mode_label = "[DRY-RUN] " if dry_run else ""
        self.stdout.write(
            self.style.WARNING(
                f"\n{mode_label}>>> {total} certificado(s) encontrado(s) para processar OCR.\n"
                + ("-" * 60)
            )
        )

        # -- Loop de processamento ---------------------------------------------
        ok = err = ambiguo = 0
        inicio = time.time()

        for cert in qs:
            matricula = cert.aluno.matricula if cert.aluno_id else "N/A"

            if not cert.arquivo_pdf:
                self.stdout.write(
                    self.style.WARNING(f"  [SKIP] ID {cert.id:>5} | {matricula} — sem arquivo PDF")
                )
                err += 1
                continue

            caminho = os.path.join(settings.MEDIA_ROOT, cert.arquivo_pdf.name)

            if not os.path.exists(caminho):
                self.stdout.write(
                    self.style.ERROR(f"  [ERRO] ID {cert.id:>5} | {matricula} — ficheiro não encontrado: {caminho}")
                )
                err += 1
                continue

            # Invoca o OCR Service
            resultado = processar_pdf(caminho)

            # -- Formata a linha de log ----------------------------------------
            if resultado.sucesso:
                conf     = int(resultado.indice_confianca)
                horas    = resultado.horas_encontradas
                tipo     = resultado.padrao_usado
                is_ambig = conf <= 30

                if is_ambig:
                    cor     = self.style.WARNING
                    prefixo = "[AMBIG]  "
                    ambiguo += 1
                else:
                    cor     = self.style.SUCCESS
                    prefixo = "[OK]     "
                    ok += 1

                linha = (
                    f"  [{prefixo}] ID {cert.id:>5} | {matricula:<15} | "
                    f"{horas:>6.2f}h | conf={conf:>3}% | {tipo}"
                )
                self.stdout.write(cor(linha))

            else:
                cor = self.style.ERROR
                self.stdout.write(
                    cor(
                        f"  [FALHA] ID {cert.id:>5} | {matricula:<15} | "
                        f"Erro: {resultado.erro or 'sem texto extraível'}"
                    )
                )
                err += 1

            # -- Persiste no banco (salvo em dry-run) -------------------------
            if not dry_run:
                try:
                    with transaction.atomic():
                        cert.horas_sugeridas_ia  = resultado.horas_encontradas if resultado.sucesso else None
                        cert.confianca_ia        = int(resultado.indice_confianca) if resultado.sucesso else None
                        cert.horas_validadas_ocr = resultado.horas_encontradas if resultado.sucesso else None
                        cert.texto_extraido_ocr  = resultado.texto_extraido or ""
                        cert.indice_confianca_ocr = resultado.indice_confianca

                        # Define status
                        if resultado.sucesso:
                            cert.status       = "revisao_manual"
                            cert.motivo_status = (
                                f"OCR (batch): {resultado.horas_encontradas:.2f}h encontradas "
                                f"via {resultado.padrao_usado} "
                                f"(confiança: {int(resultado.indice_confianca)}%)."
                            )
                            if resultado.erro:   # flag de ambiguidade
                                cert.motivo_status += f" [AMBIG] {resultado.erro}"
                        else:
                            cert.status = "revisao_manual"
                            cert.motivo_status = (
                                f"OCR (batch) não encontrou horas. "
                                f"Erro: {resultado.erro or 'texto insuficiente'}."
                            )

                        cert.save(update_fields=[
                            "horas_sugeridas_ia",
                            "confianca_ia",
                            "horas_validadas_ocr",
                            "texto_extraido_ocr",
                            "indice_confianca_ocr",
                            "status",
                            "motivo_status",
                            "data_atualizacao",
                        ])
                except Exception as exc:
                    self.stdout.write(
                        self.style.ERROR(f"         ↳ BD falhou para cert {cert.id}: {exc}")
                    )
                    err += 1

        # -- Sumário final -----------------------------------------------------
        elapsed = time.time() - inicio
        self.stdout.write("\n" + ("-" * 60))
        self.stdout.write(
            self.style.SUCCESS(
                f"{'[DRY-RUN] ' if dry_run else ''}Concluido em {elapsed:.1f}s -- "
                f"[OK] {ok} OK | [AMBIG] {ambiguo} ambiguos | [ERRO] {err} falhas"
            )
        )
        if dry_run:
            self.stdout.write(self.style.WARNING("  -> Nenhuma alteracao foi feita no banco de dados."))
