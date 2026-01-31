# API Endpoint Catalog

Comprehensive reference of all REST API endpoints in the Residency Scheduler.

> **Last Updated:** 2026-01-04
> **Total Endpoints:** 200+
> **Base URL:** `/api/v1`
> **OpenAPI Spec:** `http://localhost:8000/openapi.json`

---

## Table of Contents

1. [Overview](#overview)
2. [Health & Monitoring](#health--monitoring)
3. [Authentication & Authorization](#authentication--authorization)
4. [People Management](#people-management)
5. [Blocks & Calendar](#blocks--calendar)
6. [Block Scheduler](#block-scheduler)
7. [Assignments](#assignments)
8. [Call Assignments](#call-assignments)
9. [Absences & Leave](#absences--leave)
10. [Schedule Generation](#schedule-generation)
11. [Swaps & Exchanges](#swaps--exchanges)
13. [Rotation Templates](#rotation-templates)
14. [Procedures](#procedures)
15. [Credentials](#credentials)
16. [Certifications](#certifications)
17. [Settings](#settings)
18. [Analytics & Reporting](#analytics--reporting)
19. [Resilience Framework](#resilience-framework)
20. [Audit & Compliance](#audit--compliance)
21. [Search](#search)
22. [Exports](#exports)
23. [Conflict Resolution](#conflict-resolution)
24. [Portal & Dashboard](#portal--dashboard)
25. [Specialized Routes](#specialized-routes)
26. [Response Codes](#response-codes)
27. [Authentication Requirements](#authentication-requirements)

---

## Overview

### API Architecture

- **Framework:** FastAPI (Python 3.11+)
- **Authentication:** JWT with httpOnly cookies
- **Rate Limiting:** SlowAPI middleware
- **Idempotency:** Supported via `Idempotency-Key` header
- **Content-Type:** `application/json`

### Interactive Documentation

| Format | URL |
|--------|-----|
| **Swagger UI** | http://localhost:8000/docs |
| **ReDoc** | http://localhost:8000/redoc |
| **OpenAPI JSON** | http://localhost:8000/openapi.json |

---

## Health & Monitoring

**Prefix:** `/api/v1/health`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health/live` | None | Liveness probe for container orchestrators |
| GET | `/health/ready` | None | Readiness probe (checks DB, Redis) |
| GET | `/health/detailed` | Admin | Comprehensive health check across all services |
| GET | `/health/services/{service_name}` | Admin | Health check for specific service |
| GET | `/health/history` | Admin | Historical health check results |
| DELETE | `/health/history` | Admin | Clear health check history |
| GET | `/health/metrics` | Admin | Health performance metrics and uptime |
| POST | `/health/check` | Admin | Manually trigger health check |
| GET | `/health/status` | None | Simplified status for dashboards |

### Service Names

Valid `{service_name}` values: `database`, `redis`, `celery`

---

## Authentication & Authorization

**Prefix:** `/api/auth`

| Method | Path | Auth | Rate Limit | Description |
|--------|------|------|------------|-------------|
| POST | `/auth/login` | None | 5/min | OAuth2 password flow (form data) |
| POST | `/auth/login/json` | None | 5/min | JSON-based login |
| POST | `/auth/logout` | Bearer | - | Logout and blacklist token |
| POST | `/auth/refresh` | Refresh Token | - | Exchange refresh token |
| GET | `/auth/me` | Bearer | - | Get current user info |
| POST | `/auth/register` | Admin | 3/min | Register new user |
| GET | `/auth/users` | Admin | - | List all users |

### Token Structure

```
Access Token:  30 min lifetime, httpOnly cookie
Refresh Token: 7 day lifetime, rotated on use
```

See [Authentication](authentication.md) for full details.

---

## People Management

**Prefix:** `/api/v1/people`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/people` | Bearer | List all people with filters |
| GET | `/people/residents` | Bearer | List residents (filter by PGY level) |
| GET | `/people/faculty` | Bearer | List faculty (filter by specialty) |
| GET | `/people/{person_id}` | Bearer | Get person by ID |
| POST | `/people` | Scheduler | Create new person |
| PUT | `/people/{person_id}` | Scheduler | Update person details |
| DELETE | `/people/{person_id}` | Admin | Delete person |
| GET | `/people/{person_id}/credentials` | Bearer | Get credentials for person |
| GET | `/people/{person_id}/credentials/summary` | Bearer | Credential summary |
| GET | `/people/{person_id}/procedures` | Bearer | Procedures person can supervise |

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `type` | string | Filter by `resident` or `faculty` |
| `pgy_level` | int | Filter residents by PGY level (1-4) |
| `specialty` | string | Filter faculty by specialty |
| `is_active` | bool | Filter by active status |

---

## Blocks & Calendar

**Prefix:** `/api/v1/blocks`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/blocks` | Bearer | List blocks with date/number filters |
| GET | `/blocks/{block_id}` | Bearer | Get block by ID |
| POST | `/blocks` | Scheduler | Create new block |
| POST | `/blocks/generate` | Admin | Generate blocks for date range |
| DELETE | `/blocks/{block_id}` | Admin | Delete block |

**Prefix:** `/api/v1/academic-blocks`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/academic-blocks` | Bearer | List academic block definitions |

### Block Structure

- **730 blocks/year**: 365 days x 2 sessions (AM/PM)
- **Block numbering**: Sequential within academic year

---

## Block Scheduler

**Prefix:** `/api/block-scheduler`

Leave-eligible rotation matching for academic block scheduling. Automatically assigns residents with approved leave to leave-eligible rotations.

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/block-scheduler/dashboard` | Bearer | Dashboard view with leave info and capacity |
| POST | `/block-scheduler/schedule` | Bearer | Schedule block (dry_run mode available) |
| GET | `/block-scheduler/assignments/{id}` | Bearer | Get block assignment by ID |
| POST | `/block-scheduler/assignments` | Scheduler | Create manual assignment |
| PUT | `/block-scheduler/assignments/{id}` | Scheduler | Update assignment |
| DELETE | `/block-scheduler/assignments/{id}` | Scheduler | Delete assignment |

### Query Parameters (Dashboard)

| Parameter | Type | Description |
|-----------|------|-------------|
| `block_number` | int | Academic block (0-13) |
| `academic_year` | int | Academic year (e.g., 2025) |

### Schedule Request Body

```json
{
  "block_number": 5,
  "academic_year": 2025,
  "dry_run": true,
  "include_all_residents": true
}
```

### Assignment Reasons

| Reason | Description |
|--------|-------------|
| `leave_eligible_match` | Auto-assigned due to leave |
| `coverage_priority` | Fills non-leave-eligible rotation |
| `balanced` | Workload balance |
| `manual` | Manual override |

See [Block Scheduler](block-scheduler.md) for full details.

---

## Assignments

**Prefix:** `/api/v1/assignments`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/assignments` | Bearer | List with date/person/role filters |
| GET | `/assignments/{assignment_id}` | Bearer | Get assignment by ID |
| POST | `/assignments` | Scheduler | Create assignment (returns warnings) |
| PUT | `/assignments/{assignment_id}` | Scheduler | Update with optimistic locking |
| DELETE | `/assignments/{assignment_id}` | Scheduler | Delete assignment |
| DELETE | `/assignments` | Admin | Bulk delete by date range |
| GET | `/assignments/manifest` | Bearer | Daily manifest |

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `start_date` | date | Filter by start date |
| `end_date` | date | Filter by end date |
| `person_id` | uuid | Filter by person |
| `rotation_id` | uuid | Filter by rotation |
| `rotation_type` | string | Filter by rotation type |

---

## Call Assignments

**Prefix:** `/api/v1/call-assignments`

Endpoints for managing overnight and weekend faculty call assignments. Solver-generated call assignments emerge from constraint optimization during schedule generation.

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/call-assignments` | Bearer | List call assignments with filters |
| GET | `/call-assignments/{call_id}` | Bearer | Get call assignment by ID |
| POST | `/call-assignments` | Scheduler | Create call assignment |
| PUT | `/call-assignments/{call_id}` | Scheduler | Update call assignment |
| DELETE | `/call-assignments/{call_id}` | Scheduler | Delete call assignment |
| POST | `/call-assignments/bulk` | Admin | Bulk create (used by solver) |
| GET | `/call-assignments/by-person/{person_id}` | Bearer | Get calls for specific person |
| GET | `/call-assignments/by-date/{date}` | Bearer | Get calls for specific date |
| GET | `/call-assignments/reports/coverage` | Admin | Coverage gap analysis |
| GET | `/call-assignments/reports/equity` | Admin | Distribution equity report |

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `start_date` | date | Filter by start date (inclusive) |
| `end_date` | date | Filter by end date (inclusive) |
| `person_id` | uuid | Filter by person |
| `call_type` | string | Filter by type: `overnight`, `weekend`, `backup` |
| `skip` | int | Pagination offset (default: 0) |
| `limit` | int | Max records (default: 100, max: 1000) |

### Call Types

| Type | Description | Days |
|------|-------------|------|
| `overnight` | Sun-Thu overnight call | Sun PM → Mon AM through Thu PM → Fri AM |
| `weekend` | Fri-Sat FMIT coverage | Fri PM → Sun PM (FMIT faculty) |
| `backup` | Emergency backup coverage | Any day as needed |

### Coverage Report Response

```json
{
  "start_date": "2025-01-01",
  "end_date": "2025-01-31",
  "total_expected_nights": 22,
  "covered_nights": 20,
  "coverage_percentage": 90.91,
  "gaps": ["2025-01-15", "2025-01-22"]
}
```

### Equity Report Response

```json
{
  "start_date": "2025-01-01",
  "end_date": "2025-01-31",
  "faculty_count": 8,
  "total_overnight_calls": 22,
  "sunday_call_stats": {"min": 0, "max": 2, "mean": 0.75, "stdev": 0.5},
  "weekday_call_stats": {"min": 2, "max": 4, "mean": 2.75, "stdev": 0.71},
  "distribution": [
    {"person_id": "...", "name": "Dr. Smith", "sunday_calls": 2, "weekday_calls": 3, "total_calls": 5}
  ]
}
```

---

## Absences & Leave

### Absences

**Prefix:** `/api/v1/absences`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/absences` | Bearer | List absences with filters |
| GET | `/absences/{absence_id}` | Bearer | Get absence by ID |
| POST | `/absences` | Scheduler | Create new absence |
| PUT | `/absences/{absence_id}` | Scheduler | Update absence |
| DELETE | `/absences/{absence_id}` | Scheduler | Delete absence |

### Leave Management

**Prefix:** `/api/v1/leave`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/leave/` | Bearer | List leave records |
| GET | `/leave/calendar` | Bearer | Leave calendar with conflict markers |
| POST | `/leave/` | Scheduler | Create leave record |
| PUT | `/leave/{leave_id}` | Scheduler | Update leave record |
| DELETE | `/leave/{leave_id}` | Scheduler | Delete leave record |
| POST | `/leave/webhook` | HMAC | External leave system webhook |
| POST | `/leave/bulk-import` | Admin | Bulk import leave records |

### Absence Types

`VACATION`, `SICK`, `CONFERENCE`, `TDY`, `DEPLOYMENT`, `MATERNITY`, `PATERNITY`, `BEREAVEMENT`

---

## Schedule Generation

**Prefix:** `/api/v1/schedule`

| Method | Path | Auth | Idempotent | Description |
|--------|------|------|------------|-------------|
| POST | `/schedule/generate` | Scheduler | Yes | Generate schedule |
| GET | `/schedule/validate` | Bearer | - | Validate ACGME compliance |
| POST | `/schedule/emergency-coverage` | Scheduler | - | Handle emergency absence |
| GET | `/schedule/{start_date}/{end_date}` | Bearer | - | Get schedule for date range |
| POST | `/schedule/import/analyze` | Scheduler | - | Analyze imported schedules |
| POST | `/schedule/import/analyze-file` | Scheduler | - | Quick file analysis |
| POST | `/schedule/swaps/find` | Bearer | - | Find swap candidates (Excel) |
| POST | `/schedule/swaps/candidates` | Bearer | - | Find swap candidates (JSON) |

---

## Half-Day Import (Block Template2)

**Prefix:** `/api/v1/import/half-day`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/import/half-day/stage` | Admin | Stage Block Template2 xlsx and compute diffs |
| GET | `/import/half-day/batches/{batch_id}/preview` | Admin | Preview staged diffs + metrics |
| POST | `/import/half-day/batches/{batch_id}/draft` | Admin | Create schedule draft from selected diffs |

**Notes:**
- Draft creation is **atomic**: any failed row aborts and no draft is created.
- Draft failures return `400` with `failed_ids` in the error detail.

### Schedule Generation Request

```json
{
  "start_date": "2024-07-01",
  "end_date": "2025-06-30",
  "config": {
    "prioritize_fairness": true,
    "max_consecutive_days": 6
  }
}
```

### Idempotency

Include `Idempotency-Key` header to prevent duplicate generation:
```
Idempotency-Key: unique-request-id-12345
```

---

## Swaps & Exchanges

**Prefix:** `/api/v1/swaps`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/swaps/execute` | Scheduler | Execute FMIT swap between faculty |
| POST | `/swaps/validate` | Bearer | Validate swap without executing |
| GET | `/swaps/history` | Bearer | Get swap history with filters |
| GET | `/swaps/{swap_id}` | Bearer | Get specific swap record |
| POST | `/swaps/{swap_id}/rollback` | Scheduler | Rollback swap (24-hour window) |

### Swap Types

| Type | Description |
|------|-------------|
| `ONE_TO_ONE` | Direct exchange between two faculty |
| `ABSORB` | One faculty absorbs another's shift |
| `REDISTRIBUTE` | Shift redistributed across pool |

See [Swaps](swaps.md) for full details.

---

## Rotation Templates

**Prefix:** `/api/v1/rotation-templates`

### Core CRUD Operations

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/rotation-templates` | Bearer | List templates (supports `rotation_type`, `include_archived` filters) |
| GET | `/rotation-templates/{template_id}` | Bearer | Get template by ID |
| POST | `/rotation-templates` | Bearer | Create template |
| PUT | `/rotation-templates/{template_id}` | Bearer | Update template |
| DELETE | `/rotation-templates/{template_id}` | Bearer | Hard delete template |

### Batch Operations (Atomic)

All batch operations support `dry_run` mode for validation without side effects.
Maximum 100 items per batch. Operations are atomic (all-or-nothing).

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| DELETE | `/rotation-templates/batch` | Bearer | Delete multiple templates atomically |
| PUT | `/rotation-templates/batch` | Bearer | Update multiple templates atomically |
| POST | `/rotation-templates/batch` | Bearer | Create multiple templates atomically |
| POST | `/rotation-templates/batch/conflicts` | Bearer | Check conflicts before batch operations |
| POST | `/rotation-templates/export` | Bearer | Export templates with patterns/preferences |

### Archive/Restore Operations

Soft delete alternative that preserves data for recovery.

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| PUT | `/rotation-templates/{template_id}/archive` | Bearer | Archive single template (soft delete) |
| PUT | `/rotation-templates/{template_id}/restore` | Bearer | Restore archived template |
| PUT | `/rotation-templates/batch/archive` | Bearer | Archive multiple templates atomically |
| PUT | `/rotation-templates/batch/restore` | Bearer | Restore multiple archived templates |

### Weekly Patterns

Visual grid editor support (7 days x 2 slots = 14 max patterns per template).

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/rotation-templates/{template_id}/patterns` | Bearer | Get all weekly patterns for template |
| PUT | `/rotation-templates/{template_id}/patterns` | Bearer | Replace all patterns atomically |
| PUT | `/rotation-templates/batch/patterns` | Bearer | Apply same pattern to multiple templates |

### Rotation Preferences

Soft constraints for scheduling optimizer.

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/rotation-templates/{template_id}/preferences` | Bearer | Get all preferences for template |
| PUT | `/rotation-templates/{template_id}/preferences` | Bearer | Replace all preferences atomically |
| PUT | `/rotation-templates/batch/preferences` | Bearer | Apply same preferences to multiple templates |

### Version History

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/rotation-templates/{template_id}/history` | Bearer | Get version history (SQLAlchemy-Continuum) |

### Rotation Types

`CLINIC`, `INPATIENT`, `PROCEDURES`, `CONFERENCE`, `ADMIN`, `CALL`, `OFF`

### Preference Types

| Type | Description |
|------|-------------|
| `full_day_grouping` | Prefer AM+PM of same activity together |
| `consecutive_specialty` | Group specialty sessions consecutively |
| `avoid_isolated` | Avoid single orphaned half-day sessions |
| `preferred_days` | Prefer specific activities on specific days |
| `avoid_friday_pm` | Keep Friday PM open as travel buffer |
| `balance_weekly` | Distribute activities evenly across week |

### Batch Request Examples

**Batch Delete:**
```json
{
  "template_ids": ["uuid1", "uuid2", "uuid3"],
  "dry_run": false
}
```

**Batch Update:**
```json
{
  "templates": [
    {"template_id": "uuid1", "updates": {"max_residents": 5}},
    {"template_id": "uuid2", "updates": {"rotation_type": "inpatient"}}
  ],
  "dry_run": false
}
```

**Batch Create:**
```json
{
  "templates": [
    {"name": "New Clinic", "rotation_type": "clinic"},
    {"name": "New Inpatient", "rotation_type": "inpatient"}
  ],
  "dry_run": false
}
```

---

## Procedures

**Prefix:** `/api/v1/procedures`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/procedures` | Bearer | List with specialty/category filters |
| GET | `/procedures/specialties` | Bearer | Get unique specialties |
| GET | `/procedures/categories` | Bearer | Get unique categories |
| GET | `/procedures/by-name/{name}` | Bearer | Get procedure by name |
| GET | `/procedures/{procedure_id}` | Bearer | Get procedure by ID |
| POST | `/procedures` | Scheduler | Create procedure |
| PUT | `/procedures/{procedure_id}` | Scheduler | Update procedure |
| DELETE | `/procedures/{procedure_id}` | Admin | Delete procedure |
| POST | `/procedures/{procedure_id}/deactivate` | Scheduler | Soft delete |
| POST | `/procedures/{procedure_id}/activate` | Scheduler | Reactivate |

---

## Credentials

**Prefix:** `/api/v1/credentials`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/credentials/expiring` | Bearer | Credentials expiring within N days |
| GET | `/credentials/by-person/{person_id}` | Bearer | Credentials for person |
| GET | `/credentials/by-procedure/{procedure_id}` | Bearer | Who can supervise procedure |
| GET | `/credentials/qualified-faculty/{procedure_id}` | Bearer | All qualified faculty |
| GET | `/credentials/check/{person_id}/{procedure_id}` | Bearer | Check qualification |
| GET | `/credentials/summary/{person_id}` | Bearer | Credential summary |
| GET | `/credentials/{credential_id}` | Bearer | Get credential |
| POST | `/credentials` | Scheduler | Create credential |
| PUT | `/credentials/{credential_id}` | Scheduler | Update credential |
| DELETE | `/credentials/{credential_id}` | Admin | Delete credential |
| POST | `/credentials/{credential_id}/suspend` | Scheduler | Suspend credential |
| POST | `/credentials/{credential_id}/activate` | Scheduler | Activate credential |
| POST | `/credentials/{credential_id}/verify` | Admin | Mark as verified |

---

## Certifications

**Prefix:** `/api/v1/certifications`

### Certification Types

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/certifications/types` | Bearer | List types (BLS, ACLS, etc.) |
| GET | `/certifications/types/{cert_type_id}` | Bearer | Get type by ID |
| POST | `/certifications/types` | Admin | Create type |
| PUT | `/certifications/types/{cert_type_id}` | Admin | Update type |

### Compliance & Tracking

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/certifications/expiring` | Bearer | Certs expiring within N days |
| GET | `/certifications/compliance` | Bearer | Overall compliance summary |
| GET | `/certifications/compliance/{person_id}` | Bearer | Person's compliance |

### Person Certifications

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/certifications/by-person/{person_id}` | Bearer | Person's certifications |
| GET | `/certifications/{cert_id}` | Bearer | Get certification |
| POST | `/certifications` | Scheduler | Add certification |
| PUT | `/certifications/{cert_id}` | Scheduler | Update certification |
| POST | `/certifications/{cert_id}/renew` | Scheduler | Renew with new dates |
| DELETE | `/certifications/{cert_id}` | Admin | Delete certification |
| POST | `/certifications/admin/send-reminders` | Admin | Trigger reminder emails |

---

## Settings

**Prefix:** `/api/v1/settings`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/settings` | Admin | Get current settings |
| POST | `/settings` | Admin | Full replacement update |
| PATCH | `/settings` | Admin | Partial update |
| DELETE | `/settings` | Admin | Reset to defaults |

---

## Analytics & Reporting

**Prefix:** `/api/v1/analytics`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/analytics/metrics/current` | Bearer | Current schedule metrics |
| GET | `/analytics/metrics/history` | Bearer | Metric time series |
| GET | `/analytics/fairness/trend` | Bearer | Fairness trend over months |
| GET | `/analytics/compare/{version_a}/{version_b}` | Bearer | Compare schedule versions |
| POST | `/analytics/what-if` | Scheduler | Predict impact of changes |
| GET | `/analytics/export/research` | Admin | Export anonymized data |

### Reports

**Prefix:** `/api/v1/reports`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/reports/schedule` | Bearer | Generate schedule PDF |
| POST | `/reports/compliance` | Bearer | ACGME compliance PDF |
| POST | `/reports/faculty-summary` | Bearer | Faculty workload summary |
| POST | `/reports/analytics` | Bearer | Analytics PDF |

See [Analytics](analytics.md) for full details.

---

## Resilience Framework

**Prefix:** `/api/v1/resilience`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/resilience/health` | Bearer | System resilience health |
| POST | `/resilience/crisis/activate` | Admin | Activate crisis mode |
| POST | `/resilience/crisis/deactivate` | Admin | Deactivate crisis mode |
| GET | `/resilience/fallback` | Bearer | List fallback schedules |
| POST | `/resilience/fallback/activate` | Admin | Switch to fallback |
| POST | `/resilience/fallback/deactivate` | Admin | Return to main schedule |
| POST | `/resilience/load-shedding` | Admin | Control load shedding |
| GET | `/resilience/vulnerability` | Bearer | N-1/N-2 vulnerability analysis |
| GET | `/resilience/homeostasis` | Bearer | Feedback loop analysis |
| GET | `/resilience/events/history` | Bearer | Historical resilience events |
| GET | `/resilience/health-checks/history` | Bearer | Health check history |

### Defense Levels

```
GREEN → YELLOW → ORANGE → RED → BLACK
```

See [Cross-Disciplinary Resilience](cross-disciplinary-resilience.md) for full details.

---

## Audit & Compliance

**Prefix:** `/api/v1/audit`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/audit/logs` | Admin | Paginated audit logs |
| GET | `/audit/logs/{log_id}` | Admin | Get specific entry |
| GET | `/audit/statistics` | Admin | Statistics by action/entity/user |
| GET | `/audit/users` | Admin | Users with audit activity |
| POST | `/audit/export` | Admin | Export logs (CSV/JSON/PDF) |
| POST | `/audit/mark-reviewed` | Admin | Mark entries as reviewed |

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `action` | string | Filter by action type |
| `entity_type` | string | Filter by entity |
| `user_id` | uuid | Filter by user |
| `severity` | string | Filter by severity |
| `start_date` | datetime | Start of date range |
| `end_date` | datetime | End of date range |
| `page` | int | Page number |
| `page_size` | int | Items per page |

---

## Search

**Prefix:** `/api/v1/search`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/search` | Bearer | Full-text search |
| GET | `/search/quick` | Bearer | Quick search with minimal params |
| POST | `/search/people` | Bearer | Search people with filters |
| POST | `/search/rotations` | Bearer | Search rotation templates |
| POST | `/search/procedures` | Bearer | Search procedures |

---

## Exports

**Prefix:** `/api/v1/export`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/export/schedule` | Bearer | Export schedule data |
| POST | `/export/compliance` | Bearer | Export compliance data |

**Prefix:** `/api/v1/exports`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/exports` | Bearer | List exports |
| GET | `/exports/{export_id}` | Bearer | Download export |

---

## Conflict Resolution

**Prefix:** `/api/v1/conflicts`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/conflicts/{conflict_id}/analyze` | Bearer | Deep conflict analysis |
| GET | `/conflicts/{conflict_id}/options` | Bearer | Resolution strategies |
| POST | `/conflicts/{conflict_id}/resolve` | Scheduler | Auto-resolve if safe |
| POST | `/conflicts/batch/resolve` | Scheduler | Batch resolve |

---

## Portal & Dashboard

### Personal Dashboard

**Prefix:** `/api/v1/me`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/me/dashboard` | Bearer | Personal dashboard |

### Faculty Portal

**Prefix:** `/api/v1/portal`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/portal/schedule` | Bearer | My schedule |
| GET | `/portal/swaps` | Bearer | My swap requests |
| GET | `/portal/marketplace` | Bearer | Available swap opportunities |
| POST | `/portal/swaps/request` | Bearer | Create swap request |
| POST | `/portal/swaps/respond` | Bearer | Accept/decline swap |
| GET | `/portal/preferences` | Bearer | My preferences |
| PUT | `/portal/preferences` | Bearer | Update preferences |

---

## Specialized Routes

### Metrics & Monitoring

| Prefix | Description |
|--------|-------------|
| `/api/v1/metrics` | Prometheus-compatible metrics |

### Feature Flags

| Prefix | Description |
|--------|-------------|
| `/api/v1/features` | Feature flag management |
| `/api/v1/experiments` | A/B test experiments |

### Scheduler Operations

| Prefix | Description |
|--------|-------------|
| `/api/v1/scheduler/sitrep` | Situation report |
| `/api/v1/scheduler/fix-it` | Task recovery |
| `/api/v1/scheduler/approve` | Task approval |

### Batch Operations

| Prefix | Description |
|--------|-------------|
| `/api/v1/batch/assignments` | Bulk assignment creation |
| `/api/v1/batch/absences` | Bulk absence creation |

### WebSocket

| Prefix | Description |
|--------|-------------|
| `/ws` | Real-time notifications |

### Advanced Features

| Prefix | Description |
|--------|-------------|
| `/api/v1/ml` | ML-based predictions |
| `/api/v1/game-theory` | Game-theoretic analysis |
| `/api/v1/visualization` | Schedule visualization data |
| `/api/v1/unified-heatmap` | Cross-domain heatmap |
| `/api/v1/scheduling-catalyst` | Barrier analysis |
| `/api/v1/quota` | Work hour quotas |
| `/api/v1/rate-limit` | Rate limit status |

---

## Response Codes

### Success Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | GET, PATCH, most operations |
| 201 | Created | POST creating resources |
| 204 | No Content | DELETE, operations with no body |
| 207 | Multi-Status | Partial success (schedule generation) |

### Error Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 400 | Bad Request | Invalid request format |
| 401 | Unauthorized | Missing or invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Double-submit, overlapping dates |
| 422 | Unprocessable Entity | Validation failure |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |

### Error Response Format

```json
{
  "detail": "Error message",
  "code": "ERROR_CODE"
}
```

### Validation Error Format

```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "Validation message",
      "type": "value_error"
    }
  ]
}
```

---

## Authentication Requirements

### Role Hierarchy

| Role | Description | Access Level |
|------|-------------|--------------|
| Admin | System administrator | Full access |
| Scheduler | Schedule coordinator | Modify schedules, assignments |
| Faculty | Teaching faculty | View + own swaps |
| Resident | Resident physician | View only |
| Coordinator | Department coordinator | Limited admin |

### Authentication Methods

| Method | Header/Cookie | Description |
|--------|---------------|-------------|
| Bearer Token | `Authorization: Bearer <token>` | API clients |
| httpOnly Cookie | Automatic | Browser clients |
| Refresh Token | POST body | Token renewal |
| HMAC Signature | `X-Webhook-Signature` | Webhooks |

### Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/auth/login` | 5 requests | 1 minute |
| `/auth/register` | 3 requests | 1 minute |
| Other endpoints | 100 requests | 1 minute |

### Rate Limit Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1703433600
```

---

## Quick Reference

### Most Common Endpoints

| Action | Method | Endpoint |
|--------|--------|----------|
| Login | POST | `/api/auth/login` |
| Get schedule | GET | `/api/v1/schedule/{start}/{end}` |
| Generate schedule | POST | `/api/v1/schedule/generate` |
| List people | GET | `/api/v1/people` |
| Create assignment | POST | `/api/v1/assignments` |
| Execute swap | POST | `/api/v1/swaps/execute` |
| Validate compliance | GET | `/api/v1/schedule/validate` |
| System health | GET | `/api/v1/health/status` |

### cURL Examples

```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=password"

# Authenticated request
curl http://localhost:8000/api/v1/people \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."

# Generate schedule (with idempotency)
curl -X POST http://localhost:8000/api/v1/schedule/generate \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: unique-request-123" \
  -d '{"start_date": "2024-07-01", "end_date": "2025-06-30"}'
```

---

## Related Documentation

- [Authentication](authentication.md) - Token management details
- [Block Scheduler](block-scheduler.md) - Leave-eligible rotation matching
- [Schedule](schedule.md) - Schedule generation details
- [Swaps](swaps.md) - Swap marketplace operations
- [Analytics](analytics.md) - Metrics and reporting
- [Cross-Disciplinary Resilience](cross-disciplinary-resilience.md) - Resilience framework

---

*This catalog is auto-generated from route inspection. For the most current endpoints, consult the OpenAPI spec at `/openapi.json`.*
