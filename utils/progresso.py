import json
import os
from datetime import datetime
from pathlib import Path


class SistemaProgresso:
    """
    Responsável por salvar e carregar o estado do jogo em disco (JSON).
    Suporta múltiplos slots de save (1, 2, 3).
    """

    PASTA_SAVES = Path("saves")
    VERSAO = "1.0"

    @classmethod
    def _garantir_pasta(cls) -> None:
        cls.PASTA_SAVES.mkdir(exist_ok=True)

    @classmethod
    def _caminho(cls, slot: int) -> Path:
        return cls.PASTA_SAVES / f"save_slot{slot}.json"

    # ------------------------------------------------------------------ #
    #  Salvar
    # ------------------------------------------------------------------ #

    @classmethod
    def salvar(cls, jogador, slot: int = 1) -> bool:
        """
        Serializa o estado do jogador e grava em disco.
        Retorna True se salvou com sucesso.
        """
        cls._garantir_pasta()

        dados = {
            "versao":        cls.VERSAO,
            "data_save":     datetime.now().strftime("%d/%m/%Y %H:%M"),
            "nome":          jogador.nome,
            "raca":          jogador.raca.__class__.__name__,
            "vocacao":       jogador.vocacao.__class__.__name__,
            "nivel":         jogador.nivel,
            "xp":            jogador.xp,
            "poder":         jogador.poder,
            "defesa":        jogador.defesa,
            "vida_maxima":   jogador.vida_maxima,
            "vida_atual":    jogador.vida_atual,
            "esquiva":       jogador.esquiva,
            "celulas_fusao": jogador.celulas_fusao,
            "cenario_atual": jogador.cenario_atual,
            "inventario":    cls._serializar_inventario(jogador.inventario),
            "slot_salvo":    getattr(jogador, "slot_salvo", 1),
            "equipamentos":  cls._serializar_equipamentos(jogador.equipamentos),
        }

        try:
            with open(cls._caminho(slot), "w", encoding="utf-8") as f:
                json.dump(dados, f, ensure_ascii=False, indent=2)
            return True
        except OSError:
            return False

    @staticmethod
    def _serializar_equipamentos(equipamentos: dict) -> dict:
        """Serializa os itens equipados {slot: dados_item | None}."""
        resultado = {}
        for slot, item in equipamentos.items():
            if item is None:
                resultado[slot] = None
            else:
                base = {
                    "tipo":        "equipavel",
                    "nome":        item.nome,
                    "descricao":   item.descricao,
                    "slot":        item.slot,
                    "mod_poder":   item.mod_poder,
                    "mod_defesa":  item.mod_defesa,
                    "mod_esquiva": item.mod_esquiva,
                    "mod_vida_max":item.mod_vida_max,
                    "raridade":    item.raridade,
                }
                resultado[slot] = base
        return resultado

    @staticmethod
    def _serializar_inventario(inventario: list) -> list:
        resultado = []
        for item in inventario:
            base = {
                "tipo":       item.__class__.__name__,
                "nome":       item.nome,
                "descricao":  item.descricao,
                "consumivel": item.consumivel,
                "raridade":   item.raridade,
            }
            # Campos específicos por tipo
            if hasattr(item, "cura"):
                base["cura"] = item.cura
            if hasattr(item, "dano_min"):
                base["dano_min"] = item.dano_min
                base["dano_max"] = item.dano_max
                base["efeito"]   = item.efeito
            if hasattr(item, "buff_poder"):
                base["buff_poder"]   = item.buff_poder
                base["buff_defesa"]  = item.buff_defesa
                base["buff_esquiva"] = item.buff_esquiva
                base["buff_vida"]    = item.buff_vida
            if hasattr(item, "slot") and hasattr(item, "mod_poder"):
                base["tipo"]         = "equipavel"
                base["slot"]         = item.slot
                base["mod_poder"]    = item.mod_poder
                base["mod_defesa"]   = item.mod_defesa
                base["mod_esquiva"]  = item.mod_esquiva
                base["mod_vida_max"] = item.mod_vida_max
            resultado.append(base)
        return resultado

    # ------------------------------------------------------------------ #
    #  Carregar
    # ------------------------------------------------------------------ #

    @classmethod
    def carregar(cls, slot: int = 1):
        """
        Lê o save do slot e reconstrói o Jogador.
        Retorna o objeto Jogador ou None se não existir save.
        """
        caminho = cls._caminho(slot)
        if not caminho.exists():
            return None

        try:
            with open(caminho, encoding="utf-8") as f:
                dados = json.load(f)
        except (OSError, json.JSONDecodeError):
            return None

        return cls._reconstruir_jogador(dados)

    @classmethod
    def _reconstruir_jogador(cls, dados: dict):
        from criacao.raca    import Humano, Ciborgue, Androide
        from criacao.vocacao import Pistoleiro, TecnoSabio, Sucateiro
        from entidades.jogador import Jogador
        from itens.item import ItemCura, ItemCombate, ItemUtilidade, ItemEquipavel

        # Reconstrói raça e vocação pelos nomes salvos
        racas    = {"Humano": Humano, "Ciborgue": Ciborgue, "Androide": Androide}
        vocacoes = {"Pistoleiro": Pistoleiro, "TecnoSabio": TecnoSabio, "Sucateiro": Sucateiro}

        raca_cls    = racas.get(dados["raca"],    Humano)
        vocacao_cls = vocacoes.get(dados["vocacao"], Pistoleiro)

        jogador = Jogador(dados["nome"], raca_cls(), vocacao_cls())

        # Restaura atributos diretamente (sobrescreve os calculados no __init__)
        jogador.nivel = dados["nivel"]
        jogador.xp = dados["xp"]
        jogador.poder = dados["poder"]
        jogador.defesa = dados["defesa"]
        jogador.vida_maxima = dados["vida_maxima"]
        jogador.vida_atual = dados["vida_atual"]
        jogador.esquiva = dados["esquiva"]
        jogador.celulas_fusao = dados["celulas_fusao"]
        jogador.cenario_atual = dados["cenario_atual"]
        jogador.slot_salvo    = dados.get("slot_salvo", 1)

        # Reconstrói inventário
        for item_dados in dados.get("inventario", []):
            tipo = item_dados["tipo"]
            if tipo == "ItemCura":
                item = ItemCura(item_dados["nome"], item_dados["descricao"],
                                item_dados["cura"], item_dados["raridade"])
            elif tipo == "ItemCombate":
                item = ItemCombate(item_dados["nome"], item_dados["descricao"],
                                   item_dados["dano_min"], item_dados["dano_max"],
                                   item_dados.get("efeito"), item_dados["raridade"])
            elif tipo == "ItemUtilidade":
                item = ItemUtilidade(item_dados["nome"], item_dados["descricao"],
                                     item_dados.get("buff_poder", 0),
                                     item_dados.get("buff_defesa", 0),
                                     item_dados.get("buff_esquiva", 0),
                                     item_dados.get("buff_vida", 0),
                                     item_dados["raridade"])
            elif tipo == "ItemEquipavel" or tipo == "equipavel":
                item = ItemEquipavel(
                    nome         = item_dados["nome"],
                    descricao    = item_dados["descricao"],
                    slot         = item_dados["slot"],
                    mod_poder    = item_dados.get("mod_poder",    0),
                    mod_defesa   = item_dados.get("mod_defesa",   0),
                    mod_esquiva  = item_dados.get("mod_esquiva",  0),
                    mod_vida_max = item_dados.get("mod_vida_max", 0),
                    raridade     = item_dados.get("raridade", "comum"),
                )
            else:
                continue
            jogador.inventario.append(item)

        # Reconstrói equipamentos (mods já estão nos atributos salvos — não reaplicar)
        for slot, dados_eq in dados.get("equipamentos", {}).items():
            if dados_eq is None:
                continue
            item_eq = ItemEquipavel(
                nome         = dados_eq["nome"],
                descricao    = dados_eq["descricao"],
                slot         = dados_eq["slot"],
                mod_poder    = dados_eq.get("mod_poder",    0),
                mod_defesa   = dados_eq.get("mod_defesa",   0),
                mod_esquiva  = dados_eq.get("mod_esquiva",  0),
                mod_vida_max = dados_eq.get("mod_vida_max", 0),
                raridade     = dados_eq.get("raridade", "comum"),
            )
            # Marca como equipado SEM reaplicar mods (atributos já foram restaurados)
            item_eq._equipado = True
            jogador.equipamentos[slot] = item_eq
            # Se o item não está no inventário ainda, adiciona
            nomes_inv = {i.nome for i in jogador.inventario}
            if item_eq.nome not in nomes_inv:
                jogador.inventario.append(item_eq)
            else:
                # Substitui a referência no inventário pela instância com _equipado=True
                for i, inv_item in enumerate(jogador.inventario):
                    if inv_item.nome == item_eq.nome:
                        jogador.inventario[i] = item_eq
                        break

        return jogador

    # ------------------------------------------------------------------ #
    #  Utilitários de slot
    # ------------------------------------------------------------------ #

    @classmethod
    def listar_saves(cls) -> list[dict]:
        """
        Retorna lista com info de todos os slots (1-3).
        Slots vazios retornam {"slot": N, "vazio": True}.
        """
        cls._garantir_pasta()
        resultado = []
        for slot in range(1, 4):
            caminho = cls._caminho(slot)
            if caminho.exists():
                try:
                    with open(caminho, encoding="utf-8") as f:
                        dados = json.load(f)
                    resultado.append({
                        "slot":       slot,
                        "vazio":      False,
                        "nome":       dados.get("nome", "?"),
                        "raca":       dados.get("raca", "?"),
                        "vocacao":    dados.get("vocacao", "?"),
                        "nivel":      dados.get("nivel", 1),
                        "cenario":    dados.get("cenario_atual", 0),
                        "data_save":  dados.get("data_save", ""),
                        "vida":       f"{dados.get('vida_atual',0)}/{dados.get('vida_maxima',0)}",
                    })
                except (OSError, json.JSONDecodeError):
                    resultado.append({"slot": slot, "vazio": True})
            else:
                resultado.append({"slot": slot, "vazio": True})
        return resultado

    @classmethod
    def deletar(cls, slot: int) -> bool:
        """Remove o save do slot. Retorna True se deletou com sucesso."""
        caminho = cls._caminho(slot)
        if caminho.exists():
            try:
                os.remove(caminho)
                return True
            except OSError:
                return False
        return False

    @classmethod
    def existe(cls, slot: int) -> bool:
        return cls._caminho(slot).exists()