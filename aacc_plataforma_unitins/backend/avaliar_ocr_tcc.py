#!/usr/bin/env python
"""
Avaliação científica do pipeline OCR (TCC - Fase 3 / Capítulo 4).

Lê `relatorio_dataset_tcc.json` e calcula:
  - CER/WER do nome (normalizado: maiúsculas, sem acentos)
  - Acurácia booleana da carga horária
  - Taxa de Falso Aceite (FAR) e Gatilho Correto da trava RN04
Gera 2 gráficos em `resultados_tcc/` e imprime resumo em Markdown.

Dependências: pip install jiwer matplotlib
Uso: python avaliar_ocr_tcc.py [caminho_do_json]
"""
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

import jiwer
import matplotlib

matplotlib.use("Agg")  # backend sem janela (script standalone)
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parent
ARQUIVO_JSON = BASE_DIR / "relatorio_dataset_tcc.json"
PASTA_SAIDA = BASE_DIR / "resultados_tcc"

AZUL_UNITINS = "#003366"
OURO_UNITINS = "#F5A623"

LIMIAR_CONFIANCA = 70.0  # RN04
LIMIAR_CER_ERRO = 0.10  # 10%


def limpar_nome(texto):
    """
    Limpeza estrita: maiúsculas, sem acentos, sem pontuação (.,:;!?-),
    sem quebras de linha e sem espaços duplos.
    """
    if not texto:
        return ""
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFD", str(texto))
        if unicodedata.category(c) != "Mn"
    )
    sem_pontuacao = re.sub(r"[.,:;!?\-]", "", sem_acento.upper())
    return re.sub(r"\s+", " ", sem_pontuacao).strip()


normalizar = limpar_nome  # alias de compatibilidade


def calcular_cer_wer(gabarito, extraido):
    """Retorna (cer, wer). Extração vazia => erro total (1.0)."""
    ref, hip = normalizar(gabarito), normalizar(extraido)
    if not ref:
        return None, None
    if not hip:
        return 1.0, 1.0
    return jiwer.cer(ref, hip), jiwer.wer(ref, hip)


def horas_iguais(gabarito, extraido):
    if gabarito is None or extraido is None:
        return False
    try:
        return float(gabarito) == float(extraido)
    except (TypeError, ValueError):
        return False


def avaliar_registro(reg):
    meta = reg.get("metadados") or {}
    res = reg.get("resultado_pipeline") or {}

    cer, wer = calcular_cer_wer(meta.get("nome_exibido"), res.get("nome_extraido"))
    horas_ok = horas_iguais(meta.get("horas_gabarito"), res.get("horas_extraidas"))
    confianca = float(res.get("indice_confianca_ocr") or 0.0)
    titular = bool(res.get("titularidade_confirmada"))

    erro = (not horas_ok) or (cer is not None and cer > LIMIAR_CER_ERRO)
    bloqueado = confianca < LIMIAR_CONFIANCA or not titular

    return {
        "arquivo": reg.get("arquivo"),
        "nivel": meta.get("nivel"),
        "cer": cer,
        "wer": wer,
        "horas_ok": horas_ok,
        "confianca": confianca,
        "erro": erro,
        "far_literal": erro and confianca >= LIMIAR_CONFIANCA,
        "gatilho_correto": erro and bloqueado,
        # Falso aceite estrito: errou e NENHUM mecanismo da RN04 disparou
        "falso_aceite": erro and not bloqueado,
    }


def media(valores):
    valores = [v for v in valores if v is not None]
    return sum(valores) / len(valores) if valores else 0.0


def pct(parte, total):
    return 100.0 * parte / total if total else 0.0


def grafico_cer_por_nivel(por_nivel, destino):
    niveis = sorted(por_nivel)
    medias = [media([r["cer"] for r in por_nivel[n]]) * 100 for n in niveis]
    cores = [AZUL_UNITINS, OURO_UNITINS, AZUL_UNITINS][: len(niveis)] or [AZUL_UNITINS]

    fig, ax = plt.subplots(figsize=(7, 5))
    barras = ax.bar([f"Nível {n}" for n in niveis], medias,
                    color=[cores[i % len(cores)] for i in range(len(niveis))])
    for b, v in zip(barras, medias):
        ax.text(b.get_x() + b.get_width() / 2, v, f"{v:.2f}%",
                ha="center", va="bottom", fontweight="bold", color=AZUL_UNITINS)
    ax.set_ylabel("CER médio do nome (%)")
    ax.set_title("CER médio do Nome por Nível de Degradação",
                 color=AZUL_UNITINS, fontweight="bold")
    ax.set_ylim(0, max(medias + [1]) * 1.2)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(destino, dpi=300)
    plt.close(fig)


def grafico_eficacia_rn04(corretos, falsos, destino):
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.bar(["Nível 3"], [corretos], color=AZUL_UNITINS,
           label="Gatilho Correto (RN04 bloqueou)")
    ax.bar(["Nível 3"], [falsos], bottom=[corretos], color=OURO_UNITINS,
           label="Falso Aceite")
    if corretos:
        ax.text(0, corretos / 2, str(corretos), ha="center", va="center",
                color="white", fontweight="bold")
    if falsos:
        ax.text(0, corretos + falsos / 2, str(falsos), ha="center", va="center",
                color=AZUL_UNITINS, fontweight="bold")
    ax.set_ylabel("Documentos com erro de extração")
    ax.set_title("Eficácia da Trava RN04 - Nível 3",
                 color=AZUL_UNITINS, fontweight="bold")
    ax.legend(loc="upper right")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(destino, dpi=300)
    plt.close(fig)


