# Platform Wiring Roadmap

> **Last Updated:** 2026-03-12
> **Purpose:** Track non-scheduler features that have tables/code but no data flowing through them.
> **Companion:** `ROADMAP.md` (scheduler-focused), `TECHNICAL_DEBT.md`

---

## How to Read This

Every item below has **tables in the database** and usually **service code** already written, but **zero or near-zero rows**. The system looks like it supports these features, but nothing is actually wired end-to-end.

Items are tagged:

- **SCHEDULER-BLOCKING** — The scheduler can't ship to production without this. Must be sequenced with engine work.
- **NON-BLOCKING** — Can be built in parallel by a separate agent/developer. No dependency on solver or engine changes.

Effort estimates: **S** = a few hours, **M** = 1-2 days, **L** = 3-5 days, **XL** = 1+ week

---

## Tier 1: Ship Blockers (need before coordinators use the system solo)

### 1.1 Audit Trail — `activity_log` (SCHEDULER-BLOCKING, M)

| Table | Rows | Code Exists |
|-------|------|-------------|
| `activity_log` | 0 | Model, `audit_service.py` (1,062 LOC), `change_tracker.py` utility |

**What's missing:** Nothing writes to it. The `change_tracker.py` utility exists but no service or route calls it. Schedule generation, swap execution, absence changes, and override application all skip audit logging.

**Why it blocks:** ACGME and military compliance require a record of who changed what. Coordinators need to see why the schedule looks the way it does.

**Work:**
- Wire `change_tracker` calls into schedule generation, swap execution, absence CRUD, and override application
- Add `/api/v1/audit/` read-only route for coordinators
- Tests for each write path

---

### 1.2 Draft & Publish Workflow (SCHEDULER-BLOCKING, L)

| Table | Rows | Code Exists |
|-------|------|-------------|
| `schedule_drafts` | 0 | Model, `schedule_draft_service.py` (2,205 LOC), routes |
| `schedule_draft_assignments` | 0 | Model |
| `schedule_draft_flags` | 0 | Model |
| `schedule_overrides` | 0 | Model, `schedule_override_service.py`, routes |
| `assignment_backups` | 0 | Model |

**What's missing:** The engine writes directly to production `assignments` / `half_day_assignments`. There's no stage → review → publish flow. The draft service is substantial code but the engine never creates drafts.

**Why it blocks:** Coordinators need to review a generated schedule, flag issues, apply manual overrides, and then publish. Without this, every engine run is a live fire.

**Work:**
- Engine generates into `schedule_drafts` instead of `assignments`
- Publish action copies draft → production (with backup)
- Override application layer on top of drafts
- Frontend Phase 2 (already on frontend roadmap)

---

### 1.3 Constraints in DB (SCHEDULER-BLOCKING, M)

| Table | Rows | Code Exists |
|-------|------|-------------|
| `constraint_configurations` | 0 | Model, `constraint_service.py`, MCP tools |

**What's missing:** All 47 constraints are hardcoded in Python. The table exists, the MCP tools exist, but the solver reads from code, not from the table.

**Why it blocks:** Coordinators need to toggle constraints and adjust weights without a code deploy. The half-block initiative (Phase 8) depends on this.

**Work:**
- Seed table from current `ConstraintConfigManager` defaults
- Solver reads enabled/weight/priority from DB at generation time
- Admin UI for constraint toggles
- Already on half-block roadmap as Phase 8

---

## Tier 2: Production Quality (need before go-live, can build in parallel)

### 2.1 Email Notifications (NON-BLOCKING, L)

| Table | Rows | Code Exists |
|-------|------|-------------|
| `email_templates` | 2 | Model |
| `email_logs` | 0 | Model, `email_service.py` (661 LOC) |
| `scheduled_notifications` | 0 | Model |
| `notification_preferences` | 27 | Model (pre-seeded for all people) |
| `notifications` | 3 | Model |

**What's missing:** `EmailService` exists and is imported by `swap_notification_service`, `certification_scheduler`, and `outbox_notification_service` — but no SMTP config, no Celery tasks actually fire, and no emails are ever sent.

**Why it matters:** Swap requests, schedule publications, and certification expirations need to notify people. Currently everything is invisible until someone opens the app.

**Work:**
- Configure SMTP (env vars, `EmailConfig`)
- Wire Celery tasks in `notifications/tasks.py` (file exists, partially written)
- Hook notification triggers into swap execution, schedule publish, absence creation
- Preference-based filtering (table already populated)

