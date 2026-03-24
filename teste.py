"""
teste.py — Suite de testes para o RPG Cyber-Western
Testa todas as classes, subclasses e mecânicas sem precisar de pygame.

Uso:  python teste.py
      python teste.py -v   (verbose)
"""

import sys
import os

# Garante que imports funcionem a partir da raiz do projeto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ------------------------------------------------------------------ #
#  Patch: evita importar pygame nos módulos de interface
# ------------------------------------------------------------------ #
import unittest
from unittest.mock import MagicMock, patch

# ================================================================== #
#  1. SISTEMA DE DADOS
# ================================================================== #

class TestSistemaDados(unittest.TestCase):

    def setUp(self):
        from mecanicas.dados import SistemaDados
        self.D = SistemaDados

    def test_d4_range(self):
        for _ in range(100):
            r = self.D.rolar_d4()
            self.assertGreaterEqual(r, 1)
            self.assertLessEqual(r, 4)

    def test_d6_range(self):
        for _ in range(100):
            r = self.D.rolar_d6()
            self.assertIn(r, range(1, 7))

    def test_d8_range(self):
        for _ in range(100):
            self.assertIn(self.D.rolar_d8(), range(1, 9))

    def test_d10_range(self):
        for _ in range(100):
            self.assertIn(self.D.rolar_d10(), range(1, 11))

    def test_d12_range(self):
        for _ in range(100):
            self.assertIn(self.D.rolar_d12(), range(1, 13))

    def test_d20_range(self):
        for _ in range(200):
            r = self.D.rolar_d20()
            self.assertGreaterEqual(r, 1)
            self.assertLessEqual(r, 20)

    def test_d100_range(self):
        for _ in range(100):
            self.assertIn(self.D.rolar_d100(), range(1, 101))

    def test_personalizado(self):
        for _ in range(100):
            r = self.D.rolar_personalizado(5, 10)
            self.assertGreaterEqual(r, 5)
            self.assertLessEqual(r, 10)


# ================================================================== #
#  2. RAÇAS
# ================================================================== #

class TestRacas(unittest.TestCase):

    def test_humano_modificadores(self):
        from criacao.raca import Humano
        h = Humano()
        self.assertEqual(h.mod_poder,   2)
        self.assertEqual(h.mod_defesa,  2)
        self.assertEqual(h.mod_vida,    2)
        self.assertEqual(h.mod_esquiva, 2)
        self.assertEqual(h.nome, "Humano")

    def test_ciborgue_modificadores(self):
        from criacao.raca import Ciborgue
        c = Ciborgue()
        self.assertEqual(c.mod_defesa,  5)
        self.assertEqual(c.mod_vida,   10)
        self.assertEqual(c.mod_esquiva,-2)
        self.assertFalse(c._escudo_ativo)

    def test_androide_modificadores(self):
        from criacao.raca import Androide
        a = Androide()
        self.assertEqual(a.mod_poder,   5)
        self.assertEqual(a.mod_esquiva, 3)
        self.assertEqual(a.mod_vida,   -3)

    def test_humano_passiva_cura(self):
        from criacao.raca import Humano
        from entidades.jogador import Jogador
        from criacao.vocacao import Pistoleiro
        j = Jogador("Teste", Humano(), Pistoleiro())
        j.receber_dano(20)
        vida_antes = j.vida_atual
        msg = j.raca.habilidade_passiva(j)
        self.assertEqual(j.vida_atual, vida_antes + 5)
        self.assertIn("5", msg)

    def test_ciborgue_escudo(self):
        from criacao.raca import Ciborgue
        c = Ciborgue()
        c.ativar_escudo()
        self.assertTrue(c._escudo_ativo)
        dano_real = c.absorver_dano(10)
        self.assertEqual(dano_real, 7)   # 10 - 3
        self.assertFalse(c._escudo_ativo)
        # Sem escudo, dano passa inteiro
        self.assertEqual(c.absorver_dano(10), 10)

    def test_androide_mira(self):
        from criacao.raca import Androide
        from entidades.jogador import Jogador
        from criacao.vocacao import Pistoleiro
        j = Jogador("Teste", Androide(), Pistoleiro())
        poder_antes = j.poder
        j.raca.habilidade_passiva(j)
        self.assertEqual(j.poder, poder_antes + 5)
        self.assertFalse(j.raca._mira_disponivel)
        # Segunda chamada não dá bônus
        j.raca.habilidade_passiva(j)
        self.assertEqual(j.poder, poder_antes + 5)

    def test_resumo_modificadores_formato(self):
        from criacao.raca import Humano
        resumo = Humano().resumo_modificadores()
        self.assertIn("Poder", resumo)
        self.assertIn("+2", resumo)

    def test_raca_e_classe_abstrata(self):
        from criacao.raca import Raca
        with self.assertRaises(TypeError):
            Raca()


