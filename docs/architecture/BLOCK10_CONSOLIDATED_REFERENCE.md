# Block 10 Consolidated Reference

> **Block 10 Dates:** March 12 - April 8, 2026
> **Purpose:** Single source of truth for all activities, preloads, and constraints

---

## Activity Codes (Master Table)

All services MUST use codes from this table. No ad-hoc codes.

| Code | Display | Name | Category | Source Migration |
|------|---------|------|----------|------------------|
| **Clinical - Core** |
| `fm_clinic` | C | FM Clinic | clinical | 20260109_add_activities |
| `specialty` | S | Specialty | clinical | 20260109_add_activities |
| `inpatient` | INP | Inpatient | clinical | 20260109_add_activities |
| `call` | CALL | Call | clinical | 20260109_add_activities |
| `procedure` | PROC | Procedure | clinical | 20260109_add_activities |
| `elective` | ELEC | Elective | clinical | 20260109_add_activities |
| **Clinical - Inpatient Rotations** |
| `FMIT` | FMIT | FM Inpatient Team | clinical | 20260120_add_rot_activities |
| `NF` | NF | Night Float | clinical | 20260120_add_rot_activities |
| `PedW` | PedW | Pediatrics Ward | clinical | 20260120_add_rot_activities |
| `PedNF` | PedNF | Peds Night Float | clinical | 20260120_add_rot_activities |
| `KAP` | KAP | Kapiolani L&D | clinical | 20260120_add_rot_activities |
| `IM` | IM | Internal Medicine | clinical | 20260120_add_rot_activities |
| `LDNF` | LDNF | L&D Night Float | clinical | 20260120_add_rot_activities |
| `TDY` | TDY | Temporary Duty | clinical | 20260120_add_rot_activities |
| **Clinical - Specialty/Electives** |
| `NEURO` | NEURO | Neurology | clinical | 20260120_add_rot_activities |
| `US` | US | Ultrasound/POCUS | clinical | 20260120_add_rot_activities |
| `GYN` | GYN | Gynecology | clinical | 20260120_add_rot_activities |
| `SURG` | SURG | Surgery | clinical | 20260120_add_rot_activities |
| `PR` | PR | Procedures | clinical | 20260120_add_rot_activities |
| `VAS` | VAS | Vasectomy (procedure) | clinical | 20260120_add_rot_activities |
| `VASC` | VASC | Vasectomy Counseling | clinical | 202602XX_add_vasc |
| `HLC` | HLC | Houseless Clinic | clinical | 20260120_add_rot_activities |
| `C-N` | C-N | Night Float Clinic | clinical | 20260120_add_rot_activities |
| `CV` | CV | Virtual Clinic | clinical | 20260120_add_rot_activities |
| **Educational** |
| `lec` | LEC | Lecture | educational | 20260109_add_activities |
| `conference` | CONF | Conference | educational | 20260109_add_activities |
| `SIM` | SIM | Simulation | educational | 20260120_add_rot_activities |
| `PI` | PI | Process Improvement | educational | 20260120_add_rot_activities |
| `MM` | MM | M&M Conference | educational | 20260120_add_rot_activities |
| `CLC` | CLC | Continuity Learning | educational | 20260120_add_rot_activities |
| `HAFP` | HAFP | Hawaii AFP | educational | 20260120_add_rot_activities |
| `USAFP` | USAFP | USAFP Conference | educational | 20260120_add_rot_activities |
| `BLS` | BLS | BLS Training | educational | 20260120_add_rot_activities |
| **Time Off** |
| `off` | OFF | Day Off | time_off | 20260109_add_activities |
| `recovery` | REC | Recovery | time_off | 20260109_add_activities |
| `W` | W | Weekend | time_off | 20260120_add_rot_activities |
| `HOL` | HOL | Holiday | time_off | 20260120_add_rot_activities |
| `LV-AM` | LV | Leave AM | time_off | 20260120_add_lv_activity |
| `LV-PM` | LV | Leave PM | time_off | 20260120_add_lv_activity |
| **Administrative** |
| `gme` | GME | Graduate Medical Education | administrative | 20260109_faculty_weekly |
| `dfm` | DFM | Dept Family Medicine | administrative | 20260109_faculty_weekly |
| `at` | AT | Attending Time | administrative | 20260109_faculty_weekly |
| `pcat` | PCAT | Post-Call Attending Time | administrative | 20260109_faculty_weekly |
| `do` | DO | Direct Observation | administrative | 20260109_faculty_weekly |
| `sm_clinic` | SM | Sports Medicine Clinic | administrative | 20260109_faculty_weekly |
| `DEP` | DEP | Deployed | administrative | 20260120_add_rot_activities |
| `FLX` | FLX | Flex Time | administrative | 20260120_add_rot_activities |
| `ADM` | ADM | Admin | administrative | 20260120_add_rot_activities |

