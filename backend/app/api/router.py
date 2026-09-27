from fastapi import APIRouter

from app.api.routes import (
    admin_audit,
    admin_content,
    admin_dashboard,
    admin_registrations,
    admin_settings,
    admin_submissions,
    auth,
    public,
    registration_form,
    team,
    uploads,
)

api_router = APIRouter()
api_router.include_router(public.router)
api_router.include_router(registration_form.router)
api_router.include_router(auth.router)
api_router.include_router(team.router)
api_router.include_router(uploads.router)
api_router.include_router(admin_dashboard.router)
api_router.include_router(admin_registrations.router)
api_router.include_router(admin_content.router)
api_router.include_router(admin_submissions.router)
api_router.include_router(admin_settings.router)
api_router.include_router(admin_audit.router)
