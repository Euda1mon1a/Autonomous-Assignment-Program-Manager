# Hardcoded-to-Postgres Migration Roadmap

> **Created:** 2026-03-14 | **Updated:** 2026-03-14 | **Status:** Tracks 1-4 Complete, Track 5-6 Backlog | **Priority:** FOUNDATION
>
> **Problem:** Almost nothing that is changeable by a human should be hardcoded in Python.
> Multiple audits (Gemini, Claude) found that scheduling policy, preload rules, constraint
> behavior, role defaults, and compliance settings are defined in Python code instead of
> Postgres — making them impossible for coordinators to change without a code deploy.

---

## Severity Legend

| Icon | Meaning |
|------|---------|
| 🔴 | **DB exists but solver ignores it** — worst case, false sense of control |
| 🟡 | **Hardcoded in Python, no DB surface** — needs new table or columns |
| 🟢 | **Already DB-backed and solver reads it** — no action needed |

---

## Track 1: Constraint Hard→Soft Refactor

**Status:** Classified (PR #1297 wired DB, §1.4 in PLATFORM_WIRING_ROADMAP)

16 of 23 active hard constraints are policy rules using `model.Add()` (infeasible if violated) when they should be soft constraints with high weights (best-effort with penalty). Hard/soft is Python inheritance — the DB cannot change it.

| Constraint | Current | Target | Priority |
|-----------|---------|--------|----------|
| Availability | Hard | **Keep Hard** (physical) | — |
| CallAvailability | Hard | **Keep Hard** (physical) | — |
| MaxPhysiciansInClinic | Hard | **Keep Hard** (physical) | — |
| ProtectedSlot | Hard | **Keep Hard** (locked fact) | — |
| ClinicCapacity | Hard | Borderline — keep if room cap | Low |
| ResidentInpatientHeadcount | Hard | Borderline — keep if true cap | Low |
| WeekendWork | Hard | Borderline — keep if template truth | Low |
| 80HourRule | Hard | 🟡 **→ Soft** (weight 1000) | High |
| 1in7Rule | Hard | 🟡 **→ Soft** (weight 1000) | High |
| SupervisionRatio | Hard | 🟡 **→ Soft** (weight 1000) | High |
| WednesdayAMInternOnly | Hard | 🟡 **→ Soft** | Medium |
| NightFloatPostCall | Hard | 🟡 **→ Soft** | Medium |
| PostFMITRecovery | Hard | 🟡 **→ Soft** | Medium |
| FacultyPrimaryDutyClinic | Hard | 🟡 **→ Soft** | Medium |
| FacultyDayAvailability | Hard | 🟡 **→ Soft** | Medium |
| FacultyRoleClinic | Hard | 🟡 **→ Soft** | Medium |
| OvernightCallCoverage | Hard | 🟡 **→ Soft** | Medium |
| OvernightCallGeneration | Hard | 🟡 **→ Soft** | Medium |
| SMResidentFacultyAlignment | Hard | 🟡 **→ Soft** | Low |
| SMFacultyNoRegularClinic | Hard | 🟡 **→ Soft** | Low |
| FMITWeekBlocking | Hard | 🟡 **→ Soft** | Low |
| FMITMandatoryCall | Hard | 🟡 **→ Soft** | Low |
| AdjunctCallExclusion | Hard | 🟡 **→ eligibility filter** | Low |

**Work:** Change Python base class from `HardConstraint` to `SoftConstraint`, assign weight, test solver convergence. One constraint per PR.

---

## Track 2: Preload Rules → Postgres

**Status:** Plan approved (this session), implementation starting

The preload service has a 300-line switch statement mapping rotation codes to AM/PM activities per day. These are scheduling policy decisions that coordinators should control from the UI.

### Phase 1: Classification columns on `rotation_templates`

| What | Current Location | Target | Status |
|------|-----------------|--------|--------|
| Offsite rotations | 🟡 `constants.py` OFFSITE_ROTATIONS (6 entries) | `rotation_templates.is_offsite` | Planned |
| LEC-exempt rotations | 🟡 `constants.py` LEC_EXEMPT_ROTATIONS (17) | `rotation_templates.is_lec_exempt` | Planned |
| Continuity-exempt | 🟡 `constants.py` INTERN_CONTINUITY_EXEMPT (17) | `rotation_templates.is_continuity_exempt` | Planned |
| Saturday-off rotations | 🟡 `constants.py` SATURDAY_OFF_ROTATIONS (28) | `rotation_templates.is_saturday_off` | Planned |
| Simple preload activity | 🟡 `rotation_codes.py` switch statement | `rotation_templates.preload_activity_code` | Planned |

### Phase 2: Complex day-of-week patterns via `weekly_patterns`

| What | Current Location | Target | Status |
|------|-----------------|--------|--------|
| KAP daily pattern | 🟡 `rotation_codes.py` get_kap_codes() | `weekly_patterns` rows | Backlog |
| HILO pre/post clinic | 🟡 `rotation_codes.py` get_hilo_codes() | `weekly_patterns` rows | Backlog |
| NF-combined specialty map | 🟡 `constants.py` NF_COMBINED_ACTIVITY_MAP (7) | `rotation_templates` FK or `weekly_patterns` | Backlog |
| Rotation aliases | 🟡 `constants.py` ROTATION_ALIASES (34) | `rotation_aliases` table or template column | Backlog |

---

## Track 3: ACGME/Compliance Settings — DB Exists, Solver Ignores

**Status:** 🔴 **Worst case — false sense of control**

`ApplicationSettings` table stores work_hours_per_week, max_consecutive_days, min_days_off_per_week, and PGY supervision ratios. But the solver hardcodes the same values in Python constants and never reads the DB.

| Setting | DB Location | Solver Location (ignored) | Priority |
|---------|------------|--------------------------|----------|
| Work hours/week (80) | 🔴 `settings.py:57` | `acgme.py:221` (hardcoded 80) | **Critical** |
| Max consecutive days (7) | 🔴 `settings.py:57` | `acgme.py:531` (hardcoded) | **Critical** |
| Min days off/week (1) | 🔴 `settings.py:57` | `acgme.py:531` (hardcoded) | **Critical** |
| PGY-1 supervision ratio | 🔴 `settings.py:57` | `acgme.py:813` (hardcoded) | **Critical** |
| PGY-2 supervision ratio | 🔴 `settings.py:57` | `acgme.py:813` (hardcoded) | **Critical** |
| PGY-3 supervision ratio | 🔴 `settings.py:57` | `acgme.py:813` (hardcoded) | **Critical** |

**Work:** Solver constraint classes read from `ApplicationSettings` at init instead of using Python constants. Small change per constraint, high impact.

---

## Track 4: Primary Duty Policy → Postgres

**Status:** 🟡 Hardcoded in Airtable JSON export

`PrimaryDutyConfig` is parsed from a JSON file and carries clinic min/max plus weekday availability. Both `FacultyPrimaryDutyClinicConstraint` and `FacultyDayAvailabilityConstraint` read it from code-side config, not the DB.

| What | Current Location | Target | Priority |
|------|-----------------|--------|----------|
| Faculty clinic min/max | 🟡 `primary_duty.py:41` (JSON config) | New `primary_duty_configs` table | High |
| Faculty available days | 🟡 `primary_duty.py:41` (JSON config) | Same table or `faculty_weekly_templates` | High |
| Allowed clinic templates | 🟡 `primary_duty.py` (JSON config) | FK to `rotation_templates` | High |

---

## Track 5: Role Defaults & Call Preferences → Postgres

**Status:** 🟡 Derived in Python from `faculty_role`

Role-based defaults (clinic limits, call preferences) are computed as Python properties on the Person model based on `faculty_role`. These are admin policy, not code.

| What | Current Location | Target | Priority |
|------|-----------------|--------|----------|
| weekly_clinic_limit | 🟡 `person.py:289` (code property) | `people` column or role config table | Medium |
| block_clinic_limit | 🟡 `person.py:323` (code property) | Same | Medium |
| avoid_tuesday_call | 🟡 `person.py:354` (code property) | `faculty_schedule_preferences` | Medium |
| prefer_wednesday_call | 🟡 `person.py:359` (code property) | `faculty_schedule_preferences` | Medium |
| sm_clinic_weekly_target | 🟡 Python code | `people` column or SM config | Medium |

**Note:** Per-person DB fields already exist for some of these (`max_clinic_halfdays_per_week` on `people`). The issue is the solver falls back to code defaults when DB fields are NULL. Fix: require DB fields, remove code fallbacks.

---

## Track 6: Calendar/Timetable Policy → Postgres

**Status:** 🟡 Hardcoded day-of-week checks

| What | Current Location | Target | Priority |
|------|-----------------|--------|----------|
| Overnight call nights (Sun-Thu) | 🟡 `call_coverage.py:34` | `scheduling_settings` or config table | Low |
| FMIT week definition (Fri-Thu) | 🟡 `fmit.py:46` | Same | Low |
| Wednesday AM intern-only | 🟡 `temporal.py:27` | `weekly_patterns` or requirements | Low |
| Last Wednesday LEC/ADV | 🟡 `rotation_codes.py:205` | `weekly_patterns` | Low |

---

## What's Already Correct (No Action)

| What | DB Location | Status |
|------|------------|--------|
| Rotation templates (name, type, max_residents) | `rotation_templates` | 🟢 Good |
| includes_weekend_work | `rotation_templates` | 🟢 Good |
| is_block_half_rotation | `rotation_templates` | 🟢 Good |
| Activity definitions | `activities` | 🟢 Good |
| Faculty weekly templates | `faculty_weekly_templates` | 🟢 Good |
| Weekly patterns | `weekly_patterns` | 🟢 Good (underutilized) |
| Activity requirements (min/max/target) | `rotation_activity_requirements` | 🟢 Good |
| Graduation requirements | `graduation_requirements` | 🟢 Good (empty) |
| Constraint enabled/weight | `constraint_configurations` | 🟢 Good (PR #1297) |
| Absences | `absences` | 🟢 Good |
| Block assignments | `block_assignments` | 🟢 Good |
| Per-person clinic caps | `people.max_clinic_halfdays_per_week` | 🟢 Good |

---

## Recommended Execution Order

| # | Track | What | Effort | Impact | Status |
|---|-------|------|--------|--------|--------|
| 1 | **3** | Wire ACGME constraints to ApplicationSettings | S | 🔴 | **DONE** (PR #1301) |
| 2 | **2.1** | Preload classification columns on rotation_templates | M | 🟡 | **DONE** (PR #1302) |
| 3 | **4** | Primary duty policy → Postgres | M | 🟡 | **DONE** (PRs #1303-#1305, #1308, #1312) |
| 4 | **1** | Hard→soft constraint refactor | L | 🟡 | **DONE** class change (PRs #1310-#1311). Solver semantics partial. |
| 5 | **5** | Role defaults from DB, remove code fallbacks | S | 🟡 | Backlog |
| 6 | **2.2** | Complex day-of-week patterns via weekly_patterns | M | 🟡 | Backlog |
| 7 | **6** | Calendar policy → Postgres | S | 🟡 | Backlog |

## Related Planning Documents

| Document | Scope | Status |
|----------|-------|--------|
| `GUI_EDITABILITY_BOUNDARY.md` | What should be GUI-editable vs DB-only vs Python-only | Reference (architecture) |
| `POLICY_STORAGE_BOUNDARY.md` | DB vs Python ownership decision rules | Reference (architecture) |
| `AI_POLICY_STORAGE_BOUNDARY.md` | Agent guidance: never build GUI for Python constants | Reference (development) |
| `POLICY_GUI_MIGRATION_BACKLOG_20260314.md` | Concrete follow-up list after PRs #1297-#1312 | Active backlog |
| `MCP_FOLLOWUP_BACKLOG_20260314.md` | MCP tools needed for new DB-backed surfaces | Active backlog |
| `OVERNIGHT_WORK_PLAN_20260314.md` | Completed overnight items (PRs #1307-#1311) | Done |

**Total scope:** ~7 PRs across ~4 weeks if done sequentially. Tracks 1-3 are parallelizable.

---

## References

- `PLATFORM_WIRING_ROADMAP.md` §1.3 (constraints in DB — DONE), §1.4 (hard→soft — planned)
- Memory: `feedback_constraint-ssot.md`, `project_hard-soft-constraint-refactor.md`
- Source: Gemini deep audit (2026-03-13), Claude preload audit (2026-03-14)
