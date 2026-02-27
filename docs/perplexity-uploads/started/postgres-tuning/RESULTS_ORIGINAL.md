# PostgreSQL 15 Query Tuning Analysis

**System:** Military Residency Scheduling System  
**Stack:** FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL 15  
**Scale:** ~100 people, ~5,000 assignments/year, ~500 swap records, ~1,000 conflict alerts  
**Date:** February 26, 2026  

---

## Section 1: Query Pattern Classification

Every SQLAlchemy query found across the six uploaded service/repository files is cataloged below, classified by access pattern, with the tables involved and current index coverage noted.

### 1.1 call_assignment_service.py

| # | Approx Line | Query Description | Pattern | Tables | Current Index |
|---|-------------|-------------------|---------|--------|---------------|
| 1 | 68–84 | CallAssignment via JOIN CallOverride by `replacement_person_id` + `is_active`, optional date range | Multi-table join + filtered range | `call_assignments`, `call_overrides` | `idx_call_assignments_person_date` (partial; not on `call_overrides.replacement_person_id`) |
| 2 | 99–105 | CallAssignment by PK `id` with `selectinload(person)` | Point lookup | `call_assignments` | PK index |
| 3 | 134–163 | CallAssignment list with optional `person_id`, `call_type`, `start_date`, `end_date` + COUNT + ORDER BY `date DESC` + OFFSET/LIMIT | Filtered range + aggregation + sort+limit | `call_assignments` | `idx_call_assignments_person_date` (covers person_id+date only) |
| 4 | 204–218 | CallAssignment by date range (`date >= ? AND date <= ?`) ORDER BY `date` | Range scan + sort | `call_assignments` | `idx_call_assignments_person_date` (not a leading-column match for date-only) |
| 5 | 243–256 | CallAssignment by `person_id` with optional date range, ORDER BY `date` | Composite point + range scan | `call_assignments` | `idx_call_assignments_person_date` ✅ |
| 6 | 298–300 | Person by PK `id` | Point lookup | `people` | PK index |
| 7 | 309–315 | CallAssignment duplicate check: `date = ? AND person_id = ? AND call_type = ?` | Composite point (3-col) | `call_assignments` | `idx_call_assignments_person_date` (covers 2/3 columns) |
| 8 | 338–344 | CallAssignment by PK `id` (post-create reload) | Point lookup | `call_assignments` | PK index |
| 9 | 374–376 | CallAssignment by PK `id` (for update) | Point lookup | `call_assignments` | PK index |
| 10 | 383–385 | Person by PK `id` (validate person_id update) | Point lookup | `people` | PK index |
| 11 | 437–439 | CallAssignment by PK `id` (for delete) | Point lookup | `call_assignments` | PK index |
| 12 | 533–537 | DELETE CallAssignment by date range | Range scan (DML) | `call_assignments` | No leading date index |
| 13 | 736–742 | CallAssignment by PK `id` (bulk update loop) | Point lookup (N iterations) | `call_assignments` | PK index |
| 14 | 797–801 | RotationTemplate by `func.upper(abbreviation) = ?` | Expression scan | `rotation_templates` | `idx_rotation_templates_name` (on `name`, not `abbreviation`) |
| 15 | 807–812 | Block by `date = ? AND time_of_day = ?` | Composite point | `blocks` | No known index on `(date, time_of_day)` |
| 16 | 829–835 | DELETE Assignment by `person_id + block_id + rotation_template_id` | Composite point (DML) | `assignments` | No known composite index |
| 17 | 862–868 | Assignment existence check: `person_id + block_id + rotation_template_id` | Existence check | `assignments` | No known composite index |

### 1.2 conflict_auto_resolver.py

| # | Approx Line | Query Description | Pattern | Tables | Current Index |
|---|-------------|-------------------|---------|--------|---------------|
| 18 | 490–493 | ConflictAlert by PK `id`, optional `FOR UPDATE` | Point lookup (with row lock) | `conflict_alerts` | PK index |
| 19 | 73 | Person by `id` (faculty lookup) | Point lookup | `people` | PK index |
| 20 | 555–569 | ConflictAlert COUNT by `fmit_week = ? AND status IN (NEW, ACKNOWLEDGED)` excluding self | Filtered aggregation | `conflict_alerts` | `idx_conflict_alerts_fmit_week`, `idx_conflict_alerts_status` (separate, not composite) |
| 21 | 597 | Person by PK `id` (ACGME check) | Point lookup | `people` | PK index |
| 22 | 611–622 | Assignment JOIN Block: COUNT WHERE `person_id = ? AND date BETWEEN ? AND ?` | Multi-table join + range + aggregation | `assignments`, `blocks` | No index on `assignments.person_id`; no composite on blocks.date |
| 23 | 644–654 | Assignment JOIN Block: COUNT WHERE `date BETWEEN ? AND ?` (coverage gap) | Multi-table join + range + aggregation | `assignments`, `blocks` | Same as above |
| 24 | 695 | Person by PK `id` (supervision check) | Point lookup | `people` | PK index |
| 25 | 706–717 | Assignment JOIN Block JOIN Person: COUNT WHERE date range + `person.type = 'resident'` | Multi-table join (3 tables) + range + filter | `assignments`, `blocks`, `people` | No join indexes |
| 26 | 721–734 | Assignment JOIN Block JOIN Person: COUNT WHERE date range + `person.type = 'faculty'` + exclude ID | Multi-table join (3 tables) + range + filter + exclusion | `assignments`, `blocks`, `people` | No join indexes |
| 27 | 756–768 | Assignment JOIN Block JOIN RotationTemplate: COUNT WHERE `person_id = ?` + `date >= today()` + `name ILIKE '%FMIT%'` | Multi-table join (3) + range + pattern match | `assignments`, `blocks`, `rotation_templates` | `idx_rotation_templates_name` (useless for ILIKE '%FMIT%') |
| 28 | 771–785 | Same as 27 but for ALL faculty: COUNT total FMIT assignments | Multi-table join (4) + range + ILIKE + aggregation | `assignments`, `blocks`, `people`, `rotation_templates` | Same gap |
| 29 | 787 | Person COUNT by `type = 'faculty'` | Filtered aggregation | `people` | `idx_people_type` ✅ |
| 30 | 838–849 | ConflictAlert COUNT by `fmit_week = ?` + `status IN (...)` | Filtered aggregation | `conflict_alerts` | `idx_conflict_alerts_fmit_week` + `idx_conflict_alerts_status` (separate) |
| 31 | 1228–1238 | ConflictAlert COUNT by `faculty_id = ?` + `status IN (...)` | Filtered aggregation | `conflict_alerts` | `idx_conflict_alerts_faculty_status` ✅ |
| 32 | 1590–1597 | Person list WHERE `type = 'faculty'` + exclude ID | Filtered scan | `people` | `idx_people_type` ✅ |
| 33 | 1604–1615 | ConflictAlert COUNT by `faculty_id = ?` + `fmit_week = ?` + `status IN (...)` | Multi-column filter + aggregation | `conflict_alerts` | `idx_conflict_alerts_faculty_status` (partial — missing fmit_week) |
| 34 | 1619–1630 | Assignment JOIN Block: COUNT by `person_id = ?` + date range | Multi-table join + range | `assignments`, `blocks` | No composite |
| 35 | 1638–1645 | Person list WHERE `type = 'resident'` + `pgy_level IN (2,3)` | Filtered scan | `people` | `idx_people_pgy_level` (single col); no composite `(type, pgy_level)` |
| 36 | 1652–1661 | Assignment JOIN Block: COUNT by `person_id = ?` + date range | Multi-table join + range | `assignments`, `blocks` | No composite |

### 1.3 schedule_draft_service.py

