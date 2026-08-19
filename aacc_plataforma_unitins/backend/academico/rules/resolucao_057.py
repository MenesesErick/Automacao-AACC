"""
academico/rules/resolucao_057.py

Sistema Especialista Baseado em Regras (SEBR)
Fonte da Verdade Matemática: Resolução CONSUNI N.º 057/2025 — Unitins
Atividades Acadêmico-Científico-Culturais (AACC)

═══════════════════════════════════════════════════════════════════════════════
REGRA DE OURO:
  O Rule Engine decide. O OCR apenas extrai. O Regex apenas higieniza.
  Todo cálculo deve ser reproduzível e auditável.

  NUNCA altere os limites abaixo sem embasamento normativo documentado.
  Qualquer mudança constitui uma versão de resolução (ex: 058/2026).
═══════════════════════════════════════════════════════════════════════════════

Estrutura de cada regra:
    codigo          str   — identificador slug imutável (chave primária lógica)
    nome            str   — nome oficial da atividade (Resolução, Art. X)
    eixo            str   — "Ensino" | "Pesquisa" | "Extensao"
    teto_total      int | None — máximo cumulativo aprovável na categoria (None = sem teto)
    teto_por_evento int | None — máximo por certificado individual (None = sem teto)
    artigo          str   — referência normativa para auditoria
"""

from __future__ import annotations
from decimal import Decimal
from typing import NamedTuple, Optional


# ─────────────────────────────────────────────────────────────────────────────
#  Estrutura de Dados Imutável
# ─────────────────────────────────────────────────────────────────────────────

class RegraCategoria(NamedTuple):
    """
    Definição imutável dos limites de uma categoria AACC.

    Attributes:
        codigo:         Slug único e imutável — chave do dicionário LIMITES_CATEGORIAS.
        nome:           Descrição oficial da atividade conforme a Resolução.
        eixo:           Eixo temático: "Ensino", "Pesquisa" ou "Extensao".
        teto_total:     Máximo de horas acumuláveis nesta categoria ao longo do curso.
                        None significa sem teto global (verificar apenas teto_por_evento).
        teto_por_evento: Máximo de horas computáveis por certificado/evento individual.
                        None significa sem limitação por evento.
        artigo:         Referência normativa para rastreabilidade em auditorias.
    """
    codigo:          str
    nome:            str
    eixo:            str
    teto_total:      Optional[int]
    teto_por_evento: Optional[int]
    artigo:          str


# ─────────────────────────────────────────────────────────────────────────────
#  Tabela de Limites — Resolução CONSUNI N.º 057/2025
# ─────────────────────────────────────────────────────────────────────────────
#  Chave: código slug imutável.
#  O nome no BD (CategoriaAACC.nome) pode mudar; o slug nunca deve mudar.
# ─────────────────────────────────────────────────────────────────────────────