---

## Preload Sources (Execution Order)

Preloads are loaded in this order by `SyncPreloadService.load_all_preloads()`:

| # | Preload Type | Source Table | Activity Codes | Service Method |
|---|--------------|--------------|----------------|----------------|
| 1 | Absences | `absences` | `LV-AM`, `LV-PM` | `_load_absences()` |
| 2 | Inpatient Rotations | `inpatient_preloads` | `FMIT`, `NF`, `PedW`, `PedNF`, `KAP`, `IM`, `LDNF` | `_load_inpatient_preloads()` |
| 3 | FMIT Fri/Sat Call | `inpatient_preloads` | `call` | `_load_fmit_call()` |
| 4 | Inpatient Clinic (C-I) | `block_assignments` | `fm_clinic` | `_load_inpatient_clinic()` |
| 5 | Resident Call | `resident_call_preloads` | `call`, `off` (PC) | `_load_resident_call()` |
| 6 | Faculty Call | `call_assignment` | `call`, `pcat`, `do` | `_load_faculty_call()` |
| 7 | Sports Medicine | (faculty roles) | `sm_clinic` (aSM Wed AM) | `_load_sm_preloads()` |

### Preload Priority
All preloads have `source='preload'` which is LOCKED - solver cannot overwrite.

---

## Constraints (Enabled for Block 10)

### HARD Constraints (Must Not Violate)

| Constraint | Module | Description |
|------------|--------|-------------|
| 80-Hour Rule | `acgme.py` | Max 80 clinical hours/week |
| 1-in-7 Day Off | `acgme.py` | One day off every 7 days |
| Supervision Ratios | `acgme.py` | PGY1: 0.5 AT, PGY2/3: 0.25 AT |
| Availability | `acgme.py` | No double-booking |
| One Person Per Block | `capacity.py` | Person can't be in two places |
| Clinic Capacity | `capacity.py` | Max 6 in clinic per half-day |
| Wednesday AM Intern | `temporal.py` | PGY-1 continuity clinic Wed AM |
| Wednesday PM Faculty | `temporal.py` | Single faculty Wed PM (LEC) |
| Faculty Clinic Caps | `primary_duty.py` | min_c/max_c per week |
| FMIT Resident Headcount | `inpatient.py` | 1 per PGY level |
| Post-FMIT Recovery | `fmit.py` | Faculty PC Friday after FMIT |
| Post-FMIT Sunday Block | `fmit.py` | No faculty call Sunday after FMIT |
| Protected Slots | `protected_slot.py` | LEC, ADV immutable |
| Post-Call | `post_call.py` | PCAT (AM) + DO (PM) after call |

### SOFT Constraints (Optimized)

| Constraint | Module | Weight | Description |
|------------|--------|--------|-------------|
| Coverage | `capacity.py` | 1000.0 | All rotations filled |
| Sunday Call Equity | `call_equity.py` | 10.0 | Max 1 Sunday/faculty/block |
| Call Spacing | `call_equity.py` | 8.0 | Gap between calls |
| Weekday Call Equity | `call_equity.py` | 5.0 | Balanced distribution |
| Hub Protection | `resilience.py` | 15.0 | Protect key personnel |
| Utilization Buffer | `resilience.py` | 20.0 | Stay under 80% |
| Faculty Clinic Equity | `primary_duty.py` | 15.0 | Balance clinic loads |

