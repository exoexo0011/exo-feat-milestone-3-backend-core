# Build distributable EXO desktop installers (Windows / PowerShell).
#
#   1. Bundle the backend into a self-contained executable (PyInstaller).
#   2. Package the Electron app + NSIS installer (electron-builder), shipping
#      the backend bundle and plugins directory as extra resources.
#
# Output lands in frontend\release\.
$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host '==> [1/2] Bundling backend (PyInstaller)'
python -m pip install --quiet -r backend\requirements-dev.txt
Push-Location backend\packaging
try { pyinstaller --clean --noconfirm exo-backend.spec } finally { Pop-Location }

Write-Host '==> [2/2] Packaging desktop app (electron-builder)'
Push-Location frontend
try {
  npm install --no-fund --no-audit
  npm run dist
} finally {
  Pop-Location
}

Write-Host '==> Done. Installers are in frontend\release\'
