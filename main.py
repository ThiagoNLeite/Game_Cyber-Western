"""
Deserto de Silício — RPG Cyber-Western
Ponto de entrada principal do jogo.

Fluxo por cenário:
  1. Narração de entrada
  2. Combate com inimigo fixo da entrada (inimigo_entrada)
  3. Loop de exploração:
       - O jogador escolhe [Explorar] ou [Avançar]
       - Explorar sorteia um evento (nada / cofre / terminal / armadilha)
       - Combates aleatórios podem ocorrer durante a exploração
       - [Avançar] só fica disponível após o mínimo de explorações
  4. Guardião de passagem (se houver): enigma ou pagamento
  5. Boss (cenário 6 apenas)
  6. Narração de saída → próximo cenário
"""

import sys
import json
import random
from pathlib import Path

from interface.gerenciador_tela import GerenciadorTela
from entidades.jogador          import Jogador
from entidades.monstro          import Monstro, Boss
from mecanicas.combate          import SistemaCombate
from mecanicas.desafios         import (DesafioTerminal, DesafioArmadilha,
                                        EnigmaNPC, DesafioRecurso)
from utils.progresso            import SistemaProgresso


# ================================================================== #
#  Carrega JSONs de dados
# ================================================================== #

def _carregar_json(nome: str) -> list:
    """
    Carrega JSON da pasta /data relativa a este arquivo.
    Usa __file__ para funcionar independente do diretório de execução.
    """
    caminho = Path(__file__).parent / "data" / nome
    try:
        with open(caminho, encoding="utf-8") as f:
            dados = json.load(f)
        print(f"[OK] {nome} ({len(dados)} registros)")
        return dados
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[ERRO] {nome}: {e}")
        print(f"[ERRO] Caminho: {caminho.resolve()}")
        return []


CENARIOS = _carregar_json("cenario.json")
INIMIGOS = {i["id"]: i for i in _carregar_json("inimigos.json")}


def _validar_dados() -> None:
    if not CENARIOS:
        print("[CRITICO] cenario.json vazio — vitória imediata ao iniciar!")
    if not INIMIGOS:
        print("[CRITICO] inimigos.json vazio — combates sem inimigos!")

_validar_dados()


# ================================================================== #
#  Utilitários internos
# ================================================================== #

def _inimigo_por_id(inimigo_id: str, nivel: int) -> Monstro | None:
    """Cria um Monstro escalado pelo nível a partir do dicionário JSON."""
    dados = INIMIGOS.get(inimigo_id)
    if not dados:
        print(f"[AVISO] Inimigo '{inimigo_id}' não encontrado em inimigos.json")
        return None
    return Monstro.escalar(dados, nivel)


def _narrativa_encontro(inimigo_id: str) -> str:
    """Retorna a narrativa de encontro do inimigo, ou texto genérico."""
    dados = INIMIGOS.get(inimigo_id, {})
    return dados.get(
        "narrativa_encontro",
        f"Um inimigo surge do nada bloqueando seu caminho."
    )


# ================================================================== #
#  Loop de combate
# ================================================================== #