---

## Faculty Weekly Caps (Block 10)

From `Person` model `min_clinic_halfdays_per_week` and `max_clinic_halfdays_per_week`
(**solver overrides min to 0 for all faculty to preserve AT capacity**):

| Faculty | min_c | max_c | admin_type | Notes |
|---------|-------|-------|------------|-------|
| Bevis | 0 | 0 | GME | APD, 100% admin |
| Kinkennon | 0 | 4 | GME | min overridden to 0 |
| LaBounty | 0 | 4 | GME | min overridden to 0 |
| McGuire | 0 | 1 | DFM | min overridden to 0 |
| McRae | 0 | 4 | GME | min overridden to 0 |
| Tagawa | 0 | 0 | GME | SM only, no personal C |
| Montgomery | 0 | 2 | GME | min overridden to 0 |
| Colgan | 0 | 0 | GME | DEP (deployed) |
| Chu | 0 | 4 | GME | min overridden to 0 |
| Napierala | 0 | 0 | GME | FMIT/Call only (adjunct) |
| Van Brunt | 0 | 0 | GME | FMIT/Call only (adjunct) |
| Lamoureux | 0 | 0 | GME | adjunct (manual only) |
| Dahl | 0 | 2 | GME | OUT Dec-Jun |

---

## Block 10 FMIT Schedule

| Week | Dates | Faculty | Residents |
|------|-------|---------|-----------|
| 1 | Mar 13-19 | Chu | Petrie (R3), Cataquiz (R2) |
| 2 | Mar 20-26 | Bevis | Petrie (R3), Cataquiz (R2) |
| 3 | Mar 27-Apr 2 | Chu | Petrie (R3), Cataquiz (R2) |
| 4 | Apr 3-9 | LaBounty | Petrie (R3), Cataquiz (R2) |

## Procedure Templates (Non‑Rotation)
- **BTX/COLPO/VAS/PROC‑AM/PR‑PM** templates are **archived** (not rotations).
- Procedures are handled as **activities** within **PROC/FMC/POCUS** rotations and
  faculty weekly templates.
- **POCUS** is a rotation (US + C mix), not a procedure template.

---

## Engine Pipeline (Order of Operations)

```
engine.py generate_schedule():
│
├─ Step 1.5h: Block Assignment Expansion (residents)
│   └─ BlockAssignmentExpansionService
│
├─ Step 1.5h.3: Sync Preloads
│   └─ SyncPreloadService.load_all_preloads()
│       ├─ Absences → LV-AM/LV-PM
│       ├─ Inpatient → FMIT/NF/etc
│       ├─ FMIT Call → call
│       ├─ C-I Clinic → fm_clinic
│       ├─ Resident Call → call/off
│       ├─ Faculty Call → call/pcat/do
│       └─ SM → sm_clinic
│
├─ Step 1.5h.5: Faculty Expansion ← NEW
│   └─ FacultyAssignmentExpansionService.fill_faculty_assignments()
│       ├─ Weekend → W
│       ├─ Holiday → HOL
│       ├─ Absence → LV-AM/LV-PM
│       ├─ Deployed → DEP
│       └─ Default → gme/dfm
│
├─ Step 4: Activity Solver
│   └─ CPSATActivitySolver.solve()
│
└─ Step 7: Faculty Supervision (skipped in half-day mode)
```

---

## Validation Checklist

Before running schedule generation:

- [ ] All activity codes from this table exist in `activities` table
- [ ] `inpatient_preloads` populated for Block 10 FMIT/NF rotations
- [ ] `call_assignment` table has faculty call assignments
- [ ] `absences` table has leave/absence records
- [ ] `people` table has correct `admin_type` (GME/DFM) for faculty
- [ ] `people` table has correct `min_clinic_halfdays_per_week` / `max_clinic_halfdays_per_week`

---

*Generated: 2026-01-20 | Session 123*
