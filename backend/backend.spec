import sys
from pathlib import Path
import playwright as _pw

# Diretório do driver do Playwright (incluído no pacote Python)
playwright_driver_dir = Path(_pw.__file__).parent / 'driver'

a = Analysis(
    ['api.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        (str(playwright_driver_dir), 'playwright/driver'),
        ('browsers', 'browsers'),
        ('assets', 'assets'),
        ('config', 'config'),
    ],
    hiddenimports=[
        # uvicorn carrega muita coisa dinamicamente
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.loops.asyncio',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.http.h11_impl',
        'uvicorn.protocols.http.httptools_impl',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.protocols.websockets.websockets_impl',
        'uvicorn.protocols.websockets.wsproto_impl',
        'uvicorn.lifespan',
        'uvicorn.lifespan.off',
        'uvicorn.lifespan.on',
        # websockets
        'websockets',
        'websockets.legacy',
        'websockets.legacy.server',
        'websockets.legacy.client',
        # outros
        'anyio',
        'anyio._backends._asyncio',
        'anyio._backends._trio',
        'starlette.middleware.cors',
        'pydantic',
        'yaml',
        'cv2',
        'numpy',
        'loguru',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='backend',
)
