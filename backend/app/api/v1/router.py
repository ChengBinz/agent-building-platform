from fastapi import APIRouter

api_router = APIRouter(prefix="/api/v1")

# Routers will be registered here:
# api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
# api_router.include_router(chat.router, prefix="/chat", tags=["对话"])
# api_router.include_router(knowledge.router, prefix="/knowledge", tags=["知识库"])
# api_router.include_router(admin.router, prefix="/admin", tags=["管理"])
# api_router.include_router(monitoring.router, prefix="/monitoring", tags=["监控"])
