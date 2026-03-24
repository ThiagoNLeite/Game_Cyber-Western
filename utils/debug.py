"""
utils/debug.py — Ferramentas de balanceamento e debug para Deserto de Silício.

Funcionalidades:
  - Simulação de combates sem I/O (calibrar dano/XP)
  - Logging estruturado via módulo logging
  - Relatório de balanceamento completo

Uso direto:
  python -m utils.debug            # relatório completo
  python -m utils.debug sim        # simula todos os inimigos vs jogador padrão
  python -m utils.debug cenario 1  # simula o cenário 1 N vezes
"""

from __future__ import annotations

import json
import logging
import random
import sys
from pathlib import Path
from typing import Any

# ================================================================== #
#  Configuração de logging
# ================================================================== #

_LOG_FORMAT = "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s"
_DATA_DIR   = Path(__file__).parent.parent / "data"
_LOG_FILE   = Path(__file__).parent.parent / "debug.log"


def configurar_logging(nivel: str = "INFO",
                       arquivo: bool = True) -> logging.Logger:
    """
    Configura o sistema de logging.
    nivel: "DEBUG" | "INFO" | "WARNING" | "ERROR"
    arquivo: se True, grava também em debug.log
    """
    nivel_num = getattr(logging, nivel.upper(), logging.INFO)

    handlers: list[logging.Handler] = [
        logging.StreamHandler(sys.stdout),
    ]
    if arquivo:
        handlers.append(
            logging.FileHandler(_LOG_FILE, encoding="utf-8")
        )

    logging.basicConfig(
        level   = nivel_num,
        format  = _LOG_FORMAT,
        handlers= handlers,
        force   = True,
    )
    return logging.getLogger("deserto_silicio")


logger = configurar_logging()


# ================================================================== #
#  Carrega dados de referência
# ================================================================== #

def _carregar(nome: str) -> list:
    try:
        with open(_DATA_DIR / nome, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error("Falha ao carregar %s: %s", nome, e)
        return []


# ================================================================== #
#  Simulação de combate (sem I/O)
# ================================================================== #

def simular_combate(config_jogador: dict[str, Any],
                    config_inimigo: dict[str, Any],
                    n: int = 500,
                    seed: int | None = None) -> dict[str, Any]:
    """
    Simula N combates entre jogador e inimigo sem nenhuma saída de tela.

    Parâmetros
    ----------
    config_jogador : dict com chaves poder, defesa, vida, esquiva, nivel
    config_inimigo : dict com os campos do inimigos.json (id, poder, defesa, etc.)
    n              : número de simulações
    seed           : semente para reproduzir resultados

    Retorna
    -------
    dict com: vitorias, derrotas, taxa_vitoria, media_turnos,
              dano_recebido_medio, xp_medio_por_vitoria
    """
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).parent.parent))

    from criacao.raca    import Humano
    from criacao.vocacao import Pistoleiro
    from entidades.jogador import Jogador
    from entidades.monstro import Monstro
    from mecanicas.combate import SistemaCombate

    if seed is not None:
        random.seed(seed)

    logger.debug("Iniciando simulação: %s vs %s (%d combates)",
                 config_jogador.get("nome", "Jogador"),
                 config_inimigo.get("nome", "Inimigo"), n)

    vitorias       = 0
    derrotas       = 0
    total_turnos   = 0
    total_dano_rec = 0
    total_xp       = 0
    LIMITE_TURNOS  = 60   # evita loop infinito em combates empatados

    for _ in range(n):
        # Cria jogador do zero com os atributos passados
        j = Jogador(config_jogador.get("nome", "Sim"),
                    Humano(), Pistoleiro())
        j.poder      = config_jogador.get("poder",   10)
        j.defesa     = config_jogador.get("defesa",   5)
        j.vida_maxima = config_jogador.get("vida",    60)
        j.vida_atual  = j.vida_maxima
        j.esquiva    = config_jogador.get("esquiva",  5)
        j.nivel      = config_jogador.get("nivel",    1)

        nivel_sim = config_jogador.get("nivel", 1)
        inimigo   = Monstro.escalar(config_inimigo, nivel_sim)
        combate   = SistemaCombate(j, inimigo)

        vida_inicial = j.vida_maxima
        turno = 0
        fim   = False

        while not fim and turno < LIMITE_TURNOS:
            turno += 1
            resultado = combate.executar_turno("atacar")
            if resultado["fim_combate"]:
                fim = True
                if resultado.get("vitoria"):
                    vitorias     += 1
                    total_xp     += resultado.get("xp_ganho", 0)
                else:
                    derrotas     += 1

        total_turnos   += turno
        total_dano_rec += max(0, vida_inicial - j.vida_atual)

    taxa = vitorias / n * 100
    logger.info("Resultado %s vs %s: %.1f%% vitórias (%d/%d)",
                config_jogador.get("nome", "Jogador"),
                config_inimigo.get("nome", "Inimigo"),
                taxa, vitorias, n)

    return {
        "inimigo":              config_inimigo.get("nome", "?"),
        "total_simulacoes":     n,
        "vitorias":             vitorias,
        "derrotas":             derrotas,
        "taxa_vitoria":         f"{taxa:.1f}%",
        "media_turnos":         f"{total_turnos / n:.1f}",
        "dano_recebido_medio":  f"{total_dano_rec / n:.1f}",
        "xp_medio_vitoria":     f"{total_xp / max(vitorias, 1):.0f}",
    }


