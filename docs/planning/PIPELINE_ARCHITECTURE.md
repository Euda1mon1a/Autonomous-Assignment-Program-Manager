# Schedule ↔ Excel Pipeline Architecture

> Generated 2026-03-11 · `fix/combined-vs-split-rotations` branch

---

## Current State (What Works Today)

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                         SCHEDULE GENERATION                              ║
╚═══════════════════════════════════════════════════════════════════════════╝

    block_assignments              rotation_templates
    (resident → rotation           (FMIT, NF, DERM/NF,
     per block)                     MED, etc.)
          │                              │
          └──────────┬───────────────────┘
                     ▼
         ┌───────────────────────┐
         │  SchedulingEngine     │  POST /api/v1/schedule/generate
         │  .generate()          │
         └───────────┬───────────┘
                     │
     ┌───────────────┼───────────────────┐
     ▼               ▼                   ▼
 ┌────────┐   ┌────────────┐    ┌──────────────┐
 │Preloads│   │  CP-SAT    │    │  Context     │
 │Service │   │  Solver    │    │  Builder     │
 │        │   │            │    │              │
 │10 cats:│   │Optimize:   │    │Availability, │
 │LV, FMIT│   │• rotations │    │constraints,  │
 │NF, C-I │   │• call eq.  │    │faculty,      │
 │CALL,PC │   │• coverage  │    │residents     │
 │LEC,SIM │   │• fairness  │    │              │
 │PCAT,DO │   └──────┬─────┘    └──────────────┘
 │HAFP,PI │          │
 └───┬────┘          │
     │               │
     └───────┬───────┘
             ▼
   ┌──────────────────────┐
   │  Assignment Table     │  1 row per person per block
   │  (person × block ×    │  (same rotation_template for
   │   rotation_template)  │   all 56 half-day slots)
   └──────────┬───────────┘
              │
              ▼
   ┌──────────────────────┐
   │  Activity Solver      │  Resolves per-half-day activity
   │                       │  DERM/NF → "DERM" Mon-Thu,
   │                       │            "NF" Fri-Sun
   └──────────┬───────────┘
              │
              ▼
   ┌──────────────────────┐
   │  half_day_assignments │  ★ DESCRIPTIVE TRUTH ★
   │  (person × date ×     │  ~1000 rows per block
   │   AM/PM × activity)   │  (18 people × 28 days × 2)
   └──────────────────────┘


