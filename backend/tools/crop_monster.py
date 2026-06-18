"""
Abre o frame capturado e deixa você recortar o monstro com o mouse.

Uso:
    python tools/crop_monster.py
    python tools/crop_monster.py tools/frame_capturado.png  # imagem específica

Instruções:
  - Clique e arraste para selecionar a área do monstro
  - Pressione ENTER para salvar o recorte
  - Pressione R para resetar a seleção
  - Pressione ESC para cancelar
"""

import os
import sys
import cv2
import numpy as np
from pathlib import Path

os.chdir(Path(__file__).parent.parent)


# Estado do mouse
_drawing = False
_start = (-1, -1)
_end = (-1, -1)
_frame_original = None
_frame_display = None


def _on_mouse(event, x, y, flags, param):
    global _drawing, _start, _end, _frame_display

    if event == cv2.EVENT_LBUTTONDOWN:
        _drawing = True
        _start = (x, y)
        _end = (x, y)

    elif event == cv2.EVENT_MOUSEMOVE and _drawing:
        _end = (x, y)
        _frame_display = _frame_original.copy()
        cv2.rectangle(_frame_display, _start, _end, (0, 255, 0), 2)

    elif event == cv2.EVENT_LBUTTONUP:
        _drawing = False
        _end = (x, y)
        _frame_display = _frame_original.copy()
        cv2.rectangle(_frame_display, _start, _end, (0, 255, 0), 2)


def main():
    global _frame_original, _frame_display, _start, _end

    image_path = sys.argv[1] if len(sys.argv) > 1 else "tools/frame_capturado.png"

    if not Path(image_path).exists():
        print(f"Imagem não encontrada: {image_path}")
        print("Rode primeiro: python tools/capture_frame.py")
        return

    _frame_original = cv2.imread(image_path)
    _frame_display = _frame_original.copy()

    h, w = _frame_original.shape[:2]
    print(f"Imagem: {image_path} ({w}x{h})")
    print("Clique e arraste para selecionar o monstro.")
    print("ENTER = salvar | R = resetar | ESC = cancelar")

    cv2.namedWindow("Recortar Monstro", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Recortar Monstro", min(w, 1280), min(h, 720))
    cv2.setMouseCallback("Recortar Monstro", _on_mouse)

    while True:
        cv2.imshow("Recortar Monstro", _frame_display)
        key = cv2.waitKey(20) & 0xFF

        if key == 27:  # ESC
            print("Cancelado.")
            break

        elif key == ord('r'):  # Reset
            _start = (-1, -1)
            _end = (-1, -1)
            _frame_display = _frame_original.copy()
            print("Seleção resetada.")

        elif key == 13:  # ENTER
            x1, y1 = min(_start[0], _end[0]), min(_start[1], _end[1])
            x2, y2 = max(_start[0], _end[0]), max(_start[1], _end[1])

            if x2 - x1 < 5 or y2 - y1 < 5:
                print("Seleção muito pequena. Tente novamente.")
                continue

            crop = _frame_original[y1:y2, x1:x2]

            name = input("Nome do monstro (ex: mushroom, lawolf): ").strip()
            if not name:
                name = "monster"

            output_path = Path(f"assets/monsters/{name}/{name}.png")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(output_path), crop)

            print(f"Salvo em: {output_path}  ({x2-x1}x{y2-y1} px)")

            # Mostra o recorte salvo
            cv2.imshow("Recorte Salvo", crop)
            cv2.waitKey(2000)
            break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
