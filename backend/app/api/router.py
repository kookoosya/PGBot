from fastapi import APIRouter

from app.api.v1 import admin, ai_chat, auth, catalog, categories, classifieds, departments, feedback, issues, places, public_info, services, statistics, users, verification, visits, vk_webhook

api_router = APIRouter()

api_router.include_router(public_info.router, prefix="/public", tags=["public"])
api_router.include_router(ai_chat.router, prefix="/ai", tags=["ai"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(verification.router, prefix="/verification", tags=["verification"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(issues.router, prefix="/issues", tags=["issues"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(departments.router, prefix="/departments", tags=["departments"])
api_router.include_router(places.router, prefix="/places", tags=["places"])
api_router.include_router(services.router, prefix="/services", tags=["services"])
api_router.include_router(catalog.router, prefix="/catalog", tags=["catalog"])
api_router.include_router(classifieds.router, prefix="/classifieds", tags=["classifieds"])
api_router.include_router(statistics.router, prefix="/statistics", tags=["statistics"])
api_router.include_router(visits.router, prefix="/visits", tags=["visits"])
api_router.include_router(feedback.router, prefix="/feedback", tags=["feedback"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(vk_webhook.router, prefix="/vk", tags=["vk"])
