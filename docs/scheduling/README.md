# TAMC Scheduling - CSV Bridge System

**The Four Universes:**
1. **You** (Program Director) - Knows what the schedule should look like
2. **Cowork** - Domain expert, defines rules, validates output
3. **Claude macOS** - Controls Excel directly via AppleScript/VBA
4. **Claude Code** - Backend database and expansion service

---

## Quick Start

### For Claude macOS (Excel Control)

1. **Open** the Block 10 workbook in Excel
2. **Install VBA macros** from `VBA_MACROS.bas`:
   - Press `Alt+F11` → Insert → Module → Paste code
   - Save as `.xlsm`
3. **Export current schedule:**
   ```
   Run macro: ExportScheduleToCSV
   Output: SCHEDULE_INPUT.csv (same folder as workbook)
   ```
4. **Import corrected schedule:**
   ```
   Run macro: ImportScheduleFromCSV
   Input: SCHEDULE_OUTPUT.csv (same folder as workbook)
   ```
5. **Validate and highlight errors:**
   ```
   Copy VALIDATION.csv to workbook folder
   Run macro: ValidateAndHighlight
   ```

### For Claude Code (Backend)

1. **Read rules:** `docs/scheduling/RULES.csv`
2. **Process input:** Apply rules to `SCHEDULE_INPUT.csv`
3. **Write output:** Generate `SCHEDULE_OUTPUT.csv`

### For Cowork (Validation)

1. **Review output** from Claude Code
2. **Generate** `VALIDATION.csv` with errors
3. **Update** `RULES.csv` if rules need refinement

---

## Files in This Directory

| File | Purpose | Creator | Consumer |
|------|---------|---------|----------|
| `README.md` | This guide | Cowork | Everyone |
| `RULES.csv` | Machine-readable scheduling rules | Cowork | Claude Code |
| `VBA_MACROS.bas` | Excel macros for import/export | Cowork | Claude macOS |
| `VALIDATION.csv` | Errors to highlight | Cowork | Claude macOS |
| `CSV_BRIDGE_SPEC.md` | Full technical specification | Cowork | Everyone |
| `BLOCK_SCHEDULE_RULES.md` | Human-readable rules reference | Cowork | Everyone |

---

## The Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   STEP 1: Export from Excel                                                 │
│   ┌──────────┐     VBA Macro      ┌───────────────────┐                    │
│   │  Excel   │ ────────────────►  │ SCHEDULE_INPUT.csv │                    │
│   │ Workbook │                    └───────────────────┘                    │
│   └──────────┘                              │                               │
│                                             ▼                               │
│   STEP 2: Apply Rules                                                       │
│   ┌───────────┐                  ┌─────────────────────┐                   │
│   │ RULES.csv │ ───────────────► │    Claude Code      │                   │
│   └───────────┘                  │  (apply_rules.py)   │                   │
│                                  └──────────┬──────────┘                   │
│                                             │                               │
│                                             ▼                               │
│   STEP 3: Import to Excel        ┌────────────────────┐                    │
│   ┌──────────┐     VBA Macro     │ SCHEDULE_OUTPUT.csv │                   │
│   │  Excel   │ ◄──────────────── └────────────────────┘                    │
│   │ Workbook │                                                              │
│   └──────────┘                                                              │
│                                                                             │
│   STEP 4: Validate               ┌─────────────────┐                       │
│   ┌──────────┐     VBA Macro     │ VALIDATION.csv  │                       │
│   │  Excel   │ ◄──────────────── └─────────────────┘                       │
│   │ (errors  │                                                              │
│   │  in red) │                                                              │
│   └──────────┘                                                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Current Status (Block 10)

**Validation found 51 errors** in the current export.

### Top Issues:

| Resident | Issue | Count |
|----------|-------|-------|
| Travis (KAP) | Kapiolani pattern not applied | 14 |
| Headid (LDNF) | L&D NF pattern not applied | 16 |
| Sloss (PROC) | Intern Wed AM not C | 5 |
| Monsivais (IM) | Intern Wed AM not C | 5 |
| You (NEURO→NF) | Mid-block transition missing | 2 |
| Wilhelm (PedW→PedNF) | Mid-block + intern Wed AM | 4 |
| Byrnes (PedNF→PedW) | Mid-block + intern Wed AM | 3 |
| Sawyer (FMC) | Last Wed not LEC/ADV | 2 |

---

## AppleScript for Claude macOS

### Run Export Macro
```applescript
tell application "Microsoft Excel"
    activate
    run VBA macro "ExportScheduleToCSV" macro file workbook 1
end tell
```

### Run Import Macro
```applescript
tell application "Microsoft Excel"
    activate
    run VBA macro "ImportScheduleFromCSV" macro file workbook 1
end tell
```

### Run Validation Macro
```applescript
tell application "Microsoft Excel"
    activate
    run VBA macro "ValidateAndHighlight" macro file workbook 1
end tell
```

---

## Rule Priority

Rules are applied in priority order (1 = highest):

| Priority | Rule Type | Example |
|----------|-----------|---------|
| 1 | Last Wednesday | AM=LEC, PM=ADV |
| 2 | Wednesday PM | LEC for most |
| 3 | Intern Wed AM | Continuity clinic |
| 4 | Special Rotations | KAP, LDNF patterns |
| 5 | Weekends | W for non-24/7 |
| 6 | Default Patterns | Rotation → AM/PM codes |
| 7 | Mid-block | Switch at col 28 |

---

## Troubleshooting

### "Name not found" during import
- Check name spelling matches exactly
- Names are normalized (lowercase, no punctuation)

### Macro won't run
- Save workbook as `.xlsm` (macro-enabled)
- Enable macros in Excel security settings

### Wrong columns highlighted
- Verify Block 10 dates start Mar 12, 2026
- Check column mapping: Col 6 = Mar 12 AM

---

## Contact

- **Rules questions:** Ask Cowork
- **Excel issues:** Ask Claude macOS
- **Backend issues:** Ask Claude Code
- **Everything else:** Ask the Program Director
