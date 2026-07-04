"""EXO backend application factory and lifecycle.

Startup: configure logging, initialise the SQLite schema.
Shutdown: dispose the database engine.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.router import api_router
from app.api.ws import router as ws_router
from app.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.db.session import dispose_db, init_db
from app.logging_config import setup_logging
from app.services.ai import ProviderFactory

logger = logging.getLogger("exo.app")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application startup/shutdown lifecycle."""
    settings = get_settings()
    setup_logging(settings)
    await init_db()
    # Build the AI provider once and share it across requests/WebSockets so
    # HTTP-backed providers reuse a single connection pool.
    provider = ProviderFactory.create(settings)
    app.state.ai_provider = provider
    logger.info(
        "EXO backend %s started (env=%s, ai_provider=%s)",
        __version__,
        settings.env,
        settings.ai_provider,
    )
    yield
    await provider.aclose()
    await dispose_db()
    logger.info("EXO backend stopped")


def create_app() -> FastAPI:
    """Build and configure the FastAPI application instance."""
    settings = get_settings()

    app = FastAPI(
        title="EXO Backend",
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(api_router)
    app.include_router(ws_router)
    return app


app = create_app()
