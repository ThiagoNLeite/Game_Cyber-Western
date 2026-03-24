from abc import ABC, abstractmethod
from mecanicas.dados import SistemaDados


class Entidade(ABC):
    """
    Classe base abstrata para todas as entidades do jogo.
    Jogador, Monstro e Boss herdam desta classe.
    """

    def __init__(self, nome: str, poder: int, defesa: int, vida: int, esquiva: int):
        self.nome = nome
        self.poder = poder
        self.defesa = defesa
        self.vida_maxima = vida
        self.vida_atual = vida
        self.esquiva = esquiva
        self.nivel = 1

    # ------------------------------------------------------------------ #
    #  Propriedades
    # ------------------------------------------------------------------ #

    @property
    def esta_vivo(self) -> bool:
        return self.vida_atual > 0

    @property
    def percentual_vida(self) -> float:
        return self.vida_atual / self.vida_maxima

    # ------------------------------------------------------------------ #
    #  Métodos concretos compartilhados
    # ------------------------------------------------------------------ #

    def atacar(self, alvo: "Entidade") -> dict:
        """
        Realiza um ataque contra o alvo usando o sistema D20.
        Regra: d20 + Poder >= Defesa do alvo + 10 para acertar.
        Retorna um dict com os resultados para a interface exibir.
        """
        d20 = SistemaDados.rolar_d20()
        critico = d20 == 20
        acertou = critico or (d20 + self.poder >= alvo.defesa + 10)

        resultado = {
            "atacante": self.nome,
            "alvo": alvo.nome,
            "d20": d20,
            "acertou": acertou,
            "critico": critico,
            "dano": 0,
        }

        if acertou:
            d6 = SistemaDados.rolar_d6()
            dano = max(1, self.poder + d6 - alvo.defesa)
            if critico:
                dano = dano * 2
            alvo.receber_dano(dano)
            resultado["dano"] = dano

        return resultado

    def receber_dano(self, dano: int) -> None:
        self.vida_atual = max(0, self.vida_atual - dano)

    def curar(self, quantidade: int) -> None:
        self.vida_atual = min(self.vida_maxima, self.vida_atual + quantidade)

    def status(self) -> str:
        return (
            f"{self.nome} | HP: {self.vida_atual}/{self.vida_maxima} "
            f"| P:{self.poder} D:{self.defesa} E:{self.esquiva}"
        )

    # ------------------------------------------------------------------ #
    #  Método abstrato — cada subclasse define sua apresentação
    # ------------------------------------------------------------------ #

    @abstractmethod
    def descricao(self) -> str:
        """Retorna uma descrição narrativa da entidade."""
        ...