# Codex Review Findings - 2025-12-21

## Critical (Fix Before Production)
| Issue | Location | Description | Suggested Fix |
|-------|----------|-------------|---------------|
| ACGME compliance checks are effectively disabled on assignment events | backend/app/events/handlers/schedule_events.py:151 | Event handlers import `app.scheduling.acgme_validator` (file does not exist) and instantiate `ACGMEValidator()` with no DB session, so compliance validation never runs on create/update events. This is a direct ACGME compliance gap. | Update import to `app.scheduling.validator`, inject a DB session, and actually invoke `validate_all` (or remove the dead try/except) so assignment events trigger real validation; add regression tests for event handlers. |

## High (Fix This Sprint)
| Issue | Location | Description | Suggested Fix |
|-------|----------|-------------|---------------|
| Coverage rate always computes to 0% due to SQLAlchemy filter bug | backend/app/scheduling/validator.py:149 | `not Block.is_weekend` is evaluated in Python, producing `False` and turning the SQLAlchemy filter into `WHERE false`, so `total_blocks` is 0 and coverage rate is always 0%. | Replace with `Block.is_weekend.is_(False)` (and consider `Block.is_holiday.is_(False)`) to keep the predicate in SQL. |
| Faculty supervision assignments omit `rotation_template_id` | backend/app/scheduling/engine.py:778 | Faculty assignments created in `_assign_faculty` have no `rotation_template_id`, leaving `activity_type` null and breaking views that depend on inpatient/clinic activity (e.g., Faculty Inpatient Weeks). | Assign a supervision-specific template or inherit the resident template for the block so faculty assignments carry an activity type. |
| Auth refresh endpoint lacks rate limiting | backend/app/api/routes/auth.py:204 | `/auth/refresh` is not protected by rate limiting, allowing high-volume refresh attempts if tokens leak. | Add a `rate_limit_refresh` dependency with a smaller window and cap. |

## Medium (Technical Debt)
| Issue | Location | Description | Suggested Fix |
|-------|----------|-------------|---------------|
| 1-in-7 rule is implemented as “>6 consecutive days” only | backend/app/scheduling/validator.py:230 | ACGME 1-in-7 is averaged over 4 weeks, but current logic only checks max consecutive days, which can yield false positives/negatives against the rolling average requirement. | Implement rolling 7-day windows over a 4-week period to validate “days off” on average, not just consecutive streaks. |
| N+1 query pattern inside ACGME validator | backend/app/scheduling/validator.py:245 | `_check_1_in_7_rule`, `_check_supervision_ratios`, `_assignments_to_hours`, and `_is_resident` query `Block`/`Person` per assignment, which will scale poorly with real schedules. | Prefetch blocks/people once, build maps, and reuse them across validation checks. |
| Leave list builds person data with lazy loads | backend/app/api/routes/leave.py:125 | `absence.person` is accessed per absence without eager loading; this creates N+1 queries for list views at scale. | Use `joinedload(Absence.person)` or `selectinload` when fetching absences. |

## Low (Cleanup)
| Issue | Location | Description | Suggested Fix |
|-------|----------|-------------|---------------|
| `Person.type` uses reserved name | backend/app/models/person.py:51 | Column name `type` shadows Python built-in and can cause confusion in serializers and IDE tooling. | Rename to `person_type` and add a migration (keep backward compatibility in schemas). |
| My Schedule page ignores template fetch errors | frontend/src/app/my-schedule/page.tsx:64 | `templatesError` is never included in the composite `error`, so the UI can silently render with missing template data. | Include `templatesError` in the error aggregation and show the error state. |
| Rotation template routes bypass service layer | backend/app/api/routes/rotation_templates.py:21 | Routes execute DB logic directly, violating the Route → Controller → Service → Model architecture, making validation and error handling inconsistent across endpoints. | Move CRUD logic into a service/controller layer and keep routes thin. |

## Observations (Not Bugs, But Notable)
- Frontend feature modules `frontend/src/features/analytics`, `frontend/src/features/audit`, `frontend/src/features/fmit-timeline`, and `frontend/src/features/my-dashboard` do not appear wired to any route in `frontend/src/app` (no imports found).
- Frontend test coverage is sparse (only 10 `.test.tsx` files); no tests appear to cover the templates page, swap marketplace, or heatmap feature modules.
- No dedicated unit tests found for ACGME edge cases highlighted in the checklist (rolling average boundary, academic year turnover, midnight-spanning assignments); only performance tests reference the validator.
