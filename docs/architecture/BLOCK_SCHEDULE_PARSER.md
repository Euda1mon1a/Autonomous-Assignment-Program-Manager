# Block Schedule Parser Architecture

**Last Updated:** 2025-12-26
**Source:** `backend/app/services/xlsx_import.py`

---

## Overview

The `BlockScheduleParser` is an anchor-based fuzzy-tolerant Excel parser designed to extract schedule data from human-edited spreadsheets with unpredictable structure.

## Problem Space

Medical residency schedules are often maintained in Excel files that exhibit:

| Problem | Cause | Traditional Parser Failure |
|---------|-------|---------------------------|
| **Column shifts** | Copy/paste operations | Hardcoded column indices break |
| **Merged cells** | Multi-day events, headers | Values appear in unexpected cells |
| **Name variations** | Typos, format inconsistency | Exact string matching fails |
| **Missing headers** | Manual editing | Header-based parsing fails |
| **Date scatter** | Non-contiguous date columns | Left-to-right scan fails |

## Design Principles

### 1. Anchor-Based Column Discovery

Instead of assuming column positions, the parser searches for known content patterns:

```
┌─────────────────────────────────────────────────────┐
│  A       B         C          D       E       F    │
├─────────────────────────────────────────────────────┤
│  [gap]   TEMPLATE  ROLE       NAME    [date]  ...  │  <- Headers might be here
│          R3        PGY 3      Doria   AM      ...  │  <- Or values here
│          R3        PGY 3      Evans   PM      ...  │
└─────────────────────────────────────────────────────┘
           ↑         ↑          ↑
        Anchor 1  Anchor 2   Anchor 3
```

**Algorithm:**
```python
def _find_anchor_columns(self):
    """Scan first N rows to find columns by content, not position."""
    for row in range(1, min(50, max_rows)):
        for col in range(max_cols):
            val = str(cell(row, col).value or "").upper().strip()

            # Template anchor: R1, R2, R3, or "TEMPLATE"
            if val in {"R1", "R2", "R3", "R2-NIGHT", "TEMPLATE"}:
                self.template_col = col

            # Role anchor: PGY levels or "ROLE"
            if val in {"PGY 1", "PGY 2", "PGY 3", "FAC", "ROLE"}:
                self.role_col = col

            # Provider anchor: Known names or "PROVIDER"
            if val in known_names or val == "PROVIDER":
                self.provider_col = col
```

### 2. Fuzzy Name Matching

Uses `difflib.SequenceMatcher` to handle name variations:

```python
def _fuzzy_match_name(self, parsed_name: str) -> tuple[str, float]:
    """Match parsed name against known people.

    Returns:
        (matched_name, confidence) where confidence is 0.0-1.0
    """
    # Direct match
    if parsed_name in self.known_people:
        return parsed_name, 1.0

    # Fuzzy match
    best_match = None
    best_ratio = 0.0

    for known in self.known_people:
        ratio = SequenceMatcher(None, parsed_name.lower(), known.lower()).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = known

    if best_ratio >= 0.85:
        return best_match, best_ratio

    # No match, return original
    return parsed_name, 0.5
```

**Match Examples:**

| Parsed | Known | Ratio | Action |
|--------|-------|-------|--------|
| "Doria, Russell" | "Doria, Russell" | 1.00 | Exact match |
| "Doria Russell" | "Doria, Russell" | 0.93 | Fuzzy match accepted |
| "R. Doria" | "Doria, Russell" | 0.71 | Below threshold, warn |

### 3. Merged Cell Handling

Excel merged cells only store the value in the top-left cell:

```
┌─────┬─────┬─────┐
│ A   │ B   │ C   │  <- Merged: A spans rows 1-3
├─────┼─────┼─────┤
│     │ X   │ Y   │  <- A appears empty, but value is from row 1
├─────┼─────┼─────┤
│     │ Z   │ W   │
└─────┴─────┴─────┘
```

**Solution:**
```python
def _get_merged_cell_value(self, row: int, col: int):
    """Get value, following merged cell references."""
    cell = self.sheet.cell(row, col)

    if isinstance(cell, MergedCell):
        # Find the master cell
        for merged_range in self.sheet.merged_cells.ranges:
            if cell.coordinate in merged_range:
                master = self.sheet.cell(merged_range.min_row, merged_range.min_col)
                return master.value

    return cell.value
```

### 4. Date Column Discovery

Instead of assuming date positions, scan for datetime values:

