# Importing Data

Import schedules and data into Residency Scheduler from Excel files.

---

## Web Interface (Recommended)

The easiest way to import data is through the **Import/Export** page:

1. Navigate to **Import/Export** in the main navigation
2. Click the **Import** tab
3. Click **Start Import**
4. Select your file (CSV, Excel, or JSON)
5. Preview the data and fix any validation errors
6. Click **Import** to complete

The web interface provides:
- Real-time validation with error highlighting
- Preview before importing
- Progress tracking for large imports
- Automatic duplicate detection

### Half-Day Block Template2 (Draft Flow)

For Block Template2 half-day schedules, the system stages diffs before drafting:

1. Upload the workbook (Block Template2 sheet).
2. Review the diff preview (slot-level changes).
3. Create a schedule draft from selected rows.

Notes:
- Draft creation is **atomic**: if any selected row fails validation, the draft is not created.
- The draft response includes `failed_ids` (staged row IDs that failed). On failure, the `400` error detail includes the same list.

### Supported File Formats

| Format | Extension | Features |
|--------|-----------|----------|
| **Excel** | `.xlsx`, `.xls` | Full support including date conversion, color-coded cells (backend parsing) |
| **CSV** | `.csv` | Standard comma-separated values |
| **JSON** | `.json` | Array of objects format |

### Excel Parsing Architecture

Excel files are parsed using a **backend-first approach** with client-side fallback:

1. **Primary (Backend)**: Uses `openpyxl` for full Excel support including:
   - Date cell conversion to ISO format
   - Merged cell handling
   - Cell color detection (for color-coded schedules)
   - Duplicate header detection
   - Empty row filtering

2. **Fallback (Client-Side)**: If the backend is unavailable, uses SheetJS:
   - Basic cell value extraction
   - Date handling
   - A warning banner will appear when using fallback mode

!!! note "Color-Coded Schedules"
    If your Excel files use color coding (e.g., yellow for FMIT, red for vacation),
    the backend parser can detect these. The client-side fallback cannot read colors.

---

## Command Line Import

For advanced users and automation, use the Excel import script.

### Overview

The Excel import script (`scripts/import_excel.py`) allows you to bulk import:

- **Absences/Leave** - Vacation, sick, deployment, TDY, conference, etc.
- **Pre-assigned Rotations** - Schedule assignments from legacy systems

This is useful for:
- Initial data migration from spreadsheets
- Bulk leave entry from HR systems
- Importing schedules from external sources

---

## Prerequisites

Before importing:

1. **People must exist** in the database (residents and faculty)
2. **Rotation templates** must be configured (for schedule imports)
3. **Blocks** must be generated for the date range (for schedule imports)

---

## Excel File Format

### Absence/Leave Sheet

The importer auto-detects sheets containing absence data. Required columns:

| Column | Description | Example |
|--------|-------------|---------|
| **Person/Name** | Person's name | Dr. Sarah Johnson |
| **Type** | Absence type or abbreviation | VAC, SICK, DEP |
| **Start Date** | First day of absence | 2024-01-15 |
| **End Date** | Last day of absence | 2024-01-19 |
| **Notes** (optional) | Additional notes | Family vacation |
| **TDY Location** (optional) | For TDY absences | Fort Bragg |

### Absence Type Abbreviations

| Abbreviation | Full Type |
|--------------|-----------|
| VAC | Vacation |
| SICK | Sick Leave |
| MED | Medical Leave |
| CONF | Conference |
| DEP | Military Deployment |
| TDY | Temporary Duty |
| FEM | Family Emergency |
| PER | Personal |
| BER | Bereavement |
| MAT/PAT | Maternity/Paternity |

### Schedule Sheet (Legacy Format)

For importing from the legacy Excel format exported by `xlsx_export.py`:

- AM/PM columns per day
- Person names in column E
- Dates in row 3
- Rotation abbreviations in cells

---

## Name Matching

The importer uses intelligent name matching:

| Input | Matches |
|-------|---------|
| `Dr. Sarah Johnson` | Sarah Johnson |
| `SARAH JOHNSON` | Sarah Johnson |
| `Johnson, Sarah` | Sarah Johnson |
| `Dr. Sarah Johnson, MD` | Sarah Johnson |

!!! tip "Matching Tips"
    - Names are matched case-insensitively
    - "Dr.", "Mr.", "Mrs.", prefixes are ignored
    - ", MD", ", DO" suffixes are removed
    - "Last, First" format is converted to "First Last"

---

## Date Formats

The importer recognizes multiple date formats:

| Format | Example |
|--------|---------|
| ISO | 2024-01-15 |
| US | 01/15/2024 |
| Short US | 01/15/24 |
| European | 15/01/2024 |
| German | 15.01.2024 |
| Text | Jan 15, 2024 |
| Text Full | 15-January-2024 |

