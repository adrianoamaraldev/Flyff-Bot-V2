import asyncio
import time
from loguru import logger

from src.modules.browser_controller import BrowserController
from src.vision.vision_engine import VisionEngine
from src.utils.config_manager import BotConfig


class HealingManager:
    def __init__(self, config: BotConfig, browser: BrowserController, vision: VisionEngine):
        self.config = config
        self.browser = browser
        self.vision = vision

        self._potion_cooldown: float = self.config.character.potion_cooldown
        self._last_hp_potion: float = 0
        self._last_mp_potion: float = 0
        self._last_fp_potion: float = 0

        self._monitoring = False
        self._paused = False

        self._current_hp: float = 1.0
        self._current_mp: float = 1.0
        self._current_fp: float = 1.0

    @property
    def current_hp(self) -> float:
        return self._current_hp

    @property
    def current_mp(self) -> float:
        return self._current_mp

    @property
    def current_fp(self) -> float:
        return self._current_fp

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False

    async def start_monitoring(self):
        self._monitoring = True
        await asyncio.sleep(3.0)
        while self._monitoring:
            if not self._paused:
                await self._check_and_heal()
            await asyncio.sleep(0.5)

    def stop_monitoring(self):
        self._monitoring = False

    async def _check_and_heal(self):
        try:
            frame = await self.browser.get_frame()
            self._current_hp = self.vision.read_player_hp(frame)
            self._current_mp = self.vision.read_player_mp(frame)
            self._current_fp = self.vision.read_player_fp(frame)

            now = time.time()

            if self._current_hp <= self.config.character.hp_threshold:
                await self._use_potion(
                    key=self.config.character.hp_potion_key,
                    value=self._current_hp,
                    threshold=self.config.character.hp_threshold,
                    bar="HP",
                    last_used=self._last_hp_potion,
                )
                self._last_hp_potion = now

            if self.config.vision.mp_bar_region and self._current_mp <= self.config.character.mp_threshold:
                await self._use_potion(
                    key=self.config.character.mp_potion_key,
                    value=self._current_mp,
                    threshold=self.config.character.mp_threshold,
                    bar="MP",
                    last_used=self._last_mp_potion,
                )
                self._last_mp_potion = now

            if self.config.vision.fp_bar_region and self._current_fp <= self.config.character.fp_threshold:
                await self._use_potion(
                    key=self.config.character.fp_potion_key,
                    value=self._current_fp,
                    threshold=self.config.character.fp_threshold,
                    bar="FP",
                    last_used=self._last_fp_potion,
                )
                self._last_fp_potion = now

        except Exception as e:
            logger.warning(f"Erro no HealingManager: {e}")

    async def _use_potion(self, key: str, value: float, threshold: float, bar: str, last_used: float):
        if time.time() - last_used < self._potion_cooldown:
            return
        pct = round(threshold * 100)
        logger.warning(f"{bar} abaixo de {pct}% ({value:.0%}) — usando poção!")
        await self.browser.press_key(key)
