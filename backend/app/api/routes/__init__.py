"""API routes."""

from fastapi import APIRouter

from app.api.routes import (
    absences,
    academic_blocks,
    activities,
    admin_block_assignments,
    # approval_chain,  # QUARANTINED: requires_coordinator_or_above not implemented
    faculty_activities,
    faculty_schedule_preferences,
    admin_users,
    analytics,
    assignments,
    audit,
    audience_tokens,
    auth,
    backup,
    batch,
    block_scheduler,
    blocks,
    calendar,
    call_assignments,
    call_overrides,
    certifications,
    changelog,
    claude_chat,
    conflict_resolution,
    conflicts,
    constraints,
    credentials,
    daily_manifest,
    db_admin,
    docs,
    exotic_resilience,
    experiments,
    export,
    exports,
    fairness,
    fatigue_risk,
    features,
    fmit_assignments,
    fmit_health,
    fmit_timeline,
    game_theory,
    half_day_assignments,
    health,
    impersonation,
    import_staging,
    half_day_imports,
    imports,
    institutional_events,
    jobs,
    leave,
    mcp_proxy,
    me_dashboard,
    metrics,
    ml,
    oauth2,
    people,
    portal,
    procedures,
    profiling,
    proxy_coverage,
    qubo_templates,
    queue,
    quota,
    rag,
    rate_limit,
    reports,
    resident_weekly_requirements,
    resilience,
    role_views,
    rotation_templates,
    schedule,
    schedule_drafts,
    schedule_overrides,
    scheduler,
    scheduler_ops,
    scheduling_catalyst,
    search,
    sessions,
    settings,
    sso,
    swap,
    unified_heatmap,
    upload,
    visualization,
    webhooks,
    wellness,
    ws,
)

api_router = APIRouter()

# Core infrastructure routes
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(docs.router, prefix="/docs", tags=["documentation"])
api_router.include_router(features.router, prefix="/features", tags=["features"])
api_router.include_router(
    experiments.router, prefix="/experiments", tags=["experiments"]
)
api_router.include_router(changelog.router, prefix="/changelog", tags=["changelog"])

api_router.include_router(people.router, prefix="/people", tags=["people"])
api_router.include_router(blocks.router, prefix="/blocks", tags=["blocks"])
api_router.include_router(
    academic_blocks.router, prefix="/academic-blocks", tags=["academic-blocks"]
)
api_router.include_router(
    block_scheduler.router, prefix="/block-scheduler", tags=["block-scheduler"]
)
api_router.include_router(
    rotation_templates.router, prefix="/rotation-templates", tags=["rotation-templates"]
)
api_router.include_router(activities.router, prefix="/activities", tags=["activities"])
api_router.include_router(faculty_activities.router, tags=["faculty-activities"])
api_router.include_router(
    resident_weekly_requirements.router,
    prefix="/resident-weekly-requirements",
    tags=["resident-weekly-requirements"],
)
api_router.include_router(
    daily_manifest.router, prefix="/assignments", tags=["daily-manifest"]
)
api_router.include_router(
    assignments.router, prefix="/assignments", tags=["assignments"]
)
api_router.include_router(
    call_assignments.router
)  # prefix="/call-assignments" defined in router
api_router.include_router(batch.router, prefix="/batch", tags=["batch"])
api_router.include_router(absences.router, prefix="/absences", tags=["absences"])
api_router.include_router(schedule.router, prefix="/schedule", tags=["schedule"])
api_router.include_router(
    half_day_assignments.router,
    prefix="/half-day-assignments",
    tags=["half-day-assignments"],
)
# Aliases for frontend hardcoded paths
api_router.include_router(
    constraints.router, prefix="/schedule/constraints", tags=["schedule"]
)
api_router.include_router(metrics.router, prefix="/schedule/metrics", tags=["schedule"])
# NOTE: queue endpoints for /schedule/queue are now in schedule.py
# api_router.include_router(queue.router, prefix="/schedule/queue", tags=["schedule"])

