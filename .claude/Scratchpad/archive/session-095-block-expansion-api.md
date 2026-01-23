# Session 095: Block Assignment Expansion API

**Date:** 2026-01-13
**Branch:** `feat/exotic-explorations`
**Status:** Implemented, needs MCP integration

## Summary

Added `expand_block_assignments` params to `/api/v1/schedule/generate` endpoint.

## Changes

### `backend/app/schemas/schedule.py`
Added to `ScheduleRequest`:
```python
expand_block_assignments: bool = Field(default=False)
block_number: int | None = Field(default=None, ge=0, le=13)
academic_year: int | None = Field(default=None, ge=2020, le=2100)
```

### `backend/app/api/routes/schedule.py`
Updated `engine.generate()` calls to pass new params.

## Usage

```bash
curl -X POST "http://localhost:8000/api/v1/schedule/generate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2026-03-12",
    "end_date": "2026-04-08",
    "algorithm": "cp_sat",
    "timeout_seconds": 120,
    "expand_block_assignments": true,
    "block_number": 10,
    "academic_year": 2025
  }'
```

## TODO: MCP Integration

**CRITICAL:** Add `expand_block_assignments` workflow to MCP tools.

Needed MCP tool updates:
1. `generate_schedule_tool` - Add `expand_block_assignments`, `block_number`, `academic_year` params
2. Consider new `expand_block_assignments_tool` for standalone expansion

Location: `mcp-server/src/scheduler_mcp/tools/`

## Workflow

1. Coordinator imports block-year Excel → `block_assignments` table
2. Call generate with `expand_block_assignments=true` + `block_number` + `academic_year`
3. Engine expands `block_assignments` into daily slots
4. Solver fills gaps around expanded assignments
5. Validate ACGME compliance