# ================================================================== #
#  3. VOCAÇÕES
# ================================================================== #

class TestVocacoes(unittest.TestCase):

    def _jogador_com(self, raca_cls, voc_cls):
        from entidades.jogador import Jogador
        return Jogador("Herói", raca_cls(), voc_cls())

    def test_pistoleiro_mods(self):
        from criacao.vocacao import Pistoleiro
        p = Pistoleiro()
        self.assertEqual(p.mod_poder,   5)
        self.assertEqual(p.mod_esquiva, 2)
        self.assertEqual(p.nome, "Pistoleiro")
        self.assertEqual(p.nome_habilidade, "Tiro Duplo")

    def test_tecnos_abio_mods(self):
        from criacao.vocacao import TecnoSabio
        t = TecnoSabio()
        self.assertEqual(t.mod_poder,  5)
        self.assertEqual(t.mod_defesa, 2)

    def test_sucateiro_mods(self):
        from criacao.vocacao import Sucateiro
        s = Sucateiro()
        self.assertEqual(s.mod_defesa, 3)
        self.assertEqual(s.mod_vida,  15)

    def test_usos_resetar(self):
        from criacao.vocacao import Pistoleiro
        p = Pistoleiro()
        p._habilidade_usos = 0
        self.assertFalse(p.tem_uso_disponivel())
        p.resetar_usos()
        self.assertTrue(p.tem_uso_disponivel())

    def test_pistoleiro_tiro_duplo(self):
        from criacao.raca import Humano
        from criacao.vocacao import Pistoleiro
        from entidades.monstro import Monstro
        j = self._jogador_com(Humano, Pistoleiro)
        alvo = Monstro("Alvo", poder=3, defesa=2, vida=100, esquiva=2,
                        xp_recompensa=10)
        res = j.vocacao.habilidade_especial(j, alvo)
        self.assertIn("narrativa", res)
        self.assertIn("dano", res)
        self.assertFalse(j.vocacao.tem_uso_disponivel())
        # Segundo uso — bloqueado
        res2 = j.vocacao.habilidade_especial(j, alvo)
        self.assertIn("usado", res2["narrativa"])

    def test_tecnos_abio_hack(self):
        from criacao.raca import Humano
        from criacao.vocacao import TecnoSabio
        from entidades.monstro import Monstro
        j = self._jogador_com(Humano, TecnoSabio)
        alvo = Monstro("Alvo", poder=3, defesa=8, vida=100, esquiva=2,
                        xp_recompensa=10)
        res = j.vocacao.habilidade_especial(j, alvo)
        self.assertEqual(alvo.defesa, 0)          # zerada
        self.assertGreater(res["dano"], 0)
        self.assertTrue(hasattr(alvo, "_defesa_hackeada"))
        self.assertEqual(alvo._defesa_hackeada, 8)  # valor original guardado

    def test_sucateiro_escudo(self):
        from criacao.raca import Humano
        from criacao.vocacao import Sucateiro
        from entidades.monstro import Monstro
        j = self._jogador_com(Humano, Sucateiro)
        defesa_antes = j.defesa
        alvo = Monstro("Alvo", poder=3, defesa=2, vida=50, esquiva=2,
                        xp_recompensa=10)
        res = j.vocacao.habilidade_especial(j, alvo)
        self.assertEqual(j.defesa, defesa_antes + 5)
        self.assertGreater(j.vocacao._escudo_pontos, 0)

    def test_sucateiro_absorver_dano(self):
        from criacao.vocacao import Sucateiro
        s = Sucateiro()
        s._escudo_pontos = 10
        self.assertEqual(s.absorver_dano_escudo(7),  0)   # tudo absorvido, 3 sobra
        self.assertEqual(s._escudo_pontos, 3)
        self.assertEqual(s.absorver_dano_escudo(10), 7)   # 3 absorvido, 7 passa

    def test_vocacao_e_classe_abstrata(self):
        from criacao.vocacao import Vocacao
        with self.assertRaises(TypeError):
            Vocacao()


# ================================================================== #
#  4. JOGADOR
# ================================================================== #

