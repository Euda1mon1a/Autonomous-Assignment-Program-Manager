# Session: Block Schedule Import - Anchor-Based Fuzzy-Tolerant Excel Parser

**Date:** 2025-12-26
**Branch:** `claude/block0-engine-fix-commands`
**Status:** Complete, ready for PR to main

---

## Problem Statement

The residency program maintains schedules in human-edited Excel files with chaotic structure:
- Columns shift after copy/paste operations
- Merged cells span multiple rows/columns
- Name variations (e.g., "Doria, Russell" vs "Russell Doria")
- No consistent column headers between blocks

**User's exact description:** "it's fucking awful, no spreadsheet should be used in this way"

The existing codebase had parsing code in `xlsx_import.py` but no way to invoke it from CLI, API, or generate human-readable output.

---

## Solution: Anchor-Based Fuzzy-Tolerant Parser

### Core Concept

Instead of hardcoded column positions, the parser finds "anchors" by searching for known content patterns:

```python
# Traditional (brittle):
template_col = 0  # Assumes column A always has templates

# Anchor-based (robust):
for col in range(max_cols):
    val = str(sheet.cell(row, col).value or "").upper()
    if val in {"R1", "R2", "R3", "TEMPLATE"}:
        self.template_col = col
        break
```

### Key Features

| Feature | Implementation | Purpose |
|---------|----------------|---------|
| **Anchor discovery** | Scan rows/cols for known values | Handle column shifts |
| **Fuzzy name matching** | `difflib.SequenceMatcher` | Handle typos, format variations |
| **Merged cell handling** | openpyxl `MergedCell` detection | Extract values from merged ranges |
| **Date column discovery** | Scan for datetime values | Find schedule date columns |
| **Confidence scoring** | 0.0-1.0 per match | Flag low-confidence matches for review |

---

## Files Created

### 1. `backend/app/schemas/block_import.py`
Pydantic schemas for type-safe API responses:

```python
class ResidentRosterItem(BaseModel):
    name: str           # "Last, First" format
    template: str       # R1, R2, R3
    role: str           # PGY 1, PGY 2, PGY 3, FAC
    row: int            # Source spreadsheet row
    confidence: float   # 0.0-1.0 match confidence

class BlockParseResponse(BaseModel):
    success: bool
    block_number: int
    residents: list[ResidentRosterItem]
    residents_by_template: dict[str, list[ResidentRosterItem]]
    fmit_schedule: list[ParsedFMITWeekSchema]
    warnings: list[str]
    errors: list[str]
```

### 2. `backend/app/services/block_markdown.py`
Markdown generator with structured output:

```python
def generate_block_markdown(
    result: BlockParseResult,
    fmit_weeks: list[ParsedFMITWeek] | None = None,
    include_assignments: bool = False,
) -> str:
```

Outputs to `docs/schedules/BLOCK_<N>_SUMMARY.md` with:
- Roster tables by template (R3, R2, R1)
- FMIT attending schedule
- Special events (hardcoded for Block 10)
- Parsing warnings/errors

### 3. `backend/app/cli/block_import_commands.py`
Typer CLI with Rich table output:

```bash
# Parse block and show roster
python -m app.cli.block_import_commands parse schedule.xlsx 10

# Output as JSON
python -m app.cli.block_import_commands parse schedule.xlsx 10 -o json

# Generate markdown
python -m app.cli.block_import_commands parse schedule.xlsx 10 -m block10.md

# Show just roster filtered by template
python -m app.cli.block_import_commands roster schedule.xlsx 10 -t R3

# Show FMIT schedule
python -m app.cli.block_import_commands fmit schedule.xlsx
```

### 4. `.claude/skills/managed/import-block.md`
Slash command skill for `/import-block`:
- CLI usage examples
- API usage examples
- Output format documentation
- Related files reference

---

## Files Modified

### `backend/app/api/routes/schedule.py`
Added endpoint at line ~695:

```python
@router.post("/import/block", response_model=BlockParseResponse)
async def import_block_schedule(
    file: UploadFile = File(...),
    block_number: int = Form(..., ge=1, le=13),
    known_people: str = Form("[]"),  # JSON array for fuzzy matching
    current_user: User = Depends(get_current_active_user),
):
```