| # | Approx Line | Query Description | Pattern | Tables | Current Index |
|---|-------------|-------------------|---------|--------|---------------|
| 37 | 183–191 | ScheduleDraftAssignment WHERE `draft_id = ?` + `assignment_date <= lock_date` | Composite point + range | `schedule_draft_assignments` | `idx_sched_draft_asgn_draft_id` (single col) |
| 38 | 205–212 | ScheduleDraftFlag WHERE `draft_id = ?` + `flag_type = LOCK_WINDOW_VIOLATION` | Composite point | `schedule_draft_flags` | `idx_sched_draft_flags_draft_id` (single col) |
| 39 | 216–219, 249–250, 278–280, 311–313, 409–412, 584–588, 650–654, 728–738, 823–825, 939–944, 1365–1370, 1567–1570, 1731–1733, 2001–2004, 2103–2104, 2188–2192 | ScheduleDraft by PK `id` (many instances, some with `FOR UPDATE`) | Point lookup | `schedule_drafts` | PK index |
| 40 | 267–274 | ScheduleDraftFlag WHERE `draft_id = ?` + `flag_type = LOCK_WINDOW_VIOLATION` | Composite point | `schedule_draft_flags` | `idx_sched_draft_flags_draft_id` |
| 41 | 296–303 | ScheduleDraftFlag list WHERE `draft_id = ?` + `flag_type = CREDENTIAL_MISSING` | Composite point | `schedule_draft_flags` | `idx_sched_draft_flags_draft_id` |
| 42 | 331–341 | ScheduleDraftAssignment JOIN Person WHERE `draft_id = ?` + `change_type != DELETE` + `person.type = 'faculty'` | Multi-table join + filtered | `schedule_draft_assignments`, `people` | `idx_sched_draft_asgn_draft_id` |
| 43 | 351–355 | ProcedureCredential WHERE `person_id IN (...)` | IN-list lookup | `procedure_credentials` | No known index on `person_id` |
| 44 | 453–461 | ScheduleDraft WHERE `status = DRAFT` + `target_start_date = ?` + `target_end_date = ?` | Composite point | `schedule_drafts` | `idx_schedule_drafts_status_dates` ✅ |
| 45 | 546–555 | ScheduleDraftAssignment WHERE `draft_id + person_id + assignment_date + time_of_day` | Composite point (4-col) | `schedule_draft_assignments` | `idx_sched_draft_asgn_draft_id`, `idx_sched_draft_asgn_person_id` (separate) |
| 46 | 684–688 | ScheduleDraftFlag by PK `id` | Point lookup | `schedule_draft_flags` | PK index |
| 47 | 863–871 | ScheduleDraftFlag WHERE `draft_id = ?` + `flag_type = LOCK_WINDOW_VIOLATION` + `acknowledged_at IS NULL` | Composite point + NULL filter | `schedule_draft_flags` | `idx_sched_draft_flags_draft_id` |
| 48 | 1017–1021 | ScheduleDraftAssignment list WHERE `draft_id = ?` | Point lookup (FK) | `schedule_draft_assignments` | `idx_sched_draft_asgn_draft_id` ✅ |
| 49 | 1156–1176 | Activity WHERE `func.lower(code) = ?`, then `func.lower(display_abbreviation) = ?`, then `func.lower(name) = ?` | Expression scan (3 queries) | `activities` | No expression indexes |
| 50 | 1217–1221, 1229–1237, 1257–1265 | HalfDayAssignment by `person_id + date + time_of_day` (upsert pattern) | Composite point | `half_day_assignments` | Unknown (not in uploaded migration) |
| 51 | 1290–1302 | BlockAssignment WHERE `resident_id = ?` + `block_number = ?` + `academic_year = ?` | Composite point | `block_assignments` | `unique_resident_per_block` constraint ✅ |
| 52 | 1609–1622 | ScheduleDraft WHERE `status = DRAFT`, optional `target_block`, optional date match | Filtered scan | `schedule_drafts` | `idx_schedule_drafts_status` ✅ |
| 53 | 1641–1646 | ScheduleDraft list ORDER BY `created_at DESC` + LIMIT/OFFSET | Sort + limit | `schedule_drafts` | No index on `created_at` |
| 54 | 1697–1705 | Assignment JOIN Block WHERE `person_id = ?` + `block.date = ?` + `block.time_of_day = ?` | Multi-table join + composite point | `assignments`, `blocks` | No composite |
| 55 | 1735–1742, 1743–1750 | ScheduleDraftAssignment COUNT WHERE `draft_id = ?` + `change_type = ?` | Filtered aggregation | `schedule_draft_assignments` | `idx_sched_draft_asgn_draft_id` (partial) |

### 1.4 swap_repository.py

| # | Approx Line | Query Description | Pattern | Tables | Current Index |
|---|-------------|-------------------|---------|--------|---------------|
| 56 | 58 | SwapRecord by PK `id` | Point lookup | `swap_records` | PK index |
| 57 | 70–79 | SwapRecord by PK `id` with `selectinload` of 3 relations | Point lookup + eager | `swap_records` | PK index |
| 58 | 151–160 | SwapRecord WHERE `source_faculty_id = ? OR target_faculty_id = ?` ORDER BY `requested_at DESC` | OR-filter + sort | `swap_records` | `idx_swap_records_status_requested` (partial; no faculty_id index) |
| 59 | 180–197 | SwapRecord WHERE `status = ?`, optional `faculty_id` OR, ORDER BY `requested_at DESC` | Filtered + OR + sort | `swap_records` | `idx_swap_records_status`, `idx_swap_records_status_requested` ✅ |
| 60 | 212–234 | SwapRecord WHERE `source_week = ? OR target_week = ?`, optional faculty OR | OR-filter | `swap_records` | No index on `source_week` or `target_week` |
| 61 | 238–246 | SwapRecord WHERE `target_faculty_id = ?` + `status = PENDING` ORDER BY `requested_at DESC` | Composite point + sort | `swap_records` | No composite `(target_faculty_id, status)` |
| 62 | 254–266 | SwapRecord WHERE `status = EXECUTED`, optional faculty OR, ORDER BY `executed_at DESC` LIMIT | Filtered + sort + limit | `swap_records` | `idx_swap_records_status` |
| 63 | 283–306 | SwapRecord with pagination: optional faculty OR, status, source_week range, COUNT + OFFSET/LIMIT | Filtered range + aggregation + sort+limit | `swap_records` | Partial coverage |
| 64 | 336 | SwapApproval WHERE `swap_id = ?` | Point lookup (FK) | `swap_approvals` | `idx_swap_approvals_swap_id` ✅ |
| 65 | 346 | SwapApproval by PK `id` | Point lookup | `swap_approvals` | PK index |
| 66 | 374–384 | SwapRecord GROUP BY `status` with optional faculty OR — COUNT aggregation | Aggregation + group by | `swap_records` | `idx_swap_records_status` |
| 67 | 394–407 | SwapRecord COUNT WHERE `status = EXECUTED` + faculty OR + optional date range | Filtered aggregation + range | `swap_records` | `idx_swap_records_status` |

### 1.5 audit_repository.py

| # | Approx Line | Query Description | Pattern | Tables | Current Index |
|---|-------------|-------------------|---------|--------|---------------|
| 68 | 174–182 | Raw SQL: `{version_table} v JOIN transaction t` WHERE `v.id = :entry_id` | Point lookup (raw SQL) | `*_version`, `transaction` | PK on version tables |
| 69 | 246–258 | Raw SQL: COUNT + GROUP BY `operation_type, user_id, DATE(issued_at)` with date filter | Aggregation + group by (raw SQL) | `*_version`, `transaction` | No known index on `transaction.issued_at` |
| 70 | 304–314 | Raw SQL: `transaction` GROUP BY `user_id` ORDER BY count DESC | Aggregation + group by | `transaction` | No known index on `user_id` |
| 71 | 374–383 | Raw SQL: `{version_table} v JOIN transaction t` WHERE `v.id = :entity_id` ORDER BY `issued_at` | Point lookup + sort | `*_version`, `transaction` | PK on version tables |
| 72 | 434–442 | Raw SQL: Dynamic filter query against version tables, LIMIT 1000 | Filtered scan (raw SQL) | `*_version`, `transaction` | Varies |

### 1.6 async_base.py

| # | Approx Line | Query Description | Pattern | Tables | Current Index |
|---|-------------|-------------------|---------|--------|---------------|
| 73 | 128 | Generic `db.get(model, id)` — PK lookup | Point lookup | Any model | PK index |
| 74 | 145–158 | Generic `select(model)` with `selectinload` + pagination | Full scan + sort + limit | Any model | Varies |
| 75 | 227–274 | Generic paginated query with filters + count + sort + offset/limit | Filtered + aggregation + sort+limit | Any model | Varies |
| 76 | 413–421 | Generic COUNT with filters | Filtered aggregation | Any model | Varies |

---

## Section 2: Index Gap Analysis

### 2.1 Indexes from 20260212 Migration (What Exists)

| Index Name | Table | Columns | Type |
|------------|-------|---------|------|
| `idx_conflict_alerts_status` | conflict_alerts | (status) | B-tree |
| `idx_conflict_alerts_faculty_id` | conflict_alerts | (faculty_id) | B-tree |
| `idx_conflict_alerts_fmit_week` | conflict_alerts | (fmit_week) | B-tree |
| `idx_conflict_alerts_faculty_status` | conflict_alerts | (faculty_id, status) | B-tree |
| `idx_conflict_alerts_created_at` | conflict_alerts | (created_at) | B-tree |
| `idx_swap_records_status` | swap_records | (status) | B-tree |
| `idx_swap_records_status_requested` | swap_records | (status, requested_at) | B-tree |
| `idx_swap_approvals_swap_id` | swap_approvals | (swap_id) | B-tree |
| `idx_swap_approvals_faculty_id` | swap_approvals | (faculty_id) | B-tree |
| `idx_schedule_runs_status` | schedule_runs | (status) | B-tree |
| `idx_schedule_runs_date_range` | schedule_runs | (start_date, end_date) | B-tree |
| `idx_schedule_drafts_status` | schedule_drafts | (status) | B-tree |
| `idx_schedule_drafts_status_dates` | schedule_drafts | (status, target_start_date, target_end_date) | B-tree |
| `idx_sched_draft_asgn_draft_id` | schedule_draft_assignments | (draft_id) | B-tree |
| `idx_sched_draft_asgn_person_id` | schedule_draft_assignments | (person_id) | B-tree |
| `idx_sched_draft_flags_draft_id` | schedule_draft_flags | (draft_id) | B-tree |
| `idx_rotation_templates_name` | rotation_templates | (name) | B-tree |
| `idx_rotation_templates_rotation_type` | rotation_templates | (rotation_type) | B-tree |
| `idx_absences_person_dates` | absences | (person_id, start_date, end_date) | B-tree |
| `idx_absences_status` | absences | (status) | B-tree |
| `idx_absences_type` | absences | (absence_type) | B-tree |
| `idx_call_assignments_person_date` | call_assignments | (person_id, date) | B-tree |
| `idx_users_role` | users | (role) | B-tree |
| `idx_users_is_active` | users | (is_active) | B-tree |

