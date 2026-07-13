"""
Módulo: consuni_057.py
Referência: Resolução Consuni 057 - Regras de cômputo de horas para AACC.

Este módulo é Python puro e não possui nenhuma dependência do Django ou
da camada de base de dados. Recebe valores primitivos e devolve resultados
calculados, garantindo total isolamento e testabilidade.
"""


class CalculadoraAACC:
    """
    Calculadora de horas aproveitáveis para Atividades Acadêmico-Culturais
    e Complementares (AACC), baseada nos tetos definidos pela Resolução 057.

    Todas as regras de cômputo são implementadas como métodos estáticos para
    que possam ser invocadas sem necessidade de instanciar a classe.
    """

    @staticmethod
    def calcular_horas_aprovadas(
        horas_submetidas: float,
        limite_categoria: float,
        saldo_atual: float,
    ) -> float:
        """
        Calcula o número de horas que serão efetivamente aproveitadas para
        uma categoria, respeitando o teto máximo definido pela Resolução 057.

        Regras (em ordem de prioridade):
            1. Calcula o espaço restante até o teto: ``limite_categoria - saldo_atual``.
            2. Se o espaço restante for <= 0, o teto já foi atingido; devolve 0.0.
            3. Se as horas submetidas excederem o espaço restante, devolve
               apenas o espaço restante (corte do excedente).
            4. Caso contrário, devolve as horas submetidas na íntegra.

        Args:
            horas_submetidas (float): Horas declaradas/lidas pelo OCR no certificado.
            limite_categoria (float): Teto máximo de horas aproveitáveis na categoria.
            saldo_atual (float): Horas já computadas para o aluno nesta categoria.

        Returns:
            float: Total de horas aprovadas para este certificado.

        Examples:
            >>> CalculadoraAACC.calcular_horas_aprovadas(30.0, 60.0, 20.0)
            30.0  # cabe dentro do teto (60 - 20 = 40 de espaço)

            >>> CalculadoraAACC.calcular_horas_aprovadas(50.0, 60.0, 20.0)
            40.0  # excede; retorna apenas o espaço restante

            >>> CalculadoraAACC.calcular_horas_aprovadas(10.0, 60.0, 60.0)
            0.0   # teto já atingido
        """
        espaco_restante: float = limite_categoria - saldo_atual

        # Regra 2: teto já atingido ou ultrapassado
        if espaco_restante <= 0:
            return 0.0

        # Regra 3: horas excedem o espaço disponível — corte do excedente
        if horas_submetidas > espaco_restante:
            return espaco_restante

        # Regra 4: horas cabem integralmente
        return horas_submetidas