---

### 2.2 Approval Chains (NON-BLOCKING, M)

| Table | Rows | Code Exists |
|-------|------|-------------|
| `approval_record` | 0 | Model, `approval_chain_service.py` (637 LOC) |
| `swap_approvals` | 6 | Model |

**What's missing:** Swap approvals have a few test rows, but the approval chain service is not wired into any workflow. No route triggers it, no frontend calls it.

**Why it matters:** Swaps, schedule overrides, and leave requests need multi-step approval (resident → coordinator → program director).

**Work:**
- Wire approval chain into swap request flow
- Wire into schedule override flow
- Add approval status to relevant API responses
- Frontend approval UI

---

### 2.3 Background Job Infrastructure (NON-BLOCKING, S)

| Table | Rows | Code Exists |
|-------|------|-------------|
| `scheduled_jobs` | 0 | Model |
| `job_executions` | 0 | Model, `job_monitor/` (3 files) |
| `metric_snapshots` | 0 | Model |

**What's missing:** Celery is configured and the monitor code exists, but nothing registers jobs or records executions. The MCP `start_background_task_tool` uses Celery directly without touching these tables.

**Why it matters:** Need job history for debugging failed schedule runs, email batches, metric collection.

**Work:**
- Register schedule generation as a tracked job
- Hook `job_monitor` into Celery task lifecycle
- Periodic metric snapshot task (utilization, coverage rates)

---

### 2.4 Schedule Versioning & Diffs (NON-BLOCKING, M)

| Table | Rows | Code Exists |
|-------|------|-------------|
| `schedule_versions` | 0 | Model |
| `schedule_diffs` | 0 | Model |

**What's missing:** SQLAlchemy-Continuum tracks row-level history automatically (`assignments_version` has 138K rows), but the app-level version/diff system is empty. No "Version 1 vs Version 2" comparison exists.

**Why it matters:** Coordinators need "what changed since last publish" and "undo to previous version."

**Work:**
- Create version snapshot on each publish
- Diff computation between snapshots
- Version history API route
- Depends on Draft & Publish (1.2) being wired first

---

## Tier 3: User Experience (post-MVP, nice-to-have)

### 3.1 Surveys & Preferences (NON-BLOCKING, M)

| Table | Rows | Code Exists |
|-------|------|-------------|
| `surveys` | 3 | Model |
| `survey_availability` | 0 | Model |
| `survey_responses` | 0 | Model |
| `rotation_preferences` | 0 | Model |
| `faculty_preferences` | 0 | Model |

**What's missing:** Survey objects were created but no collection mechanism. No frontend for residents/faculty to submit preferences.

**Why it matters:** The annual rotation planner (ARO) could use preferences as soft constraints. Currently it optimizes blindly.

**Work:**
- Survey distribution mechanism (email link or in-app)
- Preference collection frontend
- Wire preferences into ARO solver as soft constraints

---

### 3.2 Wellness & Equity Tracking (NON-BLOCKING, M)

| Table | Rows | Code Exists |
|-------|------|-------------|
| `wellness_accounts` | 27 | Model, `wellness_service.py` (1,150 LOC) |
| `wellness_point_transactions` | 27 | Model (seeded) |
| `wellness_leaderboard_snapshots` | 0 | Model |
| `compensation_records` | 0 | Model |
| `positive_feedback_alerts` | 0 | Model |
| `conflict_alerts` | 0 | Model, `conflict_alert_service.py` (1,036 LOC) |

**What's missing:** Accounts exist and have initial balances, but nothing credits/debits them. No events trigger point changes. The conflict alert service is fully coded but never invoked.

**Why it matters:** Workload equity visibility. Residents should see "you've worked X extra calls, you're owed Y comp time."

**Work:**
- Wire point transactions into call assignment, weekend duty, holiday coverage
- Periodic leaderboard snapshot task
- Conflict alert triggers (consecutive call violations, equity outliers)
- Frontend dashboard

---

### 3.3 Procedure Credentialing & Learner Tracks (NON-BLOCKING, L)

| Table | Rows | Code Exists |
|-------|------|-------------|
| `procedures` | 4 | Model, `procedure_service.py` |
| `procedure_credentials` | 3 | Model, `credential_service.py` (375 LOC) |
| `certification_types` | 5 | Model, `certification_service.py` (340 LOC) |
| `person_certifications` | 0 | Model |
| `learner_tracks` | 0 | Model |
| `learner_assignments` | 0 | Model |
| `learner_to_tracks` | 0 | Model |

