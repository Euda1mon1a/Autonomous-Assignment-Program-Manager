# 3D Schedule Visualization Guide

> **Feature:** VoxelScheduleView Component
> **Location:** `frontend/src/features/voxel-schedule/`

This guide explains how to use the 3D voxel schedule visualization component in your application.

---

## Quick Start

### Basic Usage

```tsx
import { VoxelScheduleView } from '@/features/voxel-schedule';

function ScheduleVisualization() {
  return (
    <VoxelScheduleView
      startDate={new Date('2024-01-15')}
      endDate={new Date('2024-01-28')}
    />
  );
}
```

This renders an interactive 3D view of all assignments in the date range.

---

## Component Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `startDate` | `Date` | today | Start of visualization window |
| `endDate` | `Date` | today + 14 days | End of visualization window |
| `personIds` | `string[]` | all | Filter to specific people |
| `activityTypes` | `string[]` | all | Filter to specific activities |
| `onVoxelClick` | `(voxel) => void` | - | Callback when voxel is clicked |
| `onVoxelHover` | `(voxel) => void` | - | Callback when hovering voxel |
| `showConflictsOnly` | `boolean` | false | Only show conflict/violation voxels |
| `colorMode` | `string` | "activity" | Color by: "activity", "compliance", "workload" |

---

## Interactive Controls

The visualization supports mouse-based navigation:

| Action | How To |
|--------|--------|
| **Pan** | Click and drag |
| **Rotate** | Hold Shift + drag |
| **Zoom** | Mouse wheel scroll |
| **Select** | Click on a voxel |

---

## Examples

### Filter by Person

Show only specific residents' schedules:

```tsx
<VoxelScheduleView
  startDate={new Date('2024-01-15')}
  endDate={new Date('2024-01-28')}
  personIds={[
    'uuid-resident-1',
    'uuid-resident-2'
  ]}
/>
```

### Filter by Rotation Type

Show only clinic and call assignments:

```tsx
<VoxelScheduleView
  startDate={new Date('2024-01-15')}
  endDate={new Date('2024-01-28')}
  rotationTypes={['clinic', 'call']}
/>
```

### Handle Voxel Clicks

Open a modal when an assignment is clicked:

```tsx
import { useState } from 'react';
import { VoxelScheduleView } from '@/features/voxel-schedule';
import type { Voxel } from '@/features/voxel-schedule/types';

function SchedulePage() {
  const [selectedVoxel, setSelectedVoxel] = useState<Voxel | null>(null);

  const handleVoxelClick = (voxel: Voxel) => {
    setSelectedVoxel(voxel);
    // Open assignment edit modal
  };

  return (
    <>
      <VoxelScheduleView
        startDate={new Date('2024-01-15')}
        endDate={new Date('2024-01-28')}
        onVoxelClick={handleVoxelClick}
      />

      {selectedVoxel && (
        <AssignmentModal
          assignmentId={selectedVoxel.identity.assignment_id}
          onClose={() => setSelectedVoxel(null)}
        />
      )}
    </>
  );
}
```

### Show Only Conflicts

Highlight scheduling problems:

```tsx
<VoxelScheduleView
  startDate={new Date('2024-01-15')}
  endDate={new Date('2024-01-28')}
  showConflictsOnly={true}
/>
```

### Display Hover Tooltips

Show custom tooltip on hover:

```tsx
import { useState } from 'react';
import { VoxelScheduleView } from '@/features/voxel-schedule';
import type { Voxel } from '@/features/voxel-schedule/types';

function SchedulePage() {
  const [hoveredVoxel, setHoveredVoxel] = useState<Voxel | null>(null);

  return (
    <div className="relative">
      <VoxelScheduleView
        startDate={new Date('2024-01-15')}
        endDate={new Date('2024-01-28')}
        onVoxelHover={setHoveredVoxel}
      />

      {hoveredVoxel && (
        <div className="absolute top-4 right-4 bg-white p-4 rounded shadow">
          <h3>{hoveredVoxel.identity.person_name}</h3>
          <p>{hoveredVoxel.identity.rotation_name}</p>
          <p>{hoveredVoxel.identity.block_date}</p>
          {hoveredVoxel.state.is_conflict && (
            <p className="text-red-500">CONFLICT DETECTED</p>
          )}
        </div>
      )}
    </div>
  );
}
```

---

## Understanding the 3D Space

### Axes

```
         Time (X-axis)
         →→→→→→→→→→→

    ↑   ┌─────────────┐
    │  /             /│
    │ /  Activity   / │
P   │/   (Z-axis)  /  │
e   │─────────────│   │
o   │             │   │
p   │   VOXEL     │  /
l   │             │ /
e   │_____________│/
(Y)
```

