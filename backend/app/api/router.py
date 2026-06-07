from fastapi import APIRouter

from app.api.v1 import admin, ai_chat, auth, categories, departments, issues, statistics, users, verification, vk_webhook

api_router = APIRouter()

api_router.include_router(ai_chat.router, prefix="/ai", tags=["ai"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(verification.router, prefix="/verification", tags=["verification"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(issues.router, prefix="/issues", tags=["issues"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(departments.router, prefix="/departments", tags=["departments"])
api_router.include_router(statistics.router, prefix="/statistics", tags=["statistics"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(vk_webhook.router, prefix="/vk", tags=["vk"])
