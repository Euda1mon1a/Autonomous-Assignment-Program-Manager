# Spreadsheet Editor & Export Feature Specification

> **Purpose:** Enable human verification of generated schedules in an Excel-like interface before finalization and export.
> **Target Users:** Program coordinators, schedulers, admins ("normies" comfortable with Excel)
> **Priority:** High - Critical for adoption by non-technical users

---

## Problem Statement

Generated schedules need human review before deployment. Current workflow requires exporting to Excel, editing externally, then re-importing. This creates friction and data sync issues.

**Goal:** Provide an in-app spreadsheet experience familiar to Excel users, with direct export capability.

---

## Feature Requirements

### Must Have (MVP)
- [ ] Grid display with rows (residents) × columns (dates)
- [ ] Click-to-edit cells with dropdown for rotation types
- [ ] Color coding by rotation type (matches existing Excel export)
- [ ] Keyboard navigation (arrows, Tab, Enter)
- [ ] Export to `.xlsx` with formatting preserved
- [ ] Save edits back to database
- [ ] ACGME hours validation displayed per row

### Should Have (v1.1)
- [ ] Copy/paste from Excel (parse clipboard)
- [ ] Undo/redo stack
- [ ] Conflict highlighting (double-booked, coverage gaps)
- [ ] Column resize/freeze first column
- [ ] Print-friendly view

### Nice to Have (Future)
- [ ] Multi-select cells for bulk edit
- [ ] Conditional formatting rules
- [ ] Comments/notes on cells
- [ ] Version history/diff view

---

## Technical Approach

### Why Custom vs Library

| Option | Pros | Cons |
|--------|------|------|
| **Custom (Recommended)** | No license cost, matches codebase style, full control | More initial work |
| Handsontable | Feature-rich, Excel-like | Commercial license required ($) |
| react-datasheet | Lightweight, MIT license | Limited features, dated |
| AG Grid | Enterprise features | Overkill, complex, expensive |

**Decision:** Build custom using existing patterns from `WeeklyGridEditor.tsx` and `EditableCell.tsx`.

### Key Libraries (Already Installed)

```json
{
  "xlsx": "0.20.2"  // SheetJS - handles .xlsx read/write with formatting
}
```

---

## Component Architecture

```
src/features/spreadsheet-editor/
├── components/
│   ├── SpreadsheetEditor.tsx      # Main container
│   ├── SpreadsheetToolbar.tsx     # Actions: Save, Export, Undo
│   ├── SpreadsheetGrid.tsx        # The grid itself
│   ├── SpreadsheetCell.tsx        # Individual cell (editable)
│   ├── SpreadsheetHeader.tsx      # Column headers (dates)
│   ├── SpreadsheetRowHeader.tsx   # Row headers (resident names)
│   └── HoursIndicator.tsx         # ACGME hours with status
├── hooks/
│   ├── useSpreadsheetState.ts     # Grid state management
│   ├── useKeyboardNav.ts          # Arrow/Tab/Enter handling
│   ├── useCellEdit.ts             # Edit mode logic
│   └── useExcelExport.ts          # SheetJS export logic
├── utils/
│   ├── excelStyles.ts             # Color mappings, formatting
│   ├── gridHelpers.ts             # Cell coordinate helpers
│   └── validation.ts              # ACGME checks per row
├── types.ts                       # TypeScript interfaces
└── index.ts                       # Public exports
```

---

## Data Model

### Grid Data Structure

```typescript
// types.ts

interface SpreadsheetData {
  rows: SpreadsheetRow[];
  columns: SpreadsheetColumn[];
  metadata: {
    blockNumber: number;
    startDate: string;  // ISO date
    endDate: string;
    generatedAt: string;
    lastModified: string;
  };
}

interface SpreadsheetRow {
  id: string;              // resident_id
  label: string;           // Display name (can be anonymized)
  pgyLevel: number;
  cells: SpreadsheetCell[];
  computed: {
    totalHours: number;
    acgmeStatus: 'ok' | 'warning' | 'violation';
    violations: string[];  // e.g., ["Exceeds 80hr weekly average"]
  };
}

interface SpreadsheetColumn {
  id: string;              // date as ISO string
  label: string;           // "Mon 1/15" display format
  dayOfWeek: number;       // 0-6
  isWeekend: boolean;
  isHoliday: boolean;
  holidayName?: string;
}

interface SpreadsheetCell {
  rowId: string;
  columnId: string;
  value: string;           // Rotation code: "CLI", "ICU", "OFF", etc.
  rotationType: RotationType;
  isEdited: boolean;       // Track user modifications
  isLocked: boolean;       // Some cells may be read-only
  note?: string;
  style?: CellStyle;
}

interface CellStyle {
  backgroundColor?: string;
  textColor?: string;
  bold?: boolean;
  italic?: boolean;
  borderColor?: string;
}

type RotationType =
  | 'CLINIC'
  | 'INPATIENT'
  | 'ICU'
  | 'NIGHT_FLOAT'
  | 'CALL'
  | 'OFF'
  | 'VACATION'
  | 'CONFERENCE'
  | 'ELECTIVE'
  | 'ADMIN';
```

