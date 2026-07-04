"""Aggregated API router. Domain routers register here as they are implemented."""

from fastapi import APIRouter

from app.api import health

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
