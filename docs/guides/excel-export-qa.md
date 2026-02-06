# Excel Export QA (Block Template2)

This workflow verifies that exported `.xlsx` data matches schedule data in the database.

## What changed

Canonical export now:

- Preserves AM/PM cells even when the template contains merged schedule ranges.
- Adds an `Export_QA` worksheet by default with explicit code totals and per-faculty
  clinic breakdown (`C`, `SM`, and `C+SM`).

## Quick export

```bash
python scripts/ops/block_export.py --block 10 --academic-year 2025 --output /tmp/block10.xlsx
```

Optional:

```bash
python scripts/ops/block_export.py --block 10 --academic-year 2025 --output /tmp/block10.xlsx --no-qa
```

Optional identity/presentation controls:

```bash
# Write columns A-E from DB values instead of keeping template labels/names.
python scripts/ops/block_export.py --block 10 --academic-year 2025 --output /tmp/block10.xlsx --write-identity-fields

# Use a different presentation profile (default is tamc_handjam_v2).
python scripts/ops/block_export.py --block 10 --academic-year 2025 --output /tmp/block10.xlsx --presentation-profile tamc_handjam_v2
```

## Parity audit (DB vs XLSX)

Run against live DB and generate an audited workbook:

```bash
DBURL=$(docker exec -i scheduler-local-backend printenv DATABASE_URL | sed 's/@db:/@localhost:/')
DATABASE_URL="$DBURL" CORS_ORIGINS='["http://localhost:3000"]' \
  ./backend/venv/bin/python scripts/ops/export_parity_audit.py \
  --block 10 --academic-year 2025 --output /tmp/block10_parity.xlsx
```

`STATUS: PASS` means rendered workbook values match effective export data.

## Notes on template summary columns

Some built-in summary columns on `Block Template2` are composite:

- Resident `BJ` combines `C`, `C-I`, `SM`.
- Faculty `BJ` combines `C`, `SM`.

Use `Export_QA` for explicit code totals when you need pure `C` counts.

## Known limitation: activity granularity

The exporter reflects codes present in `half_day_assignments` (descriptive truth).
If a legacy handjam sheet contains codes that are not in DB for the block
(for example `Ophtho`, `URO`, `EPIC`, `C30`), export cannot recreate those
without regenerating assignments upstream.
