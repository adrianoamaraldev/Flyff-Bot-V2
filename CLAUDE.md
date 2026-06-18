# CLAUDE.md — Flyff Universe Bot

Este arquivo contém todo o contexto do projeto para ser usado com Claude Code no terminal.
Leia este arquivo antes de qualquer interação com o projeto.

---

## O que é este projeto

Bot de automação para o jogo **Flyff Universe** (MMORPG browser-based, acesso via navegador em https://universe.flyff.com/play).

O objetivo principal é fazer o personagem farmar automaticamente (matar monstros, coletar itens, se curar) **sem monopolizar o mouse e teclado do usuário**.

---

## Arquitetura atual (monorepo)

```
Flyff-Bot-V2/
├── build.ps1               # Script de build do instalador (PyInstaller + Tauri)
├── backend/                # Backend Python (FastAPI + automação)
└── desktop/                # Frontend Tauri + React
```

### Backend (Python / FastAPI)

O backend roda como servidor HTTP na porta `127.0.0.1:8000`. O frontend Tauri lança o processo `backend.exe` (ou `python api.py` em dev) automaticamente ao abrir.

**Ponto de entrada:** `backend/api.py`

Endpoints disponíveis:
- `GET /health` — Health check
- `GET /monsters` — Lista pastas em `assets/monsters/`
- `POST /bot/start` — Instancia e inicia o BotCore
- `POST /bot/ready` — Sinaliza que o usuário fez login no jogo
- `POST /bot/stop` — Para o bot
- `POST /bot/pause` / `POST /bot/resume` — Pause/resume
- `GET /bot/status` — Estado atual (BotState, HP, kills, paused)
- `GET /config` / `PUT /config` — Lê/salva `config/config.yaml`
- `WS /ws/logs` — WebSocket de logs em tempo real (broadcast a cada 100ms)

### Frontend (Tauri + React)

Duas telas principais:
- **ConfigScreen** — Edita configurações (skills, limiares de HP, monstro alvo) e inicia o bot
- **RunningScreen** — Monitoramento em tempo real (estado, HP/MP/FP, kills, log ao vivo)

O frontend faz poll do `/bot/status` a cada 1s e recebe logs via WebSocket.

### Comunicação

```
Desktop (Tauri) ──spawn──> backend.exe / api.py
Desktop (React) ──HTTP──> localhost:8000 (FastAPI)
Desktop (React) ──WS───> localhost:8000/ws/logs
```

---

## Contexto e decisões técnicas

### Por que Playwright e não pyautogui?

A versão anterior usava `pyautogui` → roubava o mouse/teclado físico.

A nova arquitetura usa **Playwright (CDP — Chrome DevTools Protocol)**:
- Captura frames diretamente da aba do Chrome, sem precisar de foco
- Envia clicks e teclas virtualmente (não move o mouse físico)
- O jogo pode ficar minimizado e o computador livre para uso normal
- Flags especiais do Chrome evitam throttling de renderização em segundo plano

### Detecção de monstros

Template matching via **nome do monstro** (texto acima do corpo), não do corpo — muito mais robusto a ângulos. Templates ficam em `backend/assets/monsters/{NomeMonstro}/*.png`.

Suporte a **YOLOv8** já implementado — quando o arquivo `backend/assets/model.pt` existir, o bot troca automaticamente.

### Prioridade de ataque

1. **Monstros agressivos (nome vermelho)** — prioridade absoluta, atacados antes de qualquer outro
2. **Monstros passivos (nome amarelo)** — atacado o mais próximo do centro da tela

A detecção de nome vermelho usa HSV: hue ≤10 ou ≥170, saturação >130, valor >100.

### Build para distribuição

`build.ps1` faz:
1. Baixa Chromium em `backend/browsers/` (via Playwright)
2. Empacota o backend com PyInstaller (`--onedir`) → `backend/dist/backend/`
3. Builda o Tauri com os recursos bundled via `--config` inline

**Importante — PyInstaller 6.x:** Os data files ficam em `_internal/` ao lado do `.exe`, não na mesma pasta. Por isso `api.py` usa `sys._MEIPASS` (aponta para `_internal/`) e não `sys.executable.parent`.

**Importante — tauri.conf.json:** O campo `resources` é injetado via arquivo temporário `tauri.release.conf.json` passado ao `--config` do `tauri build`. Nunca modificar `tauri.conf.json` via PowerShell `ConvertTo-Json` — o PS 5.1 escreve UTF-8 com BOM, que quebra o parser do Tauri.

---

## Stack técnica

| Lib | Uso |
|-----|-----|
| `playwright` | Controle do Chrome sem inputs físicos |
| `opencv-python` | Template matching, processamento de imagem |
| `ultralytics` | YOLOv8 para detecção de monstros (opcional) |
| `fastapi` + `uvicorn` | API HTTP + WebSocket |
| `pydantic` | Validação do config.yaml |
| `loguru` | Logs coloridos e rotativos |
| `pyyaml` | Leitura do arquivo de configuração |
| `asyncio` | Bot roda assíncrono (healing em paralelo com combate) |
| React + Tauri | Interface gráfica desktop |
| PyInstaller | Empacotamento do backend em `.exe` |

---

## Estrutura de arquivos

```
Flyff-Bot-V2/
├── build.ps1                        # Build do instalador (rodar da raiz)
│
├── backend/
│   ├── api.py                       # FastAPI + WebSocket de logs + entry point
│   ├── backend.spec                 # Config do PyInstaller
│   ├── requirements.txt
│   ├── config/
│   │   └── config.yaml              # Configuração principal
│   ├── assets/
│   │   ├── monsters/                # Subpastas por monstro com templates .png
│   │   └── attacking/               # Templates de indicadores de ataque
│   └── src/
│       ├── bot_core.py              # Máquina de estados: IDLE→SCANNING→ATTACKING→LOOTING
│       ├── modules/
│       │   ├── browser_controller.py
│       │   ├── combat_engine.py
│       │   ├── healing_manager.py
│       │   └── loot_manager.py
│       ├── vision/
│       │   └── vision_engine.py
│       └── utils/
│           ├── config_manager.py    # Pydantic models + load_config()
│           └── logger.py
│
└── desktop/
    ├── src/
    │   ├── App.tsx                  # Router ConfigScreen ↔ RunningScreen
    │   ├── screens/
    │   │   ├── ConfigScreen.tsx
    │   │   └── RunningScreen.tsx
    │   ├── components/
    │   │   ├── config/              # SkillsConfig, VisionConfig, etc
    │   │   ├── dashboard/           # BotControls, BotStats, LogPanel
    │   │   └── ui/                  # Componentes shadcn/ui
    │   └── lib/
    │       ├── api.ts               # Cliente HTTP para o backend
    │       └── theme-context.tsx
    └── src-tauri/
        ├── tauri.conf.json          # Config do Tauri (sem resources — injetado no build)
        └── src/
            ├── lib.rs               # spawn_backend() + kill_backend()
            └── main.rs
```

---

## Máquina de estados do bot

```
IDLE → SCANNING → ATTACKING → LOOTING → SCANNING → ...

Estados:
  IDLE      — aguardando início
  SCANNING  — procurando monstros via VisionEngine
  ATTACKING — em combate (CombatEngine + HealingManager em paralelo)
  LOOTING   — coletando itens após monstro morrer
  PAUSED    — pausado pelo usuário
  STOPPED   — encerrado

Prioridade de ataque no SCANNING:
  1. Monstros com nome vermelho (agressivos) — o mais próximo do centro
  2. Monstros com nome amarelo (passivos)    — o mais próximo do centro
```

---

## config.yaml — campos importantes

```yaml
browser:
  headless: false
  width: 1024
  height: 600
  game_url: "https://universe.flyff.com/play"

farm:
  attack_timeout: 15        # segundos antes de desistir de um monstro
  action_delay: 0.3

character:
  hp_threshold: 0.5         # cura quando HP < 50%
  hp_potion_key: "1"
  mp_threshold: 0.3
  mp_potion_key: "2"
  fp_threshold: 0.3
  fp_potion_key: "3"
  potion_cooldown: 3.0

skills:
  rotation:
    - key: "c"
      cooldown: 0.0
  skill_delay: 0.5

loot:
  loot_key: "4"
  auto_loot: true
  loot_delay: 0.8
  loot_duration: 2.5

vision:
  detection_confidence: 0.75
  monsters_path: "assets/monsters"
  selected_monster: ""        # "" = todos; "Pukepuke" = somente esse
  name_click_offset_y: 20     # pixels abaixo do nome até o corpo do monstro
  hp_bar_region:
    x: 10
    y: 500
    width: 180
    height: 14

logging:
  level: INFO
  save_to_file: true
  log_path: "logs/bot.log"
```

---

## Como rodar em desenvolvimento

```powershell
# Da raiz do projeto
cd desktop
npm run tauri dev
```

O Tauri em dev (`cfg!(debug_assertions) == true`) lança automaticamente:
```
venv\Scripts\python.exe backend\api.py
```

---

## Como gerar o instalador

```powershell
# Da raiz do projeto
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

Saída: `desktop\src-tauri\target\release\bundle\nsis\Flyff Bot_1.0.0_x64-setup.exe`

---

## O que está implementado

- [x] `BrowserController` — Chrome via Playwright, inputs virtuais, captura de frame sem foco
- [x] `VisionEngine` — template matching (OpenCV) + suporte a YOLO pronto
- [x] Prioridade de ataque: monstros agressivos (nome vermelho) antes dos passivos
- [x] `CombatEngine` — rotação de skills configurável
- [x] `HealingManager` — monitoramento de HP/MP/FP em task paralela
- [x] `LootManager` — loot automático com tecla configurável
- [x] `BotCore` — máquina de estados orquestrando todos os módulos
- [x] `ConfigManager` — carrega/valida config.yaml com Pydantic
- [x] FastAPI + WebSocket de logs em tempo real
- [x] Interface Tauri/React (ConfigScreen + RunningScreen)
- [x] Build distribível: PyInstaller + Tauri → instalador `.exe` standalone

---

## O que está planejado (próximos passos)

1. **Calibração visual de regiões** — script para clicar na tela e definir HP bar/minimapa
2. **Recovery de stuck** — detectar personagem preso e executar sequência de escape
3. **Treinamento YOLO** — scripts para coletar dados e treinar modelo
4. **Filtro de loot por nome** — OCR para ignorar itens indesejados
5. **Delays humanizados** — gaussian random nos tempos de ação (anti-detecção)

---

## Problemas conhecidos

- **HP bar**: a cor exata depende da resolução e configurações do jogo. Ajustar `vision.hp_bar_region` e os ranges HSV em `vision_engine.py → _read_bar()`
- **WebGL throttling**: se o jogo pausar quando minimizado, verificar flags do Chrome em `browser_controller.py`
- **Login**: o bot abre o jogo mas não faz login automaticamente. O usuário precisa logar e clicar "Pronto" na interface
- **Confiança baixa em monstros vermelhos**: o contraste do nome vermelho pode ser menor dependendo das configurações gráficas do jogo

---

## Contexto do usuário

- Linguagem principal: Python
- Sistema operacional: Windows
- Objetivo: bot genérico que funcione para qualquer classe do Flyff
- Prioridade: mouse/teclado livres durante o farm
