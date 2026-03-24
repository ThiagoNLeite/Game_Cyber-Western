import json
import random
from abc import ABC, abstractmethod
from pathlib import Path
from mecanicas.dados import SistemaDados
from itens.item import FabricaItens


class Desafio(ABC):
    """
    Classe base abstrata para todos os desafios/eventos interativos.
    Cada subclasse implementa executar() com sua própria lógica — polimorfismo.
    """

    @abstractmethod
    def executar(self, jogador, resposta=None) -> dict:
        """
        Resolve o desafio com base na resposta/ação do jogador.
        Retorna um dict com:
          - "sucesso"   : bool
          - "narrativa" : str  — texto para a interface exibir
          - "recompensa": dict — { "celulas": int, "item": str|None }
          - "penalidade": dict — { "dano": int, "efeito": str|None }
          - "concluido" : bool — True quando o desafio não pode mais ser tentado
        """
        ...

    @staticmethod
    def _resultado_base(sucesso: bool) -> dict:
        return {
            "sucesso":    sucesso,
            "narrativa":  "",
            "recompensa": {"celulas": 0, "item": None},
            "penalidade": {"dano": 0, "efeito": None},
            "concluido":  sucesso,
        }


# ======================================================================= #
#  Desafios concretos
# ======================================================================= #

class DesafioTerminal(Desafio):
    """
    Quebra-cabeça matemático em um terminal abandonado.
    O Tecno-Sábio recebe uma dica automática.
    Até 3 tentativas antes de tomar choque.
    """

    SEQUENCIAS = [
        {"pergunta": "Próximo número: 2, 4, 8, 16, ...?",  "resposta": 32},
        {"pergunta": "Próximo número: 1, 1, 2, 3, 5, ...?", "resposta": 8},
        {"pergunta": "Próximo número: 3, 6, 12, 24, ...?",  "resposta": 48},
        {"pergunta": "Próximo número: 5, 10, 20, 40, ...?", "resposta": 80},
        {"pergunta": "Próximo número: 7, 14, 21, 28, ...?", "resposta": 35},
    ]

    def __init__(self, dificuldade: int = 1):
        self.dificuldade = dificuldade
        self._puzzle = random.choice(self.SEQUENCIAS)
        self.tentativas = 3
        self._concluido = False

    @property
    def pergunta(self) -> str:
        return self._puzzle["pergunta"]

    def dica(self, jogador) -> str:
        """Tecno-Sábio recebe dica automática."""
        if jogador.vocacao.__class__.__name__ == "TecnoSabio":
            return f"[HACK] Dica do sistema: a resposta é {self._puzzle['resposta']}."
        return "Nenhuma dica disponível para sua vocação."

    def executar(self, jogador, resposta=None) -> dict:
        resultado = self._resultado_base(False)

        if self._concluido:
            resultado["narrativa"]  = "Este terminal já foi resolvido."
            resultado["concluido"]  = True
            return resultado

        if resposta is None:
            resultado["narrativa"] = (
                f"Terminal de Segurança\n"
                f"{self._puzzle['pergunta']}\n"
                f"Tentativas restantes: {self.tentativas}"
            )
            return resultado

        try:
            resposta_int = int(resposta)
        except (ValueError, TypeError):
            resultado["narrativa"] = "Entrada inválida. Digite um número."
            return resultado

        if resposta_int == self._puzzle["resposta"]:
            recompensa_celulas = 5 * self.dificuldade
            resultado["sucesso"] = True
            resultado["concluido"] = True
            resultado["recompensa"]["celulas"] = recompensa_celulas
            resultado["narrativa"] = (
                f"Acesso concedido! O terminal destrava.\n"
                f"+{recompensa_celulas} Células de Fusão encontradas!"
            )
            jogador.celulas_fusao += recompensa_celulas
            self._concluido = True
        else:
            self.tentativas -= 1
            if self.tentativas <= 0:
                dano = 10 * jogador.nivel
                jogador.receber_dano(dano)
                resultado["penalidade"]["dano"] = dano
                resultado["narrativa"] = (
                    f"Senha incorreta! O terminal dispara um choque elétrico!\n"
                    f"Você perdeu {dano} de vida!"
                )
                resultado["concluido"] = True
                self._concluido = True
            else:
                resultado["narrativa"] = (
                    f"❌ Senha incorreta!\n"
                    f"  Tentativas restantes: {self.tentativas}"
                )

        return resultado


