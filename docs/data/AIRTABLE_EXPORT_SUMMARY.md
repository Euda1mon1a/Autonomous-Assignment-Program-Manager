***REMOVED*** Airtable Data Export Summary

**Source:** `appDgFtrU7njCKDW5` - Residency Schedule Manager
**Exported:** 2025-12-21

---

***REMOVED******REMOVED*** Data Counts

| Table | Records |
|-------|---------|
| Residents | 17 |
| Faculty | 12 |
| Rotations | 15 |
| Primary Duties | 25 |
| AI Agent Memory | 20+ |
| Rotation Templates | Many |
| Blocks | 13 |

> ⚠️ **Note:** 
> - Absence data cleaned: 100 → 92 records (8 duplicates removed)
> - Clean export: `docs/data/airtable_absences_clean.json`
> - Raw backup: `docs/data/airtable_absences_export.json`
> - **C4** = Combat Casualty Care Course (TDY for HPSP grads, not USU)
> - **COMLEX** = DO equivalent of USMLE STEP exams

---

***REMOVED******REMOVED*** Key Business Rules (from AI Agent Memory)

***REMOVED******REMOVED******REMOVED*** Rotation Sequence Rules
- **Order matters in rotation names:**
  - "Dermatology + Night Float" = 1st half Derm → 2nd half Night Float
  - "Night Float + Cardiology" = 1st half Night Float → 2nd half Cardiology
- Must have night float coverage in every block
- Cannot merge rotations with different sequences

***REMOVED******REMOVED******REMOVED*** Faculty Assignment Rules
- **Faculty-A-Last:** EXCLUDED from assignments
- **Chu:** NOW ASSIGNABLE (exclusions removed)
- **Beckwith:** Has specific exclusions

***REMOVED******REMOVED******REMOVED*** Procedure Supervision System
Tracking implemented for:
- Vasectomy (AM/PM attending counters)
- Botox (AM/PM attending counters)
- Colposcopy (AM/PM attending counters)
- Each resident adds +1 to attending needed count

---

***REMOVED******REMOVED*** Primary Duties (25 total)

| Duty | Min Clinic Half-Days/Week |
|------|--------------------------|
| Program Director | 0 |
| Associate Program Director | 1 |
| Officer in Charge | 1 |
| Department Chief | 1 |
| Sports Medicine | 0 |
| Faculty Alpha-Hotel | 2 each |
| Adjunct Alpha-Hotel | 0 each |
| Deployed Alpha/Bravo | 0 |
| TDY Alpha/Bravo | 0 |

---

***REMOVED******REMOVED*** Rotations (15)

1. FMIT + Night Float Intern
2. Procedures Rotation
3. Family Medicine Clinic Resident
4. Internal Medicine Intern
5. Emergency Medicine
6. Neurology Selective
7. Infectious Disease Selective
8. Dermatology + Night Float
9. Night Float + Psychiatry
10. Neonatal Intensive Care Unit + Night Float
11. Palliative Selective
12. Pediatrics Subspecialty
13. Selective Medicine
14. Surgical Experience
15. Research Elective

---

***REMOVED******REMOVED*** Sample Data

***REMOVED******REMOVED******REMOVED*** Residents
- Cook (PGY-2)
- You (PGY-3)
- PGY1-A-Last (PGY-1)
- PGY1-B-Last (PGY-1)
- PGY3-B-Last (PGY-3)
- ... (17 total)

***REMOVED******REMOVED******REMOVED*** Faculty
- Faculty-C-Last
- Faculty-D-Last
- Faculty-I-Last
- Montgomery
- Faculty-J-Last
- ... (12 total)

---

***REMOVED******REMOVED*** Implementation Opportunities

1. **Import residents/faculty** from Airtable to local DB
2. **Apply rotation sequence logic** to scheduling constraints
3. **Implement procedure supervision counters**
4. **Add faculty exclusion rules** (Faculty-A-Last exclusions, etc.)
5. **Use 25 primary duties** for role-based scheduling

---

***REMOVED******REMOVED*** API Access

```bash
***REMOVED*** Set in ~/.zshrc
export AIRTABLE_API_KEY="your-token"

***REMOVED*** List all records
curl "https://api.airtable.com/v0/appDgFtrU7njCKDW5/Residents" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY"
```
