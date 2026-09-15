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

Gerado automaticamente via scripts/atualizar_regras_pdf.py
Fonte dos tooltips: Tabela_AACC.pdf — RESOLUÇÃO/CONSUNI/N.057, de 15 out 2025.

Estrutura de cada regra:
    codigo          str   — identificador slug imutável (chave primária lógica)
    nome            str   — nome oficial da atividade (Resolução, Art. X)
    eixo            str   — "Ensino" | "Pesquisa" | "Extensao"
    teto_total      int | None — máximo cumulativo aprovável na categoria (None = sem teto)
    teto_por_evento int | None — máximo por certificado individual (None = sem teto)
    artigo          str   — referência normativa para auditoria
    tooltip         str   — descrição oficial para exibição na interface (UX)
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
        tooltip:        Texto oficial da Resolução para exibição na interface (UX).
    """
    codigo:          str
    nome:            str
    eixo:            str
    teto_total:      Optional[int]
    teto_por_evento: Optional[int]
    artigo:          str
    tooltip:         str = ''


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
        tooltip         = (
            "Disciplinas pertencentes a outros cursos superiores de graduação, sequenciais, na modalidade a distância ou presenciais, cursadas no mesmo período do curso vigente, nessa ou em outras Instituições de Ensino Superior, correlatas à formação do profissional a ele concernente, nas quais o aluno tenha obtido aprovação e que não tenham sido aproveitadas na estrutura curricular do curso vigente (como por exemplo, disciplinas optativas ou eletivas)."
        ),
    ),
    "monitoria": RegraCategoria(
        codigo          = "monitoria",
        nome            = "Monitoria Institucional",
        eixo            = "Ensino",
        teto_total      = 60,
        teto_por_evento = None,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Ensino, Item 2",
        tooltip         = (
            "Participação em Programa Institucional de Monitoria correlacionado à área de formação do curso (monitoria acadêmica, monitoria de oficinas pedagógicas, monitoria de cursos etc.)."
        ),
    ),
    "cursos_curta_duracao": RegraCategoria(
        codigo          = "cursos_curta_duracao",
        nome            = "Cursos de curta duração",
        eixo            = "Ensino",
        teto_total      = 60,
        teto_por_evento = None,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Ensino, Item 3",
        tooltip         = (
            "Participação em cursos de curta duração."
        ),
    ),
    "escola_linguas": RegraCategoria(
        codigo          = "escola_linguas",
        nome            = "Cursos da Escola de Línguas",
        eixo            = "Ensino",
        teto_total      = 60,
        teto_por_evento = None,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Ensino, Item 4",
        tooltip         = (
            "Participação em cursos da Escola de Línguas da Unitins ou de outras Instituições."
        ),
    ),
    "pibid": RegraCategoria(
        codigo          = "pibid",
        nome            = "PIBID",
        eixo            = "Ensino",
        teto_total      = 120,
        teto_por_evento = None,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Ensino, Item 5",
        tooltip         = (
            "Participação em programa de iniciação à docência (PIBID) institucionalizado na Unitins ou de outra IES."
        ),
    ),

    # ─── EIXO: PESQUISA ──────────────────────────────────────────────────────

    "projetos_pesquisa": RegraCategoria(
        codigo          = "projetos_pesquisa",
        nome            = "Projetos de pesquisa",
        eixo            = "Pesquisa",
        teto_total      = 100,
        teto_por_evento = None,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Pesquisa, Item 1",
        tooltip         = (
            "Participação em projetos de pesquisa nas áreas pertinentes aos cursos de graduação, com orientação docente, apresentados em eventos científicos específicos ou seminários, e publicados em anais, mencionando o nome da Unitins."
        ),
    ),
    "grupos_pesquisa": RegraCategoria(
        codigo          = "grupos_pesquisa",
        nome            = "Grupos de pesquisa",
        eixo            = "Pesquisa",
        teto_total      = 100,
        teto_por_evento = None,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Pesquisa, Item 2",
        tooltip         = (
            "Participação em grupos de pesquisa, grupos de trabalhos ou grupo de estudos nas áreas pertinentes aos cursos de graduação, conduzidas por instituições Públicas ou Privadas."
        ),
    ),
    "trabalhos_cientificos": RegraCategoria(
        codigo          = "trabalhos_cientificos",
        nome            = "Trabalhos científicos (apresentação/publicação em eventos)",
        eixo            = "Pesquisa",
        teto_total      = 90,
        teto_por_evento = 30,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Pesquisa, Item 3",
        tooltip         = (
            "Trabalhos científicos desenvolvidos, nas áreas pertinentes aos cursos de graduação, com orientação docente, apresentados na Unitins ou em outra IES, em eventos científicos específicos ou seminários multidisciplinares e publicados em anais. Teto de 30h por apresentação e 90h no total do curso."
        ),
    ),
    "publicacoes": RegraCategoria(
        codigo          = "publicacoes",
        nome            = "Publicação (livros, artigos, capítulos)",
        eixo            = "Pesquisa",
        teto_total      = 120,
        teto_por_evento = None,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Pesquisa, Item 4",
        tooltip         = (
            "Publicação de livros, capítulo de livros, resumo em anais, artigo completo em anais (como autor ou coautor), artigo publicado como autor ou coautor em periódicos com conselho editorial."
        ),
    ),

    # ─── EIXO: EXTENSÃO ──────────────────────────────────────────────────────

    "projetos_extensao": RegraCategoria(
        codigo          = "projetos_extensao",
        nome            = "Projetos de extensão institucionais",
        eixo            = "Extensao",
        teto_total      = 100,
        teto_por_evento = 20,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Extensao, Item 1",
        tooltip         = (
            "Participação nos projetos de extensão institucionalizados na Unitins: até 20 horas por projeto, limitado a, no máximo, 100 horas em todo o curso de graduação."
        ),
    ),
    "seminarios_congressos": RegraCategoria(
        codigo          = "seminarios_congressos",
        nome            = "Seminários, simpósios, congressos, jornadas, fóruns",
        eixo            = "Extensao",
        teto_total      = 120,
        teto_por_evento = None,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Extensao, Item 2",
        tooltip         = (
            "Participação em seminários, palestras, congressos, conferências, jornadas, simpósios e semanas acadêmicas, na área do curso: até 120 horas em todo o curso de graduação."
        ),
    ),
    "cursos_extensao": RegraCategoria(
        codigo          = "cursos_extensao",
        nome            = "Cursos de extensão e nivelamento",
        eixo            = "Extensao",
        teto_total      = None,
        teto_por_evento = 60,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Extensao, Item 3",
        tooltip         = (
            "Participação com aprovação em cursos de extensão, atualização e nivelamento, na área do curso ou afins: até 60 horas por curso."
        ),
    ),
    "organizacao_cursos_eventos": RegraCategoria(
        codigo          = "organizacao_cursos_eventos",
        nome            = "Organização de cursos e eventos",
        eixo            = "Extensao",
        teto_total      = 60,
        teto_por_evento = 10,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Extensao, Item 4",
        tooltip         = (
            "Participação na organização, coordenação ou realização de cursos e/ou eventos científicos internos ou externos à Unitins, na área do curso ou afins: até 10 horas por evento, limitado a, no máximo, 60 horas em todo o curso de graduação."
        ),
    ),
    "organizacao_jornal_incubadora": RegraCategoria(
        codigo          = "organizacao_jornal_incubadora",
        nome            = "Organização de jornal/incubadora",
        eixo            = "Extensao",
        teto_total      = 60,
        teto_por_evento = 10,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Extensao, Item 5",
        tooltip         = (
            "Participação na organização de jornal informativo da Unitins, home page do curso, incubadora, agência ou escritório experimental/modelo dentre outros: até 10 horas por evento, limitado a, no máximo, 60 horas em todo o curso de graduação."
        ),
    ),
    "campanhas_voluntariado": RegraCategoria(
        codigo          = "campanhas_voluntariado",
        nome            = "Campanhas de voluntariado",
        eixo            = "Extensao",
        teto_total      = 60,
        teto_por_evento = 10,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Extensao, Item 6",
        tooltip         = (
            "Trabalho na organização ou participação em campanhas de voluntariado ou programas de ação social: até 10 horas por evento, limitado a, no máximo, 60 horas em todo o curso de graduação."
        ),
    ),
    "visitas_tecnicas": RegraCategoria(
        codigo          = "visitas_tecnicas",
        nome            = "Visitas técnicas e viagens de estudo",
        eixo            = "Extensao",
        teto_total      = 60,
        teto_por_evento = 10,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Extensao, Item 7",
        tooltip         = (
            "Participação em visitas técnicas programadas ou em viagens científicas e de estudo: até 10 horas por evento, limitado a, no máximo, 60 horas em todo o curso de graduação."
        ),
    ),
    "intercambio": RegraCategoria(
        codigo          = "intercambio",
        nome            = "Programas de intercâmbio",
        eixo            = "Extensao",
        teto_total      = None,
        teto_por_evento = 120,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Extensao, Item 8",
        tooltip         = (
            "Participação em programas de intercâmbio institucional, nacional e/ou internacional: até 120 horas por programa."
        ),
    ),
    "idiomas_informatica": RegraCategoria(
        codigo          = "idiomas_informatica",
        nome            = "Cursos de idiomas e informática (externos à Escola de Línguas)",
        eixo            = "Extensao",
        teto_total      = 60,
        teto_por_evento = None,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Extensao, Item 9",
        tooltip         = (
            "Participação, com aprovação, em cursos de idiomas, comunicação e expressão e de informática, realizados durante o curso de graduação, dentro ou fora da Unitins, cujas cargas horárias não tenham sido objeto de aproveitamento de disciplina: limitado a, no máximo, 60 horas em todo o curso de graduação."
        ),
    ),
    "estagios_extracurriculares": RegraCategoria(
        codigo          = "estagios_extracurriculares",
        nome            = "Estágios extracurriculares",
        eixo            = "Extensao",
        teto_total      = 120,
        teto_por_evento = None,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Extensao, Item 10",
        tooltip         = (
            "Estágios extracurriculares em instituições públicas ou privadas ou em órgãos públicos, desempenhando atividades relacionadas com as áreas dos cursos de graduação, desde que orientadas e atendidas às exigências legais e validada pela Coordenação do Curso: até 120 horas em todo o curso de graduação."
        ),
    ),
    "campanhas_unitins": RegraCategoria(
        codigo          = "campanhas_unitins",
        nome            = "Campanhas promovidas pela Unitins (trote solidário, doação etc.)",
        eixo            = "Extensao",
        teto_total      = 30,
        teto_por_evento = 5,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Extensao, Item 11",
        tooltip         = (
            "Participação ou trabalho na organização em campanhas da Unitins (trote solidário, doação de sangue ou outros eventos): 05 horas por evento, limitado a, no máximo, 30 horas em todo o curso de graduação."
        ),
    ),
    "representacao_colegiado": RegraCategoria(
        codigo          = "representacao_colegiado",
        nome            = "Representação discente (Colegiado/CONSUNI)",
        eixo            = "Extensao",
        teto_total      = 40,
        teto_por_evento = None,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Extensao, Item 12",
        tooltip         = (
            "Participação como representante discente no Colegiado do Curso, Conselho de Ensino, Pesquisa e Extensão – CONSEPE, Conselho Universitário – CONSUNI, comitês, câmaras ou outro que seja institucionalizado, sendo limitado a, no máximo, 40 horas em todo o curso de graduação."
        ),
    ),
    "representacao_estudantil": RegraCategoria(
        codigo          = "representacao_estudantil",
        nome            = "Representação estudantil (DCE/CA)",
        eixo            = "Extensao",
        teto_total      = 40,
        teto_por_evento = None,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Extensao, Item 13",
        tooltip         = (
            "Participação como representante discente em organizações estudantis nacionais, como por exemplo: ligas acadêmicas, Empresa Júnior - EJ, União Nacional dos Estudantes – UNE, União Estadual dos Estudantes – UEE, Diretório Central dos Estudantes - DCE e Centro Acadêmico, sendo limitado a, no máximo, 40 horas em todo o curso de graduação."
        ),
    ),
    "membro_cpa": RegraCategoria(
        codigo          = "membro_cpa",
        nome            = "Membro da CPA",
        eixo            = "Extensao",
        teto_total      = 60,
        teto_por_evento = None,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Extensao, Item 14",
        tooltip         = (
            "Participação como membro da Comissão Própria de Avaliação – CPA, sendo limitado a, no máximo, 60 horas em todo o curso de graduação."
        ),
    ),
    "exames_proficiencia": RegraCategoria(
        codigo          = "exames_proficiencia",
        nome            = "Exames de proficiência",
        eixo            = "Extensao",
        teto_total      = 60,
        teto_por_evento = None,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Extensao, Item 15",
        tooltip         = (
            "Participação, com aprovação, em exames de proficiência em língua estrangeira, sendo limitado a, no máximo, 60 horas em todo o curso de graduação."
        ),
    ),
    "doacao_sangue_medula": RegraCategoria(
        codigo          = "doacao_sangue_medula",
        nome            = "Doação de sangue ou medula óssea",
        eixo            = "Extensao",
        teto_total      = 40,
        teto_por_evento = 10,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Extensao, Item 16",
        tooltip         = (
            "Doação de sangue ou de medula óssea, limitado a 10 horas por doação e, no máximo, 40 horas em todo o curso de graduação."
        ),
    ),
    "premios_condecoracoes": RegraCategoria(
        codigo          = "premios_condecoracoes",
        nome            = "Prêmios e condecorações",
        eixo            = "Extensao",
        teto_total      = 10,
        teto_por_evento = None,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Extensao, Item 17",
        tooltip         = (
            "Prêmios, condecorações ou homenagens recebidas em razão de atividades ligadas à área de conhecimento do curso, limitado a, no máximo, 10 horas em todo o curso de graduação."
        ),
    ),
    "mesario_voluntario": RegraCategoria(
        codigo          = "mesario_voluntario",
        nome            = "Mesário voluntário",
        eixo            = "Extensao",
        teto_total      = 60,
        teto_por_evento = None,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Extensao, Item 18",
        tooltip         = (
            "Participação como mesário voluntário nas eleições, limitado a, no máximo, 60 horas em todo o curso de graduação."
        ),
    ),
    "projetos_voluntarios": RegraCategoria(
        codigo          = "projetos_voluntarios",
        nome            = "Ações de projetos voluntários",
        eixo            = "Extensao",
        teto_total      = 30,
        teto_por_evento = None,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Extensao, Item 19",
        tooltip         = (
            "Participação como voluntário em ações de projetos, que sejam institucionalizadas, limitado a, no máximo, 30 horas em todo o curso de graduação."
        ),
    ),
    "sustentabilidade": RegraCategoria(
        codigo          = "sustentabilidade",
        nome            = "Ações de sustentabilidade",
        eixo            = "Extensao",
        teto_total      = 30,
        teto_por_evento = None,
        artigo          = "Resolucao CONSUNI 057/2025, Eixo Extensao, Item 20",
        tooltip         = (
            "Participação em ações de sustentabilidade, institucionalizadas, limitado a, no máximo, 30 horas em todo o curso de graduação."
        ),
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
