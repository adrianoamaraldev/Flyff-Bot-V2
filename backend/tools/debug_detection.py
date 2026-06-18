"""
Mostra ao vivo onde o bot vai clicar nos monstros.
Cruz vermelha = ponto de clique exato.
ESC para sair.
"""

import asyncio
import os
import sys
import cv2
from pathlib import Path

os.chdir(Path(__file__).parent.parent)
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.modules.browser_controller import BrowserController
from src.utils.config_manager import load_config
from src.vision.vision_engine import VisionEngine


async def main():
    config = load_config("config/config.yaml")
    browser = BrowserController(config)
    vision = VisionEngine(config)

    print("Iniciando Chrome... faça login e pressione ENTER.")
    await browser.start()
    input()

    vision.setup()
    print(f"name_click_offset_y: {config.vision.name_click_offset_y}px")
    print("Ajuste no config.yaml e reinicie para ver o efeito.")
    print("ESC para sair.\n")

    while True:
        frame = await browser.get_frame()
        debug = frame.copy()

        monsters = vision.find_monsters(frame)

        for m in monsters:
            cx, cy = int(m.x), int(m.y)

            # Cruz vermelha no ponto de clique
            cv2.line(debug, (cx - 15, cy), (cx + 15, cy), (0, 0, 255), 2)
            cv2.line(debug, (cx, cy - 15), (cx, cy + 15), (0, 0, 255), 2)
            cv2.circle(debug, (cx, cy), 8, (0, 0, 255), 2)

            # Label acima da cruz
            cv2.putText(debug, f"{m.label} {m.confidence:.0%}",
                (cx - 40, cy - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        total = len(monsters)
        cv2.putText(debug, f"Detectados: {total} | y:{config.vision.name_click_offset_y}",
            (10, 700), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        if total:
            print(f"Cliques: {[(m.label, m.x, m.y) for m in monsters]}")
        else:
            print("Nenhum detectado")

        cv2.imshow("Debug — cruz vermelha = onde vai clicar", debug)
        if cv2.waitKey(800) & 0xFF == 27:
            break

    cv2.destroyAllWindows()
    await browser.stop()


if __name__ == "__main__":
    asyncio.run(main())
