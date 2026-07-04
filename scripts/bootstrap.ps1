# EXO one-command developer bootstrap (Windows / PowerShell).
#   .\\scripts\\bootstrap.ps1          # setup + run
#   .\\scripts\\bootstrap.ps1 -SetupOnly
param([switch]$SetupOnly)
$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host '==> [1/4] Checking prerequisites'
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { throw 'Python 3.12 is required' }
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { throw 'Node 20+ (npm) is required' }

Write-Host '==> [2/4] Setting up Python virtual environment'
if (-not (Test-Path .venv)) { python -m venv .venv }
& .\.venv\Scripts\Activate.ps1
pip install --quiet --upgrade pip
pip install --quiet -r backend\requirements-dev.txt
if (-not (Test-Path backend\.env)) { Copy-Item backend\.env.example backend\.env }
New-Item -ItemType Directory -Force -Path database, logs | Out-Null

Write-Host '==> [3/4] Installing frontend dependencies'
Push-Location frontend; npm install --no-fund --no-audit; Pop-Location

if ($SetupOnly) { Write-Host '==> Setup complete.'; exit 0 }

Write-Host '==> [4/4] Starting backend and frontend dev servers'
$backend = Start-Process -PassThru -NoNewWindow .\.venv\Scripts\uvicorn.exe -ArgumentList 'app.main:app','--reload','--port','8000' -WorkingDirectory backend
Push-Location frontend
try { npm run dev } finally { Pop-Location; Stop-Process -Id $backend.Id -Force -ErrorAction SilentlyContinue }
