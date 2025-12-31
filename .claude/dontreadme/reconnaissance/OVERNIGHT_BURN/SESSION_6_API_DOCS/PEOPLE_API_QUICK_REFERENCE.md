# People API - Quick Reference Card

## Endpoints at a Glance

### List/Query Endpoints
| Method | Path | Purpose | Key Filters |
|--------|------|---------|------------|
| GET | `/api/people` | List all people | `type`, `pgy_level` |
| GET | `/api/people/residents` | List residents | `pgy_level` |
| GET | `/api/people/faculty` | List faculty | `specialty` |
| GET | `/api/people/{id}` | Get single person | - |

### CRUD Endpoints
| Method | Path | Purpose | Status |
|--------|------|---------|--------|
| POST | `/api/people` | Create person | 201 |
| PUT | `/api/people/{id}` | Update person | 200 |
| DELETE | `/api/people/{id}` | Delete person | 204 |

### Credential Endpoints
| Method | Path | Purpose | Filters |
|--------|------|---------|---------|
| GET | `/api/people/{id}/credentials` | List credentials | `status`, `include_expired` |
| GET | `/api/people/{id}/credentials/summary` | Credential summary | - |
| GET | `/api/people/{id}/procedures` | List procedures | - |

---

## Quick Curl Templates

### List All
```bash
curl http://localhost:8000/api/people \
  -H "Authorization: Bearer $TOKEN"
```

### Filter Residents by PGY
```bash
curl "http://localhost:8000/api/people/residents?pgy_level=1" \
  -H "Authorization: Bearer $TOKEN"
```

### Create Resident
```bash
curl -X POST http://localhost:8000/api/people \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Dr. Name",
    "type": "resident",
    "email": "user@hospital.org",
    "pgy_level": 1
  }'
```

### Create Faculty
```bash
curl -X POST http://localhost:8000/api/people \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Dr. Faculty",
    "type": "faculty",
    "email": "faculty@hospital.org",
    "specialties": ["Cardiology"],
    "faculty_role": "core",
    "performs_procedures": true
  }'
```

### Update Person
```bash
curl -X PUT http://localhost:8000/api/people/{person_id} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"pgy_level": 2}'
```

### Delete Person
```bash
curl -X DELETE http://localhost:8000/api/people/{person_id} \
  -H "Authorization: Bearer $TOKEN"
```

### Get Credentials
```bash
curl http://localhost:8000/api/people/{person_id}/credentials \
  -H "Authorization: Bearer $TOKEN"
```

---

## Data Validation

### Resident Requirements
- `name`: Required, max 255 chars
- `type`: Required, must be "resident"
- `email`: Optional but must be unique if provided
- `pgy_level`: **REQUIRED**, must be 1-3

### Faculty Requirements
- `name`: Required, max 255 chars
- `type`: Required, must be "faculty"
- `email`: Optional but must be unique if provided
- `pgy_level`: Must be null for faculty

### Valid Faculty Roles
- `pd` - Program Director
- `apd` - Associate Program Director
- `oic` - Officer in Charge
- `dept_chief` - Department Chief
- `sports_med` - Sports Medicine
- `core` - Core Faculty
- `adjunct` - Adjunct Faculty

---

## Response Fields

### Person Response
```json
{
  "id": "uuid",
  "name": "string",
  "type": "resident|faculty",
  "email": "email",
  "pgy_level": 1|2|3|null,
  "performs_procedures": boolean,
  "specialties": ["string"],
  "primary_duty": "string",
  "faculty_role": "enum",
  "sunday_call_count": integer,
  "weekday_call_count": integer,
  "fmit_weeks_count": integer,
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

### List Response
```json
{
  "items": [/* array of persons */],
  "total": integer
}
```

---

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success (GET, PUT) |
| 201 | Created (POST) |
| 204 | No Content (DELETE success) |
| 400 | Bad Request (business logic error) |
| 401 | Unauthorized (missing/invalid token) |
| 404 | Not Found (invalid ID) |
| 422 | Validation Error (invalid data) |

---

## Common Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| "pgy_level required for residents" | Missing PGY level on resident | Add `pgy_level: 1|2|3` |
| "type must be 'resident' or 'faculty'" | Invalid type | Use exactly "resident" or "faculty" |
| "pgy_level must be between 1 and 3" | Invalid PGY value | Use 1, 2, or 3 |
| "Person not found" | Invalid person_id | Verify UUID exists |
| "Email already registered" | Duplicate email | Use unique email address |
| 401 Unauthorized | Missing/invalid token | Provide valid JWT |

---

## Faculty Clinic Limits

| Role | Weekly Clinic | Block Clinic | Notes |
|------|---------------|--------------|-------|
| PD | 0 | 0 | Avoid Tue call |
| APD | 2 | 8 | Avoid Tue call |
| OIC | 2 | 8 | - |
| Dept Chief | 1 | 4 | Prefers Wed |
| Sports Med | 0 | 0 | SM clinic 4/week |
| Core | 4 | 16 | Hard max |
| Adjunct | 0 | 0 | Not auto-scheduled |

---

## Authentication

All endpoints require JWT token:
```bash
-H "Authorization: Bearer <your_jwt_token>"
```

Token stored in httpOnly cookie (XSS resistant).

---

## Special Features

### Read-Only Fields (System-Managed)
- `sunday_call_count` - Reset annually
- `weekday_call_count` - Reset annually
- `fmit_weeks_count` - Reset annually
- `id`, `created_at`, `updated_at` - Set by system

### Partial Updates
PUT endpoint supports partial updates:
```json
{
  "name": "New Name"
  /* Other fields unchanged */
}
```

### Cascade Delete
Deleting a person also deletes:
- All assignments
- All absences
- All credentials
- All certifications

---

## Performance Tips

### Avoid N+1 Queries
```python
# Use service layer with include_assignments=True
service.list_residents(include_assignments=True)
```

### Efficient Filtering
```bash
# Filter at API level, not in-app
GET /api/people?type=resident&pgy_level=1
```

### Batch Operations
Iterate results efficiently:
```bash
# Get all faculty
FACULTY=$(curl http://localhost:8000/api/people/faculty -H "Authorization: Bearer $TOKEN")

# Process each
echo $FACULTY | jq -r '.items[] | .id'
```

---

## Testing

Run tests:
```bash
cd backend
pytest tests/test_people_api.py -v
```

Coverage: 25+ tests for all endpoints and error cases.

---

## Links

- **Full Documentation**: See `api-docs-people.md`
- **Source Code**: `backend/app/api/routes/people.py`
- **Tests**: `backend/tests/test_people_api.py`
- **Models**: `backend/app/models/person.py`
