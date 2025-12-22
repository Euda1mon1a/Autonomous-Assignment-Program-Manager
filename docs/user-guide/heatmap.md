# Schedule Heatmap

The heatmap provides visual analytics for schedule coverage and workload distribution.

---

## Overview

Navigate to **Heatmap** from the main navigation to see a color-coded visualization of your schedule data. The heatmap helps identify patterns, gaps, and imbalances that might not be obvious in traditional schedule views.

---

## View Modes

### Coverage View

Shows staffing levels across time and locations:

- **Color Scale**: Red (understaffed) → Yellow (adequate) → Green (well-staffed)
- **Axes**: Time (columns) × Locations (rows)
- **Values**: Number of staff assigned

### Workload View

Shows individual workload distribution:

- **Color Scale**: Green (light load) → Yellow (moderate) → Red (heavy load)
- **Axes**: Time (columns) × People (rows)
- **Values**: Hours or shifts assigned

---

## Controls

### Date Range

Select the time period to analyze:

- **Quick Picks**: This Week, This Month, This Quarter
- **Custom Range**: Select specific start and end dates

### Grouping

Choose how to aggregate data:

| Group By | Description |
|----------|-------------|
| **Day** | One column per day |
| **Week** | One column per week |
| **Month** | One column per month |

### Filters

Narrow the view:

- **Rotation Type**: Filter by specific rotations
- **PGY Level**: Filter by training year
- **Location**: Filter by specific locations

---

## Reading the Heatmap

### Color Interpretation

**Coverage Mode:**
- Dark Red: Critical understaffing
- Light Red: Below minimum
- Yellow: At minimum
- Light Green: Adequate
- Dark Green: Well-staffed

**Workload Mode:**
- Dark Green: Light workload
- Yellow: Moderate workload
- Orange: Heavy workload
- Red: Potential overwork

### Hover Details

Hover over any cell to see:
- Exact count or hours
- List of assigned personnel
- Comparison to target

### Click Actions

Click a cell to:
- Drill down to detailed view
- Navigate to that day's schedule
- See list of assignments

---

## Legend

The legend panel shows:

- Color scale with value ranges
- Activity type colors (if applicable)
- Coverage indicator meanings

---

## Export Options

Export heatmap data:

| Format | Use Case |
|--------|----------|
| **PNG/SVG** | Presentations, reports |
| **CSV** | Data analysis |
| **PDF** | Printable reports |

To export:
1. Configure the view you want
2. Click **Export** button
3. Select format and download

---

## Common Patterns

### Coverage Gaps

Look for red cells indicating understaffing:
- **Horizontal patterns**: Problem at a specific location
- **Vertical patterns**: Problem on specific days
- **Scattered**: Random gaps to address

### Workload Imbalance

Look for uneven color distribution:
- **Dark rows**: Overworked individuals
- **Light rows**: Underutilized personnel
- **Consistent colors**: Good balance

### Seasonal Patterns

Compare across months to identify:
- Conference season impacts
- Holiday coverage challenges
- Rotation cycle effects

---

## Best Practices

!!! tip "Weekly Review"
    Check the heatmap weekly to identify emerging patterns before
    they become problems.

!!! tip "Compare Views"
    Toggle between coverage and workload views to get the full picture.

!!! tip "Use Filters"
    Filter by PGY level to ensure fair workload distribution within
    training levels.

!!! tip "Export for Meetings"
    Export heatmaps for curriculum committee or staffing meetings.

---

## Related Documentation

- **[Schedule Management](schedule.md)** - Detailed schedule view
- **[Compliance](compliance.md)** - Work hour tracking
- **[Daily Manifest](daily-manifest.md)** - Day-by-day staffing
