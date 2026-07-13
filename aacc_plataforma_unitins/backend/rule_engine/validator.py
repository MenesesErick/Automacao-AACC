"""
Módulo: validator.py
Responsabilidade: Auditoria de segurança (RN04) e orquestração do fluxo de
                  avaliação de certificados de AACC.

Este módulo é Python puro e não possui nenhuma dependência do Django ou
da camada de base de dados. Toda a comunicação é feita via valores primitivos,
garantindo total isolamento e testabilidade.
"""

from rule_engine.consuni_057 import CalculadoraAACC

# Limiar mínimo de confiança exigido para aprovação automática (RN04)
LIMIAR_CONFIANCA_MINIMA: float = 70.0


class ValidadorCertificado:
    """
    Orquestrador de validação de certificados submetidos pelos alunos.

    Responsabilidades:
        - Simular a leitura OCR (mock até integração real com o ocr_engine).
        - Auditar o índice de confiança retornado pelo OCR (RN04).
        - Invocar a CalculadoraAACC para aplicar os tetos da Resolução 057.
        - Devolver um dicionário de resultado padronizado para a camada de serviço.
    """

    def avaliar_confianca_ocr(self, indice_confianca: float) -> str:
        """
        Auditoria de segurança RN04: avalia se o índice de confiança do OCR
        é suficiente para aprovação automática.

        Args:
            indice_confianca (float): Percentual de confiança retornado pelo OCR
                                     (0.0 a 100.0).

        Returns:
            str: ``'revisao_manual'`` se o índice for inferior ao limiar mínimo
                 (< 70.0), ou ``'aprovado'`` caso contrário.

        Examples:
            >>> v = ValidadorCertificado()
            >>> v.avaliar_confianca_ocr(65.5)
            'revisao_manual'
            >>> v.avaliar_confianca_ocr(85.0)
            'aprovado'
        """
        if indice_confianca < LIMIAR_CONFIANCA_MINIMA:
            return "revisao_manual"
        return "aprovado"

    def simular_leitura_ocr(
        self, horas_informadas: float
    ) -> tuple[float, float, str]:
        """
        Mock do motor OCR — substitui temporariamente a integração real com o
        módulo ``ocr_engine``.

        Simula que a IA leu o documento com perfeição: devolve as horas
        exatamente como foram informadas pelo aluno, um índice de confiança
        de 100.0% e um texto simulado.

        Args:
            horas_informadas (float): Horas declaradas pelo aluno no certificado.

        Returns:
            tuple[float, float, str]: Tuplo ``(horas_lidas, indice_confianca, texto_extraido)``.
        """
        horas_lidas: float = horas_informadas
        indice_confianca: float = 100.0
        texto_extraido: str = f"[SIMULAÇÃO OCR] Certificado validado automaticamente. Carga horária identificada: {horas_lidas}h."
        return horas_lidas, indice_confianca, texto_extraido

    def processar_certificado(
        self,
        horas_informadas: float,
        limite_cat: float,
        saldo_cat: float,
    ) -> dict:
        """
        Método orquestrador do fluxo completo de avaliação de um certificado.

        Fluxo:
            1. Chama ``simular_leitura_ocr`` para obter as horas lidas e o
               índice de confiança.
            2. Avalia o índice via ``avaliar_confianca_ocr``.
            3. Se o status for ``'revisao_manual'``, retorna imediatamente com
               horas zeradas para aguardar intervenção humana.
            4. Se aprovado, delega o cálculo final à ``CalculadoraAACC`` e
               retorna o resultado com as horas efetivamente computadas.

        Args:
            horas_informadas (float): Horas declaradas pelo aluno no certificado.
            limite_cat (float): Teto máximo de horas aproveitáveis na categoria
                                (conforme Resolução 057).
            saldo_cat (float): Horas já acumuladas pelo aluno nesta categoria.

        Returns:
            dict: Dicionário de resultado com as seguintes chaves:
                - ``status_sugerido`` (str)
                - ``horas_finais`` (float)
                - ``horas_descartadas`` (float)
                - ``confianca_ocr`` (float)
                - ``texto_extraido`` (str)
                - ``motivo`` (str)
        """
        # Passo 1: leitura (simulada) do documento
        horas_lidas, confianca, texto_extraido = self.simular_leitura_ocr(horas_informadas)

        # Passo 2: auditoria de confiança (RN04)
        status: str = self.avaliar_confianca_ocr(confianca)

        # Passo 3: fluxo de revisão manual — confiança insuficiente
        if status == "revisao_manual":
            return {
                "status_sugerido": "revisao_manual",
                "horas_finais": 0.0,
                "horas_descartadas": 0.0,
                "confianca_ocr": confianca,
                "texto_extraido": texto_extraido,
                "motivo": "Índice de confiança do OCR abaixo do limiar mínimo. Necessária revisão manual.",
            }

        # Passo 4: aprovado — aplica as regras de cômputo da Resolução 057
        horas_finais: float = CalculadoraAACC.calcular_horas_aprovadas(
            horas_submetidas=horas_lidas,
            limite_categoria=limite_cat,
            saldo_atual=saldo_cat,
        )
        
        horas_descartadas = horas_lidas - horas_finais
        
        motivo = "Aprovado integralmente."
        if horas_descartadas > 0:
            if horas_finais == 0:
                motivo = "Teto máximo da categoria já atingido. Nenhuma hora foi aproveitada."
            else:
                motivo = f"Aprovado parcialmente. Teto da categoria atingido, descartando {horas_descartadas}h."

        return {
            "status_sugerido": "aprovado",
            "horas_finais": horas_finais,
            "horas_descartadas": horas_descartadas,
            "confianca_ocr": confianca,
            "texto_extraido": texto_extraido,
            "motivo": motivo,
        }