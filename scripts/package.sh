#!/usr/bin/env bash
# Build distributable EXO desktop installers.
#
#   1. Bundle the backend into a self-contained executable (PyInstaller).
#   2. Package the Electron app + platform installer (electron-builder), which
#      ships the backend bundle and the plugins directory as extra resources.
#
# Run on the target platform (installers are OS-specific). Output lands in
# frontend/release/.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> [1/2] Bundling backend (PyInstaller)"
python -m pip install --quiet -r backend/requirements-dev.txt
(cd backend/packaging && pyinstaller --clean --noconfirm exo-backend.spec)

echo "==> [2/2] Packaging desktop app (electron-builder)"
(cd frontend && npm install --no-fund --no-audit && npm run dist)

echo "==> Done. Installers are in frontend/release/"