**What's missing:** Seed data exists but no workflow to record procedure completions, advance credentials, or assign learners to tracks.

**Why it matters:** ACGME requires procedure logging. Currently tracked outside the system.

**Work:**
- Procedure logging UI (resident records procedures)
- Credential advancement logic (X procedures → credentialed)
- Certification expiration alerts (wire into email notifications)
- Learner track assignment and progress tracking

---

## Tier 4: Hardening & Enterprise (post-production)

### 4.1 Security Infrastructure (NON-BLOCKING, L)

| Table | Rows | Code Exists |
|-------|------|-------------|
| `api_keys` | 0 | Model (21 columns — fully designed) |
| `oauth2_clients` | 0 | Model |
| `ip_blacklists` | 0 | Model |
| `ip_whitelists` | 0 | Model |
| `request_signatures` | 0 | Model |
| `feature_flag_audit` | 0 | Model |

**What's missing:** Single admin user with JWT. No API key auth, no OAuth, no IP filtering.

**Why it matters:** Multi-user deployment needs API keys for integrations, OAuth for SSO, IP filtering for network security.

**Work:**
- API key issuance, rotation, and middleware
- OAuth2 authorization server (or integrate with DoD IdP)
- IP allowlist middleware for production
- Feature flag audit logging

---

### 4.2 AI Governance (NON-BLOCKING, S)

| Table | Rows | Code Exists |
|-------|------|-------------|
| `ai_budget_config` | 0 | Model |
| `ai_usage_log` | 0 | Model |
| `model_tiers` | 0 | Model |
| `cognitive_sessions` | 1 | Model |
| `cognitive_decisions` | 3 | Model |

**What's missing:** PAI v1 scaffolding. The agent system now uses Claude Code natively, making most of this obsolete.

**Decision needed:** Keep for future cost tracking, or drop tables? The `ai_usage_log` could be useful if we add token-metered features.

---

### 4.3 Resilience Persistence (NON-BLOCKING, M)

| Table | Rows | Code Exists |
|-------|------|-------------|
| `faculty_centrality` | 0 | Model |
| `hub_protection_plans` | 0 | Model |
| `cross_training_recommendations` | 0 | Model |
| `fallback_activations` | 0 | Model |
| `chaos_experiments` | 0 | Model |
| `sacrifice_decisions` | 0 | Model |
| `preference_trails` | 0 | Model |
| `trail_signals` | 0 | Model |

**What's missing:** MCP resilience tools compute everything on-the-fly from current state. Results are returned but never persisted.

**Decision needed:** Persist for trend analysis, or keep ephemeral? Current approach works but loses history.

---

### 4.4 Game Theory (NON-BLOCKING, S)

| Table | Rows | Code Exists |
|-------|------|-------------|
| `game_theory_strategies` | 6 | Model, `game_theory.py` (869 LOC) |
| `game_theory_tournaments` | 2 | Model |
| `game_theory_evolution` | 0 | Model |
| `game_theory_matches` | 0 | Model |
| `game_theory_validations` | 0 | Model |

**What's missing:** Strategies and tournaments were seeded but matches never ran.

**Decision needed:** Research feature — keep, finish, or remove? The solver (CP-SAT) already handles optimization without game theory.

---

## Parallelization Matrix

| Item | Blocks Scheduler? | Depends On | Can Start Now? |
|------|-------------------|------------|----------------|
| 1.1 Audit Trail | YES | — | YES |
| 1.2 Draft & Publish | YES | — | YES (backend); needs frontend Phase 2 |
| 1.3 Constraints in DB | YES | — | YES |
| 2.1 Email Notifications | no | SMTP config | YES |
| 2.2 Approval Chains | no | — | YES |
| 2.3 Background Jobs | no | — | YES |
| 2.4 Schedule Versioning | no | 1.2 Draft & Publish | AFTER 1.2 |
| 3.1 Surveys & Preferences | no | — | YES |
| 3.2 Wellness & Equity | no | — | YES |
| 3.3 Procedure Credentialing | no | — | YES |
| 4.1 Security Infrastructure | no | — | YES |
| 4.2 AI Governance | no | Decision: keep or drop | BLOCKED on decision |
| 4.3 Resilience Persistence | no | Decision: persist or ephemeral | BLOCKED on decision |
| 4.4 Game Theory | no | Decision: keep or remove | BLOCKED on decision |

