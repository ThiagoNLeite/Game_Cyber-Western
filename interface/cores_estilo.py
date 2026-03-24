"""
Paleta de cores e constantes visuais do jogo Cyber-Western.
Estética: neon sobre preto — laranja enferrujado, ciano elétrico, vermelho plasma.
Todas as constantes são tuplas RGB para uso direto com pygame.
"""

# ------------------------------------------------------------------ #
#  Dimensões da janela
# ------------------------------------------------------------------ #

LARGURA  = 900
ALTURA   = 600
FPS      = 60
TITULO   = "Deserto de Silício — RPG Cyber-Western"

# ------------------------------------------------------------------ #
#  Paleta principal
# ------------------------------------------------------------------ #

# Fundos
PRETO          = (0,   0,   0)
CINZA_ESCURO   = (18,  18,  18)
CINZA_MEDIO    = (35,  35,  35)
CINZA_PAINEL   = (25,  25,  30)

# Texto
BRANCO         = (255, 255, 255)
CINZA_TEXTO    = (180, 180, 180)
CINZA_FRACO    = (100, 100, 100)

# Primária — laranja enferrujado
LARANJA        = (210, 120,  30)
LARANJA_CLARO  = (240, 160,  60)
LARANJA_ESCURO = (140,  70,  10)

# Secundária — ciano elétrico
CIANO          = ( 30, 200, 210)
CIANO_CLARO    = ( 80, 230, 240)
CIANO_ESCURO   = ( 10, 120, 130)

# Acento — vermelho plasma
VERMELHO       = (200,  40,  40)
VERMELHO_CLARO = (240,  80,  80)
VERMELHO_ESCURO= (120,  15,  15)

# Verde — vida / sucesso
VERDE          = ( 60, 200,  80)
VERDE_CLARO    = (100, 230, 120)
VERDE_ESCURO   = ( 20, 100,  30)

# Amarelo — alerta / crítico
AMARELO        = (240, 200,  40)
AMARELO_CLARO  = (255, 230,  80)

# Roxo — raridade rara
ROXO           = (160,  60, 220)
ROXO_CLARO     = (200, 110, 255)

# ------------------------------------------------------------------ #
#  Cores semânticas (alias)
# ------------------------------------------------------------------ #

COR_FUNDO          = CINZA_ESCURO
COR_PAINEL         = CINZA_PAINEL
COR_BORDA          = CINZA_MEDIO
COR_TEXTO          = BRANCO
COR_TEXTO_FRACO    = CINZA_TEXTO
COR_DESTAQUE       = LARANJA
COR_TITULO         = CIANO_CLARO
COR_SUBTITULO      = LARANJA_CLARO
COR_NARRACAO       = CINZA_TEXTO

COR_HP_CHEIO       = VERDE
COR_HP_MEDIO       = AMARELO
COR_HP_BAIXO       = VERMELHO

COR_CRITICO        = AMARELO_CLARO
COR_DANO           = VERMELHO_CLARO
COR_CURA           = VERDE_CLARO
COR_BUFF           = CIANO_CLARO

COR_BOTAO          = CINZA_MEDIO
COR_BOTAO_HOVER    = LARANJA_ESCURO
COR_BOTAO_ATIVO    = LARANJA
COR_BOTAO_TEXTO    = BRANCO
COR_BOTAO_DISABLED = CINZA_FRACO

COR_RARIDADE = {
    "comum":   CINZA_TEXTO,
    "incomum": VERDE_CLARO,
    "raro":    ROXO_CLARO,
}

# ------------------------------------------------------------------ #
#  Tamanhos de fonte
# ------------------------------------------------------------------ #

FONTE_TITULO    = 36
FONTE_SUBTITULO = 24
FONTE_TEXTO     = 18
FONTE_PEQUENO   = 14
FONTE_HUD       = 16

# ------------------------------------------------------------------ #
#  Margens e espaçamentos
# ------------------------------------------------------------------ #

MARGEM          = 20
PADDING         = 12
RAIO_BORDA      = 6       # border_radius dos retângulos arredondados
ESPESSURA_BORDA = 2

# ------------------------------------------------------------------ #
#  Constantes de layout das telas
# ------------------------------------------------------------------ #

# Área de narração (tela de cenário)
NARRACAO_X      = MARGEM
NARRACAO_Y      = 80
NARRACAO_LARGURA = LARGURA - 2 * MARGEM
NARRACAO_ALTURA  = ALTURA - 200

# HUD de combate
HUD_ALTURA       = 110
HUD_Y            = ALTURA - HUD_ALTURA - MARGEM

# Painel de log de combate
LOG_X            = LARGURA // 2 + MARGEM
LOG_Y            = 100
LOG_LARGURA      = LARGURA // 2 - 2 * MARGEM
LOG_ALTURA       = HUD_Y - LOG_Y - MARGEM        # 350px — termina antes do HUD

# Botões de ação (combate)
BOTAO_LARGURA    = 160
BOTAO_ALTURA     = 38
BOTAO_ESPACO     = 10