╔═══════════════════════════════════════════════════════════════════════════╗
║                         EXCEL EXPORT                                     ║
╚═══════════════════════════════════════════════════════════════════════════╝

   half_day_assignments ──────────────────────────────────┐
              │                                           │
              ▼                                           │
   ┌──────────────────────┐                               │
   │ HalfDayJSONExporter   │  DB → intermediate JSON      │
   │ .export()             │                               │
   └──────────┬───────────┘                               │
              │                                           │
              ▼                                           │
   ┌─ JSON Dict ──────────────────────────┐               │
   │ { block_start, block_end,            │               │
   │   residents: [{                      │               │
   │     id: "uuid",                      │               │
   │     name: "Smith",                   │               │
   │     rotation1: "DERM/NF",            │               │
   │     days: [                          │               │
   │       {date, am:"DERM", pm:"DERM"}, │               │
   │       {date, am:"NF",   pm:"NF"}    │               │
   │     ]                                │               │
   │   }],                                │               │
   │   faculty: [...],                    │               │
   │   call: {...}                        │               │
   │ }                                    │               │
   └──────────┬───────────────────────────┘               │
              │                                           │
              ▼                                           │
   ┌──────────────────────────────────────────────┐       │
   │  TAMCBlockExporter.export()                   │       │
   │                                               │       │
   │  Phase 1: Structure ✅                        │       │
   │    Workbook, dims, freeze panes, fonts        │       │
   │                                               │       │
   │  Phase 2: Formatting ✅                       │       │
   │    TAMC color scheme, rotation colors,        │       │
   │    black bars, header cells                   │       │
   │                                               │       │
   │  Phase 3: Data Injection ✅                   │       │
   │    Names, rotation codes, activity codes      │       │
   │                                               │       │
   │  Phase 4: Enrichment                          │       │
   │    4a: Conditional Formatting ✅              │       │
   │    4b: Leave-Day Formula Column ✅            │       │
   │    4c: Provenance Comments ⏳ (pending)       │       │
   │    4d: Schedule Diff Guard ✅ (20% max)       │       │
   └──────────┬───────────────────────────────────┘       │
              │                                           │
              ▼                                           │
   ┌── XLSX Workbook ─────────────────────────────┐       │
   │                                               │       │
   │  Visible: "Block 13"                          │       │
   │  ┌─────────────────────────────────────────┐ │       │
   │  │ Name  Rot1  Rot2  Thu  Fri  Sat  Sun ...│ │       │
   │  │ Smith DERM/NF  -  DERM DERM  NF   NF  ...│ │       │
   │  │ Jones FMIT     -  FMIT FMIT FMIT FMIT ...│ │       │
   │  │ ...   ...      -  ...  ...  ...   ...  ...│ │       │
   │  └─────────────────────────────────────────┘ │       │
   │                                               │       │
   │  Hidden sheets:                               │       │
   │  ├─ __SYS_META__  (AY, block#, timestamp) ✅│       │
   │  ├─ __ANCHORS__   (UUIDs, row hashes)     ✅│       │
   │  ├─ __REF__       (valid rotation/activity │       │
   │  │                 named ranges)           ✅│       │
   │  ├─ __BASELINE__  (cell fingerprints)     ✅│       │
   │  └─ __OVERRIDES__ (manual edits)          ⏳│       │
   └──────────┬───────────────────────────────────┘       │
              │                                           │
              ▼                                           │
        ┌───────────┐                                     │
        │ Download  │  GET /api/v1/export/schedule/xlsx   │
        │ .xlsx     │  or POST /admin/block-assignments/  │
        │           │       export-block-format           │
        └───────────┘                                     │


╔═══════════════════════════════════════════════════════════════════════════╗
║                         EXCEL IMPORT (Round-Trip)                         ║
╚═══════════════════════════════════════════════════════════════════════════╝

   Coordinator edits .xlsx
   (changes activities, fixes
    leave days, adjusts coverage)
              │
              ▼
   ┌──────────────────────────────────────────────┐
   │  HalfDayImportService.stage_import()          │
   │                                               │
   │  1. Read __SYS_META__                         │
   │     → Validate block# + AY match ✅          │
   │     → Reject wrong-block file                 │
   │                                               │
   │  2. Read __ANCHORS__                          │
   │     → Map rows → person_id by UUID ✅        │
   │     → Hash unchanged rows → skip (O(1)) ✅   │
   │     → Fuzzy name fallback for legacy files    │
   │                                               │
   │  3. Parse Excel Rows                          │
   │     → Extract activity codes per cell         │
   │     → Match rotation templates                │
   │                                               │
   │  4. Compute Diffs                             │
   │     → Compare vs existing half_day_assignments│
   │     → Classify: add / modify / remove         │
   └──────────┬───────────────────────────────────┘
              │
              ▼
   ┌──────────────────────────────────────────────┐
   │  ImportStagingService                         │
   │                                               │
   │  import_batch (metadata)                      │
   │  import_staged_assignment (per-cell diffs)    │
   │                                               │
   │  ┌─────────────────────────────────────────┐ │
   │  │ Person    Date    Time  Old   New  Type │ │
   │  │ Smith     03/15   AM    DERM  LV   MOD  │ │
   │  │ Smith     03/15   PM    DERM  LV   MOD  │ │
   │  │ Jones     03/20   AM    -     SIM  ADD  │ │
   │  └─────────────────────────────────────────┘ │
   │                                               │
   │  Preview → Coordinator reviews diffs          │
   │  Apply   → Upsert to half_day_assignments     │
   │  Reject  → Discard batch                      │
   │  Rollback → Undo within 24h window            │
   └──────────┬───────────────────────────────────┘
              │
              ▼
   ┌──────────────────────┐
   │  half_day_assignments │  Updated descriptive truth
   │  is_override = True   │  source = "import"
   │  source = "import"    │
   └──────────────────────┘


╔═══════════════════════════════════════════════════════════════════════════╗
║               COMBINED ROTATION HANDLING (NF Split Resolution)           ║
╚═══════════════════════════════════════════════════════════════════════════╝

   Legacy Excel (2-column)          Current DB (1-column)
   ┌──────┬──────┐                  ┌────────────┐
   │Rot 1 │Rot 2 │
   │ DERM │  NF  │
   │ ENDO │  NF  │
   │ FMIT │  NF  │
   └──┬───┴──┬───┘
      │      │
      ▼      ▼
   Two block_assignment rows
   with block_half=1 and block_half=2:
      │
      ├── block_half=1: rotation_template → DERM
      └── block_half=2: rotation_template → NF
                     │
                     ▼
            Activity Solver / Preloads
            resolve per block_half row:
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
    Week 1-2: DERM          Week 3-4: NF
    (AM: DERM, PM: DERM)    (AM: OFF, PM: NF)
```

---

## Future State (When Complete)

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                    FULL PIPELINE — FUTURE VISION                         ║
╚═══════════════════════════════════════════════════════════════════════════╝


                    ┌──────────────────────┐
                    │  Annual Rotation     │  Track E (ARO)
                    │  Optimizer (ARO)     │  CP-SAT: assign
                    │                      │  rotations to blocks
                    │  Input: Residents,   │  for entire AY
                    │    rotation reqs,    │
                    │    leave requests    │  ★ BACKEND WIRED ★
                    │                      │  ★ FRONTEND TBD  ★
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  block_assignments   │  (pre-populated by
                    │  (full AY: 13 blocks │   ARO or manual entry)
                    │   × ~18 residents)   │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
        ┌──────────┐  ┌──────────────┐  ┌──────────────┐
        │ Preloads  │  │  CP-SAT      │  │  PGY Rollover│ Track A
        │ (10 cats) │  │  Main Solver │  │              │ July 2026
        │           │  │              │  │Person        │
        │ ★ NEW:    │  │              │  │AcademicYear  │
        │ Leave SSoT│  │              │  │model: scope  │
        │ (Track C) │  │              │  │PGY by year,  │
        │ absences  │  │              │  │reset call    │
        │ as single │  │              │  │counts on     │
        │ source    │  │              │  │July 1        │
        └────┬─────┘  └──────┬───────┘  └──────┬───────┘
             │               │                  │
             └───────┬───────┘                  │
                     │  ◄───────────────────────┘
                     ▼
           ┌──────────────────────┐
           │  half_day_assignments │  ★ DESCRIPTIVE TRUTH ★
           └──────────┬───────────┘
                      │
        ┌─────────────┼──────────────────┐
        │             │                  │
        ▼             ▼                  ▼
   ┌─────────┐  ┌──────────┐    ┌──────────────┐
   │  XLSX   │  │  ACGME   │    │  Dashboard   │
   │  Export │  │  Validate│    │  (Next.js)   │
   │         │  │          │    │              │
   │ Phases  │  │ 80-hr    │    │ Coverage     │
   │ 1-4     │  │ 1-in-7   │    │ Calendar     │
   │ ✅✅✅ │  │ Superv.  │    │ Swap Mgmt    │
   │ Phase4c │  │ Ratios   │    │ Reports      │
   │ ⏳      │  │          │    │              │
   └────┬────┘  └──────────┘    └──────────────┘
        │
        ▼
   ┌─────────────────────────────────────────────────┐
   │              STATEFUL ROUND-TRIP                 │
   │                                                  │
   │  Export → Coordinator Edits → Re-Import          │
   │                                                  │
   │  ┌─────────┐    ┌─────────┐    ┌─────────┐     │
   │  │  XLSX   │───▶│  Human  │───▶│  XLSX   │     │
   │  │  (with  │    │  Edits  │    │  (with  │     │
   │  │  meta,  │    │         │    │  edits) │     │
   │  │  anchors│    │ • Fix   │    │         │     │
   │  │  valid.)│    │   leave │    │         │     │
   │  │         │    │ • Swap  │    │         │     │
   │  │         │    │   slots │    │         │     │
   │  │         │    │ • Adj.  │    │         │     │
   │  │         │    │   cover │    │         │     │
   │  └─────────┘    └─────────┘    └────┬────┘     │
   │                                     │           │
   │                                     ▼           │
   │                     ┌───────────────────────┐   │
   │                     │  Import Service        │   │
   │                     │                        │   │
   │                     │  1. Metadata gate      │   │
   │                     │     (block/AY match)   │   │
   │                     │                        │   │
   │                     │  2. UUID anchoring     │   │
   │                     │     (no fuzzy needed)  │   │
   │                     │                        │   │
   │                     │  3. Diff detection     │   │
   │                     │     (hash skip O(1))   │   │
   │                     │                        │   │
   │                     │  4. ACGME validation   │   │
   │                     │     (reject violations)│   │
   │                     │                        │   │
   │                     │  5. Diff guard         │   │
   │                     │     (>20% = warning)   │   │
   │                     │                        │   │
   │                     │  6. Stage → Preview    │   │
   │                     │     → Apply/Reject     │   │
   │                     │                        │   │
   │                     │  ★ Phase 4c:           │   │
   │                     │  Provenance comments   │   │
   │                     │  on overridden cells   │   │
   │                     │  (audit trail)     ⏳  │   │
   │                     └───────────┬───────────┘   │
   │                                 │               │
   │                                 ▼               │
   │                     half_day_assignments         │
   │                     (is_override=True,           │
   │                      source="import")            │
   └─────────────────────────────────────────────────┘
```

---

## Completion Checklist

```
EXPORT PIPELINE
═══════════════
  ✅  Schedule generation (CP-SAT solver)
  ✅  Preload service (10 categories)
  ✅  Activity solver (per-half-day resolution)
  ✅  HalfDayJSONExporter (DB → JSON)
  ✅  TAMCBlockExporter Phases 1-4b
  ✅  Hidden metadata sheet (__SYS_META__)
  ✅  UUID anchoring (__ANCHORS__)
  ✅  Data validation dropdowns (__REF__)
  ✅  Conditional formatting (Phase 4a)
  ✅  Leave-day formula column (Phase 4b)
  ✅  Schedule diff guard — 20% max (Phase 4d)
  ⏳  Provenance comments on overrides (Phase 4c)

IMPORT PIPELINE (ROUND-TRIP)
════════════════════════════
  ✅  Metadata validation (block/AY gate)
  ✅  UUID identity anchoring
  ✅  Row hash skip (O(1) unchanged detection)
  ✅  Fuzzy name fallback (legacy files)
  ✅  Diff staging (ImportBatch/ImportStagedAssignment)
  ✅  Preview before apply
  ✅  Apply/Reject/Rollback workflow
  ⏳  ACGME validation on import (pre-apply check)

COMBINED ROTATION CANONICALIZATION
══════════════════════════════════
  ✅  8 canonical X/NF templates in DB (migration)
  ✅  Legacy split mapper (2-col → 1-col)
  ✅  FMIT-NF-PG in preload constants
  ✅  Leave-ineligible block scoping
  ✅  Activity solver bugfix (slot dict)
  ✅  64 mapper tests + 10 preload tests
  ⚠️  Branch not yet merged (needs PR)

FUTURE TRACKS
═════════════
  ⏳  Track A: PGY Graduation Rollover (July 2026)
       PersonAcademicYear model, call count reset
  ⏳  Track C: Leave Single-Source-of-Truth
       Absence CRUD → auto preload refresh
  ✅  Track E: ARO Backend (CP-SAT solver + API)
  ⏳  Track E: ARO Frontend (UI for annual planning)
```

---

## Key Tables

```
                    ┌─────────────────────┐
                    │  rotation_templates  │ ~70 rows
                    │  (FMIT, NF, DERM/NF │ canonical definitions
                    │   MED, C, AT, etc.) │
                    └────────┬────────────┘
                             │
        ┌────────────────────┼──────────────────────┐
        │                    │                      │
        ▼                    ▼                      ▼
 ┌──────────────┐  ┌──────────────────┐  ┌──────────────────┐
 │block_         │  │ assignment       │  │ half_day_        │
 │assignments    │  │                  │  │ assignments      │
 │               │  │ person_id        │  │                  │
 │ resident_id   │  │ block_id         │  │ person_id        │
 │ rotation_     │  │ rotation_        │  │ block_id         │
 │  template_id  │  │  template_id     │  │ date             │
 │ block_number  │  │                  │  │ time_of_day      │
 │ academic_year │  │ 1 row per person │  │ activity_id      │
 │ leave_eligible│  │ per block        │  │ source           │
 │               │  │                  │  │ is_override      │
 │ ~18 per block │  │ ~18 per block    │  │ ~1000 per block  │
 └──────────────┘  └──────────────────┘  └──────────────────┘
       INPUT            SOLVER OUTPUT        DESCRIPTIVE TRUTH
   (what rotations     (who got what)       (what happens each
    are assigned)                             half-day)
```
