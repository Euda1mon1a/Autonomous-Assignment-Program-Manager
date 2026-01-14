# CSV Bridge Specification

**Purpose:** Enable communication between Cowork (domain expert), Claude macOS (Excel controller), and Claude Code (backend) using CSV as the interchange format.

**Version:** 1.0
**Date:** 2026-01-14

---

## Architecture Overview

```
┌──────────────┐                    ┌──────────────┐                    ┌──────────────┐
│   COWORK     │                    │ CLAUDE macOS │                    │ CLAUDE CODE  │
│              │                    │              │                    │              │
│ • Defines    │    RULES.csv       │ • Controls   │                    │ • Reads CSV  │
│   rules      │ ─────────────────► │   Excel      │                    │ • Applies    │
│ • Validates  │                    │ • Runs VBA   │                    │   rules      │
│   output     │                    │ • Exports/   │                    │ • Writes     │
│              │    VALIDATION.csv  │   Imports    │   SCHEDULE_*.csv   │   backend    │
│              │ ◄───────────────── │              │ ◄────────────────► │              │
└──────────────┘                    └──────────────┘                    └──────────────┘
```

---

## CSV File Specifications

### 1. RULES.csv

**Purpose:** Machine-readable scheduling rules that Claude Code can parse and apply.

**Format:**
```csv
rule_id,priority,applies_to,day_condition,slot_condition,rotation_condition,pgy_condition,assignment,description
R001,1,ALL,last_wed,AM,*,*,LEC,Last Wednesday AM = Lecture
R002,1,ALL,last_wed,PM,*,*,ADV,Last Wednesday PM = Advising
R003,2,ALL,wed,PM,NOT_IN:NF|LDNF|TDY|FMIT,*,LEC,Wednesday PM = Lecture
R004,3,RES,wed,AM,NOT_IN:NF|LDNF|TDY|KAP|FMIT,1,C,Intern Wed AM = Continuity
R005,4,RES,*,*,KAP,1,PATTERN:KAP,Apply Kapiolani pattern
R006,4,RES,*,*,LDNF,2,PATTERN:LDNF,Apply L&D NF pattern
R007,5,RES,*,*,*,*,PATTERN:DEFAULT,Apply default rotation pattern
```

**Columns:**
- `rule_id`: Unique identifier (R001, R002, etc.)
- `priority`: Lower number = higher priority (1 is highest)
- `applies_to`: ALL, RES (residents), FAC (faculty)
- `day_condition`: Specific day or pattern (wed, last_wed, fri, mon, *)
- `slot_condition`: AM, PM, or *
- `rotation_condition`: Rotation code, NOT_IN:list, or *
- `pgy_condition`: PGY level (1, 2, 3) or *
- `assignment`: Code to assign, or PATTERN:name
- `description`: Human-readable explanation

---

### 2. SCHEDULE_INPUT.csv

**Purpose:** Export current schedule from Excel for processing.

**Format:**
```csv
type,name,pgy,rotation,rotation2,2026-03-12_AM,2026-03-12_PM,2026-03-13_AM,2026-03-13_PM,...
RES,Connolly Laura,3,Hilo,,HILO,HILO,HILO,HILO,...
RES,Travis Colin,1,KAP,,KAP,KAP,KAP,KAP,...
FAC,Bevis Zach,,,FMT,FMT,FMT,FMT,...
```

**Columns:**
- `type`: RES (resident) or FAC (faculty)
- `name`: Full name (Last, First or Last First)
- `pgy`: PGY level (1, 2, 3) or blank for faculty
- `rotation`: Primary rotation code
- `rotation2`: Secondary rotation (for mid-block transitions)
- `YYYY-MM-DD_AM/PM`: One column per half-day slot

**Date columns:** ISO format date + underscore + AM/PM
- Example: `2026-03-12_AM`, `2026-03-12_PM`

---

### 3. SCHEDULE_OUTPUT.csv

**Purpose:** Corrected schedule to import back into Excel.

**Format:** Same as SCHEDULE_INPUT.csv, but with corrected assignments.

```csv
type,name,pgy,rotation,rotation2,2026-03-12_AM,2026-03-12_PM,2026-03-13_AM,2026-03-13_PM,...
RES,Travis Colin,1,KAP,,KAP,OFF,KAP,KAP,...
```

**Note:** Only cells that differ from input need to be populated. Blank cells = keep original.

---

### 4. VALIDATION.csv

**Purpose:** Compare expected vs actual, flag errors.

**Format:**
```csv
name,pgy,rotation,date,slot,current,expected,status,rule_id
Travis Colin,1,KAP,2026-03-18,AM,KAP,C,ERROR,R004
Headid Ronald,2,LDNF,2026-03-13,AM,L&D,C,ERROR,R006
Sloss Meleighe,1,PROC,2026-03-18,AM,PR,C,ERROR,R004
```

