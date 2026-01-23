# Block 10 Audit Gaps - Visual Guide

> **Purpose:** Human-auditable documentation of scheduling system gaps
> **Date:** 2026-01-20
> **Block 10:** March 12 - April 8, 2026

---

## Source of Truth

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           WHAT IS "TRUTH"?                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                                                                     │   │
│   │   DATABASE (half_day_assignments)  ══════▶  SOURCE OF TRUTH        │   │
│   │   ─────────────────────────────────                                 │   │
│   │   Block 10 doesn't exist until it's locked in here.                │   │
│   │   This is what gets audited. This is what matters.                 │   │
│   │                                                                     │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│   ROSETTA (vestigial)                                                        │
│   ───────────────────                                                        │
│   Excel file used during development to derive the Python code.             │
│   The patterns were extracted, the .py was generated, it works.             │
│   ROSETTA served its purpose. The code is the living artifact now.          │
│                                                                              │
│   Excel export for MSAs uses the same familiar format,                       │
│   but the data comes from DB, not ROSETTA.                                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. The Big Picture: Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SCHEDULING DATA FLOW                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   INPUTS (Human Configured)              PROCESSING                 OUTPUT  │
│   ──────────────────────────             ──────────                 ──────  │
│                                                                              │
│   ┌──────────────┐                                                          │
│   │   people     │───┐                                                      │
│   │  (faculty/   │   │                                                      │
│   │  residents)  │   │     ┌─────────────────────┐                          │
│   └──────────────┘   │     │                     │      ┌──────────────────┐│
│                      ├────▶│  SyncPreloadService │─────▶│                  ││
│   ┌──────────────┐   │     │                     │      │ half_day_        ││
│   │  absences    │───┤     └─────────────────────┘      │ assignments      ││
│   │  (leave,     │   │              │                   │                  ││
│   │  TDY, etc)   │   │              ▼                   │ (56 slots per    ││
│   └──────────────┘   │     ┌─────────────────────┐      │  person per      ││
│                      │     │ FacultyAssignment   │─────▶│  block)          ││
│   ┌──────────────┐   │     │ ExpansionService    │      │                  ││
│   │  inpatient_  │───┤     └─────────────────────┘      │ source:          ││
│   │  preloads    │   │              │                   │  - preload       ││
│   │  (FMIT, NF)  │   │              ▼                   │  - manual        ││
│   └──────────────┘   │     ┌─────────────────────┐      │  - solver        ││
│                      │     │                     │      │  - template      ││
│   ┌──────────────┐   │     │  CPSATActivitySolver│─────▶│                  ││
│   │  call_       │───┘     │  (OR-Tools)         │      └──────────────────┘│
│   │  assignment  │         │                     │                          │
│   │  (faculty    │         └─────────────────────┘                          │
│   │   call)      │                                                          │
│   └──────────────┘                                                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. The Wiring Gaps

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CURRENT WIRING STATUS                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                        GUI                 API              DATABASE         │
│                     (Frontend)          (Backend)           (Postgres)       │
│                     ──────────          ─────────           ──────────       │
│                                                                              │
│  PEOPLE/FACULTY                                                              │
│  ──────────────                                                              │
│                                                                              │
│    ┌─────────┐      ┌─────────┐      ┌─────────────────────┐                │
│    │  Admin  │      │ Person  │      │      people         │                │
│    │ People  │─────▶│ Schema  │─────▶│                     │                │
│    │  Page   │      │         │      │  name............✅ │                │
│    └─────────┘      │ ❌ GAPS │      │  type............✅ │                │
│                     │         │      │  pgy_level.......✅ │                │
│    Can edit:        │ Missing:│      │  faculty_role....✅ │                │
│    ✅ name          │         │      │                     │                │
│    ✅ email         │ • min_  │      │  min_clinic......✅ │◀── DB has it   │
│    ✅ type          │   clinic│      │  max_clinic......✅ │    but API     │
│    ✅ pgy_level     │ • max_  │      │  admin_type......✅ │    doesn't     │
│    ✅ faculty_role  │   clinic│      │  is_adjunct......✅ │    expose it   │
│                     │ • admin │      │                     │                │
│    ❌ min_clinic    │   _type │      └─────────────────────┘                │
│    ❌ max_clinic    │ • is_   │                                             │
│    ❌ admin_type    │   adjunct                                             │
│    ❌ is_adjunct    └─────────┘                                             │
│                                                                              │
│                                                                              │
│  ROTATIONS/TEMPLATES                                                         │
│  ───────────────────                                                         │
│                                                                              │
│    ┌─────────┐      ┌─────────┐      ┌─────────────────────┐                │
│    │  Admin  │      │Template │      │  rotation_templates │                │
│    │Rotations│─────▶│ Schema  │─────▶│                     │                │
│    │  Page   │      │         │      │  name............✅ │                │
│    └─────────┘      │ ✅ OK?  │      │  abbreviation....✅ │                │
│                     │         │      │  activity_type...✅ │                │
│    Can edit:        │ Verify: │      │  category........✅ │                │
│    ✅ name          │ • weekly│      └─────────────────────┘                │
│    ✅ abbreviation  │   pattern                                             │
│    ✅ activity_type │   writes│      ┌─────────────────────┐                │
│                     │ • half_ │      │  weekly_patterns    │                │
│    ❓ weekly_pattern│   day   │      │                     │                │
│    ❓ half_day_reqs │   writes│      │  (AM/PM patterns)   │                │
│                     └─────────┘      └─────────────────────┘                │
│                                                                              │
│                                                                              │
│  PRELOADS (FMIT, CALL, ABSENCES)                                            │
│  ───────────────────────────────                                            │
│                                                                              │
│    ┌─────────┐      ┌─────────┐      ┌─────────────────────┐                │
│    │  FMIT   │      │Preload  │      │  inpatient_preloads │                │
│    │ Import  │─────▶│ Schema  │─────▶│                     │                │
│    │  Page   │      │         │      │  person_id.......✅ │                │
│    └─────────┘      │ ❓CHECK │      │  rotation_type...✅ │                │
│                     │         │      │  start_date......✅ │                │
│    ┌─────────┐      │         │      │  end_date........✅ │                │
│    │ Faculty │      │         │      └─────────────────────┘                │
│    │  Call   │─────▶│         │                                             │
│    │  Page   │      │         │      ┌─────────────────────┐                │
│    └─────────┘      │         │      │  call_assignment    │                │
│                     │         │      │                     │                │
│                     └─────────┘      │  person_id.......✅ │                │
│                                      │  date.............✅│                │
│                                      │  call_type.......✅ │                │
│                                      └─────────────────────┘                │
│                                                                              │
│                                                                              │
│  HALF-DAY ASSIGNMENTS (THE OUTPUT)                                          │
│  ─────────────────────────────────                                          │
│                                                                              │
│    ┌─────────┐      ┌─────────┐      ┌─────────────────────┐                │
│    │Debugger │      │HalfDay  │      │ half_day_assignments│                │
│    │  Page   │─────▶│Assignment     │                     │                │
│    │         │      │ Schema  │─────▶│  person_id.......✅ │                │
│    └─────────┘      │         │      │  date.............✅│                │
│                     │ ✅ READ │      │  time_of_day.....✅ │                │
│    Can view:        │ ❓WRITE │      │  activity_id.....✅ │                │
│    ✅ assignments   │         │      │  source..........✅ │                │
│                     │         │      │                     │                │
│    ❌ manual edit   │         │      │  source values:     │                │
│    ❌ override slot │         │      │  • preload (locked) │                │
│                     └─────────┘      │  • manual (locked)  │                │
│                                      │  • solver           │                │
│                                      │  • template         │                │
│                                      └─────────────────────┘                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Activity Codes - The Rosetta Stone

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ACTIVITY CODES (activities table)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Every half_day_assignment has an activity_id pointing to this table.        │
│  This is how you audit what someone is assigned to do.                       │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ CODE     │ DISPLAY │ MEANING                    │ CATEGORY             │ │
│  ├──────────┼─────────┼────────────────────────────┼──────────────────────┤ │
│  │                    CLINICAL (patient care)                             │ │
│  ├──────────┼─────────┼────────────────────────────┼──────────────────────┤ │
│  │ fm_clinic│ C       │ FM Clinic (seeing patients)│ clinical             │ │
│  │ FMIT     │ FMIT    │ FM Inpatient Team          │ clinical             │ │
│  │ NF       │ NF      │ Night Float                │ clinical             │ │
│  │ call     │ CALL    │ On-call duty               │ clinical             │ │
│  │ KAP      │ KAP     │ Kapiolani L&D              │ clinical             │ │
│  │ IM       │ IM      │ Internal Medicine          │ clinical             │ │
│  │ PedW     │ PedW    │ Pediatrics Ward            │ clinical             │ │
│  │ PedNF    │ PedNF   │ Peds Night Float           │ clinical             │ │
│  │ LDNF     │ LDNF    │ L&D Night Float            │ clinical             │ │
│  ├──────────┼─────────┼────────────────────────────┼──────────────────────┤ │
│  │                    FACULTY SUPERVISION                                 │ │
│  ├──────────┼─────────┼────────────────────────────┼──────────────────────┤ │
│  │ at       │ AT      │ Attending Time (supervise) │ administrative       │ │
│  │ pcat     │ PCAT    │ Post-Call Attending Time   │ administrative       │ │
│  │ do       │ DO      │ Direct Observation         │ administrative       │ │
│  ├──────────┼─────────┼────────────────────────────┼──────────────────────┤ │
│  │                    ADMINISTRATIVE                                      │ │
│  ├──────────┼─────────┼────────────────────────────┼──────────────────────┤ │
│  │ gme      │ GME     │ Graduate Medical Education │ administrative       │ │
│  │ dfm      │ DFM     │ Dept Family Medicine       │ administrative       │ │
│  │ ADM      │ ADM     │ Admin time                 │ administrative       │ │
│  │ FLX      │ FLX     │ Flex time                  │ administrative       │ │
│  ├──────────┼─────────┼────────────────────────────┼──────────────────────┤ │
│  │                    TIME OFF                                            │ │
│  ├──────────┼─────────┼────────────────────────────┼──────────────────────┤ │
│  │ W        │ W       │ Weekend                    │ time_off             │ │
│  │ HOL      │ HOL     │ Holiday                    │ time_off             │ │
│  │ LV-AM    │ LV      │ Leave (morning)            │ time_off             │ │
│  │ LV-PM    │ LV      │ Leave (afternoon)          │ time_off             │ │
│  │ off      │ OFF     │ Day off (post-call)        │ time_off             │ │
│  │ DEP      │ DEP     │ Deployed                   │ administrative       │ │
│  │ TDY      │ TDY     │ Temporary Duty (Hilo etc)  │ clinical             │ │
│  ├──────────┼─────────┼────────────────────────────┼──────────────────────┤ │
│  │                    EDUCATIONAL                                         │ │
│  ├──────────┼─────────┼────────────────────────────┼──────────────────────┤ │
│  │ lec      │ LEC     │ Lecture (Wed PM)           │ educational          │ │
│  │ SIM      │ SIM     │ Simulation                 │ educational          │ │
│  │ MM       │ MM      │ M&M Conference             │ educational          │ │
│  │ CLC      │ CLC     │ Continuity Learning        │ educational          │ │
│  │ HAFP     │ HAFP    │ Hawaii AFP conference      │ educational          │ │
│  │ USAFP    │ USAFP   │ USAFP conference           │ educational          │ │
│  └──────────┴─────────┴────────────────────────────┴──────────────────────┘ │
│                                                                              │
│  ⚠️  CASE SENSITIVITY MATTERS!                                              │
│      gme ≠ GME  │  The code column uses what's shown above exactly.         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Source Priority - Who Wins?

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      ASSIGNMENT SOURCE PRIORITY                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  When multiple things try to assign the same slot, who wins?                 │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                     │    │
│  │   HIGHEST PRIORITY                                                  │    │
│  │   ════════════════                                                  │    │
│  │                                                                     │    │
│  │   ┌─────────────────────────────────────────────────────────────┐  │    │
│  │   │  1. PRELOAD  │  FMIT, call, absences, holidays              │  │    │
│  │   │              │  Created by: SyncPreloadService              │  │    │
│  │   │              │  LOCKED - solver CANNOT change               │  │    │
│  │   └─────────────────────────────────────────────────────────────┘  │    │
│  │                              │                                      │    │
│  │                              ▼                                      │    │
│  │   ┌─────────────────────────────────────────────────────────────┐  │    │
│  │   │  2. MANUAL   │  Human override via GUI (future)             │  │    │
│  │   │              │  Created by: Admin user                      │  │    │
│  │   │              │  LOCKED - solver CANNOT change               │  │    │
│  │   └─────────────────────────────────────────────────────────────┘  │    │
│  │                              │                                      │    │
│  │                              ▼                                      │    │
│  │   ┌─────────────────────────────────────────────────────────────┐  │    │
│  │   │  3. SOLVER   │  CP-SAT optimizer output                     │  │    │
│  │   │              │  Created by: CPSATActivitySolver             │  │    │
│  │   │              │  Can be overwritten by preload/manual        │  │    │
│  │   └─────────────────────────────────────────────────────────────┘  │    │
│  │                              │                                      │    │
│  │                              ▼                                      │    │
│  │   ┌─────────────────────────────────────────────────────────────┐  │    │
│  │   │  4. TEMPLATE │  Default fill (weekends=W, admin=GME/DFM)    │  │    │
│  │   │              │  Created by: FacultyAssignmentExpansionService│  │    │
│  │   │              │  LOWEST priority - anything can overwrite    │  │    │
│  │   └─────────────────────────────────────────────────────────────┘  │    │
│  │                                                                     │    │
│  │   LOWEST PRIORITY                                                   │    │
│  │                                                                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  AUDIT TIP: Query half_day_assignments and group by source to see           │
│             how many slots were filled by each method.                       │
│                                                                              │
│  SELECT source, COUNT(*) FROM half_day_assignments                          │
│  WHERE date BETWEEN '2026-03-12' AND '2026-04-08'                           │
│  GROUP BY source;                                                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Block 10 Specific Gaps

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    BLOCK 10 READINESS CHECKLIST                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  PRELOAD DATA NEEDED                                          STATUS        │
│  ───────────────────                                          ──────        │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                     │    │
│  │  □ inpatient_preloads populated                                     │    │
│  │    └─ FMIT: Chu (W1,W3), Bevis (W2), LaBounty (W4)                 │    │
│  │    └─ Residents: Petrie (R3), Cataquiz (R2)                        │    │
│  │    └─ NF, PedW, PedNF, KAP, IM, LDNF rotations                     │    │
│  │                                                                     │    │
│  │  □ call_assignment populated                                        │    │
│  │    └─ Faculty call distribution for Mar 12 - Apr 8                 │    │
│  │    └─ FMIT faculty auto-assigned Fri/Sat call                      │    │
│  │                                                                     │    │
│  │  □ absences populated                                               │    │
│  │    └─ All known leave, TDY, deployments                            │    │
│  │    └─ Connolly: Hilo TDY (entire block)                            │    │
│  │    └─ Colgan: DEP (deployed)                                       │    │
│  │    └─ Dahl: OUT (Dec-Jun)                                          │    │
│  │                                                                     │    │
│  │  □ holidays table populated (or computed)                           │    │
│  │    └─ Block 10 has NO federal holidays                             │    │
│  │                                                                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│                                                                              │
│  ACTIVITY CODES NEEDED                                        STATUS        │
│  ────────────────────                                         ──────        │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                     │    │
│  │  ✅ W, HOL, DEP exist (from 20260120_add_rot_activities)           │    │
│  │  ✅ FMIT, NF, PedW, etc exist (from 20260120_add_rot_activities)   │    │
│  │  ✅ gme, dfm exist (from 20260109_faculty_weekly)                  │    │
│  │  ⏳ LV-AM, LV-PM need migration (20260120_add_lv_activity)         │    │
│  │                                                                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│                                                                              │
│  FACULTY CONSTRAINTS                                          STATUS        │
│  ───────────────────                                          ──────        │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                     │    │
│  │  □ All faculty have correct min_clinic/max_clinic in DB            │    │
│  │  □ All faculty have correct admin_type (GME/DFM) in DB             │    │
│  │  □ Adjuncts marked correctly (Napierala, Van Brunt)                │    │
│  │                                                                     │    │
│  │  ⚠️  CAN'T EDIT VIA GUI - schema doesn't expose these fields!      │    │
│  │                                                                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│                                                                              │
│  ENGINE PIPELINE STATUS                                       STATUS        │
│  ──────────────────────                                       ──────        │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                     │    │
│  │  ✅ BlockAssignmentExpansionService (residents)                    │    │
│  │  ✅ SyncPreloadService (preloads)                                  │    │
│  │  ✅ FacultyAssignmentExpansionService (faculty gaps) - JUST FIXED  │    │
│  │  ⏳ CPSATActivitySolver (needs testing)                            │    │
│  │                                                                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. How to Audit Block 10 by Hand

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        MANUAL AUDIT QUERIES                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. CHECK: How many assignments exist for Block 10?                          │
│  ──────────────────────────────────────────────────                          │
│                                                                              │
│    SELECT source, COUNT(*)                                                   │
│    FROM half_day_assignments                                                 │
│    WHERE date BETWEEN '2026-03-12' AND '2026-04-08'                         │
│    GROUP BY source                                                           │
│    ORDER BY source;                                                          │
│                                                                              │
│    Expected: ~2000+ rows (20 people × 56 slots × 2 = 2240 potential)        │
│                                                                              │
│                                                                              │
│  2. CHECK: Faculty assignments by person                                     │
│  ──────────────────────────────────────────                                  │
│                                                                              │
│    SELECT p.name, a.code, COUNT(*)                                          │
│    FROM half_day_assignments h                                               │
│    JOIN people p ON h.person_id = p.id                                      │
│    JOIN activities a ON h.activity_id = a.id                                │
│    WHERE p.type = 'faculty'                                                  │
│      AND h.date BETWEEN '2026-03-12' AND '2026-04-08'                       │
│    GROUP BY p.name, a.code                                                   │
│    ORDER BY p.name, a.code;                                                  │
│                                                                              │
│    Look for: Each faculty should have 56 total slots                        │
│              Weekend slots should be 'W'                                     │
│              Non-weekend should be gme/dfm/at/pcat/do/FMIT                  │
│                                                                              │
│                                                                              │
│  3. CHECK: FMIT assignments match expected weeks                             │
│  ──────────────────────────────────────────────────                          │
│                                                                              │
│    SELECT p.name, h.date, h.time_of_day, a.code                             │
│    FROM half_day_assignments h                                               │
│    JOIN people p ON h.person_id = p.id                                      │
│    JOIN activities a ON h.activity_id = a.id                                │
│    WHERE a.code = 'FMIT'                                                     │
│      AND h.date BETWEEN '2026-03-12' AND '2026-04-08'                       │
│    ORDER BY h.date, p.name;                                                  │
│                                                                              │
│    Expected:                                                                 │
│    - Week 1 (Mar 13-19): Chu                                                │
│    - Week 2 (Mar 20-26): Bevis                                              │
│    - Week 3 (Mar 27-Apr 2): Chu                                             │
│    - Week 4 (Apr 3-9): LaBounty                                             │
│                                                                              │
│                                                                              │
│  4. CHECK: Preload sources are locked                                        │
│  ──────────────────────────────────────                                      │
│                                                                              │
│    SELECT p.name, h.date, h.time_of_day, a.code, h.source                   │
│    FROM half_day_assignments h                                               │
│    JOIN people p ON h.person_id = p.id                                      │
│    JOIN activities a ON h.activity_id = a.id                                │
│    WHERE h.source = 'preload'                                                │
│      AND h.date BETWEEN '2026-03-12' AND '2026-04-08'                       │
│    ORDER BY p.name, h.date;                                                  │
│                                                                              │
│    These should NOT change when solver runs.                                 │
│                                                                              │
│                                                                              │
│  5. CHECK: Missing slots (gaps in coverage)                                  │
│  ──────────────────────────────────────────                                  │
│                                                                              │
│    -- Generate expected slots, find missing                                  │
│    WITH expected AS (                                                        │
│      SELECT p.id as person_id, p.name,                                      │
│             d.date, t.time_of_day                                           │
│      FROM people p                                                           │
│      CROSS JOIN generate_series('2026-03-12'::date,                         │
│                                  '2026-04-08'::date,                         │
│                                  '1 day') as d(date)                        │
│      CROSS JOIN (VALUES ('AM'), ('PM')) as t(time_of_day)                   │
│      WHERE p.type = 'faculty' AND p.is_active = true                        │
│    )                                                                         │
│    SELECT e.name, e.date, e.time_of_day                                     │
│    FROM expected e                                                           │
│    LEFT JOIN half_day_assignments h                                          │
│      ON e.person_id = h.person_id                                           │
│      AND e.date = h.date                                                     │
│      AND e.time_of_day = h.time_of_day                                      │
│    WHERE h.id IS NULL;                                                       │
│                                                                              │
│    Expected: 0 rows (all slots should be filled)                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Gap Summary Table