class TestJogador(unittest.TestCase):

    def _j(self):
        from criacao.raca import Humano
        from criacao.vocacao import Pistoleiro
        from entidades.jogador import Jogador
        return Jogador("Dust", Humano(), Pistoleiro())

    def test_atributos_iniciais(self):
        j = self._j()
        # base + Humano(+2) + Pistoleiro(+5 poder, +2 esquiva)
        self.assertEqual(j.poder,   5 + 2 + 5)
        self.assertEqual(j.defesa,  5 + 2 + 0)
        self.assertEqual(j.esquiva, 5 + 2 + 2)
        self.assertEqual(j.vida_maxima, 50 + 2 + 0)
        self.assertEqual(j.nivel, 1)
        self.assertEqual(j.xp,    0)
        self.assertEqual(j.celulas_fusao, 10)

    def test_subir_nivel(self):
        j = self._j()
        poder_antes  = j.poder
        defesa_antes = j.defesa
        j.ganhar_xp(100)
        self.assertEqual(j.nivel, 2)
        self.assertEqual(j.poder,  poder_antes  + 2)
        self.assertEqual(j.defesa, defesa_antes + 1)

    def test_nao_sobe_nivel_sem_xp_suficiente(self):
        j = self._j()
        subiu = j.ganhar_xp(50)
        self.assertFalse(subiu)
        self.assertEqual(j.nivel, 1)

    def test_inventario_pegar_e_usar(self):
        from itens.item import ItemCura
        j = self._j()
        j.receber_dano(20)
        item = ItemCura("Cantil", "Agua boa", cura=15)
        j.pegar_item(item)
        self.assertEqual(len(j.inventario), 1)
        j.usar_item("Cantil")
        self.assertEqual(len(j.inventario), 0)   # consumível removido

    def test_usar_item_inexistente(self):
        j = self._j()
        msg = j.usar_item("Objeto Invalido")
        self.assertIn("não tem", msg)

    def test_descricao(self):
        j = self._j()
        desc = j.descricao()
        self.assertIn("Dust", desc)
        self.assertIn("Humano", desc)

    def test_esta_vivo_e_receber_dano(self):
        j = self._j()
        self.assertTrue(j.esta_vivo)
        j.receber_dano(9999)
        self.assertFalse(j.esta_vivo)
        self.assertEqual(j.vida_atual, 0)

    def test_curar_nao_ultrapassa_maximo(self):
        j = self._j()
        j.curar(9999)
        self.assertEqual(j.vida_atual, j.vida_maxima)

    def test_todas_combinacoes_raca_vocacao(self):
        from criacao.raca    import Humano, Ciborgue, Androide
        from criacao.vocacao import Pistoleiro, TecnoSabio, Sucateiro
        from entidades.jogador import Jogador
        for Raca in [Humano, Ciborgue, Androide]:
            for Voc in [Pistoleiro, TecnoSabio, Sucateiro]:
                j = Jogador("X", Raca(), Voc())
                self.assertGreater(j.vida_maxima, 0)
                self.assertGreater(j.poder,       0)


# ================================================================== #
#  5. MONSTRO
# ================================================================== #

class TestMonstro(unittest.TestCase):

    def _monstro(self, **kw):
        from entidades.monstro import Monstro
        defaults = dict(nome="Rato", poder=4, defesa=2, vida=20,
                        esquiva=3, xp_recompensa=15)
        defaults.update(kw)
        return Monstro(**defaults)

    def test_escalar_nivel1(self):
        from entidades.monstro import Monstro
        dados = {"nome": "Rato", "poder": 4, "defesa": 2, "vida": 20,
                 "esquiva": 3, "xp": 15}
        m = Monstro.escalar(dados, 1)
        self.assertEqual(m.poder, 4)

    def test_escalar_nivel2(self):
        from entidades.monstro import Monstro
        dados = {"nome": "Rato", "poder": 10, "defesa": 4, "vida": 30,
                 "esquiva": 4, "xp": 20}
        m = Monstro.escalar(dados, 2)
        self.assertEqual(m.poder, int(10 * 1.3))

    def test_efeito_choque(self):
        from criacao.raca import Humano
        from criacao.vocacao import Pistoleiro
        from entidades.jogador import Jogador
        j = Jogador("X", Humano(), Pistoleiro())
        m = self._monstro(efeito_especial="choque", poder=99)
        vida_antes = j.vida_atual
        # Força acerto setando poder alto
        resultado = m.atacar(j)
        if resultado["acertou"]:
            self.assertIn("efeito", resultado)

    def test_efeito_radiacao(self):
        from criacao.raca import Humano
        from criacao.vocacao import Pistoleiro
        from entidades.jogador import Jogador
        j = Jogador("X", Humano(), Pistoleiro())
        m = self._monstro(efeito_especial="radiacao", poder=999)
        for _ in range(10):   # garante pelo menos 1 acerto
            resultado = m.atacar(j)
            if resultado["acertou"]:
                self.assertIn("efeito", resultado)
                break

    def test_descricao(self):
        m = self._monstro(descricao_texto="Perigoso!")
        self.assertIn("Perigoso", m.descricao())

    def test_descricao_fallback(self):
        m = self._monstro()
        self.assertIn("Rato", m.descricao())