api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(
    impersonation.router, prefix="/auth", tags=["auth", "impersonation"]
)
api_router.include_router(oauth2.router, prefix="/oauth2", tags=["oauth2"])
api_router.include_router(
    admin_users.router, prefix="/admin/users", tags=["admin-users"]
)
api_router.include_router(
    admin_block_assignments.router,
    prefix="/admin/block-assignments",
    tags=["admin-block-assignments"],
)
api_router.include_router(
    schedule_overrides.router,
    prefix="/admin/schedule-overrides",
    tags=["schedule-overrides"],
)
api_router.include_router(
    call_overrides.router,
    prefix="/admin/call-overrides",
    tags=["call-overrides"],
)
api_router.include_router(
    institutional_events.router,
    prefix="/admin/institutional-events",
    tags=["institutional-events"],
)
api_router.include_router(
    faculty_schedule_preferences.router,
    prefix="/admin/faculty-schedule-preferences",
    tags=["faculty-schedule-preferences"],
)
api_router.include_router(me_dashboard.router, prefix="/me", tags=["dashboard"])
api_router.include_router(export.router, prefix="/export", tags=["export"])
api_router.include_router(exports.router, prefix="/exports", tags=["exports"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(resilience.router, prefix="/resilience", tags=["resilience"])
api_router.include_router(
    exotic_resilience.router,
    prefix="/resilience/exotic",
    tags=["exotic-resilience"],
)
api_router.include_router(
    fatigue_risk.router
)  # prefix="/fatigue-risk" defined in router
api_router.include_router(
    game_theory.router, prefix="/game-theory", tags=["game-theory"]
)
api_router.include_router(
    scheduler_ops.router, prefix="/scheduler", tags=["scheduler-ops"]
)
api_router.include_router(procedures.router, prefix="/procedures", tags=["procedures"])
api_router.include_router(
    constraints.router, prefix="/constraints", tags=["constraints"]
)
api_router.include_router(
    credentials.router, prefix="/credentials", tags=["credentials"]
)
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(
    certifications.router, prefix="/certifications", tags=["certifications"]
)
api_router.include_router(calendar.router, prefix="/calendar", tags=["calendar"])
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
# QUARANTINED: approval_chain requires require_coordinator_or_above (not implemented)
# api_router.include_router(
#     approval_chain.router, prefix="/approval-chain", tags=["approval-chain"]
# )
api_router.include_router(analytics.router, tags=["analytics"])
api_router.include_router(fairness.router, tags=["fairness"])
api_router.include_router(db_admin.router, tags=["db-admin"])
api_router.include_router(backup.router, tags=["backup"])
api_router.include_router(
    visualization.router, prefix="/visualization", tags=["visualization"]
)
api_router.include_router(
    unified_heatmap.router, prefix="/unified-heatmap", tags=["unified-heatmap"]
)
api_router.include_router(rate_limit.router, prefix="/rate-limit", tags=["rate-limit"])
api_router.include_router(quota.router, prefix="/quota", tags=["quota"])
api_router.include_router(
    scheduling_catalyst.router,
    prefix="/scheduling-catalyst",
    tags=["scheduling-catalyst"],
)
api_router.include_router(ml.router, prefix="/ml", tags=["ml"])
api_router.include_router(rag.router, prefix="/rag", tags=["rag"])
api_router.include_router(
    qubo_templates.router, prefix="/qubo-templates", tags=["qubo-templates"]
)
api_router.include_router(mcp_proxy.router, prefix="/mcp", tags=["mcp-proxy"])
# FMIT scheduling routes
api_router.include_router(swap.router)  # prefix="/swaps" defined in router
api_router.include_router(leave.router)  # prefix="/leave" defined in router
api_router.include_router(portal.router)  # prefix="/portal" defined in router
api_router.include_router(fmit_health.router, prefix="/fmit", tags=["fmit-health"])
api_router.include_router(
    fmit_assignments.router, prefix="/fmit", tags=["fmit-assignments"]
)
api_router.include_router(
    fmit_timeline.router, prefix="/fmit_timeline", tags=["fmit-timeline"]
)
api_router.include_router(
    conflicts.router, prefix="/conflicts/analysis", tags=["conflicts-analysis"]
)
api_router.include_router(
    conflict_resolution.router, prefix="/conflicts", tags=["conflict-resolution"]
)

api_router.include_router(role_views.router, prefix="/views", tags=["role-views"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(queue.router, prefix="/queue", tags=["queue"])
api_router.include_router(upload.router, prefix="/uploads", tags=["upload"])
api_router.include_router(imports.router, prefix="/imports", tags=["imports"])
api_router.include_router(
    import_staging.router, prefix="/import", tags=["import-staging"]
)
api_router.include_router(
    half_day_imports.router, prefix="/import/half-day", tags=["import-half-day"]
)
api_router.include_router(
    schedule_drafts.router, prefix="/schedules/drafts", tags=["schedule-drafts"]
)
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
api_router.include_router(wellness.router)  # prefix="/wellness" defined in router
api_router.include_router(ws.router, tags=["websocket"])
api_router.include_router(
    proxy_coverage.router, prefix="/proxy-coverage", tags=["proxy-coverage"]
)

# Previously orphaned routes (wired 2026-01-18)
api_router.include_router(sso.router, prefix="/sso", tags=["sso"])
api_router.include_router(
    audience_tokens.router, prefix="/audience-tokens", tags=["audience-tokens"]
)
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(profiling.router, prefix="/profiling", tags=["profiling"])
api_router.include_router(claude_chat.router, tags=["claude-chat"])  # prefix in router
api_router.include_router(
    scheduler.router, prefix="/scheduler-jobs", tags=["scheduler-jobs"]
)