Model-level indexes: `people.name`, `people.type`, `people.pgy_level`, `people.email` (unique), `block_assignments.academic_block_id`, UniqueConstraint `(block_number, academic_year, resident_id)`.

### 2.2 Covered Queries (Optimal Index Support)

| Query # | Description | Index Used |
|---------|-------------|------------|
| 2,6,8–11,13,18–19,21,24,39,46,56–57,64–65,68,71,73 | All PK lookups | PK index |
| 5 | CallAssignment by person_id + date range | `idx_call_assignments_person_date` ✅ |
| 29,32 | Person by type='faculty' | `people.type` index ✅ |
| 31 | ConflictAlert by faculty_id + status IN | `idx_conflict_alerts_faculty_status` ✅ |
| 44 | ScheduleDraft by status + start + end | `idx_schedule_drafts_status_dates` ✅ |
| 48 | ScheduleDraftAssignment by draft_id | `idx_sched_draft_asgn_draft_id` ✅ |
| 51 | BlockAssignment by resident_id + block + year | `unique_resident_per_block` ✅ |
| 52 | ScheduleDraft by status | `idx_schedule_drafts_status` ✅ |
| 59 | SwapRecord by status ORDER BY requested_at | `idx_swap_records_status_requested` ✅ |

### 2.3 Partially Covered Queries

| Query # | Description | Index Used | Gap |
|---------|-------------|------------|-----|
| 1 | CallOverride join by `replacement_person_id` | None on call_overrides | Missing `call_overrides(replacement_person_id)` |
| 3 | CallAssignment by person_id+call_type+date range + COUNT | `idx_call_assignments_person_date` | Missing `call_type` in index; separate COUNT duplicates filter logic |
| 7 | Duplicate check: date+person_id+call_type | `idx_call_assignments_person_date` | Missing `call_type` as 3rd column |
| 20,30 | ConflictAlert by fmit_week + status IN | Separate indexes on fmit_week and status | Need composite `(fmit_week, status)` |
| 33 | ConflictAlert by faculty_id+fmit_week+status | `idx_conflict_alerts_faculty_status` | Missing `fmit_week` in composite |
| 37 | ScheduleDraftAssignment by draft_id + date ≤ | `idx_sched_draft_asgn_draft_id` | Missing `assignment_date` in composite |
| 45 | ScheduleDraftAssignment by 4-column unique combo | Two separate single-col indexes | Need composite `(draft_id, person_id, assignment_date, time_of_day)` |
| 58 | SwapRecord by faculty_id (source OR target) | No faculty_id index on swap_records | Missing `source_faculty_id` and `target_faculty_id` indexes |
| 61 | SwapRecord by target_faculty_id + PENDING | No composite | Missing `(target_faculty_id, status)` |

### 2.4 Uncovered Queries (No Index Support)

| Query # | Description | Recommended Index | Expected Improvement |
|---------|-------------|-------------------|---------------------|
| 4,12 | CallAssignment by date range only (no person_id) | `call_assignments(date)` | Seq scan → Index scan; 5,000 rows scanned → <100 |
| 14 | RotationTemplate by `UPPER(abbreviation)` | `rotation_templates USING btree (UPPER(abbreviation))` expression index | Seq scan → Index scan on ~20 rows |
| 15 | Block by `(date, time_of_day)` | `blocks(date, time_of_day)` | Seq scan on blocks → Index scan |
| 16,17 | Assignment by `(person_id, block_id, rotation_template_id)` | `assignments(person_id, block_id, rotation_template_id)` | Seq scan → Index scan for existence check |
| 22–23,25–26,34,36,54 | Assignment JOIN Block with date range | `blocks(date)` and `assignments(person_id)` or `assignments(block_id)` | Hash/Nested Loop with seq scan → Index Nested Loop |
| 27–28 | ILIKE '%FMIT%' on rotation_templates.name | `pg_trgm` GIN index or flag column `is_fmit` boolean | Pattern match → trigram index scan, or point lookup on flag |
| 35 | Person by type='resident' + pgy_level IN (2,3) | `people(type, pgy_level)` partial WHERE type='resident' | Seq scan → Index scan |
| 43 | ProcedureCredential by person_id IN (...) | `procedure_credentials(person_id)` | Seq scan → Index scan |
| 49 | Activity by `lower(code)`, `lower(abbreviation)`, `lower(name)` | Three expression indexes (see Section 6) | 3× seq scan → 3× Index scan |
| 50 | HalfDayAssignment by `(person_id, date, time_of_day)` | `half_day_assignments(person_id, date, time_of_day)` | Seq scan → Index scan for upserts |
| 53 | ScheduleDraft ORDER BY created_at DESC LIMIT | `schedule_drafts(created_at DESC)` | Sort → Index-only scan with backward scan |
| 60 | SwapRecord by source_week OR target_week | `swap_records(source_week)`, `swap_records(target_week)` | BitmapOr with seq scans → Index scans |
| 69–70,72 | Raw SQL audit queries on transaction table | `transaction(issued_at)`, `transaction(user_id)` | Seq scan → Index scan for date filtering |

### 2.5 Potentially Unused Indexes

| Index | Table | Assessment |
|-------|-------|------------|
| `idx_conflict_alerts_created_at` | conflict_alerts | No query in uploaded code sorts/filters by `created_at` on conflict_alerts. May be used by UI route handlers not uploaded. **Verdict: Verify with `pg_stat_user_indexes`.** |
| `idx_absences_type` | absences | No query in uploaded code filters by `absence_type` alone. **Verdict: Likely used by absence management code not uploaded.** |
| `idx_users_role`, `idx_users_is_active` | users | No user table queries in uploaded code. **Verdict: Used by auth middleware — keep.** |
| `idx_schedule_runs_status`, `idx_schedule_runs_date_range` | schedule_runs | No query in uploaded code touches `schedule_runs`. **Verdict: Likely used by scheduling engine — keep.** |

### 2.6 Recommended New Index Migration

```sql
-- ============================================================
-- Wave 4: Gap-filling indexes based on query pattern analysis
-- ============================================================

-- call_overrides: JOIN key for override lookups (#1)
CREATE INDEX idx_call_overrides_replacement_person
    ON call_overrides (replacement_person_id)
    WHERE is_active = true;

-- call_assignments: date-only range scans (#4, #12)
CREATE INDEX idx_call_assignments_date
    ON call_assignments (date);

-- call_assignments: 3-column duplicate check (#7)
-- Extends existing (person_id, date) to include call_type
CREATE INDEX idx_call_assignments_person_date_type
    ON call_assignments (person_id, date, call_type);

-- blocks: composite for date+time lookups (#15, #22–26, #34, #36, #54)
CREATE INDEX idx_blocks_date_time
    ON blocks (date, time_of_day);

-- assignments: FK index on block_id (used in every JOIN)
CREATE INDEX idx_assignments_block_id
    ON assignments (block_id);

-- assignments: composite for existence checks (#16, #17)
CREATE INDEX idx_assignments_person_block_template
    ON assignments (person_id, block_id, rotation_template_id);

-- conflict_alerts: composite for fmit_week + status (#20, #30)
CREATE INDEX idx_conflict_alerts_fmit_week_status
    ON conflict_alerts (fmit_week, status);

-- conflict_alerts: 3-col composite (#33)
CREATE INDEX idx_conflict_alerts_faculty_fmit_status
    ON conflict_alerts (faculty_id, fmit_week, status);

-- swap_records: faculty lookups (#58, #61, #63)
CREATE INDEX idx_swap_records_source_faculty
    ON swap_records (source_faculty_id);
CREATE INDEX idx_swap_records_target_faculty
    ON swap_records (target_faculty_id);
CREATE INDEX idx_swap_records_source_week
    ON swap_records (source_week);
CREATE INDEX idx_swap_records_target_week
    ON swap_records (target_week);

-- schedule_draft_assignments: 4-col upsert composite (#45)
CREATE UNIQUE INDEX idx_sched_draft_asgn_upsert
    ON schedule_draft_assignments (draft_id, person_id, assignment_date, time_of_day);

-- schedule_draft_flags: composite for flag type lookups (#38, #40, #41, #47)
CREATE INDEX idx_sched_draft_flags_draft_type
    ON schedule_draft_flags (draft_id, flag_type);

-- schedule_drafts: created_at for ORDER BY DESC LIMIT (#53)
CREATE INDEX idx_schedule_drafts_created_at
    ON schedule_drafts (created_at DESC);

-- procedure_credentials: person_id for IN-list lookups (#43)
CREATE INDEX idx_procedure_credentials_person
    ON procedure_credentials (person_id);

-- half_day_assignments: composite for upsert pattern (#50)
CREATE UNIQUE INDEX idx_half_day_assignments_upsert
    ON half_day_assignments (person_id, date, time_of_day);

-- people: composite partial for resident queries (#35)
CREATE INDEX idx_people_type_pgy
    ON people (type, pgy_level)
    WHERE type = 'resident';

-- transaction (audit): date and user lookups (#69–72)
CREATE INDEX idx_transaction_issued_at ON transaction (issued_at);
CREATE INDEX idx_transaction_user_id ON transaction (user_id);
```