### Rotation Color Map (Match Existing Export)

```typescript
// utils/excelStyles.ts

export const ROTATION_COLORS: Record<RotationType, { bg: string; text: string }> = {
  CLINIC:      { bg: '#E8F5E9', text: '#1B5E20' },  // Green
  INPATIENT:   { bg: '#E3F2FD', text: '#0D47A1' },  // Blue
  ICU:         { bg: '#FCE4EC', text: '#880E4F' },  // Pink
  NIGHT_FLOAT: { bg: '#F3E5F5', text: '#4A148C' },  // Purple
  CALL:        { bg: '#FFF3E0', text: '#E65100' },  // Orange
  OFF:         { bg: '#FAFAFA', text: '#757575' },  // Gray
  VACATION:    { bg: '#FFFDE7', text: '#F57F17' },  // Yellow
  CONFERENCE:  { bg: '#E0F7FA', text: '#006064' },  // Cyan
  ELECTIVE:    { bg: '#FBE9E7', text: '#BF360C' },  // Deep Orange
  ADMIN:       { bg: '#ECEFF1', text: '#37474F' },  // Blue Gray
};
```

---

## Component Specifications

### SpreadsheetEditor (Main Container)

```typescript
interface SpreadsheetEditorProps {
  blockNumber: number;
  startDate: string;
  endDate: string;
  onSave?: (data: SpreadsheetData) => Promise<void>;
  readOnly?: boolean;
}

// Features:
// - Fetches schedule data on mount
// - Manages edit state
// - Handles save/export actions
// - Shows loading/error states
```

### SpreadsheetGrid

```typescript
interface SpreadsheetGridProps {
  data: SpreadsheetData;
  selectedCell: CellCoord | null;
  onCellSelect: (coord: CellCoord) => void;
  onCellEdit: (coord: CellCoord, value: string) => void;
  editingCell: CellCoord | null;
}

// Layout:
// - CSS Grid with sticky first column and header row
// - Virtualized if >50 rows (react-window optional)
// - Responsive horizontal scroll
```

### SpreadsheetCell

```typescript
interface SpreadsheetCellProps {
  cell: SpreadsheetCell;
  isSelected: boolean;
  isEditing: boolean;
  onSelect: () => void;
  onStartEdit: () => void;
  onCommitEdit: (value: string) => void;
  onCancelEdit: () => void;
}

// Behavior:
// - Click to select
// - Double-click or Enter to edit
// - Escape to cancel
// - Tab/Enter to commit and move
// - Shows dropdown with rotation options when editing
```

---

## Keyboard Navigation

| Key | Action |
|-----|--------|
| Arrow keys | Move selection |
| Tab | Move right, wrap to next row |
| Shift+Tab | Move left, wrap to previous row |
| Enter | Start editing / Commit and move down |
| Escape | Cancel edit |
| Delete/Backspace | Clear cell (if editable) |
| Ctrl+S | Save changes |
| Ctrl+E | Export to Excel |
| Ctrl+Z | Undo |
| Ctrl+Shift+Z | Redo |

```typescript
// hooks/useKeyboardNav.ts

export function useKeyboardNav(
  gridRef: RefObject<HTMLDivElement>,
  selectedCell: CellCoord | null,
  setSelectedCell: (coord: CellCoord) => void,
  totalRows: number,
  totalCols: number
) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!selectedCell) return;

      const { row, col } = selectedCell;

      switch (e.key) {
        case 'ArrowUp':
          e.preventDefault();
          if (row > 0) setSelectedCell({ row: row - 1, col });
          break;
        case 'ArrowDown':
          e.preventDefault();
          if (row < totalRows - 1) setSelectedCell({ row: row + 1, col });
          break;
        case 'ArrowLeft':
          e.preventDefault();
          if (col > 0) setSelectedCell({ row, col: col - 1 });
          break;
        case 'ArrowRight':
          e.preventDefault();
          if (col < totalCols - 1) setSelectedCell({ row, col: col + 1 });
          break;
        case 'Tab':
          e.preventDefault();
          // Move right, wrap to next row
          if (col < totalCols - 1) {
            setSelectedCell({ row, col: col + 1 });
          } else if (row < totalRows - 1) {
            setSelectedCell({ row: row + 1, col: 0 });
          }
          break;
      }
    };

    gridRef.current?.addEventListener('keydown', handleKeyDown);
    return () => gridRef.current?.removeEventListener('keydown', handleKeyDown);
  }, [selectedCell, totalRows, totalCols]);
}
```

