***REMOVED*** Block Schedule Drag GUI Components

> **Owner**: Schedule Team
> **Created**: 2025-12-17
> **Status**: Active

***REMOVED******REMOVED*** Overview

This directory contains drag-and-drop schedule components for annual scheduling views, enabling visual manipulation of assignments across the academic year.

***REMOVED******REMOVED*** Components

***REMOVED******REMOVED******REMOVED*** ScheduleDragProvider.tsx

**Purpose**: Context provider and drag-and-drop infrastructure using dnd-kit.

**Features**:
- DndContext wrapper with collision detection
- Drag state management (activeAssignment, overTarget)
- API integration for moving assignments (PUT /assignments/{id})
- Optimistic UI updates with rollback on error
- Toast feedback for success/warning/error states
- Drag preview overlay

**Props**:
- `blockLookup: Map<string, Block>` - Lookup table for blocks
- `onAssignmentMove?: (assignmentId, newBlockId) => void` - Optional callback

***REMOVED******REMOVED******REMOVED*** DraggableBlockCell.tsx

**Purpose**: Individual schedule cell with drag-and-drop capability.

**Features**:
- Combined draggable/droppable functionality
- Color-coded by activity type
- Visual feedback for drag states (hover, over, dragging)
- Compact mode for year-at-a-glance views
- Weekend/holiday/today highlighting

**Props**:
- `assignment?: CellAssignment` - Assignment data
- `personId, personName` - Person context
- `date, timeOfDay` - Cell position (date + AM/PM)
- `isWeekend, isToday, isHoliday` - Visual modifiers
- `compact?: boolean` - Compact display mode

***REMOVED******REMOVED******REMOVED*** ResidentAcademicYearView.tsx

**Purpose**: Full academic year view for resident scheduling.

**Features**:
- Academic year range (July 1 - June 30)
- Residents grouped by PGY level
- 52 weeks with month headers
- Zoom toggle (compact/normal)
- Today navigation and auto-scroll
- Color-coded activity legend

**Props**:
- `academicYear?: number` - Year (e.g., 2024 for AY 2024-2025)
- `startMonth?: number` - Start month (default: 6 = July)

<<<<<<< HEAD
***REMOVED******REMOVED******REMOVED*** FacultyInpatientWeeksView.tsx
=======
***REMOVED******REMOVED******REMOVED***InpatientWeeksView.tsx
>>>>>>> origin/docs/session-14-summary

**Purpose**: Faculty-focused view for inpatient service week management.

**Features**:
- Faculty sorted by inpatient week count
- Summary statistics (total, avg, max, min weeks)
- Toggle between all activities and inpatient-only
- Same drag-and-drop as resident view

**Props**:
- `academicYear?: number` - Year
- `startMonth?: number` - Start month

***REMOVED******REMOVED*** Dependencies

- `@dnd-kit/core` - Core drag-and-drop
- `@dnd-kit/utilities` - CSS transforms, utilities
- `@dnd-kit/sortable` - Sortable presets
- `@dnd-kit/modifiers` - Drag modifiers

***REMOVED******REMOVED*** API Integration

**Endpoint Used**: `PUT /assignments/{assignment_id}`

**Request**: `{ block_id: string }`

**Response**: Updated assignment with warnings (ACGME violations)

***REMOVED******REMOVED*** Color Scheme

| Activity Type | Color |
|--------------|-------|
| Clinic | Blue (***REMOVED***3b82f6) |
| Inpatient | Purple (***REMOVED***8b5cf6) |
| Procedure | Red (***REMOVED***ef4444) |
| Call | Orange (***REMOVED***f97316) |
| Elective | Green (***REMOVED***10b981) |
| Leave/Vacation | Amber (***REMOVED***f59e0b) |
| Conference | Gray (***REMOVED***6b7280) |

***REMOVED******REMOVED*** Testing

Components should be tested for:
- Drag start/end event handling
- Drop zone validation (same person only)
- API mutation calls
- Optimistic update/rollback
- Visual feedback states

***REMOVED******REMOVED*** Future Improvements

- Keyboard accessibility for drag operations
- Multi-select drag (move multiple assignments)
- Undo/redo functionality
- Bulk operations (swap weeks)
- Export drag history for audit

***REMOVED******REMOVED*** Related Documentation

- [USER_GUIDE.md](../../../../../USER_GUIDE.md) - User documentation
- [CHANGELOG.md](../../../../../CHANGELOG.md) - Version history
