import asyncio
from pathlib import Path
from typing import Optional, Tuple
import numpy as np
from PIL import Image
import io

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright
from loguru import logger

from src.utils.config_manager import BotConfig


class BrowserController:
    """
    Gerencia o Chrome via Playwright.
    - Captura frames da aba do jogo SEM precisar de foco
    - Envia cliques e teclas virtualmente (não move o mouse físico)
    - Mantém o jogo renderizando mesmo minimizado
    """

    def __init__(self, config: BotConfig):
        self.config = config
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._running = False

    # ── Inicialização ────────────────────────────────────────

    async def start(self):
        """Abre o Chrome e navega para o jogo."""
        logger.debug("Iniciando BrowserController...")

        self._playwright = await async_playwright().start()

        # Perfil persistente — salva login, cookies e configurações do jogo entre sessões
        profile_dir = str(Path("browser_profile").resolve())
        self._context = await self._playwright.chromium.launch_persistent_context(
            profile_dir,
            headless=self.config.browser.headless,
            args=self._chrome_args(),
            viewport={
                "width": self.config.browser.width,
                "height": self.config.browser.height,
            },
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )

        self._page = self._context.pages[0] if self._context.pages else await self._context.new_page()

        logger.debug(f"Navegando para {self.config.browser.game_url}")
        await self._page.goto(self.config.browser.game_url, wait_until="domcontentloaded")

        # Aguarda o jogo carregar (canvas aparecer)
        await self._wait_for_game()

        self._running = True
        logger.debug("BrowserController pronto!")

    async def stop(self):
        """Fecha o browser de forma limpa."""
        self._running = False
        if self._context:
            await self._context.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("BrowserController encerrado.")

    # ── Captura de Frame ─────────────────────────────────────

    async def get_frame(self) -> np.ndarray:
        """
        Captura um screenshot da aba do jogo e retorna como array numpy (BGR).
        Funciona sem foco — o jogo pode estar minimizado.
        """
        if not self._page:
            raise RuntimeError("Browser não iniciado. Chame start() primeiro.")

        screenshot_bytes = await self._page.screenshot(type="png")
        image = Image.open(io.BytesIO(screenshot_bytes)).convert("RGB")
        frame = np.array(image)

        # Converte RGB → BGR (padrão do OpenCV)
        return frame[:, :, ::-1].copy()

    async def get_region(self, x: int, y: int, width: int, height: int) -> np.ndarray:
        """Captura apenas uma região específica da tela (mais rápido que frame completo)."""
        frame = await self.get_frame()
        return frame[y:y+height, x:x+width]

    # ── Controles de Input Virtual ───────────────────────────

    async def click(self, x: int, y: int, button: str = "left", delay: float = 0.05):
        """
        Clique virtual na posição (x, y) da aba do jogo.
        NÃO move o mouse físico.
        """
        await self._page.mouse.click(int(x), int(y), button=button, delay=int(delay * 1000))
        logger.debug(f"Click virtual em ({x}, {y})")

    async def double_click(self, x: int, y: int):
        """Duplo clique virtual."""
        await self._page.mouse.dblclick(x, y)

    async def press_key(self, key: str, delay: float = 0.05):
        """
        Pressiona uma tecla virtualmente na aba do jogo.
        NÃO usa o teclado físico.
        Exemplos: 'v', 'h', 'F1', 'Escape'
        """
        if not key or not key.strip():
            return
        try:
            await self._page.keyboard.press(key)
            await asyncio.sleep(delay)
            logger.debug(f"Tecla virtual: {key}")
        except Exception as e:
            logger.warning(f"Erro ao pressionar tecla '{key}': {e}")

    async def hold_key(self, key: str, duration: float = 1.0):
        """Segura uma tecla por X segundos (útil para movimento)."""
        await self._page.keyboard.down(key)
        await asyncio.sleep(duration)
        await self._page.keyboard.up(key)
        logger.debug(f"Tecla segurada: {key} por {duration}s")

    async def move_mouse(self, x: int, y: int):
        """Move o mouse virtual para uma posição."""
        await self._page.mouse.move(x, y)

    async def inject_overlay(self):
        """Injeta um canvas transparente sobre o jogo para desenhar o overlay."""
        await self._page.evaluate("""
            if (!document.getElementById('bot-overlay')) {
                const canvas = document.createElement('canvas');
                canvas.id = 'bot-overlay';
                canvas.width = window.innerWidth;
                canvas.height = window.innerHeight;
                canvas.style.cssText = `
                    position: fixed; top: 0; left: 0; z-index: 99999;
                    pointer-events: none; width: 100%; height: 100%;
                `;
                document.body.appendChild(canvas);
            }
        """)

    async def draw_overlay(self, detections: list):
        """Atualiza o overlay no browser com as detecções atuais."""
        data = [{"x": int(d.x), "y": int(d.y), "label": d.label,
                 "conf": round(d.confidence * 100), "w": int(d.width),
                 "offset_y": 0} for d in detections]

        await self._page.evaluate("""(detections) => {
            const canvas = document.getElementById('bot-overlay');
            if (!canvas) return;
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            detections.forEach(d => {
                const nameY = d.y - 20;

                // Borda verde ao redor do nome
                ctx.strokeStyle = '#00ff00';
                ctx.lineWidth = 2;
                ctx.strokeRect(d.x - d.w / 2 - 2, nameY - 12, d.w + 4, 22);

                // Label
                ctx.fillStyle = '#00ff00';
                ctx.font = 'bold 12px Arial';
                ctx.fillText(d.label + ' ' + d.conf + '%', d.x - d.w / 2, nameY - 15);

                // Cruz vermelha no ponto de clique
                ctx.strokeStyle = '#ff0000';
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.moveTo(d.x - 12, d.y); ctx.lineTo(d.x + 12, d.y);
                ctx.moveTo(d.x, d.y - 12); ctx.lineTo(d.x, d.y + 12);
                ctx.stroke();
                ctx.beginPath();
                ctx.arc(d.x, d.y, 6, 0, Math.PI * 2);
                ctx.stroke();
            });
        }""", data)

    async def clear_overlay(self):
        """Limpa o overlay."""
        await self._page.evaluate("""
            const canvas = document.getElementById('bot-overlay');
            if (canvas) canvas.getContext('2d').clearRect(0, 0, canvas.width, canvas.height);
        """)

    async def setup_camera(self):
        """
        Configura a câmera antes de iniciar o farm:
        1. Inclina para visão top-down (arrastar vertical com botão direito)
        2. Afasta o zoom (scroll wheel para trás)
        """
        cx = self.config.browser.width // 2
        start_y = int(self.config.browser.height * 0.05)
        end_y   = int(self.config.browser.height * 0.95)

        await self._page.mouse.move(cx, start_y)
        await self._page.mouse.down(button="right")
        steps = 20
        for i in range(1, steps + 1):
            y = start_y + int((end_y - start_y) * i / steps)
            await self._page.mouse.move(cx, y)
            await asyncio.sleep(0.02)
        await self._page.mouse.up(button="right")

        await asyncio.sleep(0.3)

        await self._page.mouse.move(cx, self.config.browser.height // 2)
        for _ in range(8):
            await self._page.mouse.wheel(0, -150)
            await asyncio.sleep(0.05)

    async def rotate_camera(self, direction: str = "right", distance: int = 300):
        """
        Rotaciona a câmera arrastando o mouse com botão direito pressionado.
        direction: 'right' ou 'left'
        distance: pixels de deslocamento horizontal
        """
        cx = self.config.browser.width // 2
        cy = self.config.browser.height // 2

        start_x = cx - distance // 2 if direction == "right" else cx + distance // 2
        end_x   = cx + distance // 2 if direction == "right" else cx - distance // 2

        await self._page.mouse.move(start_x, cy)
        await self._page.mouse.down(button="right")
        # Arrasta em passos para parecer movimento suave
        steps = 10
        for i in range(1, steps + 1):
            x = start_x + int((end_x - start_x) * i / steps)
            await self._page.mouse.move(x, cy)
            await asyncio.sleep(0.02)
        await self._page.mouse.up(button="right")
        logger.debug(f"Câmera rotacionada para {direction}")

    # ── Utilitários ──────────────────────────────────────────

    async def _wait_for_game(self, timeout: int = 60):
        """Aguarda o canvas do jogo aparecer na página."""
        try:
            await self._page.wait_for_selector("canvas", timeout=timeout * 1000)
        except Exception:
            logger.warning("Canvas não detectado — o jogo pode demorar mais para carregar.")

    def _chrome_args(self) -> list:
        """
        Flags do Chrome que mantêm o jogo renderizando mesmo minimizado.
        Sem isso, o browser reduz o framerate quando perde foco.
        """
        return [
            # Mantém renderização em segundo plano
            "--disable-background-timer-throttling",
            "--disable-renderer-backgrounding",
            "--disable-backgrounding-occluded-windows",
            "--disable-ipc-flooding-protection",
            # WebGL funcionando mesmo sem foco
            "--enable-gpu-rasterization",
            "--enable-zero-copy",
            # Desativa economia de energia agressiva
            "--disable-features=OptimizeBackgroundRendering",
            # Evita detecção básica de automação
            "--disable-blink-features=AutomationControlled",
        ]

    @property
    def page(self) -> Optional[Page]:
        return self._page

    @property
    def is_running(self) -> bool:
        return self._running
