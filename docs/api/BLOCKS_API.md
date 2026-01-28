# Blocks API

The Blocks API provides endpoints for managing schedule blocks. A block represents a single time slot in the schedule (AM or PM session for a specific date). The academic year consists of 730 blocks (365 days × 2 sessions per day).

## Base URL

```
/blocks
```

## Endpoints Overview

| Endpoint | Method | Purpose | Authentication |
|----------|--------|---------|----------------|
| `/blocks` | GET | List blocks with filtering | Required |
| `/blocks/{block_id}` | GET | Get specific block | Required |
| `/blocks` | POST | Create a single block | Required |
| `/blocks/generate` | POST | Generate blocks for date range | Required |
| `/blocks/{block_id}` | DELETE | Delete a block | Required |

---

## List Blocks

**Purpose:** List blocks with optional filtering by date range or block number.

```http
GET /blocks?start_date=2024-01-01&end_date=2024-01-31&block_number=1
```

**Authentication:** Required (JWT)

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | date | No | Filter blocks from this date (YYYY-MM-DD) |
| `end_date` | date | No | Filter blocks until this date (YYYY-MM-DD) |
| `block_number` | integer | No | Filter by academic block number (0-13) |

### Response

**Status:** 200 OK

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "date": "2024-01-15",
      "time_of_day": "AM",
      "block_number": 1,
      "is_weekend": false,
      "is_holiday": false,
      "holiday_name": null
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "date": "2024-01-15",
      "time_of_day": "PM",
      "block_number": 1,
      "is_weekend": false,
      "is_holiday": false,
      "holiday_name": null
    }
  ],
  "total": 2
}
```

**Schema:** `BlockListResponse`

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique block identifier |
| `date` | date | Date of the block (YYYY-MM-DD) |
| `time_of_day` | string | Time of day: "AM" or "PM" |
| `block_number` | integer | Academic block number (0-13) |
| `is_weekend` | boolean | Whether block falls on weekend (Sat/Sun) |
| `is_holiday` | boolean | Whether block is a recognized holiday |
| `holiday_name` | string | Name of holiday (null if not a holiday) |

### Block Number System

Academic year blocks are numbered sequentially:
- **Block 0:** Pre-academic year (June/July prep time)
- **Blocks 1-13:** Academic year blocks (roughly 4-week periods)
- Each block contains approximately 56 sessions (28 days × 2 sessions)

### Notes
- Returns empty list if no blocks match filters
- Date range is inclusive of both start_date and end_date
- Blocks are returned in chronological order

---

## Get Block

**Purpose:** Retrieve a specific block by ID.

```http
GET /blocks/{block_id}
```

**Authentication:** Required (JWT)

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `block_id` | UUID | Block UUID |

### Response

**Status:** 200 OK

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "date": "2024-01-15",
  "time_of_day": "AM",
  "block_number": 1,
  "is_weekend": false,
  "is_holiday": false,
  "holiday_name": null
}
```

**Schema:** `BlockResponse`

### Error Responses

**404 Not Found**
```json
{
  "detail": "Block not found"
}
```

---

## Create Block

**Purpose:** Create a single schedule block.

```http
POST /blocks
```

**Authentication:** Required (JWT)

### Request Body

```json
{
  "date": "2024-01-15",
  "time_of_day": "AM",
  "block_number": 1,
  "is_weekend": false,
  "is_holiday": false,
  "holiday_name": null
}
```

**Schema:** `BlockCreate`

### Request Fields

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `date` | date | Yes | Within academic year | Date of the block |
| `time_of_day` | string | Yes | "AM" or "PM" | Session time |
| `block_number` | integer | Yes | 0-13 | Academic block number |
| `is_weekend` | boolean | No | Default: false | Weekend flag |
| `is_holiday` | boolean | No | Default: false | Holiday flag |
| `holiday_name` | string | No | Max 100 chars | Holiday name if applicable |