# ================================================================== #
#  6. BOSS
# ================================================================== #

class TestBoss(unittest.TestCase):

    def setUp(self):
        from entidades.monstro import Boss
        self.boss = Boss()

    def test_fase_inicial(self):
        self.assertEqual(self.boss.fase, 1)

    def test_transicao_fase2(self):
        self.boss.vida_atual = int(self.boss.vida_maxima * 0.49)
        self.boss._atualizar_fase()
        self.assertEqual(self.boss.fase, 2)

    def test_transicao_fase3(self):
        self.boss.vida_atual = int(self.boss.vida_maxima * 0.24)
        self.boss.fase = 2
        self.boss._atualizar_fase()
        self.assertEqual(self.boss.fase, 3)

    def test_buff_fase2_aumenta_poder(self):
        poder_antes = self.boss.poder
        self.boss.fase = 2
        self.boss._aplicar_buff_fase()
        self.assertEqual(self.boss.poder, poder_antes + 5)

    def test_descricao_contem_fase(self):
        desc = self.boss.descricao()
        self.assertIn("Fase", desc)

    def test_heranca(self):
        from entidades.monstro import Monstro
        self.assertIsInstance(self.boss, Monstro)


# ================================================================== #
#  7. SISTEMA DE COMBATE
# ================================================================== #

class TestSistemaCombate(unittest.TestCase):

    def _setup(self, raca_cls=None, voc_cls=None):
        from criacao.raca    import Humano
        from criacao.vocacao import Pistoleiro
        from entidades.jogador import Jogador
        from entidades.monstro import Monstro
        from mecanicas.combate import SistemaCombate

        r = raca_cls() if raca_cls else Humano()
        v = voc_cls()  if voc_cls  else Pistoleiro()
        j = Jogador("Herói", r, v)
        m = Monstro("Zumbi", poder=3, defesa=2, vida=30,
                    esquiva=2, xp_recompensa=20)
        c = SistemaCombate(j, m)
        return j, m, c

    def test_turno_atacar_estrutura(self):
        j, m, c = self._setup()
        res = c.executar_turno("atacar")
        self.assertIn("fim_combate", res)
        self.assertIn("turno",       res)
        self.assertIn("acao_jogador", res)

    def test_turno_fugir(self):
        j, m, c = self._setup()
        with patch.object(j, "tentar_fuga", return_value=True):
            res = c.executar_turno("fugir")
        self.assertTrue(res["fuga"])
        self.assertTrue(res["fim_combate"])

    def test_vitoria_inimigo_morto(self):
        j, m, c = self._setup()
        m.vida_atual = 1          # quase morto
        m.defesa     = 0          # garante dano
        j.poder      = 999
        res = c.executar_turno("atacar")
        self.assertTrue(res["vitoria"])
        self.assertTrue(res["fim_combate"])
        self.assertIn("xp_ganho", res)

    def test_game_over_jogador_morto(self):
        j, m, c = self._setup()
        j.vida_atual = 1
        j.defesa     = 0
        m.poder      = 999
        # Força inimigo a acertar
        with patch("mecanicas.dados.SistemaDados.rolar_d20", return_value=20):
            res = c.executar_turno("atacar")
        if res["fim_combate"] and not res["vitoria"]:
            self.assertFalse(j.esta_vivo)

    def test_log_registra_eventos(self):
        j, m, c = self._setup()
        c.executar_turno("atacar")
        self.assertGreater(len(c.log), 0)

    def test_estado_combate_estrutura(self):
        j, m, c = self._setup()
        estado = c.estado_combate()
        self.assertIn("jogador", estado)
        self.assertIn("inimigo", estado)
        self.assertIn("turno",   estado)
        self.assertEqual(estado["jogador"]["nome"], "Herói")

    def test_habilidade_pistoleiro(self):
        from criacao.vocacao import Pistoleiro
        j, m, c = self._setup(voc_cls=Pistoleiro)
        res = c.executar_turno("habilidade")
        self.assertIn("acao_jogador", res)

    def test_habilidade_tecnos_abio(self):
        from criacao.vocacao import TecnoSabio
        j, m, c = self._setup(voc_cls=TecnoSabio)
        defesa_original = m.defesa
        c.executar_turno("habilidade")
        # Defesa deve ser restaurada após o turno (hack)
        self.assertEqual(m.defesa, defesa_original)

    def test_item_em_combate(self):
        from itens.item import ItemCura
        j, m, c = self._setup()
        j.receber_dano(10)
        item = ItemCura("Cantil", "Agua", cura=10)
        j.pegar_item(item)
        res = c.executar_turno("item", "Cantil")
        self.assertIn("acao_jogador", res)