**Maximum parallelism:** 3 scheduler-blocking items + up to 8 non-blocking items can all be worked simultaneously. Only 2.4 and the Tier 4 decision-blocked items need sequencing.

---

## Table Inventory (65 unwired tables)

For reference, every table with 0 rows or seed-only data, mapped to the item above:

| Table | Rows | Roadmap Item |
|-------|------|-------------|
| `activity_log` | 0 | 1.1 Audit Trail |
| `approval_record` | 0 | 2.2 Approval Chains |
| `assignment_backups` | 0 | 1.2 Draft & Publish |
| `schedule_drafts` | 0 | 1.2 Draft & Publish |
| `schedule_draft_assignments` | 0 | 1.2 Draft & Publish |
| `schedule_draft_flags` | 0 | 1.2 Draft & Publish |
| `schedule_overrides` | 0 | 1.2 Draft & Publish |
| `schedule_versions` | 0 | 2.4 Schedule Versioning |
| `schedule_diffs` | 0 | 2.4 Schedule Versioning |
| `constraint_configurations` | 0 | 1.3 Constraints in DB |
| `email_logs` | 0 | 2.1 Email Notifications |
| `scheduled_notifications` | 0 | 2.1 Email Notifications |
| `scheduled_jobs` | 0 | 2.3 Background Jobs |
| `job_executions` | 0 | 2.3 Background Jobs |
| `metric_snapshots` | 0 | 2.3 Background Jobs |
| `survey_availability` | 0 | 3.1 Surveys & Preferences |
| `survey_responses` | 0 | 3.1 Surveys & Preferences |
| `rotation_preferences` | 0 | 3.1 Surveys & Preferences |
| `faculty_preferences` | 0 | 3.1 Surveys & Preferences |
| `wellness_leaderboard_snapshots` | 0 | 3.2 Wellness & Equity |
| `compensation_records` | 0 | 3.2 Wellness & Equity |
| `positive_feedback_alerts` | 0 | 3.2 Wellness & Equity |
| `conflict_alerts` | 0 | 3.2 Wellness & Equity |
| `person_certifications` | 0 | 3.3 Procedure Credentialing |
| `learner_tracks` | 0 | 3.3 Procedure Credentialing |
| `learner_assignments` | 0 | 3.3 Procedure Credentialing |
| `learner_to_tracks` | 0 | 3.3 Procedure Credentialing |
| `api_keys` | 0 | 4.1 Security Infrastructure |
| `oauth2_clients` | 0 | 4.1 Security Infrastructure |
| `ip_blacklists` | 0 | 4.1 Security Infrastructure |
| `ip_whitelists` | 0 | 4.1 Security Infrastructure |
| `request_signatures` | 0 | 4.1 Security Infrastructure |
| `feature_flag_audit` | 0 | 4.1 Security Infrastructure |
| `ai_budget_config` | 0 | 4.2 AI Governance |
| `ai_usage_log` | 0 | 4.2 AI Governance |
| `model_tiers` | 0 | 4.2 AI Governance |
| `faculty_centrality` | 0 | 4.3 Resilience Persistence |
| `hub_protection_plans` | 0 | 4.3 Resilience Persistence |
| `cross_training_recommendations` | 0 | 4.3 Resilience Persistence |
| `fallback_activations` | 0 | 4.3 Resilience Persistence |
| `chaos_experiments` | 0 | 4.3 Resilience Persistence |
| `sacrifice_decisions` | 0 | 4.3 Resilience Persistence |
| `preference_trails` | 0 | 4.3 Resilience Persistence |
| `trail_signals` | 0 | 4.3 Resilience Persistence |
| `game_theory_evolution` | 0 | 4.4 Game Theory |
| `game_theory_matches` | 0 | 4.4 Game Theory |
| `game_theory_validations` | 0 | 4.4 Game Theory |
| `clinic_sessions` | 0 | 1.3 Constraints in DB (data-driven scheduling) |
| `intern_stagger_patterns` | 0 | 1.3 Constraints in DB (data-driven scheduling) |
| `resident_call_preloads` | 0 | Preload pipeline (engine uses `inpatient_preloads` instead) |
| `import_staged_absences` | 0 | 2.1 or standalone (staging flow exists, never used) |
| `annual_rotation_plans` | 0 | ARO (backend wired, needs production use) |
| `annual_rotation_assignments` | 0 | ARO (backend wired, needs production use) |
