# Block 12 Dry Run Report

**Generated:** 2026-02-18 18:44
**Block:** 12 (May 7 – Jun 3, 2026), AY 2025
**Source:** Excel Block Schedule + DB rotation templates
**Type:** DRY RUN — template-derived, NOT from coordinator handjam

## Rotation Assignments (Corrected from Excel)

| Resident | PGY | Primary Rotation | Secondary (Split) | Leave Days |
|----------|-----|-----------------|-------------------|------------|
| Tessa Sawyer | 1 | NF-PEDS-PG | - | - |
| Clara Wilhelm | 1 | NF-FMIT-PG | - | - |
| Colin Travis | 1 | MSK-SEL | - | - |
| Katie Byrnes | 1 | FMIT-PGY2 | NF | - |
| Meleigh Sloss | 1 | PEDS-WARD- | NF-PEDS-PG | - |
| Josh Monsivais | 1 | NBN | - | 7 days |
| Felipe Cataquiz | 2 | NF-LD | - | - |
| Scott Cook | 2 | ELEC | - | - |
| Alaine Gigon | 2 | FMC | - | 6 days |
| James Headid | 2 | ELEC | - | 7 days |
| Nick Maher | 2 | NF-DERM-PG | - | - |
| Devin Thomas | 2 | NF-CARDIO | - | - |
| Christian Hernandez | 3 | PEDS-EM | - | 7 days |
| Cam Mayell | 3 | FMIT-PGY3 | - | - |
| Clay Petrie | 3 | HILO-PGY3 | - | - |
| Jae You | 3 | JAPAN | - | - |

**Total expected HDAs:** 842 (16 residents x 56 slots - absence days)

## Known Absences Overlapping Block 12

| Person | Type | Start | End | Notes |
|--------|------|-------|-----|-------|
| Alaine Gigon | vacation | 2026-05-29 | 2026-06-04 | Block 12 |
| Brian Dahl | vacation | 2026-05-18 | 2026-05-21 | Leave request submitted via email August 10, 2025 - FMIT starts May 22nd |
| Bridget Colgan | deployment | 2026-02-21 | 2026-06-30 | Deployment |
| Chelsea Tagawa | vacation | 2026-05-26 | 2026-05-29 | Leave |
| Christian Hernandez | vacation | 2026-05-27 | 2026-06-02 | Block 12 |
| James Headid | vacation | 2026-05-14 | 2026-05-18 | Block 12 |
| James Headid | vacation | 2026-06-02 | 2026-06-07 | Block 12-13 |
| Josh Monsivais | vacation | 2026-05-24 | 2026-05-30 | Block 12 |

## Issues Identified

1. **DB block_assignments were 100% stale** — all 16 had wrong rotations (Block 11 data)
2. **Laura Connolly** not assigned to Block 12 (graduated/done after Block 10)
3. **Bridget Colgan** (faculty) deployed Feb 21 – Jun 30 — removed supervision assignments
4. **Memorial Day (May 25)** not flagged as holiday in blocks table
5. **6 split-block residents** — using combined NF templates where available

## What This Dry Run Did NOT Generate

- Faculty daily AM/PM activity codes (need handjam)
- Call schedule (Staff Call row)
- Day-specific overrides (clinic cancellations, SIM, conference)
- Sports Medicine rotator schedule (Travis listed as SM rotator)
- TY/Flight Surgeon, medical student, IPAP assignments
- Exact NF split dates (used day 15 cutoff; actual may differ)

## DB vs Excel Discrepancy (Pre-Fix State)

| Resident | Was (DB) | Should Be (Excel) |
|----------|---------|------------------|
| Clara Wilhelm | TAMC-LD | NF-FMIT-PG |
| Colin Travis | PROC | MSK-SEL |
| Katie Byrnes | KAPI-LD-PG | FMIT-PGY2 |
| Meleigh Sloss | NF-AM | PEDS-WARD- |
| Josh Monsivais | NF-AM | NBN |
| Felipe Cataquiz | PEDS-SUB | NF-LD |
| Scott Cook | FMIT-PGY1 | ELEC |
| Alaine Gigon | DERM | FMC |
| James Headid | NF-LD | ELEC |
| Nick Maher | NF-LD | NF-DERM-PG |
| Devin Thomas | ELEC | NF-CARDIO |
| Christian Hernandez | NF-AM | PEDS-EM |
| Cam Mayell | NF-AM | FMIT-PGY3 |
| Clay Petrie | FMC | HILO-PGY3 |
| Jae You | ELEC | JAPAN |