def loop_combate(tela: GerenciadorTela, jogador: Jogador, inimigo,
                 is_boss: bool = False) -> str | bool:
    """
    Executa um combate completo turno a turno.
    Retorna:
      True       — vitória ou fuga de combate normal
      False      — jogador morreu
      "fuga_boss" — jogador fugiu do boss (tratado como derrota especial)
    """
    combate = SistemaCombate(jogador, inimigo)

    while True:
        estado   = combate.estado_combate()
        tem_hab  = jogador.vocacao.tem_uso_disponivel()
        nome_hab = jogador.vocacao.nome_habilidade

        acao = tela.tela_combate(
            estado, combate.log, nome_hab, tem_hab, jogador.inventario
        )

        # "item_NomeDoItem" → separa ação e nome
        nome_item = None
        if acao.startswith("item_"):
            nome_item = acao[5:]
            acao = "item"

        resultado = combate.executar_turno(acao, nome_item)

        # Mostra narrativa do item usado
        if acao == "item":
            msg_item = resultado.get("acao_jogador", {}).get("narrativa", "")
            if msg_item:
                tela.tela_resultado("Item Usado!", msg_item, cor_titulo=(100, 230, 120))

        # Mensagem de transição de fase do boss
        fase_nova = resultado.get("acao_inimigo", {}).get("mudou_fase")
        if fase_nova:
            tela.tela_resultado(
                f"Boss — Fase {fase_nova}!",
                resultado["acao_inimigo"].get("narrativa", ""),
                cor_titulo=(255, 200, 0),
            )

        if resultado["fim_combate"]:
            if resultado["fuga"]:
                if is_boss:
                    # Fugir do boss = fim de covarde
                    return "fuga_boss"
                tela.tela_resultado("Fuga!",
                                    "Voce escapou para lutar outro dia.")
                return True
            if resultado["vitoria"]:
                xp    = resultado.get("xp_ganho", 0)
                subiu = resultado.get("subiu_nivel", False)
                msg   = f"+{xp} XP"
                if subiu:
                    msg += f"\nNivel {jogador.nivel}! Seus atributos aumentaram!"
                tela.tela_resultado("Vitoria!", msg)
                return True
            # Jogador morreu
            return False


# ================================================================== #
#  Loop de desafio (terminal ou armadilha)
# ================================================================== #

def loop_desafio(tela: GerenciadorTela, jogador: Jogador,
                 desafio) -> None:
    """
    Executa um desafio já instanciado (DesafioTerminal ou DesafioArmadilha).
    Gerencia tentativas e exibe os resultados.
    """
    pede_input = isinstance(desafio, DesafioTerminal)

    # Primeira chamada sem resposta — obtém enunciado
    resultado = desafio.executar(jogador, resposta=None)
    narrativa = resultado["narrativa"]

    # Armadilha se resolve na primeira chamada (sem input)
    if resultado["concluido"]:
        tela.tela_resultado("Evento", narrativa)
        return

    # Terminal — loop de tentativas
    while not resultado["concluido"]:
        resposta = tela.tela_desafio(narrativa, pede_input=pede_input)
        if resposta == "pular":
            break
        resultado = desafio.executar(jogador, resposta=resposta)
        narrativa = resultado["narrativa"]

    # Concede XP se o desafio foi concluído com sucesso
    if resultado.get("sucesso"):
        xp_desafio = 25
        subiu = jogador.ganhar_xp(xp_desafio)
        msg_xp = f"+{xp_desafio} XP pelo desafio!"
        if subiu:
            msg_xp += f"\nNivel {jogador.nivel}! Seus atributos aumentaram!"
        tela.tela_resultado("Resultado", narrativa + "\n\n" + msg_xp)
    else:
        tela.tela_resultado("Resultado", narrativa)


# ================================================================== #
#  Loop de exploração
# ================================================================== #

