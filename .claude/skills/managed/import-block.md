---
description: Parse block schedules from Excel files with fuzzy-tolerant parsing. Use when importing roster data, checking FMIT assignments, or generating block summaries. Handles column shifts, merged cells, and name typos. (project)
---

# Import Block Schedule Skill

Parse block schedules from human-edited Excel files using anchor-based fuzzy-tolerant parsing.

## When to Use

- Importing resident rosters from Excel spreadsheets
- Extracting FMIT faculty weekly assignments
- Generating markdown summaries for blocks
- Validating block schedule data before solver runs
- Analyzing roster changes between blocks

## Capabilities

- **Anchor-based parsing**: Finds TEMPLATE, ROLE, PROVIDER columns by content, not position
- **Fuzzy name matching**: Handles "Doria, Russell" vs "Russell Doria" variations
- **Merged cell handling**: Gracefully processes Excel merged cells
- **Date discovery**: Scans for datetime values to find date columns
- **Column shift tolerance**: Works even after copy/paste operations shift data

## CLI Usage

```bash
# Parse block 10 and show roster (Rich table output)
python -m app.cli.block_import_commands parse schedule.xlsx 10

# Output as JSON
python -m app.cli.block_import_commands parse schedule.xlsx 10 -o json

# Generate markdown summary
python -m app.cli.block_import_commands parse schedule.xlsx 10 -m docs/schedules/BLOCK_10_SUMMARY.md

# Show just the roster
python -m app.cli.block_import_commands roster schedule.xlsx 10

# Filter by template
python -m app.cli.block_import_commands roster schedule.xlsx 10 -t R3

# Show FMIT schedule
python -m app.cli.block_import_commands fmit schedule.xlsx 10
```

## API Usage

```bash
# Parse block with file upload
curl -X POST "http://localhost:8000/api/v1/schedule/import/block" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@schedule.xlsx" \
  -F "block_number=10"

# With fuzzy matching hints
curl -X POST "http://localhost:8000/api/v1/schedule/import/block" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@schedule.xlsx" \
  -F "block_number=10" \
  -F 'known_people=["Doria, Russell", "Evans, Amber", "Giblin, Bailey"]'
```

## Output Format

### Residents by Template

| Template | Count | Description |
|----------|-------|-------------|
| R3 | 7 | Senior residents (all PGY-3) |
| R2 | 5 | Mixed PGY-2/3 |
| R1 | 13 | Junior residents (PGY-1/2) |

### FMIT Schedule

| Week | Faculty |
|------|---------|
| 1 | Chu |
| 2 | Bevis |
| 3 | Chu |
| 4 | LaBounty |

### Confidence Scores

- **1.0 (100%)**: Exact match with known people
- **0.8-0.99**: High confidence fuzzy match
- **< 0.8**: Low confidence - review manually

## Related Files

- `backend/app/services/xlsx_import.py` - BlockScheduleParser class
- `backend/app/services/block_markdown.py` - Markdown generator
- `backend/app/cli/block_import_commands.py` - CLI commands
- `backend/app/api/routes/schedule.py` - API endpoint
- `docs/schedules/` - Generated markdown summaries

## Related Skills

- `/xlsx` - General Excel import/export
- `/generate-schedule` - Run the solver for a block
- `/verify-schedule` - Validate a generated schedule
