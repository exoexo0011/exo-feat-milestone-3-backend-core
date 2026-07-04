"""Aggregated API router. Domain routers register here as they are implemented."""

from fastapi import APIRouter

from app.api import chat, health, plugins, system, tools

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(chat.router)
api_router.include_router(tools.router)
api_router.include_router(plugins.router)
api_router.include_router(system.router)