---

## Section 3: PostgreSQL 15 Feature Opportunities

| # | Feature | Applicable? | Justification |
|---|---------|-------------|---------------|
| 1 | **MERGE statement** | **YES** | At least 4 upsert patterns exist: (a) `HalfDayAssignment` upsert by `(person_id, date, time_of_day)` in `_apply_draft_assignment` (lines 1252–1283), (b) `_create_assignment_if_not_exists` in `call_assignment_service.py` (lines 849–883), (c) `ScheduleDraftAssignment` upsert in `add_assignment_to_draft` (lines 546–602), (d) `_upsert_lock_window_flag` in schedule_draft_service (lines 202–264). Each currently does a SELECT-then-INSERT/UPDATE in two round trips. PG15 `MERGE` consolidates to one statement, reducing round trips by 50% and eliminating race conditions without explicit locking. Expected ~30% speedup per upsert on these hot paths. Requires raw SQL via `text()` or `connection.execute()` since SQLAlchemy 2.0 doesn't have native MERGE support yet. |
| 2 | **JSON path improvements** | **NO** | The codebase uses `change_summary` as a JSONB column on `ScheduleDraft`, but it's only read/written as a whole dict (Python-side manipulation), never queried with `@>`, `->`, or `jsonpath`. No benefit from PG15 JSON path enhancements. |
| 3 | **Improved sort performance** | **MAYBE** | PG15 improves sort performance for `text` and `numeric` types by 3–44%. Relevant for: (a) `ORDER BY name` on `people` table (~100 rows — negligible), (b) `ORDER BY requested_at DESC` on `swap_records` (~500 rows — minor), (c) `ORDER BY created_at DESC` on `schedule_drafts` (few rows). At this data scale, the improvement is under 1ms. **Verdict:** Free improvement, no action needed, but will matter if data grows 10–100×. |
| 4 | **Parallel query improvements** | **NO** | PG15 parallelism kicks in for large scans (default `min_parallel_table_scan_size = 8MB`). With ~5,000 assignments and ~100 people, no table exceeds a few MB. Parallel query would add overhead, not benefit. Leave `max_parallel_workers_per_gather = 0` or default. |
| 5 | **Logical replication improvements** | **MAYBE** | PG15 allows logical replication of sequences and adds `row_filter`. Not immediately useful for a single-site deployment, but if you add a read replica for reporting (audit queries are heavy JOINs), logical replication with row filters could replicate only `transaction` + `*_version` tables to a reporting database. **Verdict:** Defer until multi-site or reporting offload is needed. |
| 6 | **Security improvements** | **YES** | PG15 adds `GRANT ... ON ALL TABLES IN SCHEMA` and predefined roles (`pg_read_all_data`, `pg_write_all_data`). Relevant for: (a) creating a read-only role for the audit/reporting endpoints, (b) locking down the application role to only DML (no DDL). Recommended: create `app_readonly` role with `pg_read_all_data` for monitoring dashboards. |
| 7 | **pg_stat_statements improvements** | **YES** | PG15 adds `temp_blk_read_time`, `temp_blk_write_time`, JIT counters, and auto-enables `compute_query_id`. Critical for this system because: (a) no monitoring is configured yet, (b) the conflict_auto_resolver runs multi-JOIN queries that may spill to temp, (c) `compute_query_id` enables correlating `pg_stat_statements` with `auto_explain` output. See Section 8 for configuration. |

### 3.1 MERGE Statement Migration Example

Current pattern (`_create_assignment_if_not_exists`, line 862):
```python
existing = await self.db.execute(select(Assignment).where(...))
if existing.scalar_one_or_none():
    return existing.id, False
new = Assignment(...)
self.db.add(new)
```

Recommended PG15 MERGE:
```python
merge_sql = text("""
    MERGE INTO assignments AS target
    USING (VALUES (:person_id, :block_id, :template_id, 'primary'))
        AS source(person_id, block_id, rotation_template_id, role)
    ON target.person_id = source.person_id
       AND target.block_id = source.block_id
       AND target.rotation_template_id = source.rotation_template_id
    WHEN MATCHED THEN
        DO NOTHING
    WHEN NOT MATCHED THEN
        INSERT (id, person_id, block_id, rotation_template_id, role)
        VALUES (gen_random_uuid(), source.person_id, source.block_id,
                source.rotation_template_id, source.role)
    RETURNING id, (xmax = 0) AS was_inserted;
""")
result = await self.db.execute(merge_sql, params)
```

---

## Section 4: EXPLAIN Plan Prediction

Predictions below assume the existing 20260212 indexes are in place, the table sizes mentioned in context (~100 people, ~5,000 assignments, ~10,000 blocks, ~1,000 conflict_alerts, ~500 swaps), and standard PG15 `random_page_cost = 4.0`, `effective_cache_size = 4GB`.

### Query 1: Workload Balance — Assignment JOIN Block JOIN RotationTemplate with ILIKE
**Source:** conflict_auto_resolver.py, line 756  
**SQL equivalent:**
```sql
SELECT COUNT(*)
FROM assignments a
JOIN blocks b ON a.block_id = b.id
JOIN rotation_templates rt ON a.rotation_template_id = rt.id
WHERE a.person_id = :faculty_id
  AND b.date >= CURRENT_DATE
  AND rt.name ILIKE '%FMIT%';
```

**Predicted plan:**
```
Aggregate (cost=180..181 rows=1)
  -> Nested Loop (cost=0.56..179 rows=5)
       -> Seq Scan on assignments a (cost=0..125 rows=50)
            Filter: (person_id = :faculty_id)
       -> Index Scan on blocks_pkey b (cost=0.29..0.31 rows=1)
            Index Cond: (id = a.block_id)
            Filter: (date >= CURRENT_DATE)
       -> Seq Scan on rotation_templates rt (cost=0..1.20 rows=1)
            Filter: (name ~~* '%FMIT%')
```

**Bottleneck:** Sequential scan on `assignments` (no person_id index) + seq scan on `rotation_templates` for ILIKE pattern. With ~5,000 assignments, ~50 per person, scanning is tolerable but not ideal.  
**Optimization:** (1) Add `assignments(person_id)` index → Nested Loop with Index Scan. (2) Replace `ILIKE '%FMIT%'` with boolean `is_fmit` column on `rotation_templates` or a `pg_trgm` GIN index. The ILIKE is the bigger problem — it forces a full scan of `rotation_templates` per iteration.

### Query 2: Coverage Gap — Assignment JOIN Block COUNT with Date Range
**Source:** conflict_auto_resolver.py, line 644  
```sql
SELECT COUNT(*)
FROM assignments a JOIN blocks b ON a.block_id = b.id
WHERE b.date >= :week_start AND b.date < :week_end;
```

**Predicted plan:**
```
Aggregate (cost=220..221 rows=1)
  -> Hash Join (cost=85..218 rows=100)
       Hash Cond: (a.block_id = b.id)
       -> Seq Scan on assignments (cost=0..100 rows=5000)
       -> Hash (cost=40..40 rows=14)
            -> Seq Scan on blocks b (cost=0..40 rows=14)
                 Filter: (date >= :start AND date < :end)
```

**Bottleneck:** Full seq scan of `assignments` (5,000 rows) to hash join against ~14 blocks in the week. Without an index on `assignments.block_id`, PG can't do a nested loop with index lookups.  
**Optimization:** Add `assignments(block_id)` → Hash Join becomes Nested Loop with Index Scan: fetch 14 blocks, then 14 index lookups into assignments. Cost drops from ~220 to ~30.

### Query 3: Activity Resolution — Three Expression Scans
**Source:** schedule_draft_service.py, line 1156  
```sql
SELECT * FROM activities WHERE lower(code) = lower(:input) LIMIT 1;
-- If no match:
SELECT * FROM activities WHERE lower(display_abbreviation) = lower(:input) LIMIT 1;
-- If no match:
SELECT * FROM activities WHERE lower(name) = lower(:input) LIMIT 1;
```

**Predicted plan (each):**
```
Limit (cost=0..5 rows=1)
  -> Seq Scan on activities (cost=0..25 rows=1)
       Filter: (lower(code) = lower(:input))
```

