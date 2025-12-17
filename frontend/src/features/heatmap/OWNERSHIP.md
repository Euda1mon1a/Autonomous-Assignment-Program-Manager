# File Ownership Matrix: frontend/src/features/heatmap/

## Territory: Heatmap Visualization
**Owner**: Terminal-4 (Heatmap-Frontend)
**Created**: 2025-12-17
**Branch**: claude/assess-project-status-Ia9J6

## Files and Responsibilities

| File | Purpose | Dependencies | Exports |
|------|---------|--------------|---------|
| `types.ts` | Type definitions, interfaces, constants | None | All heatmap types, constants, utility functions |
| `hooks.ts` | React Query hooks for API integration | `@tanstack/react-query`, `@/lib/api`, `./types` | Query hooks, mutation hooks, utility hooks |
| `HeatmapView.tsx` | Main Plotly heatmap visualization | `react-plotly.js`, `next/dynamic`, `lucide-react`, `./types` | `HeatmapView`, `HeatmapViewSkeleton` |
| `HeatmapControls.tsx` | Filter and control UI | `lucide-react`, `./types` | `HeatmapControls` |
| `HeatmapLegend.tsx` | Color scale and legend display | `lucide-react`, `./types` | `HeatmapLegend`, `CompactHeatmapLegend` |
| `index.ts` | Barrel exports | All above files | All public exports |
| `OWNERSHIP.md` | Documentation and ownership | None | N/A |

## Feature Summary

### Components

1. **HeatmapView** - Main visualization component
   - Interactive Plotly.js heatmap
   - Responsive sizing and layout
   - Hover tooltips with cell details
   - Click handlers for drill-down
   - Loading, error, and empty states
   - Export functionality via Plotly
   - Color scale customization
   - Annotations support

2. **HeatmapControls** - Comprehensive filtering UI
   - Date range picker (start/end dates)
   - Person multi-select filter
   - Rotation multi-select filter
   - Include FMIT toggle
   - Group by selector (day/week/person/rotation)
   - Export button
   - Expandable filter panel
   - Active filter count badges
   - Clear filters functionality

3. **HeatmapLegend** - Visual legend components
   - Color scale gradient with labels
   - Activity type indicators
   - Coverage status indicators
   - View mode descriptions
   - Compact inline variant
   - Customizable display options

### Hooks

- `useHeatmapData` - Fetch generic heatmap with filters
- `useCoverageHeatmap` - Fetch rotation coverage over time
- `useWorkloadHeatmap` - Fetch person workload distribution
- `useRotationCoverageComparison` - Fetch rotation comparison
- `useAvailableRotations` - Fetch rotations for filtering
- `useExportHeatmap` - Export heatmap mutation
- `useDownloadHeatmap` - Download heatmap file with utilities
- `usePrefetchHeatmap` - Prefetch for better UX
- `useInvalidateHeatmaps` - Invalidate queries after changes

### Types

Core types:
- `HeatmapData` - Main data structure (x_labels, y_labels, z_values, color_scale, annotations)
- `HeatmapFilters` - Filter configuration
- `HeatmapGroupBy` - Grouping options enum
- `HeatmapViewMode` - View mode enum
- `ColorScale` - Color scale definition
- `HeatmapAnnotation` - Cell annotation structure

Response types:
- `HeatmapResponse` - Generic heatmap response
- `CoverageHeatmapResponse` - Coverage with metrics
- `WorkloadHeatmapResponse` - Workload with metrics
- `CoverageMetrics` - Coverage statistics
- `WorkloadMetrics` - Workload statistics

Export types:
- `HeatmapExportConfig` - Export configuration
- `HeatmapExportFormat` - Export format enum (png, svg, pdf, json)

## Integration Points

### API Endpoints Expected
- `GET /api/visualization/heatmap` - Generic heatmap with filters
- `GET /api/visualization/heatmap/coverage` - Coverage heatmap
- `GET /api/visualization/heatmap/workload` - Workload heatmap
- `GET /api/visualization/heatmap/rotation-comparison` - Rotation comparison
- `GET /api/visualization/rotations` - Available rotations for filtering
- `POST /api/visualization/heatmap/export` - Export heatmap as file

### API Request Parameters

Coverage heatmap:
```
GET /api/visualization/heatmap/coverage?start_date=2025-01-01&end_date=2025-01-31
```

Workload heatmap:
```
GET /api/visualization/heatmap/workload?start_date=2025-01-01&end_date=2025-01-31&person_ids=1,2,3
```

Custom heatmap with filters:
```
GET /api/visualization/heatmap?start_date=2025-01-01&end_date=2025-01-31&person_ids=1,2&rotation_ids=5,6&include_fmit=true&group_by=week
```

