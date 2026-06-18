"""
Calibração das barras HP, MP e FP.

Uso:
    python tools/calibrate_hp.py

O script captura um frame do jogo e abre 3 janelas em sequência —
uma para cada barra. Clique e arraste sobre a barra e pressione ENTER para salvar.
Pressione S para pular uma barra, ESC para cancelar tudo.
"""

import asyncio
import os
import sys
import cv2
import yaml
from pathlib import Path

os.chdir(Path(__file__).parent.parent)
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.modules.browser_controller import BrowserController
from src.utils.config_manager import load_config

_start = None
_end = None
_drawing = False
_frame_orig = None
_display = None


def _on_mouse(event, x, y, flags, param):
    global _start, _end, _drawing, _display
    if event == cv2.EVENT_LBUTTONDOWN:
        _drawing = True
        _start = (x, y)
        _end = (x, y)
    elif event == cv2.EVENT_MOUSEMOVE and _drawing:
        _end = (x, y)
        _display = _frame_orig.copy()
        cv2.rectangle(_display, _start, _end, (0, 255, 0), 1)
    elif event == cv2.EVENT_LBUTTONUP:
        _drawing = False
        _end = (x, y)
        _display = _frame_orig.copy()
        cv2.rectangle(_display, _start, _end, (0, 255, 0), 2)


def _calibrate_bar(title: str, hint: str) -> dict | None:
    """Abre uma janela para calibrar uma barra. Retorna o dict {x,y,width,height} ou None."""
    global _start, _end, _display

    _start = None
    _end = None
    _display = _frame_orig.copy()

    cv2.namedWindow(title, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(title, 1280, 720)
    cv2.setMouseCallback(title, _on_mouse)

    print(f"\n{title}")
    print(f"  {hint}")
    print("  ENTER = salvar | S = pular | R = resetar | ESC = cancelar tudo")

    while True:
        cv2.imshow(title, _display)
        key = cv2.waitKey(20) & 0xFF

        if key == 27:
            cv2.destroyWindow(title)
            return "cancel"

        elif key == ord('s'):
            print(f"  Pulado.")
            cv2.destroyWindow(title)
            return None

        elif key == ord('r'):
            _start = None
            _end = None
            _display = _frame_orig.copy()

        elif key == 13 and _start and _end:
            x1 = min(_start[0], _end[0])
            y1 = min(_start[1], _end[1])
            x2 = max(_start[0], _end[0])
            y2 = max(_start[1], _end[1])
            w, h = x2 - x1, y2 - y1

            if w < 5 or h < 3:
                print("  Seleção muito pequena, tente novamente.")
                continue

            cv2.destroyWindow(title)
            print(f"  Salvo: x={x1} y={y1} width={w} height={h}")
            return {"x": x1, "y": y1, "width": w, "height": h}


async def main():
    global _frame_orig

    config = load_config("config/config.yaml")
    browser = BrowserController(config)

    print("Iniciando Chrome... faça login no jogo e pressione ENTER.")
    await browser.start()
    input()

    _frame_orig = await browser.get_frame()
    await browser.stop()

    bars = [
        ("HP Bar", "hp_bar_region",  "Selecione a barra de HP (vermelha)"),
        ("MP Bar", "mp_bar_region",  "Selecione a barra de MP (azul)"),
        ("FP Bar", "fp_bar_region",  "Selecione a barra de FP (verde/amarela)"),
    ]

    config_path = Path("config/config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    for title, config_key, hint in bars:
        result = _calibrate_bar(title, hint)
        if result == "cancel":
            print("\nCancelado.")
            cv2.destroyAllWindows()
            return
        if result is not None:
            raw["vision"][config_key] = result

    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(raw, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print("\nConfigurações salvas em config/config.yaml!")
    cv2.destroyAllWindows()


if __name__ == "__main__":
    asyncio.run(main())
