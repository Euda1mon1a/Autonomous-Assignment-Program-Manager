# Rotation Templates Reference

This document describes the rotation templates used in the residency scheduling system.

## Overview

Rotation templates define the types of clinical rotations, educational activities, and administrative time blocks that residents can be assigned to. Each template has:

- **Name**: Full descriptive name
- **Abbreviation**: Short code used in the system
- **Display Abbreviation**: What appears on schedules
- **Rotation Type**: Category (`rotation_type`: inpatient, outpatient, procedures, education, off, absence, recovery)

## Rotation Types

| Type | Description |
|------|-------------|
| `inpatient` | Hospital-based rotations requiring 24/7 coverage |
| `outpatient` | Clinic-based rotations during business hours |
| `procedures` | Procedural training (Botox, vasectomy, colposcopy) |
| `education` | Lectures, GME activities, orientation |
| `off` | Off-site rotations (Hilo, Kapiolani, Okinawa) |
| `absence` | Leave, weekends |
| `recovery` | Post-call recovery time |

## Current Rotation Templates

### Inpatient Rotations

| Abbreviation | Display | Name | Notes |
|--------------|---------|------|-------|
| FMI | FMIT | Family Medicine Inpatient Team Intern | PGY1 |
| FMIT-R | FMIT | Family Medicine Inpatient Team Resident | PGY2/3 |
| FMIT-PA | FMIT | Family Medicine Inpatient Team Pre-Attending | Senior |
| FMIT-AM | FMIT | FMIT AM | Morning block |
| FMIT-PM | FMIT | FMIT PM | Evening block |
| NF-AM | NF | Night Float AM | |
| NF-PM | NF | Night Float PM | |
| NFI | NF-I | Night Float Intern + FMIT | Combined |
| NF+ | NF+ | Night Float + Cardiology | Half-block |
| NF-DERM | NF-DERM | Night Float + Dermatology | Half-block |
| NF-MED | NF-MED | Night Float + Medical Selective | Half-block |
| NF-NICU | NF-NICU | Night Float + NICU | Half-block |
| C+N | CARD+NF | Cardiology + Night Float | Half-block |
| D+N | DERM+NF | Dermatology + Night Float | Half-block |
| NIC | NICU+NF | NICU + Night Float | Half-block |
| ICU | ICU | Intensive Care Unit Intern | |
| IM-INT | IMW | Internal Medicine Intern | |
| LAD | LND | Labor and Delivery Intern | |
| LDNF | LDNF | Labor and Delivery Night Float | |
| NBN | NBN | Newborn Nursery | |
| NICU | NICU | NICU | |
| PEDS-W | PEDSW | Pediatrics Ward Intern | |
| PNF | PNF | Pediatrics Night Float Intern | |

### Outpatient Rotations

| Abbreviation | Display | Name | Notes |
|--------------|---------|------|-------|
| C-AM | C | Clinic AM | Generic clinic |
| C-PM | C | Clinic PM | Generic clinic |
| SM-AM | SM | Sports Medicine AM | |
| SM-PM | SM | Sports Medicine PM | |
| ACS-AM | ACS | Academic Sports Medicine AM | |
| DFM-AM | DFM | Department of Family Medicine AM | |
| DFM-PM | DFM | Department of Family Medicine PM | |
| HC-AM | HC | Houseless Clinic AM | |
| HC-PM | HC | Houseless Clinic PM | |
| PCAT-AM | PCAT | PCAT AM | |
| AT-AM | AT | Resident Supervision AM | Attending supervision |
| AT-PM | AT | Resident Supervision PM | Attending supervision |
| ADV-PM | ADV | Advising PM | |
| DO-PM | DO | Direct Observation PM | |
| COLP-AM | COLP | Colposcopy AM | |
| COLP-PM | COLP | Colposcopy PM | |

### Procedures

