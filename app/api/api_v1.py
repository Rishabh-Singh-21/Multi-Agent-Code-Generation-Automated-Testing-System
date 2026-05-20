from fastapi import APIRouter

from app.api.routes import agents, health, memory

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(memory.router, prefix="/memory", tags=["memory"])
