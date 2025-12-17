# Schedule Endpoints

Schedule management API endpoints.

---

## Get Schedule

<span class="endpoint-badge get">GET</span> `/api/v1/schedule/{start_date}/{end_date}`

### Parameters

| Name | Type | Description |
|------|------|-------------|
| `start_date` | date | Start date (YYYY-MM-DD) |
| `end_date` | date | End date (YYYY-MM-DD) |

### Response

```json
{
  "items": [
    {
      "id": "uuid",
      "block_id": "uuid",
      "person_id": "uuid",
      "role": "resident",
      "date": "2025-01-15",
      "period": "AM"
    }
  ],
  "total": 100
}
```

---

## Generate Schedule

<span class="endpoint-badge post">POST</span> `/api/v1/schedule/generate`

### Request

```json
{
  "start_date": "2025-01-01",
  "end_date": "2025-01-31",
  "algorithm": "greedy",
  "priorities": {
    "coverage": 1.0,
    "fairness": 0.8,
    "preferences": 0.5
  }
}
```

### Response

```json
{
  "job_id": "uuid",
  "status": "pending",
  "message": "Schedule generation started"
}
```

---

## Get Assignment

<span class="endpoint-badge get">GET</span> `/api/v1/assignments/{id}`

---

## Update Assignment

<span class="endpoint-badge put">PUT</span> `/api/v1/assignments/{id}`

---

## Delete Assignment

<span class="endpoint-badge delete">DELETE</span> `/api/v1/assignments/{id}`
