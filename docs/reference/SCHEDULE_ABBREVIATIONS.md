# Schedule Abbreviations Reference

> **Last Updated:** 2025-12-26
> **Source:** Domain expert input, Excel schedule analysis

This document defines all abbreviations used in the residency schedule spreadsheets.

---

## Clinic Types

| Code | Full Name | Description | Location |
|------|-----------|-------------|----------|
| **C** | Clinic | Standard family medicine clinic appointment | On-site |
| **CC** | Continuity Clinic | Residents book their own patients for PCP continuity (military-specific challenge) | On-site |
| **CLC** | Nursing Home Clinic | Residents spend half-day at nursing home | Off-site |
| **C-I** | PGY-3 FMIT Clinic | Shielded from central scheduling; for discharge follow-up patients | On-site |
| **C30** | FM Clinic 30-min | 30-minute appointments; used for interns or pre-Night Float | On-site |
| **CV** | Clinic Virtual | Virtual/telehealth visits (think of "v" as subscript) | Remote |

## Specialty Clinics

| Code | Full Name | Description | Location |
|------|-----------|-------------|----------|
| **WICS** | Walk-In Contraceptive Services | Walk-in prescriptions and procedures for contraception | Off-site |
| **HC** | Houseless Clinic | Clinic at homeless shelter in Honolulu | Off-site (shelter) |
| **HV** | Home Visit | Home visits with psychologist; ACGME requirement | Off-site |
| **VAS** | Vasectomy Procedure Clinic | Vasectomy procedures performed in FM clinic | On-site |
| **VasC** | Vasectomy Counseling | Group visit covering risks/benefits, permanence | On-site |

## Video Review Clinics

| Code | Full Name | Description |
|------|-----------|-------------|
| **V1** | Video Clinic PGY-1 | Intern records patient interaction for self-review with psychologist |
| **V2** | Video Clinic PGY-2 | Second-year version |
| **V3** | Video Clinic PGY-3 | Third-year version; uses non-networked camcorder |

*Note: These are distinct from CV (virtual clinic). Video clinics are for self-assessment, not telehealth.*

## Teaching/Administrative

| Code | Full Name | Description |
|------|-----------|-------------|
| **FMIT** | Family Medicine Inpatient Team | Inpatient teaching rotation |
| **SIM** | Simulation | Simulation training |
| **LEC** | Lecture | Didactic session |
| **ADM** | Administrative | Admin time |
| **PR** | Procedures | Procedure clinic/training |
| **PI** | Process Improvement | Clinic meeting (historic abbreviation); OIC leads, includes civilian staff |
| **GME** | Graduate Medical Education | GME-related activities |
| **RSH** | Research | Research time; often used as elective for free time, some are productive |
| **FLX** | Flex Time | Unscheduled time; ideally spent with clinical pharmacist (diabetes expert) |

## Rotations

| Code | Full Name | Notes |
|------|-----------|-------|
| **NF** | Night Float | Night shift coverage |
| **NICU** | NICU | Neonatal ICU rotation |
| **ER** | Emergency Room | ED rotation |
| **IMW** | Internal Medicine Ward | IM inpatient |
| **PedW** | Peds Ward | Pediatric inpatient |
| **PedC** | Peds Clinic | Pediatric outpatient |
| **PedSP** | Peds Subspecialty | Pediatric specialty rotation |
| **Ophtho/Optho** | Ophthalmology | Eye clinic |
| **URO/Uro** | Urology | Urology rotation |
| **ENT** | ENT | Ear/Nose/Throat |

## Military-Specific

| Code | Full Name | Description |
|------|-----------|-------------|
| **MUC** | Military Unique Curriculum | Last rotation before graduating; crash course in Army medicine |
| **C4** | Combat Casualty Care Course | TDY required for HPSP graduates; USU grads do Operation Bushmaster instead |
| **TDY** | Temporary Duty | Military temporary assignment |
| **FED** | Federal Holiday | Federal holiday |

## Leave/Time Off

| Code | Full Name |
|------|-----------|
| **W** | Weekend |
| **OFF** | Day Off |
| **HOL** | Holiday |
| **LV** | Leave |
| **PC** | Post-Call | Day after call shift |

## Pre-Kapiolani Requirements

| Code | Full Name | Timing | Notes |
|------|-----------|--------|-------|
| **EPIC** | Epic EMR Training | Wednesday AM, block before Kapiolani | Required |
| **STRAUB** | Health Visit | Wednesday PM, block before Kapiolani | Required |

*EPIC and STRAUB preferred same Wednesday but not mandatory.*

## External Sites

| Code | Full Name | Description |
|------|-----------|-------------|
| **KAP** | Kapiolani | Kapiolani Medical Center rotation |
| **STRAUB** | Straub Hospital | Straub Medical Center |

## Faculty/Role Codes

| Code | Meaning |
|------|---------|
| **FAC** | Faculty |
| **OIC** | Officer in Charge |
| **FACDEV** | Faculty Development |

---

## Parsing Notes

### Column Structure (Block 9 Sheet)
- Columns come in AM/PM pairs
- Column 0: Template/rotation name
- Column 2: Role code (R1, R2, R3)
- Column 3: PGY level
- Column 4: Resident name
- Columns 5+: Daily assignments (odd=AM, even=PM)

### Row Structure
- Row 0-1: Day name headers
- Row 2: Dates
- Row 3: Staff call (faculty on call)
- Row 4: Resident call / special notes
- Rows 8+: Individual schedules

### Color Coding
(To be documented after visual analysis)

---

## Import Mapping

For database import, map abbreviations to rotation templates:

```python
ABBREV_TO_TEMPLATE = {
    # Clinic types
    "C": "fm_clinic",
    "CC": "continuity_clinic",
    "CLC": "nursing_home",
    "C-I": "fmit_clinic_pgy3",
    "C30": "fm_clinic_30min",
    "CV": "clinic_virtual",

    # Specialty
    "WICS": "contraceptive_services",
    "HC": "houseless_clinic",
    "HV": "home_visit",
    "VAS": "vasectomy_procedure",
    "VasC": "vasectomy_counseling",

    # Video
    "V1": "video_clinic_pgy1",
    "V2": "video_clinic_pgy2",
    "V3": "video_clinic_pgy3",

    # Teaching
    "FMIT": "fmit",
    "SIM": "simulation",
    "LEC": "lecture",
    "ADM": "administrative",
    "PR": "procedures",
    "PI": "process_improvement",
    "RSH": "research",
    "FLX": "flex_time",

    # Rotations
    "NF": "night_float",
    "NICU": "nicu",
    "ER": "emergency",
    "IMW": "internal_medicine_ward",
    "PedW": "peds_ward",
    "PedC": "peds_clinic",
    "PedSP": "peds_subspecialty",

    # Leave/Off
    "W": "weekend",
    "OFF": "day_off",
    "HOL": "holiday",
    "FED": "federal_holiday",
    "LV": "leave",
    "PC": "post_call",
    "TDY": "tdy",

    # Military
    "MUC": "military_unique",
    "C4": "combat_casualty_care",

    # Pre-Kap
    "EPIC": "epic_training",
    "STRAUB": "straub_health_visit",
}
```

---

*This document is essential for parsing schedule spreadsheets. Update when new abbreviations are discovered.*
