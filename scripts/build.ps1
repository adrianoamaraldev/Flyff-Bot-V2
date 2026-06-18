# Build completo: PyInstaller (backend) + Tauri (desktop)
# Rodar da raiz do projeto: powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1

$ErrorActionPreference = "Stop"
$root = "$PSScriptRoot\.."

Write-Host "=== 1/4 Instalando Chromium localmente ===" -ForegroundColor Cyan
$env:PLAYWRIGHT_BROWSERS_PATH = "$root\backend\browsers"
& "$root\venv\Scripts\playwright" install chromium

Write-Host "=== 2/4 Instalando PyInstaller ===" -ForegroundColor Cyan
& "$root\venv\Scripts\pip" install pyinstaller --quiet

Write-Host "=== 3/4 Buildando backend com PyInstaller ===" -ForegroundColor Cyan
Push-Location "$root\backend"
& "$root\venv\Scripts\pyinstaller" backend.spec --clean --noconfirm
Pop-Location

Write-Host "=== 4/4 Buildando app Tauri ===" -ForegroundColor Cyan

# Escreve config extra em arquivo temporario (sem BOM, sem aspas quebradas pelo PS)
$tauriExtraConf = "$root\desktop\src-tauri\tauri.release.conf.json"
[System.IO.File]::WriteAllText($tauriExtraConf, '{"bundle":{"resources":{"../../backend/dist/backend":"backend"}}}')

try {
    Push-Location "$root\desktop"
    npm run tauri build -- --config src-tauri/tauri.release.conf.json
    Pop-Location
} finally {
    if (Test-Path $tauriExtraConf) { Remove-Item $tauriExtraConf }
}

Write-Host ""
Write-Host "Build concluido!" -ForegroundColor Green
Write-Host "Instalador em: desktop\src-tauri\target\release\bundle\" -ForegroundColor Green