**Columns:**
- `name`: Resident/faculty name
- `pgy`: PGY level
- `rotation`: Current rotation
- `date`: Date in ISO format
- `slot`: AM or PM
- `current`: What the cell currently shows
- `expected`: What it should show per rules
- `status`: OK or ERROR
- `rule_id`: Which rule determined the expected value

---

## VBA Macros for Excel

### ExportToCSV Macro

```vba
Sub ExportScheduleToCSV()
    ' Export Block Template2 to CSV format
    ' Output: SCHEDULE_INPUT.csv in same folder as workbook

    Dim ws As Worksheet
    Dim outputPath As String
    Dim fso As Object
    Dim txtFile As Object
    Dim row As Long, col As Long
    Dim lineData As String
    Dim startDate As Date

    Set ws = ThisWorkbook.Sheets("Block Template2")
    outputPath = ThisWorkbook.Path & "\SCHEDULE_INPUT.csv"

    Set fso = CreateObject("Scripting.FileSystemObject")
    Set txtFile = fso.CreateTextFile(outputPath, True)

    ' Write header row
    lineData = "type,name,pgy,rotation,rotation2"
    startDate = DateSerial(2026, 3, 12)  ' Block 10 start
    For col = 0 To 27  ' 28 days
        lineData = lineData & "," & Format(startDate + col, "yyyy-mm-dd") & "_AM"
        lineData = lineData & "," & Format(startDate + col, "yyyy-mm-dd") & "_PM"
    Next col
    txtFile.WriteLine lineData

    ' Write resident rows (rows 9-25)
    For row = 9 To 25
        lineData = "RES"
        lineData = lineData & "," & Replace(ws.Cells(row, 5).Value, ",", " ")  ' Name
        lineData = lineData & "," & ws.Cells(row, 4).Value  ' PGY (extract number)
        lineData = lineData & "," & ws.Cells(row, 1).Value  ' Rotation
        lineData = lineData & "," & ws.Cells(row, 2).Value  ' Rotation2

        For col = 6 To 61  ' Data columns
            lineData = lineData & "," & ws.Cells(row, col).Value
        Next col
        txtFile.WriteLine lineData
    Next row

    ' Write faculty rows (rows 31-40)
    For row = 31 To 40
        lineData = "FAC"
        lineData = lineData & "," & Replace(ws.Cells(row, 5).Value, ",", " ")
        lineData = lineData & ",,"  ' No PGY for faculty
        lineData = lineData & ","   ' No rotation

        For col = 6 To 61
            lineData = lineData & "," & ws.Cells(row, col).Value
        Next col
        txtFile.WriteLine lineData
    Next row

    txtFile.Close
    MsgBox "Exported to: " & outputPath
End Sub
```

### ImportFromCSV Macro

```vba
Sub ImportScheduleFromCSV()
    ' Import corrected schedule from SCHEDULE_OUTPUT.csv
    ' Only updates cells that have values (blank = keep original)

    Dim ws As Worksheet
    Dim inputPath As String
    Dim fso As Object
    Dim txtFile As Object
    Dim lineData As String
    Dim fields() As String
    Dim row As Long, col As Long
    Dim dataRow As Long
    Dim residentRows As Object
    Dim facultyRows As Object

    Set ws = ThisWorkbook.Sheets("Block Template2")
    inputPath = ThisWorkbook.Path & "\SCHEDULE_OUTPUT.csv"

    ' Map names to rows
    Set residentRows = CreateObject("Scripting.Dictionary")
    For row = 9 To 25
        residentRows(Trim(Replace(ws.Cells(row, 5).Value, ",", " "))) = row
    Next row

    Set facultyRows = CreateObject("Scripting.Dictionary")
    For row = 31 To 40
        facultyRows(Trim(Replace(ws.Cells(row, 5).Value, ",", " "))) = row
    Next row

    Set fso = CreateObject("Scripting.FileSystemObject")
    Set txtFile = fso.OpenTextFile(inputPath, 1)

    ' Skip header
    txtFile.ReadLine

    Do While Not txtFile.AtEndOfStream
        lineData = txtFile.ReadLine
        fields = Split(lineData, ",")

        ' Find the row for this person
        Dim personName As String
        Dim targetRow As Long
        personName = Trim(fields(1))

        If fields(0) = "RES" Then
            If residentRows.Exists(personName) Then
                targetRow = residentRows(personName)
            Else
                GoTo NextLine
            End If
        Else
            If facultyRows.Exists(personName) Then
                targetRow = facultyRows(personName)
            Else
                GoTo NextLine
            End If
        End If

        ' Update cells (skip first 5 fields: type,name,pgy,rotation,rotation2)
        For col = 5 To UBound(fields)
            If Trim(fields(col)) <> "" Then
                ws.Cells(targetRow, col + 1).Value = fields(col)
            End If
        Next col

NextLine:
    Loop

    txtFile.Close
    MsgBox "Import complete!"
End Sub
```