def loop_exploracao(tela: GerenciadorTela, jogador: Jogador,
                    dados_cenario: dict) -> str:
    """
    Gerencia o loop de exploração livre dentro de um cenário.

    O jogador escolhe [Explorar] ou [Avançar] repetidamente.
    Cada exploração consome um slot e sorteia um evento do JSON.
    [Avançar] só fica disponível após `exploracoes_minimas`.

    Retorna:
      "continuar" — jogador avançou normalmente
      "game_over" — jogador morreu durante uma exploração
      "menu"      — jogador saiu para o menu
    """
    nome      = dados_cenario["nome"]
    subtitulo = dados_cenario["subtitulo"]
    minimo    = dados_cenario.get("exploracoes_minimas", 0)
    maximo    = dados_cenario.get("exploracoes_disponiveis", 3)
    eventos   = dados_cenario.get("eventos_exploracao", [])

    # Rastreia quantas explorações já aconteceram nesta sessão
    exploracoes_feitas = 0

    # Pool de eventos embaralhado para não repetir na mesma ordem sempre
    pool_eventos = eventos.copy()
    random.shuffle(pool_eventos)
    idx_evento = 0   # ponteiro no pool embaralhado

    # Inimigos disponíveis para combates aleatórios durante exploração
    ids_inimigos_area = dados_cenario.get("inimigos", [])

    while True:
        saida_disponivel = exploracoes_feitas >= minimo

        # Monta descrição da situação atual para exibir no painel
        descricao = _descricao_situacao(nome, exploracoes_feitas,
                                        minimo, saida_disponivel)

        acao = tela.tela_exploracao(
            nome_cenario            = nome,
            subtitulo               = subtitulo,
            descricao_situacao      = descricao,
            jogador                 = jogador,
            exploracoes_feitas      = exploracoes_feitas,
            exploracoes_minimas     = minimo,
            exploracoes_disponiveis = maximo,
        )

        if acao == "sair":
            return "menu"

        if acao == "inventario":
            tela.tela_inventario(jogador)
            continue

        if acao == "avancar":
            # Só chega aqui se saida_disponivel == True (a tela bloqueia)
            return "continuar"

        # acao == "explorar"
        if exploracoes_feitas >= maximo:
            # Não deveria acontecer (botão desabilitado), mas por segurança
            continue

        exploracoes_feitas += 1

        # --- Sorteia evento ---
        if not pool_eventos:
            # Pool esgotado antes do máximo — só nada
            tela.tela_resultado("Exploracao",
                                "Voce ja vasculhou tudo por aqui. Nao ha mais nada.")
            continue

        evento = pool_eventos[idx_evento % len(pool_eventos)]
        idx_evento += 1

        resultado = _executar_evento_exploracao(tela, jogador, evento,
                                                 ids_inimigos_area)
        if resultado == "game_over":
            return "game_over"
        if resultado == "menu":
            return "menu"
        # resultado == "ok" → continua o loop


def _descricao_situacao(nome_cenario: str, feitas: int,
                        minimo: int, saida_disponivel: bool) -> str:
    """Texto narrativo dinâmico exibido no painel de exploração."""
    if saida_disponivel and minimo > 0:
        return (f"Voce conhece bem o suficiente este lugar para encontrar "
                f"o caminho de saida. Pode avançar quando quiser — "
                f"ou continuar explorando em busca de recursos.")
    elif saida_disponivel and minimo == 0:
        return ("Voce acabou de chegar. Pode avançar diretamente ou "
                "explorar a area em busca de recursos e informacoes.")
    else:
        faltam = minimo - feitas
        return (f"Voce ainda nao encontrou o caminho de saida de {nome_cenario}. "
                f"Continue explorando — faltam pelo menos {faltam} exploracoes "
                f"para orientar sua rota.")


