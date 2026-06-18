import asyncio
import time
from enum import Enum, auto
from loguru import logger

from src.modules.browser_controller import BrowserController
from src.modules.combat_engine import CombatEngine
from src.modules.healing_manager import HealingManager
from src.modules.loot_manager import LootManager
from src.vision.vision_engine import VisionEngine
from src.utils.config_manager import BotConfig


class BotState(Enum):
    IDLE      = auto()
    SCANNING  = auto()
    ATTACKING = auto()
    LOOTING   = auto()
    PAUSED    = auto()
    STOPPED   = auto()


class BotCore:
    def __init__(self, config: BotConfig):
        self.config = config
        self.state = BotState.IDLE

        self.browser = BrowserController(config)
        self.vision  = VisionEngine(config)
        self.combat  = CombatEngine(config, self.browser, self.vision)
        self.healing = HealingManager(config, self.browser, self.vision)
        self.loot    = LootManager(config, self.browser)

        self.stats = {
            "kills": 0,
        }

        self._running = False
        self._paused  = False
        self._ready_event = asyncio.Event()
        self._last_monster_found_time = time.time()
        self._camera_rotation_interval = 5.0
        self._rotation_direction = "right"

    # ── Lifecycle ────────────────────────────────────────────

    async def start(self):
        logger.info("=" * 50)
        logger.info("  Flyff Universe Bot — Iniciando")
        logger.info("=" * 50)

        await self.browser.start()
        self.vision.setup()

        logger.info("=" * 50)
        logger.info("  Faça login no jogo e vá até a área de farm.")
        logger.info("  Clique em 'Pronto' no app quando estiver na área de farm.")
        logger.info("=" * 50)
        await self._ready_event.wait()

        logger.info("Configurando câmera...")
        await self.browser.setup_camera()

        self._running = True

        heal_task = asyncio.create_task(self.healing.start_monitoring())

        overlay_task = None
        if self.config.logging.visual_overlay:
            overlay_task = asyncio.create_task(self._visual_overlay_loop())

        try:
            await self._main_loop()
        except KeyboardInterrupt:
            logger.info("Interrompido pelo usuário.")
        except Exception as e:
            logger.exception(f"Erro crítico no BotCore: {e}")
        finally:
            self._running = False
            self.healing.stop_monitoring()
            heal_task.cancel()
            if overlay_task:
                overlay_task.cancel()
            await self.browser.stop()
            self._print_stats()

    async def stop(self):
        logger.info("Parando o bot...")
        self._running = False
        self._set_state(BotState.STOPPED)

    def pause(self):
        self._paused = True
        self.state = BotState.PAUSED
        self.healing.pause()
        logger.info("Bot pausado.")

    def resume(self):
        self._paused = False
        self.state = BotState.SCANNING
        self.healing.resume()
        logger.info("Bot retomado.")

    def signal_ready(self):
        self._ready_event.set()
        logger.info("Sinal de pronto recebido — iniciando farm.")

    # ── Loop Principal ───────────────────────────────────────

    async def _main_loop(self):
        self._set_state(BotState.SCANNING)

        while self._running:
            if self._paused:
                await asyncio.sleep(0.5)
                continue

            try:
                await self._tick()
            except Exception as e:
                logger.error(f"Erro no ciclo do bot: {e}")
                if self._running:
                    self._set_state(BotState.SCANNING)
                await asyncio.sleep(1.0)

    async def _tick(self):
        if self.state == BotState.SCANNING:
            await self._tick_scanning()
        elif self.state == BotState.LOOTING:
            await self._tick_looting()
        else:
            await asyncio.sleep(0.3)

    async def _tick_scanning(self):
        frame = await self.browser.get_frame()
        monster = self.vision.find_nearest_monster(frame)

        if not monster:
            time_without_monster = time.time() - self._last_monster_found_time
            if time_without_monster >= self._camera_rotation_interval:
                logger.info("Sem monstros — girando câmera para procurar...")
                await self.browser.rotate_camera(self._rotation_direction)
                self._rotation_direction = "left" if self._rotation_direction == "right" else "right"
                self._last_monster_found_time = time.time()
            else:
                await asyncio.sleep(self.config.farm.action_delay)
            return

        self._last_monster_found_time = time.time()
        logger.info(f"Monstro encontrado: {monster.label} ({monster.confidence:.0%})")
        self._set_state(BotState.ATTACKING)

        killed = await self.combat.attack(monster)

        if killed:
            self.stats["kills"] += 1
            self._set_state(BotState.LOOTING)
        else:
            self._set_state(BotState.SCANNING)

    async def _tick_looting(self):
        await self.loot.loot()
        self._set_state(BotState.SCANNING)

    # ── Utilitários ──────────────────────────────────────────

    async def _visual_overlay_loop(self):
        await self.browser.inject_overlay()
        while self._running:
            try:
                frame = await self.browser.get_frame()
                monsters = self.vision.find_monsters(frame)
                await self.browser.draw_overlay(monsters)
            except Exception:
                pass
            await asyncio.sleep(0.3)
        await self.browser.clear_overlay()

    def _set_state(self, new_state: BotState):
        if self._paused:
            return
        if self.state != new_state:
            self.state = new_state

    def _print_stats(self):
        logger.info("=" * 40)
        logger.info("  Estatísticas da Sessão")
        logger.info("=" * 40)
        for key, value in self.stats.items():
            logger.info(f"  {key}: {value}")
        logger.info("=" * 40)

    def get_status(self) -> dict:
        return {
            "state": self.state.name,
            "running": self._running,
            "paused": self._paused,
            "hp": self.healing.current_hp,
            "mp": self.healing.current_mp,
            "fp": self.healing.current_fp,
            "stats": {
                "kills": self.stats["kills"],
            },
        }
