***REMOVED*** Blocks API

Complete reference for the `/api/v1/blocks` endpoints.

> **Base Path:** `/api/v1/blocks`
> **Authentication:** Required (Bearer token)
> **Source:** `backend/app/api/routes/blocks.py`

---

***REMOVED******REMOVED*** Table of Contents

1. [Overview](***REMOVED***overview)
2. [Endpoints](***REMOVED***endpoints)
3. [Schemas](***REMOVED***schemas)
4. [Examples](***REMOVED***examples)
5. [Error Handling](***REMOVED***error-handling)

---

***REMOVED******REMOVED*** Overview

The Blocks API manages time slots in the academic schedule. Each block represents a half-day session (AM or PM) on a specific date.

***REMOVED******REMOVED******REMOVED*** Key Features

- **Academic Year Structure**: 730 blocks per year (365 days × 2 sessions)
- **Block Numbering**: Sequential numbering within academic year (1-730)
- **Holiday Tracking**: Mark blocks as weekends or holidays
- **Bulk Generation**: Create blocks for entire date ranges
- **Date Filtering**: Query blocks by date range or block number

---

***REMOVED******REMOVED*** Endpoints

***REMOVED******REMOVED******REMOVED*** List Blocks

```http
GET /api/v1/blocks
```

List blocks with optional filters.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `start_date` | date | No | - | Filter blocks from this date (YYYY-MM-DD) |
| `end_date` | date | No | - | Filter blocks until this date (YYYY-MM-DD) |
| `block_number` | int | No | - | Filter by academic block number (1-730) |

**Response:** `BlockListResponse`

**Status Codes:**
- `200 OK`: Success
- `401 Unauthorized`: Missing or invalid authentication
- `422 Unprocessable Entity`: Invalid query parameters

---

***REMOVED******REMOVED******REMOVED*** Get Block

```http
GET /api/v1/blocks/{block_id}
```

Get a single block by ID.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `block_id` | UUID | Yes | Block ID |

**Response:** `BlockResponse`

**Status Codes:**
- `200 OK`: Success
- `401 Unauthorized`: Missing or invalid authentication
- `404 Not Found`: Block not found

---

***REMOVED******REMOVED******REMOVED*** Create Block

```http
POST /api/v1/blocks
```

Create a new block.

**Authorization:** Required (authenticated user)

**Request Body:** `BlockCreate`

**Response:** `BlockResponse` (201 Created)

**Status Codes:**
- `201 Created`: Block created successfully
- `401 Unauthorized`: Missing or invalid authentication
- `422 Unprocessable Entity`: Validation failure

**Note:** For bulk creation, use the `/generate` endpoint instead.

---

***REMOVED******REMOVED******REMOVED*** Generate Blocks

```http
POST /api/v1/blocks/generate
```

Generate blocks for a date range. Creates AM and PM blocks for each day.

**Authorization:** Required (authenticated user)

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `start_date` | date | Yes | - | Start date for block generation (YYYY-MM-DD) |
| `end_date` | date | Yes | - | End date for block generation (YYYY-MM-DD) |
| `base_block_number` | int | No | 1 | Starting block number |

**Response:** `BlockListResponse`

**Status Codes:**
- `200 OK`: Blocks generated successfully
- `401 Unauthorized`: Missing or invalid authentication
- `422 Unprocessable Entity`: Invalid date range

**Notes:**
- Creates 2 blocks per day (AM and PM)
- Block numbers increment sequentially from `base_block_number`
- Automatically marks weekends with `is_weekend: true`

---

***REMOVED******REMOVED******REMOVED*** Delete Block

```http
DELETE /api/v1/blocks/{block_id}
```

Delete a block.

**Authorization:** Required (authenticated user)

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `block_id` | UUID | Yes | Block ID |

**Status Codes:**
- `204 No Content`: Block deleted successfully
- `401 Unauthorized`: Missing or invalid authentication
- `404 Not Found`: Block not found

**Warning:** Deleting a block will cascade delete all associated assignments.

---

***REMOVED******REMOVED*** Schemas

***REMOVED******REMOVED******REMOVED*** BlockCreate