def main():
    caminho = Path(sys.argv[1]) if len(sys.argv) > 1 else ARQUIVO_JSON
    with open(caminho, encoding="utf-8") as f:
        dados = json.load(f)

    registros = [avaliar_registro(r) for r in dados]
    total = len(registros)
    if not total:
        print("Dataset vazio.")
        return

    por_nivel = defaultdict(list)
    for r in registros:
        por_nivel[r["nivel"]].append(r)

    PASTA_SAIDA.mkdir(exist_ok=True)
    grafico_cer_por_nivel(por_nivel, PASTA_SAIDA / "grafico1_cer_por_nivel.png")

    n3 = por_nivel.get(3, [])
    erros_n3 = [r for r in n3 if r["erro"]]
    corretos_n3 = sum(r["gatilho_correto"] for r in erros_n3)
    falsos_n3 = sum(r["falso_aceite"] for r in erros_n3)
    grafico_eficacia_rn04(corretos_n3, falsos_n3,
                          PASTA_SAIDA / "grafico2_eficacia_rn04_nivel3.png")

    erros = [r for r in registros if r["erro"]]
    n_erros = len(erros)
    far_literal = sum(r["far_literal"] for r in erros)
    gatilhos = sum(r["gatilho_correto"] for r in erros)
    falsos = sum(r["falso_aceite"] for r in erros)

    print("# Resultados da Avaliação do Pipeline OCR\n")
    print(f"**Arquivo:** `{caminho.name}` | **Documentos:** {total}\n")

    print("## 1. Métricas por Nível\n")
    print("| Nível | N | CER médio (Nome) | WER médio (Nome) | Acurácia Carga Horária |")
    print("|:-----:|:-:|:----------------:|:----------------:|:----------------------:|")
    for n in sorted(por_nivel):
        g = por_nivel[n]
        acc = pct(sum(r["horas_ok"] for r in g), len(g))
        print(f"| {n} | {len(g)} | {media([r['cer'] for r in g]) * 100:.2f}% "
              f"| {media([r['wer'] for r in g]) * 100:.2f}% | {acc:.2f}% |")
    acc_g = pct(sum(r["horas_ok"] for r in registros), total)
    print(f"| **Geral** | {total} | {media([r['cer'] for r in registros]) * 100:.2f}% "
          f"| {media([r['wer'] for r in registros]) * 100:.2f}% | {acc_g:.2f}% |\n")

    print("## 2. Resiliência e Trava RN04\n")
    print(f"Erro de Extração = carga horária incorreta **OU** CER do nome > "
          f"{LIMIAR_CER_ERRO:.0%}. Limiar de confiança RN04: {LIMIAR_CONFIANCA:.0f}.\n")
    print("| Escopo | Erros | FAR (conf >= 70) | Gatilho Correto | Falso Aceite estrito |")
    print("|:-------|:-----:|:----------------:|:---------------:|:--------------------:|")
    escopos = [("Geral", registros)] + [(f"Nível {n}", por_nivel[n]) for n in sorted(por_nivel)]
    for nome, grupo in escopos:
        e = [r for r in grupo if r["erro"]]
        fl = sum(r["far_literal"] for r in e)
        gc = sum(r["gatilho_correto"] for r in e)
        fa = sum(r["falso_aceite"] for r in e)
        print(f"| {nome} | {len(e)} | {fl} ({pct(fl, len(e)):.2f}%) "
              f"| {gc} ({pct(gc, len(e)):.2f}%) | {fa} ({pct(fa, len(e)):.2f}%) |")

    print(f"\n- **Taxa de Falso Aceite (FAR, confianca_ocr >= 70):** "
          f"{far_literal}/{n_erros} = {pct(far_literal, n_erros):.2f}%")
    print(f"- **Gatilho Correto (confianca < 70 ou titularidade == False):** "
          f"{gatilhos}/{n_erros} = {pct(gatilhos, n_erros):.2f}%")
    print(f"- **Falso Aceite estrito (nenhum gatilho disparou):** "
          f"{falsos}/{n_erros} = {pct(falsos, n_erros):.2f}%")
    print(f"- **Nível 3:** {len(erros_n3)} erros -> {corretos_n3} gatilhos corretos, "
          f"{falsos_n3} falsos aceites\n")

    print("> Nota: o FAR literal considera apenas a confiança (>= 70). Um erro com "
          "confiança alta mas `titularidade_confirmada == False` ainda é bloqueado "
          "pela RN04, por isso é contado como Gatilho Correto e fora do Falso Aceite "
          "estrito (usado no Gráfico 2, que particiona os erros).\n")

    print("## 3. Gráficos\n")
    print(f"- `{PASTA_SAIDA.name}/grafico1_cer_por_nivel.png`")
    print(f"- `{PASTA_SAIDA.name}/grafico2_eficacia_rn04_nivel3.png`")


if __name__ == "__main__":
    main()