**Bottleneck:** Three sequential scans in the worst case. The `activities` table is likely <100 rows so each scan is fast (~0.1ms), but this is called inside a loop over every draft assignment during credential checking. With 50 assignments, that's up to 150 seq scans.  
**Optimization:** Expression indexes on `lower(code)`, `lower(display_abbreviation)`, `lower(name)` → Index Scan. Better yet, create a single covering expression index or use a lookup cache (already done with `activity_cache` dict in the code, so this is mostly mitigated for repeated lookups within one draft).

### Query 4: Cascading Conflict Check — ConflictAlert COUNT with Multi-Column Filter
**Source:** conflict_auto_resolver.py, line 555  
```sql
SELECT COUNT(*)
FROM conflict_alerts
WHERE id != :alert_id
  AND fmit_week = :week
  AND status IN ('new', 'acknowledged');
```

**Predicted plan:**
```
Aggregate (cost=12..13 rows=1)
  -> Bitmap Heap Scan on conflict_alerts (cost=4.5..12 rows=3)
       Recheck Cond: (fmit_week = :week)
       Filter: (id != :alert_id AND status IN ('new','acknowledged'))
       -> Bitmap Index Scan on idx_conflict_alerts_fmit_week (cost=0..4.5 rows=10)
            Index Cond: (fmit_week = :week)
```

**Bottleneck:** Uses `fmit_week` index but applies status filter post-scan. With ~1,000 alerts and ~20 per week, filtering ~20 rows in heap is fine.  
**Optimization:** Composite `(fmit_week, status)` index would allow index-only scan, but the improvement on 20 rows is negligible (~0.05ms saved). Worth adding only because this query runs in a loop during batch resolution.

### Query 5: Draft Assignment Upsert Check — 4-Column Equality
**Source:** schedule_draft_service.py, line 546  
```sql
SELECT * FROM schedule_draft_assignments
WHERE draft_id = :did AND person_id = :pid
  AND assignment_date = :date AND time_of_day = :tod
LIMIT 1;
```

**Predicted plan:**
```
Limit (cost=0..8 rows=1)
  -> Seq Scan on schedule_draft_assignments (cost=0..35 rows=1)
       Filter: (draft_id = :did AND person_id = :pid AND ...)
```

**Bottleneck:** Despite having indexes on `draft_id` and `person_id` individually, PG likely chooses seq scan because the table is small enough per-draft (~50–200 rows per draft). For larger drafts, this becomes a BitmapAnd of two indexes.  
**Optimization:** Composite unique index `(draft_id, person_id, assignment_date, time_of_day)` gives exact index scan. Also enforces data integrity at the DB level.

### Query 6: Swap Faculty OR-Query — BitmapOr Pattern
**Source:** swap_repository.py, line 151  
```sql
SELECT * FROM swap_records
WHERE source_faculty_id = :fid OR target_faculty_id = :fid
ORDER BY requested_at DESC;
```

**Predicted plan:**
```
Sort (cost=45..46 rows=10)
  Sort Key: requested_at DESC
  -> Seq Scan on swap_records (cost=0..40 rows=10)
       Filter: (source_faculty_id = :fid OR target_faculty_id = :fid)
```

**Bottleneck:** Full table scan of ~500 rows with OR filter, then sort. Without indexes on either faculty FK column, no bitmap OR is possible.  
**Optimization:** Add indexes on `(source_faculty_id)` and `(target_faculty_id)` → BitmapOr of two index scans, skip sort if combined with a covering index. Expected cost drops from 45 to ~8.

### Query 7: HalfDayAssignment Upsert — Composite Point Lookup in Loop
**Source:** schedule_draft_service.py, line 1257  
```sql
SELECT * FROM half_day_assignments
WHERE person_id = :pid AND date = :d AND time_of_day = :tod
LIMIT 1;
```

**Predicted plan:**
```
Limit (cost=0..15 rows=1)
  -> Seq Scan on half_day_assignments (cost=0..150 rows=1)
       Filter: (person_id = :pid AND date = :d AND time_of_day = :tod)
```

**Bottleneck:** Called inside a loop for every draft assignment publish (50–200 iterations). Each does a seq scan on what could be 5,000+ rows. Total: ~0.5s for 100 iterations.  
**Optimization:** Composite unique index `(person_id, date, time_of_day)` → Index Scan per iteration costs ~0.02ms each. Total: ~2ms. **This is the highest-impact single index recommendation.**

### Query 8: Assignment Existence Check — 3-Column Composite
**Source:** call_assignment_service.py, line 862  
```sql
SELECT * FROM assignments
WHERE person_id = :pid AND block_id = :bid AND rotation_template_id = :tid
LIMIT 1;
```

**Predicted plan:**
```
Limit (cost=0..25 rows=1)
  -> Seq Scan on assignments (cost=0..100 rows=1)
       Filter: (person_id = :pid AND block_id = :bid AND rotation_template_id = :tid)
```

**Bottleneck:** Full scan of ~5,000 assignments. Called in a loop during PCAT generation (up to ~20 iterations).  
**Optimization:** Composite index `(person_id, block_id, rotation_template_id)` → exact Index Scan. Cost: ~0.02ms vs ~2ms per call.

### Query 9: Audit Statistics — GROUP BY on Version Tables
**Source:** audit_repository.py, line 246  
```sql
SELECT COUNT(*), v.operation_type, t.user_id, DATE(t.issued_at)
FROM assignment_version v
LEFT JOIN transaction t ON v.transaction_id = t.id
WHERE t.issued_at >= :start AND t.issued_at <= :end
GROUP BY v.operation_type, t.user_id, DATE(t.issued_at);
```

**Predicted plan:**
```
HashAggregate (cost=500..510 rows=30)
  -> Hash Left Join (cost=150..480 rows=2000)
       Hash Cond: (v.transaction_id = t.id)
       -> Seq Scan on assignment_version v (cost=0..100 rows=5000)
       -> Hash (cost=80..80 rows=500)
            -> Seq Scan on transaction t (cost=0..80 rows=500)
                 Filter: (issued_at BETWEEN :start AND :end)
```

**Bottleneck:** Full scan of both tables, hash join, then hash aggregate. The `transaction` table grows unbounded — after a year of use it could have 50,000+ rows. No index on `issued_at` means the date filter always requires a full scan.  
**Optimization:** Add `transaction(issued_at)` index → Index Scan on date range reduces hash build from 50K rows to the relevant date window (~500). Also consider a partial index `WHERE issued_at >= CURRENT_DATE - INTERVAL '90 days'` for the common "recent activity" case.

### Query 10: Bulk Solver Assignment Staging — Assignment JOIN Block per-assignment
**Source:** schedule_draft_service.py, line 1697  
```sql
SELECT * FROM assignments a
JOIN blocks b ON a.block_id = b.id
WHERE a.person_id = :pid AND b.date = :d AND b.time_of_day = :tod
LIMIT 1;
```

**Predicted plan:**
```
Limit (cost=0..30 rows=1)
  -> Nested Loop (cost=0..300 rows=1)
       -> Seq Scan on blocks b (cost=0..200 rows=1)
            Filter: (date = :d AND time_of_day = :tod)
       -> Seq Scan on assignments a (cost=0..100 rows=1)
            Filter: (block_id = b.id AND person_id = :pid)
```

**Bottleneck:** Called in a tight loop for every solver assignment (~200–500 per run). Two nested seq scans per iteration. With 10,000 blocks and 5,000 assignments, each iteration costs ~5ms. Total: ~1–2.5s.  
**Optimization:** (1) `blocks(date, time_of_day)` index → Index Scan for block lookup. (2) `assignments(block_id)` index → Index Scan for assignment lookup. Combined: ~0.1ms per iteration. Total: ~20–50ms. **Second highest-impact optimization.**

---

## Section 5: Connection Pool & Async Tuning

### 5.1 Pool Sizing Recommendation

For a FastAPI app with ~5 concurrent users, ~12 residents, ~8 faculty:

```python
engine = create_async_engine(
    DATABASE_URL,
    # Pool sizing
    pool_size=5,           # Base connections (matches concurrent user count)
    max_overflow=5,        # Burst capacity (total max = 10)
    pool_timeout=30,       # Wait for connection before error (seconds)
    pool_recycle=1800,     # Recycle connections every 30 minutes
    pool_pre_ping=True,    # Verify connection liveness before checkout

    # Statement caching (PG15)
    connect_args={
        "prepared_statement_cache_size": 256,  # Cache prepared statements
        "statement_cache_size": 256,           # asyncpg statement cache
    },

    # Echo for development (disable in production)
    echo=False,
    echo_pool=False,
)
```

**Justification:**
- `pool_size=5`: With 5 concurrent users, 5 base connections ensures no waiting under normal load. PG15 default `max_connections=100`, so 5 is well within budget.
- `max_overflow=5`: During batch operations (solver runs, bulk publish), the app may need extra connections. 10 total connections handles spikes without starving PG.
- `pool_recycle=1800`: Prevents stale connections from hitting PG's `idle_in_transaction_session_timeout`. 30 minutes is conservative for a small deployment.
- `pool_pre_ping=True`: Essential because the app uses long-lived FastAPI workers. Without pre-ping, connections closed by PG (e.g., after restart) cause silent errors.
- `prepared_statement_cache_size=256`: asyncpg can cache prepared statements to avoid re-parsing. With ~75 distinct query patterns identified, 256 provides ample headroom.

