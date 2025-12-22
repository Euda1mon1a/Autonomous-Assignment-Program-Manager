***REMOVED*** Excel CSV Auto-Export

VBA module that automatically maintains CSV "twins" of Excel worksheets. When you save your schedule workbook, CSV files are automatically created/updated in the same directory, ready for import into the Residency Scheduler system.

***REMOVED******REMOVED*** Features

- **Auto-export on save**: CSV files are created automatically when you save the workbook
- **UTF-8 encoding**: Full international character support compatible with the import system
- **Smart naming**: `{WorkbookName}_{SheetName}.csv` convention
- **Filename sanitization**: Spaces become underscores, invalid characters removed
- **Hidden sheet skip**: Only visible worksheets are exported
- **Manual trigger**: Ctrl+Shift+E to force export anytime
- **Status feedback**: Message box shows count of exported files

---

***REMOVED******REMOVED*** For Program Leadership & Administrators

***REMOVED******REMOVED******REMOVED*** What This Does

This tool creates a bridge between your Excel schedule workbooks and the Residency Scheduler web application. Instead of manually exporting each worksheet as a CSV file every time you make changes, the system now does it automatically.

**Before:** Save Excel → File → Save As → CSV → Navigate to folder → Save → Repeat for each sheet → Upload to scheduler

**After:** Save Excel → Done (CSV files appear automatically)

***REMOVED******REMOVED******REMOVED*** Why This Matters

| Benefit | Impact |
|---------|--------|
| **Eliminates manual steps** | No more "Save As CSV" for each worksheet |
| **Always current data** | Web app always has your latest schedule |
| **Reduces errors** | No risk of uploading outdated files |
| **Saves time** | 5-10 minutes saved per schedule update |
| **Works silently** | Just save normally - CSV files appear automatically |

***REMOVED******REMOVED******REMOVED*** What You'll See

When you save your schedule workbook, CSV files appear in the same folder:

```
📁 Schedules/
   📄 Block10_Schedule.xlsm        ← Your Excel file
   📄 Block10_Schedule_Residents.csv   ← Auto-generated
   📄 Block10_Schedule_Faculty.csv     ← Auto-generated
   📄 Block10_Schedule_Absences.csv    ← Auto-generated
```

These CSV files are ready to import into the Residency Scheduler.

***REMOVED******REMOVED******REMOVED*** One-Time Setup (5 minutes)

Have your IT support or a tech-comfortable colleague perform these steps once:

1. Open your master schedule workbook in Excel
2. Press **Alt+F11** to open the code editor
3. Go to **File → Import File** and select `CSVAutoExport.bas`
4. Find "ThisWorkbook" in the left panel and paste in the event code
5. Save the workbook as `.xlsm` (macro-enabled format)

Detailed instructions are in the [Quick Start](***REMOVED***quick-start) section below.

***REMOVED******REMOVED******REMOVED*** Daily Use

**Automatic mode:** Just save your workbook normally (Ctrl+S or File → Save). CSV files are created/updated silently.

**Manual export:** Press **Ctrl+Shift+E** anytime to force an export and see a confirmation message.

***REMOVED******REMOVED******REMOVED*** Common Questions

**Q: Do I need to change how I edit the schedule?**
A: No. Edit your Excel file exactly as before. The only change is saving as `.xlsm` instead of `.xlsx`.

**Q: Where do the CSV files go?**
A: Same folder as your Excel file. They're named `{YourWorkbook}_{SheetName}.csv`.

**Q: What if I have hidden sheets?**
A: Hidden sheets are skipped. Only visible worksheets are exported.

**Q: Will this slow down saving?**
A: Barely noticeable. Export adds 1-2 seconds for a typical schedule workbook.

**Q: What about security?**
A: The macro only reads your cells and writes CSV files locally. It doesn't access the internet or send data anywhere.

**Q: Can multiple people use this?**
A: Yes. Each person needs the macro installed in their copy of the workbook, or use the global installation option.

---

***REMOVED******REMOVED*** Quick Start

