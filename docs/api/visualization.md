# Visualization API

> **Base Path:** `/api/visualization`
> **Authentication:** Required (JWT)

The Visualization API provides endpoints for generating schedule visualizations including 2D heatmaps and novel 3D voxel representations.

---

## Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/heatmap` | Generate 2D unified heatmap |
| POST | `/heatmap/unified` | Generate heatmap with time range |
| GET | `/heatmap/image` | Export heatmap as image |
| GET | `/coverage` | Generate coverage analysis heatmap |
| GET | `/workload` | Generate workload heatmap |
| POST | `/export` | Export heatmap with custom options |
| GET | `/voxel-grid` | **3D voxel grid representation** |
| GET | `/voxel-grid/conflicts` | **3D conflict detection** |
| GET | `/voxel-grid/coverage-gaps` | **3D coverage gap analysis** |

---

## 2D Heatmap Endpoints

### GET `/heatmap`

Generate unified heatmap showing residency and FMIT schedules.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `start_date` | date | Yes | - | Start date (YYYY-MM-DD) |
| `end_date` | date | Yes | - | End date (YYYY-MM-DD) |
| `person_ids` | UUID[] | No | all | Filter by person IDs |
| `rotation_ids` | UUID[] | No | all | Filter by rotation template IDs |
| `include_fmit` | boolean | No | true | Include FMIT swap data |
| `group_by` | string | No | "person" | Group by "person" or "rotation" |

**Response:** `HeatmapResponse`

```json
{
  "title": "Schedule Heatmap",
  "data": {
    "x_labels": ["2024-01-15", "2024-01-16"],
    "y_labels": ["Dr. Smith", "Resident A"],
    "z_values": [[2, 1], [1, 2]]
  },
  "color_scale": "Viridis",
  "metadata": {
    "generated_at": "2024-01-15T10:30:00Z"
  }
}
```

---

### GET `/heatmap/image`

Export heatmap as PNG, PDF, or SVG image.

**Query Parameters:**

Same as `/heatmap` plus:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `format` | string | No | "png" | Export format: png, pdf, svg |
| `width` | integer | No | 1200 | Image width in pixels |
| `height` | integer | No | 800 | Image height in pixels |

**Response:** Binary image file with appropriate Content-Type header.

---

### GET `/coverage`

Generate coverage heatmap showing staffing levels per rotation.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | date | Yes | Start date |
| `end_date` | date | Yes | End date |

**Response:** `CoverageHeatmapResponse`

```json
{
  "title": "Coverage Analysis",
  "data": {...},
  "gaps": [
    {
      "date": "2024-01-21",
      "rotation": "ICU",
      "expected": 2,
      "actual": 1
    }
  ]
}
```

---

## 3D Voxel Visualization Endpoints

These endpoints provide novel 3D representations of schedule data. See [3D Voxel Visualization Architecture](/docs/architecture/3d-voxel-visualization.md) for conceptual details.

### GET `/voxel-grid`

Generate 3D voxel grid representation of schedule data.

**Concept:** Represents the schedule as a 3D space where:
- **X-axis:** Time (blocks/dates)
- **Y-axis:** People (residents, faculty)
- **Z-axis:** Rotation type (clinic, inpatient, procedures, etc.)

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `start_date` | date | Yes | - | Start date for voxel grid |
| `end_date` | date | Yes | - | End date for voxel grid |
| `person_ids` | UUID[] | No | all | Filter by person IDs |
| `rotation_types` | string[] | No | all | Filter by rotation types |
| `include_violations` | boolean | No | true | Include ACGME violation markers |

**Example Request:**

```bash
curl -X GET \
  'http://localhost:8000/api/visualization/voxel-grid?start_date=2024-01-15&end_date=2024-01-28' \
  -H 'Authorization: Bearer <token>'
```

**Response:**

