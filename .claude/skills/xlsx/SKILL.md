---
name: xlsx
description: Excel spreadsheet import and export for schedules, coverage matrices, and compliance reports. Use when importing schedule data from Excel or generating Excel files for faculty/admin.
---

# Excel Spreadsheet Skill

Comprehensive spreadsheet operations for schedule imports, exports, ACGME compliance reporting, and data analysis.

## When This Skill Activates

- Importing schedules from Excel files
- Exporting schedules to Excel format
- Creating coverage matrices or rotation calendars
- Generating ACGME compliance reports in spreadsheet format
- Analyzing existing Excel data
- Building faculty workload summaries
- Bulk data imports (residents, faculty, rotations)

## Required Libraries

```python
# For data analysis and basic operations
import pandas as pd

# For Excel-specific features (formulas, formatting)
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border
from openpyxl.utils.dataframe import dataframe_to_rows
```

## Core Principles

### 1. Use Formulas, Not Hardcoded Values

```python
# BAD - Hardcoding calculated values
ws['C2'] = 45  # Total hours

# GOOD - Use Excel formulas
ws['C2'] = '=SUM(A2:B2)'
```

### 2. Pandas for Analysis, openpyxl for Excel Features

```python
# Use pandas for data manipulation
df = pd.read_excel('schedule.xlsx')
summary = df.groupby('rotation').sum()

# Use openpyxl for formatting and formulas
wb = load_workbook('schedule.xlsx')
ws = wb.active
ws['A1'].font = Font(bold=True)
```

### 3. Cell Indices Are 1-Based

```python
# openpyxl uses 1-based indexing
ws.cell(row=1, column=1, value="Header")  # A1, not A0
```

## Schedule Export Patterns

### Weekly Schedule Export

```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from datetime import date, timedelta

def export_weekly_schedule(assignments: list, start_date: date) -> Workbook:
    """Export weekly schedule to Excel format."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Weekly Schedule"

    # Header row
    headers = ["Name", "Role"] + [
        (start_date + timedelta(days=i)).strftime("%a %m/%d")
        for i in range(7)
    ]

    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="366092", fill_type="solid")
        cell.font = Font(bold=True, color="FFFFFF")

    # Data rows
    for row_idx, assignment in enumerate(assignments, 2):
        ws.cell(row=row_idx, column=1, value=assignment.person_name)
        ws.cell(row=row_idx, column=2, value=assignment.role)
        # ... populate daily assignments

    # Auto-adjust column widths
    for column in ws.columns:
        max_length = max(len(str(cell.value or "")) for cell in column)
        ws.column_dimensions[column[0].column_letter].width = max_length + 2

    return wb
```

### Coverage Matrix

```python
def create_coverage_matrix(rotations: list, dates: list) -> Workbook:
    """Create rotation coverage matrix."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Coverage Matrix"

    # Rotation names in column A
    for row, rotation in enumerate(rotations, 2):
        ws.cell(row=row, column=1, value=rotation.name)

    # Dates across top row
    for col, date in enumerate(dates, 2):
        ws.cell(row=1, column=col, value=date.strftime("%m/%d"))

    # Coverage counts with conditional formatting
    # Use formulas for totals
    total_row = len(rotations) + 2
    for col in range(2, len(dates) + 2):
        col_letter = ws.cell(row=1, column=col).column_letter
        ws.cell(
            row=total_row,
            column=col,
            value=f'=SUM({col_letter}2:{col_letter}{total_row-1})'
        )

    return wb
```

## ACGME Compliance Report