# ================================================================== #
#  Relatório de balanceamento completo
# ================================================================== #

def relatorio_balanceamento(n: int = 300) -> None:
    """
    Gera um relatório completo de balanceamento para todos os inimigos,
    testando contra um jogador padrão do nível correspondente ao cenário.
    """
    inimigos = _carregar("inimigos.json")
    if not inimigos:
        logger.error("inimigos.json não encontrado. Rode de dentro do projeto.")
        return

    # Jogadores de referência por nível (escalam com o cenário)
    jogadores_ref = {
        1: {"nome": "Ref_Nv1",  "poder": 12, "defesa": 7,  "vida": 65,  "esquiva": 7,  "nivel": 1},
        2: {"nome": "Ref_Nv2",  "poder": 16, "defesa": 9,  "vida": 82,  "esquiva": 8,  "nivel": 2},
        3: {"nome": "Ref_Nv3",  "poder": 20, "defesa": 11, "vida": 98,  "esquiva": 9,  "nivel": 3},
        4: {"nome": "Ref_Nv4",  "poder": 24, "defesa": 13, "vida": 115, "esquiva": 10, "nivel": 4},
        5: {"nome": "Ref_Nv5",  "poder": 28, "defesa": 15, "vida": 132, "esquiva": 11, "nivel": 5},
    }

    print("\n" + "=" * 72)
    print("  RELATÓRIO DE BALANCEAMENTO — Deserto de Silício")
    print("=" * 72)
    print(f"  {'Inimigo':<35} {'Cenário':<8} {'%Vitória':<10} {'Turnos':<8} {'Dano Rec':<10}")
    print("-" * 72)

    total_ok = 0
    alertas  = []

    for ini in inimigos:
        cenarios_ini = ini.get("cenarios", [1])
        nivel_ref    = min(max(cenarios_ini), 5)
        jog          = jogadores_ref[nivel_ref]

        resultado = simular_combate(jog, ini, n=n, seed=42)

        taxa_num = float(resultado["taxa_vitoria"].strip("%"))
        status   = "✓" if 50 <= taxa_num <= 95 else "⚠"

        if taxa_num < 50:
            alertas.append(f"  ⚠ {ini['nome']}: taxa de vitória muito baixa ({taxa_num:.0f}%) — inimigo pode ser OP")
        elif taxa_num > 95:
            alertas.append(f"  ⚠ {ini['nome']}: taxa de vitória muito alta ({taxa_num:.0f}%) — inimigo muito fraco")
        else:
            total_ok += 1

        print(f"  {status} {ini['nome']:<33} {str(cenarios_ini):<8} "
              f"{resultado['taxa_vitoria']:<10} "
              f"{resultado['media_turnos']:<8} "
              f"{resultado['dano_recebido_medio']}")

    print("=" * 72)
    print(f"  Inimigos bem balanceados: {total_ok}/{len(inimigos)}")
    if alertas:
        print("\n  Alertas:")
        for a in alertas:
            print(a)
    print()

    logger.info("Relatório concluído: %d/%d inimigos balanceados", total_ok, len(inimigos))


