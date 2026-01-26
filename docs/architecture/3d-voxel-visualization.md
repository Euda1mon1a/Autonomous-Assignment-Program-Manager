# 3D Voxel Schedule Visualization

> **Status:** Novel Implementation
> **Module:** `backend/app/visualization/`, `frontend/src/features/voxel-schedule/`
> **Added:** December 2024

---

## Overview

The 3D Voxel Schedule Visualization is a novel approach to schedule visualization that represents assignments as voxels in a three-dimensional space. This enables **spatial reasoning** about scheduling problems that are difficult to perceive in traditional 2D grids.

### The Core Insight

Traditional schedule views are 2D grids:
- **X-axis:** Time (days/weeks)
- **Y-axis:** People (residents/faculty)
- **Cell:** Single assignment

This works for viewing, but analysis requires mental effort. The 3D approach adds a third dimension:

```
         Time (X)
         │
         │    ┌──────────────────────┐
         │   /                      /│
         │  /    Activity Layers   / │
         │ /        (Z-axis)      /  │
         │/______________________/   │
People   │                       │   │
 (Y)     │   VOXEL = Assignment  │   │
         │                       │  /
         │                       │ /
         │_______________________│/
```

**Axis Mapping:**
- **X-axis:** Time (blocks/dates) - 730 blocks per academic year
- **Y-axis:** People (faculty first, then residents by PGY level)
- **Z-axis:** Activity type (clinic, inpatient, procedures, call, leave, etc.)

---

## What 3D Unlocks

### 1. Collision Detection = Double-Booking

In 2D, you scan cells row by row looking for conflicts. In 3D:

```python
# Multiple voxels at same (x, y) position = CONFLICT
# Visually obvious as overlapping cubes
conflicts = grid.detect_conflicts()
```

Two assignments for the same person at the same time appear as **voxels occupying the same space** - immediately visible.

### 2. Empty Space = Coverage Gaps

In 2D, you count cells per column. In 3D:

```python
# Empty regions in the voxel space = coverage gaps
gaps = grid.get_coverage_gaps()
```

Understaffed time slots appear as **literal empty space** in the visualization.

### 3. Layer Analysis = Supervision Compliance

ACGME requires supervision ratios (PGY-1: 1 faculty per 2 residents). In 3D:

- **Resident assignments:** Lower Y-indices (bottom of grid)
- **Faculty assignments:** Higher Y-indices (top of grid)
- **Supervision gaps:** Visible when resident layers have no overlapping faculty layers

### 4. Volume Distribution = Workload Balance

```python
# Total hours per person = volume in their Y-slice
workload = grid.calculate_workload_distribution()
```

Workload imbalance appears as **uneven terrain** across the Y-axis.

---

## Architecture

### Backend Components

```
backend/app/visualization/
├── __init__.py              # Module exports
└── schedule_voxel.py        # Core implementation
    ├── ActivityLayer        # Z-axis enum (clinic, inpatient, etc.)
    ├── VoxelColor           # RGBA color handling
    ├── ScheduleVoxel        # Single voxel dataclass
    ├── ScheduleVoxelGrid    # 3D grid container
    └── ScheduleVoxelTransformer  # Assignment → Voxel conversion
```

### Data Flow

```
Database Models                    3D Voxel Grid
┌─────────────┐                   ┌─────────────────┐
│ Assignment  │                   │ ScheduleVoxel   │
│ - person_id │──┐                │ - x (time)      │
│ - block_id  │  │                │ - y (person)    │
│ - rotation  │  │                │ - z (activity)  │
└─────────────┘  │                │ - color         │
                 │   Transform    │ - opacity       │
┌─────────────┐  │──────────────► │ - is_conflict   │
│ Person      │  │                │ - is_violation  │
│ - type      │──┤                └─────────────────┘
│ - pgy_level │  │                        │
└─────────────┘  │                        ▼
                 │                ┌─────────────────┐
┌─────────────┐  │                │ScheduleVoxelGrid│
│ Block       │──┘                │ - dimensions    │
│ - date      │                   │ - voxels[]      │
│ - time_of_day                   │ - statistics    │
└─────────────┘                   └─────────────────┘
```

