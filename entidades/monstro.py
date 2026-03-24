from entidades.entidade import Entidade
from mecanicas.dados import SistemaDados


class Monstro(Entidade):
    """
    Representa um inimigo comum.
    Seus atributos escalam com o nível do jogador.
    Pode ter um efeito especial passivo (ex: choque, radiação, roubo de energia).
    """

    def __init__(
        self,
        nome: str,
        poder: int,
        defesa: int,
        vida: int,
        esquiva: int,
        xp_recompensa: int,
        efeito_especial: str = None,
        descricao_texto: str = "",
    ):
        super().__init__(nome, poder, defesa, vida, esquiva)
        self.xp_recompensa = xp_recompensa
        self.efeito_especial = efeito_especial   # "choque", "radiacao", "roubo", etc.
        self._descricao_texto = descricao_texto

    # ------------------------------------------------------------------ #
    #  Escalonamento pelo nível do jogador
    # ------------------------------------------------------------------ #

    @classmethod
    def escalar(cls, dados: dict, nivel_jogador: int) -> "Monstro":
        """
        Cria um Monstro com atributos multiplicados pelo nível do jogador.
        Permite instanciar inimigos direto do JSON sem criar 15 subclasses.
        """
        mult = 1 + (nivel_jogador - 1) * 0.3   # +30% por nível
        return cls(
            nome = dados["nome"],
            poder = int(dados["poder"]   * mult),
            defesa = int(dados["defesa"]  * mult),
            vida  = int(dados["vida"]     * mult),
            esquiva = int(dados["esquiva"]  * mult),
            xp_recompensa = int(dados["xp"]       * mult),
            efeito_especial = dados.get("efeito_especial"),
            descricao_texto = dados.get("descricao", ""),
        )

    # ------------------------------------------------------------------ #
    #  Ataque com efeito especial (polimorfismo de comportamento)
    # ------------------------------------------------------------------ #

    def atacar(self, alvo: Entidade) -> dict:
        resultado = super().atacar(alvo)

        # Aplica efeito especial se o ataque acertou
        if resultado["acertou"] and self.efeito_especial:
            resultado["efeito"] = self._aplicar_efeito(alvo)

        return resultado

    def _aplicar_efeito(self, alvo: Entidade) -> str:
        """Aplica o efeito especial do monstro no alvo."""
        efeito = self.efeito_especial

        if efeito == "choque":
            dano_extra = SistemaDados.rolar_d6()
            alvo.receber_dano(dano_extra)
            return f"Choque elétrico! {dano_extra} de dano extra!"

        if efeito == "radiacao":
            # Reduz poder do alvo por 1 (debuff)
            alvo.poder = max(1, alvo.poder - 1)
            return "Radiação! Seu poder foi reduzido em 1!"

        if efeito == "roubo_energia":
            roubo = SistemaDados.rolar_d4()
            alvo.receber_dano(roubo)
            self.curar(roubo)
            return f"Roubo de energia! Absorveu {roubo} de vida!"

        if efeito == "debuff_status":
            alvo.defesa = max(1, alvo.defesa - 1)
            alvo.esquiva = max(0, alvo.esquiva - 1)
            return "IA Tática! Seus sistemas foram comprometidos! -1 Defesa e -1 Esquiva."

        return ""

    # ------------------------------------------------------------------ #
    #  Descrição narrativa
    # ------------------------------------------------------------------ #

    def descricao(self) -> str:
        return self._descricao_texto or f"{self.nome} — um inimigo perigoso do deserto."


# ======================================================================= #
#  BOSS: herda de Monstro e adiciona fases
# ======================================================================= #

class Boss(Monstro):
    """
    O Xerife de Ferro — chefe final com 3 fases.
    Muda o padrão de ataque ao atingir 50% e 25% de vida.
    Demonstra polimorfismo sobrescrevendo atacar().
    """

    NOME = "O Xerife de Ferro"
    DESCRICAO = (
        "Uma máquina colossal de supressão primária. "
        "Chapéu de caubói de aço. Canhão de plasma no braço direito. "
        "Seus olhos vermelhos já viram mil rebeldes cair."
    )

    def __init__(self):
        super().__init__(
            nome = self.NOME,
            poder = 18,
            defesa = 14,
            vida = 300,
            esquiva = 4,
            xp_recompensa = 500,
            efeito_especial = None,
            descricao_texto = self.DESCRICAO,
        )
        self.fase = 1

    # ------------------------------------------------------------------ #
    #  Detecção de fase
    # ------------------------------------------------------------------ #

    def _atualizar_fase(self) -> int | None:
        """Verifica se deve mudar de fase. Retorna o número da nova fase ou None."""
        nova_fase = None
        if self.percentual_vida <= 0.25 and self.fase < 3:
            nova_fase = 3
        elif self.percentual_vida <= 0.50 and self.fase < 2:
            nova_fase = 2

        if nova_fase:
            self.fase = nova_fase
            self._aplicar_buff_fase()
        return nova_fase

    def _aplicar_buff_fase(self) -> None:
        """Cada fase deixa o boss mais agressivo."""
        if self.fase == 2:
            self.poder   += 5
            self.defesa  += 3
        elif self.fase == 3:
            self.poder   += 8
            self.esquiva += 4   # começa a desviar mais

    # ------------------------------------------------------------------ #
    #  Ataque por fase (polimorfismo sobre Monstro.atacar)
    # ------------------------------------------------------------------ #

    def atacar(self, alvo: Entidade) -> dict:
        # Verifica transição de fase antes de atacar
        mudou_fase = self._atualizar_fase()

        resultado = super(Monstro, self).atacar(alvo)   # chama Entidade.atacar
        resultado["fase_boss"]  = self.fase
        resultado["mudou_fase"] = mudou_fase

        # Se mudou de fase, define narrativa de transição independente do acerto
        if mudou_fase == 2:
            resultado["narrativa"] = (
                "O Xerife de Ferro range e se reconfigura. Seus olhos vermelhos "                "pulsam mais intensos. Ele entra em MODO BERSERK!"            )
        elif mudou_fase == 3:
            resultado["narrativa"] = (
                "Uma sirene de emergência ecoa pela sala. O Xerife expõe seus "                "reatores nucleares e começa a se REGENERAR. Esta é a fase final!"            )

        # Se o ataque não acertou, retorna após registrar a narrativa de fase
        if not resultado["acertou"]:
            return resultado

        # Comportamento especial por fase
        if self.fase == 1:
            # Fase 1: ataque simples de canhão
            resultado["narrativa"] = "O Xerife dispara um raio de plasma!"

        elif self.fase == 2:
            # Fase 2: ataque duplo — um extra garantido
            dano_extra = SistemaDados.rolar_d6() + 2
            alvo.receber_dano(dano_extra)
            resultado["dano"] += dano_extra
            resultado["narrativa"] = (
                "O Xerife entra em modo berserk! "
                "Dispara duas vezes com o canhão de plasma!"
            )

        elif self.fase == 3:
            # Fase 3: ataque em área + escudo
            dano_area = SistemaDados.rolar_d8() + 4
            alvo.receber_dano(dano_area)
            resultado["dano"] += dano_area
            self.curar(10)   # regenera 10 de vida por turno
            resultado["narrativa"] = (
                "O Xerife ativa seus reatores de emergência! "
                "Uma explosão de plasma varre a sala. Ele está se regenerando!"
            )

        return resultado

    def descricao(self) -> str:
        return f"{self.DESCRICAO}\n[Fase atual: {self.fase}/3]"