# Session 101: Backup Analysis & ROSETTA Fix

**Date:** 2026-01-14
**Branch:** `feat/session-091`
**Status:** 🔄 Code fix required - backup has same issues

## Key Finding

**Backup inspection reveals the issue predates the nuke.** Restoring from backup won't help.

### Backup Contents (pre_destructive_20260113_215933.sql.gz)

| Template | abbreviation | display_abbreviation | Issue |
|----------|--------------|----------------------|-------|
| NF-PM | NF-PM | NF | Half-day template, not rotation |
| NEURO-NF | NEURO-NF | NEURO/NF | Combined template, not split |
| PROC | PROC | PROC | Exists correctly |

### Block Assignments in Backup

| Resident | rotation_template_id | secondary_rotation_template_id | Issue |
|----------|---------------------|-------------------------------|-------|
| Sloss | Points to PR-AM | NULL | Should point to PROC |
| You, Jae | Points to NEURO-NF | NULL | Should be NEURO + NF (split) |

## Root Cause

The original data import (`claude-import`) never created:
1. Standalone `NEURO` rotation template
2. Standalone `NF` rotation template
3. Correct block assignments with primary + secondary templates

## Recommended Fix: Option B (Code Fix)

Since DB data is fundamentally wrong and backup has same issues, modify code to handle edge cases.

### Fix 1: Add PR Alias in schedule_xml_exporter.py

```python
ROT_HANDLERS = {
    ...
    "PROC": _get_proc_assignment,
    "PR": _get_proc_assignment,  # Alias for half-day template
    ...
}
```

### Fix 2: Handle Combined Templates in _get_active_rotation()

```python
def _get_active_rotation(self, resident: dict[str, Any], current: date) -> str:
    rotation1 = resident.get("rotation1", "")
    rotation2 = resident.get("rotation2", "")

    # Handle combined templates like "NEURO/NF"
    if "/" in rotation1 and not rotation2:
        parts = rotation1.split("/")
        if current >= self.mid_block_date:
            return parts[1] if len(parts) > 1 else rotation1
        return parts[0]

    # Original logic for proper split templates
    if rotation2 and current >= self.mid_block_date:
        return rotation2
    return rotation1
```

## Backup Locations (For Reference)

| Backup | Location | Size | Timestamp |
|--------|----------|------|-----------|
| Pre-destructive | `backups/auto/pre_destructive_20260113_215933.sql.gz` | 4.7MB | Jan 13 21:59 |
| Pre-destructive | `backups/auto/pre_destructive_20260113_215654.sql.gz` | 4.7MB | Jan 13 21:56 |

## Files Modified

| File | Line | Change |
|------|------|--------|
| `schedule_xml_exporter.py` | 199 | Added `"PR": _get_proc_assignment` alias to ROT_HANDLERS |
| `schedule_xml_exporter.py` | 268-291 | Modified `_get_active_rotation()` to handle combined templates |

## Code Changes Applied

### 1. PR Alias (line 199)
```python
"PR": _get_proc_assignment,  # Alias for half-day template (PR-AM uses display=PR)
```

### 2. Combined Template Handling (lines 284-289)
```python
# Case 2: Combined template like "NEURO/NF" - parse and split at mid-block
if "/" in rotation1 and not rotation2:
    parts = rotation1.split("/")
    if len(parts) == 2 and current >= self.mid_block_date:
        return parts[1]
    return parts[0]
```

## Next Step

Re-export Block 10 and run ROSETTA validation:
- Expected: 100% (448/448 slots)