| Abbreviation | Display | Name |
|--------------|---------|------|
| PR-AM | PR | Procedure AM |
| PR-PM | PR | Procedure PM |
| BTX-AM | BTX | Botox AM |
| BTX-PM | BTX | Botox PM |
| VAS-AM | VAS | Vasectomy AM |
| VAS-PM | VAS | Vasectomy PM |

### Education

| Abbreviation | Display | Name |
|--------------|---------|------|
| LEC-AM | LEC | Lecture AM |
| LEC-PM | LEC | Lecture PM |
| GME-AM | GME | Graduate Medical Education AM |
| GME-PM | GME | Graduate Medical Education PM |
| FMO | FMO | Family Medicine Orientation |

### Off-Site Rotations

| Abbreviation | Display | Name | Location |
|--------------|---------|------|----------|
| HILO | HILO | Hilo | Big Island rural rotation |
| KAPI | KAP | Kapiolani | Kapiolani Medical Center |
| OKI | OKI | Okinawa | Okinawa, Japan |

### Absence/Recovery

| Abbreviation | Display | Name |
|--------------|---------|------|
| LV-AM | LV | Leave AM |
| LV-PM | LV | Leave PM |
| W-AM | W | Weekend AM |
| W-PM | W | Weekend PM |
| OFF-AM | OFF | OFF AM |
| OFF-PM | OFF | OFF PM |
| PC | PC | Post-Call Recovery |

## Common Abbreviation Mappings

When importing schedule data, these abbreviations may be used:

| Schedule Abbrev | Maps To | Template |
|-----------------|---------|----------|
| FMC | C-AM/C-PM or new | Family Medicine Clinic |
| FMIT | FMI/FMIT-R | Based on PGY level |
| FMIT 2 | FMIT-R | Second FMIT resident |
| SM | SM-AM/SM-PM | Sports Medicine |
| L&D NF | LDNF | Labor & Delivery Night Float |
| Peds Ward | PEDS-W | Pediatrics Ward |
| Peds NF | PNF | Pediatrics Night Float |
| PROC | PR-AM/PR-PM | Procedures |
| IM | IM-INT | Internal Medicine |
| NF/MS:Endo | Half-block | NF first half + Endo selective |
| NEURO/NF | Half-block | Neurology first half + NF |
| Kapi L&D | New template | Kapiolani L&D (off-site) |

## Recently Added Templates (Session 073)

| Abbreviation | Display | Name | Type |
|--------------|---------|------|------|
| FMC | FMC | Family Medicine Clinic | outpatient |
| POCUS | POCUS | Point of Care Ultrasound | procedures |
| SURG-EXP | SURG | Surgical Experience | outpatient |
| GYN-CLIN | GYN | Gynecology Clinic | outpatient |
| KAPI-LD | KAP-LD | Kapiolani Labor & Delivery | off |
| NF-ENDO | NF/ENDO | Night Float + Endocrinology | inpatient (half-block) |
| NEURO-NF | NEURO/NF | Neurology + Night Float | inpatient (half-block) |

## Half-Block Rotations

Some rotations are "half-block" meaning they occupy only half of a 4-week block:

- First half (weeks 1-2): One rotation
- Second half (weeks 3-4): Different rotation

Examples:
- `NF/MS:Endo` = Night Float (weeks 1-2) + Endocrinology (weeks 3-4)
- `NEURO/NF` = Neurology (weeks 1-2) + Night Float (weeks 3-4)
- `C+N` = Cardiology (weeks 1-2) + Night Float (weeks 3-4)

The system tracks these using:
- `is_block_half_rotation`: true/false
- `paired_template_id`: UUID of the paired rotation
- `split_day`: Day number where split occurs

## Block Structure

- Academic year: 13 blocks (4 weeks each, 52 weeks total)
- Block 1: Late June/early July
- Block 13: Late May/early June

### Block 10 (2025-2026)
- Dates: March 12 - April 8, 2026
- Mid-year block
