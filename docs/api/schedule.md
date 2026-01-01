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

---

## Best Practices

### 1. Always Validate After Generation

```bash
# Generate
curl -X POST http://localhost:8000/api/v1/schedule/generate \
  -d '{"start_date": "2025-07-01", "end_date": "2025-09-30"}'

# Immediately validate
curl "http://localhost:8000/api/v1/compliance/validate?start_date=2025-07-01&end_date=2025-09-30"
```

### 2. Use Idempotency Keys

```python
import uuid

# Generate unique key
idempotency_key = str(uuid.uuid4())

response = requests.post(
    "http://localhost:8000/api/v1/schedule/generate",
    headers={
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": idempotency_key
    },
    json={"start_date": "2025-07-01", "end_date": "2025-09-30"}
)
```

### 3. Monitor Long-Running Generations

```python
# Start generation
response = requests.post(
    "http://localhost:8000/api/v1/schedule/generate",
    json={"start_date": "2025-07-01", "end_date": "2025-09-30"}
)

run_id = response.json()['run_id']

# Poll status
import time
while True:
    status = requests.get(
        f"http://localhost:8000/api/v1/scheduler/runs/{run_id}"
    ).json()

    if status['state'] in ['completed', 'failed']:
        break

    print(f"Progress: {status['progress']}%")
    time.sleep(5)
```

## See Also

- [Schedule Generation Runbook](../guides/SCHEDULE_GENERATION_RUNBOOK.md)
- [Compliance API](endpoints/compliance.md)
- [Quick Reference](../QUICK_REFERENCE.md)
