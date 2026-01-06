# GUI Bug Report - 2026-01-06

**Testers:** Human + Gemini Flash
**Environment:** immaculate_testdata_20260106 backup

---

## CRITICAL - Data/Backend

| # | Issue | Page | Notes |
|---|-------|------|-------|
| 1 | **Block dates wrong** for Block 10 and likely all blocks | Schedule | Block 0 fudge factor lost (recurring issue) |
| 2 | **Month view only populates 2 days** | Schedule/Month | Only Jan 2 & Jan 5 show data |
| 3 | **Week view only shows Mon/Tue** | Schedule/Week | Wed-Sun empty |
| 4 | **Call roster empty** in January | Call Roster | All views (All, Attending, Senior, Intern) empty despite 231 seeded |
| 5 | **Conflicts API returns 404** | Conflicts | "Error loading conflicts - Not Found" but dashboard shows 42 violations |
| 6 | **Import batches not displayed** | Import/Export | 7 batches seeded but table missing from UI |
| 7 | **CSV export fails** | Import/Export | Download initiates but file never appears in Downloads |

## HIGH - Permissions/Auth

| # | Issue | Page | Notes |
|---|-------|------|-------|
| 8 | **Swap Marketplace permission error** | Swaps | "You do not have permission" for admin user |

## MEDIUM - UX/Layout

| # | Issue | Page | Notes |
|---|-------|------|-------|
| 9 | **Top bar not sticky** | Schedule | Date display should be locked during scroll |
| 10 | **Nav buttons trail off right** | All | Should segment into User/Admin dropdowns |
| 11 | **Manifest not useful** | Daily Manifest | Needs birds-eye: Clinic AM/PM, AT AM/PM, Procs AM/PM, FMIT coverage |
| 12 | **People profiles not clickable** | People | Names are static text, not links |
| 13 | **Missing PGY filter** | Schedule | No dropdown to filter by PGY level |

## LOW - Data Quality (may be seed script)

| # | Issue | Page | Notes |
|---|-------|------|-------|
| 14 | **FMIT not on weekends** | Schedule | May be intentional per rotation rules |
| 15 | **05 JAN AM missing assignments** | Daily View | Unsure if intentional gaps |
| 16 | **Sick leave shows only 2 days** | Absences | Only 6 absences seeded total |

---

## Priority Fix Order

### P0 - Blockers
1. **Block 0 fudge factor** - WITHOUT THIS, ALL ROTATION DATES ARE WRONG. Recurring regression. See `docs/architecture/BLOCK_ZERO_FUDGE.md`
2. Conflicts API 404 (mismatch between dashboard count and conflicts page)
3. Swap permission error for admin

### P1 - Core Functionality
4. Month/Week view data population
5. Call roster display
6. Import batch table component
7. CSV export download

### P2 - UX Polish
8. Sticky header
9. Nav dropdown refactor
10. Manifest redesign
11. People profile links
12. PGY filter

---

## Screenshots Reference
- Month view: Only Jan 2 (45 assignments) and Jan 5 (34 assignments) populated
- Week view: Only Mon 1/5 and Tue 1/6 have data, Wed-Sun show "-"
- Swap: Red error box "You do not have permission to perform this action"
- Conflicts: "Error loading conflicts - Not Found" with Try Again button
- Dashboard: Shows 42 Violations Found correctly

---

## Next Steps
1. Investigate conflicts API endpoint - likely missing route or wrong path
2. Check swap marketplace RBAC - admin should have access
3. Review block date calculation in seed script and frontend
4. Add ImportBatchTable component to Import/Export page
