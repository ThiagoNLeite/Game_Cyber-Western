from abc import ABC, abstractmethod
from mecanicas.dados import SistemaDados


class Vocacao(ABC):
    """
    Classe base abstrata para todas as vocações (classes) do jogo.
    Cada subclasse define modificadores e sobrescreve habilidade_especial()
    com comportamento único — polimorfismo.
    """

    def __init__(self):
        self.mod_poder:   int = 0
        self.mod_defesa:  int = 0
        self.mod_vida:    int = 0
        self.mod_esquiva: int = 0
        self._habilidade_usos = 1   # usos por combate (padrão: 1)

    @property
    @abstractmethod
    def nome(self) -> str:
        ...

    @property
    @abstractmethod
    def descricao(self) -> str:
        ...

    @property
    @abstractmethod
    def nome_habilidade(self) -> str:
        """Nome da habilidade especial para exibir no menu."""
        ...

    @abstractmethod
    def habilidade_especial(self, jogador: object, alvo: object) -> dict:
        """
        Habilidade especial ativada pelo jogador em combate.
        Retorna um dict com: { "narrativa": str, "dano": int, "efeito": str }
        """
        ...

    def tem_uso_disponivel(self) -> bool:
        return self._habilidade_usos > 0

    def resetar_usos(self) -> None:
        """Chamado ao início de cada novo combate."""
        self._habilidade_usos = 1

    def resumo_modificadores(self) -> str:
        partes = []
        if self.mod_poder: partes.append(f"Poder {self.mod_poder:+d}")
        if self.mod_defesa: partes.append(f"Defesa {self.mod_defesa:+d}")
        if self.mod_vida: partes.append(f"Vida {self.mod_vida:+d}")
        if self.mod_esquiva: partes.append(f"Esquiva {self.mod_esquiva:+d}")
        return " | ".join(partes) if partes else "Sem modificadores"

    def __str__(self) -> str:
        return f"{self.nome} ({self.resumo_modificadores()})"


# ======================================================================= #
#  Vocações concretas
# ======================================================================= #

class Pistoleiro(Vocacao):
    """
    Especialista em dano direto e velocidade.
    Habilidade: Tiro Duplo — dispara duas vezes no mesmo turno.
    """

    def __init__(self):
        super().__init__()
        self.mod_poder   = 5
        self.mod_defesa  = 0
        self.mod_vida    = 0
        self.mod_esquiva = 2

    @property
    def nome(self) -> str:
        return "Pistoleiro"

    @property
    def descricao(self) -> str:
        return (
            "Nasceu com uma arma na mão e morreu com outra. "
            "Nenhum alvo escapa dos seus disparos no deserto do silício."
        )

    @property
    def nome_habilidade(self) -> str:
        return "Tiro Duplo"

    def habilidade_especial(self, jogador, alvo: object) -> dict:
        """Realiza dois ataques no mesmo turno."""
        if not self.tem_uso_disponivel():
            return {
                "narrativa": "Tiro Duplo já foi usado neste combate!",
                "dano": 0,
                "efeito": "",
            }

        self._habilidade_usos -= 1
        dano_total = 0
        narrativa_partes = ["TIRO DUPLO!"]

        for i in range(2):
            d20  = SistemaDados.rolar_d20()
            critico = d20 == 20
            acertou = (d20 + jogador.poder) >= (alvo.defesa + 10) or critico
            if acertou:
                d6  = SistemaDados.rolar_d6()
                dano = max(1, jogador.poder + d6 - alvo.defesa)
                if critico:
                    dano *= 2
                alvo.receber_dano(dano)
                dano_total += dano
                narrativa_partes.append(f"  Disparo {i+1}: {dano} de dano!")
            else:
                narrativa_partes.append(f"  Disparo {i+1}: errou!")

        return {
            "narrativa": "\n".join(narrativa_partes),
            "dano": dano_total,
            "efeito": "tiro_duplo",
        }