### Frontend Components

```
frontend/src/features/voxel-schedule/
├── index.ts                 # Exports
├── types.ts                 # TypeScript interfaces
├── VoxelScheduleView.tsx    # Main React component
└── __tests__/               # Component tests
```

The frontend uses a **canvas-based isometric renderer** (no Three.js dependency) for lightweight, fast visualization.

---

## API Reference

### GET `/api/visualization/voxel-grid`

Generate 3D voxel grid representation of schedule data.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | date | Yes | Start of date range |
| `end_date` | date | Yes | End of date range |
| `person_ids` | UUID[] | No | Filter to specific people |
| `rotation_types` | string[] | No | Filter to specific rotation types |
| `include_violations` | bool | No | Include ACGME violation markers (default: true) |

**Response:**

```json
{
  "dimensions": {
    "x_size": 28,
    "y_size": 15,
    "z_size": 6,
    "x_labels": ["2024-01-15 AM", "2024-01-15 PM", ...],
    "y_labels": ["Dr. Smith", "Resident A", ...],
    "z_labels": ["clinic", "inpatient", "procedures", ...]
  },
  "voxels": [
    {
      "position": {"x": 0, "y": 0, "z": 0},
      "identity": {
        "assignment_id": "uuid",
        "person_name": "Dr. Smith",
        "block_date": "2024-01-15",
        "rotation_name": "Morning Clinic"
      },
      "visual": {
        "color": "#3B82F6",
        "opacity": 1.0,
        "height": 1.0
      },
      "state": {
        "is_occupied": true,
        "is_conflict": false,
        "is_violation": false
      }
    }
  ],
  "statistics": {
    "total_assignments": 150,
    "total_conflicts": 2,
    "total_violations": 0,
    "coverage_percentage": 68.5
  },
  "date_range": {
    "start_date": "2024-01-15",
    "end_date": "2024-01-28"
  }
}
```

### GET `/api/visualization/voxel-grid/conflicts`

Get schedule conflicts detected through spatial collision analysis.

**Response:**

```json
{
  "total_conflicts": 2,
  "conflict_voxels": [
    {
      "position": {"x": 5, "y": 3, "z": 0},
      "identity": {...},
      "details": ["Double-booked: Clinic and Call"]
    }
  ],
  "conflict_positions": [
    {"x": 5, "y": 3}
  ]
}
```

### GET `/api/visualization/voxel-grid/coverage-gaps`

Identify coverage gaps using 3D voxel space analysis.

**Response:**

```json
{
  "total_gaps": 3,
  "total_warnings": 5,
  "gaps": [
    {
      "x": 12,
      "time_label": "2024-01-21 PM",
      "coverage_count": 0,
      "severity": "critical"
    }
  ]
}
```

---

## Frontend Usage

### Basic Usage

```tsx
import { VoxelScheduleView } from '@/features/voxel-schedule';

function SchedulePage() {
  return (
    <VoxelScheduleView
      startDate={new Date('2024-01-15')}
      endDate={new Date('2024-01-28')}
    />
  );
}
```

### With Interaction Handlers

```tsx
<VoxelScheduleView
  startDate={startDate}
  endDate={endDate}
  onVoxelClick={(voxel) => {
    console.log('Clicked:', voxel.identity.person_name);
    openAssignmentModal(voxel.identity.assignment_id);
  }}
  onVoxelHover={(voxel) => {
    setTooltipData(voxel);
  }}
  showConflictsOnly={showConflictsOnly}
/>
```

### Controls

| Action | Control |
|--------|---------|
| Pan | Drag mouse |
| Rotate | Shift + Drag |
| Zoom | Mouse wheel |
| Select | Click voxel |

---

## Color Coding

### Rotation Type Colors

