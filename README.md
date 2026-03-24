# Deserto de Silício — RPG Cyber-Western

> *"No ano 2245, após O Grande Curto destruir 90% da tecnologia conhecida, o planeta-colônia Nova Fronteira sobrevive à beira do colapso. Em algum lugar no deserto, a Torre do Silício guarda o Código Fonte — e você é o único louco o suficiente para ir atrás."*

Trabalho acadêmico de **Programação Orientada a Objetos** — RPG de turnos com interface gráfica em pygame, demonstrando herança, polimorfismo, encapsulamento e classes abstratas em Python.

---

## Sumário

- [Sobre o Projeto](#sobre-o-projeto)
- [Tecnologias](#tecnologias)
- [Como Executar](#como-executar)
- [Como Jogar](#como-jogar)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Arquitetura POO](#arquitetura-poo)
- [Mecânicas de Jogo](#mecânicas-de-jogo)
- [Testes](#testes)
- [Ferramentas de Debug](#ferramentas-de-debug)
- [Equipe](#equipe)

---

## Sobre o Projeto

**Deserto de Silício** é um RPG narrativo de turnos ambientado em um universo Cyber-Western pós-apocalíptico. O jogador cria um personagem combinando raça e vocação, explora 6 cenários progressivos, enfrenta 15 inimigos únicos e um boss com 3 fases, e toma decisões que afetam recursos e progressão.

O projeto foi desenvolvido como trabalho da disciplina de POO, com foco explícito em demonstrar os quatro pilares da orientação a objetos através de uma aplicação interativa completa.

---

## Tecnologias

| Tecnologia | Versão | Uso |
|---|---|---|
| Python | 3.12+ | Linguagem principal |
| pygame | 2.6+ | Interface gráfica e loop de jogo |
| unittest | stdlib | Suite de testes (92 testes) |
| json | stdlib | Persistência de dados e saves |
| logging | stdlib | Sistema de debug e balanceamento |
| abc | stdlib | Classes abstratas (ABC) |

---

## Como Executar

### Pré-requisitos

- Python 3.12 ou superior
- pip

### Instalação

```bash
# 1. Clone o repositório
git clone https://github.com/ThiagoNLeite/Game_Cyber-Western.git
cd deserto-de-silicio

# 2. Crie e ative o ambiente virtual
python -m venv env

# Windows
env\Scripts\activate

# Linux / macOS
source env/bin/activate

# 3. Instale as dependências
pip install pygame

# 4. Execute o jogo
python main.py
```

### Executar Ferramentas de Debug

```bash
# Relatório completo de balanceamento
python -m utils.debug relatorio

# Simular todos os inimigos vs jogador nível 3
python -m utils.debug sim

# Simular sequência de combates de um cenário específico
python -m utils.debug cenario 3
```

---

## Como Jogar

### Criação de Personagem

Combine uma **raça** e uma **vocação** para definir os atributos base do seu personagem:

| Raça | Bônus | Habilidade Passiva |
|---|---|---|
| Humano | +2 em todos os atributos | Cura 5 HP ao receber crítico |
| Ciborgue | +5 Defesa, +10 Vida, -2 Esquiva | Escudo absorve 3 de dano |
| Androide | +5 Poder, +3 Esquiva, -3 Vida | Mira Assistida (+5 Poder no 1º ataque) |

| Vocação | Bônus | Habilidade Especial |
|---|---|---|
| Pistoleiro | +5 Poder, +2 Esquiva | Tiro Duplo (2 ataques independentes) |
| Tecno-Sábio | +5 Poder, +2 Defesa | Hack (zera defesa do inimigo por 1 turno) |
| Sucateiro | +3 Defesa, +15 Vida | Escudo Improvisado (+5 Defesa + absorção) |

### Loop de Exploração

Ao entrar em cada área o jogador pode:

- **Explorar** — vasculha a área em busca de cofres, terminais, armadilhas ou encontros aleatórios. Algumas áreas exigem um número mínimo de explorações antes de liberar a saída
- **Avançar** — segue para o próximo evento quando o caminho de saída foi encontrado
- **Inventário** — gerencia itens e equipamentos

### Combate

O sistema de combate é por turnos com rolagem de dados (d20 + Poder vs. Defesa + 10). Crítico em 20 natural (dano dobrado).

Ações disponíveis em combate:
- **Atacar** — ataque básico
- **Habilidade** — habilidade especial da vocação (uso único por combate)
- **Item** — usa item de cura ou de dano do inventário
- **Fugir** — teste de Esquiva (d20 + Esquiva ≥ 15)

### Progressão

- **XP** ganho por: combates (15–75 XP), desafios resolvidos (+25 XP), cofres arrombados (+20 XP), enigmas de NPC resolvidos (+40 XP)
- A cada nível: +2 Poder, +1 Defesa, +15 Vida Máxima, +1 Esquiva
- Projeção: chegar ao boss final em torno do **nível 5** explorando tudo

### Guardiões de Passagem

3 NPCs bloqueiam saídas de cenários com uma charada. O jogador pode:
- Resolver a charada (gratuito)
- Pagar o custo de passagem (células de fusão / vida / item)
- Voltar à área para se preparar melhor

| Guardião | Aparece em | Custo |
|---|---|---|
| Velho Minerador | Saída do Saloon | 15 células de fusão |
| Fantasma de Sinal | Saída das Minas | 30% da vida atual |
| Dróide Guardião | Saída do Oásis | 1 item do inventário |

### Sistema de Save

3 slots de save independentes. O jogo salva automaticamente após cada cenário. Use os slots para manter diferentes personagens ou tentar estratégias distintas.

---

## Estrutura do Projeto

```
deserto-de-silicio/
│
├── main.py                     # Ponto de entrada e orquestração do jogo
├── teste.py                    # Suite de testes (92 testes unitários)
│
├── data/                       # Dados do jogo em JSON
│   ├── cenario.json            # 6 cenários com eventos de exploração
│   ├── inimigos.json           # 15 inimigos + narrativas de encontro
│   └── itens.json              # 16 itens (cura, combate, utilidade, equipáveis)
│
├── entidades/                  # Hierarquia de entidades de combate
│   ├── entidade.py             # Classe base abstrata (ABC)
│   ├── jogador.py              # Personagem do jogador
│   └── monstro.py              # Monstro + Boss (herança)
│
├── criacao/                    # Sistema de criação de personagem
│   ├── raca.py                 # Raca (ABC) → Humano, Ciborgue, Androide
│   └── vocacao.py              # Vocacao (ABC) → Pistoleiro, TecnoSabio, Sucateiro
│
├── itens/
│   └── item.py                 # Item (ABC) → ItemCura, ItemCombate,
│                               #              ItemUtilidade, ItemEquipavel
│                               #              + FabricaItens
│
├── mecanicas/
│   ├── combate.py              # SistemaCombate — loop de turnos
│   ├── desafios.py             # Desafio (ABC) → Terminal, Armadilha,
│   │                           #                  EnigmaNPC, Recurso
│   └── dados.py                # SistemaDados — d4/d6/d8/d10/d12/d20/d100
│
├── interface/
│   ├── gerenciador_tela.py     # Todas as telas pygame
│   └── cores_estilo.py         # Paleta, fontes e constantes de layout
│
├── utils/
│   ├── progresso.py            # SistemaProgresso — save/load JSON (3 slots)
│   └── debug.py                # Simulação de combates e relatório de balanceamento
│
└── saves/                      # Saves gerados automaticamente (gitignore)
    ├── save_slot1.json
    ├── save_slot2.json
    └── save_slot3.json
```

---

## Arquitetura POO

### Hierarquia de Classes

```
Entidade (ABC)
├── Jogador              — personagem com XP, inventário, equipamentos, vocação
└── Monstro              — escalado por nível via Monstro.escalar()
    └── Boss             — 3 fases com atributos e comportamentos distintos

Item (ABC)
├── ItemCura             — restaura HP
├── ItemCombate          — causa dano ao inimigo + efeito especial
├── ItemUtilidade        — buffs temporários em atributos
└── ItemEquipavel        — modificadores permanentes via equip() / unequip()

Raca (ABC)
├── Humano               — passiva: cura ao receber crítico
├── Ciborgue             — passiva: escudo absorve dano fixo
└── Androide             — passiva: bônus de mira no primeiro ataque

Vocacao (ABC)
├── Pistoleiro           — habilidade: Tiro Duplo
├── TecnoSabio           — habilidade: Hack
└── Sucateiro            — habilidade: Escudo Improvisado

Desafio (ABC)
├── DesafioTerminal      — sequência matemática, 3 tentativas
├── DesafioArmadilha     — teste de esquiva, escolha prévia do jogador
├── EnigmaNPC            — charadas dos guardiões de passagem
└── DesafioRecurso       — arrombamento de cofres, até 3 tentativas
```

### Pilares de POO Demonstrados

**Abstração**
- `Entidade`, `Item`, `Raca`, `Vocacao` e `Desafio` são classes abstratas (ABC) com métodos obrigatórios
- `descricao()`, `usar()`, `aplicar_modificadores()` e `executar()` são abstratos em cada hierarquia

**Herança**
- `Jogador` e `Monstro` herdam de `Entidade` — compartilham `atacar()`, `receber_dano()`, `curar()`
- `Boss` herda de `Monstro` e sobrescreve o comportamento de ataque para incluir as 3 fases
- `ItemEquipavel` herda de `Item` e estende com `equip()` e `unequip()`

**Polimorfismo**
- `SistemaCombate` chama `inimigo.atacar()` sem saber se é `Monstro` ou `Boss`
- `FabricaItens.criar()` instancia a subclasse correta com base no campo `"tipo"` do JSON
- `jogador.habilidade_especial()` delega para `vocacao.habilidade_especial()` — cada vocação responde diferente

**Encapsulamento**
- Atributos de saúde manipulados exclusivamente via `curar()` e `receber_dano()`
- `_subir_nivel()` é método privado — a progressão é gerenciada internamente por `ganhar_xp()`
- `ItemEquipavel._equipado` controla estado interno, exposto somente via propriedade `esta_equipado`
- `SistemaProgresso` encapsula toda a lógica de serialização/deserialização de saves

---

## Mecânicas de Jogo

### Os 6 Cenários

| # | Nome | Inimigo da Entrada | Explorações Mín. | Guardião |
|---|---|---|---|---|
| 1 | Refúgio Poeira-Estelar | Arruaceiro de Saloon | — (tutorial) | Velho Minerador |
| 2 | Desfiladeiro dos Cabos Partidos | Rato-Cibernético | 1 | — |
| 3 | As Minas de Lítio | Minerador Infectado | 2 | Fantasma de Sinal |
| 4 | O Trem Bala Abandonado | Torreta de Segurança | 4 | — |
| 5 | O Oásis Metálico | Holograma Defensivo | 2 | Dróide Guardião |
| 6 | A Torre do Silício | Guarda de Elite | 3 | Boss: Xerife de Ferro |

### Os 15 Inimigos

Cada inimigo tem narrativa de encontro contextualizada, atributos escalados pelo nível do jogador e efeitos especiais únicos:

- **Choque** — dano extra d6 elétrico (Drone, Escorpião)
- **Radiação** — reduz -1 Poder por turno (Minerador Infectado)
- **Roubo de energia** — absorve HP do jogador (Sanguessuga)
- **Debuff de status** — reduz Defesa e Esquiva (IA Tática)

### Boss: Xerife de Ferro (3 Fases)

| Fase | Gatilho | Mudança |
|---|---|---|
| Fase 1 | Início | Comportamento padrão |
| Fase 2 | ≤ 50% HP | +5 Poder, +3 Defesa, ataque duplo |
| Fase 3 | ≤ 25% HP | +8 Poder, +4 Esquiva, dano em área + regeneração 10 HP/turno |

### Sistema de Equipamentos

Itens equipáveis ocupam slots de **arma** ou **armadura**. Equipar um item no slot substitui o anterior automaticamente, revertendo seus modificadores.

| Item | Slot | Efeito |
|---|---|---|
| Revólver Modificado | Arma | POD +5, ESQ +1 |
| Canhão de Plasma | Arma | POD +8, ESQ -1 |
| Colete de Sucata | Armadura | DEF +4, VID +10, ESQ -1 |
| Exoesqueleto Parcial | Armadura | DEF +7, VID +20, ESQ -2 |

---

## Testes

A suite cobre todos os módulos principais com 92 testes unitários:

```
python -m unittest teste -v

Módulos testados:
  ✓ SistemaDados          — todos os tipos de dado (d4 a d100)
  ✓ Racas (3)             — modificadores e habilidades passivas
  ✓ Vocações (3)          — modificadores e habilidades especiais
  ✓ Jogador (9 combos)    — todas as combinações raça × vocação
  ✓ Monstro / Boss        — escalonamento e fases do boss
  ✓ SistemaCombate        — turnos, crítico, fuga, morte
  ✓ Desafios (4 tipos)    — terminal, armadilha, enigma, recurso
  ✓ Itens (4 tipos)       — cura, combate, utilidade, equipável
  ✓ FabricaItens          — instanciação correta por tipo
  ✓ SistemaProgresso      — save, load, múltiplos slots
  ✓ Herança/Polimorfismo  — verificação explícita das hierarquias

----------------------------------------------------------------------
Ran 92 tests in 0.177s  |  OK
```

---

## Ferramentas de Debug

O módulo `utils/debug.py` oferece simulação de combates sem I/O para calibrar dificuldade:

```bash
# Relatório completo — testa todos os 15 inimigos e sinaliza desbalanceados
python -m utils.debug relatorio

# Saída de exemplo:
# ========================================================================
#   RELATÓRIO DE BALANCEAMENTO — Deserto de Silício
# ========================================================================
#   Inimigo                             Cenário  %Vitória   Turnos   Dano Rec
# ------------------------------------------------------------------------
#   ✓ Rato-Cibernético                  [1, 2]   78.3%      4.2      12.1
#   ✓ Arruaceiro de Saloon              [1]      71.0%      5.8      18.4
#   ...
```

O sistema de logging grava em `debug.log` com timestamp, nível e módulo de origem.

---