def simular_cenario(id_cenario: int, config_jogador: dict,
                    n: int = 200) -> dict[str, Any]:
    """
    Simula todos os combates de um cenário e calcula a taxa de sobrevivência.
    Útil para calibrar a dificuldade de sequências de combate.
    """
    cenarios = _carregar("cenario.json")
    inimigos_json = _carregar("inimigos.json")
    inimigos_map  = {i["id"]: i for i in inimigos_json}

    cenario = next((c for c in cenarios if c["id"] == id_cenario), None)
    if not cenario:
        logger.error("Cenário %d não encontrado", id_cenario)
        return {}

    ids = ([cenario.get("inimigo_entrada")] if cenario.get("inimigo_entrada") else [])
    ids += cenario.get("inimigos", [])[:2]   # entrada + 2 aleatórios

    logger.info("Simulando cenário %d: %s (%d combates por sequência, %d sequências)",
                id_cenario, cenario["nome"], len(ids), n)

    sobreviventes = 0
    xp_total      = 0

    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).parent.parent))
    from criacao.raca    import Humano
    from criacao.vocacao import Pistoleiro
    from entidades.jogador import Jogador
    from entidades.monstro import Monstro
    from mecanicas.combate import SistemaCombate

    for _ in range(n):
        j = Jogador(config_jogador.get("nome", "Sim"), Humano(), Pistoleiro())
        j.poder       = config_jogador.get("poder",  10)
        j.defesa      = config_jogador.get("defesa",  5)
        j.vida_maxima = config_jogador.get("vida",   60)
        j.vida_atual  = j.vida_maxima
        j.esquiva     = config_jogador.get("esquiva", 5)
        j.nivel       = config_jogador.get("nivel",   1)

        vivo = True
        xp_seq = 0
        for iid in ids:
            if not iid or iid not in inimigos_map:
                continue
            inimigo = Monstro.escalar(inimigos_map[iid], j.nivel)
            combate = SistemaCombate(j, inimigo)
            for _ in range(60):
                res = combate.executar_turno("atacar")
                if res["fim_combate"]:
                    if res.get("vitoria"):
                        xp_seq += res.get("xp_ganho", 0)
                    else:
                        vivo = False
                    break
            if not vivo:
                break

        if vivo:
            sobreviventes += 1
            xp_total      += xp_seq

    taxa_surv = sobreviventes / n * 100
    logger.info("Cenário %d — sobrevivência: %.1f%%", id_cenario, taxa_surv)

    return {
        "cenario":              cenario["nome"],
        "combates_simulados":   len(ids),
        "sequencias":           n,
        "sobreviventes":        sobreviventes,
        "taxa_sobrevivencia":   f"{taxa_surv:.1f}%",
        "xp_medio_sobrevivente":f"{xp_total / max(sobreviventes, 1):.0f}",
    }


# ================================================================== #
#  Entry point CLI
# ================================================================== #

if __name__ == "__main__":
    args = sys.argv[1:]

    if not args or args[0] == "relatorio":
        relatorio_balanceamento(n=300)

    elif args[0] == "sim":
        # Simula todos os inimigos vs jogador nível 3 padrão
        inimigos = _carregar("inimigos.json")
        jog_ref  = {"nome": "Debug", "poder": 20, "defesa": 11,
                    "vida": 98, "esquiva": 9, "nivel": 3}
        for ini in inimigos:
            r = simular_combate(jog_ref, ini, n=200, seed=42)
            print(f"  {r['inimigo']:<35} {r['taxa_vitoria']:<10} "
                  f"turnos={r['media_turnos']}  dano={r['dano_recebido_medio']}")

    elif args[0] == "cenario" and len(args) >= 2:
        try:
            cid = int(args[1])
        except ValueError:
            print("Uso: python -m utils.debug cenario <numero>")
            sys.exit(1)
        jog = {"nome": "Debug", "poder": 15 + cid*4, "defesa": 8 + cid*2,
               "vida": 65 + cid*15, "esquiva": 7 + cid, "nivel": cid}
        r = simular_cenario(cid, jog, n=300)
        print(f"\nCenário {cid} — {r.get('cenario', '?')}")
        for k, v in r.items():
            if k != "cenario":
                print(f"  {k}: {v}")

    else:
        print("Uso:")
        print("  python -m utils.debug                # relatório completo")
        print("  python -m utils.debug sim            # simula todos inimigos")
        print("  python -m utils.debug cenario <N>    # simula cenário N")