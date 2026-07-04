"""Development entry point for the EXO backend.

Usage:
    python run.py
"""

import uvicorn

from app.config import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.env == "development",
    )


if __name__ == "__main__":
    main()