LIMITES_CATEGORIAS: dict[str, RegraCategoria] = {

    # ─── EIXO: ENSINO ────────────────────────────────────────────────────────

    "disciplinas_outros_cursos": RegraCategoria(
        codigo          = "disciplinas_outros_cursos",
        nome            = "Disciplinas cursadas em outros cursos",
        eixo            = "Ensino",
        teto_total      = 90,
        teto_por_evento = None,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Ensino, Item 1",
    ),
    "monitoria": RegraCategoria(
        codigo          = "monitoria",
        nome            = "Monitoria",
        eixo            = "Ensino",
        teto_total      = 60,
        teto_por_evento = None,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Ensino, Item 2",
    ),
    "cursos_curta_duracao": RegraCategoria(
        codigo          = "cursos_curta_duracao",
        nome            = "Cursos de curta duracao",
        eixo            = "Ensino",
        teto_total      = 60,
        teto_por_evento = None,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Ensino, Item 3",
    ),
    "escola_linguas": RegraCategoria(
        codigo          = "escola_linguas",
        nome            = "Cursos da Escola de Linguas",
        eixo            = "Ensino",
        teto_total      = 60,
        teto_por_evento = None,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Ensino, Item 4",
    ),
    "pibid": RegraCategoria(
        codigo          = "pibid",
        nome            = "PIBID",
        eixo            = "Ensino",
        teto_total      = 120,
        teto_por_evento = None,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Ensino, Item 5",
    ),

    # ─── EIXO: PESQUISA ──────────────────────────────────────────────────────

    "projetos_pesquisa": RegraCategoria(
        codigo          = "projetos_pesquisa",
        nome            = "Projetos de pesquisa",
        eixo            = "Pesquisa",
        teto_total      = 100,
        teto_por_evento = None,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Pesquisa, Item 1",
    ),
    "grupos_pesquisa": RegraCategoria(
        codigo          = "grupos_pesquisa",
        nome            = "Grupos de pesquisa",
        eixo            = "Pesquisa",
        teto_total      = 100,
        teto_por_evento = None,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Pesquisa, Item 2",
    ),
    "trabalhos_cientificos": RegraCategoria(
        codigo          = "trabalhos_cientificos",
        nome            = "Trabalhos cientificos (apresentacao/publicacao em eventos)",
        eixo            = "Pesquisa",
        teto_total      = 90,
        teto_por_evento = 30,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Pesquisa, Item 3",
    ),
    "publicacoes": RegraCategoria(
        codigo          = "publicacoes",
        nome            = "Publicacao (livros, artigos, capitulos)",
        eixo            = "Pesquisa",
        teto_total      = 120,
        teto_por_evento = None,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Pesquisa, Item 4",
    ),

    # ─── EIXO: EXTENSAO E DIVERSOS ───────────────────────────────────────────

    "projetos_extensao": RegraCategoria(
        codigo          = "projetos_extensao",
        nome            = "Projetos de extensao institucionais",
        eixo            = "Extensao",
        teto_total      = 100,
        teto_por_evento = 20,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Extensao, Item 1",
    ),
    "seminarios_congressos": RegraCategoria(
        codigo          = "seminarios_congressos",
        nome            = "Seminarios, simposios, congressos, jornadas, foruns",
        eixo            = "Extensao",
        teto_total      = 120,
        teto_por_evento = None,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Extensao, Item 2",
    ),
    "cursos_extensao": RegraCategoria(
        codigo          = "cursos_extensao",
        nome            = "Cursos de extensao e nivelamento",
        eixo            = "Extensao",
        teto_total      = None,
        teto_por_evento = 60,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Extensao, Item 3",
    ),
    "organizacao_cursos_eventos": RegraCategoria(
        codigo          = "organizacao_cursos_eventos",
        nome            = "Organizacao de cursos e eventos",
        eixo            = "Extensao",
        teto_total      = 60,
        teto_por_evento = 10,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Extensao, Item 4",
    ),
    "organizacao_jornal_incubadora": RegraCategoria(
        codigo          = "organizacao_jornal_incubadora",
        nome            = "Organizacao de jornal/incubadora",
        eixo            = "Extensao",
        teto_total      = 60,
        teto_por_evento = 10,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Extensao, Item 5",
    ),
    "campanhas_voluntariado": RegraCategoria(
        codigo          = "campanhas_voluntariado",
        nome            = "Campanhas de voluntariado",
        eixo            = "Extensao",
        teto_total      = 60,
        teto_por_evento = 10,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Extensao, Item 6",
    ),
    "visitas_tecnicas": RegraCategoria(
        codigo          = "visitas_tecnicas",
        nome            = "Visitas tecnicas e viagens de estudo",
        eixo            = "Extensao",
        teto_total      = 60,
        teto_por_evento = 10,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Extensao, Item 7",
    ),
    "intercambio": RegraCategoria(
        codigo          = "intercambio",
        nome            = "Programas de intercambio",
        eixo            = "Extensao",
        teto_total      = None,
        teto_por_evento = 120,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Extensao, Item 8",
    ),
    "idiomas_informatica": RegraCategoria(
        codigo          = "idiomas_informatica",
        nome            = "Cursos de idiomas e informatica (externos a Escola de Linguas)",
        eixo            = "Extensao",
        teto_total      = 60,
        teto_por_evento = None,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Extensao, Item 9",
    ),
    "estagios_extracurriculares": RegraCategoria(
        codigo          = "estagios_extracurriculares",
        nome            = "Estagios extracurriculares",
        eixo            = "Extensao",
        teto_total      = 120,
        teto_por_evento = None,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Extensao, Item 10",
    ),
    "campanhas_unitins": RegraCategoria(
        codigo          = "campanhas_unitins",
        nome            = "Campanhas promovidas pela Unitins (trote solidario, doacao etc.)",
        eixo            = "Extensao",
        teto_total      = 30,
        teto_por_evento = 5,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Extensao, Item 11",
    ),
    "representacao_colegiado": RegraCategoria(
        codigo          = "representacao_colegiado",
        nome            = "Representacao discente (Colegiado/CONSUNI)",
        eixo            = "Extensao",
        teto_total      = 40,
        teto_por_evento = None,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Extensao, Item 12",
    ),
    "representacao_estudantil": RegraCategoria(
        codigo          = "representacao_estudantil",
        nome            = "Representacao estudantil (DCE/CA)",
        eixo            = "Extensao",
        teto_total      = 40,
        teto_por_evento = None,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Extensao, Item 13",
    ),
    "membro_cpa": RegraCategoria(
        codigo          = "membro_cpa",
        nome            = "Membro da CPA",
        eixo            = "Extensao",
        teto_total      = 60,
        teto_por_evento = None,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Extensao, Item 14",
    ),
    "exames_proficiencia": RegraCategoria(
        codigo          = "exames_proficiencia",
        nome            = "Exames de proficiencia",
        eixo            = "Extensao",
        teto_total      = 60,
        teto_por_evento = None,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Extensao, Item 15",
    ),
    "doacao_sangue_medula": RegraCategoria(
        codigo          = "doacao_sangue_medula",
        nome            = "Doacao de sangue ou medula ossea",
        eixo            = "Extensao",
        teto_total      = 40,
        teto_por_evento = 10,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Extensao, Item 16",
    ),
    "premios_condecoracoes": RegraCategoria(
        codigo          = "premios_condecoracoes",
        nome            = "Premios e condecoracoes",
        eixo            = "Extensao",
        teto_total      = 10,
        teto_por_evento = None,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Extensao, Item 17",
    ),
    "mesario_voluntario": RegraCategoria(
        codigo          = "mesario_voluntario",
        nome            = "Mesario voluntario",
        eixo            = "Extensao",
        teto_total      = 60,
        teto_por_evento = None,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Extensao, Item 18",
    ),
    "projetos_voluntarios": RegraCategoria(
        codigo          = "projetos_voluntarios",
        nome            = "Acoes de projetos voluntarios",
        eixo            = "Extensao",
        teto_total      = 30,
        teto_por_evento = None,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Extensao, Item 19",
    ),
    "sustentabilidade": RegraCategoria(
        codigo          = "sustentabilidade",
        nome            = "Acoes de sustentabilidade",
        eixo            = "Extensao",
        teto_total      = 30,
        teto_por_evento = None,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Extensao, Item 20",
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
#  Motor de Cálculo — CalculadoraLimites
# ─────────────────────────────────────────────────────────────────────────────

class ResultadoCalculo(NamedTuple):
    """
    Resultado completo do cálculo de limite AACC para auditoria.

    Attributes:
        horas_deferidas:       Horas efectivamente aprovadas após aplicação das regras.
        horas_cortadas_evento: Horas removidas pelo teto_por_evento (0 se N/A).
        horas_cortadas_total:  Horas removidas por atingir o teto_total da categoria.
        atingiu_teto_evento:   True se o teto_por_evento foi activado.
        atingiu_teto_total:    True se o teto_total foi activado.
        saldo_apos:            Novo saldo da categoria após o deferimento.
        regra_aplicada:        Descrição textual da(s) regra(s) usada(s) — para o Log.
        artigo:                Referência normativa da categoria.
    """
    horas_deferidas:       Decimal
    horas_cortadas_evento: Decimal
    horas_cortadas_total:  Decimal
    atingiu_teto_evento:   bool
    atingiu_teto_total:    bool
    saldo_apos:            Decimal
    regra_aplicada:        str
    artigo:                str


class CalculadoraLimites:
    """
    Motor de Cálculo do SEBR — aplica os limites da Resolução CONSUNI 057/2025.

    Stateless: não persiste nada no banco.
    Toda a lógica é determinística e reproduzível.

    Uso típico (no momento da aprovação pelo coordenador):

        calculadora = CalculadoraLimites()
        resultado = calculadora.aplicar_limites(
            codigo_categoria = "trabalhos_cientificos",
            horas_submetidas = Decimal("40"),
            saldo_atual      = Decimal("60"),
        )
        # resultado.horas_deferidas == 30  (teto_por_evento cortou para 30;
        #                                   30 + 60 = 90 == teto_total)
    """

    def aplicar_limites(
        self,
        codigo_categoria: str,
        horas_submetidas: Decimal,
        saldo_atual:      Decimal = Decimal("0"),
    ) -> ResultadoCalculo:
        """
        Aplica os limites normativos da categoria e retorna o resultado auditável.

        Pipeline de cálculo (dois estágios):
            1. Corte por evento: se horas_submetidas > teto_por_evento, reduz ao teto.
            2. Corte por total:  se saldo_atual + valor_cortado > teto_total, aprova
               apenas a diferença para completar o teto (pode resultar em 0h).

        Args:
            codigo_categoria:  Slug da categoria (chave de LIMITES_CATEGORIAS).
            horas_submetidas:  Horas indicadas pelo OCR/coordenador para este certificado.
            saldo_atual:       Total de horas já aprovadas nesta categoria para o aluno.

        Returns:
            ResultadoCalculo com todos os campos preenchidos para auditoria.

        Raises:
            ValueError: Se o codigo_categoria não for reconhecido pelo SEBR.
        """
        if codigo_categoria not in LIMITES_CATEGORIAS:
            raise ValueError(
                f"Categoria desconhecida pelo SEBR: '{codigo_categoria}'. "
                f"Codigos validos: {sorted(LIMITES_CATEGORIAS.keys())}"
            )

        regra = LIMITES_CATEGORIAS[codigo_categoria]

        horas_submetidas = Decimal(str(horas_submetidas))
        saldo_atual      = Decimal(str(saldo_atual))

        horas_cortadas_evento = Decimal("0")
        horas_cortadas_total  = Decimal("0")
        atingiu_teto_evento   = False
        atingiu_teto_total    = False
        partes_regra: list[str] = []

        # ── Estágio 1: Teto por evento ────────────────────────────────────────
        valor_apos_evento = horas_submetidas
        if regra.teto_por_evento is not None:
            teto_ev = Decimal(str(regra.teto_por_evento))
            if horas_submetidas > teto_ev:
                horas_cortadas_evento = horas_submetidas - teto_ev
                valor_apos_evento     = teto_ev
                atingiu_teto_evento   = True
                partes_regra.append(
                    f"Teto por evento: {horas_submetidas}h -> {teto_ev}h "
                    f"(cortadas {horas_cortadas_evento}h). {regra.artigo}."
                )

        # ── Estágio 2: Teto total da categoria ────────────────────────────────
        valor_final = valor_apos_evento
        if regra.teto_total is not None:
            teto_tot = Decimal(str(regra.teto_total))
            espaco_restante = teto_tot - saldo_atual

            if espaco_restante <= 0:
                # Aluno já atingiu o teto — nenhuma hora é aprovada
                horas_cortadas_total = valor_apos_evento
                valor_final          = Decimal("0")
                atingiu_teto_total   = True
                partes_regra.append(
                    f"Teto total da categoria ja atingido: "
                    f"saldo={saldo_atual}h / teto={teto_tot}h -> 0h deferidas. "
                    f"{regra.artigo}."
                )
            elif valor_apos_evento > espaco_restante:
                horas_cortadas_total = valor_apos_evento - espaco_restante
                valor_final          = espaco_restante
                atingiu_teto_total   = True
                partes_regra.append(
                    f"Teto total atingido: {valor_apos_evento}h -> {espaco_restante}h "
                    f"(saldo anterior: {saldo_atual}h / teto: {teto_tot}h). "
                    f"{regra.artigo}."
                )

        if not partes_regra:
            partes_regra.append(
                f"Aprovado integralmente: {valor_final}h "
                f"(sem cortes — {regra.artigo})."
            )

        return ResultadoCalculo(
            horas_deferidas       = valor_final,
            horas_cortadas_evento = horas_cortadas_evento,
            horas_cortadas_total  = horas_cortadas_total,
            atingiu_teto_evento   = atingiu_teto_evento,
            atingiu_teto_total    = atingiu_teto_total,
            saldo_apos            = saldo_atual + valor_final,
            regra_aplicada        = " | ".join(partes_regra),
            artigo                = regra.artigo,
        )

    def get_regra(self, codigo_categoria: str) -> RegraCategoria:
        """Retorna a definição normativa de uma categoria para consulta."""
        if codigo_categoria not in LIMITES_CATEGORIAS:
            raise ValueError(f"Categoria desconhecida: '{codigo_categoria}'")
        return LIMITES_CATEGORIAS[codigo_categoria]

    def listar_por_eixo(self, eixo: str) -> list[RegraCategoria]:
        """Retorna todas as regras de um eixo ('Ensino', 'Pesquisa' ou 'Extensao')."""
        return [r for r in LIMITES_CATEGORIAS.values() if r.eixo == eixo]


# ─────────────────────────────────────────────────────────────────────────────
#  Singleton de acesso rápido — importável em qualquer módulo do projecto
# ─────────────────────────────────────────────────────────────────────────────

calculadora = CalculadoraLimites()
