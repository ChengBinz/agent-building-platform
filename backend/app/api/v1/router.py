from fastapi import APIRouter

from app.api.v1 import admin, auth, chat, knowledge, models, monitoring, users

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(chat.router, tags=["chat"])
api_router.include_router(knowledge.router, tags=["knowledge"])
api_router.include_router(models.router, tags=["models"])
api_router.include_router(monitoring.router, tags=["monitoring"])
api_router.include_router(users.router, tags=["users"])
api_router.include_router(admin.router, tags=["admin"])