### API Response Format

Heatmap data structure:
```typescript
{
  "heatmap": {
    "x_labels": ["2025-01-01", "2025-01-02", ...],
    "y_labels": ["Rotation A", "Rotation B", ...],
    "z_values": [[0.8, 0.9, ...], [0.7, 1.0, ...], ...],
    "color_scale": {
      "min": 0,
      "max": 100,
      "colors": ["#ef4444", "#fbbf24", "#22c55e"],
      "labels": ["Low", "Medium", "High"]
    },
    "annotations": [
      {"x": 0, "y": 0, "text": "80%", "font": {"color": "white", "size": 10}}
    ],
    "title": "Rotation Coverage Heatmap",
    "x_axis_label": "Date",
    "y_axis_label": "Rotation"
  },
  "metrics": {
    "total_slots": 100,
    "filled_slots": 85,
    "coverage_percentage": 85.0,
    "gaps": [...]
  }
}
```

### Shared Dependencies
- `@/lib/api` - API client utilities (get, post)
- `@tanstack/react-query` - Data fetching and caching
- `react-plotly.js` - Plotly.js React wrapper for heatmaps
- `plotly.js` - Plotly.js core library
- `next/dynamic` - Dynamic imports for SSR compatibility
- `lucide-react` - Icons
- `date-fns` - Date formatting (used in consuming pages)

### Required Package Additions

The following packages need to be added to `frontend/package.json`:

```json
{
  "dependencies": {
    "react-plotly.js": "^2.6.0",
    "plotly.js": "^2.27.0"
  }
}
```

Note: As instructed, the packages are not yet added to package.json. They should be installed via:
```bash
npm install react-plotly.js plotly.js
```

## Non-Overlapping Boundaries

This module is exclusively responsible for:
- Heatmap visualization rendering
- Heatmap filtering and controls
- Heatmap legend display
- Heatmap data fetching
- Heatmap export functionality
- Coverage and workload visualization
- Interactive drill-down via cell clicks

This module does NOT handle:
- Schedule generation (handled by schedule feature)
- Assignment creation/editing (handled by assignments feature)
- Audit logging (handled by audit feature)
- Conflict resolution (handled by conflicts feature)
- Actual heatmap data computation (backend responsibility)
- User authentication (handled by auth feature)

## Usage Example

### Basic Coverage Heatmap

```tsx
import {
  HeatmapView,
  HeatmapControls,
  HeatmapLegend,
  useCoverageHeatmap,
  getDefaultDateRange
} from '@/features/heatmap';

function CoverageHeatmapPage() {
  const [dateRange, setDateRange] = useState(getDefaultDateRange());
  const { data, isLoading, error } = useCoverageHeatmap(dateRange);

  return (
    <div className="space-y-4">
      <HeatmapControls
        filters={{}}
        onFiltersChange={() => {}}
        dateRange={dateRange}
        onDateRangeChange={setDateRange}
      />
      <div className="grid grid-cols-4 gap-4">
        <div className="col-span-3">
          <HeatmapView
            data={data?.heatmap}
            isLoading={isLoading}
            error={error}
          />
        </div>
        <div>
          <HeatmapLegend viewMode="coverage" />
        </div>
      </div>
    </div>
  );
}
```

### Workload Heatmap with Filters

```tsx
import {
  HeatmapView,
  HeatmapControls,
  useWorkloadHeatmap,
  usePeople
} from '@/features/heatmap';

function WorkloadHeatmapPage() {
  const [filters, setFilters] = useState<HeatmapFilters>({
    group_by: 'person',
    include_fmit: true,
  });
  const [dateRange, setDateRange] = useState(getDefaultDateRange());
  const { data: people } = usePeople();
  const { data, isLoading } = useWorkloadHeatmap(
    filters.person_ids || [],
    dateRange
  );

  return (
    <div>
      <HeatmapControls
        filters={filters}
        onFiltersChange={setFilters}
        dateRange={dateRange}
        onDateRangeChange={setDateRange}
        availablePersons={people?.items}
      />
      <HeatmapView
        data={data?.heatmap}
        isLoading={isLoading}
        onCellClick={(cell) => console.log('Clicked:', cell)}
      />
    </div>
  );
}
```

## Future Enhancements

Potential future additions (NOT part of current scope):
- Real-time updates via WebSocket
- Custom color scale editor
- Multiple heatmap comparison view
- Statistical overlays (mean, median lines)
- Drill-down modal with detailed data
- Saved filter presets
- Collaborative annotations
- Animation for time-series data
- 3D surface plot option