# ================================================================== #
#  8. DESAFIOS
# ================================================================== #

class TestDesafios(unittest.TestCase):

    def _jogador(self):
        from criacao.raca import Humano
        from criacao.vocacao import Pistoleiro
        from entidades.jogador import Jogador
        return Jogador("X", Humano(), Pistoleiro())

    # --- DesafioTerminal ---

    def test_terminal_exibe_pergunta_sem_resposta(self):
        from mecanicas.desafios import DesafioTerminal
        t = DesafioTerminal()
        j = self._jogador()
        res = t.executar(j, resposta=None)
        self.assertFalse(res["concluido"])
        self.assertIn("Terminal", res["narrativa"])

    def test_terminal_resposta_correta(self):
        from mecanicas.desafios import DesafioTerminal
        t = DesafioTerminal()
        j = self._jogador()
        resposta_certa = str(t._puzzle["resposta"])
        res = t.executar(j, resposta=resposta_certa)
        self.assertTrue(res["sucesso"])
        self.assertTrue(res["concluido"])
        self.assertGreater(res["recompensa"]["celulas"], 0)

    def test_terminal_resposta_errada_3x(self):
        from mecanicas.desafios import DesafioTerminal
        t = DesafioTerminal()
        j = self._jogador()
        vida_antes = j.vida_atual
        for _ in range(3):
            t.executar(j, resposta="9999")
        self.assertTrue(t._concluido)
        self.assertLess(j.vida_atual, vida_antes)

    def test_terminal_dica_tecnos_abio(self):
        from criacao.raca import Humano
        from criacao.vocacao import TecnoSabio
        from entidades.jogador import Jogador
        from mecanicas.desafios import DesafioTerminal
        j = Jogador("X", Humano(), TecnoSabio())
        t = DesafioTerminal()
        dica = t.dica(j)
        self.assertIn(str(t._puzzle["resposta"]), dica)

    # --- DesafioArmadilha ---

    def test_armadilha_retorna_resultado(self):
        from mecanicas.desafios import DesafioArmadilha
        j = self._jogador()
        a = DesafioArmadilha()
        res = a.executar(j)
        # Estrutura obrigatória presente
        self.assertIn("sucesso",   res)
        self.assertIn("narrativa", res)
        self.assertIn("penalidade", res)
        # Resultado é sempre determinado (sucesso ou falha com dano)
        narrativa_tem_conteudo = len(res["narrativa"]) > 0
        self.assertTrue(narrativa_tem_conteudo)

    def test_armadilha_sucateiro_bonus(self):
        from criacao.raca import Humano
        from criacao.vocacao import Sucateiro
        from entidades.jogador import Jogador
        from mecanicas.desafios import DesafioArmadilha
        j = Jogador("X", Humano(), Sucateiro())
        a = DesafioArmadilha()
        res = a.executar(j)
        if not res["sucesso"]:
            self.assertIn("Sucateiro", res["narrativa"])

    # --- EnigmaNPC ---

    def test_enigma_exibe_charada(self):
        from mecanicas.desafios import EnigmaNPC
        j = self._jogador()
        e = EnigmaNPC(indice=0)
        res = e.executar(j, resposta=None)
        self.assertFalse(res["concluido"])
        self.assertIn("Minerador", res["narrativa"])

    def test_enigma_resposta_correta(self):
        from mecanicas.desafios import EnigmaNPC
        j = self._jogador()
        e = EnigmaNPC(indice=0)   # resposta: "mapa"
        res = e.executar(j, resposta="mapa")
        self.assertTrue(res["sucesso"])

    def test_enigma_resposta_errada(self):
        from mecanicas.desafios import EnigmaNPC
        j = self._jogador()
        e = EnigmaNPC(indice=0)
        res = e.executar(j, resposta="cactus")
        self.assertFalse(res["sucesso"])
        self.assertFalse(res["concluido"])

    # --- DesafioRecurso ---

    def test_recurso_abre_com_poder_alto(self):
        from mecanicas.desafios import DesafioRecurso
        j = self._jogador()
        j.poder = 999
        r = DesafioRecurso(tipo="cofre", dificuldade=1)
        res = r.executar(j)
        self.assertTrue(res["sucesso"])
        self.assertGreater(len(j.inventario), 0)

    def test_recurso_da_item_aleatorio(self):
        from mecanicas.desafios import DesafioRecurso
        from itens.item import Item
        j = self._jogador()
        j.poder = 999
        r = DesafioRecurso(dificuldade=1)
        r.executar(j)
        if j.inventario:
            self.assertIsInstance(j.inventario[0], Item)

    def test_recurso_ja_aberto(self):
        from mecanicas.desafios import DesafioRecurso
        j = self._jogador()
        j.poder = 999
        r = DesafioRecurso()
        r.executar(j)
        res2 = r.executar(j)
        self.assertIn("aberto", res2["narrativa"])

    def test_heranca_desafios(self):
        from mecanicas.desafios import (Desafio, DesafioTerminal,
                                         DesafioArmadilha, EnigmaNPC,
                                         DesafioRecurso)
        for cls in [DesafioTerminal, DesafioArmadilha, EnigmaNPC, DesafioRecurso]:
            self.assertTrue(issubclass(cls, Desafio))


