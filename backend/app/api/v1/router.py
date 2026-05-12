from fastapi import APIRouter

from app.api.v1 import admin, agents, auth, chat, knowledge, models, monitoring, users, mcp, skill

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(agents.router, tags=["agents"])
api_router.include_router(chat.router, tags=["chat"])
api_router.include_router(knowledge.router, tags=["knowledge"])
api_router.include_router(models.router, tags=["models"])
api_router.include_router(monitoring.router, tags=["monitoring"])
api_router.include_router(users.router, tags=["users"])
api_router.include_router(admin.router, tags=["admin"])
api_router.include_router(mcp.router, tags=["mcp"])
api_router.include_router(skill.router, tags=["skill"])
