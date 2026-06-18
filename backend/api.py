import asyncio
import os
import queue as _queue
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

# Detecta execução como bundle PyInstaller e ajusta paths antes de qualquer import local
if getattr(sys, 'frozen', False):
    # PyInstaller 6.x: sys._MEIPASS aponta para _internal/ onde os data files vivem
    BASE_DIR = Path(sys._MEIPASS)
    os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH', str(BASE_DIR / 'browsers'))
else:
    BASE_DIR = Path(__file__).parent

os.chdir(str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR))

import uvicorn
import yaml
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from src.bot_core import BotCore
from src.utils.config_manager import load_config
from src.utils.logger import setup_logger

# ── Estado global ──────────────────────────────────────────────────────────────

_bot: Optional[BotCore] = None
_bot_task: Optional[asyncio.Task] = None
_log_clients: list[WebSocket] = []
_ws_sink_id: Optional[int] = None

# queue.Queue é thread-safe e não depende do event loop — funciona direto em sinks síncronos
_log_sync_queue: _queue.Queue = _queue.Queue(maxsize=500)


# ── Sink de log → WebSocket ────────────────────────────────────────────────────

def _ws_log_sink(message):
    record = message.record
    try:
        _log_sync_queue.put_nowait({
            "time": record["time"].strftime("%H:%M:%S"),
            "level": record["level"].name,
            "message": record["message"],
        })
    except _queue.Full:
        pass


def _attach_ws_sink():
    global _ws_sink_id
    if _ws_sink_id is not None:
        try:
            logger.remove(_ws_sink_id)
        except Exception:
            pass
    _ws_sink_id = logger.add(_ws_log_sink, level="INFO")


async def _broadcast_logs():
    """Lê a fila síncrona a cada 100ms e envia para todos os clientes WebSocket."""
    while True:
        await asyncio.sleep(0.1)

        entries: list[dict] = []
        while True:
            try:
                entries.append(_log_sync_queue.get_nowait())
            except _queue.Empty:
                break

        if not entries or not _log_clients:
            continue

        dead = []
        for ws in _log_clients:
            try:
                for entry in entries:
                    await ws.send_json(entry)
            except Exception:
                dead.append(ws)

        for ws in dead:
            if ws in _log_clients:
                _log_clients.remove(ws)


# ── App ────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    _attach_ws_sink()
    asyncio.create_task(_broadcast_logs())
    yield

app = FastAPI(title="Flyff Bot API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health ─────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/monsters")
async def list_monsters():
    monsters_path = Path("assets/monsters")
    if not monsters_path.exists():
        return {"monsters": []}
    monsters = sorted(d.name for d in monsters_path.iterdir() if d.is_dir())
    return {"monsters": monsters}


# ── Bot ────────────────────────────────────────────────────────────────────────

@app.post("/bot/start")
async def start_bot():
    global _bot, _bot_task
    if _bot_task and not _bot_task.done():
        return {"error": "Bot já está rodando"}

    config = load_config("config/config.yaml")
    setup_logger(
        level=config.logging.level,
        save_to_file=config.logging.save_to_file,
        log_path=config.logging.log_path,
    )
    _attach_ws_sink()

    _bot = BotCore(config)
    _bot_task = asyncio.create_task(_run_bot())
    return {"status": "started"}


async def _run_bot():
    try:
        await _bot.start()
    except Exception as e:
        logger.error(f"Bot encerrado com erro: {e}")


@app.post("/bot/ready")
async def signal_ready():
    """Usuário fez login no jogo — bot pode continuar."""
    if not _bot:
        return {"error": "Bot não iniciado"}
    _bot.signal_ready()
    return {"status": "ok"}


@app.post("/bot/stop")
async def stop_bot():
    if _bot:
        await _bot.stop()
    return {"status": "stopped"}


@app.post("/bot/pause")
async def pause_bot():
    if _bot:
        _bot.pause()
    return {"status": "paused"}


@app.post("/bot/resume")
async def resume_bot():
    if _bot:
        _bot.resume()
    return {"status": "resumed"}


@app.get("/bot/status")
async def get_status():
    if not _bot:
        return {"state": "IDLE", "running": False, "paused": False, "stats": {}}
    return _bot.get_status()


# ── Config ─────────────────────────────────────────────────────────────────────

@app.get("/config")
async def get_config():
    with open("config/config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@app.put("/config")
async def update_config(data: dict):
    with open("config/config.yaml", "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    return {"status": "saved"}


# ── WebSocket logs ─────────────────────────────────────────────────────────────

@app.websocket("/ws/logs")
async def ws_logs(websocket: WebSocket):
    origin = websocket.headers.get("origin", "sem origin")
    print(f"[WS] Conexão recebida — origin: {origin}", flush=True)
    await websocket.accept()
    _log_clients.append(websocket)
    await websocket.send_json({
        "time": "00:00:00",
        "level": "INFO",
        "message": "Log ao vivo conectado.",
    })
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in _log_clients:
            _log_clients.remove(websocket)


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")
