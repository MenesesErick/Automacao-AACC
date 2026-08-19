"""
academico/services/avaliacao_service.py

Serviço de Avaliação de Certificados — Camada de Negócio Isolada.

Responsabilidades:
    - Calcular o saldo atual do aluno numa categoria (RN07).
    - Invocar o SEBR (CalculadoraLimites) para aplicar os limites normativos.
    - Persistir o resultado auditável no Certificado e no RuleValidationLog (RN02).
    - Gerir rejeição com obrigatoriedade de justificativa (RN03).

Filosofia:
    Esta camada NÃO contém lógica de HTTP (sem Request/Response).
    A ViewSet invoca estas funções e traduz os resultados para respostas HTTP.
    Todo o cálculo é determinístico, reproduzível e auditável via RuleValidationLog.
"""

from __future__ import annotations

import logging
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.db.models import Sum

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _calcular_saldo_categoria(aluno, categoria) -> Decimal:
    """
    RN07 — Calcula o saldo de horas já aprovadas pelo aluno nesta categoria.

    Soma APENAS certificados com status 'aprovado' ou 'requerimento_gerado',
    baseando-se estritamente no campo horas_computadas_final (horas validadas
    pelo SEBR). Nunca usa horas_declaradas ou horas_sugeridas_ia.

    Returns:
        Decimal com o saldo actual (0 se não houver certificados aprovados).
    """
    from academico.models import Certificado

    resultado = (
        Certificado.objects
        .filter(
            aluno=aluno,
            categoria=categoria,
            status__in=["aprovado", "requerimento_gerado"],
        )
        .exclude(horas_computadas_final__isnull=True)
        .aggregate(total=Sum("horas_computadas_final"))
    )
    return resultado["total"] or Decimal("0")


# ─────────────────────────────────────────────────────────────────────────────
#  Aprovação
# ─────────────────────────────────────────────────────────────────────────────

def aprovar_certificado(
    certificado,
    horas_confirmadas: Decimal,
    usuario_responsavel=None,
) -> dict:
    """
    Fluxo completo de aprovação de um certificado pelo coordenador.

    Pipeline:
        1. Valida que a categoria possui codigo_slug mapeado no SEBR.
        2. Calcula o saldo actual do aluno na categoria (RN07).
        3. Invoca CalculadoraLimites.aplicar_limites() com o saldo correcto.
        4. Persiste o resultado em horas_computadas_final e horas_descartadas.
        5. Cria RuleValidationLog com todos os campos auditáveis.
        6. Retorna um dict com o resumo da operação para a ViewSet.

    Args:
        certificado:         Instância de Certificado a aprovar.
        horas_confirmadas:   Horas que o coordenador confirmou após ver o OCR.
        usuario_responsavel: Instância de User do coordenador (para o log).

    Returns:
        dict com chaves: horas_deferidas, horas_cortadas_evento,
                         horas_cortadas_total, saldo_apos, regra_aplicada,
                         atingiu_teto_evento, atingiu_teto_total.

    Raises:
        ValueError: Se a categoria não tiver codigo_slug ou slug inválido.
        ValueError: Se horas_confirmadas for <= 0.
    """
    from academico.models import RuleValidationLog
    from academico.rules.resolucao_057 import calculadora

    # ── Validação de entrada ──────────────────────────────────────────────────
    if horas_confirmadas <= 0:
        raise ValueError("horas_confirmadas deve ser um valor positivo.")

    categoria = certificado.categoria

    if not categoria.codigo_slug:
        raise ValueError(
            f"A categoria '{categoria.nome}' (id={categoria.pk}) não possui "
            f"codigo_slug definido. Configure-o no Admin para activar o SEBR."
        )

    # ── RN07: Saldo actual ────────────────────────────────────────────────────
    saldo_atual = _calcular_saldo_categoria(certificado.aluno, categoria)
    logger.info(
        "[SEBR] Cert %s | categoria=%s | saldo_atual=%.2fh | horas_confirmadas=%.2fh",
        certificado.pk, categoria.codigo_slug, saldo_atual, horas_confirmadas,
    )

    # ── Invocação do SEBR ─────────────────────────────────────────────────────
    resultado = calculadora.aplicar_limites(
        codigo_categoria = categoria.codigo_slug,
        horas_submetidas = horas_confirmadas,
        saldo_atual      = saldo_atual,
    )

    logger.info(
        "[SEBR] Cert %s | deferidas=%.2fh | corte_ev=%.2fh | corte_tot=%.2fh | saldo_apos=%.2fh",
        certificado.pk,
        resultado.horas_deferidas,
        resultado.horas_cortadas_evento,
        resultado.horas_cortadas_total,
        resultado.saldo_apos,
    )

    # ── Persistência atómica ──────────────────────────────────────────────────
    with transaction.atomic():
        horas_descartadas = resultado.horas_cortadas_evento + resultado.horas_cortadas_total

        certificado.status                 = "aprovado"
        certificado.horas_computadas_final = resultado.horas_deferidas
        certificado.horas_descartadas      = horas_descartadas
        certificado.justificativa_indeferimento = None   # limpa eventual rejeição anterior
        certificado.motivo_status = (
            f"Aprovado pelo SEBR: {resultado.horas_deferidas}h deferidas. "
            f"{resultado.regra_aplicada}"
        )

        certificado.save(update_fields=[
            "status",
            "horas_computadas_final",
            "horas_descartadas",
            "justificativa_indeferimento",
            "motivo_status",
            "data_atualizacao",
        ])

        # RuleValidationLog — auditoria completa
        RuleValidationLog.objects.create(
            certificado        = certificado,
            usuario_responsavel = usuario_responsavel,
            regra_aplicada     = resultado.regra_aplicada,
            artigo_resolucao   = resultado.artigo,
            justificativa      = certificado.motivo_status,
            horas_enviadas     = int(horas_confirmadas),
            horas_computadas   = int(resultado.horas_deferidas),
            horas_descartadas  = int(horas_descartadas),
        )

    return {
        "horas_deferidas":        resultado.horas_deferidas,
        "horas_cortadas_evento":  resultado.horas_cortadas_evento,
        "horas_cortadas_total":   resultado.horas_cortadas_total,
        "saldo_apos":             resultado.saldo_apos,
        "regra_aplicada":         resultado.regra_aplicada,
        "atingiu_teto_evento":    resultado.atingiu_teto_evento,
        "atingiu_teto_total":     resultado.atingiu_teto_total,
    }


