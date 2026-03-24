from entidades.entidade import Entidade
from mecanicas.dados import SistemaDados


class Jogador(Entidade):
    """
    Representa o personagem controlado pelo jogador.
    Herda de Entidade e adiciona nível, inventário, raça e vocação.
    """

    XP_POR_NIVEL = 80   # XP necessário para subir de nível

    def __init__(self, nome: str, raca, vocacao):
        # Atributos base antes dos modificadores
        poder_base  = 5
        defesa_base = 5
        vida_base   = 50
        esquiva_base = 5

        # Aplica modificadores de raça e vocação (polimorfismo)
        poder_base   += raca.mod_poder   + vocacao.mod_poder
        defesa_base  += raca.mod_defesa  + vocacao.mod_defesa
        vida_base    += raca.mod_vida    + vocacao.mod_vida
        esquiva_base += raca.mod_esquiva + vocacao.mod_esquiva

        super().__init__(nome, poder_base, defesa_base, vida_base, esquiva_base)

        self.raca = raca
        self.vocacao = vocacao
        self.xp = 0
        self.celulas_fusao = 10        # moeda do jogo
        self.inventario: list = []
        self.cenario_atual = 0
        self.nivel = 1
        # Slots de equipamento: "arma" e "armadura"
        self.equipamentos: dict = {"arma": None, "armadura": None}
        # Slot de save que este perfil usa (definido no carregamento/criação)
        self.slot_salvo: int = 1

    # ------------------------------------------------------------------ #
    #  Progressão
    # ------------------------------------------------------------------ #

    def ganhar_xp(self, quantidade: int) -> bool:
        """Adiciona XP e verifica se sobe de nível. Retorna True se subiu."""
        self.xp += quantidade
        if self.xp >= self.nivel * self.XP_POR_NIVEL:
            self._subir_nivel()
            return True
        return False

    def _subir_nivel(self) -> None:
        self.nivel += 1
        self.xp = 0
        # Cada nível aumenta os atributos base
        self.poder        += 2
        self.defesa       += 1
        self.vida_maxima  += 15
        self.vida_atual   += 15          # cura parcial ao subir de nível
        self.esquiva      += 1

    # ------------------------------------------------------------------ #
    #  Inventário
    # ------------------------------------------------------------------ #

    def pegar_item(self, item) -> None:
        self.inventario.append(item)

    def usar_item(self, nome_item: str) -> str:
        for item in self.inventario:
            if item.nome.lower() == nome_item.lower():
                resultado = item.usar(self)
                if item.consumivel:
                    self.inventario.remove(item)
                return resultado
        return f"Você não tem '{nome_item}' no inventário."

    # ------------------------------------------------------------------ #
    #  Habilidade especial — polimorfismo via vocação
    # ------------------------------------------------------------------ #

    def habilidade_especial(self, alvo: Entidade) -> dict:
        """Delega a habilidade especial para a vocação do jogador."""
        return self.vocacao.habilidade_especial(self, alvo)


    def equipar(self, item) -> str:
        """
        Equipa um ItemEquipavel e retorna narrativa.
        Desequipa automaticamente o item anterior do mesmo slot.
        """
        slot = item.slot
        atual = self.equipamentos.get(slot)
        if atual and atual is not self:
            atual.unequip(self)
            self.equipamentos[slot] = None
        self.equipamentos[slot] = item
        item.equip(self)
        mods = item.resumo_mods()
        return f"Voce equipou {item.nome}!\n  {mods}"

    def desequipar(self, slot: str) -> str:
        """Desequipa o item do slot informado e retorna narrativa."""
        item = self.equipamentos.get(slot)
        if not item:
            return f"Nenhum item equipado no slot '{slot}'."
        item.unequip(self)
        self.equipamentos[slot] = None
        return f"{item.nome} desequipado."

    def item_equipado(self, slot: str):
        """Retorna o item equipado no slot ou None."""
        return self.equipamentos.get(slot)

    # ------------------------------------------------------------------ #
    #  Fuga
    # ------------------------------------------------------------------ #

    def tentar_fuga(self) -> bool:
        """Teste de fuga: d20 + Esquiva >= 15."""
        return SistemaDados.rolar_d20() + self.esquiva >= 15

    # ------------------------------------------------------------------ #
    #  Descrição narrativa (implementação do método abstrato)
    # ------------------------------------------------------------------ #

    def descricao(self) -> str:
        return (
            f"{self.nome}, {self.raca.nome} {self.vocacao.nome} "
            f"— Nível {self.nivel} | {self.celulas_fusao} Células de Fusão"
        )