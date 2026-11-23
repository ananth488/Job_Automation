"""Master API v1 router combining all resource endpoints."""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.resume import router as resume_router, resumes_alias_router
from app.api.v1.profile import router as profile_router
from app.api.v1.preferences import router as preferences_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.applications import router as applications_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.bot import router as bot_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.browser import router as browser_router
from app.api.v1.chat import router as chat_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(resume_router)
api_router.include_router(resumes_alias_router)
api_router.include_router(profile_router)
api_router.include_router(preferences_router)
api_router.include_router(jobs_router)
api_router.include_router(applications_router)
api_router.include_router(dashboard_router)
api_router.include_router(bot_router)
api_router.include_router(notifications_router)
api_router.include_router(browser_router)
api_router.include_router(chat_router)