### Response

**Status:** 201 Created

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "date": "2024-01-15",
  "time_of_day": "AM",
  "block_number": 1,
  "is_weekend": false,
  "is_holiday": false,
  "holiday_name": null
}
```

**Schema:** `BlockResponse`

### Error Responses

**400 Bad Request**
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

**400 Bad Request (Date Validation)**
```json
{
  "detail": "date must be within academic year bounds"
}
```

### Validation Rules

- `date` must be within the academic year (July 1 - June 30)
- `time_of_day` must be exactly "AM" or "PM" (case-sensitive)
- `block_number` must be between 0 and 13
- `holiday_name` only valid if `is_holiday` is true

---

## Generate Blocks

**Purpose:** Bulk generate blocks for a date range (creates AM and PM blocks for each day).

```http
POST /blocks/generate?start_date=2024-01-01&end_date=2024-12-31&base_block_number=1
```

**Authentication:** Required (JWT)

### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `start_date` | date | Yes | - | Start of date range |
| `end_date` | date | Yes | - | End of date range |
| `base_block_number` | integer | No | 1 | Starting block number |

### Response

**Status:** 200 OK

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "date": "2024-01-01",
      "time_of_day": "AM",
      "block_number": 1,
      "is_weekend": true,
      "is_holiday": true,
      "holiday_name": "New Year's Day"
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "date": "2024-01-01",
      "time_of_day": "PM",
      "block_number": 1,
      "is_weekend": true,
      "is_holiday": true,
      "holiday_name": "New Year's Day"
    },
    {
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "date": "2024-01-02",
      "time_of_day": "AM",
      "block_number": 1,
      "is_weekend": false,
      "is_holiday": false,
      "holiday_name": null
    }
    // ... 727 more blocks for the year
  ],
  "total": 730
}
```

**Schema:** `BlockListResponse`

### Generation Logic

For each day in the date range:
1. Creates AM block (morning session)
2. Creates PM block (afternoon session)
3. Automatically detects weekends (Saturday/Sunday)
4. Automatically detects US federal holidays
5. Assigns block numbers based on academic calendar

### Supported Holidays

The system automatically recognizes these US federal holidays:
- New Year's Day (January 1)
- Martin Luther King Jr. Day (3rd Monday in January)
- Presidents Day (3rd Monday in February)
- Memorial Day (Last Monday in May)
- Independence Day (July 4)
- Labor Day (1st Monday in September)
- Columbus Day (2nd Monday in October)
- Veterans Day (November 11)
- Thanksgiving (4th Thursday in November)
- Christmas Day (December 25)

### Example Use Cases

**Generate full academic year:**
```http
POST /blocks/generate?start_date=2024-07-01&end_date=2025-06-30&base_block_number=1
```
Result: 730 blocks (365 days × 2 sessions)

**Generate single block (4 weeks):**
```http
POST /blocks/generate?start_date=2024-07-01&end_date=2024-07-28&base_block_number=1
```
Result: 56 blocks (28 days × 2 sessions)

### Error Responses

**400 Bad Request**
```json
{
  "detail": "end_date must be after start_date"
}
```

**400 Bad Request**
```json
{
  "detail": "Date range too large - maximum 365 days"
}
```

### Notes
- Existing blocks are not duplicated (idempotent operation)
- Weekend detection uses Saturday/Sunday logic
- Holiday detection is automatic based on year
- All blocks in a 4-week period typically share the same block_number

---

## Delete Block

**Purpose:** Delete a specific block.

```http
DELETE /blocks/{block_id}
```

**Authentication:** Required (JWT)

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `block_id` | UUID | Block UUID to delete |

### Response

**Status:** 204 No Content

No response body.

### Error Responses

**404 Not Found**
```json
{
  "detail": "Block not found"
}
```

**409 Conflict**
```json
{
  "detail": "Cannot delete block with existing assignments"
}
```

