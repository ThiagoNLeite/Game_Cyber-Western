import pygame
from interface.cores_estilo import *
from criacao.raca import Humano, Ciborgue, Androide
from criacao.vocacao import Pistoleiro, TecnoSabio, Sucateiro


# ======================================================================= #
#  Classe auxiliar: botão clicável
# ======================================================================= #

class Botao:
    def __init__(self, x: int, y: int, largura: int, altura: int,
                 texto: str, ativo: bool = True):
        self.rect   = pygame.Rect(x, y, largura, altura)
        self.texto  = texto
        self.ativo  = ativo
        self._hover = False

    def atualizar(self, pos_mouse: tuple) -> None:
        self._hover = self.rect.collidepoint(pos_mouse) and self.ativo

    def clicado(self, evento) -> bool:
        return (self.ativo and evento.type == pygame.MOUSEBUTTONDOWN
                and evento.button == 1 and self.rect.collidepoint(evento.pos))

    def desenhar(self, tela, fonte) -> None:
        if not self.ativo:
            cor_fundo = CINZA_MEDIO
            cor_texto = CINZA_FRACO
        elif self._hover:
            cor_fundo = COR_BOTAO_HOVER
            cor_texto = COR_BOTAO_TEXTO
        else:
            cor_fundo = COR_BOTAO
            cor_texto = COR_BOTAO_TEXTO

        pygame.draw.rect(tela, cor_fundo, self.rect, border_radius=RAIO_BORDA)
        pygame.draw.rect(tela, COR_BORDA,  self.rect, ESPESSURA_BORDA, border_radius=RAIO_BORDA)

        surf = fonte.render(self.texto, True, cor_texto)
        tela.blit(surf, surf.get_rect(center=self.rect.center))


# ======================================================================= #
#  Gerenciador principal de tela
# ======================================================================= #

