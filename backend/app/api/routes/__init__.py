"""API routes."""
from fastapi import APIRouter

from app.api.routes import people, blocks, rotation_templates, assignments, absences, schedule, settings, auth, export, resilience, procedures, credentials, certifications, calendar, audit, visualization
from app.api.routes import swap, leave, portal, fmit_health

api_router = APIRouter()

api_router.include_router(people.router, prefix="/people", tags=["people"])
api_router.include_router(blocks.router, prefix="/blocks", tags=["blocks"])
api_router.include_router(rotation_templates.router, prefix="/rotation-templates", tags=["rotation-templates"])
api_router.include_router(assignments.router, prefix="/assignments", tags=["assignments"])
api_router.include_router(absences.router, prefix="/absences", tags=["absences"])
api_router.include_router(schedule.router, prefix="/schedule", tags=["schedule"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(export.router, prefix="/export", tags=["export"])
api_router.include_router(resilience.router, prefix="/resilience", tags=["resilience"])
api_router.include_router(procedures.router, prefix="/procedures", tags=["procedures"])
api_router.include_router(credentials.router, prefix="/credentials", tags=["credentials"])
api_router.include_router(certifications.router, prefix="/certifications", tags=["certifications"])
api_router.include_router(calendar.router, prefix="/calendar", tags=["calendar"])
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
api_router.include_router(visualization.router, prefix="/visualization", tags=["visualization"])
# FMIT scheduling routes
api_router.include_router(swap.router)  # prefix="/swaps" defined in router
api_router.include_router(leave.router)  # prefix="/leave" defined in router
api_router.include_router(portal.router)  # prefix="/portal" defined in router
api_router.include_router(fmit_health.router, prefix="/fmit", tags=["fmit-health"])
