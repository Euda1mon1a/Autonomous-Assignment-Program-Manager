# Import/Export System Architecture

> **Last Updated:** 2025-12-28
> **Status:** Production
> **Reviewed:** ChatGPT Pulse Analysis + Security Audit

---

## Overview

The Residency Scheduler provides bidirectional data exchange via multiple formats. This document describes the architecture, security considerations, and implementation details.

---

## Export System

### Supported Formats

| Format | Backend | Frontend | True Format |
|--------|---------|----------|-------------|
| **CSV** | ✅ | ✅ | Real CSV |
| **JSON** | ✅ | ✅ | Real JSON |
| **XLSX** | ✅ | ⚠️ Workaround | Backend: Real XLSX, Frontend: TSV |
| **PDF** | ✅ | ✅ (print dialog) | HTML-to-Print |

### Backend Excel Export (Recommended)

**Library:** `openpyxl==3.1.5` (Python)

**Endpoint:** `GET /export/schedule/xlsx`

**Features:**
- True `.xlsx` format (Office Open XML)
- Proper cell formatting, column widths
- Multi-sheet support
- Date formatting
- Military schedule compliance formatting

**Code Location:** `backend/app/api/routes/export.py`

```python
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill

@router.get("/schedule/xlsx")
async def export_schedule_xlsx(
    start_date: date,
    end_date: date,
    block_number: Optional[int] = None,
):
    wb = Workbook()
    ws = wb.active
    # ... generate Excel content
    return StreamingResponse(
        io.BytesIO(save_virtual_workbook(wb)),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
```

### Frontend Excel Export (Fallback)

**Library:** None (TSV workaround)

**Location:** `frontend/src/features/import-export/useExport.ts`

**Implementation:**
```typescript
// Generates TSV with .xls extension (Excel can open TSV files)
const tsvContent = content.replace(/,/g, '\t');
const blob = new Blob(['\ufeff' + tsvContent], {
  type: 'application/vnd.ms-excel;charset=utf-8;',
});
```

**Limitations:**
- Not a true `.xlsx` file
- No cell formatting
- No multi-sheet support
- May have encoding issues with special characters

**When to Use:**
- Backend is unavailable
- Quick local export needed
- Data is simple (no formatting required)

### Frontend → Backend Excel Export

**Location:** `frontend/src/lib/export.ts`

```typescript
export async function exportToLegacyXlsx(
  startDate: string,
  endDate: string,
  blockNumber?: number,
): Promise<void> {
  const url = `${apiUrl}/export/schedule/xlsx?${params}`;
  const response = await fetch(url);
  const blob = await response.blob();
  // Download blob as file
}
```

---

## Import System

### Supported Formats

| Format | Backend | Frontend | Parser |
|--------|---------|----------|--------|
| **CSV** | ✅ | ✅ | Custom parser |
| **JSON** | ✅ | ✅ | `JSON.parse()` |
| **XLSX** | ✅ | ❌ | `openpyxl` |
| **XLS** | ❌ | ❌ | Not supported |

### Backend Excel Import

**Library:** `openpyxl==3.1.5`

**Location:** `backend/app/services/xlsx_import.py`

**Features:**
- Fuzzy-tolerant parsing (handles human-edited spreadsheets)
- Semantic anchor detection (finds headers by content, not position)
- Merged cell handling
- Date format auto-detection
- Name fuzzy matching against database

**Key Classes:**

```python
class ClinicScheduleImporter:
    """Imports clinic schedules from Excel files."""

    def import_file(
        self,
        file_path: str | None = None,
        file_bytes: bytes | None = None,
        sheet_name: str | None = None,
    ) -> ImportResult: ...

class BlockScheduleParser:
    """Fuzzy-tolerant parser for block rotation spreadsheets."""

    def parse_block_sheet(
        self,
        filepath: str | Path,
        sheet_name: str,
        expected_block: int | None = None,
    ) -> BlockParseResult: ...
```

### Frontend Import

**Location:** `frontend/src/features/import-export/`

**Files:**
- `useImport.ts` - React hook for import operations
- `utils.ts` - File parsing utilities
- `validation.ts` - Data validation
- `types.ts` - Type definitions