# ─────────────────────────────────────────────────────────────────────────────
#  Rejeição
# ─────────────────────────────────────────────────────────────────────────────

def rejeitar_certificado(
    certificado,
    justificativa: str,
    usuario_responsavel=None,
) -> None:
    """
    Fluxo de rejeição de um certificado (RN03).

    Regras:
        - A justificativa é OBRIGATÓRIA (RN03). Levanta ValueError se vazia.
        - Zera horas_computadas_final e horas_descartadas.
        - Persiste justificativa_indeferimento para rastreabilidade.
        - Cria RuleValidationLog.

    Args:
        certificado:         Instância de Certificado a rejeitar.
        justificativa:       Texto obrigatório explicando o motivo (RN03).
        usuario_responsavel: Instância de User do coordenador (para o log).

    Raises:
        ValueError: Se a justificativa for vazia ou só espaços.
    """
    from academico.models import RuleValidationLog

    justificativa = (justificativa or "").strip()
    if not justificativa:
        raise ValueError(
            "RN03 — A justificativa é obrigatória ao rejeitar um certificado."
        )

    horas_base = certificado.horas_sugeridas_ia or Decimal("0")

    with transaction.atomic():
        certificado.status                      = "rejeitado"
        certificado.horas_computadas_final      = Decimal("0")
        certificado.horas_descartadas           = horas_base
        certificado.justificativa_indeferimento = justificativa
        certificado.motivo_status               = f"Indeferido: {justificativa}"

        certificado.save(update_fields=[
            "status",
            "horas_computadas_final",
            "horas_descartadas",
            "justificativa_indeferimento",
            "motivo_status",
            "data_atualizacao",
        ])

        RuleValidationLog.objects.create(
            certificado         = certificado,
            usuario_responsavel = usuario_responsavel,
            regra_aplicada      = "RN03 — Indeferimento pelo Coordenador",
            artigo_resolucao    = "Resolucao CONSUNI 057/2025 — RN03",
            justificativa       = justificativa,
            horas_enviadas      = int(horas_base),
            horas_computadas    = 0,
            horas_descartadas   = int(horas_base),
        )

    logger.info(
        "[SEBR] Cert %s REJEITADO por %s. Motivo: %s",
        certificado.pk,
        getattr(usuario_responsavel, "username", "sistema"),
        justificativa[:80],
    )