---

## Excel Export

### Using SheetJS (xlsx)

```typescript
// hooks/useExcelExport.ts

import * as XLSX from 'xlsx';
import { ROTATION_COLORS } from '../utils/excelStyles';

export function useExcelExport() {
  const exportToExcel = (data: SpreadsheetData, filename: string) => {
    // Create workbook
    const wb = XLSX.utils.book_new();

    // Build data array for sheet
    const sheetData: (string | number)[][] = [];

    // Header row
    const headerRow = ['Resident', ...data.columns.map(c => c.label), 'Hours', 'Status'];
    sheetData.push(headerRow);

    // Data rows
    data.rows.forEach(row => {
      const rowData = [
        row.label,
        ...row.cells.map(c => c.value),
        row.computed.totalHours,
        row.computed.acgmeStatus.toUpperCase()
      ];
      sheetData.push(rowData);
    });

    // Create worksheet
    const ws = XLSX.utils.aoa_to_sheet(sheetData);

    // Apply column widths
    ws['!cols'] = [
      { wch: 20 },  // Resident name
      ...data.columns.map(() => ({ wch: 8 })),  // Date columns
      { wch: 8 },   // Hours
      { wch: 10 }   // Status
    ];

    // Apply cell styles (requires xlsx-style or manual approach)
    // Note: Base xlsx doesn't support styles; use xlsx-style fork or
    // generate via backend with openpyxl for full formatting

    // Add to workbook
    XLSX.utils.book_append_sheet(wb, ws, 'Schedule');

    // Trigger download
    XLSX.writeFile(wb, `${filename}.xlsx`);
  };

  return { exportToExcel };
}
```

### For Full Formatting: Backend Export

SheetJS community edition has limited style support. For full Excel formatting (colors, borders, fonts), use the existing backend:

```typescript
// Option: Call backend for styled export
const exportWithFormatting = async (data: SpreadsheetData) => {
  const response = await api.post('/api/v1/export/schedule-xlsx', {
    data,
    includeFormatting: true
  });

  // Download blob
  const blob = new Blob([response.data], {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `schedule_block_${data.metadata.blockNumber}.xlsx`;
  a.click();
};
```

---

## API Integration

### Fetch Schedule for Editing

```typescript
// GET /api/v1/schedules/block/{block_number}/spreadsheet
interface SpreadsheetResponse {
  data: SpreadsheetData;
  permissions: {
    canEdit: boolean;
    canExport: boolean;
    canPublish: boolean;
  };
}
```

### Save Edits

```typescript
// PATCH /api/v1/schedules/block/{block_number}/spreadsheet
interface SpreadsheetUpdateRequest {
  changes: CellChange[];  // Only send changed cells
}

interface CellChange {
  residentId: string;
  date: string;
  value: string;
  previousValue: string;  // For audit trail
}
```

### Backend Endpoint (New)

```python
# backend/app/api/routes/schedule_spreadsheet.py

@router.get("/block/{block_number}/spreadsheet")
async def get_schedule_spreadsheet(
    block_number: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> SpreadsheetResponse:
    """Get schedule data formatted for spreadsheet editor."""
    # Fetch assignments for block
    # Transform to SpreadsheetData format
    # Calculate ACGME hours per resident
    pass

@router.patch("/block/{block_number}/spreadsheet")
async def update_schedule_spreadsheet(
    block_number: int,
    request: SpreadsheetUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> SpreadsheetResponse:
    """Apply spreadsheet edits to schedule."""
    # Validate changes
    # Apply to database
    # Log audit trail
    # Return updated data
    pass
```

---

