#!/usr/bin/env bash
# EXO one-command developer bootstrap.
#
# Installs backend + frontend dependencies and starts both dev servers.
#   ./scripts/bootstrap.sh            # setup + run
#   ./scripts/bootstrap.sh --setup    # setup only
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "==> [1/4] Checking prerequisites"
command -v python3 >/dev/null || { echo "python3 is required"; exit 1; }
command -v npm >/dev/null || { echo "npm (Node 20+) is required"; exit 1; }

echo "==> [2/4] Setting up Python virtual environment"
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r backend/requirements-dev.txt

if [ ! -f backend/.env ]; then
  cp backend/.env.example backend/.env
  echo "    Created backend/.env from template"
fi
mkdir -p database logs

echo "==> [3/4] Installing frontend dependencies"
(cd frontend && npm install --no-fund --no-audit)

if [ "${1:-}" = "--setup" ]; then
  echo "==> Setup complete. Run './scripts/bootstrap.sh' to start dev servers."
  exit 0
fi

echo "==> [4/4] Starting backend (http://127.0.0.1:8000) and frontend (http://127.0.0.1:5173)"
trap 'kill 0' EXIT INT TERM
(cd backend && ../.venv/bin/uvicorn app.main:app --reload --port 8000) &
(cd frontend && npm run dev) &
wait