def _executar_evento_exploracao(tela: GerenciadorTela, jogador: Jogador,
                                 evento: dict,
                                 ids_inimigos_area: list) -> str:
    """
    Executa um único evento de exploração.

    Tipos de evento: "nada" | "cofre" | "terminal" | "armadilha"
    Cada um pode ter um combate aleatório associado (30% de chance).

    Retorna "ok" | "game_over" | "menu".
    """
    tipo = evento.get("tipo", "nada")

    # --- Exibe narrativa de contexto (antes do evento) ---
    narrativa_antes = evento.get("narrativa_antes") or evento.get("narrativa", "")
    if narrativa_antes:
        tela.tela_resultado("Exploracao", narrativa_antes)

    # --- Resolve o evento propriamente ---
    if tipo == "nada":
        # Evento "nada" já exibiu a narrativa acima, nada mais a fazer
        pass

    elif tipo == "cofre":
        dificuldade   = evento.get("dificuldade", 1)
        MAX_TENTATIVAS = 3

        # Pergunta se o jogador quer tentar abrir
        # (narrativa_antes já foi exibida acima como contexto)
        escolha_cofre = tela.tela_desafio(
            "Voce encontrou algo trancado. Quer tentar arrombar?\n\n"
            "[Tecno-Sabio tem vantagem neste teste.]",
            pede_input=False,
        )
        if escolha_cofre != "pular":
            tentativa_num = 0
            aberto        = False

            while tentativa_num < MAX_TENTATIVAS and not aberto:
                tentativa_num += 1
                desafio  = DesafioRecurso(tipo="cofre", dificuldade=dificuldade)
                resultado = desafio.executar(jogador)
                aberto   = resultado["sucesso"]

                if aberto:
                    xp_cofre = 20
                    subiu_cofre = jogador.ganhar_xp(xp_cofre)
                    msg_cofre = resultado["narrativa"] + f"\n\n+{xp_cofre} XP pelo arrombamento!"
                    if subiu_cofre:
                        msg_cofre += f"\nNivel {jogador.nivel}! Seus atributos aumentaram!"
                    tela.tela_resultado("Cofre Aberto!", msg_cofre)
                else:
                    if tentativa_num < MAX_TENTATIVAS:
                        # Falhou mas ainda tem tentativas
                        msg_tent = (resultado["narrativa"] +
                                    f"\n\nTentativa {tentativa_num}/{MAX_TENTATIVAS} falhou."
                                    f" Tentar de novo?")
                        nova_escolha = tela.tela_desafio(msg_tent, pede_input=False)
                        if nova_escolha == "pular":
                            tela.tela_resultado("Cofre", "Voce desistiu de abrir o cofre.")
                            break
                    else:
                        # Esgotou as tentativas
                        tela.tela_resultado(
                            "Cofre",
                            resultado["narrativa"] +
                            "\n\nVoce esgotou suas tentativas e abandona o cofre."
                        )

    elif tipo == "terminal":
        dificuldade = evento.get("dificuldade", 1)
        desafio     = DesafioTerminal(dificuldade=dificuldade)
        loop_desafio(tela, jogador, desafio)

    elif tipo == "armadilha":
        # Mostra escolha ANTES de rolar os dados
        # [Arriscar] executa o teste; [Achar outro caminho] pula sem penalidade
        escolha = tela.tela_desafio(
            "Voce identifica o perigo a tempo. O que fazer?",
            pede_input=False,
        )
        if escolha != "pular":
            desafio  = DesafioArmadilha()
            resultado_arm = desafio.executar(jogador)
            tela.tela_resultado("Resultado", resultado_arm["narrativa"])

    # Verifica se o jogador sobreviveu ao evento
    if not jogador.esta_vivo:
        return "game_over"

    # --- Chance de combate aleatório (30%) durante exploração ---
    if ids_inimigos_area and random.random() < 0.30:
        inimigo_id = random.choice(ids_inimigos_area)
        inimigo    = _inimigo_por_id(inimigo_id, jogador.nivel)
        if inimigo:
            tela.tela_narracao(
                titulo    = "Encontro!",
                subtitulo = inimigo.nome,
                narrativa = _narrativa_encontro(inimigo_id),
                jogador   = jogador,
            )
            vivo = loop_combate(tela, jogador, inimigo)
            if not vivo:
                return "game_over"

    return "ok"


# ================================================================== #
#  Loop de guardião
# ================================================================== #

