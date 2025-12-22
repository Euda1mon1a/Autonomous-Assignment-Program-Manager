# Excel CSV Auto-Export

VBA module that automatically maintains CSV "twins" of Excel worksheets. When you save your schedule workbook, CSV files are automatically created/updated in the same directory, ready for import into the Residency Scheduler system.

## Features

- **Auto-export on save**: CSV files are created automatically when you save the workbook
- **UTF-8 encoding**: Full international character support compatible with the import system
- **Smart naming**: `{WorkbookName}_{SheetName}.csv` convention
- **Filename sanitization**: Spaces become underscores, invalid characters removed
- **Hidden sheet skip**: Only visible worksheets are exported
- **Manual trigger**: Ctrl+Shift+E to force export anytime
- **Status feedback**: Message box shows count of exported files

## Quick Start

### Option 1: Add to a Specific Workbook

1. **Open your schedule workbook** in Excel

2. **Open VBA Editor** (Alt+F11)

3. **Import the module**:
   - File → Import File
   - Navigate to `scripts/excel/CSVAutoExport.bas`
   - Click Open

4. **Add event handlers**:
   - In Project Explorer, double-click `ThisWorkbook`
   - Copy the contents of `ThisWorkbook_Events.txt` into the code window

5. **Save as macro-enabled**:
   - File → Save As
   - Choose "Excel Macro-Enabled Workbook (*.xlsm)"

### Option 2: Global Installation (Personal.xlsb)

For auto-export across ALL workbooks:

1. **Create Personal.xlsb** (if it doesn't exist):
   - Open Excel
   - Record a macro (Developer → Record Macro)
   - Choose "Personal Macro Workbook" as location
   - Stop recording immediately
   - Close Excel and save Personal.xlsb when prompted

2. **Open VBA Editor** (Alt+F11)

3. **Import to Personal.xlsb**:
   - In Project Explorer, expand `PERSONAL.XLSB`
   - Right-click → Import File → select `CSVAutoExport.bas`

4. **Modify for global use**:
   - The module uses `ThisWorkbook` - for global use, change to `ActiveWorkbook`
   - See "Global Use Modifications" section below

## Usage

### Automatic Export
Simply save your workbook (Ctrl+S). CSV files are created automatically.

### Manual Export
Press **Ctrl+Shift+E** to export all sheets immediately.

### Output Location
CSV files are created in the same directory as your Excel file:
```
/Documents/Schedule_Block10.xlsx
/Documents/Schedule_Block10_Residents.csv
/Documents/Schedule_Block10_Faculty.csv
/Documents/Schedule_Block10_Summary.csv
```

## CSV Format

The exported CSV preserves the Excel format expected by `import_excel.py`:

### Schedule Sheet Format
```csv
,,Block Number,,,MON,MON,TUE,TUE,...
,,,,,am,pm,am,pm,...
Date:,,,,,15-Jan,15-Jan,16-Jan,16-Jan,...
...
ROTATION,CODE,ROLE,PROVIDER,,C,C,FMIT,FMIT,...
FMIT,R1,PGY 1,Dr. Smith,,W,W,FMIT,FMIT,...
```

### Absence Sheet Format
```csv
Person,Type,Start Date,End Date,Notes
Dr. Smith,VAC,2025-01-15,2025-01-22,Annual leave
Dr. Jones,CONF,2025-02-01,2025-02-03,AAFP Conference
```

## Abbreviation Reference

The import system recognizes these abbreviations:

| Abbreviation | Meaning |
|-------------|---------|
| W | Working (available) |
| VAC | Vacation |
| SICK | Sick leave |
| MED | Medical |
| CONF | Conference |
| DEP | Deployment |
| TDY | Temporary Duty |
| FEM | Family Emergency |
| PER | Personal |
| OFF | Day Off |
| HOL/FED | Holiday |
| FMIT | Inpatient rotation |
| NF | Night Float |
| C | Clinic |

## Global Use Modifications

For Personal.xlsb installation, modify `CSVAutoExport.bas`:

```vba
' Change this:
Public Function ExportAllSheetsToCSV(...) As Integer
    If Len(ThisWorkbook.Path) = 0 Then
    ...
    workbookPath = ThisWorkbook.Path

' To this:
Public Function ExportAllSheetsToCSV(...) As Integer
    If Len(ActiveWorkbook.Path) = 0 Then
    ...
    workbookPath = ActiveWorkbook.Path
```

Replace all occurrences of `ThisWorkbook` with `ActiveWorkbook`.

## Troubleshooting

### "Please save the workbook first"
The workbook must be saved at least once before CSV export (so it has a file path).

### CSV files not appearing
- Check the workbook directory (same folder as .xlsx/.xlsm file)
- Ensure worksheets aren't hidden
- Verify macro security allows VBA execution

### Encoding issues with special characters
The module uses ADODB.Stream for UTF-8 encoding. If you see encoding problems:
- Verify the CSV opens correctly in Notepad (should show UTF-8)
- Some older Excel versions may require "Microsoft ActiveX Data Objects" reference

### Keyboard shortcut not working
- Ensure the workbook containing the macro is open
- For global install, ensure Personal.xlsb is loaded
- Check for conflicting shortcuts in other add-ins

## Integration with Import System

The CSV files work directly with `scripts/import_excel.py`:

```bash
# Import all CSV files from a directory
python scripts/import_excel.py Schedule_Block10_Residents.csv --dry-run

# The import script auto-detects:
# - Absence sheets (columns: Person, Type, Start Date, End Date)
# - Schedule sheets (AM/PM grid format with rotations)
```

## Security Note

This module runs VBA macros. Only enable macros for workbooks from trusted sources. The module:
- Only reads cell values and writes to local CSV files
- Does not access network resources
- Does not modify the original Excel data
- Does not execute external commands

## Files

| File | Description |
|------|-------------|
| `CSVAutoExport.bas` | Main VBA module (import this) |
| `ThisWorkbook_Events.txt` | Event handlers to paste into ThisWorkbook |
| `README.md` | This documentation |

## Version History

- **1.0.0** (2024-12): Initial release
  - Auto-export on save
  - UTF-8 encoding
  - Ctrl+Shift+E manual trigger
  - Hidden sheet filtering