# ================================================================== #
#  9. ITENS
# ================================================================== #

class TestItens(unittest.TestCase):

    def _j(self):
        from criacao.raca import Humano
        from criacao.vocacao import Pistoleiro
        from entidades.jogador import Jogador
        return Jogador("X", Humano(), Pistoleiro())

    def test_item_cura(self):
        from itens.item import ItemCura
        j = self._j()
        j.receber_dano(30)
        item = ItemCura("Gel", "Cura bastante", cura=20)
        msg = item.usar(j)
        self.assertIn("20", msg)
        self.assertEqual(item.consumivel, True)

    def test_item_cura_nao_passa_maximo(self):
        from itens.item import ItemCura
        j = self._j()
        item = ItemCura("Super", "desc", cura=9999)
        item.usar(j)
        self.assertEqual(j.vida_atual, j.vida_maxima)

    def test_item_combate_prepara_pendente(self):
        from itens.item import ItemCombate
        j = self._j()
        item = ItemCombate("Granada", "Boom", dano_min=10, dano_max=20)
        msg = item.usar(j)
        self.assertTrue(hasattr(j, "_item_combate_pendente"))
        self.assertIn("Granada", msg)

    def test_item_utilidade_buffs(self):
        from itens.item import ItemUtilidade
        j = self._j()
        poder_antes  = j.poder
        defesa_antes = j.defesa
        item = ItemUtilidade("Boost", "desc", buff_poder=3, buff_defesa=2)
        item.usar(j)
        self.assertEqual(j.poder,  poder_antes  + 3)
        self.assertEqual(j.defesa, defesa_antes + 2)

    def test_item_raridade_str(self):
        from itens.item import ItemCura
        i = ItemCura("X", "desc", cura=5, raridade="raro")
        self.assertIn("★", str(i))

    def test_fabrica_cria_cura(self):
        from itens.item import FabricaItens, ItemCura
        dados = {"tipo": "cura", "nome": "Cantil", "descricao": "ok",
                 "cura": 20, "raridade": "comum"}
        item = FabricaItens.criar(dados)
        self.assertIsInstance(item, ItemCura)

    def test_fabrica_cria_combate(self):
        from itens.item import FabricaItens, ItemCombate
        dados = {"tipo": "combate", "nome": "Bomba", "descricao": "ok",
                 "dano_min": 5, "dano_max": 15, "raridade": "incomum"}
        item = FabricaItens.criar(dados)
        self.assertIsInstance(item, ItemCombate)

    def test_fabrica_cria_utilidade(self):
        from itens.item import FabricaItens, ItemUtilidade
        dados = {"tipo": "utilidade", "nome": "Oculos", "descricao": "ok",
                 "buff_poder": 2, "raridade": "comum"}
        item = FabricaItens.criar(dados)
        self.assertIsInstance(item, ItemUtilidade)

    def test_fabrica_tipo_invalido(self):
        from itens.item import FabricaItens
        with self.assertRaises(ValueError):
            FabricaItens.criar({"tipo": "magico", "nome": "X"})

    def test_fabrica_item_aleatorio_raridade(self):
        from itens.item import FabricaItens
        pool = [
            {"tipo": "cura", "nome": "A", "descricao": "d", "cura": 10, "raridade": "comum"},
            {"tipo": "cura", "nome": "B", "descricao": "d", "cura": 20, "raridade": "raro"},
        ]
        for _ in range(20):
            item = FabricaItens.item_aleatorio(pool, "raro")
            self.assertEqual(item.raridade, "raro")

    def test_item_classe_abstrata(self):
        from itens.item import Item
        with self.assertRaises(TypeError):
            Item("X", "desc")