class GerenciadorTela:
    """
    Centraliza toda a renderização pygame do jogo.
    Cada método público corresponde a uma tela/estado:
      tela_menu_principal / tela_criacao_personagem / tela_narracao /
      tela_combate / tela_desafio / tela_inventario /
      tela_resultado / tela_game_over / tela_vitoria
    """

    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITULO)
        self.tela  = pygame.display.set_mode((LARGURA, ALTURA))
        self.clock = pygame.time.Clock()
        self._inicializar_fontes()

        self._texto_completo   = ""
        self._texto_exibido    = ""
        self._char_index       = 0
        self._velocidade_texto = 2
        self._texto_pronto     = False

    def _inicializar_fontes(self) -> None:
        try:
            self.fonte_titulo    = pygame.font.SysFont("consolas", FONTE_TITULO,    bold=True)
            self.fonte_subtitulo = pygame.font.SysFont("consolas", FONTE_SUBTITULO, bold=True)
            self.fonte_texto     = pygame.font.SysFont("consolas", FONTE_TEXTO)
            self.fonte_pequeno   = pygame.font.SysFont("consolas", FONTE_PEQUENO)
            self.fonte_hud       = pygame.font.SysFont("consolas", FONTE_HUD,       bold=True)
        except Exception:
            self.fonte_titulo    = pygame.font.SysFont(None, FONTE_TITULO    + 6)
            self.fonte_subtitulo = pygame.font.SysFont(None, FONTE_SUBTITULO + 4)
            self.fonte_texto     = pygame.font.SysFont(None, FONTE_TEXTO     + 2)
            self.fonte_pequeno   = pygame.font.SysFont(None, FONTE_PEQUENO   + 2)
            self.fonte_hud       = pygame.font.SysFont(None, FONTE_HUD       + 2)

    # ------------------------------------------------------------------ #
    #  Primitivas de desenho
    # ------------------------------------------------------------------ #

    def _limpar(self, cor=COR_FUNDO) -> None:
        self.tela.fill(cor)

    def _painel(self, x, y, w, h, cor=COR_PAINEL, borda=COR_BORDA) -> None:
        pygame.draw.rect(self.tela, cor,   (x, y, w, h), border_radius=RAIO_BORDA)
        pygame.draw.rect(self.tela, borda, (x, y, w, h), ESPESSURA_BORDA, border_radius=RAIO_BORDA)

    def _texto(self, texto: str, x: int, y: int, cor=COR_TEXTO,
               fonte=None, centralizar=False) -> int:
        """
        Renderiza uma linha. Retorna Y da próxima linha.
        BUG CORRIGIDO: centralizar=True agora passa 'top=y' para não ficar em y=0.
        """
        fonte = fonte or self.fonte_texto
        surf  = fonte.render(str(texto), True, cor)
        # *** CORREÇÃO: get_rect precisa do 'top=y' quando centraliza ***
        rect  = surf.get_rect(centerx=x, top=y) if centralizar else surf.get_rect(topleft=(x, y))
        self.tela.blit(surf, rect)
        return y + surf.get_height() + 4

    def _barra(self, x, y, w, h, valor, maximo, cor_cheia, cor_vazia=CINZA_MEDIO) -> None:
        pygame.draw.rect(self.tela, cor_vazia, (x, y, w, h), border_radius=3)
        if maximo > 0:
            fill = int(w * max(0, valor) / maximo)
            if fill > 0:
                pygame.draw.rect(self.tela, cor_cheia, (x, y, fill, h), border_radius=3)
        pygame.draw.rect(self.tela, COR_BORDA, (x, y, w, h), 1, border_radius=3)

    def _cor_hp(self, vida_atual, vida_max) -> tuple:
        pct = vida_atual / vida_max if vida_max > 0 else 0
        if pct > 0.5:  return COR_HP_CHEIO
        if pct > 0.25: return COR_HP_MEDIO
        return COR_HP_BAIXO

    def _wrap_texto(self, texto: str, largura_max: int, fonte) -> list:
        palavras = texto.split(" ")
        linhas, linha_atual = [], ""
        for palavra in palavras:
            teste = (linha_atual + " " + palavra).strip()
            if fonte.size(teste)[0] <= largura_max:
                linha_atual = teste
            else:
                if linha_atual:
                    linhas.append(linha_atual)
                linha_atual = palavra
        if linha_atual:
            linhas.append(linha_atual)
        return linhas

    def _renderizar_bloco_texto(self, texto: str, x, y, largura,
                                 cor=COR_NARRACAO, fonte=None, espacamento=6) -> int:
        fonte = fonte or self.fonte_texto
        for paragrafo in texto.split("\n"):
            linhas = self._wrap_texto(paragrafo, largura, fonte)
            if not linhas:
                y += fonte.get_height()
                continue
            for linha in linhas:
                surf = fonte.render(linha, True, cor)
                self.tela.blit(surf, (x, y))
                y += fonte.get_height() + espacamento
        return y

    # ------------------------------------------------------------------ #
    #  Texto rolando (máquina de escrever)
    # ------------------------------------------------------------------ #

    def iniciar_narracao(self, texto: str) -> None:
        self._texto_completo = texto
        self._texto_exibido  = ""
        self._char_index     = 0
        self._texto_pronto   = False

    def _avancar_narracao(self) -> None:
        if self._texto_pronto:
            return
        self._char_index += self._velocidade_texto
        if self._char_index >= len(self._texto_completo):
            self._char_index   = len(self._texto_completo)
            self._texto_pronto = True
        self._texto_exibido = self._texto_completo[:self._char_index]

    def pular_narracao(self) -> None:
        self._texto_exibido = self._texto_completo
        self._char_index    = len(self._texto_completo)
        self._texto_pronto  = True

    @property
    def narracao_concluida(self) -> bool:
        return self._texto_pronto

    # ------------------------------------------------------------------ #
    #  TELA: Menu Principal
    # ------------------------------------------------------------------ #

    def tela_menu_principal(self, saves: list) -> str:
        """
        Menu principal redesenhado com 3 painéis de slot lado a lado.
        Slots vazios mostram [Novo Jogo]. Slots ocupados mostram info + [Carregar] + [X].
        """
        btn_sair = Botao(LARGURA//2 - 70, ALTURA - 56, 140, 38, "Sair")

        # Layout: 3 painéis de slot horizontais
        N_SLOTS  = 3
        PAINEL_W = (LARGURA - MARGEM * 2 - (N_SLOTS - 1) * 12) // N_SLOTS   # ~273px
        PAINEL_H = 230
        PAINEL_Y = 200

        while True:
            pos = pygame.mouse.get_pos()
            saves_map = {s["slot"]: s for s in saves}

            # Botões recriados a cada frame para refletir estado atual
            btns_carregar = {}   # slot → Botao
            btns_deletar  = {}   # slot → Botao
            btns_novo     = {}   # slot → Botao

            for i in range(N_SLOTS):
                slot = i + 1
                px   = MARGEM + i * (PAINEL_W + 12)
                s    = saves_map.get(slot, {"slot": slot, "vazio": True})

                if s["vazio"]:
                    btns_novo[slot] = Botao(px + 20, PAINEL_Y + 150, PAINEL_W - 40, 40, "Novo Jogo")
                else:
                    btns_carregar[slot] = Botao(px + 10, PAINEL_Y + 160, PAINEL_W - 60, 38, "Carregar")
                    btns_deletar[slot]  = Botao(px + PAINEL_W - 44, PAINEL_Y + 160, 34, 38, "X")

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    return "sair"
                if btn_sair.clicado(ev):
                    return "sair"
                for slot, b in btns_novo.items():
                    if b.clicado(ev):
                        return f"novo_jogo_{slot}"
                for slot, b in btns_carregar.items():
                    if b.clicado(ev):
                        return f"carregar_{slot}"
                for slot, b in btns_deletar.items():
                    if b.clicado(ev):
                        return f"deletar_{slot}"

            self._limpar()

            # Título
            self._texto("DESERTO DE SILICIO", LARGURA//2, 60,
                        COR_TITULO, self.fonte_titulo, centralizar=True)
            self._texto("RPG Cyber-Western", LARGURA//2, 112,
                        COR_SUBTITULO, self.fonte_subtitulo, centralizar=True)
            pygame.draw.line(self.tela, LARANJA,
                             (MARGEM * 4, 158), (LARGURA - MARGEM * 4, 158), 1)

            # Painéis de slot
            for i in range(N_SLOTS):
                slot = i + 1
                px   = MARGEM + i * (PAINEL_W + 12)
                s    = saves_map.get(slot, {"slot": slot, "vazio": True})

                # Borda do painel — laranja se ocupado, cinza se vazio
                cor_borda = LARANJA_ESCURO if not s["vazio"] else COR_BORDA
                self._painel(px, PAINEL_Y, PAINEL_W, PAINEL_H, borda=cor_borda)

                # Cabeçalho do slot
                self._texto(f"SLOT {slot}", px + PAINEL_W//2, PAINEL_Y + 12,
                            COR_SUBTITULO, self.fonte_pequeno, centralizar=True)
                pygame.draw.line(self.tela, cor_borda,
                                 (px + 12, PAINEL_Y + 32), (px + PAINEL_W - 12, PAINEL_Y + 32), 1)

                if s["vazio"]:
                    self._texto("— vazio —", px + PAINEL_W//2, PAINEL_Y + 60,
                                CINZA_FRACO, self.fonte_pequeno, centralizar=True)
                    b = btns_novo.get(slot)
                    if b:
                        b.atualizar(pos)
                        b.desenhar(self.tela, self.fonte_texto)
                else:
                    # Nome e nível
                    self._texto(s["nome"], px + PAINEL_W//2, PAINEL_Y + 44,
                                COR_DESTAQUE, self.fonte_hud, centralizar=True)
                    self._texto(f"Nível {s['nivel']}",
                                px + PAINEL_W//2, PAINEL_Y + 72,
                                CIANO, self.fonte_pequeno, centralizar=True)
                    # Raça / Vocação
                    self._texto(f"{s.get('raca','?')} / {s.get('vocacao','?')}",
                                px + PAINEL_W//2, PAINEL_Y + 92,
                                CINZA_TEXTO, self.fonte_pequeno, centralizar=True)
                    # Cenário
                    nomes_cenario = ["Refúgio", "Desfiladeiro", "Minas",
                                     "Trem Bala", "Oásis", "Torre", "Concluído"]
                    idx_c = min(s.get("cenario", 0), len(nomes_cenario) - 1)
                    self._texto(f"Cenário: {nomes_cenario[idx_c]}",
                                px + PAINEL_W//2, PAINEL_Y + 112,
                                CINZA_TEXTO, self.fonte_pequeno, centralizar=True)
                    # Data
                    self._texto(s.get("data_save", ""),
                                px + PAINEL_W//2, PAINEL_Y + 132,
                                CINZA_FRACO, self.fonte_pequeno, centralizar=True)
                    # Botões
                    bc = btns_carregar.get(slot)
                    bd = btns_deletar.get(slot)
                    if bc:
                        bc.atualizar(pos)
                        bc.desenhar(self.tela, self.fonte_texto)
                    if bd:
                        bd.atualizar(pos)
                        bd.desenhar(self.tela, self.fonte_pequeno)

            btn_sair.atualizar(pos)
            btn_sair.desenhar(self.tela, self.fonte_texto)

            pygame.display.flip()
            self.clock.tick(FPS)

    # ------------------------------------------------------------------ #
    #  TELA: Criação de Personagem
    # ------------------------------------------------------------------ #

    def tela_criacao_personagem(self) -> dict | None:

        racas = [Humano(), Ciborgue(), Androide()]
        vocacoes = [Pistoleiro(), TecnoSabio(), Sucateiro()]

        idx_raca = 0
        idx_vocacao = 0
        nome = ""
        digitando = False

        # Layout
        CY = 170   # y do painel de raça
        VY = 300   # y do painel de vocação
        PW = 380   # largura dos painéis centrais

        btn_rp = Botao(LARGURA//2 - PW//2 - 44, CY + 12, 36, 36, "<")
        btn_rn = Botao(LARGURA//2 + PW//2 + 8,  CY + 12, 36, 36, ">")
        btn_vp = Botao(LARGURA//2 - PW//2 - 44, VY + 12, 36, 36, "<")
        btn_vn = Botao(LARGURA//2 + PW//2 + 8,  VY + 12, 36, 36, ">")

        # Campo de nome — retângulo clicável
        CAMPO_X = LARGURA//2 - 140
        CAMPO_Y = 400
        CAMPO_W = 280
        CAMPO_H = 40
        campo_rect = pygame.Rect(CAMPO_X, CAMPO_Y, CAMPO_W, CAMPO_H)

        btn_confirmar = Botao(LARGURA//2 - 115, 468, 230, 46, "Comecar Jornada")
        btn_voltar    = Botao(MARGEM, ALTURA - 54, 120, 36, "Voltar")

        while True:
            pos = pygame.mouse.get_pos()
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    return None

                # ---- Teclado (sempre ativo quando digitando) ----
                if ev.type == pygame.KEYDOWN:
                    if digitando:
                        if ev.key == pygame.K_RETURN or ev.key == pygame.K_ESCAPE:
                            digitando = False
                        elif ev.key == pygame.K_BACKSPACE:
                            nome = nome[:-1]
                        elif len(nome) < 20 and ev.unicode.isprintable():
                            nome += ev.unicode

                # ---- Mouse ----
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    # Clique no campo de nome
                    if campo_rect.collidepoint(ev.pos):
                        digitando = True
                        continue
                    # Clique fora do campo desativa digitação
                    if digitando:
                        digitando = False

                    # Navegação raça / vocação (só quando não digitando)
                    if btn_rp.clicado(ev): idx_raca    = (idx_raca    - 1) % len(racas)
                    if btn_rn.clicado(ev): idx_raca    = (idx_raca    + 1) % len(racas)
                    if btn_vp.clicado(ev): idx_vocacao = (idx_vocacao - 1) % len(vocacoes)
                    if btn_vn.clicado(ev): idx_vocacao = (idx_vocacao + 1) % len(vocacoes)
                    if btn_voltar.clicado(ev):
                        return None

                    # BUG CORRIGIDO: confirmar funciona independente do modo digitação
                    if btn_confirmar.clicado(ev) and nome.strip():
                        return {
                            "nome":    nome.strip(),
                            "raca":    racas[idx_raca],
                            "vocacao": vocacoes[idx_vocacao],
                        }

            raca    = racas[idx_raca]
            vocacao = vocacoes[idx_vocacao]

            self._limpar()

            # Título
            self._texto("Escolha sua Linhagem e Vocacao", LARGURA//2, 30,
                        COR_TITULO, self.fonte_subtitulo, centralizar=True)

            # Painel raça
            self._painel(LARGURA//2 - PW//2, CY, PW, 62)
            self._texto(f"Raca: {raca.nome}", LARGURA//2, CY + 8,
                        COR_DESTAQUE, self.fonte_texto, centralizar=True)
            self._texto(raca.resumo_modificadores(), LARGURA//2, CY + 34,
                        COR_TEXTO_FRACO, self.fonte_pequeno, centralizar=True)

            # Painel vocação
            self._painel(LARGURA//2 - PW//2, VY, PW, 62)
            self._texto(f"Vocacao: {vocacao.nome}", LARGURA//2, VY + 8,
                        COR_DESTAQUE, self.fonte_texto, centralizar=True)
            self._texto(vocacao.resumo_modificadores(), LARGURA//2, VY + 34,
                        COR_TEXTO_FRACO, self.fonte_pequeno, centralizar=True)

            # Campo de nome
            cor_borda_campo = CIANO if digitando else COR_BORDA
            pygame.draw.rect(self.tela, CINZA_MEDIO, campo_rect, border_radius=4)
            pygame.draw.rect(self.tela, cor_borda_campo, campo_rect, 2, border_radius=4)

            label    = (nome + "_") if digitando else (nome if nome else "Clique aqui para digitar o nome")
            cor_lbl  = BRANCO if nome else CINZA_FRACO
            surf_lbl = self.fonte_texto.render(label, True, cor_lbl)
            self.tela.blit(surf_lbl, surf_lbl.get_rect(
                midleft=(CAMPO_X + 10, CAMPO_Y + CAMPO_H // 2)))

            # Label acima do campo
            self._texto("Nome:", CAMPO_X, CAMPO_Y - 22, CINZA_TEXTO, self.fonte_pequeno)

            # Hint se nome vazio e não digitando
            if not nome and not digitando:
                self._texto("(necessario para iniciar)", LARGURA//2, CAMPO_Y + CAMPO_H + 6,
                            CINZA_FRACO, self.fonte_pequeno, centralizar=True)

            # Botões
            btn_confirmar.ativo = bool(nome.strip())
            for b in [btn_rp, btn_rn, btn_vp, btn_vn, btn_confirmar, btn_voltar]:
                b.atualizar(pos)
                b.desenhar(self.tela, self.fonte_texto)

            pygame.display.flip()
            self.clock.tick(FPS)

    # ------------------------------------------------------------------ #
    #  TELA: Narração de Cenário
    # ------------------------------------------------------------------ #

    def tela_narracao(self, titulo: str, subtitulo: str,
                      narrativa: str, jogador) -> str:
        self.iniciar_narracao(narrativa)

        btn_continuar  = Botao(LARGURA - 210, ALTURA - 60, 190, 40, "Continuar >")
        btn_inventario = Botao(MARGEM,        ALTURA - 60, 160, 40, "Inventario")
        btn_menu       = Botao(LARGURA//2 - 55,  ALTURA - 60, 110, 40, "Menu")

        while True:
            pos = pygame.mouse.get_pos()
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    return "sair"
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_SPACE:
                    if not self.narracao_concluida:
                        self.pular_narracao()
                if btn_continuar.clicado(ev) and self.narracao_concluida:
                    return "continuar"
                if btn_inventario.clicado(ev):
                    return "inventario"
                if btn_menu.clicado(ev):
                    return "sair"

            self._avancar_narracao()
            self._limpar()

            # Cabeçalho
            self._texto(titulo,    MARGEM, MARGEM + 10, COR_TITULO,    self.fonte_subtitulo)
            self._texto(subtitulo, MARGEM, MARGEM + 44, COR_SUBTITULO, self.fonte_pequeno)
            pygame.draw.line(self.tela, LARANJA_ESCURO,
                             (MARGEM, 80), (LARGURA - MARGEM, 80), 1)

            # HUD mini
            self._hud_mini(jogador)

            # Texto narrativo
            self._painel(NARRACAO_X, NARRACAO_Y, NARRACAO_LARGURA, NARRACAO_ALTURA)
            self._renderizar_bloco_texto(
                self._texto_exibido,
                NARRACAO_X + PADDING, NARRACAO_Y + PADDING,
                NARRACAO_LARGURA - PADDING * 2,
            )

            if not self.narracao_concluida:
                self._texto("[ESPACO para avancar]", LARGURA//2, ALTURA - 100,
                            CINZA_FRACO, self.fonte_pequeno, centralizar=True)

            btn_continuar.ativo = self.narracao_concluida
            for b in [btn_continuar, btn_inventario, btn_menu]:
                b.atualizar(pos)
                b.desenhar(self.tela, self.fonte_texto)

            pygame.display.flip()
            self.clock.tick(FPS)

    # ------------------------------------------------------------------ #
    #  TELA: Combate
    # ------------------------------------------------------------------ #

    def tela_combate(self, estado: dict, log: list,
                     habilidade_nome: str, tem_habilidade: bool,
                     inventario: list) -> str:
        btn_atacar = Botao(MARGEM, HUD_Y + 8, BOTAO_LARGURA, BOTAO_ALTURA, "Atacar")
        btn_habilidade = Botao(MARGEM + BOTAO_LARGURA + BOTAO_ESPACO, HUD_Y + 8,
                        BOTAO_LARGURA, BOTAO_ALTURA,
                        habilidade_nome, ativo=tem_habilidade)
        btn_fugir = Botao(MARGEM, HUD_Y + 8 + BOTAO_ALTURA + BOTAO_ESPACO,
                    BOTAO_LARGURA, BOTAO_ALTURA, "Fugir")

        # Equipáveis excluídos — não faz sentido equipar no meio do combate
        itens_usaveis = [it for it in inventario if not hasattr(it, "slot")][:4]
        botoes_itens  = []
        ix_col0 = MARGEM + (BOTAO_LARGURA + BOTAO_ESPACO) * 2
        ix_col1 = ix_col0 + BOTAO_LARGURA + 12
        _btn_item_w = BOTAO_LARGURA - 4
        for i, item in enumerate(itens_usaveis):
            col = i % 2
            row = i // 2
            bx  = ix_col0 if col == 0 else ix_col1
            by  = HUD_Y + 8 + row * (BOTAO_ALTURA + BOTAO_ESPACO)
            rotulo = item.nome[:14] + ("..." if len(item.nome) > 14 else "")
            b = Botao(bx, by, _btn_item_w, BOTAO_ALTURA, rotulo)
            botoes_itens.append((item.nome, b))

        while True:
            pos = pygame.mouse.get_pos()
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    return "fugir"
                if btn_atacar.clicado(ev):     return "atacar"
                if btn_habilidade.clicado(ev): return "habilidade"
                if btn_fugir.clicado(ev):      return "fugir"
                for nome_item, b in botoes_itens:
                    if b.clicado(ev):
                        return f"item_{nome_item}"

            self._limpar()

            # Status jogador
            self._painel(MARGEM, 10, LARGURA // 2 - MARGEM * 2, 85)
            j = estado["jogador"]
            self._texto(j["nome"], MARGEM + PADDING, 18, COR_DESTAQUE, self.fonte_hud)
            self._texto(f"Nv.{j['nivel']}", 280, 18, CINZA_TEXTO, self.fonte_pequeno)
            self._barra(MARGEM + PADDING, 44, 220, 14,
                        j["vida_atual"], j["vida_max"],
                        self._cor_hp(j["vida_atual"], j["vida_max"]))
            self._texto(f"{j['vida_atual']}/{j['vida_max']} HP",
                        MARGEM + PADDING, 62, CINZA_TEXTO, self.fonte_pequeno)

            # Status inimigo
            ini = estado["inimigo"]
            px  = LARGURA // 2 + MARGEM
            self._painel(px, 10, LARGURA // 2 - MARGEM * 2, 85)
            self._texto(ini["nome"], px + PADDING, 18, VERMELHO_CLARO, self.fonte_hud)
            fase = ini.get("fase")
            if fase:
                self._texto(f"Fase {fase}/3", px + 200, 18, AMARELO, self.fonte_pequeno)
            self._barra(px + PADDING, 44, 220, 14,
                        ini["vida_atual"], ini["vida_max"],
                        self._cor_hp(ini["vida_atual"], ini["vida_max"]))
            self._texto(f"{ini['vida_atual']}/{ini['vida_max']} HP",
                        px + PADDING, 62, CINZA_TEXTO, self.fonte_pequeno)

            # Log de combate — full-width, abaixo dos painéis de status
            _LX = MARGEM                        # começa na margem esquerda
            _LY = LOG_Y                         # mesma y de sempre (100px)
            _LW = LARGURA - 2 * MARGEM          # 860px — largura total
            _LH = LOG_ALTURA                    # altura inalterada

            self._painel(_LX, _LY, _LW, _LH)

            # Aplica clipping para texto nunca vazar do painel
            _clip = pygame.Rect(_LX + PADDING, _LY + PADDING,
                                _LW - PADDING * 2, _LH - PADDING * 2)
            self.tela.set_clip(_clip)

            _txt_w     = _LW - PADDING * 2
            _linha_h   = self.fonte_pequeno.get_height() + 3   # altura de cada linha
            _sep_h     = self.fonte_pequeno.get_height() + 2   # altura do separador
            _area_h    = _LH - PADDING * 2                     # altura útil do painel

            # ── Pré-processa todas as entradas do log em blocos renderizáveis ──
            # Cada bloco: (tipo, texto, cor)  tipo="sep"|"linha"
            def _cor_linha(txt):
                lu = txt.upper()
                if "CRITICO" in lu:                                  return AMARELO_CLARO
                if "DANO" in lu or "CAUSOU" in lu:                  return VERMELHO_CLARO
                if any(p in lu for p in ["CUROU","RECUPERA","CURA","VIDA"]): return VERDE_CLARO
                if any(p in lu for p in ["HACK","ESCUDO","IMPROVISADO","TIRO DUPLO"]): return CIANO_CLARO
                return CINZA_TEXTO

            blocos = []   # lista de (altura_px, render_fn) — construída de trás pra frente
            turno_visto = set()

            for entrada in reversed(log):
                if isinstance(entrada, dict):
                    num_turno = entrada.get("turno", 0)
                    linhas_ev = entrada.get("linhas", [])
                else:
                    num_turno = 0
                    linhas_ev = [entrada]

                # Linhas do evento (em ordem reversa para empilhar de baixo)
                for linha in reversed(linhas_ev):
                    subs = self._wrap_texto(linha, _txt_w, self.fonte_pequeno)
                    cor  = _cor_linha(linha)
                    for sub in reversed(subs):
                        blocos.append((_linha_h, sub, cor))

                # Separador de turno (uma vez por turno, acima das linhas do evento)
                if num_turno > 0 and num_turno not in turno_visto:
                    turno_visto.add(num_turno)
                    sep_txt = f"─── Turno {num_turno} " + "─" * 38
                    blocos.append((_sep_h, sep_txt, CINZA_FRACO))

            # ── Calcula quantos blocos cabem de baixo para cima ──
            altura_usada = 0
            blocos_visiveis = []
            for bloco in blocos:
                if altura_usada + bloco[0] > _area_h:
                    break
                blocos_visiveis.append(bloco)
                altura_usada += bloco[0]

            # ── Renderiza de baixo para cima ──
            y_cur = _LY + _LH - PADDING   # começa na base do painel
            for (h, txt, cor) in blocos_visiveis:
                y_cur -= h
                surf = self.fonte_pequeno.render(txt, True, cor)
                self.tela.blit(surf, (_LX + PADDING, y_cur))

            self.tela.set_clip(None)

            # Turno — dentro do painel do jogador, canto inferior direito
            # Fica em x < LOG_X (470) para nunca vazar sobre o log
            _borda_esq = MARGEM + (LARGURA // 2 - MARGEM * 2) - PADDING
            self._texto(f"T:{estado['turno']}", _borda_esq, 62,
                        CINZA_FRACO, self.fonte_pequeno)

            # HUD ações
            self._painel(MARGEM - 4, HUD_Y - 4,
                         LARGURA - MARGEM * 2 + 8, HUD_ALTURA + 8)
            for b in [btn_atacar, btn_habilidade, btn_fugir]:
                b.atualizar(pos)
                b.desenhar(self.tela, self.fonte_texto)
            for _, b in botoes_itens:
                b.atualizar(pos)
                b.desenhar(self.tela, self.fonte_pequeno)

            pygame.display.flip()
            self.clock.tick(FPS)

    # ------------------------------------------------------------------ #
    #  TELA: Desafio
    # ------------------------------------------------------------------ #

    def tela_desafio(self, narrativa: str, pede_input: bool = False,
                     placeholder: str = "Digite sua resposta...") -> str:
        entrada  = ""
        digitando = pede_input

        # Rótulos mudam conforme o tipo de desafio
        _label_confirmar = "Confirmar" if pede_input else "Arriscar"
        _label_pular     = "Achar outro caminho"
        btn_confirmar = Botao(LARGURA//2 - 130, ALTURA - 70, 210, 40, _label_confirmar)
        btn_pular     = Botao(LARGURA - 230,    ALTURA - 70, 210, 40, _label_pular)

        while True:
            pos = pygame.mouse.get_pos()
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    return "pular"
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        return "pular"
                    if digitando:
                        if ev.key == pygame.K_RETURN:
                            return entrada
                        elif ev.key == pygame.K_BACKSPACE:
                            entrada = entrada[:-1]
                        elif len(entrada) < 40 and ev.unicode.isprintable():
                            entrada += ev.unicode
                if btn_confirmar.clicado(ev): return entrada
                if btn_pular.clicado(ev):     return "pular"

            self._limpar()
            self._texto("Desafio", LARGURA//2, 20, COR_TITULO,
                        self.fonte_subtitulo, centralizar=True)
            pygame.draw.line(self.tela, LARANJA_ESCURO,
                             (MARGEM, 60), (LARGURA - MARGEM, 60), 1)

            self._painel(MARGEM, 70, LARGURA - 2*MARGEM, ALTURA - 200)
            self._renderizar_bloco_texto(narrativa, MARGEM + PADDING, 82,
                                         LARGURA - 2*MARGEM - PADDING*2,
                                         cor=COR_TEXTO)

            if pede_input:
                pygame.draw.rect(self.tela, CINZA_MEDIO,
                                 (MARGEM, ALTURA-130, LARGURA-2*MARGEM, 42), border_radius=4)
                pygame.draw.rect(self.tela, CIANO,
                                 (MARGEM, ALTURA-130, LARGURA-2*MARGEM, 42), 2, border_radius=4)
                texto_campo = (entrada + "_") if entrada else placeholder
                self._texto(texto_campo, MARGEM + PADDING, ALTURA - 122,
                            BRANCO if entrada else CINZA_FRACO, self.fonte_texto)

            for b in [btn_confirmar, btn_pular]:
                b.atualizar(pos)
                b.desenhar(self.tela, self.fonte_texto)

            pygame.display.flip()
            self.clock.tick(FPS)

    # ------------------------------------------------------------------ #
    #  TELA: Inventário
    # ------------------------------------------------------------------ #

    def tela_inventario(self, jogador) -> str:
        """
        Inventário completo com:
        - Painel de status do personagem (HP, XP, atributos, raça/vocação)
        - Seção de equipamentos ativos (arma e armadura)
        - Lista de itens com botão [Equipar]/[Desequipar]/[Usar] por tipo
        """
        btn_voltar = Botao(MARGEM, ALTURA - 56, 140, 40, "Voltar")

        while True:
            pos       = pygame.mouse.get_pos()
            inventario = jogador.inventario

            # Botões por item — rótulo e ação dependem do tipo
            botoes_item = []
            for i, item in enumerate(inventario):
                eq = hasattr(item, "slot")   # é ItemEquipavel?
                if eq:
                    rotulo = "Desequipar" if item.esta_equipado else "Equipar"
                    ativo  = True
                else:
                    rotulo = "Usar"
                    ativo  = item.consumivel
                b = Botao(LARGURA - MARGEM - 150, 274 + i * 52, 150, 36, rotulo, ativo=ativo)
                botoes_item.append(b)

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    return "voltar"
                if btn_voltar.clicado(ev):
                    return "voltar"
                for i, b in enumerate(botoes_item):
                    if b.clicado(ev) and i < len(inventario):
                        jogador.usar_item(inventario[i].nome)
                        break

            self._limpar()

            # ── Título ────────────────────────────────────────────────────
            self._texto("Inventario", LARGURA//2, 14, COR_TITULO,
                        self.fonte_subtitulo, centralizar=True)
            pygame.draw.line(self.tela, LARANJA_ESCURO, (MARGEM, 50), (LARGURA-MARGEM, 50), 1)

            # ── Painel de status ──────────────────────────────────────────
            STATUS_W = 340
            self._painel(MARGEM, 58, STATUS_W, 130)
            self._texto(jogador.nome, MARGEM + PADDING, 66, COR_DESTAQUE, self.fonte_hud)
            self._texto(f"Nivel {jogador.nivel}",
                        MARGEM + STATUS_W - PADDING - 80, 66, CIANO, self.fonte_pequeno)
            self._barra(MARGEM + PADDING, 94, STATUS_W - PADDING*2, 10,
                        jogador.vida_atual, jogador.vida_maxima,
                        self._cor_hp(jogador.vida_atual, jogador.vida_maxima))
            self._texto(f"{jogador.vida_atual}/{jogador.vida_maxima} HP",
                        MARGEM + PADDING, 108, CINZA_TEXTO, self.fonte_pequeno)
            xp_prox = jogador.nivel * jogador.XP_POR_NIVEL
            self._barra(MARGEM + PADDING, 128, STATUS_W - PADDING*2, 8,
                        jogador.xp, xp_prox, CIANO_ESCURO)
            self._texto(f"XP: {jogador.xp}/{xp_prox}",
                        MARGEM + PADDING, 140, CINZA_TEXTO, self.fonte_pequeno)
            self._texto(f"Celulas: {jogador.celulas_fusao}",
                        MARGEM + PADDING, 160, AMARELO, self.fonte_pequeno)

            # ── Painel de atributos ───────────────────────────────────────
            ATTR_X = MARGEM + STATUS_W + 12
            ATTR_W = LARGURA - ATTR_X - MARGEM
            self._painel(ATTR_X, 58, ATTR_W, 130)
            self._texto("Atributos", ATTR_X + PADDING, 66, COR_TITULO, self.fonte_pequeno)
            for idx, (label, valor, cor_a) in enumerate([
                ("Poder",   jogador.poder,   VERMELHO_CLARO),
                ("Defesa",  jogador.defesa,  CIANO_CLARO),
                ("Esquiva", jogador.esquiva, VERDE_CLARO),
            ]):
                ax = ATTR_X + PADDING + idx * (ATTR_W // 3)
                self._texto(label, ax, 88, CINZA_TEXTO, self.fonte_pequeno)
                self._texto(str(valor), ax, 108, cor_a, self.fonte_subtitulo)
            self._texto(f"{jogador.raca.nome} / {jogador.vocacao.nome}",
                        ATTR_X + PADDING, 150, CINZA_TEXTO, self.fonte_pequeno)

            # ── Equipamentos ativos ───────────────────────────────────────
            EQ_Y = 196
            self._texto("Equipamentos:", MARGEM, EQ_Y, COR_SUBTITULO, self.fonte_pequeno)
            for idx_s, slot in enumerate(("arma", "armadura")):
                item_eq = jogador.equipamentos.get(slot)
                ex      = MARGEM + idx_s * ((LARGURA - 2*MARGEM) // 2 + 6)
                ew      = (LARGURA - 2*MARGEM) // 2 - 6
                self._painel(ex, EQ_Y + 18, ew, 32,
                             borda=(LARANJA_ESCURO if item_eq else COR_BORDA))
                label_slot = slot.upper()
                if item_eq:
                    txt = f"{label_slot}: {item_eq.nome}"
                    self._texto(txt, ex + PADDING, EQ_Y + 26, LARANJA, self.fonte_pequeno)
                else:
                    self._texto(f"{label_slot}: — vazio —",
                                ex + PADDING, EQ_Y + 26, CINZA_FRACO, self.fonte_pequeno)

            # ── Divisor e lista de itens ──────────────────────────────────
            pygame.draw.line(self.tela, LARANJA_ESCURO,
                             (MARGEM, 252), (LARGURA-MARGEM, 252), 1)
            self._texto("Itens:", MARGEM, 258, COR_SUBTITULO, self.fonte_pequeno)

            if not inventario:
                self._texto("Inventario vazio.", LARGURA//2, 300,
                            CINZA_FRACO, self.fonte_texto, centralizar=True)
            else:
                for i, item in enumerate(inventario):
                    y = 272 + i * 52
                    if y + 48 > ALTURA - 70:
                        break   # não vaza fora da tela
                    eq = hasattr(item, "slot")
                    equipado = eq and item.esta_equipado
                    cor_borda_item = LARANJA_ESCURO if equipado else COR_BORDA
                    self._painel(MARGEM, y - 2, LARGURA - 2*MARGEM, 46,
                                 borda=cor_borda_item)
                    cor_rar = COR_RARIDADE.get(item.raridade, CINZA_TEXTO)
                    tag = "[EQUIPADO]" if equipado else f"[{item.raridade.upper()}]"
                    self._texto(tag, MARGEM + PADDING, y + 4, cor_rar, self.fonte_pequeno)
                    self._texto(item.nome, MARGEM + 120, y + 4, COR_TEXTO, self.fonte_texto)
                    # Sub-info: descrição ou bônus de equipamento
                    if eq:
                        sub = item.resumo_mods()
                    else:
                        sub = item.descricao
                    self._texto(sub, MARGEM + 120, y + 24, CINZA_TEXTO, self.fonte_pequeno)
                    botoes_item[i].atualizar(pos)
                    botoes_item[i].desenhar(self.tela, self.fonte_pequeno)

            btn_voltar.atualizar(pos)
            btn_voltar.desenhar(self.tela, self.fonte_texto)
            pygame.display.flip()
            self.clock.tick(FPS)

    # ------------------------------------------------------------------ #
    #  TELA: Resultado rápido (mensagem intermediária)
    # ------------------------------------------------------------------ #

    def tela_resultado(self, titulo: str, mensagem: str,
                       cor_titulo=COR_DESTAQUE) -> None:
        btn = Botao(LARGURA//2 - 90, ALTURA - 80, 180, 44, "Continuar")

        while True:
            pos = pygame.mouse.get_pos()
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    return
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_RETURN:
                    return
                if btn.clicado(ev):
                    return

            self._limpar()
            self._texto(titulo, LARGURA//2, MARGEM + 15,
                        cor_titulo, self.fonte_titulo, centralizar=True)
            _panel_y = MARGEM + 62
            _panel_h = ALTURA - _panel_y - 90
            self._painel(MARGEM * 2, _panel_y, LARGURA - MARGEM * 4, _panel_h)
            clip_rect = pygame.Rect(MARGEM * 2 + PADDING, _panel_y + PADDING,
                                    LARGURA - MARGEM * 4 - PADDING * 2,
                                    _panel_h - PADDING * 2)
            self.tela.set_clip(clip_rect)
            self._renderizar_bloco_texto(mensagem,
                                          MARGEM * 2 + PADDING,
                                          _panel_y + PADDING,
                                          LARGURA - MARGEM * 4 - PADDING * 2,
                                          cor=COR_TEXTO)
            self.tela.set_clip(None)
            btn.atualizar(pos)
            btn.desenhar(self.tela, self.fonte_texto)
            pygame.display.flip()
            self.clock.tick(FPS)

    # ------------------------------------------------------------------ #
    #  TELA: Game Over / Vitória
    # ------------------------------------------------------------------ #

    def tela_game_over(self) -> str:
        return self._tela_fim("GAME OVER",
                              "Voce caiu no deserto de silicio.",
                              VERMELHO, "Tentar Novamente", "Menu Principal")

    def tela_fim_covarde(self) -> str:
        """
        Tela especial exibida quando o jogador foge do Xerife de Ferro.
        Narrativa de derrota moral — o Código Fonte permanece preso.
        """
        return self._tela_fim(
            "FIM DO COVARDE",
            "Voce virou as costas para o Xerife de Ferro e fugiu.\n\n"            "O Codigo Fonte permanece preso na Torre do Silicio.\n"            "O deserto nunca soube seu nome — e nao vai saber.",
            CINZA_FRACO,
            "Tentar de Novo",
            "Menu Principal",
        )

    def tela_vitoria(self) -> str:
        return self._tela_fim(
            "VITORIA",
            "O Xerife de Ferro caiu. O Codigo Fonte esta livre.\n"
            "O deserto de silicio nunca mais sera o mesmo.",
            VERDE, "Nova Jornada", "Menu Principal",
        )

    def _tela_fim(self, titulo, subtitulo, cor_titulo, op1, op2) -> str:
        btn1 = Botao(LARGURA//2 - 130, ALTURA//2 + 60,  240, 48, op1)
        btn2 = Botao(LARGURA//2 - 130, ALTURA//2 + 120, 240, 48, op2)

        while True:
            pos = pygame.mouse.get_pos()
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    return "menu"
                if btn1.clicado(ev): return "reiniciar"
                if btn2.clicado(ev): return "menu"

            self._limpar()
            self._texto(titulo, LARGURA//2, ALTURA//2 - 80,
                        cor_titulo, self.fonte_titulo, centralizar=True)
            self._renderizar_bloco_texto(subtitulo, MARGEM * 4, ALTURA//2 - 20,
                                          LARGURA - MARGEM * 8, cor=COR_TEXTO)
            for b in [btn1, btn2]:
                b.atualizar(pos)
                b.desenhar(self.tela, self.fonte_texto)
            pygame.display.flip()
            self.clock.tick(FPS)

    # ------------------------------------------------------------------ #
    #  HUD mini (narração)
    # ------------------------------------------------------------------ #

    def _hud_mini(self, jogador) -> None:
        x = LARGURA - 220
        self._painel(x, 4, 210, 72, COR_PAINEL)
        self._texto(jogador.nome, x + 8, 10, COR_DESTAQUE, self.fonte_pequeno)
        self._texto(f"Nv.{jogador.nivel}", x + 160, 10, CINZA_TEXTO, self.fonte_pequeno)
        self._barra(x + 8, 32, 192, 10,
                    jogador.vida_atual, jogador.vida_maxima,
                    self._cor_hp(jogador.vida_atual, jogador.vida_maxima))
        self._texto(f"{jogador.vida_atual}/{jogador.vida_maxima} HP",
                    x + 8, 46, CINZA_TEXTO, self.fonte_pequeno)
        self._texto(f"{jogador.celulas_fusao} cel.",
                    x + 130, 46, AMARELO, self.fonte_pequeno)


    # ------------------------------------------------------------------ #
    #  TELA: Exploração — menu de escolha dentro do cenário
    # ------------------------------------------------------------------ #

    def tela_exploracao(self, nome_cenario: str, subtitulo: str,
                        descricao_situacao: str, jogador,
                        exploracoes_feitas: int,
                        exploracoes_minimas: int,
                        exploracoes_disponiveis: int) -> str:
        """
        Menu principal de exploração dentro de um cenário.
        O jogador escolhe o que fazer a cada momento.

        Retorna:
          "explorar"   — jogador quer explorar a área
          "avancar"    — jogador quer ir para o próximo evento/saída
          "inventario" — abre o inventário
          "sair"       — volta ao menu principal
        """
        pode_explorar = exploracoes_feitas < exploracoes_disponiveis
        pode_avancar  = exploracoes_feitas >= exploracoes_minimas

        # Botões de ação
        BW, BH = 220, 50    # largura e altura dos botões principais
        BX = LARGURA // 2 - BW // 2
        btn_explorar   = Botao(BX, 410, BW, BH, "[ Explorar Area ]",  ativo=pode_explorar)
        btn_avancar    = Botao(BX, 472, BW, BH, "[ Avancar ]",        ativo=pode_avancar)
        btn_inventario = Botao(MARGEM, ALTURA - 56, 150, 36, "Inventario")
        btn_menu       = Botao(LARGURA - 150 - MARGEM, ALTURA - 56, 150, 36, "Menu")

        while True:
            pos = pygame.mouse.get_pos()
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    return "sair"
                if btn_explorar.clicado(ev):
                    return "explorar"
                if btn_avancar.clicado(ev):
                    return "avancar"
                if btn_inventario.clicado(ev):
                    return "inventario"
                if btn_menu.clicado(ev):
                    return "sair"

            self._limpar()

            # --- Cabeçalho ---
            self._texto(nome_cenario, MARGEM, MARGEM + 8,
                        COR_TITULO, self.fonte_subtitulo)
            self._texto(subtitulo, MARGEM, MARGEM + 42,
                        COR_SUBTITULO, self.fonte_pequeno)
            pygame.draw.line(self.tela, LARANJA_ESCURO,
                             (MARGEM, 78), (LARGURA - MARGEM, 78), 1)

            # --- HUD mini do jogador ---
            self._hud_mini(jogador)

            # --- Painel de situação narrativa ---
            self._painel(MARGEM, 88, LARGURA - 2 * MARGEM, 260)
            self._renderizar_bloco_texto(
                descricao_situacao,
                MARGEM + PADDING, 98,
                LARGURA - 2 * MARGEM - PADDING * 2,
                cor=COR_NARRACAO,
            )

            # --- Contador de exploração ---
            # Barra de progresso visual
            BAR_X = MARGEM
            BAR_Y = 340
            BAR_W = LARGURA - 2 * MARGEM
            BAR_H = 10
            pygame.draw.rect(self.tela, CINZA_MEDIO,
                             (BAR_X, BAR_Y, BAR_W, BAR_H), border_radius=3)
            if exploracoes_disponiveis > 0:
                # Progresso geral (cinza claro)
                fill_total = int(BAR_W * exploracoes_feitas / exploracoes_disponiveis)
                if fill_total > 0:
                    pygame.draw.rect(self.tela, CINZA_TEXTO,
                                     (BAR_X, BAR_Y, fill_total, BAR_H), border_radius=3)
                # Marcador do mínimo necessário (laranja)
                if exploracoes_minimas > 0:
                    x_min = int(BAR_W * exploracoes_minimas / exploracoes_disponiveis)
                    pygame.draw.rect(self.tela, LARANJA,
                                     (BAR_X + x_min - 2, BAR_Y - 3, 4, BAR_H + 6))
            pygame.draw.rect(self.tela, COR_BORDA,
                             (BAR_X, BAR_Y, BAR_W, BAR_H), 1, border_radius=3)

            # Texto do contador
            if exploracoes_minimas > 0 and not pode_avancar:
                texto_prog = (f"Explorado: {exploracoes_feitas} / {exploracoes_disponiveis}"
                              f"  |  minimo para avancar: {exploracoes_minimas}")
                cor_prog   = LARANJA
            else:
                texto_prog = (f"Explorado: {exploracoes_feitas} / {exploracoes_disponiveis}"
                              + ("  |  Caminho encontrado!" if exploracoes_minimas > 0 else ""))
                cor_prog   = VERDE if pode_avancar else CINZA_TEXTO
            self._texto(texto_prog, LARGURA // 2, BAR_Y + 14,
                        cor_prog, self.fonte_pequeno, centralizar=True)

            # --- Hint quando não pode avançar ainda ---
            if not pode_avancar and exploracoes_minimas > 0:
                faltam = exploracoes_minimas - exploracoes_feitas
                hint = f"Explore mais {faltam}x para encontrar o caminho de saida."
                self._texto(hint, LARGURA // 2, BAR_Y + 32,
                            CINZA_FRACO, self.fonte_pequeno, centralizar=True)

            # --- Hint quando não pode mais explorar ---
            if not pode_explorar:
                self._texto("Nao ha mais o que explorar aqui.",
                            LARGURA // 2, BAR_Y + 32,
                            CINZA_FRACO, self.fonte_pequeno, centralizar=True)

            # --- Botões de ação ---
            for b in [btn_explorar, btn_avancar, btn_inventario, btn_menu]:
                b.atualizar(pos)
                b.desenhar(self.tela, self.fonte_texto)

            pygame.display.flip()
            self.clock.tick(FPS)

    # ------------------------------------------------------------------ #
    #  TELA: Guardião de Passagem — NPC que bloqueia a saída do cenário
    # ------------------------------------------------------------------ #

    def tela_guardiao(self, narrativa_guardiao: str, custo_tipo: str,
                      custo_valor, jogador) -> str:
        """
        Apresenta o NPC guardião com suas opções de passagem.

        custo_tipo : "celulas" | "vida" | "item"
        custo_valor: int (células ou % de vida) | int (qtd de itens)

        Retorna:
          "resolver"          — jogador quer tentar o enigma
          "pagar"             — jogador aceita pagar o custo (cells/vida)
          "pagar_NOME_ITEM"   — jogador escolhe item específico (custo_tipo == "item")
          "voltar"            — jogador volta para a exploração
        """
        # Monta label do botão de custo com base no tipo
        if custo_tipo == "celulas":
            label_pagar = f"Pagar {custo_valor} Celulas"
            pode_pagar  = jogador.celulas_fusao >= custo_valor
        elif custo_tipo == "vida":
            custo_vida  = max(1, int(jogador.vida_atual * custo_valor / 100))
            label_pagar = f"Pagar {custo_valor}% da vida ({custo_vida} HP)"
            pode_pagar  = jogador.vida_atual > custo_vida   # não deixa morrer pagando
        else:  # "item"
            label_pagar = "Entregar um Item"
            pode_pagar  = len(jogador.inventario) > 0

        # Estado interno: se está mostrando o sub-menu de itens
        modo_item = False

        BW, BH = 260, 46
        BX = LARGURA // 2 - BW // 2
        btn_resolver = Botao(BX, 420, BW, BH, "Resolver o Enigma")
        btn_pagar    = Botao(BX, 480, BW, BH, label_pagar, ativo=pode_pagar)
        btn_voltar   = Botao(MARGEM, ALTURA - 56, 130, 36, "Voltar")

        # Botões de itens (para custo_tipo == "item")
        # Reconstruídos a cada frame para refletir inventário atual
        self.iniciar_narracao(narrativa_guardiao)

        while True:
            pos = pygame.mouse.get_pos()
            inventario = jogador.inventario

            # Botões de item — só usados se modo_item == True
            botoes_itens = []
            if custo_tipo == "item" and modo_item:
                for i, item in enumerate(inventario[:5]):  # máx 5 visíveis
                    rotulo = item.nome[:22] + ("..." if len(item.nome) > 22 else "")
                    b = Botao(BX - 20, 300 + i * 48, BW + 40, 40, rotulo)
                    botoes_itens.append((item.nome, b))

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    return "voltar"

                # Espaço avança narração
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_SPACE:
                    if not self.narracao_concluida:
                        self.pular_narracao()

                if btn_resolver.clicado(ev):
                    return "resolver"

                if btn_pagar.clicado(ev) and pode_pagar:
                    if custo_tipo == "item":
                        if len(inventario) == 0:
                            pass
                        elif len(inventario) == 1:
                            # Só um item: entrega direto
                            return f"pagar_{inventario[0].nome}"
                        else:
                            # Abre sub-menu de seleção
                            modo_item = not modo_item
                    else:
                        return "pagar"

                if btn_voltar.clicado(ev):
                    return "voltar"

                # Clique em item do sub-menu
                for nome_item, b in botoes_itens:
                    if b.clicado(ev):
                        return f"pagar_{nome_item}"

            self._avancar_narracao()
            self._limpar()

            # --- Cabeçalho ---
            self._texto("Passagem Bloqueada", MARGEM, MARGEM + 8,
                        VERMELHO_CLARO, self.fonte_subtitulo)
            pygame.draw.line(self.tela, LARANJA_ESCURO,
                             (MARGEM, 52), (LARGURA - MARGEM, 52), 1)

            # --- Narrativa do guardião (máquina de escrever) ---
            # Painel narrativo: começa abaixo do HUD mini (altura 76px)
            _narr_y = 80
            _narr_h = 320
            self._painel(MARGEM, _narr_y, LARGURA - 2 * MARGEM, _narr_h)
            # HUD mini termina em y≈76, painel começa em y=80 — sem sobreposição
            # Usa largura total do painel
            _txt_w = LARGURA - 2 * MARGEM - 2 * PADDING
            self._renderizar_bloco_texto(
                self._texto_exibido,
                MARGEM + PADDING, _narr_y + PADDING,
                _txt_w,
                cor=COR_NARRACAO,
            )
            if not self.narracao_concluida:
                self._texto("[ESPACO para avancar]", LARGURA // 2, _narr_y + _narr_h - 22,
                            CINZA_FRACO, self.fonte_pequeno, centralizar=True)

            # --- Status do jogador (referência para a decisão) ---
            # HUD mini no canto superior direito
            self._hud_mini(jogador)
            # --- Sub-menu de itens (se ativo) ---
            if modo_item and custo_tipo == "item":
                self._painel(BX - 24, 288, BW + 48, len(botoes_itens) * 48 + 12,
                             CINZA_PAINEL, LARANJA_ESCURO)
                self._texto("Escolha o item a entregar:",
                            LARGURA // 2, 292,
                            LARANJA, self.fonte_pequeno, centralizar=True)
                for _, b in botoes_itens:
                    b.atualizar(pos)
                    b.desenhar(self.tela, self.fonte_pequeno)

            # --- Botões principais (só aparecem se sub-menu fechado) ---
            if not modo_item:
                btn_resolver.atualizar(pos)
                btn_resolver.desenhar(self.tela, self.fonte_texto)
                btn_pagar.atualizar(pos)
                btn_pagar.desenhar(self.tela, self.fonte_texto)

            btn_voltar.atualizar(pos)
            btn_voltar.desenhar(self.tela, self.fonte_texto)

            pygame.display.flip()
            self.clock.tick(FPS)


    # ------------------------------------------------------------------ #
    #  Encerramento
    # ------------------------------------------------------------------ #

    def encerrar(self) -> None:
        pygame.quit()