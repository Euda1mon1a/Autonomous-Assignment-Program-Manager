# Block Import Templates

Sanitized templates for importing block schedule data from Excel handjam files.

## Files

| Template | Purpose |
|----------|---------|
| `block_import_template.py` | Parse Excel, load HDAs, sync absences |
| `fix_assignments_template.py` | Fix stale assignments, backfill HDA linkage |
| `populate_faculty_templates_template.py` | Extract faculty weekly patterns from Excel |

## Workflow

1. **Backup** the database before any import
2. **Copy** templates to `/tmp/` and fill in block-specific config (names, dates, code mappings)
3. **Run** `block_import_template.py` first (HDAs + absences)
4. **Run** `fix_assignments_template.py` (assignments + HDA linkage)
5. **Run** `populate_faculty_templates_template.py` (faculty patterns)
6. **Verify** in GUI and via API

## Local Scripts

Executed scripts with real data (names, UUIDs) are stored in `scripts/data/` which is gitignored.
Each block gets its own subdirectory: `scripts/data/blockNN_import/`.

## Reference

See `docs/development/BLOCK11_SCHEDULE_LOAD.md` for the full Block 11 import log.
