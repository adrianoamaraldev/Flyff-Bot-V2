import asyncio
import os
import sys
from pathlib import Path

os.chdir(Path(__file__).parent)
sys.path.insert(0, str(Path(__file__).parent))

from src.bot_core import BotCore
from src.utils.config_manager import load_config
from src.utils.logger import setup_logger


async def main():
    config = load_config("config/config.yaml")
    setup_logger(
        level=config.logging.level,
        save_to_file=config.logging.save_to_file,
        log_path=config.logging.log_path,
    )

    bot = BotCore(config)
    await bot.start()


if __name__ == "__main__":
    asyncio.run(main())
