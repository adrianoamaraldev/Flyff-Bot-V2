"""
Captura um frame do jogo e abre para você recortar o monstro.

Uso:
    python tools/capture_frame.py

O script vai:
  1. Abrir o Chrome com o jogo
  2. Esperar você fazer login e chegar perto de um monstro
  3. Ao pressionar ENTER, capturar o frame
  4. Abrir a imagem para você ver (salva em tools/frame_capturado.png)

Depois é só abrir a imagem em qualquer editor (Paint, etc),
recortar o monstro e salvar em assets/monsters/nome_do_monstro.png
"""

import asyncio
import os
import sys
from pathlib import Path

os.chdir(Path(__file__).parent.parent)
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.modules.browser_controller import BrowserController
from src.utils.config_manager import load_config


async def main():
    config = load_config("config/config.yaml")
    browser = BrowserController(config)

    print("Iniciando o Chrome...")
    await browser.start()
    print("\nFaça login no jogo e vá até onde tem monstros.")
    print("Quando estiver pronto, pressione ENTER para capturar o frame.")
    input()

    frame = await browser.get_frame()

    import cv2
    output_path = "tools/frame_capturado.png"
    cv2.imwrite(output_path, frame)
    print(f"\nFrame salvo em: {output_path}")
    print("Resolução capturada:", frame.shape[1], "x", frame.shape[0])
    print("\nAbra o arquivo, recorte o monstro e salve em assets/monsters/nome.png")
    print("Pressione ENTER para fechar o Chrome.")
    input()

    await browser.stop()


if __name__ == "__main__":
    asyncio.run(main())