- **X-axis (horizontal):** Time - Each unit is a half-day block (AM/PM)
- **Y-axis (vertical):** People - Faculty at top, then residents by PGY level
- **Z-axis (depth):** Activity type - Different layers for clinic, inpatient, etc.

### What Each Voxel Represents

Each cube in the visualization represents one **assignment**:

- **Position:** When (X), who (Y), what type (Z)
- **Color:** Activity type (blue = clinic, purple = inpatient, etc.)
- **Opacity:** Confidence score (faded = lower confidence)
- **Red X marker:** Conflict detected

---

## Color Legend

The component displays a built-in legend:

| Color | Rotation Type |
|-------|---------------|
| Blue | Clinic |
| Purple | Inpatient |
| Red | Procedures |
| Orange | Call |
| Amber | Leave |
| Gray | Conference |
| Green | Admin |
| Pink | Supervision |

---

## Conflict Detection

When two assignments occupy the same (time, person) coordinate, they appear as **overlapping voxels** marked with a red X. This indicates:

- **Double-booking:** Same person assigned to two things at once
- Requires resolution before schedule can be finalized

---

## TypeScript Types

Import types for type-safe usage:

```typescript
import type {
  Voxel,
  VoxelGridData,
  VoxelPosition,
  VoxelIdentity,
  VoxelVisual,
  VoxelState,
  VoxelScheduleViewProps,
} from '@/features/voxel-schedule/types';
```

### Voxel Interface

```typescript
interface Voxel {
  position: {
    x: number;  // Time index
    y: number;  // Person index
    z: number;  // Activity layer
  };
  identity: {
    assignment_id: string | null;
    person_id: string | null;
    person_name: string | null;
    block_date: string | null;
    block_time_of_day: 'AM' | 'PM' | null;
    rotation_name: string | null;
    rotation_type: string | null;
  };
  visual: {
    color: string;     // Hex color
    opacity: number;   // 0-1
    height: number;    // Workload intensity
  };
  state: {
    is_occupied: boolean;
    is_conflict: boolean;
    is_violation: boolean;
    violation_details: string[];
  };
  metadata: {
    role: 'primary' | 'supervising' | 'backup' | null;
    confidence: number;
    hours: number;
  };
}
```

---

## Integration with Other Components

### With Date Range Picker

```tsx
import { useState } from 'react';
import { DateRangePicker } from '@/components/ui/DateRangePicker';
import { VoxelScheduleView } from '@/features/voxel-schedule';

function SchedulePage() {
  const [dateRange, setDateRange] = useState({
    start: new Date(),
    end: addDays(new Date(), 14),
  });

  return (
    <div>
      <DateRangePicker
        value={dateRange}
        onChange={setDateRange}
      />
      <VoxelScheduleView
        startDate={dateRange.start}
        endDate={dateRange.end}
      />
    </div>
  );
}
```

### With Person Filter

```tsx
import { PersonSelect } from '@/components/schedule/PersonSelect';
import { VoxelScheduleView } from '@/features/voxel-schedule';

function SchedulePage() {
  const [selectedPersons, setSelectedPersons] = useState<string[]>([]);

  return (
    <div>
      <PersonSelect
        value={selectedPersons}
        onChange={setSelectedPersons}
        multiple
      />
      <VoxelScheduleView
        startDate={new Date()}
        endDate={addDays(new Date(), 14)}
        personIds={selectedPersons.length > 0 ? selectedPersons : undefined}
      />
    </div>
  );
}
```

---

## Performance Considerations

- **Date range:** Larger date ranges = more voxels = slower rendering
- **Recommended:** 2-4 weeks at a time for smooth interaction
- **Large datasets:** Consider filtering by person or rotation type
- **Caching:** API responses are cached for 60 seconds

---

## Accessibility

- Keyboard navigation is not yet supported (planned for future)
- Color-blind friendly palette used where possible
- Hover tooltips provide text alternatives to color-only information

---

## Troubleshooting

### Visualization is empty

1. Check date range contains data
2. Verify API endpoint is accessible
3. Check browser console for errors

### Voxels not rendering

1. Ensure canvas element is visible (not `display: none`)
2. Check parent container has defined height
3. Verify WebGL is enabled in browser

### Performance is slow

1. Reduce date range
2. Filter to fewer people/rotation types
3. Consider using the 2D heatmap for large datasets

---

## Related Documentation

- [3D Voxel Visualization Architecture](/docs/architecture/3d-voxel-visualization.md)
- [Visualization API Reference](/docs/api/visualization.md)
- [Frontend Architecture](/docs/architecture/frontend.md)