```json
{
  "date": "2025-01-15",
  "time_of_day": "AM",
  "block_number": 100,
  "is_weekend": false,
  "is_holiday": false,
  "holiday_name": null
}
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `date` | date | Yes | Block date (YYYY-MM-DD) |
| `time_of_day` | string | Yes | Time of day: `AM` or `PM` |
| `block_number` | int | Yes | Sequential block number |
| `is_weekend` | bool | No | Whether this is a weekend (default: false) |
| `is_holiday` | bool | No | Whether this is a holiday (default: false) |
| `holiday_name` | string | No | Name of holiday (if applicable) |

**Validation:**
- `date` must be within academic year bounds (2024-07-01 to 2025-06-30)
- `time_of_day` must be `AM` or `PM`

---

***REMOVED******REMOVED******REMOVED*** BlockResponse

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "date": "2025-01-15",
  "time_of_day": "AM",
  "block_number": 100,
  "is_weekend": false,
  "is_holiday": false,
  "holiday_name": null
}
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Block ID |
| `date` | date | Block date |
| `time_of_day` | string | Time of day: `AM` or `PM` |
| `block_number` | int | Sequential block number |
| `is_weekend` | bool | Whether this is a weekend |
| `is_holiday` | bool | Whether this is a holiday |
| `holiday_name` | string | Name of holiday (if applicable) |

---

***REMOVED******REMOVED******REMOVED*** BlockListResponse

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "date": "2025-01-15",
      "time_of_day": "AM",
      "block_number": 100,
      "is_weekend": false,
      "is_holiday": false,
      "holiday_name": null
    }
  ],
  "total": 730
}
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `items` | array[BlockResponse] | Block items |
| `total` | int | Total count of blocks |

---

***REMOVED******REMOVED*** Examples

***REMOVED******REMOVED******REMOVED*** List Blocks for a Date Range

**Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/blocks?start_date=2025-01-01&end_date=2025-01-31" \
  -H "Authorization: Bearer <token>"
```

**Response:**

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "date": "2025-01-01",
      "time_of_day": "AM",
      "block_number": 366,
      "is_weekend": false,
      "is_holiday": true,
      "holiday_name": "New Year's Day"
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "date": "2025-01-01",
      "time_of_day": "PM",
      "block_number": 367,
      "is_weekend": false,
      "is_holiday": true,
      "holiday_name": "New Year's Day"
    },
    {
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "date": "2025-01-02",
      "time_of_day": "AM",
      "block_number": 368,
      "is_weekend": false,
      "is_holiday": false,
      "holiday_name": null
    }
  ],
  "total": 62
}
```

---

***REMOVED******REMOVED******REMOVED*** Get Block by ID

**Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/blocks/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer <token>"
```

**Response:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "date": "2025-01-01",
  "time_of_day": "AM",
  "block_number": 366,
  "is_weekend": false,
  "is_holiday": true,
  "holiday_name": "New Year's Day"
}
```

---

***REMOVED******REMOVED******REMOVED*** Create Single Block

**Request:**

```bash
curl -X POST "http://localhost:8000/api/v1/blocks" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2025-02-15",
    "time_of_day": "AM",
    "block_number": 450,
    "is_weekend": false,
    "is_holiday": false
  }'
```

**Response (201 Created):**

```json
{
  "id": "880e8400-e29b-41d4-a716-446655440003",
  "date": "2025-02-15",
  "time_of_day": "AM",
  "block_number": 450,
  "is_weekend": false,
  "is_holiday": false,
  "holiday_name": null
}
```

---

***REMOVED******REMOVED******REMOVED*** Generate Blocks for Academic Year

**Request:**

```bash
curl -X POST "http://localhost:8000/api/v1/blocks/generate?start_date=2024-07-01&end_date=2025-06-30&base_block_number=1" \
  -H "Authorization: Bearer <token>"
```

**Response (200 OK):**

```json
{
  "items": [
    {
      "id": "990e8400-e29b-41d4-a716-446655440004",
      "date": "2024-07-01",
      "time_of_day": "AM",
      "block_number": 1,
      "is_weekend": false,
      "is_holiday": false,
      "holiday_name": null
    },
    {
      "id": "aa0e8400-e29b-41d4-a716-446655440005",
      "date": "2024-07-01",
      "time_of_day": "PM",
      "block_number": 2,
      "is_weekend": false,
      "is_holiday": false,
      "holiday_name": null
    }
    // ... (728 more blocks) ...
  ],
  "total": 730
}
```

**Note:** This creates 730 blocks (365 days × 2 sessions).

---

***REMOVED******REMOVED******REMOVED*** Generate Blocks for One Month

**Request:**

```bash
curl -X POST "http://localhost:8000/api/v1/blocks/generate?start_date=2025-01-01&end_date=2025-01-31&base_block_number=366" \
  -H "Authorization: Bearer <token>"
