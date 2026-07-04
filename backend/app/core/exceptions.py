"""Domain exceptions and their HTTP mapping.

Services and repositories raise these exceptions; a single FastAPI handler
translates them into consistent JSON error responses, keeping HTTP concerns
out of the business layer.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("exo.errors")


class ExoError(Exception):
    """Base class for all domain errors raised by EXO services."""

    status_code = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(ExoError):
    """Requested entity does not exist."""

    status_code = 404


class ConflictError(ExoError):
    """Operation conflicts with existing state (e.g. duplicate key)."""

    status_code = 409


class PermissionDeniedError(ExoError):
    """Operation requires a confirmation or permission that was not granted."""

    status_code = 403


def register_exception_handlers(app: FastAPI) -> None:
    """Attach the domain-error to JSON-response translation to the app."""

    @app.exception_handler(ExoError)
    async def _handle_exo_error(_request: Request, exc: ExoError) -> JSONResponse:
        logger.info("%s: %s", type(exc).__name__, exc.message)
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})