***REMOVED******REMOVED******REMOVED*** Option 1: Add to a Specific Workbook

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

***REMOVED******REMOVED******REMOVED*** Option 2: Global Installation (Personal.xlsb)

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

***REMOVED******REMOVED*** Usage

***REMOVED******REMOVED******REMOVED*** Automatic Export
Simply save your workbook (Ctrl+S). CSV files are created automatically.

***REMOVED******REMOVED******REMOVED*** Manual Export
Press **Ctrl+Shift+E** to export all sheets immediately.

***REMOVED******REMOVED******REMOVED*** Output Location
CSV files are created in the same directory as your Excel file:
```
/Documents/Schedule_Block10.xlsx
/Documents/Schedule_Block10_Residents.csv
/Documents/Schedule_Block10_Faculty.csv
/Documents/Schedule_Block10_Summary.csv
```

***REMOVED******REMOVED*** CSV Format

The exported CSV preserves the Excel format expected by `import_excel.py`:

***REMOVED******REMOVED******REMOVED*** Schedule Sheet Format
```csv
,,Block Number,,,MON,MON,TUE,TUE,...
,,,,,am,pm,am,pm,...
Date:,,,,,15-Jan,15-Jan,16-Jan,16-Jan,...
...
ROTATION,CODE,ROLE,PROVIDER,,C,C,FMIT,FMIT,...
FMIT,R1,PGY 1,Dr. Smith,,W,W,FMIT,FMIT,...
```

***REMOVED******REMOVED******REMOVED*** Absence Sheet Format
```csv
Person,Type,Start Date,End Date,Notes
Dr. Smith,VAC,2025-01-15,2025-01-22,Annual leave
Dr. Jones,CONF,2025-02-01,2025-02-03,AAFP Conference
```

***REMOVED******REMOVED*** Abbreviation Reference

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

***REMOVED******REMOVED*** Global Use Modifications

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

***REMOVED******REMOVED*** Troubleshooting

***REMOVED******REMOVED******REMOVED*** "Please save the workbook first"
The workbook must be saved at least once before CSV export (so it has a file path).

***REMOVED******REMOVED******REMOVED*** CSV files not appearing
- Check the workbook directory (same folder as .xlsx/.xlsm file)
- Ensure worksheets aren't hidden
- Verify macro security allows VBA execution

***REMOVED******REMOVED******REMOVED*** Encoding issues with special characters
The module uses ADODB.Stream for UTF-8 encoding. If you see encoding problems:
- Verify the CSV opens correctly in Notepad (should show UTF-8)
- Some older Excel versions may require "Microsoft ActiveX Data Objects" reference

***REMOVED******REMOVED******REMOVED*** Keyboard shortcut not working
- Ensure the workbook containing the macro is open
- For global install, ensure Personal.xlsb is loaded
- Check for conflicting shortcuts in other add-ins

***REMOVED******REMOVED*** Integration with Import System

The CSV files work directly with `scripts/import_excel.py`:

```bash
***REMOVED*** Import all CSV files from a directory
python scripts/import_excel.py Schedule_Block10_Residents.csv --dry-run

***REMOVED*** The import script auto-detects:
***REMOVED*** - Absence sheets (columns: Person, Type, Start Date, End Date)
***REMOVED*** - Schedule sheets (AM/PM grid format with rotations)
```

***REMOVED******REMOVED*** Security Note

This module runs VBA macros. Only enable macros for workbooks from trusted sources. The module:
- Only reads cell values and writes to local CSV files
- Does not access network resources
- Does not modify the original Excel data
- Does not execute external commands

***REMOVED******REMOVED*** Files

| File | Description |
|------|-------------|
| `CSVAutoExport.bas` | Main VBA module (import this) |
| `ThisWorkbook_Events.txt` | Event handlers to paste into ThisWorkbook |
| `README.md` | This documentation |

***REMOVED******REMOVED*** Version History

- **1.0.0** (2024-12): Initial release
  - Auto-export on save
  - UTF-8 encoding
  - Ctrl+Shift+E manual trigger
  - Hidden sheet filtering