def loop_guardiao(tela: GerenciadorTela, jogador: Jogador,
                  cfg_guardiao: dict) -> str:
    """
    Gerencia a interação com o NPC que bloqueia a saída do cenário.

    O jogador pode:
      - Resolver o enigma (EnigmaNPC)
      - Pagar o custo (células, vida ou item)
      - Voltar à exploração (e tentar de novo mais tarde)

    Retorna:
      "passou"    — guardião vencido/convencido, pode prosseguir
      "voltou"    — jogador escolheu voltar
      "game_over" — jogador morreu (custo de vida zerou HP)
      "menu"      — jogador foi ao menu
    """
    enigma_indice = cfg_guardiao["enigma_indice"]
    custo_tipo    = cfg_guardiao["custo_tipo"]
    custo_valor   = cfg_guardiao["custo_valor"]
    narrativa_npc = cfg_guardiao["narrativa_guardiao"]
    narrativa_pag = cfg_guardiao.get("narrativa_custo", "Voce paga o preco e passa.")

    enigma = EnigmaNPC(indice=enigma_indice)

    while True:
        # Verifica se o jogador tem recursos para pagar
        pode_pagar = _pode_pagar_guardiao(jogador, custo_tipo, custo_valor)

        acao = tela.tela_guardiao(
            narrativa_guardiao = narrativa_npc,
            custo_tipo         = custo_tipo,
            custo_valor        = custo_valor,
            jogador            = jogador,
        )

        # --- Jogador quer voltar ---
        if acao == "voltar":
            return "voltou"

        # --- Jogador quer pagar ---
        if acao == "pagar" or acao.startswith("pagar_"):
            if not pode_pagar:
                tela.tela_resultado(
                    "Sem recursos",
                    "Voce nao tem o necessario para pagar a passagem."
                )
                continue

            nome_item_entregue = None
            if acao.startswith("pagar_"):
                # "pagar_NomeDoItem" — custo_tipo == "item"
                nome_item_entregue = acao[6:]

            sucesso = _cobrar_guardiao(jogador, custo_tipo, custo_valor,
                                       nome_item_entregue)
            if not sucesso:
                tela.tela_resultado("Erro", "Nao foi possivel processar o pagamento.")
                continue

            tela.tela_resultado("Passagem Liberada", narrativa_pag)

            if not jogador.esta_vivo:
                return "game_over"

            return "passou"

        # --- Jogador quer resolver o enigma ---
        if acao == "resolver":
            resultado_enigma = _loop_enigma_guardiao(tela, jogador, enigma,
                                                      cfg_guardiao)
            if resultado_enigma == "passou":
                return "passou"
            if resultado_enigma == "game_over":
                return "game_over"
            # "falhou" → volta ao menu do guardião para nova tentativa
            narrativa_npc = (
                cfg_guardiao["narrativa_guardiao"] +
                "\n\n[Resposta errada. Tente novamente ou pague para passar.]"
            )
            continue


def _pode_pagar_guardiao(jogador: Jogador, custo_tipo: str,
                          custo_valor) -> bool:
    """Verifica se o jogador tem recursos suficientes para o custo."""
    if custo_tipo == "celulas":
        return jogador.celulas_fusao >= custo_valor
    elif custo_tipo == "vida":
        custo_real = max(1, int(jogador.vida_atual * custo_valor / 100))
        return jogador.vida_atual > custo_real   # não deixa morrer pagando
    elif custo_tipo == "item":
        return len(jogador.inventario) > 0
    return False


def _cobrar_guardiao(jogador: Jogador, custo_tipo: str,
                      custo_valor, nome_item: str = None) -> bool:
    """
    Aplica o custo de passagem no jogador.
    Retorna True se cobrou com sucesso, False caso contrário.
    """
    if custo_tipo == "celulas":
        if jogador.celulas_fusao < custo_valor:
            return False
        jogador.celulas_fusao -= custo_valor
        return True

    elif custo_tipo == "vida":
        custo_real = max(1, int(jogador.vida_atual * custo_valor / 100))
        if jogador.vida_atual <= custo_real:
            return False
        jogador.receber_dano(custo_real)
        return True

    elif custo_tipo == "item":
        if not jogador.inventario:
            return False
        # Se veio nome específico, remove aquele; caso contrário remove o primeiro
        if nome_item:
            for item in jogador.inventario:
                if item.nome == nome_item:
                    jogador.inventario.remove(item)
                    return True
            return False
        else:
            jogador.inventario.pop(0)
            return True

    return False


