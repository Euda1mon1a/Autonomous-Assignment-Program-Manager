# Schema Drift Tracking

> **Created:** 2026-02-17 | **Status:** Tracking (deferred migrations)
> **Decision:** Models exist as forward-looking code; migrations deferred until features are actively developed.

---

## Overview

Seven model files define 12 database tables that have **no corresponding Alembic migrations**. The tables do not exist in the database and any code path that queries them will fail at runtime.

**Impact:** Some routes ARE wired to these models (webhooks via `webhooks/service.py`, calendar subscriptions via `calendar_service.py`, exports via `routes/exports.py`). Requests to these endpoints will fail with database errors until migrations are created. These routes are not actively used in production but are reachable.

---

## Drifted Tables

| Table | Model File | Feature | Status |
|-------|-----------|---------|--------|
| `calendar_subscriptions` | `backend/app/models/calendar_subscription.py` | WebCal subscription feeds | Model only — no migration, no active routes |
| `export_jobs` | `backend/app/models/export_job.py` | Scheduled data exports | Model only — no migration |
| `export_job_executions` | `backend/app/models/export_job.py` | Export execution tracking | Model only — no migration |
| `oauth2_authorization_codes` | `backend/app/models/oauth2_authorization_code.py` | OAuth2 PKCE auth codes | Model only — no migration |
| `pkce_clients` | `backend/app/models/oauth2_client.py` | OAuth2 public client registration | Model only — no migration |
| `schema_versions` | `backend/app/models/schema_version.py` | API schema registry | Model only — no migration |
| `schema_change_events` | `backend/app/models/schema_version.py` | Schema change audit trail | Model only — no migration |
| `state_machine_instances` | `backend/app/models/state_machine.py` | Workflow state persistence | Model only — no migration |
| `state_machine_transitions` | `backend/app/models/state_machine.py` | State transition history | Model only — no migration |
| `webhooks` | `backend/app/webhooks/models.py` | Webhook endpoint registration | Model only — no migration |
| `webhook_deliveries` | `backend/app/webhooks/models.py` | Webhook delivery tracking | Model only — no migration |
| `webhook_dead_letters` | `backend/app/webhooks/models.py` | Failed webhook delivery queue | Model only — no migration |

---

## Decision Rationale

**Option chosen: Document and defer.**

1. **Low runtime risk** — routes exist but are not actively used in production; requests to webhook/calendar/export endpoints will fail until migrations are created
2. **Models serve as design documentation** — they capture the intended schema for when features are built
3. **Premature migration creates maintenance burden** — empty tables require index maintenance, backup overhead, and migration ordering complexity
4. **Features need full implementation** — creating tables without routes/services/tests creates a false sense of completeness

---

## When to Create Migrations

Create the Alembic migration for a table **when**:
1. A service or route is being built that will query the table
2. The feature is on the active development roadmap (Tier 1-2 priority)
3. Tests exist that validate the feature end-to-end

---

## Active Docs Annotated

The following documentation files have been annotated to clarify that these features have models but no database tables yet:

| File | Feature Referenced | Annotation Added |
|------|-------------------|-----------------|
| `docs/security/RBAC_AUDIT.md` | Webhooks | Schema drift note |
| `docs/security/RATE_LIMIT_AUDIT.md` | Webhooks | Schema drift note |
| `docs/security/SECURITY_PATTERN_AUDIT.md` | Webhooks | Schema drift note |
| `docs/api/game-theory.md` | Webhooks | Schema drift note |
| `docs/api/API_VALIDATION_AUDIT.md` | Webhooks | Schema drift note |
| `docs/api/ENDPOINT_CATALOG.md` | Webhooks, exports | Schema drift note |
| `docs/architecture/NOTIFICATION_SYSTEM_IMPLEMENTATION.md` | Webhooks | Schema drift note |
| `docs/api/CALENDAR_API.md` | Calendar subscriptions | Schema drift note |
| `docs/user-guide/exports.md` | Calendar subscriptions | Schema drift note |
| `docs/planning/MVP_STATUS_REPORT.md` | Export jobs | Schema drift note |

---

## Related

- `docs/tasks/GEMINI_DOC_ARCHIVAL_TASK.md` — 77-file archival sweep (completed PR #1146)
- `CLAUDE.md` → "Files and Patterns to Never Modify" (model changes require migration)