### 5.2 Session Management Analysis

**Current state:** The codebase uses two patterns:
1. **Async sessions** (`AsyncSession` via dependency injection) in `call_assignment_service.py` and `async_base.py`
2. **Sync sessions** (`Session`) in `conflict_auto_resolver.py`, `schedule_draft_service.py`, and `swap_repository.py`

**Issues found:**

1. **Mixed async/sync is the biggest risk.** `schedule_draft_service.py` is declared with `async def` methods but uses `self.db.query()` (sync ORM pattern) and `self.db.commit()` (sync commit). This works only if the sync session is wrapped in `run_sync()` or the entire service runs in a thread pool. If the async event loop calls these methods directly, it will block the loop.

2. **Session leak risk in error paths:** `schedule_draft_service.py` lines 505–512 catch exceptions and call `self.db.rollback()`, but if the exception occurs after `self.db.add()` and before `self.db.commit()`, the session may hold uncommitted objects. The `transactional_with_retry` context manager (used in `publish_draft` and `rollback_draft`) correctly handles this, but `create_draft`, `add_assignment_to_draft`, and `discard_draft` do manual try/except without guaranteed cleanup.

3. **`conflict_auto_resolver.py` holds transactions too long.** The `batch_auto_resolve` method (line 316) iterates over all conflict IDs in a single session, calling `analyze_conflict` → `generate_resolution_options` → `_apply_resolution` for each. Each `_apply_resolution` uses `transactional_with_retry` which commits, but the outer loop may hold the session open for seconds during large batches, risking lock contention.

**Recommendations:**
- Refactor `schedule_draft_service.py` to use `AsyncSession` consistently, or explicitly run sync operations via `await asyncio.to_thread(...)`.
- Wrap `create_draft`, `add_assignment_to_draft`, and `discard_draft` in the `transactional_with_retry` context manager for consistent error handling.
- In `batch_auto_resolve`, add periodic `self.db.expire_all()` after every 10 conflicts to release cached objects and reduce memory pressure.

### 5.3 Eager Loading Strategy

**Current approach:** `selectinload` everywhere — this is correct for this data shape.

**Analysis:**
- `selectinload` issues a second `SELECT ... WHERE id IN (...)` query. For N parent rows, it's always 1+1 queries regardless of N. This is ideal for one-to-many relationships like `CallAssignment → Person`.
- `joinedload` would issue a single query with JOINs, but for many-to-one (e.g., loading `person` for 100 call assignments), it would duplicate the parent row data in the result set. With selectinload, the person data comes in a clean second query.

**When to consider `joinedload` instead:**
- Loading a single parent with one child (e.g., `get_by_id_with_relations` for a single SwapRecord with source_faculty + target_faculty). Here, `joinedload` would be 1 query instead of 3. However, with 2 total rows, the difference is negligible.
- **Verdict:** Keep `selectinload` as the default. The code is already well-optimized here.

**Missing eager loads:**
- `conflict_auto_resolver.py` line 73: `self.db.query(Person).filter(Person.id == alert.faculty_id).first()` — this loads the person separately from the alert. If `ConflictAlert` has a `faculty` relationship, add `selectinload(ConflictAlert.faculty)` to `_get_alert()` to eliminate this extra query. The method is called in every analysis, so this saves 1 query per conflict.

### 5.4 Transaction Scope Analysis

| Service | Method | Transaction Duration | Lock Risk |
|---------|--------|---------------------|-----------|
| `call_assignment_service` | `bulk_create_call_assignments` | Loop over N assignments, each calling `create_call_assignment(commit=False)`, then single commit | Low — all flushes, one commit |
| `call_assignment_service` | `bulk_update_call_assignments` | Loop over N IDs with individual SELECT + flush, then commit | **Medium** — long-lived transaction while iterating |
| `conflict_auto_resolver` | `_apply_resolution` | `transactional_with_retry` with `FOR UPDATE` on alert | Low — short, retryable |
| `conflict_auto_resolver` | `batch_auto_resolve` | Outer loop with per-conflict analysis + resolution | **High** — session accumulates objects |
| `schedule_draft_service` | `publish_draft` | `transactional_with_retry` wrapping all assignment applications | **Medium** — could hold lock for 1–2s on large drafts |
| `schedule_draft_service` | `rollback_draft` | `transactional_with_retry` wrapping all rollback operations | **Medium** — same concern |

**Recommendations:**
1. For `bulk_update_call_assignments`: batch into groups of 50 with intermediate commits.
2. For `batch_auto_resolve`: commit after each conflict resolution (already done via `transactional_with_retry` inside `_apply_resolution`), but add `self.db.expire_all()` periodically.
3. For `publish_draft` with large drafts (>100 assignments): consider chunking the loop with intermediate flushes.

### 5.5 Statement Caching

**Current state:** No `prepared_statement_cache_size` configuration visible.

**Recommendation:** If using `asyncpg` (likely, given async SQLAlchemy):
```python
connect_args={"statement_cache_size": 256}
```

This caches prepared statement plans on the asyncpg side. With ~75 distinct query patterns, 256 provides ample room. Each cached statement saves ~0.1–0.5ms of parse/plan time. Over 1,000 queries per minute, that's 100–500ms saved per minute.

If using `psycopg` (sync connections for conflict_auto_resolver):
```python
# psycopg3 uses server-side prepared statements automatically
# Ensure pool_pre_ping doesn't invalidate the cache:
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=1800,
)
```

---

## Section 6: Partial & Expression Indexes

### 6.1 Status Filtering — Partial Indexes

**Pattern:** Many queries filter `WHERE status = 'pending'` or `WHERE status IN ('new', 'acknowledged')`.

| Table | Status Values Queried | Recommended Partial Index | Size Savings vs Full | Maintenance Cost |
|-------|----------------------|--------------------------|---------------------|-----------------|
| `conflict_alerts` | `NEW`, `ACKNOWLEDGED` (hot path in auto-resolver) | `CREATE INDEX idx_conflict_alerts_active ON conflict_alerts (faculty_id, fmit_week) WHERE status IN ('new', 'acknowledged');` | ~60% savings (only ~400 of 1,000 alerts are active) | Low — only updated when status changes |
| `swap_records` | `PENDING` (hot path for faculty inbox) | `CREATE INDEX idx_swap_records_pending ON swap_records (target_faculty_id, requested_at DESC) WHERE status = 'pending';` | ~80% savings (~100 of 500 swaps are pending) | Low — updated on status change |
| `schedule_drafts` | `DRAFT` (active draft lookup) | `CREATE INDEX idx_schedule_drafts_active ON schedule_drafts (target_start_date, target_end_date) WHERE status = 'draft';` | ~90% savings (typically <5 active drafts) | Minimal |

**Verdict for conflict_alerts:** Strong YES. The auto-resolver calls `_has_cascading_conflicts` and `_identify_blockers` which filter by `status IN ('new', 'acknowledged')` combined with `fmit_week`. A partial index covering only active conflicts reduces index size from ~1,000 to ~400 entries and makes the index fit entirely in cache.

**Verdict for swap_records PENDING:** Strong YES. `find_pending_for_faculty` (line 236) is the faculty's inbox query — it runs on every page load. A partial index on `(target_faculty_id, requested_at DESC) WHERE status = 'pending'` means this query does an index-only scan of typically <10 rows.

### 6.2 Active Records — `WHERE is_active = true`

The `users` table has `is_active` indexed, but `is_active` is a boolean with likely >90% TRUE. A full B-tree index on a boolean is nearly useless — PG will prefer a seq scan because most rows match.

**Recommendation:**
```sql
-- Replace the low-selectivity boolean index with a partial index
DROP INDEX IF EXISTS idx_users_is_active;
CREATE INDEX idx_users_active_role ON users (role) WHERE is_active = true;
```

This is smaller (only active users), and supports the actual query pattern: "find active users by role."

### 6.3 Date-Bounded / Rolling Window Indexes

**Pattern:** The audit queries in `audit_repository.py` typically filter `WHERE t.issued_at >= :start_date`, and the common case is "last 30 days" or "last 90 days."

```sql
-- Rolling window partial index for recent audit activity
CREATE INDEX idx_transaction_recent
    ON transaction (issued_at DESC, user_id)
    WHERE issued_at >= CURRENT_DATE - INTERVAL '90 days';
```

**Trade-off:**
- Size: ~25% of full index (90 days of data vs. lifetime)
- Maintenance: PG doesn't automatically redefine the boundary. You'd need to recreate this index periodically (e.g., quarterly via a maintenance script or `pg_partman`).
- **Verdict:** For a small system, a full `transaction(issued_at)` index is simpler and sufficient. Consider the partial approach only if the `transaction` table exceeds 100K rows.

### 6.4 Expression Indexes