class DesafioArmadilha(Desafio):
    """
    Armadilha de plasma no chão — teste de Esquiva (D20 + Esquiva >= 15).
    Sucateiros têm bônus de +3 por instinto de sobrevivência.
    """

    def __init__(self, cenario: str = "corredor"):
        self.cenario = cenario

    def executar(self, jogador, resposta=None) -> dict:
        resultado = self._resultado_base(False)

        d20 = SistemaDados.rolar_d20()
        esquiva = jogador.esquiva

        # Bônus de vocação
        bonus = 0
        if jogador.vocacao.__class__.__name__ == "Sucateiro":
            bonus = 3
            resultado["narrativa"] = "Instinto de Sucateiro! +3 de Esquiva no teste.\n"

        total  = d20 + esquiva + bonus
        limite = 15

        if total >= limite:
            resultado["sucesso"]   = True
            resultado["narrativa"] += (
                f"Você esquivou da armadilha de plasma!\n"
                f"[d20={d20} + Esquiva={esquiva}{f' +{bonus}' if bonus else ''} = {total} ≥ {limite}]"
            )
        else:
            dano = 10 * jogador.nivel
            jogador.receber_dano(dano)
            resultado["penalidade"]["dano"] = dano
            resultado["narrativa"] += (
                f"Você ativou a armadilha! Pulso de plasma!\n"
                f"[{d20} + {esquiva}{f' +{bonus}' if bonus else ''} = {total} < {limite}]\n"
                f"Perdeu {dano} de vida!"
            )

        return resultado


class EnigmaNPC(Desafio):
    """
    Um NPC bloqueia a passagem e exige a resposta de uma charada.
    Requer digitação livre do jogador.
    Falhar não causa dano, mas bloqueia o caminho por 1 tentativa.
    """

    ENIGMAS = [
        {
            "npc":      "Velho Minerador",
            "contexto": "Ele bloqueia a ponte com uma espingarda enferrujada.",
            "charada":  "Tenho cidades, mas nenhuma casa; tenho montanhas, mas nenhuma árvore;\n"
                        "tenho água, mas nenhum peixe. O que sou eu?",
            "resposta": ["mapa", "um mapa"],
        },
        {
            "npc":      "Dróide Guardião",
            "contexto": "Seus olhos piscam vermelho enquanto analisa você.",
            "charada":  "Quanto mais você me tira, maior fico. O que sou eu?",
            "resposta": ["buraco", "um buraco", "vazio"],
        },
        {
            "npc":      "Fantasma de Sinal",
            "contexto": "Uma holograma distorcida de uma criança bloqueia a porta.",
            "charada":  "Falo sem boca e ouço sem ouvidos. Não tenho corpo, mas ganho vida com o vento.",
            "resposta": ["eco", "um eco"],
        },
    ]

    def __init__(self, indice: int = None):
        enigma = (
            self.ENIGMAS[indice % len(self.ENIGMAS)]
            if indice is not None
            else random.choice(self.ENIGMAS)
        )
        self._npc      = enigma["npc"]
        self._contexto = enigma["contexto"]
        self._charada  = enigma["charada"]
        self._respostas_aceitas = enigma["resposta"]
        self._resolvido = False

    @property
    def apresentacao(self) -> str:
        return (
            f"{self._npc}\n"
            f"\"{self._contexto}\"\n\n"
            f"\"{self._charada}\""
        )

    def executar(self, jogador, resposta=None) -> dict:
        resultado = self._resultado_base(False)

        if self._resolvido:
            resultado["narrativa"] = f"{self._npc} acena e deixa você passar."
            resultado["concluido"] = True
            return resultado

        if resposta is None:
            resultado["narrativa"] = self.apresentacao
            return resultado

        resposta_norm = resposta.strip().lower()
        acertou = any(r.lower() in resposta_norm for r in self._respostas_aceitas)

        if acertou:
            recompensa = 8
            jogador.celulas_fusao += recompensa
            resultado["sucesso"] = True
            resultado["concluido"] = True
            resultado["recompensa"]["celulas"] = recompensa
            resultado["narrativa"] = (
                f"{self._npc} sorri e abre o caminho.\n"
                f"\"Você é mais esperto do que parece, viajante.\"\n"
                f"+{recompensa} Células de Fusão!"
            )
            self._resolvido = True
        else:
            resultado["narrativa"] = (
                f"{self._npc} balança a cabeça.\n"
                f"\"Errado. Pense melhor.\"\n"
                f"\"Tente de novo.\""
            )

        return resultado


