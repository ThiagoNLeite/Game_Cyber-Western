from abc import ABC, abstractmethod
from mecanicas.dados import SistemaDados


class Item(ABC):
    """
    Classe base abstrata para todos os itens do inventário.
    Cada subclasse implementa usar() com efeito único — polimorfismo.
    """

    def __init__(self, nome: str, descricao: str, consumivel: bool = True, raridade: str = "comum"):
        self.nome       = nome
        self.descricao  = descricao
        self.consumivel = consumivel   # se True, é removido do inventário após uso
        self.raridade   = raridade     # "comum", "incomum", "raro"

    @abstractmethod
    def usar(self, jogador) -> str:
        """Aplica o efeito do item no jogador. Retorna narrativa para a tela."""
        ...

    def __str__(self) -> str:
        tag = "★" if self.raridade == "raro" else ("◆" if self.raridade == "incomum" else "·")
        return f"{tag} {self.nome} — {self.descricao}"


# ======================================================================= #
#  Subclasses concretas
# ======================================================================= #

class ItemCura(Item):
    """
    Restaura vida do jogador.
    Exemplos: Cantil de Água Purificada, Gel Nanite, Ração de Emergência.
    """

    def __init__(self, nome: str, descricao: str, cura: int, raridade: str = "comum"):
        super().__init__(nome, descricao, consumivel=True, raridade=raridade)
        self.cura = cura

    def usar(self, jogador) -> str:
        vida_antes = jogador.vida_atual
        jogador.curar(self.cura)
        curado = jogador.vida_atual - vida_antes
        return (
            f"Você usou {self.nome}.\n"
            f"  +{curado} de vida! ({jogador.vida_atual}/{jogador.vida_maxima})"
        )


class ItemCombate(Item):
    """
    Causa dano direto ao inimigo ou aplica um debuff.
    Exemplos: Granada de Plasma, Bomba de Fumaça, Spike EMP.
    """

    def __init__(self, nome: str, descricao: str, dano_min: int, dano_max: int,
                 efeito: str = None, raridade: str = "comum"):
        super().__init__(nome, descricao, consumivel=True, raridade=raridade)
        self.dano_min = dano_min
        self.dano_max = dano_max
        self.efeito   = efeito   # None | "stun" | "emp" | "fogo"

    def usar(self, jogador) -> str:
        """Marca o item como pendente — o combate aplica o dano no inimigo."""
        dano = SistemaDados.rolar_personalizado(self.dano_min, self.dano_max)
        jogador._item_combate_pendente = {"dano": dano, "efeito": self.efeito, "nome": self.nome}
        msg = f"Você preparou {self.nome}! ({dano} de dano"
        if self.efeito:
            msg += f" + efeito: {self.efeito}"
        return msg + ")"


class ItemUtilidade(Item):
    """
    Melhora atributos temporariamente ou concede bônus situacional.
    Exemplos: Stimpak de Adrenalina, Óculos de Mira, Blindagem Improvisada.
    """

    def __init__(self, nome: str, descricao: str,
                 buff_poder: int = 0, buff_defesa: int = 0,
                 buff_esquiva: int = 0, buff_vida: int = 0,
                 raridade: str = "comum"):
        super().__init__(nome, descricao, consumivel=True, raridade=raridade)
        self.buff_poder   = buff_poder
        self.buff_defesa  = buff_defesa
        self.buff_esquiva = buff_esquiva
        self.buff_vida    = buff_vida

    def usar(self, jogador) -> str:
        linhas = [f"Você usou {self.nome}!"]

        if self.buff_poder:
            jogador.poder += self.buff_poder
            linhas.append(f"  +{self.buff_poder} de Poder")

        if self.buff_defesa:
            jogador.defesa += self.buff_defesa
            linhas.append(f"  +{self.buff_defesa} de Defesa")

        if self.buff_esquiva:
            jogador.esquiva += self.buff_esquiva
            linhas.append(f"  +{self.buff_esquiva} de Esquiva")

        if self.buff_vida:
            jogador.vida_maxima += self.buff_vida
            jogador.vida_atual  += self.buff_vida
            linhas.append(f"  +{self.buff_vida} de Vida Máxima")

        return "\n".join(linhas)



