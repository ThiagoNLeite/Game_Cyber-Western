from mecanicas.dados import SistemaDados
from entidades.entidade import Entidade
 
 
class SistemaCombate:
    """
    Gerencia um combate completo entre o Jogador e um inimigo.
    Controla o fluxo de turnos, aplica efeitos pós-turno
    e notifica o resultado para a interface exibir.
    """
 
    def __init__(self, jogador, inimigo: Entidade):
        self.jogador = jogador
        self.inimigo = inimigo
        self.turno = 1
        self.log: list[str] = []   # histórico para a interface
 
        # Reseta usos de habilidade especial a cada novo combate
        jogador.vocacao.resetar_usos()
 
        # Reseta mira do Androide se aplicável
        if hasattr(jogador.raca, "resetar_mira"):
            jogador.raca.resetar_mira()
 
    # ------------------------------------------------------------------ #
    #  Ações do jogador
    # ------------------------------------------------------------------ #
 
    def jogador_atacar(self) -> dict:
        """Jogador ataca o inimigo com ataque normal."""
        resultado = self.jogador.atacar(self.inimigo)
        self._restaurar_hack()
        self._registrar(resultado)
        return resultado
 
    def jogador_habilidade(self) -> dict:
        """Jogador usa a habilidade especial da vocação."""
        resultado = self.jogador.habilidade_especial(self.inimigo)
 
        # Corrige o poder do Androide após mira assistida
        if hasattr(self.jogador.raca, "_mira_disponivel"):
            if not self.jogador.raca._mira_disponivel:
                # já foi usada, reverte o bônus
                if self.jogador.poder > self.jogador.poder - 5:
                    self.jogador.poder -= 5
 
        self._restaurar_hack()
        self.log.append({"turno": self.turno, "linhas": [resultado.get("narrativa", "")]})
        return resultado
 
    def jogador_fugir(self) -> bool:
        """Tenta fuga. Retorna True se conseguiu."""
        fugiu = self.jogador.tentar_fuga()
        msg = (
            "Você escapou pela poeira do deserto!"
            if fugiu else
            "Fuga falhou! O inimigo bloqueia o caminho."
        )
        self.log.append({"turno": self.turno, "linhas": [msg]})
        return fugiu
 
    # ------------------------------------------------------------------ #
    #  Turno do inimigo
    # ------------------------------------------------------------------ #
 
    def inimigo_atacar(self) -> dict:
        """Inimigo ataca o jogador."""
        resultado = self.inimigo.atacar(self.jogador)
 
        # Sucateiro: escudo absorve dano
        if hasattr(self.jogador.vocacao, "absorver_dano_escudo") and resultado["dano"] > 0:
            dano_apos_escudo = self.jogador.vocacao.absorver_dano_escudo(resultado["dano"])
            dano_absorvido   = resultado["dano"] - dano_apos_escudo
            if dano_absorvido > 0:
                # reverte o dano já aplicado e reaplica o correto
                self.jogador.vida_atual = min(
                    self.jogador.vida_maxima,
                    self.jogador.vida_atual + dano_absorvido
                )
                resultado["narrativa_escudo"] = (
                    f"Escudo absorveu {dano_absorvido} de dano!"
                )
 
        # Ciborgue: escudo de armadura
        if hasattr(self.jogador.raca, "absorver_dano") and resultado["dano"] > 0:
            dano_apos_armadura = self.jogador.raca.absorver_dano(resultado["dano"])
            dano_absorvido     = resultado["dano"] - dano_apos_armadura
            if dano_absorvido > 0:
                self.jogador.vida_atual = min(
                    self.jogador.vida_maxima,
                    self.jogador.vida_atual + dano_absorvido
                )
                resultado["narrativa_armadura"] = (
                    f"Armadura de titânio absorveu {dano_absorvido} de dano!"
                )
 
        # Passiva Humano: ao receber crítico
        if resultado.get("critico") and isinstance(self.jogador.raca.__class__.__name__, str):
            if self.jogador.raca.__class__.__name__ == "Humano":
                msg = self.jogador.raca.habilidade_passiva(self.jogador)
                resultado["narrativa_passiva"] = msg
 
        self._registrar(resultado)
        self.turno += 1
        return resultado

    # ------------------------------------------------------------------ #
    #  Resolução completa de 1 turno (jogador → inimigo)
    # ------------------------------------------------------------------ #

    def executar_turno(self, acao: str, nome_item: str = None) -> dict:
        """
        Recebe a ação do jogador ("atacar", "habilidade", "item", "fugir")
        e resolve o turno completo.
        Retorna um dict com todos os eventos do turno para a interface renderizar.
        """
        turno_resultado = {
            "turno": self.turno,
            "acao_jogador": {},
            "acao_inimigo": {},
            "fim_combate": False,
            "vitoria": False,
            "fuga": False,
        }

        # --- Ação do jogador ---
        if acao == "atacar":
            turno_resultado["acao_jogador"] = self.jogador_atacar()

        elif acao == "habilidade":
            turno_resultado["acao_jogador"] = self.jogador_habilidade()

        elif acao == "item" and nome_item:
            msg = self.jogador.usar_item(nome_item)
            turno_resultado["acao_jogador"] = {"narrativa": msg, "dano": 0}

        elif acao == "fugir":
            fugiu = self.jogador_fugir()
            turno_resultado["fuga"] = fugiu
            turno_resultado["fim_combate"] = fugiu
            if fugiu:
                self._encerrar_combate()
            return turno_resultado

        # --- Verifica morte do inimigo ---
        if not self.inimigo.esta_vivo:
            turno_resultado["fim_combate"] = True
            turno_resultado["vitoria"] = True
            xp_ganho = self.inimigo.xp_recompensa
            subiu = self.jogador.ganhar_xp(xp_ganho)
            turno_resultado["xp_ganho"] = xp_ganho
            turno_resultado["subiu_nivel"] = subiu
            self._encerrar_combate()
            return turno_resultado

        # --- Inimigo contra-ataca ---
        turno_resultado["acao_inimigo"] = self.inimigo_atacar()

        # --- Verifica morte do jogador ---
        if not self.jogador.esta_vivo:
            turno_resultado["fim_combate"] = True
            turno_resultado["vitoria"] = False
            self._encerrar_combate()

        return turno_resultado

    # ------------------------------------------------------------------ #
    #  Encerramento de combate
    # ------------------------------------------------------------------ #

    def _encerrar_combate(self) -> None:
        """
        Reverte todos os efeitos temporários aplicados durante o combate.
        Deve ser chamado em todos os pontos de saída do combate.

        Efeitos revertidos:
          - Bônus de defesa do Escudo Improvisado (Sucateiro)
        """
        if hasattr(self.jogador.vocacao, "reverter_bonus_combate"):
            self.jogador.vocacao.reverter_bonus_combate(self.jogador)

     # ------------------------------------------------------------------ #
    #  Utilitários internos
    # ------------------------------------------------------------------ #
 
    def _restaurar_hack(self) -> None:
        """Restaura a defesa do inimigo se foi hackeada no turno anterior."""
        if hasattr(self.inimigo, "_defesa_hackeada"):
            self.inimigo.defesa = self.inimigo._defesa_hackeada
            del self.inimigo._defesa_hackeada
 
    def _registrar(self, resultado: dict) -> None:
        """
        Adiciona eventos do turno ao log como dict {turno, linhas}.
        Isso permite que a interface exiba separadores de turno.
        """
        linhas = []
        if resultado.get("critico"):
            linhas.append(f"CRÍTICO! {resultado['atacante']} causou {resultado['dano']} de dano em {resultado['alvo']}!")
        elif resultado.get("acertou"):
            linhas.append(f"{resultado['atacante']} causou {resultado['dano']} de dano em {resultado['alvo']}.")
        else:
            linhas.append(f"{resultado['atacante']} errou o ataque!")
 
        if resultado.get("efeito"):
            linhas.append(str(resultado["efeito"]))
 
        self.log.append({"turno": self.turno, "linhas": linhas})
 
    def estado_combate(self) -> dict:
        """Snapshot atual para a interface renderizar a HUD."""
        return {
            "turno": self.turno,
            "jogador": {
                "nome": self.jogador.nome,
                "vida_atual": self.jogador.vida_atual,
                "vida_max": self.jogador.vida_maxima,
                "nivel": self.jogador.nivel,
            },
            "inimigo": {
                "nome": self.inimigo.nome,
                "vida_atual": self.inimigo.vida_atual,
                "vida_max": self.inimigo.vida_maxima,
                # Boss expõe a fase atual
                "fase": getattr(self.inimigo, "fase", None),
            },
        }