def _loop_enigma_guardiao(tela: GerenciadorTela, jogador: Jogador,
                           enigma: EnigmaNPC, cfg: dict) -> str:
    """
    Executa uma tentativa de resolução do enigma do guardião.

    Retorna:
      "passou"  — jogador acertou
      "falhou"  — resposta errada (pode tentar de novo)
      "game_over" — não usado aqui, mas mantido por consistência
    """
    # Obtém o enunciado
    resultado = enigma.executar(jogador, resposta=None)
    narrativa = resultado["narrativa"]

    # Loop de input até acertar ou pular
    while not resultado["concluido"]:
        resposta = tela.tela_desafio(narrativa, pede_input=True,
                                      placeholder="Sua resposta...")
        if resposta == "pular":
            return "falhou"

        resultado = enigma.executar(jogador, resposta=resposta)
        narrativa = resultado["narrativa"]

    if resultado["sucesso"]:
        xp_enigma = 40
        subiu_enig = jogador.ganhar_xp(xp_enigma)
        msg_enig = narrativa + f"\n\n+{xp_enigma} XP por resolver o enigma!"
        if subiu_enig:
            msg_enig += f"\nNivel {jogador.nivel}! Seus atributos aumentaram!"
        tela.tela_resultado("Enigma Resolvido!", msg_enig)
        return "passou"
    else:
        tela.tela_resultado("Resposta Errada", narrativa)
        return "falhou"


# ================================================================== #
#  Loop de cenário — orquestra tudo
# ================================================================== #

def loop_cenario(tela: GerenciadorTela, jogador: Jogador,
                 dados_cenario: dict) -> str:
    """
    Executa um cenário completo na nova estrutura:

      1. Narração de entrada
      2. Combate com inimigo fixo da entrada
      3. Loop de exploração livre
      4. Guardião de passagem (se houver)
      5. Boss (cenário 6)
      6. Narração de saída

    Retorna: "proximo" | "game_over" | "menu"
    """
    nome      = dados_cenario["nome"]
    subtitulo = dados_cenario["subtitulo"]

    # ── 1. Narração de entrada ──────────────────────────────────────
    acao = tela.tela_narracao(
        titulo    = nome,
        subtitulo = subtitulo,
        narrativa = dados_cenario["narrativa_entrada"],
        jogador   = jogador,
    )
    if acao == "sair":
        return "menu"
    if acao == "inventario":
        tela.tela_inventario(jogador)

    # ── 2. Inimigo fixo da entrada ─────────────────────────────────
    id_entrada = dados_cenario.get("inimigo_entrada")
    if id_entrada:
        inimigo = _inimigo_por_id(id_entrada, jogador.nivel)
        if inimigo:
            # Usa a narração de encontro específica do inimigo
            acao = tela.tela_narracao(
                titulo    = "Encontro!",
                subtitulo = inimigo.nome,
                narrativa = _narrativa_encontro(id_entrada),
                jogador   = jogador,
            )
            if acao == "sair":
                return "menu"

            vivo = loop_combate(tela, jogador, inimigo)
            if not vivo:
                return "game_over"

    # ── 3. Loop de exploração ──────────────────────────────────────
    resultado_exp = loop_exploracao(tela, jogador, dados_cenario)
    if resultado_exp == "game_over":
        return "game_over"
    if resultado_exp == "menu":
        return "menu"
    # resultado_exp == "continuar" → jogador optou por avançar

    # Auto-save depois da exploração
    SistemaProgresso.salvar(jogador, slot=getattr(jogador, "slot_salvo", 1))

    # ── 4. Guardião de passagem ────────────────────────────────────
    cfg_guardiao = dados_cenario.get("guardiao_passagem")
    if cfg_guardiao:
        resultado_guard = loop_guardiao(tela, jogador, cfg_guardiao)

        if resultado_guard == "game_over":
            return "game_over"

        if resultado_guard == "voltou":
            # Jogador voltou para a exploração — recomeça o loop de exploração
            # com o mínimo já cumprido (exploração anterior contou)
            resultado_exp2 = loop_exploracao(tela, jogador, dados_cenario)
            if resultado_exp2 in ("game_over", "menu"):
                return resultado_exp2
            # Tenta o guardião de novo
            resultado_guard2 = loop_guardiao(tela, jogador, cfg_guardiao)
            if resultado_guard2 in ("game_over", "voltou"):
                # Segunda recusa — deixa passar (não prende o jogador para sempre)
                if resultado_guard2 == "game_over":
                    return "game_over"
            # passou ou segunda tentativa ignorada → segue em frente

        # resultado_guard == "passou" → segue normalmente

    # ── 5. Boss (cenário 6) ────────────────────────────────────────
    if dados_cenario.get("boss") == "xerife_de_ferro":
        boss = Boss()
        tela.tela_narracao(
            titulo    = "BOSS",
            subtitulo = "O Xerife de Ferro",
            narrativa = boss.descricao(),
            jogador   = jogador,
        )
        resultado_boss = loop_combate(tela, jogador, boss, is_boss=True)
        if resultado_boss == "fuga_boss":
            return "fuga_boss"   # sinaliza para iniciar_jogo mostrar tela especial
        if not resultado_boss:
            return "game_over"

    # ── 6. Narração de saída ───────────────────────────────────────
    acao = tela.tela_narracao(
        titulo    = nome,
        subtitulo = "Partindo...",
        narrativa = dados_cenario["narrativa_saida"],
        jogador   = jogador,
    )
    if acao == "sair":
        return "menu"

    jogador.cenario_atual += 1
    SistemaProgresso.salvar(jogador, slot=getattr(jogador, "slot_salvo", 1))
    return "proximo"


