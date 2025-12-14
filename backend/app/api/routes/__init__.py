"""API routes."""
from fastapi import APIRouter

from app.api.routes import people, blocks, rotation_templates, assignments, absences, schedule, settings, auth

api_router = APIRouter()

api_router.include_router(people.router, prefix="/people", tags=["people"])
api_router.include_router(blocks.router, prefix="/blocks", tags=["blocks"])
api_router.include_router(rotation_templates.router, prefix="/rotation-templates", tags=["rotation-templates"])
api_router.include_router(assignments.router, prefix="/assignments", tags=["assignments"])
api_router.include_router(absences.router, prefix="/absences", tags=["absences"])
api_router.include_router(schedule.router, prefix="/schedule", tags=["schedule"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