| Expression | Table | Query Location | Recommended Index |
|------------|-------|---------------|-------------------|
| `func.lower(Activity.code)` | activities | schedule_draft_service.py:1158 | `CREATE INDEX idx_activities_code_lower ON activities (lower(code));` |
| `func.lower(Activity.display_abbreviation)` | activities | schedule_draft_service.py:1165 | `CREATE INDEX idx_activities_abbrev_lower ON activities (lower(display_abbreviation));` |
| `func.lower(Activity.name)` | activities | schedule_draft_service.py:1173 | `CREATE INDEX idx_activities_name_lower ON activities (lower(name));` |
| `func.upper(RotationTemplate.abbreviation)` | rotation_templates | call_assignment_service.py:798 | `CREATE INDEX idx_rotation_templates_abbrev_upper ON rotation_templates (upper(abbreviation));` |
| `RotationTemplate.name.ilike('%FMIT%')` | rotation_templates | conflict_auto_resolver.py:764 | Either: (a) `CREATE INDEX idx_rotation_templates_name_trgm ON rotation_templates USING gin (name gin_trgm_ops);` or (b) Add `is_fmit BOOLEAN` column |

**Size savings vs full index:** Expression indexes are the same size as a regular B-tree on the computed column. For the `activities` table (~50–100 rows), each index is <8KB. Negligible storage cost.

**Recommended approach for ILIKE '%FMIT%':** The `pg_trgm` GIN index supports `ILIKE` patterns, but on a 20-row table it adds complexity for no real performance gain. The better approach:

```sql
-- Add a boolean flag (one-time migration)
ALTER TABLE rotation_templates ADD COLUMN is_fmit BOOLEAN
    GENERATED ALWAYS AS (name ILIKE '%FMIT%') STORED;
CREATE INDEX idx_rotation_templates_is_fmit
    ON rotation_templates (is_fmit) WHERE is_fmit = true;
```

Then change the query:
```python
# Before
RotationTemplate.name.ilike("%FMIT%")
# After
RotationTemplate.is_fmit.is_(True)
```

---

## Section 7: Materialized Views & Denormalization

### 7.1 Call Equity Statistics

**Query pattern:** `get_equity_report` (line 605) fetches all call assignments in a date range, then computes Sunday/weekday counts per person in Python.

| Aspect | Assessment |
|--------|------------|
| **Worth materializing?** | **NO** at current scale. The query fetches ~200–400 call assignments (one academic year) and processes them in Python. Total time: ~20ms query + ~5ms Python. A materialized view would save ~15ms but add complexity. |
| **Refresh frequency** | Would need refresh after every call assignment create/update/delete. |
| **Staleness tolerance** | Low — equity data is shown in real-time preview UI with simulated changes. Stale data would show incorrect previews. |
| **Storage cost** | Tiny — ~20 rows (one per faculty). |
| **Recommendation** | Instead of a matview, push the aggregation to SQL to avoid transferring 400 rows: |

```python
# Replace Python-side aggregation with SQL aggregation
stmt = (
    select(
        CallAssignment.person_id,
        Person.name,
        func.count(CallAssignment.id).filter(
            func.extract('dow', CallAssignment.date) == 0  # Sunday
        ).label('sunday_calls'),
        func.count(CallAssignment.id).filter(
            func.extract('dow', CallAssignment.date) != 0
        ).label('weekday_calls'),
        func.count(CallAssignment.id).label('total_calls'),
    )
    .join(Person, CallAssignment.person_id == Person.id)
    .where(
        CallAssignment.date.between(start_date, end_date),
        CallAssignment.call_type == 'overnight',
    )
    .group_by(CallAssignment.person_id, Person.name)
)
```

This returns ~8 rows instead of ~400, reducing network transfer by 98%.

### 7.2 Conflict Complexity Scores

**Query pattern:** `_calculate_complexity` calls `_count_affected_weeks`, `_count_involved_faculty`, and `_has_cascading_conflicts` — each hitting the database.

| Aspect | Assessment |
|--------|------------|
| **Worth materializing?** | **MAYBE** — but only as a cache column, not a matview. |
| **Recommendation** | Add a `complexity_score FLOAT` and `last_analyzed_at TIMESTAMP` column to `conflict_alerts`. Populate on first analysis, invalidate when related data changes. This avoids 3 queries per conflict during batch resolution. |

```sql
ALTER TABLE conflict_alerts
    ADD COLUMN complexity_score FLOAT,
    ADD COLUMN last_analyzed_at TIMESTAMPTZ;
```

### 7.3 Audit Summaries

**Query pattern:** `get_audit_statistics` runs aggregate queries across 4 version tables with JOINs to `transaction`.

| Aspect | Assessment |
|--------|------------|
| **Worth materializing?** | **YES** — this is the strongest matview candidate. |
| **Refresh frequency** | Daily (overnight). Audit stats are used for dashboards, not real-time decisions. |
| **Staleness tolerance** | High — 24-hour-old data is acceptable for audit dashboards. |
| **Storage cost** | ~100 rows (days × entity_types × operations). |
| **Query speedup** | 4 table scans + 4 JOINs → single table scan. Estimated 10× speedup. |

```sql
CREATE MATERIALIZED VIEW mv_audit_daily_stats AS
SELECT
    DATE(t.issued_at) AS change_date,
    'assignment' AS entity_type,
    v.operation_type,
    t.user_id,
    COUNT(*) AS change_count
FROM assignment_version v
LEFT JOIN transaction t ON v.transaction_id = t.id
GROUP BY DATE(t.issued_at), v.operation_type, t.user_id

UNION ALL

SELECT DATE(t.issued_at), 'absence', v.operation_type, t.user_id, COUNT(*)
FROM absence_version v
LEFT JOIN transaction t ON v.transaction_id = t.id
GROUP BY DATE(t.issued_at), v.operation_type, t.user_id

UNION ALL

SELECT DATE(t.issued_at), 'schedule_run', v.operation_type, t.user_id, COUNT(*)
FROM schedule_run_version v
LEFT JOIN transaction t ON v.transaction_id = t.id
GROUP BY DATE(t.issued_at), v.operation_type, t.user_id

UNION ALL

SELECT DATE(t.issued_at), 'swap_record', v.operation_type, t.user_id, COUNT(*)
FROM swap_record_version v
LEFT JOIN transaction t ON v.transaction_id = t.id
GROUP BY DATE(t.issued_at), v.operation_type, t.user_id;

CREATE UNIQUE INDEX ON mv_audit_daily_stats (change_date, entity_type, operation_type, user_id);

-- Refresh daily via pg_cron or application scheduler
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_audit_daily_stats;
```

### 7.4 Schedule Coverage

**Query pattern:** Coverage gap checks run in `_check_coverage_gaps` and `get_coverage_report`. Both query assignments + blocks for date ranges.

| Aspect | Assessment |
|--------|------------|
| **Worth materializing?** | **NO** — the query is simple (COUNT with date filter) and returns a single integer. Materialization overhead exceeds benefit. |
| **Better optimization** | The `blocks(date, time_of_day)` and `assignments(block_id)` indexes recommended in Section 2 will make these queries return in <1ms. |

---

## Section 8: Monitoring & Observability Recommendations

### 8.1 pg_stat_statements Configuration

Add to `postgresql.conf`:

```ini
# ── pg_stat_statements ──────────────────────────────────────
shared_preload_libraries = 'pg_stat_statements'  # Requires restart

pg_stat_statements.max = 5000          # Track up to 5000 distinct queries
pg_stat_statements.track = 'all'       # Track all statements (top-level + nested)
pg_stat_statements.track_utility = on  # Track DDL and utility commands
pg_stat_statements.track_planning = on # PG15: Track planning time separately

# PG15 auto-enables compute_query_id — no need to set explicitly
```

**Top-N query identification dashboard:**

```sql
-- Top 10 queries by total execution time
SELECT
    queryid,
    LEFT(query, 100) AS query_preview,
    calls,
    round(total_exec_time::numeric, 2) AS total_ms,
    round(mean_exec_time::numeric, 2) AS avg_ms,
    round(stddev_exec_time::numeric, 2) AS stddev_ms,
    rows,
    round(100.0 * shared_blks_hit / NULLIF(shared_blks_hit + shared_blks_read, 0), 2)
        AS cache_hit_pct,
    -- PG15: temp file I/O
    temp_blks_read,
    temp_blks_written
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;

-- Top 10 by average time (slowest individual queries)
SELECT queryid, LEFT(query, 100), calls,
    round(mean_exec_time::numeric, 2) AS avg_ms,
    round(max_exec_time::numeric, 2) AS max_ms
FROM pg_stat_statements
WHERE calls > 5  -- Exclude one-off queries
ORDER BY mean_exec_time DESC
LIMIT 10;
```

**Reset frequency:** Reset weekly via `SELECT pg_stat_statements_reset();` in a Monday morning cron job. This prevents historical accumulation from masking current problems.

### 8.2 auto_explain Configuration

