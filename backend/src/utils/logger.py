import sys
from pathlib import Path
from loguru import logger


def setup_logger(level: str = "INFO", save_to_file: bool = True, log_path: str = "logs/bot.log"):
    logger.remove()  # remove handler padrão

    fmt = "<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>"

    # Força UTF-8 no terminal Windows para suportar caracteres especiais
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    logger.add(sys.stdout, format=fmt, level=level, colorize=True)

    # Arquivo
    if save_to_file:
        Path(log_path).parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            log_path,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name} - {message}",
            level=level,
            rotation="10 MB",
            retention="7 days",
            encoding="utf-8",
        )

    return logger
