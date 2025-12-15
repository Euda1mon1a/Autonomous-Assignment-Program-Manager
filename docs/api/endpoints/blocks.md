# Blocks Endpoints

Base path: `/api/blocks`

Manages schedule blocks representing AM and PM time slots.

## Endpoints Overview

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/` | List blocks with filtering | No |
| GET | `/{block_id}` | Get block by ID | No |
| POST | `/` | Create a single block | No |
| POST | `/generate` | Generate blocks for date range | No |
| DELETE | `/{block_id}` | Delete a block | No |

---

## GET /api/blocks

Returns a list of blocks with optional filtering by date range or block number.

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | date | No | Filter blocks from this date (YYYY-MM-DD) |
| `end_date` | date | No | Filter blocks until this date (YYYY-MM-DD) |
| `block_number` | integer | No | Filter by academic block number |

### Example Requests

```bash
# List all blocks
curl http://localhost:8000/api/blocks

# List blocks for a date range
curl "http://localhost:8000/api/blocks?start_date=2024-01-01&end_date=2024-01-31"

# List blocks by block number
curl "http://localhost:8000/api/blocks?block_number=5"
```

### Response

**Status:** `200 OK`

```json
{
  "items": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440000",
      "date": "2024-01-15",
      "time_of_day": "AM",
      "block_number": 5,
      "is_weekend": false,
      "is_holiday": false,
      "holiday_name": null
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "date": "2024-01-15",
      "time_of_day": "PM",
      "block_number": 5,
      "is_weekend": false,
      "is_holiday": false,
      "holiday_name": null
    }
  ],
  "total": 2
}
```

---

## GET /api/blocks/{block_id}

Returns a specific block by its UUID.

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `block_id` | UUID | Yes | Block's unique identifier |

### Example Request

```bash
curl http://localhost:8000/api/blocks/660e8400-e29b-41d4-a716-446655440000
```

### Response

**Status:** `200 OK`

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "date": "2024-01-15",
  "time_of_day": "AM",
  "block_number": 5,
  "is_weekend": false,
  "is_holiday": false,
  "holiday_name": null
}
```

### Errors

| Status | Description |
|--------|-------------|
| 404 | Block not found |

```json
{
  "detail": "Block not found"
}
```

---

## POST /api/blocks

Creates a single schedule block.

### Request Body

```json
{
  "date": "2024-01-15",
  "time_of_day": "AM",
  "block_number": 5,
  "is_weekend": false,
  "is_holiday": false,
  "holiday_name": null
}
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `date` | date | Yes | YYYY-MM-DD format |
| `time_of_day` | string | Yes | `AM` or `PM` |
| `block_number` | integer | Yes | Academic block number |
| `is_weekend` | boolean | No | Default: `false` |
| `is_holiday` | boolean | No | Default: `false` |
| `holiday_name` | string | No | Name of holiday if applicable |

### Example Request

```bash
curl -X POST http://localhost:8000/api/blocks \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2024-01-15",
    "time_of_day": "AM",
    "block_number": 5,
    "is_weekend": false,
    "is_holiday": false
  }'
```

### Response

**Status:** `201 Created`

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "date": "2024-01-15",
  "time_of_day": "AM",
  "block_number": 5,
  "is_weekend": false,
  "is_holiday": false,
  "holiday_name": null
}
```

### Errors

| Status | Description |
|--------|-------------|
| 400 | Block already exists for this date and time |
| 422 | Validation error |

```json
{
  "detail": "Block already exists for this date and time"
}
```

---

## POST /api/blocks/generate

Generates AM and PM blocks for a date range. Creates 2 blocks per day (730 blocks per year).

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | date | Yes | Start date (YYYY-MM-DD) |
| `end_date` | date | Yes | End date (YYYY-MM-DD) |
| `base_block_number` | integer | No | Starting block number (default: 1) |

### Example Requests

```bash
# Generate blocks for January 2024
curl -X POST "http://localhost:8000/api/blocks/generate?start_date=2024-01-01&end_date=2024-01-31"

# Generate blocks for full year with custom block numbering
curl -X POST "http://localhost:8000/api/blocks/generate?start_date=2024-01-01&end_date=2024-12-31&base_block_number=1"
```

### Response

**Status:** `200 OK`

```json
{
  "items": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440000",
      "date": "2024-01-01",
      "time_of_day": "AM",
      "block_number": 1,
      "is_weekend": false,
      "is_holiday": true,
      "holiday_name": "New Year's Day"
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "date": "2024-01-01",
      "time_of_day": "PM",
      "block_number": 1,
      "is_weekend": false,
      "is_holiday": true,
      "holiday_name": "New Year's Day"
    }
  ],
  "total": 62
}
```

### Notes

- Automatically detects weekends (Saturday/Sunday)
- Recognizes federal holidays and sets `is_holiday` flag
- Generates exactly 2 blocks per day (AM and PM)
- Block numbers increment daily

---

## DELETE /api/blocks/{block_id}

Deletes a schedule block.

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `block_id` | UUID | Yes | Block's unique identifier |

### Example Request

```bash
curl -X DELETE http://localhost:8000/api/blocks/660e8400-e29b-41d4-a716-446655440000
```

### Response

**Status:** `204 No Content`

### Errors

| Status | Description |
|--------|-------------|
| 404 | Block not found |

---

## Block Structure

Each day has two blocks:

| Time of Day | Typical Hours | Description |
|-------------|---------------|-------------|
| AM | 8:00 - 12:00 | Morning session |
| PM | 13:00 - 17:00 | Afternoon session |

### Academic Block Numbers

Block numbers correspond to the academic calendar:

| Block | Typical Dates | Description |
|-------|---------------|-------------|
| 1 | July 1-14 | First two weeks |
| 2 | July 15-28 | Second two weeks |
| ... | ... | ... |
| 26 | June 15-30 | Final block |

---

## Usage Examples

### Generate Full Academic Year

```bash
# Generate blocks for academic year (July 1 - June 30)
curl -X POST "http://localhost:8000/api/blocks/generate?start_date=2024-07-01&end_date=2025-06-30&base_block_number=1"
```

### Find Available Blocks

```bash
# Get all blocks for a specific week
curl "http://localhost:8000/api/blocks?start_date=2024-01-15&end_date=2024-01-21"
```

### Check Block Status

```bash
# Get blocks by block number to see coverage
curl "http://localhost:8000/api/blocks?block_number=5"
```

---

*See also: [Assignments](./assignments.md) for assigning people to blocks*