## UI Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│ ◀ Back to Schedules          Block 10 Schedule Review               │
├─────────────────────────────────────────────────────────────────────┤
│ [💾 Save] [📥 Export ▼] [↩ Undo] [↪ Redo]    Last saved: 2 min ago │
├─────────────────────────────────────────────────────────────────────┤
│ Legend: [CLI] [ICU] [NF] [CALL] [OFF] [VAC]     Filter: [All ▼]    │
├───────┬───────┬───────┬───────┬───────┬───────┬───────┬─────┬──────┤
│       │Mon    │Tue    │Wed    │Thu    │Fri    │Sat    │Sun  │Hours │
│       │1/13   │1/14   │1/15   │1/16   │1/17   │1/18   │1/19 │      │
├───────┼───────┼───────┼───────┼───────┼───────┼───────┼─────┼──────┤
│ PGY-3 │       │       │       │       │       │       │     │      │
├───────┼───────┼───────┼───────┼───────┼───────┼───────┼─────┼──────┤
│ Res A │ CLI   │ CLI   │ OFF   │ NF    │ NF    │ OFF   │ OFF │ 72 ✓ │
│ Res B │ ICU   │ ICU   │ ICU   │ ICU   │ OFF   │ OFF   │ OFF │ 48 ✓ │
├───────┼───────┼───────┼───────┼───────┼───────┼───────┼─────┼──────┤
│ PGY-2 │       │       │       │       │       │       │     │      │
├───────┼───────┼───────┼───────┼───────┼───────┼───────┼─────┼──────┤
│ Res C │ OFF   │ CLI   │ CLI   │ CLI   │ CLI   │ CALL  │ OFF │ 78 ⚠ │
│ Res D │ ELEC  │ ELEC  │ ELEC  │ ELEC  │ ELEC  │ OFF   │ OFF │ 40 ✓ │
└───────┴───────┴───────┴───────┴───────┴───────┴───────┴─────┴──────┘
                                              Total Coverage: 98% ✓
```

---

## Implementation Steps

### Phase 1: Core Grid (Day 1)
1. Create feature directory structure
2. Implement `SpreadsheetGrid` with static data
3. Implement `SpreadsheetCell` with selection
4. Add keyboard navigation
5. Style with Tailwind (match existing UI)

### Phase 2: Editing (Day 2)
1. Add edit mode to cells
2. Implement rotation dropdown
3. Add undo/redo with state history
4. Connect to save API

### Phase 3: Export (Day 3)
1. Implement SheetJS export
2. Add formatting via backend endpoint
3. Add export dropdown (CSV, XLSX, PDF)

### Phase 4: Polish (Day 4)
1. ACGME validation indicators
2. Conflict highlighting
3. Loading/error states
4. Responsive adjustments
5. Tests

---

## Testing Requirements

### Unit Tests
```typescript
// __tests__/SpreadsheetGrid.test.tsx
describe('SpreadsheetGrid', () => {
  it('renders correct number of rows and columns');
  it('highlights selected cell');
  it('enters edit mode on double-click');
  it('commits edit on Enter');
  it('cancels edit on Escape');
  it('navigates with arrow keys');
});

// __tests__/useExcelExport.test.ts
describe('useExcelExport', () => {
  it('generates valid xlsx file');
  it('includes all data rows');
  it('applies column headers');
});
```

### Integration Tests
```typescript
describe('Spreadsheet Editor Flow', () => {
  it('loads schedule data and displays in grid');
  it('allows editing cells and saving');
  it('exports to Excel with correct data');
  it('shows ACGME violations');
});
```

---

## Security Considerations

1. **PERSEC:** Display resident identifiers, not full names in spreadsheet
2. **Audit Trail:** Log all cell edits with user, timestamp, before/after
3. **Permissions:** Check `canEdit` before allowing modifications
4. **Validation:** Server-side validation of all changes before save
5. **Export Logging:** Log all exports for compliance

---

## Success Metrics

- [ ] Coordinators can review schedule without Excel round-trip
- [ ] Edit → Save cycle under 2 seconds
- [ ] Export generates valid, formatted `.xlsx`
- [ ] Zero data loss on save
- [ ] ACGME violations visible inline

---

## Open Questions

1. **Virtualization:** Need react-window for blocks with many residents?
2. **Offline:** Cache edits locally before save?
3. **Collaboration:** Multiple editors simultaneously? (Future)
4. **Mobile:** Touch support needed?

---

## References

- Existing: `frontend/src/components/WeeklyGridEditor.tsx`
- Existing: `frontend/src/components/admin/EditableCell.tsx`
- Existing: `frontend/src/lib/export.ts`
- Existing: `backend/app/services/xlsx_export.py`
- SheetJS Docs: https://docs.sheetjs.com/

---

*Last Updated: 2026-01-18*