class ItemEquipavel(Item):
    """
    Item que pode ser equipado para modificar atributos do jogador.

    Implementa equip(jogador) e unequip(jogador) — polimorfismo.
    Não é consumido ao usar (consumivel=False).
    Slots disponíveis: "arma" | "armadura"

    POO: herda de Item (ABC), sobrescreve usar() e adiciona equip/unequip.
    """

    SLOTS_VALIDOS = ("arma", "armadura")

    def __init__(self, nome: str, descricao: str, slot: str,
                 mod_poder: int = 0, mod_defesa: int = 0,
                 mod_esquiva: int = 0, mod_vida_max: int = 0,
                 raridade: str = "comum"):
        if slot not in self.SLOTS_VALIDOS:
            raise ValueError(f"Slot inválido: {slot!r}. Use {self.SLOTS_VALIDOS}")
        super().__init__(nome, descricao, consumivel=False, raridade=raridade)
        self.slot         = slot
        self.mod_poder    = mod_poder
        self.mod_defesa   = mod_defesa
        self.mod_esquiva  = mod_esquiva
        self.mod_vida_max = mod_vida_max
        self._equipado    = False   # estado interno

    # ------------------------------------------------------------------ #
    #  Interface de equipar / desequipar
    # ------------------------------------------------------------------ #

    def equip(self, jogador) -> None:
        """Aplica os modificadores nos atributos do jogador."""
        jogador.poder       += self.mod_poder
        jogador.defesa      += self.mod_defesa
        jogador.esquiva     += self.mod_esquiva
        jogador.vida_maxima += self.mod_vida_max
        if self.mod_vida_max > 0:
            jogador.vida_atual = min(jogador.vida_atual + self.mod_vida_max,
                                     jogador.vida_maxima)
        self._equipado = True

    def unequip(self, jogador) -> None:
        """Remove os modificadores dos atributos do jogador."""
        jogador.poder       -= self.mod_poder
        jogador.defesa      -= self.mod_defesa
        jogador.esquiva     -= self.mod_esquiva
        jogador.vida_maxima -= self.mod_vida_max
        # Garante que vida atual não exceda o novo máximo
        jogador.vida_atual   = min(jogador.vida_atual, jogador.vida_maxima)
        self._equipado = False

    # ------------------------------------------------------------------ #
    #  usar() — alterna equip/unequip (chamado pelo inventário)
    # ------------------------------------------------------------------ #

    def usar(self, jogador) -> str:
        if self._equipado:
            # Já equipado → desequipa
            self.unequip(jogador)
            jogador.equipamentos[self.slot] = None
            return f"Voce desequipou {self.nome}."
        else:
            # Desequipa o item atual do slot se houver
            atual = jogador.equipamentos.get(self.slot)
            if atual and atual is not self:
                atual.unequip(jogador)
                jogador.equipamentos[self.slot] = None

            # Equipa este item
            jogador.equipamentos[self.slot] = self
            self.equip(jogador)

            mods = self.resumo_mods()
            return f"Voce equipou {self.nome}!\n  {mods}"

    # ------------------------------------------------------------------ #
    #  Utilitários
    # ------------------------------------------------------------------ #

    @property
    def esta_equipado(self) -> bool:
        return self._equipado

    def resumo_mods(self) -> str:
        """String compacta dos bônus para exibição na UI."""
        partes = []
        if self.mod_poder:    partes.append(f"POD {self.mod_poder:+d}")
        if self.mod_defesa:   partes.append(f"DEF {self.mod_defesa:+d}")
        if self.mod_esquiva:  partes.append(f"ESQ {self.mod_esquiva:+d}")
        if self.mod_vida_max: partes.append(f"VID {self.mod_vida_max:+d}")
        return " | ".join(partes) if partes else "sem bonus"

    def __str__(self) -> str:
        tag = "★" if self.raridade == "raro" else ("◆" if self.raridade == "incomum" else "·")
        estado = " [EQUIPADO]" if self._equipado else ""
        return f"{tag} {self.nome}{estado} — {self.resumo_mods()}"


# ======================================================================= #
#  Fábrica de itens — carrega do JSON e instancia a subclasse correta
# ======================================================================= #

class FabricaItens:
    """
    Cria instâncias de Item a partir de dicionários (carregados do JSON).
    Usa o campo "tipo" para decidir qual subclasse instanciar — polimorfismo.
    """

    _CONSTRUTORES = {
        "cura":       ItemCura,
        "combate":    ItemCombate,
        "utilidade":  ItemUtilidade,
        "equipavel":  ItemEquipavel,
    }

    @classmethod
    def criar(cls, dados: dict) -> Item:
        tipo = dados.get("tipo", "cura")
        construtor = cls._CONSTRUTORES.get(tipo)
        if not construtor:
            raise ValueError(f"Tipo de item desconhecido: '{tipo}'")

        raridade = dados.get("raridade", "comum")

        if tipo == "cura":
            return ItemCura(
                nome = dados["nome"],
                descricao = dados["descricao"],
                cura = dados["cura"],
                raridade = raridade,
            )
        if tipo == "combate":
            return ItemCombate(
                nome = dados["nome"],
                descricao = dados["descricao"],
                dano_min = dados["dano_min"],
                dano_max = dados["dano_max"],
                efeito = dados.get("efeito"),
                raridade = raridade,
            )
        if tipo == "utilidade":
            return ItemUtilidade(
                nome = dados["nome"],
                descricao = dados["descricao"],
                buff_poder = dados.get("buff_poder",   0),
                buff_defesa = dados.get("buff_defesa",  0),
                buff_esquiva= dados.get("buff_esquiva", 0),
                buff_vida = dados.get("buff_vida",    0),
                raridade = raridade,
            )
        if tipo == "equipavel":
            return ItemEquipavel(
                nome         = dados["nome"],
                descricao    = dados["descricao"],
                slot         = dados["slot"],
                mod_poder    = dados.get("mod_poder",    0),
                mod_defesa   = dados.get("mod_defesa",   0),
                mod_esquiva  = dados.get("mod_esquiva",  0),
                mod_vida_max = dados.get("mod_vida_max", 0),
                raridade     = raridade,
            )

    @classmethod
    def item_aleatorio(cls, pool: list[dict], raridade_minima: str = "comum") -> Item:
        """
        Sorteia um item aleatório do pool filtrado por raridade mínima.
        Ordem de raridade: comum < incomum < raro.
        """
        import random
        ordem = {"comum": 0, "incomum": 1, "raro": 2}
        nivel_min = ordem.get(raridade_minima, 0)
        elegíveis = [d for d in pool if ordem.get(d.get("raridade", "comum"), 0) >= nivel_min]
        if not elegíveis:
            elegíveis = pool
        return cls.criar(random.choice(elegíveis))