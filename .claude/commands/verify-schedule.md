<!--
Human verification checklist for generated schedules.
Runs systematic checks on FMIT, call, Night Float, clinic days, and absences.
-->

Run the schedule-verification skill to validate a generated schedule.

## Arguments

- `$ARGUMENTS` - Block number or date range to verify (e.g., "10" or "2026-03-12 to 2026-04-08")

## Verification Process

Load and execute the schedule-verification skill from `.claude/skills/schedule-verification/SKILL.md`.

### Required Checks

1. **Faculty FMIT Schedule**
   - No back-to-back FMIT weeks
   - FMIT faculty has Fri+Sat call during their week
   - Post-FMIT Sunday blocking respected

2. **Resident Inpatient Assignments**
   - FMIT headcount: 1 per PGY level
   - Night Float: exactly 1 resident at a time
   - Post-Call Thursday after NF ends

3. **Call Schedule Equity**
   - Sunday call evenly distributed
   - No back-to-back call weeks
   - PD/APD Tuesday avoidance

4. **Absence Handling**
   - No assignments during approved leave
   - No assignments during TDY

5. **Coverage Metrics**
   - Overall coverage > 80%
   - ACGME violations = 0

### Output Format

Generate a visible report with PASS/FAIL for each check:

```
SCHEDULE VERIFICATION REPORT
Block: [number] | Date Range: [start] to [end]
═══════════════════════════════════════════════
CHECK                              STATUS  DETAILS
───────────────────────────────────────────────
FMIT faculty rotation pattern      PASS    No b2b
Night Float headcount = 1          FAIL    Found 2 on 03/15
...
═══════════════════════════════════════════════
SUMMARY: X passed, Y failed
```

Save report to `docs/reports/schedule-verification-block{N}-{date}.md`