# ================================================================== #
#  Loop principal do jogo
# ================================================================== #

def iniciar_jogo(tela: GerenciadorTela, jogador: Jogador) -> str:
    """
    Percorre todos os cenários em ordem até terminar ou o jogador sair.
    Retorna "menu" ou "reiniciar".
    """
    while jogador.cenario_atual < len(CENARIOS):
        dados    = CENARIOS[jogador.cenario_atual]
        resultado = loop_cenario(tela, jogador, dados)

        if resultado == "game_over":
            opcao = tela.tela_game_over()
            return "reiniciar" if opcao == "reiniciar" else "menu"

        if resultado == "fuga_boss":
            opcao = tela.tela_fim_covarde()
            return "reiniciar" if opcao == "reiniciar" else "menu"

        if resultado == "menu":
            return "menu"

    # Todos os cenários concluídos → vitória
    opcao = tela.tela_vitoria()
    return "reiniciar" if opcao == "reiniciar" else "menu"


# ================================================================== #
#  Entry point
# ================================================================== #

def main() -> None:
    tela = GerenciadorTela()

    while True:
        saves = SistemaProgresso.listar_saves()
        acao  = tela.tela_menu_principal(saves)

        if acao == "sair":
            break

        if acao.startswith("novo_jogo"):
            # Slot escolhido pode vir embutido: "novo_jogo_2"
            partes = acao.split("_")
            slot_escolhido = int(partes[-1]) if len(partes) == 3 and partes[-1].isdigit() else 1

            dados_criacao = tela.tela_criacao_personagem()
            if not dados_criacao:
                continue
            jogador = Jogador(
                dados_criacao["nome"],
                dados_criacao["raca"],
                dados_criacao["vocacao"],
            )
            jogador.slot_salvo = slot_escolhido
            SistemaProgresso.salvar(jogador, slot=slot_escolhido)

        elif acao.startswith("carregar_"):
            slot    = int(acao.split("_")[1])
            jogador = SistemaProgresso.carregar(slot)
            if not jogador:
                tela.tela_resultado("Erro", "Save corrompido ou nao encontrado.")
                continue
            jogador.slot_salvo = slot

        elif acao.startswith("deletar_"):
            slot = int(acao.split("_")[1])
            SistemaProgresso.deletar(slot)
            continue   # volta ao menu sem iniciar jogo

        else:
            continue

        resultado = iniciar_jogo(tela, jogador)
        if resultado == "reiniciar":
            continue

    tela.encerrar()
    sys.exit(0)


if __name__ == "__main__":
    main()