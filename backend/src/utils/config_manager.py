from pathlib import Path
from typing import List, Optional
import yaml
from pydantic import BaseModel


class BrowserConfig(BaseModel):
    headless: bool = False
    width: int = 1280
    height: int = 720
    game_url: str = "https://universe.flyff.com/play"


class FarmConfig(BaseModel):
    attack_timeout: int = 15
    action_delay: float = 0.3


class CharacterConfig(BaseModel):
    hp_threshold: float = 0.5
    hp_potion_key: str = "1"
    mp_threshold: float = 0.3
    mp_potion_key: str = "2"
    fp_threshold: float = 0.3
    fp_potion_key: str = "3"
    potion_cooldown: float = 8.0


class SkillConfig(BaseModel):
    key: str
    cooldown: float = 0.0


class SkillsConfig(BaseModel):
    rotation: List[SkillConfig] = [SkillConfig(key="c")]
    skill_delay: float = 0.5


class LootConfig(BaseModel):
    loot_key: str = "4"
    auto_loot: bool = True
    loot_delay: float = 0.8
    loot_duration: float = 2.5


class RegionConfig(BaseModel):
    x: int
    y: int
    width: int
    height: int


class VisionConfig(BaseModel):
    detection_confidence: float = 0.6
    monsters_path: str = "assets/monsters"
    name_click_offset_y: int = 20
    selected_monster: str = ""
    hp_bar_region: RegionConfig = RegionConfig(x=10, y=680, width=180, height=14)
    mp_bar_region: Optional[RegionConfig] = None
    fp_bar_region: Optional[RegionConfig] = None


class LoggingConfig(BaseModel):
    level: str = "INFO"
    save_to_file: bool = True
    log_path: str = "logs/bot.log"
    visual_overlay: bool = False


class BotConfig(BaseModel):
    browser: BrowserConfig = BrowserConfig()
    farm: FarmConfig = FarmConfig()
    character: CharacterConfig = CharacterConfig()
    skills: SkillsConfig = SkillsConfig()
    loot: LootConfig = LootConfig()
    vision: VisionConfig = VisionConfig()
    logging: LoggingConfig = LoggingConfig()


def load_config(path: str = "config/config.yaml") -> BotConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config não encontrado: {config_path.resolve()}")

    with open(config_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    return BotConfig(**raw)