| Gap | Layer | Impact | Fix Effort | Status |
|-----|-------|--------|------------|--------|
| Faculty constraints not in API | Backend Schema | Can't edit via GUI | Small | ❌ Open |
| LV-AM/LV-PM activities missing | Database | Absences won't preload | Small | ⏳ Migration ready |
| Manual override in GUI | Frontend | Can't lock slots via UI | Medium | ❌ Open |
| Constraint enable/disable | Backend + DB | Hardcoded in Python | Large | ❌ Future |
| Debugger read-only | Frontend | Can view but not edit | Medium | ❌ Open |

---

## 8. Next Steps for Block 10 Audit

1. **Run migration** `20260120_add_lv_activity.py` to add LV-AM/LV-PM
2. **Verify preload tables** have Block 10 data (FMIT, call, absences)
3. **Run schedule generation** for Block 10
4. **Execute audit queries** from Section 6 (DB is truth)
5. **Export** DB → XML → XLSX for MSA delivery

---

## 9. The Stealth Launch

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         STEALTH LAUNCH STRATEGY                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   The goal: MSAs receive an Excel file that looks exactly like what         │
│   they've always received. They don't know (or need to know) that it        │
│   came from a database-backed scheduling system.                            │
│                                                                              │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐            │
│   │          │    │          │    │          │    │          │            │
│   │ DATABASE │───▶│   XML    │───▶│   XLSX   │───▶│   MSAs   │            │
│   │ (truth)  │    │(transport│    │ (Excel)  │    │ (users)  │            │
│   │          │    │ format)  │    │          │    │          │            │
│   └──────────┘    └──────────┘    └──────────┘    └──────────┘            │
│                                                                              │
│   What changes:                                                              │
│   • Schedule is generated by CP-SAT solver, not manual Excel editing        │
│   • Constraints are enforced programmatically                               │
│   • ACGME compliance is validated automatically                             │
│   • Audit trail exists in the database                                      │
│                                                                              │
│   What stays the same:                                                       │
│   • MSAs get their familiar Excel format                                    │
│   • Column layout matches what they expect                                  │
│   • They can still print it, share it, mark it up                          │
│   • No training required                                                    │
│                                                                              │
│   Success = MSAs can't tell the difference.                                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

*Document created: 2026-01-20 | Session 123*