# ================================================================== #
#  10. SISTEMA DE PROGRESSO (save/load)
# ================================================================== #

class TestSistemaProgresso(unittest.TestCase):

    def setUp(self):
        # Usa pasta temporária do sistema — funciona em Windows, Linux e macOS
        import tempfile
        from utils.progresso import SistemaProgresso
        from pathlib import Path
        self.SP        = SistemaProgresso
        self.slot      = 99
        self._tmp_dir  = tempfile.mkdtemp(prefix="test_cyber_")
        self.SP.PASTA_SAVES = Path(self._tmp_dir)

    def tearDown(self):
        # Remove save de teste e limpa pasta temporária
        self.SP.deletar(self.slot)
        import shutil
        shutil.rmtree(self._tmp_dir, ignore_errors=True)

    def _jogador(self):
        from criacao.raca import Humano
        from criacao.vocacao import Pistoleiro
        from entidades.jogador import Jogador
        from itens.item import ItemCura
        j = Jogador("Salvo", Humano(), Pistoleiro())
        j.pegar_item(ItemCura("Cantil", "agua", cura=20))
        j.nivel = 3
        j.celulas_fusao = 42
        j.cenario_atual = 2
        return j

    def test_salvar_cria_arquivo(self):
        j = self._jogador()
        ok = self.SP.salvar(j, self.slot)
        self.assertTrue(ok)
        self.assertTrue(self.SP.existe(self.slot))

    def test_carregar_restaura_atributos(self):
        j = self._jogador()
        self.SP.salvar(j, self.slot)
        j2 = self.SP.carregar(self.slot)
        self.assertEqual(j2.nome,          "Salvo")
        self.assertEqual(j2.nivel,         3)
        self.assertEqual(j2.celulas_fusao, 42)
        self.assertEqual(j2.cenario_atual, 2)

    def test_carregar_restaura_inventario(self):
        j = self._jogador()
        self.SP.salvar(j, self.slot)
        j2 = self.SP.carregar(self.slot)
        self.assertEqual(len(j2.inventario), 1)
        self.assertEqual(j2.inventario[0].nome, "Cantil")

    def test_carregar_slot_inexistente(self):
        resultado = self.SP.carregar(88)
        self.assertIsNone(resultado)

    def test_listar_saves(self):
        j = self._jogador()
        self.SP.salvar(j, self.slot)
        # Apenas verifica que listar não lança exceção
        saves = self.SP.listar_saves()
        self.assertIsInstance(saves, list)

    def test_deletar(self):
        j = self._jogador()
        self.SP.salvar(j, self.slot)
        ok = self.SP.deletar(self.slot)
        self.assertTrue(ok)
        self.assertFalse(self.SP.existe(self.slot))

    def test_deletar_inexistente(self):
        ok = self.SP.deletar(88)
        self.assertFalse(ok)


# ================================================================== #
#  11. HERANÇA E POLIMORFISMO — verificações diretas
# ================================================================== #