### Notes
- Blocks with assignments cannot be deleted (must delete assignments first)
- Use with caution - deleting blocks can orphan schedule data
- Consider disabling blocks instead of deleting them

---

## Common Workflows

### Initialize Academic Year

```bash
# Generate all blocks for academic year (July 1, 2024 - June 30, 2025)
POST /blocks/generate?start_date=2024-07-01&end_date=2025-06-30&base_block_number=1

# Verify block count (should be 730)
GET /blocks?start_date=2024-07-01&end_date=2025-06-30
```

### Query Specific Block Period

```bash
# Get all blocks for Block 1 (first 4 weeks)
GET /blocks?block_number=1

# Get blocks for January 2024
GET /blocks?start_date=2024-01-01&end_date=2024-01-31
```

### Identify Holidays

```bash
# Get all holiday blocks in 2024
GET /blocks?start_date=2024-01-01&end_date=2024-12-31&is_holiday=true
```

### Weekend Coverage Analysis

```bash
# Get all weekend blocks for Q1 2024
GET /blocks?start_date=2024-01-01&end_date=2024-03-31&is_weekend=true
```

---

## Block Structure and Schedule Design

### Academic Calendar Blocks

The academic year is divided into 14 blocks (numbered 0-13):

| Block | Weeks | Purpose |
|-------|-------|---------|
| 0 | 2-4 weeks | Pre-academic year (orientation, onboarding) |
| 1-13 | ~4 weeks each | Academic rotation blocks |

### Session Times

Each block represents a half-day session:
- **AM Session:** Typically 8:00 AM - 12:00 PM
- **PM Session:** Typically 1:00 PM - 5:00 PM

Exact times are defined by rotation templates and may vary by department.

### Block Count Calculation

```
Academic year = 365 days
Sessions per day = 2 (AM + PM)
Total blocks = 365 × 2 = 730 blocks
```

For 4-week rotation blocks:
```
4 weeks = 28 days
Sessions = 28 × 2 = 56 blocks per rotation
```

---

## Integration with Other APIs

### Assignments

Blocks are referenced by assignments:
```
Assignment = Person + Block + Rotation
```

To see who is assigned to a block:
```bash
GET /assignments?block_id={block_id}
```

### Rotations

Rotation templates define rotation types for blocks:
```bash
GET /rotations/{rotation_id}/blocks
```

### ACGME Compliance

Work hour validation uses blocks to calculate:
- Hours per week (14 blocks = 1 week)
- Rolling 4-week periods (56 blocks)
- Days off (2 consecutive blocks = 1 day)

---

## Error Codes Summary

| Status | Error | Common Cause |
|--------|-------|--------------|
| 400 | Bad Request | Invalid time_of_day, date out of range |
| 401 | Unauthorized | Missing or invalid JWT token |
| 404 | Not Found | Block ID doesn't exist |
| 409 | Conflict | Cannot delete block with assignments |
| 422 | Validation Error | Invalid field format or constraints |

---

## Performance Considerations

### Bulk Operations

When creating many blocks:
- **Recommended:** Use `/blocks/generate` for date ranges
- **Not recommended:** Loop calling `POST /blocks` (slower, more DB load)

### Query Optimization

- Use `block_number` filter for rotation-period queries (faster than date range)
- Date range queries are indexed and performant
- Avoid requesting all 730 blocks unless necessary

### Database Indexes

Blocks table has indexes on:
- `date` - Fast date range queries
- `block_number` - Fast block period queries
- `(date, time_of_day)` - Unique constraint, fast lookups

---

## Related Documentation

- `backend/app/api/routes/blocks.py` - Implementation
- `backend/app/controllers/block_controller.py` - Business logic
- `backend/app/schemas/block.py` - Request/response schemas
- `backend/app/models/block.py` - Database model
- `docs/architecture/SCHEDULE_STRUCTURE.md` - Schedule design overview
