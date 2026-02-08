# Excel Export QA (Block Template2)

This workflow verifies that exported `.xlsx` data matches schedule data in the database.

## What changed

Canonical export now:

- Preserves AM/PM cells even when the template contains merged schedule ranges.
- Adds an `Export_QA` worksheet by default with explicit code totals and per-faculty
  clinic breakdown (`C`, `SM`, and `C+SM`).

## Quick export

Use backend virtualenv Python (3.11+):

```bash
./backend/venv/bin/python scripts/ops/block_export.py --block 10 --academic-year 2025 --output /tmp/block10.xlsx
```

Optional:

```bash
./backend/venv/bin/python scripts/ops/block_export.py --block 10 --academic-year 2025 --output /tmp/block10.xlsx --no-qa
```

Optional identity/presentation controls:

```bash
# Write columns A-E from DB values instead of keeping template labels/names.
./backend/venv/bin/python scripts/ops/block_export.py --block 10 --academic-year 2025 --output /tmp/block10.xlsx --write-identity-fields

# Use a different presentation profile (default is tamc_handjam_v2).
./backend/venv/bin/python scripts/ops/block_export.py --block 10 --academic-year 2025 --output /tmp/block10.xlsx --presentation-profile tamc_handjam_v2
```

## Values-only fallback (preserve workbook formatting)

When visual parity is not perfect, use this path and let Excel formatting stay in control.

Generate a paste payload workbook:

```bash
./backend/venv/bin/python scripts/ops/export_values_paste.py --block 10 --academic-year 2025 --output /tmp/block10_paste_payload.xlsx
```

Apply values directly into an existing handjam workbook:

```bash
./backend/venv/bin/python scripts/ops/export_values_paste.py \
  --block 10 --academic-year 2025 \
  --target-workbook "/Users/aaronmontgomery/Downloads/TAMC_Schedule_Fixedv2_AY25-26.xlsx" \
  --target-sheet "Block 10" \
  --output "/tmp/TAMC_Schedule_Fixedv2_AY25-26_values_applied.xlsx"
```

Optional:

```bash
# Export tab-separated payload (good for copy/paste and quick diffs)
./backend/venv/bin/python scripts/ops/export_values_paste.py --block 10 --academic-year 2025 --grid-tsv /tmp/block10_grid.tsv

# Copy grid payload to macOS clipboard
./backend/venv/bin/python scripts/ops/export_values_paste.py --block 10 --academic-year 2025 --pbcopy-grid
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
