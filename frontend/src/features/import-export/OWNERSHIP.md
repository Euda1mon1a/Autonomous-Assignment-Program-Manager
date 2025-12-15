# File Ownership Matrix - Import/Export Feature

## Territory: `frontend/src/features/import-export/`

This document defines the ownership and responsibilities for files in the bulk import/export feature.

## File Matrix

| File | Owner | Description | Dependencies |
|------|-------|-------------|--------------|
| `index.ts` | Import/Export Team | Barrel exports for the feature module | All feature files |
| `types.ts` | Import/Export Team | TypeScript type definitions | `@/types/api` |
| `utils.ts` | Import/Export Team | Parsing, formatting, and utility functions | None |
| `validation.ts` | Import/Export Team | Data validation logic for imports | `types.ts`, `utils.ts` |
| `useImport.ts` | Import/Export Team | React hook for import operations | `@tanstack/react-query`, `@/lib/api`, `types.ts`, `utils.ts`, `validation.ts` |
| `useExport.ts` | Import/Export Team | React hook for export operations | `types.ts`, `utils.ts` |
| `ImportProgressIndicator.tsx` | Import/Export Team | Progress indicator component | `lucide-react`, `types.ts` |
| `ImportPreview.tsx` | Import/Export Team | Data preview table component | `lucide-react`, `types.ts` |
| `BulkImportModal.tsx` | Import/Export Team | Main import modal dialog | All hooks and components |
| `ExportPanel.tsx` | Import/Export Team | Export panel with format selection | `useExport.ts`, `types.ts` |
| `OWNERSHIP.md` | Import/Export Team | This file | None |

## Feature Responsibilities

### Core Functionality
- CSV/Excel/JSON file parsing and import
- Multi-format export (CSV, Excel, PDF, JSON)
- Data validation with error/warning handling
- Progress tracking for large imports
- Import preview and confirmation workflow

### Type Definitions (`types.ts`)
- Import data types and row interfaces
- Export format and column configurations
- Progress and validation error types
- Data mapping interfaces

### Utilities (`utils.ts`)
- File format detection
- CSV/JSON parsing
- Column name normalization
- Export content generation
- Date parsing and formatting
- Validation helper functions

### Validation (`validation.ts`)
- Row-level validation for each data type
- Cross-row validation (duplicates, overlaps)
- Required field validation
- Format validation (dates, emails, enums)

### Hooks
- `useImport`: File parsing, validation, batch import
- `useExport`: Format conversion, file download

### Components
- `BulkImportModal`: Complete import workflow UI
- `ImportPreview`: Validation results table
- `ImportProgressIndicator`: Import progress display
- `ExportPanel`: Export format selection and options

## External Dependencies

| Package | Purpose |
|---------|---------|
| `@tanstack/react-query` | Data fetching and caching |
| `lucide-react` | UI icons |
| `@/lib/api` | API client |
| `@/types/api` | Core application types |

## API Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/people/bulk` | POST | Bulk import people |
| `/assignments/bulk` | POST | Bulk import assignments |
| `/absences/bulk` | POST | Bulk import absences |
| `/schedule/import` | POST | Bulk import schedule data |

## Testing Considerations

- Unit tests for validation functions
- Unit tests for parsing utilities
- Integration tests for import workflow
- E2E tests for complete import/export flow

## Related Features

- Conflicts feature: May need conflict resolution after import
- Audit feature: Import operations should be logged
- Templates feature: Can use templates for import mapping

---

*Last updated: 2025-12-15*
*Territory owner: COMET Import/Export Team*
