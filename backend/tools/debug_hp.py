"""
Mostra ao vivo o que o bot está lendo como HP bar.

Uso:
    python tools/debug_hp.py

ESC para sair.
"""

import asyncio
import os
import sys
import cv2
import numpy as np
from pathlib import Path

os.chdir(Path(__file__).parent.parent)
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.modules.browser_controller import BrowserController
from src.utils.config_manager import load_config


async def main():
    config = load_config("config/config.yaml")
    browser = BrowserController(config)

    print("Iniciando Chrome... faça login e pressione ENTER aqui.")
    await browser.start()
    input()

    r = config.vision.hp_bar_region

    while True:
        frame = await browser.get_frame()
        region = frame[r.y:r.y + r.height, r.x:r.x + r.width]

        # Mesma lógica do vision_engine: detecta colunas coloridas (saturação > 60)
        hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
        saturation = hsv[:, :, 1]
        cols_with_color = np.any(saturation > 60, axis=0)

        if np.any(cols_with_color):
            last_col = int(np.where(cols_with_color)[0][-1])
            ratio = min(1.0, (last_col + 1) / region.shape[1])
        else:
            last_col = 0
            ratio = 0.0

        # Visualização: marca onde a barra termina
        debug = frame.copy()
        cv2.rectangle(debug, (r.x, r.y), (r.x + r.width, r.y + r.height), (0, 255, 0), 2)
        fill_x = r.x + last_col
        cv2.line(debug, (fill_x, r.y - 4), (fill_x, r.y + r.height + 4), (0, 0, 255), 2)
        cv2.putText(debug, f"HP: {ratio:.0%}", (r.x, r.y - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        # Zoom da região com mapa de saturação
        zoom = cv2.resize(region, None, fx=6, fy=6, interpolation=cv2.INTER_NEAREST)
        sat_vis = cv2.resize(saturation, None, fx=6, fy=6, interpolation=cv2.INTER_NEAREST)
        sat_color = cv2.applyColorMap(sat_vis, cv2.COLORMAP_JET)

        print(f"HP: {ratio:.0%}  |  última coluna colorida: {last_col}/{region.shape[1]}  |  "
              f"região: x={r.x} y={r.y} w={r.width} h={r.height}")

        cv2.imshow("Frame (verde=regiao, vermelho=fim da barra)", debug)
        cv2.imshow("Zoom da regiao HP", zoom)
        cv2.imshow("Mapa de saturacao (azul=cinza, vermelho=colorido)", sat_color)

        if cv2.waitKey(1500) & 0xFF == 27:
            break

    cv2.destroyAllWindows()
    await browser.stop()


if __name__ == "__main__":
    asyncio.run(main())
