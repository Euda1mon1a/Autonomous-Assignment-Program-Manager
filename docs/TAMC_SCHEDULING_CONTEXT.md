# TAMC Family Medicine Residency Scheduling - Complete Context

This document captures all discovered context about the TAMC (Tripler Army Medical Center) Family Medicine Residency scheduling system, Excel workbook structure, constraints, and intricacies learned during schedule generation sessions.

## Table of Contents
1. [Excel Workbook Structure](#excel-workbook-structure)
2. [Block Template2 Sheet Layout](#block-template2-sheet-layout)
3. [Faculty System](#faculty-system)
4. [Resident System](#resident-system)
5. [Constraint Hierarchy](#constraint-hierarchy)
6. [Code Dictionary](#code-dictionary)
7. [Critical Distinctions](#critical-distinctions)
8. [Scheduling Workflow](#scheduling-workflow)
9. [Validation Requirements](#validation-requirements)

---

## Excel Workbook Structure

### Sheets Overview
| Sheet Name | Purpose |
|------------|---------|
| **Block Template2** | Working schedule document - primary editing target |
| **Templates** | Rotation templates defining AM/PM patterns by PGY level |
| **FMIT Attending (2025-2026)** | Weekly FMIT faculty assignments |
| Other sheets | Reference data, historical records |

### Block Template2 - The Core Schedule

This is the primary working document. All schedule generation targets this sheet.

---

## Block Template2 Sheet Layout

### Row Structure

| Row Range | Content | Notes |
|-----------|---------|-------|
| **1** | Block number, Day names | THURS, FRI, SAT, SUN, MON... |
| **2** | Day abbreviations | THU, FRI, SAT... |
| **3** | Dates | Actual dates (e.g., 2025-03-12) |
| **4** | **Staff Call** | Faculty name when on call that night |
| **5** | Resident Call | Resident on call |
| **6** | Headers | TEMPLATE, ROLE, PROVIDER |
| **9-13** | PGY-3 Residents (R3) | Senior residents |
| **14-19** | PGY-2 Residents (R2) | Second-year residents |
| **20-25** | PGY-1 Residents (R1) | Interns |
| **31-43** | Faculty | C19/FAC, ADJ/FAC, SPEC/PSY |
| **49-53** | TY/Float/SM | Transitional year, floats |
| **55-65** | Medical Students | USU, IPAP, MS |
| **67-68** | CP/BHC | Pharmacist, Behavioral Health |
| **71-82** | Metrics | Calculated fields |

### Column Structure

| Column | Content |
|--------|---------|
| **1** | First-half rotation (e.g., "FMC", "FMIT 2", "Hilo") |
| **2** | Second-half rotation (if mid-block switch) |
| **3** | Template code (R1, R2, R3, C19, ADJ, etc.) |
| **4** | Role (PGY 1, PGY 2, PGY 3, FAC, etc.) |
| **5** | Provider name |
| **6+** | Half-day slots (AM/PM pairs per day) |

### Column-to-Date Mapping (Block 10 Example: Mar 12 - Apr 8, 2026)

Each date uses 2 columns: **Even = AM**, **Odd = PM**

| Columns | Date | Day | Week | Notes |
|---------|------|-----|------|-------|
| 6-7 | Mar 12 | Thu | 1 | Block start |
| 8-9 | Mar 13 | Fri | 1 | |
| 10-11 | Mar 14 | Sat | 1 | Weekend (W) |
| 12-13 | Mar 15 | Sun | 1 | Weekend (W) |
| 14-15 | Mar 16 | Mon | 2 | |
| 16-17 | Mar 17 | Tue | 2 | |
| 18-19 | Mar 18 | Wed | 2 | **LEC col 19** |
| 20-21 | Mar 19 | Thu | 2 | |
| 22-23 | Mar 20 | Fri | 2 | |
| 24-25 | Mar 21 | Sat | 2 | Weekend (W) |
| 26-27 | Mar 22 | Sun | 2 | Weekend (W) |
| **28-29** | Mar 23 | Mon | 3 | **MID-BLOCK TRANSITION** |
| 30-31 | Mar 24 | Tue | 3 | |
| 32-33 | Mar 25 | Wed | 3 | **LEC col 33** |
| 34-35 | Mar 26 | Thu | 3 | |
| 36-37 | Mar 27 | Fri | 3 | |
| 38-39 | Mar 28 | Sat | 3 | Weekend (W) |
| 40-41 | Mar 29 | Sun | 3 | Weekend (W) |
| 42-43 | Mar 30 | Mon | 4 | |
| 44-45 | Mar 31 | Tue | 4 | |
| 46-47 | Apr 01 | Wed | 4 | **LEC col 47** |
| 48-49 | Apr 02 | Thu | 4 | |
| 50-51 | Apr 03 | Fri | 4 | |
| 52-53 | Apr 04 | Sat | 4 | Weekend (W) |
| 54-55 | Apr 05 | Sun | 4 | Weekend (W) |
| 56-57 | Apr 06 | Mon | 5 | |
| 58-59 | Apr 07 | Tue | 5 | |
| 60-61 | Apr 08 | Wed | 5 | **LEC col 61**, Block end |

### Special Column Sets

```python
WEEKEND_COLS = {10, 11, 12, 13, 24, 25, 26, 27, 38, 39, 40, 41, 52, 53, 54, 55}
LEC_COLS = {19, 33, 47, 61}  # Wednesday PM - protected didactics
WED_AM_COLS = {18, 32, 46, 60}  # Wednesday AM - intern continuity
MID_BLOCK_COL = 28  # Column where second-half rotation begins
```

---

## Faculty System

### Faculty Roster (Rows 31-43)

| Row | Template | Name | Min C/wk | Max C/wk | Admin | Notes |
|-----|----------|------|----------|----------|-------|-------|
| 31 | C19/FAC | Bevis, Zach | 0 | 0 | GME | APD, 100% admin |
| 32 | C19/FAC | Kinkennon, Sarah | 2 | 4 | GME | |
| 33 | C19/FAC | LaBounty, Alex* | 2 | 4 | GME | |
| 34 | C19/FAC | McGuire, Chris | 1 | 1 | DFM | 90% DFM admin |
| 35 | C19/FAC | Dahl, Brian* | 0 | 0 | GME | OUT Dec-Jun |
| 36 | C19/FAC | McRae, Zachery | 2 | 4 | GME | |
| 37 | C19/FAC | Tagawa, Chelsea | 0 | 0 | SM/AT | Sports Med faculty |
| 38 | C19/FAC | Montgomery, Aaron | 2 | 2 | GME | |
| 39 | C19/FAC | Colgan, Bridget | 0 | 0 | GME | DEP (deployed) |
| 40 | C19/FAC | Chu, Jimmy* | 0 | 0 | GME | FMIT weeks only |
| 41 | ADJ/FAC | Napierala, Joseph | 0 | 0 | GME | FMIT/Call only |
| 42 | ADJ/FAC | Van Brunt, T. Blake | 0 | 0 | GME | FMIT/Call only |
| 43 | SPEC/PSY | Lamoureux, Anne | 2 | 2 | GME | Psychiatry |

### Faculty Call Pools

**AUTO-ASSIGN Pool** (Mon-Thu, Sun):
- KINKENNON, MCGUIRE, MCRAE, MONTGOMERY, TAGAWA

**MANUAL-ONLY Pool** (assigned by hand):
- NAPIERALA, VAN BRUNT, LAMOUREUX

### Special Faculty Rules

| Faculty | Special Rule |
|---------|--------------|
| **Chu** | Week-on/week-off FMIT; no Sun-Thu call during "off" weeks |
| **Bevis** | Available for call starting next week after post-FMIT |
| **LaBounty** | No call in week immediately preceding FMIT |
| **Tagawa** | Sports Medicine faculty; does SM not C; can do AT when not on SM |

---

## Resident System

### Resident Roster by PGY Level

#### PGY-3 (Rows 9-13)
| Row | Name | Notes |
|-----|------|-------|
| 9 | Connolly, Laura | Often Hilo (TDY) |
| 10 | Hernandez, Christian* | |
| 11 | Mayell, Cameron* | |
| 12 | Petrie, William* | |
| 13 | You, Jae* | |

#### PGY-2 (Rows 14-19)
| Row | Name | Notes |
|-----|------|-------|
| 14 | Cataquiz, Felipe | |
| 15 | Cook, Scott | Often SM rotation |
| 16 | Gigon, Alaine | |
| 17 | Headid, Ronald | |
| 18 | Maher, Nicholas | |
| 19 | Thomas, Devin | |

#### PGY-1 / Interns (Rows 20-25)
| Row | Name | Notes |
|-----|------|-------|
| 20 | Sawyer, Tessa | |
| 21 | Wilhelm, Clara | |
| 22 | Travis, Colin | |
| 23 | Byrnes, Katherine | |
| 24 | Sloss, Meleighe | |
| 25 | Monsivais, Joshua | |

### Rotation Templates

Templates are in the "Templates" sheet. Key structure:
- Row 3-14: PGY-3 rotations
- Row 17-30: PGY-2 rotations
- Row 33-52: PGY-1 rotations

Each template shows AM/PM codes for a standard week (Thu-Wed).

### Rotation Code Mapping

| Rotation | AM Code | PM Code | Notes |
|----------|---------|---------|-------|
| **Hilo** | TDY | TDY | Off-site, entire block |
| **NF (Night Float)** | OFF | NF | Works nights |
| **FMC** | C | C/CV | High clinic load |
| **FMIT / FMIT 2** | FMIT | FMIT | Inpatient team |
| **NEURO** | NEURO | C | Elective + clinic |
| **SM (Sports Med)** | SM | C | SM + clinic |
| **POCUS** | US | C | Ultrasound + clinic |
| **L&D Night Float** | L&D | L&D | Labor & Delivery |
| **Surg Exp** | SURG | C | Surgery + clinic |
| **Gyn Clinic** | GYN | C | Gynecology + clinic |
| **Peds Ward** | PedW | PedW | Pediatrics inpatient |
| **Peds NF** | OFF | PedNF | Peds night float |
| **Kapiolani L&D** | KAP | KAP | Off-site L&D |
| **PROC** | PR | C | Procedures + clinic |
| **IM** | IM | IM | Internal Medicine |

### Mid-Block Rotation Transitions

Some residents switch rotations at **column 28** (start of week 3):
- Check column 1 for first-half rotation
- Check column 2 for second-half rotation (if different)

```python
def get_rotation(col, rot1, rot2):
    if rot2 and col >= 28:
        return rot2
    return rot1
```

---

## Constraint Hierarchy

### HARD Constraints (Cannot Violate)

1. **ACGME Supervision Ratios**
   - AT coverage >= ceil(AT demand)
   - Highest priority - schedule is INVALID if violated

2. **Physical Clinic Capacity**
   - Max 6 clinical workers per half-day slot
   - Clinical = residents + faculty doing C (not AT)

3. **Intern Continuity Clinic (Wednesday AM)**
   - PGY-1 interns must have C on Wednesday mornings
   - Protected time for panel patients
   - Exceptions: NF, Peds NF, off-site (Hilo, Kapiolani), OB

4. **FMIT Blocking**
   - FMIT faculty cannot do clinic during FMIT week
   - Cannot be on Sun-Thu call during FMIT

5. **Post-Call (PCAT/DO)**
   - Non-FMIT call requires next day: AM=PCAT, PM=DO

6. **No Back-to-Back Call**
   - Cannot be on call consecutive nights

7. **One Faculty Per Call Night**
   - Exactly one faculty assigned each night

8. **SM Requires Tagawa**
   - If resident has SM, Tagawa must also have SM
   - If Tagawa blocked, resident cannot do SM

### SOFT Constraints (Optimize/Warn)

1. **Faculty Weekly C Caps (MIN and MAX)**
   - MIN: Flag for PD review if unmet
   - MAX: Hard cap, cannot exceed

2. **Call Equity**
   - Distribute call evenly across faculty
   - Sunday calls tracked separately

3. **Tagawa SM Target**
   - 3-4 SM slots per week preferred

4. **Full-Day Preferences**
   - Faculty prefer full-day C or full-day GME
   - Avoid split days when possible

---

## Code Dictionary

### Faculty Codes

| Code | Meaning | Counts as AT? | Counts as Clinical? |
|------|---------|---------------|---------------------|
| **C** | Clinic (seeing own patients) | YES | YES |
| **AT** | Attending (supervising residents) | YES | NO |
| **PCAT** | Post-Call Admin Time | YES | NO |
| **DO** | Day Off (post-call PM) | NO | NO |
| **GME** | Graduate Medical Education admin | NO | NO |
| **DFM** | Dept of Family Medicine admin | NO | NO |
| **SM** | Sports Medicine | YES (Tagawa) | NO |
| **FMIT** | FM Inpatient Team | NO | NO |
| **PC** | Post-FMIT Friday off | NO | NO |
| **LV** | Leave | NO | NO |
| **W** | Weekend | NO | NO |
| **USAFP** | USAFP Conference | NO | NO |
| **HAFP** | Hawaii AFP Conference | NO | NO |
| **DEP** | Deployed | NO | NO |

### Resident Codes

| Code | Meaning | AT Weight |
|------|---------|-----------|
| **C** | Clinic | PGY-1: 0.5, PGY-2/3: 0.25 |
| **C30/C40/C60** | Clinic with appointment length | Same as C |
| **CV** | Virtual Clinic | Same as C |
| **PR** | Procedures | 1.0 (dedicated AT) |
| **VAS** | Vascular | 1.0 (dedicated AT) |
| **FMIT** | FM Inpatient Team | 0 (not in clinic) |
| **NF** | Night Float | 0 |
| **OFF** | Day Off | 0 |
| **TDY** | Temporary Duty (off-site) | 0 |
| **LV** | Leave | 0 |
| **W** | Weekend | 0 |
| **LEC** | Lecture (Wed PM) | 0 |
| **SM** | Sports Medicine | Covered by Tagawa |
| **aSM** | Academic Sports Med | Teaching, not clinic |

### Pre-Blocked Codes (Never Overwrite)

```python
BLOCKED_CODES = {
    'FMIT', 'LV', 'W', 'PC', 'LEC', 'SIM', 'HAFP', 'BLS',
    'PCAT', 'DO', 'USAFP', 'DEP', 'aSM', 'PI', 'MM?', 'MM',
    'HOL', 'HC', 'TDY'
}
```

---

## Critical Distinctions

### C vs AT - THE MOST IMPORTANT DISTINCTION

| Aspect | C (Clinic) | AT (Attending) |
|--------|------------|----------------|
| **Definition** | Faculty seeing OWN patients | Faculty SUPERVISING residents |
| **Weekly Cap** | MIN and MAX apply | NO CAP (unlimited) |
| **Physical Clinic** | Counts toward ≤6 limit | Does NOT count |
| **When to Use** | Faculty has patient appointments | Faculty precepting residents |

**Key Insight:** If staffing is critical, faculty can do AT all day every day. AT has no cap because supervision doesn't generate additional patient load.

### Intern Continuity vs Senior Flexibility

| PGY Level | Wednesday AM | Reason |
|-----------|--------------|--------|
| **PGY-1** | Always C (unless exception) | Panel patient continuity |
| **PGY-2/3** | Varies by rotation | No continuity requirement |

Senior rotation Wednesday AM patterns:
- FMC (R3): ADM
- FMC (R2): FLX
- Procedures: SIM
- Sports Med: aSM

### Templates as Guidelines

Rotation templates are **GUIDELINES**, not strict rules. The actual schedule may vary based on:
- Faculty availability
- AT demand needs
- Call/post-call blocking
- Conference/educational requirements
- Physical clinic capacity

---

## Scheduling Workflow

### Step 1: Load Non-Negotiables
- Absences (LV)
- FMIT assignments
- Conferences (HAFP, USAFP)
- Holidays (HOL)
- Protected time (LEC, SIM)

### Step 2: Apply Call Schedule
- Assign Sun-Thu call equitably
- Apply PCAT/DO for non-FMIT call
- Track Sunday calls separately

### Step 3: Load Resident Templates
- Apply rotation patterns from columns 1-2
- Handle mid-block transitions at column 28
- Ensure LEC on all Wednesday PMs

### Step 4: Fix Intern Continuity
- Set all PGY-1 Wednesday AM to C (unless exception)
- Check for physical clinic overflow

### Step 5: Calculate AT Demand
```
AT Demand = (PGY-1 count × 0.5) + (PGY-2/3 count × 0.25) + (PROC/VAS count × 1.0)
Round UP to integer
```

### Step 6: Assign Faculty Coverage
- Assign C where physical clinic < 6
- Assign AT where coverage needed but clinic full
- Respect MIN/MAX caps for C

### Step 7: Fill Admin Time
- GME for most faculty
- DFM for McGuire
- Fill remaining empty slots

### Step 8: Validate All Constraints
- Run validation checklist
- Flag warnings for PD review

---

## Validation Requirements

### Validation Checklist

- [ ] **ACGME: AT coverage >= AT demand for every slot**
- [ ] **Physical clinic: ≤6 people doing clinical work per slot**
- [ ] **PGY-1 interns have Continuity Clinic on Wednesday AM**
- [ ] No faculty exceeds weekly C cap (MIN and MAX)
- [ ] Post-call blocks (PCAT/DO) applied correctly
- [ ] FMIT faculty have no C on FMIT days
- [ ] No assignments on weekends (W columns)
- [ ] LEC on all Wednesday PM slots
- [ ] Resident rotations match column 1/2 rotation names
- [ ] Mid-block transitions applied at column 28
- [ ] Pre-blocked codes not overwritten
- [ ] SM slots have both Tagawa and resident
- [ ] Sunday call distributed (max 1 per faculty)
- [ ] No back-to-back call for any faculty

### AT Demand Calculation

```python
def calculate_at_demand(sheet, col):
    """Calculate AT demand for a half-day slot"""
    CLINICAL_CODES = {'C', 'C30', 'C40', 'C60', 'CV', 'PR', 'VAS'}

    demand = 0

    # PGY-1 (rows 20-25): 0.5 each
    for row in range(20, 26):
        val = sheet.cell(row=row, column=col).value
        if val in CLINICAL_CODES:
            demand += 0.5

    # PGY-2 (rows 14-19): 0.25 each, PROC/VAS = 1.0
    for row in range(14, 20):
        val = sheet.cell(row=row, column=col).value
        if val in ['PR', 'VAS']:
            demand += 1.0
        elif val in CLINICAL_CODES:
            demand += 0.25

    # PGY-3 (rows 9-13): 0.25 each
    for row in range(9, 14):
        val = sheet.cell(row=row, column=col).value
        if val in CLINICAL_CODES:
            demand += 0.25

    return math.ceil(demand)
```

### Physical Clinic Count

```python
def count_clinical_workers(sheet, col):
    """Count people doing clinical work (generating patients)"""
    CLINICAL_CODES = {'C', 'C30', 'C40', 'C60', 'CV', 'PR', 'VAS'}

    count = 0

    # Residents
    for row in range(9, 26):
        val = sheet.cell(row=row, column=col).value
        if val and str(val).upper() in [c.upper() for c in CLINICAL_CODES]:
            count += 1

    # Faculty (only C counts, not AT)
    for row in range(31, 44):
        val = sheet.cell(row=row, column=col).value
        if val == 'C':
            count += 1

    return count
```

---

## Common Issues and Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| "Not enough AT coverage" | Faculty on leave/conference | Reduce resident clinic or call in additional faculty |
| "Physical clinic > 6" | Too many people in clinic | Convert faculty C to AT |
| "Faculty MIN C not met" | Conference week, limited slots | Flag as WARN for PD review |
| "Intern missing Wed AM clinic" | Wrong rotation code applied | Check template, set to C |
| "SM without Tagawa" | Tagawa blocked that slot | Change resident SM to C |
| "PCAT/DO missing" | Forgot to apply post-call | Check call schedule, apply PCAT AM + DO PM |
| "Wrong mid-block rotation" | Didn't check column 2 | Use `get_rotation()` with mid-block check |

---

## Appendix: Python Code Reference

### Faculty Configuration
```python
FACULTY = {
    'Bevis': {'row': 31, 'min_c': 0, 'max_c': 0, 'admin': 'GME'},
    'Kinkennon': {'row': 32, 'min_c': 2, 'max_c': 4, 'admin': 'GME'},
    'LaBounty': {'row': 33, 'min_c': 2, 'max_c': 4, 'admin': 'GME'},
    'McGuire': {'row': 34, 'min_c': 1, 'max_c': 1, 'admin': 'DFM'},
    'Dahl': {'row': 35, 'min_c': 0, 'max_c': 0, 'admin': 'GME'},
    'McRae': {'row': 36, 'min_c': 2, 'max_c': 4, 'admin': 'GME'},
    'Tagawa': {'row': 37, 'min_c': 0, 'max_c': 0, 'admin': 'GME'},
    'Montgomery': {'row': 38, 'min_c': 2, 'max_c': 2, 'admin': 'GME'},
    'Colgan': {'row': 39, 'min_c': 0, 'max_c': 0, 'admin': 'GME'},
    'Chu': {'row': 40, 'min_c': 0, 'max_c': 0, 'admin': 'GME'},
    'Napierala': {'row': 41, 'min_c': 0, 'max_c': 0, 'admin': 'GME'},
    'Van Brunt': {'row': 42, 'min_c': 0, 'max_c': 0, 'admin': 'GME'},
    'Lamoureux': {'row': 43, 'min_c': 2, 'max_c': 2, 'admin': 'GME'},
}
```

### Week Boundaries
```python
WEEKS = [
    (1, 6, 13, "Week 1"),    # Thu-Sun
    (2, 14, 27, "Week 2"),   # Mon-Sun
    (3, 28, 41, "Week 3"),   # Mon-Sun (mid-block transition)
    (4, 42, 55, "Week 4"),   # Mon-Sun
    (5, 56, 61, "Week 5"),   # Mon-Wed (partial)
]
```

---

*Document generated from scheduling session context - January 2026*
