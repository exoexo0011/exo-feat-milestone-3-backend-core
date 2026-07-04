"""PyInstaller entry point for the packaged EXO backend.

Runs the FastAPI application with uvicorn using settings resolved from the
environment (``EXO_HOST`` / ``EXO_PORT`` / ``EXO_ENV`` / ``EXO_DB_PATH`` ...).
The Electron shell spawns the resulting ``exo-backend`` executable and injects
those variables so data is written to a writable per-user directory.

``app.main`` is imported directly so PyInstaller statically bundles the whole
application graph.
"""

from __future__ import annotations

import uvicorn

from app.config import get_settings
from app.main import app


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
