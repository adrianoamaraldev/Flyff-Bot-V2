import asyncio
import time

from loguru import logger

from src.modules.browser_controller import BrowserController
from src.vision.vision_engine import VisionEngine, Detection
from src.utils.config_manager import BotConfig


class CombatEngine:
    def __init__(self, config: BotConfig, browser: BrowserController, vision: VisionEngine):
        self.config = config
        self.browser = browser
        self.vision = vision
        self._skill_last_used: dict[str, float] = {}

    async def attack(self, monster: Detection) -> bool:
        """Ataca um monstro até ele morrer ou timeout. Retorna True se morreu."""
        logger.info(f"Atacando: {monster.label} em ({monster.x}, {monster.y})")

        await self.browser.click(monster.x, monster.y)
        await asyncio.sleep(0.5)

        frame = await self.browser.get_frame()
        if not self.vision.is_attacking(frame):
            logger.info("Clique falhou — voltando a escanear.")
            return False

        start_time = time.time()
        timeout = self.config.farm.attack_timeout

        while time.time() - start_time < timeout:
            await self._execute_rotation()
            await asyncio.sleep(self.config.skills.skill_delay)

            frame = await self.browser.get_frame()
            if not self.vision.is_attacking(frame):
                logger.success(f"Monstro {monster.label} derrotado!")
                return True

        logger.warning(f"Timeout ao atacar {monster.label} — desistindo.")
        return False

    async def _execute_rotation(self):
        now = time.time()
        for skill in self.config.skills.rotation:
            last_used = self._skill_last_used.get(skill.key, 0)
            if now - last_used >= skill.cooldown:
                await self.browser.press_key(skill.key)
                self._skill_last_used[skill.key] = now
                await asyncio.sleep(0.1)
