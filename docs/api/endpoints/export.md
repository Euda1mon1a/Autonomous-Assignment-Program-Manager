# Export Endpoints

Base path: `/api/export`

Provides data export functionality in multiple formats (CSV, JSON, XLSX) for reporting and integration purposes.

## Endpoints Overview

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/people` | Export people data | No |
| GET | `/absences` | Export absences data | No |
| GET | `/schedule` | Export schedule (CSV/JSON) | No |
| GET | `/schedule/xlsx` | Export schedule (Excel) | No |

---

## GET /api/export/people

Exports all people (residents and faculty) in the specified format.

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `format` | string | No | Output format: `csv` or `json` (default: `json`) |

### Example Requests

```bash
# Export as JSON (default)
curl http://localhost:8000/api/export/people

# Export as CSV
curl "http://localhost:8000/api/export/people?format=csv"

# Save CSV to file
curl "http://localhost:8000/api/export/people?format=csv" -o people.csv
```

### JSON Response

**Status:** `200 OK`

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Dr. Jane Smith",
    "type": "resident",
    "email": "jane.smith@hospital.org",
    "pgy_level": 2,
    "performs_procedures": false,
    "specialties": null,
    "primary_duty": null,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "name": "Dr. Robert Johnson",
    "type": "faculty",
    "email": "robert.johnson@hospital.org",
    "pgy_level": null,
    "performs_procedures": true,
    "specialties": ["Sports Medicine"],
    "primary_duty": "Sports Medicine Clinic",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

### CSV Response

**Content-Type:** `text/csv`

```csv
id,name,type,email,pgy_level,performs_procedures,specialties,primary_duty,created_at,updated_at
550e8400-e29b-41d4-a716-446655440000,Dr. Jane Smith,resident,jane.smith@hospital.org,2,false,,,2024-01-01T00:00:00Z,2024-01-01T00:00:00Z
550e8400-e29b-41d4-a716-446655440001,Dr. Robert Johnson,faculty,robert.johnson@hospital.org,,true,Sports Medicine,Sports Medicine Clinic,2024-01-01T00:00:00Z,2024-01-01T00:00:00Z
```

---

## GET /api/export/absences

Exports absences data with optional date range filtering.

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `format` | string | No | Output format: `csv` or `json` (default: `json`) |
| `start_date` | date | No | Filter from this date (YYYY-MM-DD) |
| `end_date` | date | No | Filter until this date (YYYY-MM-DD) |

### Example Requests

```bash
# Export all absences as JSON
curl http://localhost:8000/api/export/absences

# Export as CSV
curl "http://localhost:8000/api/export/absences?format=csv"

# Export with date filter
curl "http://localhost:8000/api/export/absences?format=csv&start_date=2024-01-01&end_date=2024-03-31"

# Save to file
curl "http://localhost:8000/api/export/absences?format=csv&start_date=2024-01-01&end_date=2024-12-31" \
  -o absences_2024.csv
```

### JSON Response

**Status:** `200 OK`

```json
[
  {
    "id": "990e8400-e29b-41d4-a716-446655440000",
    "person_id": "550e8400-e29b-41d4-a716-446655440000",
    "person_name": "Dr. Jane Smith",
    "start_date": "2024-02-01",
    "end_date": "2024-02-15",
    "absence_type": "deployment",
    "deployment_orders": true,
    "tdy_location": null,
    "notes": "Annual training deployment",
    "created_at": "2024-01-15T00:00:00Z"
  }
]
```

### CSV Response

**Content-Type:** `text/csv`

```csv
id,person_id,person_name,start_date,end_date,absence_type,deployment_orders,tdy_location,notes,created_at
990e8400-e29b-41d4-a716-446655440000,550e8400-e29b-41d4-a716-446655440000,Dr. Jane Smith,2024-02-01,2024-02-15,deployment,true,,Annual training deployment,2024-01-15T00:00:00Z
```

---

## GET /api/export/schedule

Exports schedule data in CSV or JSON format.

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `format` | string | No | Output format: `csv` or `json` (default: `json`) |
| `start_date` | date | Yes | Start date (YYYY-MM-DD) |
| `end_date` | date | Yes | End date (YYYY-MM-DD) |

### Example Requests

```bash
# Export as JSON
curl "http://localhost:8000/api/export/schedule?start_date=2024-01-01&end_date=2024-01-31"

# Export as CSV
curl "http://localhost:8000/api/export/schedule?format=csv&start_date=2024-01-01&end_date=2024-01-31"

# Save monthly schedule to file
curl "http://localhost:8000/api/export/schedule?format=csv&start_date=2024-01-01&end_date=2024-01-31" \
  -o schedule_jan_2024.csv