### `backend/app/services/xlsx_import.py` (earlier in session)
Added:
- `ParsedBlockAssignment` dataclass (lines ~1485)
- `ParsedFMITWeek` dataclass
- `BlockParseResult` dataclass
- `BlockScheduleParser` class (lines ~1530-1825)
- `parse_block_schedule()` convenience function
- `parse_fmit_attending()` convenience function

---

## Domain Knowledge Captured

### Block 10 Schedule (Mar 12 - Apr 8, 2025)

| Template | Count | PGY Levels | Description |
|----------|-------|------------|-------------|
| R3 | 7 | All PGY-3 | Senior inpatient residents |
| R2 | 5 | PGY-2/3 mix | Mixed experience level |
| R1 | 13 | PGY-1/2 mix | Junior/mid-level rotation |

**FMIT Faculty Schedule:**
- Week 1: Dr. Chu
- Week 2: Dr. Bevis
- Week 3: Dr. Chu
- Week 4: Dr. LaBounty

**Special Events:**
- Mar 12-14: USAFP Conference (call coverage needed)
- Mar 27-29: OB Retreat (swaps needed)
- Mar 30: Doctors' Day
- Apr 5: Easter (federal holiday)

### Excel Structure Insights

The source file (`Current AY 25-26 pulled 22DEC2025.xlsx`) has:
- Multiple sheets per block (named "B01", "B02", etc.)
- TEMPLATE column contains: R1, R2, R3, C19 (Clinic), CP
- ROLE column contains: PGY 1, PGY 2, PGY 3, FAC, CP
- PROVIDER column contains names in "Last, First" format
- Date columns scattered across the sheet (not contiguous)
- FMIT data on separate "FMIT" sheet with block/week/faculty

---

## Verification

### CLI Test Results

```
$ DATABASE_URL="postgresql://x:x@localhost/x" ./venv/bin/python -m app.cli.block_import_commands parse "schedule.xlsx" 10

Block 10 Summary
Date Range: March 12 - April 08, 2025

         R3 Rotation (7 residents)
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Role       ┃ Name             ┃     Conf ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ PGY 3      │ Doria, Russell   │     100% │
│ PGY 3      │ Doyle, Jacob     │     100% │
│ PGY 3      │ Evans, Amber     │     100% │
...
```

All 25 residents parsed with 100% confidence scores.

### Markdown Generated

`docs/schedules/BLOCK_10_SUMMARY.md` created with:
- Full roster tables
- FMIT schedule
- Special events
- Parser attribution

---

## Architecture Decisions

### Why Anchor-Based Parsing?

| Approach | Pros | Cons |
|----------|------|------|
| **Fixed columns** | Simple, fast | Breaks on any column shift |
| **Header matching** | More flexible | Headers might be missing/renamed |
| **Anchor-based** | Handles chaos | Slightly slower initial scan |

We chose anchor-based because:
1. Source files are human-edited with frequent copy/paste
2. No guarantee of consistent headers
3. Known values (R1, R2, R3) are reliable anchors

### CLI Database Workaround

The CLI needs to import from `app.services.xlsx_import`, which triggers the FastAPI app initialization chain, which validates `DATABASE_URL`.

**Solution:** Set a dummy DATABASE_URL when running CLI locally:
```bash
DATABASE_URL="postgresql://x:x@localhost/x" python -m app.cli.block_import_commands ...
```

This is acceptable because the CLI only uses parsing logic, not database connections.

---

## Related Files

| File | Purpose |
|------|---------|
| `backend/app/services/xlsx_import.py` | BlockScheduleParser class |
| `backend/app/schemas/block_import.py` | Pydantic response schemas |
| `backend/app/services/block_markdown.py` | Markdown generator |
| `backend/app/cli/block_import_commands.py` | CLI commands |
| `backend/app/api/routes/schedule.py` | API endpoint |
| `.claude/skills/managed/import-block.md` | Slash command skill |
| `docs/schedules/BLOCK_10_SUMMARY.md` | Generated output example |

---

## Next Steps

1. **Commit changes** to `claude/block0-engine-fix-commands`
2. **Create PR** to main branch
3. **Compare** with Claude for macOS contributions (per user request)

---

*Session documented by Claude Code CLI on 2025-12-26*