```ini
# ── auto_explain ────────────────────────────────────────────
shared_preload_libraries = 'pg_stat_statements, auto_explain'

auto_explain.log_min_duration = '100ms'     # Log plans for queries > 100ms
auto_explain.log_analyze = on                # Include actual timing (ANALYZE)
auto_explain.log_buffers = on                # Include buffer usage
auto_explain.log_timing = on                 # Include per-node timing
auto_explain.log_triggers = on               # Include trigger timing
auto_explain.log_nested_statements = on      # Capture prepared statements
auto_explain.log_format = 'json'             # JSON for machine parsing
auto_explain.sample_rate = 1.0               # Log 100% of qualifying queries
                                             # (safe at this scale; reduce to 0.1
                                             # if >1000 queries/sec)
```

**Why 100ms threshold:** Your middleware uses 1s warning / 5s critical. Setting auto_explain at 100ms catches the "precursor" slow queries before they hit the 1s warning. At this data scale, 100ms queries are unusual and worth investigating.

### 8.3 pg_stat_user_tables — Sequential Scan Monitoring

```sql
-- Tables with high sequential scan counts (potential missing indexes)
SELECT
    schemaname, relname,
    seq_scan, seq_tup_read,
    idx_scan, idx_tup_fetch,
    CASE WHEN seq_scan + idx_scan > 0
         THEN round(100.0 * idx_scan / (seq_scan + idx_scan), 1)
         ELSE 0
    END AS idx_scan_pct,
    n_live_tup
FROM pg_stat_user_tables
WHERE seq_scan > 100       -- Focus on frequently-scanned tables
ORDER BY seq_tup_read DESC
LIMIT 15;
```

**Tables to watch:**

| Table | Expected Behavior After Indexing | Alert If |
|-------|--------------------------------|----------|
| `assignments` | idx_scan_pct > 90% | seq_scan increases after deploying new indexes |
| `blocks` | idx_scan_pct > 95% | seq_scan > 100/hour |
| `half_day_assignments` | idx_scan_pct > 95% | seq_scan > 50/hour |
| `conflict_alerts` | idx_scan_pct > 80% | seq_scan > 200/hour |
| `swap_records` | idx_scan_pct > 80% | seq_scan > 100/hour |
| `people` | seq_scan acceptable (100 rows) | Not a concern |
| `rotation_templates` | seq_scan acceptable (20 rows) | Not a concern |

### 8.4 pg_stat_user_indexes — Unused Index Detection

```sql
-- Indexes that haven't been used since last stats reset
SELECT
    schemaname, relname, indexrelname,
    idx_scan,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND schemaname = 'public'
ORDER BY pg_relation_size(indexrelid) DESC;
```

**Run this query 30 days after deploying the Wave 4 indexes** (Section 2.6). Any index with `idx_scan = 0` after 30 days of production traffic should be reviewed for removal.

### 8.5 Application-Level Monitoring

The timing middleware currently tracks response time. Extend it to log:

```python
# Add to timing middleware
import logging
from time import perf_counter

logger = logging.getLogger("query_monitor")

class QueryTimingMiddleware:
    async def __call__(self, request, call_next):
        start = perf_counter()

        # Track per-request query count (via SQLAlchemy event)
        request.state.query_count = 0
        request.state.total_query_ms = 0.0

        response = await call_next(request)

        elapsed = perf_counter() - start
        query_count = getattr(request.state, 'query_count', 0)
        query_ms = getattr(request.state, 'total_query_ms', 0.0)

        # Log N+1 detection
        if query_count > 20:
            logger.warning(
                "N+1 suspect: %s %s — %d queries in %.1fms (%.1fms in DB)",
                request.method, request.url.path,
                query_count, elapsed * 1000, query_ms
            )

        # Log slow queries
        if elapsed > 1.0:
            logger.warning(
                "SLOW: %s %s — %.1fs (%d queries, %.1fms in DB)",
                request.method, request.url.path,
                elapsed, query_count, query_ms
            )
        elif elapsed > 5.0:
            logger.critical(
                "CRITICAL: %s %s — %.1fs (%d queries, %.1fms in DB)",
                request.method, request.url.path,
                elapsed, query_count, query_ms
            )

        return response
```

Register a SQLAlchemy event listener to count queries:

```python
from sqlalchemy import event

@event.listens_for(engine.sync_engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info["query_start"] = perf_counter()

@event.listens_for(engine.sync_engine, "after_cursor_execute")  
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    elapsed = (perf_counter() - conn.info.get("query_start", 0)) * 1000
    # Increment request-level counters
    # (requires threading.local or contextvars to link to request)
```

### 8.6 Alerting Thresholds

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| `pg_stat_statements` mean_exec_time for any query | > 100ms | > 500ms | Investigate plan regression |
| `pg_stat_statements` calls/min for any single queryid | > 1000 | > 5000 | N+1 or hot loop detected |
| `pg_stat_user_tables` seq_tup_read/hour for assignments | > 50,000 | > 200,000 | Missing index or plan regression |
| `auto_explain` logs/hour | > 50 | > 200 | Systemic slow query problem |
| Application: requests > 1s | > 5/min | > 20/min | Infrastructure or query issue |
| Application: requests > 5s | > 1/min | > 5/min | Immediate investigation |
| Connection pool: wait events | > 5/min | > 20/min | Increase pool_size or max_overflow |
| `pg_stat_activity` idle in transaction > 30s | > 3 sessions | > 5 sessions | Session leak or long transaction |
| Cache hit ratio (`shared_blks_hit / total`) | < 95% | < 90% | Increase `shared_buffers` |
| Temp file usage (PG15 pg_stat_statements) | temp_blks_written > 0 for SELECT | temp_blks_written > 1000 | Increase `work_mem` or add index |

### 8.7 Copy-Paste postgresql.conf Additions

```ini
# ================================================================
# Performance Monitoring — add to postgresql.conf
# Requires PostgreSQL restart for shared_preload_libraries change
# ================================================================

# --- Extensions ---
shared_preload_libraries = 'pg_stat_statements, auto_explain'

# --- pg_stat_statements ---
pg_stat_statements.max = 5000
pg_stat_statements.track = 'all'
pg_stat_statements.track_utility = on
pg_stat_statements.track_planning = on

# --- auto_explain ---
auto_explain.log_min_duration = '100ms'
auto_explain.log_analyze = on
auto_explain.log_buffers = on
auto_explain.log_timing = on
auto_explain.log_triggers = on
auto_explain.log_nested_statements = on
auto_explain.log_format = 'json'
auto_explain.sample_rate = 1.0

# --- Memory (tune for small instance) ---
shared_buffers = '256MB'          # 25% of 1GB RAM, or tune to fit
work_mem = '16MB'                 # Per-sort/hash, increase if temp files appear
maintenance_work_mem = '128MB'    # For VACUUM, CREATE INDEX
effective_cache_size = '768MB'    # Hint for planner (75% of RAM)

# --- Connection ---
max_connections = 30              # 10 app + 5 pgbouncer + 5 admin + buffer
idle_in_transaction_session_timeout = '60s'  # Kill leaked transactions

# --- Logging ---
log_min_duration_statement = 500  # Log queries over 500ms (complements auto_explain)
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on
log_temp_files = 0                # Log all temp file usage
log_autovacuum_min_duration = 0   # Log all autovacuum runs

# --- Planner ---
random_page_cost = 1.1            # SSD storage (default 4.0 is for spinning disk)
effective_io_concurrency = 200    # SSD concurrent reads
```

After adding, run:
```sql
-- Create the extension (one-time, after restart)
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Verify
SELECT * FROM pg_stat_statements LIMIT 1;
```

---

## Summary of Highest-Impact Actions

| Priority | Action | Expected Impact | Effort |
|----------|--------|-----------------|--------|
| **P0** | Add `half_day_assignments(person_id, date, time_of_day)` unique index | Publish draft: ~500ms → ~2ms | 1 migration |
| **P0** | Add `blocks(date, time_of_day)` + `assignments(block_id)` indexes | Solver staging: ~2.5s → ~50ms | 1 migration |
| **P0** | Enable `pg_stat_statements` + `auto_explain` | Visibility into all query performance | Config change + restart |
| **P1** | Add `assignments(person_id, block_id, rotation_template_id)` index | PCAT generation: ~40ms → ~0.4ms | 1 migration |
| **P1** | Add expression indexes on `activities` (lower(code), etc.) | Activity resolution: 3× seq scan → 3× index scan | 1 migration |
| **P1** | Replace `ILIKE '%FMIT%'` with `is_fmit` boolean column | Workload query: seq scan → point lookup | 1 migration + code change |
| **P1** | Add `swap_records` faculty FK indexes | Swap lookups: seq scan → index scan | 1 migration |
| **P2** | Implement MERGE for upsert patterns | 50% fewer round trips for upserts | Code refactor |
| **P2** | Create `mv_audit_daily_stats` materialized view | Audit dashboard: 4 JOINs → single scan | 1 migration + cron |
| **P2** | Add partial indexes for status filtering | 60–90% index size reduction | 1 migration |
| **P2** | Push equity aggregation to SQL | 98% less data transfer | Code refactor |
| **P3** | Refactor mixed async/sync session usage | Eliminate event loop blocking risk | Code refactor |
| **P3** | Configure connection pool with statement caching | ~100–500ms/min saved on parse/plan | Config change |
