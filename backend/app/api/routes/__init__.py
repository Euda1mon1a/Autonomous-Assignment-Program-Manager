"""API routes."""
from fastapi import APIRouter

from app.api.routes import (
    absences,
    academic_blocks,
    analytics,
    assignments,
    audit,
    auth,
    batch,
    blocks,
    calendar,
    certifications,
    conflict_resolution,
    credentials,
    daily_manifest,
    db_admin,
    docs,
    export,
    fmit_health,
    fmit_timeline,
    health,
    jobs,
    leave,
    me_dashboard,
    metrics,
    people,
    portal,
    procedures,
    rate_limit,
    reports,
    resilience,
    role_views,
    rotation_templates,
    schedule,
    scheduler_ops,
    search,
    settings,
    swap,
    unified_heatmap,
    upload,
    visualization,
    ws,
)

api_router = APIRouter()

# Core infrastructure routes
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(docs.router, prefix="/docs", tags=["documentation"])

api_router.include_router(people.router, prefix="/people", tags=["people"])
api_router.include_router(blocks.router, prefix="/blocks", tags=["blocks"])
api_router.include_router(academic_blocks.router, prefix="/academic-blocks", tags=["academic-blocks"])
api_router.include_router(rotation_templates.router, prefix="/rotation-templates", tags=["rotation-templates"])
api_router.include_router(assignments.router, prefix="/assignments", tags=["assignments"])
api_router.include_router(batch.router, prefix="/batch", tags=["batch"])
api_router.include_router(absences.router, prefix="/absences", tags=["absences"])
api_router.include_router(schedule.router, prefix="/schedule", tags=["schedule"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(me_dashboard.router, prefix="/me", tags=["dashboard"])
api_router.include_router(export.router, prefix="/export", tags=["export"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(resilience.router, prefix="/resilience", tags=["resilience"])
api_router.include_router(scheduler_ops.router, prefix="/scheduler", tags=["scheduler-ops"])
api_router.include_router(procedures.router, prefix="/procedures", tags=["procedures"])
api_router.include_router(credentials.router, prefix="/credentials", tags=["credentials"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(certifications.router, prefix="/certifications", tags=["certifications"])
api_router.include_router(calendar.router, prefix="/calendar", tags=["calendar"])
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
api_router.include_router(analytics.router, tags=["analytics"])
api_router.include_router(db_admin.router, tags=["db-admin"])
api_router.include_router(visualization.router, prefix="/visualization", tags=["visualization"])
api_router.include_router(unified_heatmap.router, prefix="/unified-heatmap", tags=["unified-heatmap"])
api_router.include_router(rate_limit.router, prefix="/rate-limit", tags=["rate-limit"])
# FMIT scheduling routes
api_router.include_router(swap.router)  # prefix="/swaps" defined in router
api_router.include_router(leave.router)  # prefix="/leave" defined in router
api_router.include_router(portal.router)  # prefix="/portal" defined in router
api_router.include_router(fmit_health.router, prefix="/fmit", tags=["fmit-health"])
api_router.include_router(fmit_timeline.router, prefix="/fmit_timeline", tags=["fmit-timeline"])
api_router.include_router(conflict_resolution.router, prefix="/conflicts", tags=["conflict-resolution"])
api_router.include_router(daily_manifest.router, prefix="/assignments", tags=["daily-manifest"])
api_router.include_router(role_views.router, prefix="/views", tags=["role-views"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(upload.router, prefix="/uploads", tags=["upload"])
api_router.include_router(ws.router, tags=["websocket"])
