# Session 095: Seed Data Restore

**Date:** 2026-01-13
**Branch:** `feat/exotic-explorations`
**Status:** Complete

## Summary

Restored database with real TAMC personnel data from `immaculate_real_personnel_20260107` backup.

## Final Database State

| Table | Count | Notes |
|-------|-------|-------|
| `people` | 29 | 17 residents + 12 faculty with REAL names |
| `absences` | 153 | Leave/vacation data |
| `blocks` | 730 | Half-day slots across 14 blocks (0-13, block 0 = fudge factor) |
| `rotation_templates` | 16 | Basic templates |
| `assignments` | 0 | Cleared, ready for generation |

## Personnel

**17 Residents:**
- PGY-1 (6): Josh Monsivais, Tessa Sawyer, Clara Wilhelm, Meleigh Sloss, Colin Travis, Katie Byrnes
- PGY-2 (6): Scott Cook, Nick Maher, Felipe Cataquiz, Alaine Gigon, Devin Thomas, James Headid
- PGY-3 (5): Jae You, Clay Petrie, Cam Mayell, Christian Hernandez, Laura Connolly

**12 Faculty:** Aaron Montgomery, Alex LaBounty, Blake Van Brunt, Brian Dahl, Bridget Colgan, Chelsea Tagawa, Chris McGuire, Jimmy Chu, Joe Napierala, Sarah Kinkennon, Zach Bevis, Zach McRae

## Key Points

1. Cleared Faker-generated antigravity seed data (84 fake people)
2. Restored real personnel from Jan 7 backup
3. Had to manually handle `is_away_from_program` column (new since backup)
4. 16 basic templates retained (backup had 60 but schema evolved)

## Next Steps

1. May need to seed additional rotation templates (`python scripts/seed_rotation_templates.py`)
2. Ready for schedule generation
3. Can run `python scripts/seed_inpatient_rotations.py --block 10` for FMIT pre-assignment

## Backup Used

**Location:** `backups/immaculate_real_personnel_20260107/`
**Created:** 2026-01-07
**Contains:** Real TAMC personnel, 153 absences, 730 blocks