```python
def _discover_date_columns(self):
    """Find columns containing date values."""
    date_cols = []

    for col in range(self.provider_col + 1, max_cols):
        for row in sample_rows:
            val = self.sheet.cell(row, col).value
            if isinstance(val, datetime):
                date_cols.append(col)
                break

    return sorted(set(date_cols))
```

## Data Flow

```
Excel File (.xlsx)
       │
       ▼
┌─────────────────────────┐
│   BlockScheduleParser   │
│                         │
│  1. Load workbook       │
│  2. Find anchor columns │
│  3. Parse roster        │
│  4. Parse FMIT          │
│  5. Match names         │
│  6. Calculate dates     │
└─────────────────────────┘
       │
       ▼
┌─────────────────────────┐
│    BlockParseResult     │
│                         │
│  - residents[]          │
│  - fmit_weeks[]         │
│  - assignments[]        │
│  - warnings[]           │
│  - errors[]             │
└─────────────────────────┘
       │
       ├──────────────────────────┐
       ▼                          ▼
┌─────────────────┐      ┌──────────────────┐
│  CLI (Rich)     │      │  API (Pydantic)  │
│                 │      │                  │
│  Tables, JSON,  │      │  BlockParseResp  │
│  Markdown       │      │  JSON response   │
└─────────────────┘      └──────────────────┘
```

## API Surface

### Convenience Functions

```python
# Parse entire block roster
result = parse_block_schedule(
    filepath="schedule.xlsx",
    block_number=10,
    known_people=["Doria, Russell", "Evans, Amber"]
)

# Parse FMIT attending schedule
fmit_weeks = parse_fmit_attending(
    filepath="schedule.xlsx"
)
```

### Class Usage

```python
parser = BlockScheduleParser(
    workbook=load_workbook("schedule.xlsx"),
    block_number=10,
    known_people=known_people_list
)

result = parser.parse()

# Access parsed data
for resident in result.residents:
    print(f"{resident['name']}: {resident['template']}")

# Check confidence
low_conf = [r for r in result.residents if r['confidence'] < 0.9]
```

## Output Formats

### 1. CLI Rich Tables

```
         R3 Rotation (7 residents)
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Role       ┃ Name             ┃     Conf ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ PGY 3      │ Doria, Russell   │     100% │
│ PGY 3      │ Evans, Amber     │     100% │
└────────────┴──────────────────┴──────────┘
```

### 2. JSON (CLI or API)

```json
{
  "block_number": 10,
  "start_date": "2025-03-12",
  "end_date": "2025-04-08",
  "residents_by_template": {
    "R3": [
      {"name": "Doria, Russell", "template": "R3", "role": "PGY 3", "confidence": 1.0}
    ]
  },
  "fmit_schedule": [
    {"week_number": 1, "faculty_name": "Chu", "is_holiday_call": false}
  ]
}
```

### 3. Markdown

```markdown
# Block 10 Schedule Summary

## Resident Roster

### R3 Rotation (7 residents)

| Role | Name | Confidence |
|------|------|------------|
| PGY 3 | Doria, Russell | 100% ✓ |
```

## Configuration

### Confidence Thresholds

| Threshold | Meaning | Action |
|-----------|---------|--------|
| 1.0 | Exact match | Accept |
| 0.85-0.99 | High fuzzy match | Accept, no warning |
| 0.80-0.84 | Medium fuzzy match | Accept with warning |
| < 0.80 | Low confidence | Accept with error flag |

### Sheet Naming

The parser expects block sheets named:
- `B01`, `B02`, ... `B13` (preferred)
- `Block 1`, `Block 2`, ... `Block 13` (fallback)
- `01`, `02`, ... `13` (fallback)

FMIT sheet expected: `FMIT` or `FMIT Schedule`

## Error Handling

### Recoverable Errors (Warnings)

- Low confidence name match
- Missing optional columns
- Unexpected template values

### Fatal Errors

- Block sheet not found
- No anchor columns discovered
- Workbook load failure

## Performance

| Operation | Typical Time | Notes |
|-----------|--------------|-------|
| Workbook load | 200-500ms | Depends on file size |
| Anchor discovery | 50-100ms | First 50 rows only |
| Roster parse | 100-200ms | Per block |
| Fuzzy matching | 10-50ms | With ~50 known people |

**Total:** ~500ms for single block parse

## Security Considerations

1. **File validation:** Only `.xlsx` files accepted
2. **Path traversal:** Filenames sanitized before processing
3. **Memory limits:** Large files may exceed memory (workbook is loaded fully)
4. **No macros:** openpyxl ignores VBA macros by default

---

*Architecture documented 2025-12-26*