| Rotation Type | Color | Hex |
|----------|-------|-----|
| Clinic | Blue | `#3B82F6` |
| Inpatient | Purple | `#8B5CF6` |
| Procedures | Red | `#EF4444` |
| Conference | Gray | `#6B7280` |
| Call | Orange | `#F97316` |
| Leave | Amber | `#F59E0B` |
| Admin | Green | `#10B981` |
| Supervision | Pink | `#EC4899` |

### Compliance Status Override

When violations exist, rotation colors are overridden:

| Status | Color | Meaning |
|--------|-------|---------|
| Compliant | Green | All ACGME rules satisfied |
| Warning | Yellow | Approaching limit |
| Violation | Red | Rule violated |
| Critical | Dark Red | Multiple violations |

---

## Analysis Methods

### Conflict Detection

```python
from app.visualization import transform_schedule_to_voxels

grid = transform_schedule_to_voxels(assignments, persons, blocks)

# Detect double-bookings via spatial collision
conflicts = grid.detect_conflicts()
# Returns: List of (voxel1, voxel2) conflict pairs
```

### Coverage Analysis

```python
# Find empty time slots
gaps = grid.get_coverage_gaps()
# Returns: List of (x, y, z) empty positions

# Also available via API
# GET /visualization/voxel-grid/coverage-gaps
```

### Workload Distribution

```python
# Calculate hours per person
workload = grid.calculate_workload_distribution()
# Returns: {person_index: total_hours}

# Identify overloaded individuals
overloaded = [y for y, hours in workload.items() if hours > 80]
```

### NumPy Integration

```python
# Convert to 3D numpy array for advanced analysis
import numpy as np

numpy_grid = grid.to_numpy_grid()
# Shape: (x_size, y_size, z_size)
# Values: 0=empty, 1=occupied, 2=conflict, 3=violation

# Example: Find all conflict positions
conflict_positions = np.where(numpy_grid == 2)
```

---

## Research Context

### Why This Is Novel

Research found **no existing 3D schedule visualization library**:

- **Space-time cubes** exist for GIS (ArcGIS, Plotly) but focus on geographic data
- **3D Gantt charts** are requested but not implemented in any library
- **Voxel libraries** (matplotlib, PyVista) are general-purpose, not schedule-aware

This implementation is purpose-built for workforce scheduling with:
- Activity-type layering on Z-axis
- Compliance-aware coloring
- Spatial conflict detection
- ACGME-specific analysis

### References

- [Space-Time Cubes with Python](https://medium.com/@nickgardner_68929/mastering-space-time-cubes-with-python-a-practical-guide-8c03cdd6e1d) - Conceptual foundation
- [Matplotlib Voxels](https://matplotlib.org/stable/gallery/mplot3d/voxels.html) - 3D plotting reference
- [Isometric Projection](https://en.wikipedia.org/wiki/Isometric_projection) - Rendering technique used

---

## Future Enhancements

### Potential Extensions

1. **WebGL/Three.js Upgrade**
   - Replace canvas renderer for smoother interactions
   - Add real-time shadows and lighting
   - Enable VR/AR viewing

2. **Time Animation**
   - Animate schedule changes over time
   - "Play" through a year to see rotation patterns

3. **Supervision Layer Highlighting**
   - Automatically highlight when PGY-1 assignments lack faculty coverage
   - Visual "connection lines" between supervised pairs

4. **What-If Simulation**
   - Drag voxels to simulate reassignments
   - Instantly see ripple effects in 3D

5. **Volume-Based Metrics**
   - Calculate "schedule density" per region
   - Identify clustering vs. spread of assignments

---

## Files

| File | Purpose |
|------|---------|
| `backend/app/visualization/__init__.py` | Module exports |
| `backend/app/visualization/schedule_voxel.py` | Core implementation |
| `backend/app/api/routes/visualization.py` | API endpoints (lines 405-706) |
| `backend/tests/visualization/test_schedule_voxel.py` | Unit tests |
| `frontend/src/features/voxel-schedule/VoxelScheduleView.tsx` | React component |
| `frontend/src/features/voxel-schedule/types.ts` | TypeScript types |