```python
def create_compliance_report(residents: list, period_start: date, period_end: date) -> Workbook:
    """Generate ACGME compliance summary."""
    wb = Workbook()
    ws = wb.active
    ws.title = "ACGME Compliance"

    # Headers
    headers = [
        "Resident", "PGY Level",
        "Avg Weekly Hours", "80hr Compliant",
        "Days Off (1-in-7)", "1-in-7 Compliant",
        "Supervision Ratio", "Supervision Compliant"
    ]

    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = Font(bold=True)

    # Compliance status formatting
    green_fill = PatternFill(start_color="90EE90", fill_type="solid")
    red_fill = PatternFill(start_color="FFB6C1", fill_type="solid")

    for row, resident in enumerate(residents, 2):
        ws.cell(row=row, column=1, value=resident.name)
        ws.cell(row=row, column=2, value=f"PGY-{resident.pgy_level}")

        # Hours compliance
        hours_cell = ws.cell(row=row, column=3, value=resident.avg_weekly_hours)
        compliant_cell = ws.cell(row=row, column=4)
        compliant_cell.value = "Yes" if resident.avg_weekly_hours <= 80 else "No"
        compliant_cell.fill = green_fill if resident.avg_weekly_hours <= 80 else red_fill

        # ... additional compliance checks

    return wb
```

## Reading Excel Files

```python
# Read with pandas for analysis
df = pd.read_excel('schedule.xlsx', sheet_name='Sheet1')

# Read with openpyxl for formulas
wb = load_workbook('schedule.xlsx')
ws = wb.active

# WARNING: data_only=True reads calculated values but loses formulas
# Only use for read-only analysis
wb_values = load_workbook('schedule.xlsx', data_only=True)
```

## Schedule Import Patterns

### Bulk Resident Import

```python
from pydantic import ValidationError
from app.schemas.person import PersonCreate

async def import_residents_from_excel(
    file_path: str,
    db: AsyncSession
) -> tuple[list[Person], list[dict]]:
    """
    Import residents from Excel file.

    Expected columns: Name, Email, PGY Level, Start Date, Specialty

    Returns:
        Tuple of (created_persons, errors)
    """
    df = pd.read_excel(file_path)

    # Normalize column names
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

    created = []
    errors = []

    for idx, row in df.iterrows():
        try:
            person_data = PersonCreate(
                name=row['name'],
                email=row['email'],
                pgy_level=int(row['pgy_level']),
                start_date=pd.to_datetime(row['start_date']).date(),
                specialty=row.get('specialty', 'General'),
                role='RESIDENT'
            )

            person = await create_person(db, person_data)
            created.append(person)

        except (ValidationError, KeyError, ValueError) as e:
            errors.append({
                'row': idx + 2,  # Excel row (1-indexed + header)
                'data': row.to_dict(),
                'error': str(e)
            })

    return created, errors
```

### Schedule Assignment Import

```python
from datetime import datetime

async def import_schedule_from_excel(
    file_path: str,
    db: AsyncSession,
    schedule_id: str
) -> tuple[list[Assignment], list[dict]]:
    """
    Import schedule assignments from Excel.

    Expected format:
    - Row 1: Headers (Name, then dates across columns)
    - Column A: Person names
    - Cells: Rotation abbreviations (e.g., "CLINIC", "ICU", "OFF")

    Returns:
        Tuple of (created_assignments, errors)
    """
    wb = load_workbook(file_path, data_only=True)
    ws = wb.active

    # Parse header row for dates
    dates = []
    for col in range(2, ws.max_column + 1):
        date_val = ws.cell(row=1, column=col).value
        if isinstance(date_val, datetime):
            dates.append(date_val.date())
        elif isinstance(date_val, str):
            dates.append(datetime.strptime(date_val, "%m/%d/%Y").date())

    created = []
    errors = []

    # Parse data rows
    for row in range(2, ws.max_row + 1):
        person_name = ws.cell(row=row, column=1).value
        if not person_name:
            continue

        # Look up person
        person = await get_person_by_name(db, person_name)
        if not person:
            errors.append({
                'row': row,
                'error': f"Person not found: {person_name}"
            })
            continue

        # Parse assignments for each date
        for col_idx, date in enumerate(dates, start=2):
            rotation_code = ws.cell(row=row, column=col_idx).value
            if not rotation_code or rotation_code.upper() == "OFF":
                continue

            try:
                assignment = await create_assignment(
                    db,
                    AssignmentCreate(
                        person_id=person.id,
                        schedule_id=schedule_id,
                        date=date,
                        rotation_code=rotation_code
                    )
                )
                created.append(assignment)

            except Exception as e:
                errors.append({
                    'row': row,
                    'column': col_idx,
                    'date': str(date),
                    'error': str(e)
                })

    return created, errors
```

