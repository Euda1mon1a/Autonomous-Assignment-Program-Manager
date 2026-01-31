# Half-Day Import API

Reference for the `/api/v1/import/half-day` endpoints (Block Template2).

> **Base Path:** `/api/v1/import/half-day`
> **Authentication:** Required (Admin)
> **Source:** `backend/app/api/routes/half_day_imports.py`

---

## Overview

These endpoints stage Block Template2 half-day schedules, provide a diff preview, and create a schedule draft from selected diffs. Draft creation is **atomic**: if any selected row fails validation, the draft is not created. Preview entries include `warnings` and `errors` arrays for validation feedback.

---

## Endpoints

### Stage Block Template2

```http
POST /api/v1/import/half-day/stage
```

**Content-Type:** `multipart/form-data`

**Form Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | file | Yes | Block Template2 workbook (`.xlsx` or `.xls`) |
| `block_number` | int | Yes | Block number (1-26) |
| `academic_year` | int | Yes | Academic year start (e.g., `2025`) |
| `notes` | string | No | Optional notes for the batch |

**Response:** `HalfDayImportStageResponse`

---

### Preview Staged Diffs

```http
GET /api/v1/import/half-day/batches/{batch_id}/preview?page=1&page_size=50
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | int | No | Page number (default: 1) |
| `page_size` | int | No | Page size (default: 50) |
| `diff_type` | string | No | Filter by `added`, `removed`, `modified` |
| `activity_code` | string | No | Filter by activity code (exact match) |
| `has_errors` | bool | No | Filter rows with validation errors |
| `person_id` | UUID | No | Filter by matched person ID |

**Response:** `HalfDayImportPreviewResponse`

---

### Create Draft From Staged Diffs

```http
POST /api/v1/import/half-day/batches/{batch_id}/draft
```

**Request Body:**

```json
{
  "staged_ids": ["8c7a51a2-7c7c-4a3c-9c66-6b4c2d5db9dd"],
  "notes": "Block 10 Excel import draft"
}
```

**Response:** `HalfDayImportDraftResponse`

---

## Examples

### Draft Success Response

```json
{
  "success": true,
  "batch_id": "1c3f8e45-0b18-4d8e-8a1e-3c0adf693ef0",
  "draft_id": "a9c4a1ce-1cc3-4b5e-9b79-1d3d2f497b95",
  "message": "Draft a9c4a1ce-1cc3-4b5e-9b79-1d3d2f497b95 created from 12 staged diffs",
  "total_selected": 12,
  "added": 4,
  "modified": 7,
  "removed": 1,
  "skipped": 0,
  "failed": 0,
  "failed_ids": []
}
```

### Draft Failure Response (Atomic Abort)

```json
{
  "detail": {
    "message": "Draft creation failed for 2 staged rows",
    "error_code": "ROW_FAILURE",
    "failed_ids": [
      "3b10ed24-1e8e-49bf-9a31-4b6d3c0d9d6c",
      "d2b7b2d1-9bb6-4c5c-8fbe-4a90b5a0acb5"
    ]
  }
}
```

---

## Error Handling

- `400 Bad Request`: Invalid batch, no selection, or row validation failures
- `401 Unauthorized`: Missing/invalid authentication
- `500 Internal Server Error`: Unexpected failure