---

## Running the Import

### Basic Usage

```bash
cd /path/to/project
python scripts/import_excel.py schedule.xlsx
```

### Dry Run (Recommended First)

Always run with `--dry-run` first to validate data:

```bash
python scripts/import_excel.py absences.xlsx --dry-run
```

This parses the file and reports what would be imported without making changes.

### Verbose Mode

For detailed logging:

```bash
python scripts/import_excel.py data.xlsx --verbose
```

### Custom Database

To use a specific database:

```bash
python scripts/import_excel.py data.xlsx --database-url "postgresql://user:pass@host/db"
```

---

## Command Reference

```
usage: import_excel.py [-h] [--dry-run] [--verbose] [--database-url URL] file

positional arguments:
  file                  Path to the Excel file to import

options:
  -h, --help            Show help message
  --dry-run             Validate without creating records
  --verbose, -v         Enable detailed logging
  --database-url URL    Database connection string
```

---

## Import Results

After running, you'll see a summary:

```
============================================================
IMPORT SUMMARY
============================================================

Absences:
  Created: 45
  Skipped: 3
  Errors:  2

------------------------------------------------------------
TOTAL: Created 45, Skipped 3, Errors 2
```

- **Created**: New records successfully added
- **Skipped**: Duplicates (already exist in database)
- **Errors**: Failed rows (person not found, invalid dates, etc.)

---

## Duplicate Detection

The importer automatically detects and skips duplicates:

- **Absences**: Same person + type + start date + end date
- **Assignments**: Same person + block (date + AM/PM)

!!! info "Safe to Re-run"
    You can safely re-run an import multiple times. Existing records
    will be skipped, and only new data will be added.

---

## Error Handling

Common errors and solutions:

| Error | Cause | Solution |
|-------|-------|----------|
| Person not found | Name doesn't match any database record | Check spelling, ensure person exists |
| Unknown absence type | Unrecognized abbreviation | Use standard abbreviations (VAC, SICK, etc.) |
| Invalid date | Unrecognized date format | Use YYYY-MM-DD format |
| End before start | End date is before start date | Check date order |

---

## Best Practices

1. **Always dry-run first**
   ```bash
   python scripts/import_excel.py data.xlsx --dry-run
   ```

2. **Review errors in verbose mode**
   ```bash
   python scripts/import_excel.py data.xlsx --dry-run --verbose
   ```

3. **Fix data issues in Excel** before importing

4. **Import in small batches** for large datasets

5. **Backup database** before bulk imports

---

## Troubleshooting

### Missing Dependencies

```
Error: Missing required dependency: openpyxl
```

**Solution**: Activate the backend virtual environment:
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### Database Connection Failed

```
Error: Could not connect to database
```

**Solution**: Ensure database is running and `DATABASE_URL` is set correctly.

### Person Not Found

```
Row 5: Person not found: 'Dr. John Smith'
```

**Solution**:
- Verify the person exists in the People page
- Check for typos in the name
- Ensure "Dr." prefix matches or is handled

### Client-Side Fallback Warning

If you see "Using Client-Side Parsing" in the import modal:

**Cause**: The backend API is unavailable or unreachable.

**Impact**:
- Basic import still works
- Cell color detection is not available
- Some advanced Excel features may not parse correctly

**Solution**:
- Ensure the backend server is running
- Check network connectivity
- Verify the API URL is correct in your environment config

---

## API Reference

### POST /imports/parse-xlsx

Parse an Excel file and return structured data for preview.

**Request**: Multipart form data with file upload

**Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `file` | File | required | Excel file (.xlsx, .xls) |
| `sheet_name` | string | first sheet | Specific sheet to parse |
| `header_row` | int | 1 | Row containing headers (1-indexed) |
| `max_rows` | int | 10000 | Maximum rows to parse |
| `skip_empty_rows` | bool | true | Skip completely empty rows |

**Response**:
```json
{
  "success": true,
  "rows": [
    {"name": "John Doe", "type": "resident", "email": "john@example.com"},
    {"name": "Jane Smith", "type": "faculty", "email": "jane@example.com"}
  ],
  "columns": ["name", "type", "email"],
  "total_rows": 2,
  "sheet_name": "Sheet1",
  "warnings": ["Skipped 3 empty rows"]
}
```

### POST /imports/parse-xlsx/sheets

List all sheet names in an Excel workbook.

**Request**: Multipart form data with file upload

**Response**:
```json
{
  "success": true,
  "sheets": ["Schedule", "Leave", "Personnel"],
  "count": 3,
  "default": "Schedule"
}
```

---

## Related

- [Exporting Data](exports.md) - Export schedules to Excel
- [Absences](absences.md) - Managing absences via the UI
- [People Management](people.md) - Adding residents and faculty
- [Conflict Resolution](conflicts.md) - Resolving import conflicts