class DesafioRecurso(Desafio):
    """
    Cofre ou baú de recursos — teste de Poder para arrombar
    ou de Inteligência (usando Tecno-Sábio) para abrir sem dano.
    Ao abrir com sucesso, sorteia um item aleatório do pool de itens.
    """

    # Pool de itens embutido (fallback caso o JSON não seja encontrado)
    _POOL_FALLBACK = [
        {"tipo": "cura",      "nome": "Cantil Improvisado",    "descricao": "Água suja, mas funciona.", "cura": 20,      "raridade": "comum"},
        {"tipo": "cura",      "nome": "Gel Nanite",            "descricao": "Nanobots que fecham ferimentos.", "cura": 40, "raridade": "incomum"},
        {"tipo": "combate",   "nome": "Granada de Plasma",     "descricao": "Explode com calor intenso.", "dano_min": 15, "dano_max": 25, "efeito": "fogo",  "raridade": "incomum"},
        {"tipo": "combate",   "nome": "Spike EMP",             "descricao": "Desativa sistemas eletrônicos.", "dano_min": 10, "dano_max": 20, "efeito": "emp", "raridade": "raro"},
        {"tipo": "utilidade", "nome": "Óculos de Mira",        "descricao": "+2 de Poder temporário.", "buff_poder": 2, "raridade": "comum"},
        {"tipo": "utilidade", "nome": "Blindagem Improvisada", "descricao": "+3 de Defesa temporária.", "buff_defesa": 3, "raridade": "incomum"},
        {"tipo": "utilidade", "nome": "Stimpak de Adrenalina", "descricao": "+2 Poder, +2 Esquiva.", "buff_poder": 2, "buff_esquiva": 2, "raridade": "raro"},
    ]

    def __init__(self, tipo: str = "cofre", dificuldade: int = 1):
        self.tipo = tipo          # "cofre" ou "bau"
        self.dificuldade = dificuldade
        self._aberto = False
        self._pool = self._carregar_pool()

    @staticmethod
    def _carregar_pool() -> list:
        """Tenta carregar itens do JSON; usa fallback se não encontrar."""
        try:
            caminho = Path(__file__).parent.parent / "data" / "itens.json"
            with open(caminho, encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return DesafioRecurso._POOL_FALLBACK

    def _sortear_item(self, jogador) -> str:
        """Sorteia e entrega um item ao jogador. Retorna a narrativa."""

        # Baús de maior dificuldade dão itens melhores
        raridade_min = "raro" if self.dificuldade >= 3 else (
                        "incomum" if self.dificuldade == 2 else "comum")

        item = FabricaItens.item_aleatorio(self._pool, raridade_min)
        jogador.pegar_item(item)
        return f"  Você encontrou: [{item.raridade.upper()}] {item.nome} — {item.descricao}"

    def executar(self, jogador, resposta=None) -> dict:
        resultado = self._resultado_base(False)

        if self._aberto:
            resultado["narrativa"] = f"O {self.tipo} já está aberto."
            resultado["concluido"] = True
            return resultado

        limite = 10 + self.dificuldade * 2

        # Tecno-Sábio usa precisão (+5 bônus)
        bonus = 5 if jogador.vocacao.__class__.__name__ == "TecnoSabio" else 0
        d20   = SistemaDados.rolar_d20()
        total = d20 + jogador.poder + bonus

        if total >= limite:
            celulas   = 10 * self.dificuldade
            jogador.celulas_fusao += celulas
            narrativa_item = self._sortear_item(jogador)

            resultado["sucesso"]              = True
            resultado["concluido"]            = True
            resultado["recompensa"]["celulas"] = celulas
            resultado["narrativa"] = (
                f"Você abriu o {self.tipo}!\n"
                f"  [{d20} + Poder={jogador.poder}"
                f"{f' +{bonus} (Tecno-Sábio)' if bonus else ''} = {total} >= {limite}]\n"
                f"  +{celulas} Células de Fusão!\n"
                f"{narrativa_item}"
            )
            self._aberto = True
        else:
            dano = 5 * self.dificuldade
            jogador.receber_dano(dano)
            resultado["penalidade"]["dano"] = dano
            resultado["narrativa"] = (
                f"O {self.tipo} estava armadilhado!\n"
                f"  [{d20} + {jogador.poder}{f' +{bonus}' if bonus else ''} = {total} < {limite}]\n"
                f"  Você levou {dano} de dano na tentativa."
            )

        return resultado