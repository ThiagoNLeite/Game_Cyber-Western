from abc import ABC, abstractmethod


class Raca(ABC):
    """
    Classe BASE abstrata para todas as raças jogáveis.
    Cada subclasse define seus modificadores de atributo
    e sobrescreve o método habilidade_passiva() — polimorfismo.
    """

    def __init__(self):
        # Modificadores aplicados sobre os atributos base do Jogador
        self.mod_poder:   int = 0
        self.mod_defesa:  int = 0
        self.mod_vida:    int = 0
        self.mod_esquiva: int = 0

    @property
    @abstractmethod
    def nome(self) -> str:
        """Nome da raça exibido na tela."""
        ...

    @property
    @abstractmethod
    def descricao(self) -> str:
        """Descrição narrativa da raça."""
        ...

    @abstractmethod
    def habilidade_passiva(self, jogador) -> str:
        """
        Efeito passivo único da raça.
        Chamado em momentos específicos do jogo (ex: início de combate,
        ao receber dano, ao curar).
        Retorna uma string narrativa para exibir na tela.
        """
        ...

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
#  Raças concretas
# ======================================================================= #

class Humano(Raca):
    """
    Equilibrado em todos os atributos.
    Passiva: Resiliência — recupera 5 de vida ao sobreviver a um golpe crítico.
    """

    def __init__(self):
        super().__init__()
        self.mod_poder   = 2
        self.mod_defesa  = 2
        self.mod_vida    = 2
        self.mod_esquiva = 2

    @property
    def nome(self) -> str:
        return "Humano"

    @property
    def descricao(self) -> str:
        return (
            "Sobreviventes adaptáveis do Grande Curto. "
            "Sem implantes, sem circuitos — só força de vontade e pólvora."
        )

    def habilidade_passiva(self, jogador: object) -> str:
        """Ao receber um golpe crítico, recupera 5 de vida."""
        jogador.curar(5)
        return "Resiliência Humana! Você se recusa a cair — recupera 5 de vida!"


class Ciborgue(Raca):
    """
    Focado em resistência.
    Passiva: Armadura Reforçada — reduz o próximo dano recebido em 3.
    """

    def __init__(self):
        super().__init__()
        self.mod_poder   =  0
        self.mod_defesa  =  5
        self.mod_vida    = 10
        self.mod_esquiva = -2
        self._escudo_ativo = False

    @property
    def nome(self) -> str:
        return "Ciborgue"

    @property
    def descricao(self) -> str:
        return (
            "Metade carne, metade aço. Plaquetas de titânio sob a pele, "
            "olhos de câmera infravermelho. Lento, mas quase impossível de derrubar."
        )

    def ativar_escudo(self) -> str:
        """Ativa o escudo para o próximo turno."""
        self._escudo_ativo = True
        return "Armadura Reforçada ativada! O próximo dano será reduzido em 3."

    def habilidade_passiva(self, jogador) -> str:
        """Ao início do combate, ativa o escudo automático."""
        return self.ativar_escudo()

    def absorver_dano(self, dano: int) -> int:
        """Aplica a absorção do escudo se estiver ativo."""
        if self._escudo_ativo:
            self._escudo_ativo = False
            return max(0, dano - 3)
        return dano


class Androide(Raca):
    """
    Focado em precisão e velocidade.
    Passiva: Mira Assistida — o primeiro ataque do combate tem vantagem (+5 no d20).
    """

    def __init__(self):
        super().__init__()
        self.mod_poder   =  5
        self.mod_defesa  =  0
        self.mod_vida    = -3
        self.mod_esquiva =  3
        self._mira_disponivel = True

    @property
    def nome(self) -> str:
        return "Androide"

    @property
    def descricao(self) -> str:
        return (
            "Sintético de última geração antes do Grande Curto. "
            "Processadores ainda funcionam — seus reflexos são sobre-humanos "
            "e cada disparo é calculado ao milímetro."
        )

    def habilidade_passiva(self, jogador) -> str:
        """Concede +5 no primeiro ataque do combate."""
        if self._mira_disponivel:
            jogador.poder += 5
            self._mira_disponivel = False
            return "Mira Assistida ativada! +5 de Poder neste ataque!"
        return ""

    def resetar_mira(self) -> None:
        """Reseta a mira para o próximo combate."""
        self._mira_disponivel = True