```

### JSON Response

**Status:** `200 OK`

```json
[
  {
    "date": "2024-01-15",
    "time_of_day": "AM",
    "block_number": 5,
    "person_id": "550e8400-e29b-41d4-a716-446655440000",
    "person_name": "Dr. Jane Smith",
    "person_type": "resident",
    "pgy_level": 2,
    "role": "primary",
    "activity": "Sports Medicine Clinic",
    "abbreviation": "SM"
  },
  {
    "date": "2024-01-15",
    "time_of_day": "AM",
    "block_number": 5,
    "person_id": "550e8400-e29b-41d4-a716-446655440001",
    "person_name": "Dr. Robert Johnson",
    "person_type": "faculty",
    "pgy_level": null,
    "role": "supervising",
    "activity": "Sports Medicine Clinic",
    "abbreviation": "SM"
  }
]
```

### CSV Response

**Content-Type:** `text/csv`

```csv
date,time_of_day,block_number,person_id,person_name,person_type,pgy_level,role,activity,abbreviation
2024-01-15,AM,5,550e8400-e29b-41d4-a716-446655440000,Dr. Jane Smith,resident,2,primary,Sports Medicine Clinic,SM
2024-01-15,AM,5,550e8400-e29b-41d4-a716-446655440001,Dr. Robert Johnson,faculty,,supervising,Sports Medicine Clinic,SM
```

### Errors

| Status | Description |
|--------|-------------|
| 400 | Missing required date parameters |
| 422 | Invalid date format |

---

## GET /api/export/schedule/xlsx

Exports schedule data as an Excel workbook with formatting.

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | date | Yes | Start date (YYYY-MM-DD) |
| `end_date` | date | Yes | End date (YYYY-MM-DD) |
| `include_block_numbers` | boolean | No | Include block numbers (default: `true`) |

### Example Requests

```bash
# Export Excel file
curl "http://localhost:8000/api/export/schedule/xlsx?start_date=2024-01-01&end_date=2024-03-31" \
  -o schedule_q1_2024.xlsx

# Export without block numbers
curl "http://localhost:8000/api/export/schedule/xlsx?start_date=2024-01-01&end_date=2024-01-31&include_block_numbers=false" \
  -o schedule_jan_2024.xlsx
```

### Response

**Status:** `200 OK`

**Content-Type:** `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`

**Content-Disposition:** `attachment; filename="schedule_2024-01-01_2024-03-31.xlsx"`

### Excel Workbook Structure

The exported Excel file contains:

**Sheet 1: Calendar View**
- Dates as columns
- People as rows
- Color coding by activity type
- AM/PM sections

**Sheet 2: Assignment Details**
- Full assignment data
- Person information
- Activity details

**Sheet 3: Summary Statistics**
- Hours per person
- Coverage rates
- ACGME compliance status

### Errors

| Status | Description |
|--------|-------------|
| 400 | Missing required date parameters |
| 422 | Invalid date format |

---

## Response Headers

All export endpoints include appropriate headers:

### CSV Exports

```http
Content-Type: text/csv; charset=utf-8
Content-Disposition: attachment; filename="people_export.csv"
```

### JSON Exports

```http
Content-Type: application/json
```

### Excel Exports

```http
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename="schedule_2024-01-01_2024-03-31.xlsx"
```

---

## Usage Examples

### Export All Data for Backup

```bash
#!/bin/bash
# Export all data for backup

DATE=$(date +%Y-%m-%d)
BACKUP_DIR="backup_$DATE"
mkdir -p "$BACKUP_DIR"

# Export people
curl -s "http://localhost:8000/api/export/people?format=json" \
  > "$BACKUP_DIR/people.json"

# Export absences
curl -s "http://localhost:8000/api/export/absences?format=json" \
  > "$BACKUP_DIR/absences.json"

# Export schedule for current year
curl -s "http://localhost:8000/api/export/schedule?format=json&start_date=2024-01-01&end_date=2024-12-31" \
  > "$BACKUP_DIR/schedule.json"

echo "Backup complete: $BACKUP_DIR"
```

### Generate Monthly Reports

```bash
#!/bin/bash
# Generate monthly schedule reports

YEAR=2024
for MONTH in $(seq -w 1 12); do
  START="${YEAR}-${MONTH}-01"
  END=$(date -d "$START +1 month -1 day" +%Y-%m-%d)

  curl -s "http://localhost:8000/api/export/schedule/xlsx?start_date=$START&end_date=$END" \
    -o "schedule_${YEAR}_${MONTH}.xlsx"

  echo "Generated: schedule_${YEAR}_${MONTH}.xlsx"
done
```

### Export for External Systems

```bash
# Export CSV for spreadsheet import
curl "http://localhost:8000/api/export/people?format=csv" -o people.csv

# Export JSON for system integration
curl "http://localhost:8000/api/export/schedule?format=json&start_date=2024-01-01&end_date=2024-12-31" \
  | jq . > schedule.json
```

### Filter Absences by Type

```bash
# Export all deployment absences for reporting
curl -s "http://localhost:8000/api/export/absences?format=csv" \
  | grep deployment > deployments.csv
```

---

## Format Comparison

| Format | Use Case | Size | Human Readable | Machine Readable |
|--------|----------|------|----------------|------------------|
| JSON | API integration, backups | Medium | Moderate | Excellent |
| CSV | Spreadsheet import, analysis | Small | Good | Good |
| XLSX | Reports, presentations | Large | Excellent | Moderate |

---

## Rate Limiting

Export endpoints have additional rate limits due to resource intensity:

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/export/people` | 20 | 1 hour |
| `/export/absences` | 20 | 1 hour |
| `/export/schedule` | 20 | 1 hour |
| `/export/schedule/xlsx` | 10 | 1 hour |

---

*See also: [Rate Limiting](../rate-limiting.md) for detailed limit information*