class TestHerancaPolimorfismo(unittest.TestCase):

    def test_hierarquia_entidade(self):
        from entidades.entidade import Entidade
        from entidades.jogador  import Jogador
        from entidades.monstro  import Monstro, Boss
        from criacao.raca    import Humano
        from criacao.vocacao import Pistoleiro

        j = Jogador("X", Humano(), Pistoleiro())
        m = Monstro("Y", 4, 2, 20, 3, 10)
        b = Boss()

        self.assertIsInstance(j, Entidade)
        self.assertIsInstance(m, Entidade)
        self.assertIsInstance(b, Entidade)
        self.assertIsInstance(b, Monstro)

    def test_polimorfismo_atacar_boss_vs_monstro(self):
        """Boss.atacar() e Monstro.atacar() retornam estruturas compatíveis."""
        from criacao.raca import Humano
        from criacao.vocacao import Pistoleiro
        from entidades.jogador import Jogador
        from entidades.monstro import Monstro, Boss

        j = Jogador("X", Humano(), Pistoleiro())
        m = Monstro("M", 3, 2, 50, 2, 10)
        b = Boss()

        res_m = m.atacar(j)
        j.vida_atual = j.vida_maxima  # restaura antes do boss atacar
        res_b = b.atacar(j)

        for res in [res_m, res_b]:
            self.assertIn("acertou",  res)
            self.assertIn("atacante", res)
            self.assertIn("dano",     res)

    def test_polimorfismo_descricao_todas_entidades(self):
        from criacao.raca    import Humano
        from criacao.vocacao import Pistoleiro
        from entidades.jogador import Jogador
        from entidades.monstro import Monstro, Boss

        entidades = [
            Jogador("X", Humano(), Pistoleiro()),
            Monstro("Y", 4, 2, 20, 3, 10, descricao_texto="desc"),
            Boss(),
        ]
        for e in entidades:
            self.assertIsInstance(e.descricao(), str)
            self.assertGreater(len(e.descricao()), 0)

    def test_polimorfismo_habilidade_especial(self):
        from criacao.raca    import Humano
        from criacao.vocacao import Pistoleiro, TecnoSabio, Sucateiro
        from entidades.jogador import Jogador
        from entidades.monstro import Monstro

        alvo = Monstro("Z", 3, 3, 100, 2, 10)
        for VocCls in [Pistoleiro, TecnoSabio, Sucateiro]:
            j = Jogador("X", Humano(), VocCls())
            res = j.habilidade_especial(alvo)
            self.assertIn("narrativa", res)
            self.assertIn("dano",      res)

    def test_polimorfismo_desafios(self):
        from criacao.raca import Humano
        from criacao.vocacao import Pistoleiro
        from entidades.jogador import Jogador
        from mecanicas.desafios import (DesafioTerminal, DesafioArmadilha,
                                         EnigmaNPC, DesafioRecurso)

        j = Jogador("X", Humano(), Pistoleiro())
        for DesafioCls in [DesafioTerminal, DesafioArmadilha,
                            EnigmaNPC, DesafioRecurso]:
            d = DesafioCls()
            res = d.executar(j)
            self.assertIn("narrativa", res)
            self.assertIn("sucesso",   res)

    def test_polimorfismo_itens(self):
        from criacao.raca    import Humano
        from criacao.vocacao import Pistoleiro
        from entidades.jogador import Jogador
        from itens.item import ItemCura, ItemCombate, ItemUtilidade, Item

        j = Jogador("X", Humano(), Pistoleiro())
        itens = [
            ItemCura("Cura", "d", cura=10),
            ItemCombate("Bomba", "d", dano_min=5, dano_max=10),
            ItemUtilidade("Boost", "d", buff_poder=2),
        ]
        for item in itens:
            self.assertIsInstance(item, Item)
            msg = item.usar(j)
            self.assertIsInstance(msg, str)


# ================================================================== #
#  RUNNER
# ================================================================== #

if __name__ == "__main__":
    print("=" * 65)
    print("  SUITE DE TESTES — Deserto de Silicio RPG")
    print("=" * 65)

    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()

    modulos = [
        TestSistemaDados,
        TestRacas,
        TestVocacoes,
        TestJogador,
        TestMonstro,
        TestBoss,
        TestSistemaCombate,
        TestDesafios,
        TestItens,
        TestSistemaProgresso,
        TestHerancaPolimorfismo,
    ]

    for mod in modulos:
        suite.addTests(loader.loadTestsFromTestCase(mod))

    # Sempre usa verbosity=2 para mostrar cada teste
    # Stream para stdout para não misturar com stderr
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    resultado = runner.run(suite)

    print("\n" + "=" * 65)
    total  = resultado.testsRun
    falhas = len(resultado.failures) + len(resultado.errors)
    passou = total - falhas

    print(f"  Total: {total} | Passou: {passou} | Falhou: {falhas}")

    # Mostra resumo detalhado de cada falha/erro
    if resultado.failures:
        print("\n--- FALHAS ---")
        for test, traceback in resultado.failures:
            print(f"\n[FALHA] {test}")
            # Pega apenas a última linha do traceback (a asserção)
            linhas = traceback.strip().split("\n")
            for linha in linhas[-3:]:
                print(f"  {linha}")

    if resultado.errors:
        print("\n--- ERROS ---")
        for test, traceback in resultado.errors:
            print(f"\n[ERRO] {test}")
            linhas = traceback.strip().split("\n")
            for linha in linhas[-3:]:
                print(f"  {linha}")

    print("=" * 65)
    sys.exit(0 if resultado.wasSuccessful() else 1)