**Supported Operations:**
- CSV parsing with column detection
- JSON parsing
- Data type detection (people, assignments, absences, schedules)
- Column name normalization
- Validation with error reporting

---

## Security Considerations

### File Upload Validation

| Check | Backend | Frontend |
|-------|---------|----------|
| File size limit | 10MB | 10MB |
| Extension whitelist | `.xlsx`, `.csv`, `.json` | `.xlsx`, `.xls`, `.csv`, `.json` |
| Content-type validation | ✅ | ✅ |
| Magic bytes check | ❌ (recommended) | N/A |

### ⚠️ Known Issues

1. **`.xls` Extension Mismatch**
   - Frontend accepts `.xls` files
   - Backend `openpyxl` only supports `.xlsx`
   - Legacy `.xls` files will fail with parse error
   - **Fix:** Remove `.xls` from frontend or add `xlrd` to backend

2. **Sheet Listing Endpoint**
   - May lack size validation
   - Could allow oversized file parsing
   - **Fix:** Reuse `validate_excel_upload()` helper

### Data Sanitization

```python
# PII fields are masked in logs
SENSITIVE_FIELDS = ["ssn", "email", "phone", "mrn"]

# Validation via Pydantic schemas
class PersonImport(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: Optional[EmailStr] = None
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Next.js)                      │
├─────────────────────────────────────────────────────────────┤
│  useExport.ts          │  useImport.ts                      │
│  ├─ exportToCSV()      │  ├─ parseCSV()                     │
│  ├─ exportToJSON()     │  ├─ parseJSON()                    │
│  ├─ exportToExcel()    │  └─ detectDataType()               │
│  │   (TSV workaround)  │                                     │
│  └─ exportToPDF()      │                                     │
│         │              │         │                           │
│         ▼              │         ▼                           │
│  exportToLegacyXlsx()──┼─────────┼───────────────────────────│
│         │              │         │                           │
└─────────┼──────────────┼─────────┼───────────────────────────┘
          │              │         │
          ▼              │         ▼
┌─────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                       │
├─────────────────────────────────────────────────────────────┤
│  /export/schedule/xlsx │  /import/schedule                   │
│         │              │         │                           │
│         ▼              │         ▼                           │
│  ┌─────────────┐       │  ┌─────────────────────┐            │
│  │  openpyxl   │       │  │  xlsx_import.py     │            │
│  │  (Python)   │       │  │  ├─ ClinicImporter  │            │
│  └─────────────┘       │  │  └─ BlockParser     │            │
│                        │  └─────────────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

---

## Dependency Summary

### Backend (Python)

| Package | Version | Purpose |
|---------|---------|---------|
| `openpyxl` | 3.1.5 | Excel read/write (.xlsx only) |

### Frontend (TypeScript)

| Package | Version | Purpose |
|---------|---------|---------|
| None | - | No Excel library (uses TSV workaround) |

### NOT Used

| Package | Reason |
|---------|--------|
| `xlsx` (SheetJS) | Security vulnerabilities (CVE-2023-30533, CVE-2024-22363) |
| `xlrd` | Legacy .xls not required |
| `exceljs` | Not needed with backend handling |

---

## Recommendations

### Short Term

1. **Remove `.xls` from frontend extension check** - Prevents confusing errors
2. **Add file size validation to all upload endpoints** - Consistent security

### Medium Term

1. **Add magic bytes validation** - Verify file content matches extension
2. **Implement chunked upload** - Support larger files without memory issues
3. **Add import preview** - Show parsed data before committing

### Long Term

1. **Consider `exceljs` for frontend** - True .xlsx generation if needed
2. **Add import templates** - Pre-formatted Excel files for users
3. **Implement async import** - Background processing for large files

---

## Related Documentation

- [Security Pattern Audit](../security/SECURITY_PATTERN_AUDIT.md) - Dependency vulnerability analysis
- [API Reference](../api/export-endpoints.md) - Export API documentation
- [User Guide](../user-guide/importing-data.md) - End-user import instructions

---

*Architecture document - Last reviewed 2025-12-28*
