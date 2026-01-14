# Excel Workbook Structure - AY 25-26

## Workbook Sheets

| Sheet | Purpose |
|-------|---------|
| Block Schedule | Overview - all residents, all blocks |
| Block 2 - Block 13 | Individual block detail sheets |
| FMIT Attending (2025-2026) | FMIT faculty rotation schedule |
| Templates | Rotation templates with half-day codes |

## Individual Block Sheet Structure

### Header Section (Rows 0-5)

| Row | Content |
|-----|---------|
| 0 | Block number, Day names (THURS, FRI, SAT...) |
| 1 | AM/PM labels (alternating) |
| 2 | "Date:", Actual dates (2025-07-31, 2025-08-01...) |
| 3 | "Staff Call", Faculty name when on call that night |
| 4 | "Resident Call", Resident call markers |
| 5 | "TEMPLATE", "ROLE", "PROVIDER" headers |

### Resident Section (Rows 8-35)

| Row Range | PGY Level | Content |
|-----------|-----------|---------|
| 8-17 | R3 (PGY-3) | Third-year residents |
| 18-22 | R2 (PGY-2) | Second-year residents |
| 23-35 | R1 (PGY-1) | Interns |

**Columns:**
- Col 0: Template code (R1, R2, R3)
- Col 1: "PGY X" level
- Col 2: Provider name
- Cols 3+: Half-day assignments (AM/PM pairs)

### Faculty Section (Rows 41-56)

| Row | Faculty Member |
|-----|----------------|
| 41 | Bevis, Zach |
| 42 | Kinkennon, Sarah |
| 43 | Napierala, Joseph |
| 44 | LaBounty, Alex* |
| 45 | McGuire, Chris |
| 46 | Dahl, Brian* |
| 47 | McRae, Zachery |
| 48 | Tagawa, Chelsea |
| 49 | Montgomery, Aaron |
| 50 | (varies) |
| 51 | Van Brunt, T. Blake |
| 52 | Bennett, Nick (IMA)* |
| 53 | Raymond, Tyler (IMA)* |
| 54 | Lamoureux, Anne |
| 55 | Gouthro, Kathryn |
| 56 | Bohringer, Kate |

**Note:** Row positions may shift slightly between blocks. Always verify by checking column 2 for names.

### Other Sections

| Row Range | Content |
|-----------|---------|
| 58-60 | TY/PSYCH/Floats |
| 64-74 | Medical students (USU, MS3, IPAP) |
| 78-79 | CP (Clinical Pharmacist), BHC |
| 82-93 | Metrics and demand calculations |

### Metrics Section (Rows 82-93)

| Row | Label | Purpose |
|-----|-------|---------|
| 82 | Appointments | Day header (THURS, FRI...) |
| 83 | Screeners Needed | Support staff demand |
| 84 | Providers Virtual (CV) | Virtual coverage |
| 85 | Interns in Clinic | PGY-1 clinic count |
| 86 | Residents in Clinic | All residents in clinic |
| 87 | Attendings Needed Clinic | Clinic attending demand |
| 88 | Residents in PROC | Procedures rotation |
| 89 | Residents in V clinic | Virtual clinic |
| 90 | Residents on HV | Home visits |
| **91** | **Total Attendings Needed** | **PRIMARY AT DEMAND** |
| **92** | **# Attendings Assigned** | **CURRENT COVERAGE** |
| 93 | # Primary Care Appts | Appointment count |

## Column Structure

### Date/Time Layout

Each day occupies 2 columns:
- **Odd columns (3, 5, 7...)**: AM half-day
- **Even columns (4, 6, 8...)**: PM half-day

**Example for Aug 1, 2025:**
- Column 5: Aug 1 AM
- Column 6: Aug 1 PM

### Typical 4-Week Block

| Column | Day | Date (example Block 2) |
|--------|-----|------------------------|
| 3-4 | Thu | Jul 31 |
| 5-6 | Fri | Aug 1 |
| 7-8 | Sat | Aug 2 |
| 9-10 | Sun | Aug 3 |
| 11-12 | Mon | Aug 4 |
| 13-14 | Tue | Aug 5 |
| 15-16 | Wed | Aug 6 |
| 17-18 | Thu | Aug 7 |
| ... | ... | ... |
| ~61-62 | Wed | Aug 27 |

**Total columns:** ~70 (varies slightly by block length)

## Reading with Python/openpyxl

```python
from openpyxl import load_workbook

wb = load_workbook('schedule.xlsx')
sheet = wb['Block 7']

# Get faculty name
faculty_name = sheet.cell(row=42, column=3).value  # Kinkennon

# Get staff call for specific date
staff_call = sheet.cell(row=4, column=5).value  # Row 4, Col 5

# Get AT demand for specific day
at_demand = sheet.cell(row=92, column=5).value  # Row 92, Col 5

# Faculty assignment
assignment = sheet.cell(row=42, column=5).value  # Row 42, Col 5 = Kinkennon AM
```

**Note:** openpyxl uses 1-indexed rows/columns, but pandas uses 0-indexed.

## Special Formatting

### Cell Colors (observed)

- Yellow highlight: Attention needed
- Gray: Weekend/blocked
- Red text: Conflict or error

### Merged Cells

Some header cells are merged across AM/PM pairs. Handle carefully when editing.
