# Flyff Universe Bot

Bot de automação para Flyff Universe (MMORPG browser) — faz o personagem farmar automaticamente sem monopolizar o mouse e teclado do usuário.

## Como funciona

O bot roda em duas partes:
- **Backend** (Python/FastAPI): controla o Chrome via Playwright, detecta monstros com OpenCV, executa combate e cura
- **Desktop** (Tauri/React): interface visual para configurar e monitorar o bot em tempo real

O Chrome pode ficar minimizado. O computador fica livre para uso normal.

---

## Instalação (usuário final)

Baixe e execute o instalador:
```
Flyff Bot_1.0.0_x64-setup.exe
```

O Chromium já vem embutido — nenhuma instalação adicional necessária.

---

## Desenvolvimento

### Requisitos

- Python 3.11+
- Node.js 18+
- Rust (para compilar o Tauri)
- Windows 10/11

### Setup

```powershell
# 1. Criar ambiente virtual Python
python -m venv venv
venv\Scripts\activate

# 2. Instalar dependências Python
pip install -r backend\requirements.txt

# 3. Instalar dependências Node
cd desktop
npm install
cd ..

# 4. Rodar em modo dev
cd desktop
npm run tauri dev
```

O modo dev inicia o backend Python pelo venv automaticamente.

### Gerar instalador

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1
```

O instalador gerado fica em:
```
desktop\src-tauri\target\release\bundle\nsis\Flyff Bot_1.0.0_x64-setup.exe
```

---

## Configuração

Edite `backend/config/config.yaml` antes de iniciar o bot ou use a interface gráfica.

### Campos principais

```yaml
browser:
  headless: false         # false = mostra o Chrome; true = invisível
  width: 1024
  height: 600

character:
  hp_threshold: 0.5       # usa poção quando HP < 50%
  hp_potion_key: "1"
  mp_threshold: 0.3
  mp_potion_key: "2"

skills:
  rotation:
    - key: "c"            # auto-attack
      cooldown: 0.0
    - key: "q"            # skill com cooldown
      cooldown: 3.0
  skill_delay: 0.5

loot:
  loot_key: "4"
  auto_loot: true

vision:
  detection_confidence: 0.75   # reduzir se não detectar monstros
  selected_monster: ""          # "" = todos; ou nome da pasta ex: "Pukepuke"
  hp_bar_region:
    x: 10
    y: 500
    width: 180
    height: 14
```

---

## Adicionando monstros

Crie uma pasta com o nome do monstro dentro de `backend/assets/monsters/` e coloque screenshots do nome do monstro (o texto que aparece acima dele no jogo):

```
backend/assets/monsters/
└── Pukepuke/
    ├── Pukepuke.png          # nome amarelo (monstro passivo)
    └── Pukepuke_red.png      # nome vermelho (monstro agressivo)
```

**Dicas:**
- Fotografe só o texto do nome, com o mínimo de fundo possível
- Monstros com nome **vermelho** têm prioridade automática de ataque
- Se a confiança estiver baixa (~70%), tente tirar a foto com melhor contraste

---

## Estrutura do projeto

```
Flyff-Bot-V2/
├── scripts/
│   └── build.ps1                    # Script de build do instalador
│
├── backend/                         # Backend Python
│   ├── api.py                       # FastAPI + endpoints + WebSocket de logs
│   ├── backend.spec                 # Config do PyInstaller
│   ├── config/
│   │   └── config.yaml              # Configuração do bot
│   ├── assets/
│   │   ├── monsters/                # Templates dos monstros (subpastas por monstro)
│   │   └── attacking/               # Templates de indicadores de ataque
│   └── src/
│       ├── bot_core.py              # Máquina de estados principal
│       ├── modules/
│       │   ├── browser_controller.py
│       │   ├── combat_engine.py
│       │   ├── healing_manager.py
│       │   └── loot_manager.py
│       ├── vision/
│       │   └── vision_engine.py     # Detecção OpenCV + YOLO
│       └── utils/
│           ├── config_manager.py
│           └── logger.py
│
└── desktop/                         # Frontend Tauri + React
    ├── src/
    │   ├── screens/
    │   │   ├── ConfigScreen.tsx     # Configuração antes de iniciar
    │   │   └── RunningScreen.tsx    # Monitoramento durante execução
    │   └── lib/
    │       └── api.ts               # Cliente HTTP para o backend
    └── src-tauri/
        └── src/
            └── lib.rs               # Spawn do backend Python
```

---

## Endpoints da API (backend)

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/health` | Health check |
| GET | `/monsters` | Lista monstros disponíveis |
| POST | `/bot/start` | Inicia o bot |
| POST | `/bot/ready` | Sinaliza que o login foi feito |
| POST | `/bot/stop` | Para o bot |
| POST | `/bot/pause` | Pausa |
| POST | `/bot/resume` | Retoma |
| GET | `/bot/status` | Estado atual (HP, kills, estado) |
| GET | `/config` | Lê config.yaml |
| PUT | `/config` | Salva config.yaml |
| WS | `/ws/logs` | Stream de logs em tempo real |

---

## Problemas comuns

**Monstros não detectados**
- Reduzir `detection_confidence` para 0.6
- Verificar se a pasta do monstro existe em `assets/monsters/`
- Confirmar que o screenshot é do nome do monstro, não do corpo

**HP bar não lida corretamente**
- Ajustar `vision.hp_bar_region` para a posição exata na sua resolução
- A região deve cobrir somente a barra de HP (sem bordas)

**Bot não encontra o jogo**
- Verificar se o Chrome abriu em `https://universe.flyff.com/play`
- Aguardar o carregamento completo antes de clicar em "Pronto"

**YOLO (opcional)**
- Coloque um modelo treinado em `backend/assets/model.pt`
- O bot troca automaticamente para YOLO quando o arquivo existe
