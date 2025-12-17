"""API routes."""
from fastapi import APIRouter

from app.api.routes import (
    absences,
    academic_blocks,
    assignments,
    audit,
    auth,
    blocks,
    calendar,
    calendar_export,
    certifications,
    credentials,
    daily_manifest,
    export,
    fmit_health,
    leave,
    me_dashboard,
    people,
    portal,
    procedures,
    resilience,
    role_views,
    rotation_templates,
    schedule,
    settings,
    swap,
    unified_heatmap,
    visualization,
)

api_router = APIRouter()

api_router.include_router(people.router, prefix="/people", tags=["people"])
api_router.include_router(blocks.router, prefix="/blocks", tags=["blocks"])
api_router.include_router(academic_blocks.router, prefix="/academic-blocks", tags=["academic-blocks"])
api_router.include_router(rotation_templates.router, prefix="/rotation-templates", tags=["rotation-templates"])
api_router.include_router(assignments.router, prefix="/assignments", tags=["assignments"])
api_router.include_router(absences.router, prefix="/absences", tags=["absences"])
api_router.include_router(schedule.router, prefix="/schedule", tags=["schedule"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(me_dashboard.router, prefix="/me", tags=["dashboard"])
api_router.include_router(export.router, prefix="/export", tags=["export"])
api_router.include_router(resilience.router, prefix="/resilience", tags=["resilience"])
api_router.include_router(procedures.router, prefix="/procedures", tags=["procedures"])
api_router.include_router(credentials.router, prefix="/credentials", tags=["credentials"])
api_router.include_router(certifications.router, prefix="/certifications", tags=["certifications"])
api_router.include_router(calendar.router, prefix="/calendar", tags=["calendar"])
api_router.include_router(calendar_export.router, prefix="/calendar", tags=["calendar"])
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
api_router.include_router(visualization.router, prefix="/visualization", tags=["visualization"])
api_router.include_router(unified_heatmap.router, prefix="/unified-heatmap", tags=["unified-heatmap"])
# FMIT scheduling routes
api_router.include_router(swap.router)  # prefix="/swaps" defined in router
api_router.include_router(leave.router)  # prefix="/leave" defined in router
api_router.include_router(portal.router)  # prefix="/portal" defined in router
api_router.include_router(fmit_health.router, prefix="/fmit", tags=["fmit-health"])
api_router.include_router(daily_manifest.router, prefix="/assignments", tags=["daily-manifest"])
api_router.include_router(role_views.router, prefix="/views", tags=["role-views"])
