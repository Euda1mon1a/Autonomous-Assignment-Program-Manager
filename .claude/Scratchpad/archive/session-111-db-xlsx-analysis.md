# Session 111: DB vs XLSX Analysis

## Date: 2026-01-15
## Status: HANDOFF TO COMPACT

---

## Key Finding: DB ↔ FINAL_PIPELINE.xlsx Mismatch

**Call assignments only 15% match between DB and exported xlsx.**

### Call Comparison (DB vs FINAL_PIPELINE.xlsx)

| Date | DB | XLSX | Match |
|------|-----|------|-------|
| Mar 12 | Van Brunt | Chu | ❌ |
| Mar 15 | Kinkennon | Tagawa | ❌ |
| Mar 16 | McRae | Kinkennon | ❌ |
| Mar 17 | Montgomery | Montgomery | ✓ |
| Mar 18 | LaBounty | Bevis | ❌ |
| Mar 19 | Dahl | McGuire | ❌ |
| Mar 22 | Colgan | Brunt | ❌ |
| Mar 23 | Tagawa | LaBounty | ❌ |
| Mar 24 | McGuire | Colgan | ❌ |
| Mar 25 | Chu | McRae | ❌ |
| Mar 26 | Napierala | Napierala | ✓ |
| Mar 29 | Bevis | Dahl | ❌ |
| Mar 30 | Van Brunt | Chu | ❌ |
| Mar 31 | Kinkennon | Tagawa | ❌ |
| Apr 01 | McRae | Kinkennon | ❌ |
| Apr 02 | Montgomery | Montgomery | ✓ |
| Apr 05 | LaBounty | Bevis | ❌ |
| Apr 06 | Dahl | McGuire | ❌ |
| Apr 07 | Colgan | Brunt | ❌ |
| Apr 08 | Tagawa | LaBounty | ❌ |

**Result: 3/20 matches (15%)**

---

## DB Call vs Absence Conflicts

The DB has call assignments that conflict with absences:

| Date | On Call | Conflict |
|------|---------|----------|
| Mar 19 | Brian Dahl | Has vacation Mar 16-20 |
| Mar 22 | Bridget Colgan | DEPLOYED Feb 21 - Jun 30 |
| Mar 23 | Chelsea Tagawa | Has vacation Mar 23-27 |
| Apr 07 | Bridget Colgan | DEPLOYED |

---

## Faculty Absences (Block 10)

| Faculty | Dates | Type |
|---------|-------|------|
| Montgomery | Mar 9-14 | TDY/USAFP |
| Dahl | Mar 16-20 | Vacation |
| Colgan | Feb 21 - Jun 30 | **DEPLOYED** |
| Tagawa | Mar 6-12, Mar 23-27, Mar 30 | Vacation |
| McGuire | Mar 6-14 | Vacation/USAFP |
| Chu | Apr 5-7 | Vacation |
| Bevis | Mar 9-14 | USAFP/TDY |

---

## Resident Absences (Block 10)

| Resident | Dates | Type |
|----------|-------|------|
| Gigon | Mar 25 - Apr 3 | Vacation (C4) |
| Petrie | Apr 3-8 | Vacation |
| Sloss | Mar 14-20 | Vacation |
| Maher | Mar 21-23 | Vacation |
| Cook | Apr 4-7 | Vacation |
| Sawyer | Mar 22-28, Apr 6-8 | Vacation |

---

## Export Pipeline Issues

### Missing Faculty in XLSX
- Napierala: Shows None/None
- Van Brunt: Shows None/None
- Lamoureux: Shows None/None

These adjunct faculty have no assignments exported.

### Pipeline Architecture
```
Central Dogma: DB → XML → xlsx
```
- `block_schedule_export_service.py` - Main export service
- `_query_call_assignments()` - Queries CallAssignment table
- `_query_faculty_assignments()` - Queries Assignment table for faculty

---

## Root Cause Hypothesis

1. **FINAL_PIPELINE.xlsx not generated from DB** - May have been generated from a template or ROSETTA
2. **Export service not being used** - Pipeline might bypass `block_schedule_export_service.py`
3. **Stale export** - xlsx may be from an older DB state

---

## Next Steps

1. Verify how FINAL_PIPELINE.xlsx was generated
2. Run fresh export using `block_schedule_export_service.py`
3. Compare fresh export with DB
4. Fix call/absence conflicts in DB
5. Re-export and validate

---

## Key Files

- `backend/app/services/block_schedule_export_service.py` - Export service
- `backend/app/services/schedule_xml_exporter.py` - XML generation
- `backend/app/services/xml_to_xlsx_converter.py` - xlsx conversion
- `Block10_FINAL_PIPELINE.xlsx` - Current output (mismatched)

---

## Commands Used

```sql
-- Query call assignments
SELECT ca.date, p.name, ca.call_type
FROM call_assignments ca
JOIN people p ON ca.person_id = p.id
WHERE ca.date >= '2026-03-12' AND ca.date <= '2026-04-08'
ORDER BY ca.date;

-- Query absences
SELECT a.start_date, a.end_date, p.name, a.absence_type
FROM absences a
JOIN people p ON a.person_id = p.id
WHERE a.start_date <= '2026-04-08' AND a.end_date >= '2026-03-12'
ORDER BY p.name, a.start_date;
```

---

## Summary for Next Session

### Current Truth
**FINAL_PIPELINE.xlsx** is the current working schedule output.

### Match Analysis
| Source | Match to FINAL_PIPELINE |
|--------|------------------------|
| DB call_assignments | 15% |
| ROSETTA | 10% |

**Conclusion:** FINAL_PIPELINE was generated from a solver/template, not DB or ROSETTA.

### Critical DB Issues to Address

1. **Call/Absence Conflicts:**
   - Mar 19: Dahl on call but has vacation
   - Mar 22, Apr 07: Colgan on call but is DEPLOYED
   - Mar 23: Tagawa on call but has vacation

2. **Missing Adjunct Faculty Assignments:**
   - Napierala, Van Brunt, Lamoureux show None/None in export

### Next Session Plan
1. **Review DB call_assignments** - Decide if DB represents "requested" or needs updating
2. **Fix call/absence conflicts** - Either remove invalid calls or update absences
3. **Generate fresh export** - Run `block_schedule_export_service.py` from clean DB
4. **Compare new export to FINAL_PIPELINE** - Validate pipeline is using DB

### Key Skill Loaded
`tamc-excel-scheduling` - Contains all TAMC scheduling rules, faculty caps, rotation patterns

### Branch
`claude/session-110-block10-tuning` (clean, no uncommitted work)