### ValidateSchedule Macro

```vba
Sub ValidateSchedule()
    ' Read VALIDATION.csv and highlight errors in red

    Dim ws As Worksheet
    Dim inputPath As String
    Dim fso As Object
    Dim txtFile As Object
    Dim lineData As String
    Dim fields() As String
    Dim errorCount As Long

    Set ws = ThisWorkbook.Sheets("Block Template2")
    inputPath = ThisWorkbook.Path & "\VALIDATION.csv"

    ' Clear previous highlighting
    ws.Cells.Interior.ColorIndex = xlNone

    Set fso = CreateObject("Scripting.FileSystemObject")
    Set txtFile = fso.OpenTextFile(inputPath, 1)

    ' Skip header
    txtFile.ReadLine
    errorCount = 0

    Do While Not txtFile.AtEndOfStream
        lineData = txtFile.ReadLine
        fields = Split(lineData, ",")

        ' fields: name,pgy,rotation,date,slot,current,expected,status,rule_id
        If UBound(fields) >= 7 Then
            If fields(7) = "ERROR" Then
                ' Find cell and highlight
                ' (Implementation depends on mapping date+slot to column)
                errorCount = errorCount + 1
            End If
        End If
    Loop

    txtFile.Close
    MsgBox "Validation complete. " & errorCount & " errors found."
End Sub
```

---

## Workflow

### Step 1: Cowork Creates Rules
```
Cowork generates RULES.csv with all scheduling rules
Location: docs/scheduling/RULES.csv
```

### Step 2: Claude macOS Exports Schedule
```applescript
tell application "Microsoft Excel"
    run VBA macro "ExportScheduleToCSV"
end tell
```
**Output:** `SCHEDULE_INPUT.csv` in workbook folder

### Step 3: Claude Code Applies Rules
```python
# Read input
input_df = pd.read_csv('SCHEDULE_INPUT.csv')
rules_df = pd.read_csv('RULES.csv')

# Apply rules (priority order)
output_df = apply_rules(input_df, rules_df)

# Write output
output_df.to_csv('SCHEDULE_OUTPUT.csv', index=False)
```

### Step 4: Claude macOS Imports Corrected Schedule
```applescript
tell application "Microsoft Excel"
    run VBA macro "ImportScheduleFromCSV"
end tell
```

### Step 5: Cowork Validates
```
Cowork generates VALIDATION.csv comparing current vs expected
Claude macOS runs ValidateSchedule macro to highlight errors
```

---

## Pattern Definitions

### PATTERN:KAP (Kapiolani L&D - Intern)
```
Mon AM: KAP
Mon PM: OFF
Tue AM: OFF
Tue PM: OFF
Wed AM: C
Wed PM: LEC
Thu-Sun: KAP/KAP
```

### PATTERN:LDNF (L&D Night Float - R2)
```
Mon-Thu AM: OFF
Mon-Thu PM: LDNF
Fri AM: C
Fri PM: OFF
Sat-Sun: W/W
```

### PATTERN:NF (FM Night Float)
```
All AM: OFF
All PM: NF
(Except first Thu PM = C-N for oncoming)
```

### PATTERN:DEFAULT
```
Use ROTATION_CODES mapping:
- Look up rotation in mapping table
- Apply (AM_code, PM_code) pattern
```

---

## Error Handling

### Missing Name Match
If CSV name doesn't match Excel name:
- Log warning
- Skip row
- Report in summary

### Invalid Date Format
If date column header doesn't parse:
- Abort with error message
- List expected format

### Conflicting Rules
If multiple rules match same cell:
- Use highest priority (lowest number)
- Log which rule won

---

## Files Created by This Spec

| File | Creator | Consumer | Location |
|------|---------|----------|----------|
| RULES.csv | Cowork | Claude Code | docs/scheduling/ |
| SCHEDULE_INPUT.csv | VBA Macro | Claude Code | workbook folder |
| SCHEDULE_OUTPUT.csv | Claude Code | VBA Macro | workbook folder |
| VALIDATION.csv | Cowork | VBA Macro | docs/scheduling/ |

---

## Next Steps

1. **Cowork:** Generate RULES.csv from BLOCK_SCHEDULE_RULES.md
2. **Claude macOS:** Inject VBA macros into Excel workbook
3. **Claude Code:** Implement rule application in expansion service
4. **Test:** Run full cycle on Block 10
