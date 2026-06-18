import asyncio
from loguru import logger

from src.modules.browser_controller import BrowserController
from src.utils.config_manager import BotConfig


class LootManager:
    def __init__(self, config: BotConfig, browser: BrowserController):
        self.config = config
        self.browser = browser

    async def loot(self):
        if not self.config.loot.auto_loot:
            return

        await asyncio.sleep(self.config.loot.loot_delay)
        logger.info("Coletando itens...")

        press_interval = 0.3
        presses = int(self.config.loot.loot_duration / press_interval)
        for _ in range(presses):
            await self.browser.press_key(self.config.loot.loot_key)
            await asyncio.sleep(press_interval)
