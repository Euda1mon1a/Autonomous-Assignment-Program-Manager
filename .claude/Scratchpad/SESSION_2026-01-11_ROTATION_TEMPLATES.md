# Session 2026-01-11: Rotation Template Review & Naming Convention

## Summary

Reviewed Block 10-13 rotation templates, added missing weekly patterns, and standardized DB naming conventions for human legibility.

## Part 1: Weekly Pattern Configuration

### Activities Created
- `advising` (ADV) - Faculty Advising (educational)
- `fm_clinic_i` (C-I) - FM Clinic Inpatient Follow-ups (clinical)

### Weekly Patterns Added

**PGY-1 Wednesday Pattern (all intern templates):**
- Weeks 1-3: AM = C (fm_clinic), PM = LEC
- Week 4: AM = LEC, PM = ADV (inverted)

**PGY-2/3 Wednesday Pattern (FMIT-R, FMIT-PA):**
- Weeks 1-3: PM = LEC only (no Wed AM clinic - constraint blocks it)
- Week 4: AM = LEC, PM = ADV

**FMIT Clinic Days:**
- FMIT-PGY1: Wed AM = C
- FMIT-PGY2: Tue PM = C (all 4 weeks)
- FMIT-PGY3: Mon PM = C-I (all 4 weeks)

### Templates Updated with Patterns
- FMC, KAPI-LD, IM-INT, PEDS-W, PR-AM (PGY-1 pattern)
- IM, PROC, TAMC-LD, MSK-SEL (PGY-1 pattern)
- ELEC, EM, PEDS-SUB, SURG-EXP, DERM, GYN-CLIN (PGY-2/3 pattern)
- FMIT-PGY1 (FMI), FMIT-PGY2 (FMIT-R), FMIT-PGY3 (FMIT-PA)

## Part 2: Naming Convention Standardization

### DB Schema Change
- Extended `rotation_templates.abbreviation` from varchar(10) to varchar(20)

### Naming Pattern
```
{ROTATION}-{PGY_LEVEL} or {ROTATION}-{ROLE}

Suffixes:
- -PGY1, -PGY2, -PGY3 for resident levels
- -FAC, -FAC-AM, -FAC-PM for faculty
- -1ST-{ROT}-2ND for half-block combos
- NF-{SPECIALTY} prefix for Night Float
```

### Templates Renamed

| Old | New | Notes |
|-----|-----|-------|
| FMI | FMIT-PGY1 | Intern |
| FMIT-R | FMIT-PGY2 | Resident |
| FMIT-PA | FMIT-PGY3 | Pre-Attending |
| FMIT-AM | FMIT-FAC-AM | Faculty AM |
| FMIT-PM | FMIT-FAC-PM | Faculty PM |
| IM-INT | IM-PGY1 | Internal Medicine |
| PEDS-W | PEDS-WARD-PGY1 | Pediatrics Ward |
| PNF | NF-PEDS-PGY1 | Night Float Peds |
| LDNF | NF-LD | Night Float L&D |
| NEURO-NF | NEURO-1ST-NF-2ND | Half-block combo |
| NF-ENDO | NF-1ST-ENDO-2ND | Half-block combo |
| GYN-CLIN | GYN | Shortened |
| SURG-EXP | SURG | Shortened |
| PR-AM | PROC-AM | Clarified |
| HILO | HILO-PGY3 | PGY-specific |
| KAPI-LD | KAPI-LD-PGY1 | PGY-specific |

### Verification
- Block 10: 17 residents, 15 templates, 1,008 daily assignments
- All FKs use UUID (not abbreviation) - no broken references
- `display_abbreviation` unchanged (UI still shows short names)

## Part 3: Key Decisions (Physician Approved)

### ACGME 1-in-7 PAUSE Logic (from earlier)
- Absence: Counter HOLDS (doesn't reset)
- Scheduled day off: Counter RESETS to 0
- Protected in `block_assignment_expansion_service.py` with DO NOT MODIFY warning
- Tests in `test_block_assignment_expansion_service.py`

### Electives (Future Work)
- Move away from generic ELEC template
- Create specialty-specific templates: ELEC-DERM-PGY2, ELEC-CARDIO-PGY3, etc.
- Requires identifying all elective specialties and migrating assignments

## Files Modified (DB only this session)

Database tables updated:
- `rotation_templates` - abbreviation, name columns
- `weekly_patterns` - new patterns added
- `activities` - advising, fm_clinic_i added

## Outstanding Items

1. **Seed scripts have old names** - `scripts/seed_rotation_templates.py` etc. need updating if re-seeding
2. **Other NF combos** - C+N, D+N, NIC etc. don't follow new naming pattern yet
3. **Elective expansion** - Replace generic ELEC with specialty-specific templates

## Branch Status

- Branch: `feature/rotation-template-review`
- Changes: DB only (no code changes to commit yet)
- Ready for: PR with migration script to persist naming changes

## Next Steps

1. Create Alembic migration to persist naming convention changes
2. Update seed scripts to match new names
3. Extend naming convention to Blocks 11-13 templates
4. Consider elective template expansion