```

**Response (200 OK):**

```json
{
  "items": [
    {
      "id": "bb0e8400-e29b-41d4-a716-446655440006",
      "date": "2025-01-01",
      "time_of_day": "AM",
      "block_number": 366,
      "is_weekend": false,
      "is_holiday": true,
      "holiday_name": null
    },
    {
      "id": "cc0e8400-e29b-41d4-a716-446655440007",
      "date": "2025-01-01",
      "time_of_day": "PM",
      "block_number": 367,
      "is_weekend": false,
      "is_holiday": true,
      "holiday_name": null
    }
    // ... (60 more blocks) ...
  ],
  "total": 62
}
```

**Note:** This creates 62 blocks (31 days × 2 sessions).

---

***REMOVED******REMOVED******REMOVED*** Filter Blocks by Block Number

**Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/blocks?block_number=100" \
  -H "Authorization: Bearer <token>"
```

**Response:**

```json
{
  "items": [
    {
      "id": "dd0e8400-e29b-41d4-a716-446655440008",
      "date": "2024-07-20",
      "time_of_day": "AM",
      "block_number": 100,
      "is_weekend": true,
      "is_holiday": false,
      "holiday_name": null
    }
  ],
  "total": 1
}
```

---

***REMOVED******REMOVED*** Error Handling

***REMOVED******REMOVED******REMOVED*** 422 Unprocessable Entity - Invalid Time of Day

```json
{
  "detail": [
    {
      "loc": ["body", "time_of_day"],
      "msg": "time_of_day must be 'AM' or 'PM'",
      "type": "value_error"
    }
  ]
}
```

**Cause:** Invalid `time_of_day` value.

**Resolution:** Use `AM` or `PM`.

---

***REMOVED******REMOVED******REMOVED*** 422 Unprocessable Entity - Date Out of Range

```json
{
  "detail": [
    {
      "loc": ["body", "date"],
      "msg": "date must be within academic year bounds (2024-07-01 to 2025-06-30)",
      "type": "value_error"
    }
  ]
}
```

**Cause:** Date outside academic year bounds.

**Resolution:** Use a date within the academic year.

---

***REMOVED******REMOVED******REMOVED*** 404 Not Found

```json
{
  "detail": "Block not found"
}
```

**Cause:** Block ID does not exist.

**Resolution:** Verify the block ID.

---

***REMOVED******REMOVED*** Related Documentation

- [Assignments API](assignments.md) - Schedule assignments linked to blocks
- [Academic Blocks API](../ENDPOINT_CATALOG.md***REMOVED***blocks--calendar) - Academic block definitions
- [Schedule API](schedule.md) - Schedule generation using blocks

---

***REMOVED******REMOVED*** Block Structure

***REMOVED******REMOVED******REMOVED*** Academic Year

- **Start Date:** July 1, 2024
- **End Date:** June 30, 2025
- **Total Days:** 365
- **Total Blocks:** 730 (2 per day)

***REMOVED******REMOVED******REMOVED*** Block Numbering

Blocks are numbered sequentially from 1 to 730:

| Block Number | Date | Time of Day |
|--------------|------|-------------|
| 1 | 2024-07-01 | AM |
| 2 | 2024-07-01 | PM |
| 3 | 2024-07-02 | AM |
| 4 | 2024-07-02 | PM |
| ... | ... | ... |
| 729 | 2025-06-30 | AM |
| 730 | 2025-06-30 | PM |

***REMOVED******REMOVED******REMOVED*** Weekend Detection

The `/generate` endpoint automatically sets `is_weekend: true` for Saturday and Sunday blocks.

***REMOVED******REMOVED******REMOVED*** Holiday Marking

Holidays must be manually marked by setting:
- `is_holiday: true`
- `holiday_name: "Holiday Name"`

Common federal holidays to mark:
- New Year's Day (January 1)
- Martin Luther King Jr. Day (3rd Monday in January)
- Presidents' Day (3rd Monday in February)
- Memorial Day (Last Monday in May)
- Independence Day (July 4)
- Labor Day (1st Monday in September)
- Veterans Day (November 11)
- Thanksgiving (4th Thursday in November)
- Christmas (December 25)

---

*Last Updated: 2025-12-31*
