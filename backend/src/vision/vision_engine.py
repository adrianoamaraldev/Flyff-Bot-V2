import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np
from loguru import logger

from src.utils.config_manager import BotConfig


@dataclass
class Detection:
    """Representa um monstro detectado na tela."""
    x: int          # centro X
    y: int          # centro Y
    width: int
    height: int
    confidence: float
    label: str
    is_alive: bool = True
    is_aggressive: bool = False  # True = nome vermelho (ataca ao se aproximar)

    @property
    def click_point(self) -> Tuple[int, int]:
        """Ponto ideal para clicar no monstro."""
        return (self.x, self.y)

    @property
    def top_left(self) -> Tuple[int, int]:
        return (self.x - self.width // 2, self.y - self.height // 2)

    @property
    def bottom_right(self) -> Tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)


class VisionEngine:
    """
    Motor de visão computacional do bot.

    Modos de detecção:
      1. Template Matching (OpenCV) — para começar, sem precisar treinar
      2. YOLO (ultralytics)         — mais robusto, ativado quando modelo treinado existir

    Também monitora:
      - HP bar do personagem
      - Estado do monstro (vivo/morto) pela health bar dele
    """

    def __init__(self, config: BotConfig):
        self.config = config
        self._name_templates: List[Tuple[str, np.ndarray, int]] = []
        self._attack_indicators: List[np.ndarray] = []
        self._yolo_model = None
        self._use_yolo = False

    def setup(self):
        self._load_name_templates()
        self._load_attack_indicators()
        self._try_load_yolo()

    def _load_name_templates(self):
        monsters_path = Path(self.config.vision.monsters_path)
        if not monsters_path.exists():
            return

        extensions = {".png", ".jpg", ".jpeg", ".bmp"}
        offset = self.config.vision.name_click_offset_y

        for folder in monsters_path.iterdir():
            if not folder.is_dir():
                continue
            label = folder.name  # label = nome da pasta (ex: "Burudeng")
            for img_path in folder.iterdir():
                if img_path.suffix.lower() not in extensions:
                    continue
                template = cv2.imread(str(img_path))
                if template is None:
                    continue
                self._name_templates.append((label, template, offset))

        if not self._name_templates:
            logger.warning("Nenhum template de nome encontrado em assets/monsters/.")

        if not self._name_templates:
            logger.warning("Nenhum template de nome encontrado em assets/monsters/.")

    def _detect_by_name(self, frame: np.ndarray) -> List[Detection]:
        """
        Detecta monstros pelo nome que aparece acima deles.
        Muito mais confiável que template do corpo — independente de ângulo.
        Clica X pixels abaixo do nome (no corpo do monstro).
        """
        if not self._name_templates:
            return []

        detections = []
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        confidence_threshold = self.config.vision.detection_confidence
        offset_y = self.config.vision.name_click_offset_y
        offset_x = 0
        selected = self.config.vision.selected_monster

        for label, template, _ in self._name_templates:
            if selected and label != selected:
                continue
            tg = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            th, tw = tg.shape

            if th > frame_gray.shape[0] or tw > frame_gray.shape[1]:
                continue

            result = cv2.matchTemplate(frame_gray, tg, cv2.TM_CCOEFF_NORMED)

            # Encontra picos locais: suprime vizinhança de cada match encontrado
            result_copy = result.copy()
            while True:
                _, max_val, _, max_loc = cv2.minMaxLoc(result_copy)
                if max_val < confidence_threshold:
                    break

                name_cy = max_loc[1] + th // 2

                # Detecta o centro real do texto escaneando pixels coloridos
                # a partir do match até encontrar onde o nome termina
                text_cx = self._find_text_center_x(
                    frame_gray, frame, max_loc[0], max_loc[1], tw, th
                )

                is_aggressive = self._is_red_name(frame, max_loc[0], max_loc[1], tw, th)
                detections.append(Detection(
                    x=text_cx + offset_x,
                    y=name_cy + offset_y,
                    width=tw, height=abs(offset_y) * 2,
                    confidence=float(max_val),
                    label=label,
                    is_aggressive=is_aggressive,
                ))

                # Suprime a região ao redor desse match para encontrar o próximo
                x1 = max(0, max_loc[0] - tw)
                y1 = max(0, max_loc[1] - th)
                x2 = min(result_copy.shape[1], max_loc[0] + tw)
                y2 = min(result_copy.shape[0], max_loc[1] + th)
                result_copy[y1:y2, x1:x2] = 0

        return self._non_max_suppression(detections)

    def _find_text_center_x(self, gray: np.ndarray, frame: np.ndarray,
                             match_x: int, match_y: int, tw: int, th: int) -> int:
        """
        A partir do ponto de match, escaneia para a direita para encontrar
        onde o texto do nome termina, e retorna o centro X real do texto completo.
        Detecta tanto texto claro (amarelo) quanto texto vermelho via HSV.
        """
        frame_h, frame_w = gray.shape
        y1 = max(0, match_y)
        y2 = min(frame_h, match_y + th)

        x = match_x + tw
        last_text_x = match_x + tw

        while x < min(frame_w, match_x + tw * 3):
            col_gray = gray[y1:y2, x]
            col_bgr = frame[y1:y2, x].reshape(-1, 1, 3)
            col_hsv = cv2.cvtColor(col_bgr, cv2.COLOR_BGR2HSV).reshape(-1, 3)

            has_bright = np.any(col_gray > 180)
            is_red = (
                ((col_hsv[:, 0] <= 10) | (col_hsv[:, 0] >= 170)) &
                (col_hsv[:, 1] > 130) &
                (col_hsv[:, 2] > 100)
            )
            has_text = has_bright or np.any(is_red)

            if has_text:
                last_text_x = x
            elif last_text_x < x - 8:
                break
            x += 1

        text_start = match_x
        text_end = last_text_x
        return (text_start + text_end) // 2

    def _is_red_name(self, frame: np.ndarray, x: int, y: int, w: int, h: int) -> bool:
        """Verifica se o nome do monstro é vermelho (agressivo) pela cor dos pixels."""
        region = frame[y:y + h, x:x + w]
        if region.size == 0:
            return False
        hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
        # Vermelho em HSV ocupa duas faixas de hue
        mask1 = cv2.inRange(hsv, np.array([0, 80, 100]), np.array([10, 255, 255]))
        mask2 = cv2.inRange(hsv, np.array([170, 80, 100]), np.array([180, 255, 255]))
        return (cv2.countNonZero(mask1) + cv2.countNonZero(mask2)) >= 3

    def _load_attack_indicators(self):
        """Carrega os templates das setinhas de ataque em assets/attacking/."""
        indicators_path = Path("assets/attacking")
        if not indicators_path.exists():
            logger.warning("Pasta assets/attacking não encontrada — detecção de ataque desabilitada.")
            return

        extensions = {".png", ".jpg", ".jpeg", ".bmp"}
        for img_path in indicators_path.iterdir():
            if img_path.suffix.lower() not in extensions:
                continue
            img = cv2.imread(str(img_path))
            if img is not None:
                self._attack_indicators.append(img)

        if not self._attack_indicators:
            logger.warning("Nenhum indicador de ataque encontrado em assets/attacking/.")

    def is_attacking(self, frame: np.ndarray, confidence: float = 0.7) -> bool:
        """
        Retorna True se qualquer setinha de ataque estiver visível na tela.
        Usado para confirmar que o personagem está batendo em um monstro.
        """
        if not self._attack_indicators:
            return True  # sem templates, assume que está atacando

        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        for template in self._attack_indicators:
            tg = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            if tg.shape[0] > frame_gray.shape[0] or tg.shape[1] > frame_gray.shape[1]:
                continue
            result = cv2.matchTemplate(frame_gray, tg, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)
            if max_val >= confidence:
                return True

        return False

    def _try_load_yolo(self):
        """Tenta carregar modelo YOLO treinado se existir."""
        model_path = Path("assets/model.pt")
        if not model_path.exists():
            return
        try:
            from ultralytics import YOLO
            self._yolo_model = YOLO(str(model_path))
            self._use_yolo = True
            logger.success("Modelo YOLO carregado!")
        except Exception as e:
            logger.warning(f"Erro ao carregar YOLO: {e}. Usando Template Matching.")

    # ── Detecção de Monstros ─────────────────────────────────

    def find_monsters(self, frame: np.ndarray) -> List[Detection]:
        if self._use_yolo:
            return self._detect_yolo(frame)
        return self._detect_by_name(frame)

    def find_nearest_monster(self, frame: np.ndarray, center: Tuple[int, int] = None) -> Optional[Detection]:
        """
        Retorna o monstro prioritário:
          1. Monstros agressivos (nome vermelho) têm prioridade absoluta — ataca o mais próximo deles.
          2. Sem agressivos, ataca o mais próximo do centro da tela.
        """
        monsters = self.find_monsters(frame)
        if not monsters:
            return None

        if center is None:
            h, w = frame.shape[:2]
            center = (w // 2, h // 2)

        dist = lambda m: (m.x - center[0]) ** 2 + (m.y - center[1]) ** 2

        aggressive = [m for m in monsters if m.is_aggressive]
        if aggressive:
            return min(aggressive, key=dist)

        return min(monsters, key=dist)

    def _detect_yolo(self, frame: np.ndarray) -> List[Detection]:
        """Detecção via YOLO — mais robusta e rápida."""
        results = self._yolo_model(frame, conf=self.config.vision.detection_confidence, verbose=False)
        detections = []

        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                label = result.names[int(box.cls[0])]
                detections.append(Detection(
                    x=cx, y=cy,
                    width=x2 - x1, height=y2 - y1,
                    confidence=float(box.conf[0]),
                    label=label,
                ))

        return detections

    def _non_max_suppression(self, detections: List[Detection], min_distance: int = 50) -> List[Detection]:
        """
        Remove detecções duplicadas próximas.
        Quando dois matches estão perto, mantém o de label mais longo (mais específico).
        Ex: 'burudeng capitao' vence 'burudeng' se estiverem no mesmo monstro.
        """
        if not detections:
            return []

        # Ordena por confiança — match exato sempre tem score maior que match parcial
        detections.sort(key=lambda d: d.confidence, reverse=True)
        kept = []

        for det in detections:
            too_close = False
            for kept_det in kept:
                dx = abs(det.x - kept_det.x)
                dy = abs(det.y - kept_det.y)
                if dx < min_distance and dy < min_distance:
                    too_close = True
                    break
            if not too_close:
                kept.append(det)

        return kept

    # ── Monitoramento de barras ──────────────────────────────

    def _read_bar(self, frame: np.ndarray, region_config) -> float:
        if region_config is None:
            return 0.0
        r = region_config
        region = frame[r.y:r.y + r.height, r.x:r.x + r.width]
        if region.size == 0:
            return 0.0
        hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
        cols_with_color = np.any(hsv[:, :, 1] > 60, axis=0)
        if not np.any(cols_with_color):
            return 0.0
        last_col = int(np.where(cols_with_color)[0][-1])
        return min(1.0, (last_col + 1) / region.shape[1])

    def read_player_hp(self, frame: np.ndarray) -> float:
        return self._read_bar(frame, self.config.vision.hp_bar_region)

    def read_player_mp(self, frame: np.ndarray) -> float:
        return self._read_bar(frame, self.config.vision.mp_bar_region)

    def read_player_fp(self, frame: np.ndarray) -> float:
        return self._read_bar(frame, self.config.vision.fp_bar_region)

    def save_debug_frame(self, frame: np.ndarray, path: str = "logs/debug_frame.png"):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(path, frame)