### Import Validation Helpers

```python
def validate_import_headers(
    df: pd.DataFrame,
    required_columns: list[str]
) -> list[str]:
    """Validate that required columns exist."""
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
    missing = [col for col in required_columns if col not in df.columns]
    return missing


def detect_date_format(date_str: str) -> str:
    """Detect date format from sample string."""
    formats = [
        "%m/%d/%Y", "%Y-%m-%d", "%d/%m/%Y",
        "%m-%d-%Y", "%Y/%m/%d", "%d-%m-%Y"
    ]
    for fmt in formats:
        try:
            datetime.strptime(date_str, fmt)
            return fmt
        except ValueError:
            continue
    raise ValueError(f"Unknown date format: {date_str}")


def clean_cell_value(value) -> str:
    """Clean and normalize cell values."""
    if pd.isna(value) or value is None:
        return ""
    return str(value).strip()
```

### Import Endpoint Pattern

```python
from fastapi import APIRouter, UploadFile, File
from tempfile import NamedTemporaryFile

router = APIRouter()

@router.post("/schedules/{schedule_id}/import/xlsx")
async def import_schedule_xlsx(
    schedule_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Import schedule from Excel file."""
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(400, "File must be Excel format (.xlsx or .xls)")

    # Save to temp file
    with NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        created, errors = await import_schedule_from_excel(
            tmp_path, db, schedule_id
        )

        return {
            "imported": len(created),
            "errors": len(errors),
            "error_details": errors[:10]  # First 10 errors
        }
    finally:
        os.unlink(tmp_path)
```

## Formula Error Checking

Always verify no formula errors exist:

```python
ERROR_PATTERNS = ['#REF!', '#DIV/0!', '#VALUE!', '#N/A', '#NAME?', '#NULL!']

def check_formula_errors(ws) -> list:
    """Check worksheet for formula errors."""
    errors = []
    for row in ws.iter_rows():
        for cell in row:
            if cell.value and str(cell.value) in ERROR_PATTERNS:
                errors.append(f"{cell.coordinate}: {cell.value}")
    return errors
```

## Style Guidelines

### Color Coding (Financial Model Standard)

| Color | Meaning |
|-------|---------|
| Blue text | User inputs / editable |
| Black text | Formulas / calculated |
| Green text | Links to other sheets |
| Yellow background | Key assumptions |

### Number Formatting

```python
from openpyxl.styles.numbers import FORMAT_PERCENTAGE, FORMAT_NUMBER_COMMA_SEPARATED1

# Hours
cell.number_format = '0.0'

# Percentages
cell.number_format = '0.0%'

# Currency
cell.number_format = '"$"#,##0.00'

# Dates
cell.number_format = 'MM/DD/YYYY'
```

## Integration with Project

### Export Endpoint Pattern

```python
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from io import BytesIO

router = APIRouter()

@router.get("/schedules/{schedule_id}/export/xlsx")
async def export_schedule_xlsx(schedule_id: str, db: AsyncSession = Depends(get_db)):
    """Export schedule to Excel format."""
    schedule = await get_schedule(db, schedule_id)
    wb = create_schedule_workbook(schedule)

    # Stream response
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=schedule_{schedule_id}.xlsx"}
    )
```

## Verification Checklist

Before finalizing any Excel export:

- [ ] All formulas calculate correctly (no #REF!, #DIV/0!, etc.)
- [ ] Column widths accommodate content
- [ ] Headers are bold and clearly formatted
- [ ] Data validation applied where appropriate
- [ ] Sheet names are descriptive
- [ ] No sensitive data (names sanitized for external sharing)

## References

- [openpyxl Documentation](https://openpyxl.readthedocs.io/)
- [pandas Excel Support](https://pandas.pydata.org/docs/reference/api/pandas.read_excel.html)
- Project exports: `backend/app/services/exports/`