class TecnoSabio(Vocacao):
    """
    Especialista em exploração e puzzles de terminal.
    Habilidade: Hack — desativa a defesa do inimigo por 1 turno.
    """

    def __init__(self):
        super().__init__()
        self.mod_poder   = 5
        self.mod_defesa  = 2
        self.mod_vida    = 0
        self.mod_esquiva = 0

    @property
    def nome(self) -> str:
        return "Tecno-Sábio"

    @property
    def descricao(self) -> str:
        return (
            "Se há um terminal, ele encontra uma brecha. "
            "Conhece cada protocolo de segurança antigo e sabe exatamente "
            "como quebrá-los."
        )

    @property
    def nome_habilidade(self) -> str:
        return "Hack"

    def habilidade_especial(self, jogador, alvo) -> dict:
        """Reduz a defesa do alvo a 0 por 1 turno e causa dano de sistema."""
        if not self.tem_uso_disponivel():
            return {
                "narrativa": "Hack já foi usado neste combate!",
                "dano": 0,
                "efeito": "",
            }

        self._habilidade_usos -= 1

        defesa_original = alvo.defesa
        alvo.defesa = 0   # defesa zerada este turno

        # Ataque garantido com dano aumentado
        d6   = SistemaDados.rolar_d6()
        dano = jogador.poder + d6 + 3   # +3 de dano de sistema
        alvo.receber_dano(dano)

        # Restaura defesa no próximo turno (controle externo via flag)
        alvo._defesa_hackeada = defesa_original

        return {
            "narrativa": (
                f"HACK! Você invade os sistemas de {alvo.nome}!\n"
                f"Defesa zerada! Causa {dano} de dano de sobrecarga!"
            ),
            "dano": dano,
            "efeito": "hack",
        }


class Sucateiro(Vocacao):
    """
    Especialista em sobrevivência e resistência.
    Habilidade: Improviso — constrói um escudo improvisado que absorve dano.
    """

    def __init__(self):
        super().__init__()
        self.mod_poder   =  0
        self.mod_defesa  =  3
        self.mod_vida    = 15
        self.mod_esquiva =  0
        self._escudo_pontos = 0

    @property
    def nome(self) -> str:
        return "Sucateiro"

    @property
    def descricao(self) -> str:
        return (
            "Faz armas com latas velhas e cura ferimentos com fita isolante. "
            "Improvisa onde outros desistem — e sempre acha uma saída."
        )

    @property
    def nome_habilidade(self) -> str:
        return "Escudo Improvisado"

    def habilidade_especial(self, jogador, alvo) -> dict:
        """
        Monta um escudo improvisado com sucata.
        Absorve até 15 de dano no próximo turno.
        """
        if not self.tem_uso_disponivel():
            return {
                "narrativa": "Escudo Improvisado já foi usado neste combate!",
                "dano": 0,
                "efeito": "",
            }

        self._habilidade_usos -= 1
        escudo = 10 + SistemaDados.rolar_d6()
        self._escudo_pontos    = escudo
        self._bonus_defesa_tmp = 5      # rastreia para poder reverter ao fim do combate
        jogador.defesa += self._bonus_defesa_tmp

        return {
            "narrativa": (
                f"ESCUDO IMPROVISADO!\n"
                f"Você monta um escudo de sucata às pressas!\n"
                f"+{self._bonus_defesa_tmp} de Defesa temporária e absorção de {escudo} de dano!"
            ),
            "dano": 0,
            "efeito": "escudo_improvisado",
        }

    def absorver_dano_escudo(self, dano: int) -> int:
        """Chamado ao receber dano — desconta do escudo primeiro."""
        if self._escudo_pontos > 0:
            absorvido = min(self._escudo_pontos, dano)
            self._escudo_pontos -= absorvido
            return dano - absorvido
        return dano

    def reverter_bonus_combate(self, jogador) -> None:
        """
        Reverte o bônus temporário de defesa concedido pelo Escudo Improvisado.
        Chamado por SistemaCombate ao encerrar o combate.
        """
        bonus = getattr(self, "_bonus_defesa_tmp", 0)
        if bonus:
            jogador.defesa       -= bonus
            self._bonus_defesa_tmp = 0
        self._escudo_pontos = 0