```json
{
  "dimensions": {
    "x_size": 28,
    "y_size": 15,
    "z_size": 6,
    "x_labels": ["2024-01-15 AM", "2024-01-15 PM", "2024-01-16 AM", ...],
    "y_labels": ["Dr. Smith", "Dr. Johnson", "PGY1-01", ...],
    "z_labels": ["clinic", "inpatient", "procedures", "call", "leave", "admin"]
  },
  "voxels": [
    {
      "position": {
        "x": 0,
        "y": 0,
        "z": 0
      },
      "identity": {
        "assignment_id": "550e8400-e29b-41d4-a716-446655440000",
        "person_id": "123e4567-e89b-12d3-a456-426614174000",
        "person_name": "Dr. Smith",
        "block_id": "789e0123-e45b-67d8-a901-234567890abc",
        "block_date": "2024-01-15",
        "block_time_of_day": "AM",
        "rotation_name": "Morning Clinic",
        "rotation_type": "clinic"
      },
      "visual": {
        "color": "#3B82F6",
        "rgba": [0.231, 0.510, 0.965, 1.0],
        "opacity": 1.0,
        "height": 1.0
      },
      "state": {
        "is_occupied": true,
        "is_conflict": false,
        "is_violation": false,
        "violation_details": []
      },
      "metadata": {
        "role": "supervising",
        "confidence": 1.0,
        "hours": 4.0
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

**Voxel Properties:**

| Field | Description |
|-------|-------------|
| `position.x` | Time index (block number from start) |
| `position.y` | Person index (faculty first, then by PGY) |
| `position.z` | Rotation layer index |
| `visual.color` | Hex color based on rotation type |
| `visual.opacity` | Confidence score (0-1) |
| `state.is_conflict` | True if double-booked |
| `state.is_violation` | True if ACGME violation |

---

### GET `/voxel-grid/conflicts`

Detect schedule conflicts using 3D spatial collision analysis.

**Concept:** Multiple voxels at the same (x, y) position indicate double-booking - the same person assigned to multiple activities at the same time.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | date | Yes | Start date |
| `end_date` | date | Yes | End date |

**Example Request:**

```bash
curl -X GET \
  'http://localhost:8000/api/visualization/voxel-grid/conflicts?start_date=2024-01-15&end_date=2024-01-28' \
  -H 'Authorization: Bearer <token>'
```

**Response:**

```json
{
  "total_conflicts": 2,
  "conflict_voxels": [
    {
      "position": {"x": 5, "y": 3, "z": 0},
      "identity": {
        "person_name": "PGY1-01",
        "block_date": "2024-01-17",
        "rotation_name": "Morning Clinic"
      },
      "details": []
    },
    {
      "position": {"x": 5, "y": 3, "z": 4},
      "identity": {
        "person_name": "PGY1-01",
        "block_date": "2024-01-17",
        "rotation_name": "On-Call"
      },
      "details": []
    }
  ],
  "conflict_positions": [
    {"x": 5, "y": 3}
  ],
  "date_range": {
    "start_date": "2024-01-15",
    "end_date": "2024-01-28"
  }
}
```

---

### GET `/voxel-grid/coverage-gaps`

Identify coverage gaps using 3D voxel space analysis.

**Concept:** Empty regions in the voxel grid indicate time slots where no one is assigned. Critical gaps have zero coverage; warnings indicate less than 20% coverage.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `start_date` | date | Yes | - | Start date |
| `end_date` | date | Yes | - | End date |
| `required_rotation_types` | string[] | No | ["clinic"] | Rotation types that must be covered |

**Example Request:**

```bash
curl -X GET \
  'http://localhost:8000/api/visualization/voxel-grid/coverage-gaps?start_date=2024-01-15&end_date=2024-01-28' \
  -H 'Authorization: Bearer <token>'
```

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
    },
    {
      "x": 14,
      "time_label": "2024-01-22 PM",
      "coverage_count": 2,
      "severity": "warning"
    }
  ],
  "dimensions": {
    "x_size": 28,
    "y_size": 15,
    "z_size": 6
  },
  "date_range": {
    "start_date": "2024-01-15",
    "end_date": "2024-01-28"
  }
}
```

**Gap Severity:**

| Severity | Meaning | Threshold |
|----------|---------|-----------|
| `critical` | No one assigned | coverage_count = 0 |
| `warning` | Understaffed | coverage_count < 20% of total people |

---

## Rotation Type Color Mapping

Colors used in voxel visualization:

| Rotation Type | Color | Hex Code |
|---------------|-------|----------|
| clinic | Blue | `#3B82F6` |
| inpatient | Purple | `#8B5CF6` |
| procedures | Red | `#EF4444` |
| conference | Gray | `#6B7280` |
| call | Orange | `#F97316` |
| leave | Amber | `#F59E0B` |
| admin | Green | `#10B981` |
| supervision | Pink | `#EC4899` |

---

## Error Responses

All endpoints return standard error format:

```json
{
  "detail": "Error message here"
}
```

| Status Code | Meaning |
|-------------|---------|
| 400 | Invalid parameters (e.g., start_date > end_date) |
| 401 | Authentication required |
| 403 | Insufficient permissions |
| 500 | Server error |

---

## Rate Limiting

Visualization endpoints are subject to rate limiting:

- **Heatmap generation:** 30 requests per minute
- **Image export:** 10 requests per minute
- **Voxel grid:** 20 requests per minute

Cached responses are returned when available (TTL: 60 seconds).
