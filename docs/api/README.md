# API Documentation

Complete API reference for the Residency Scheduler application. All endpoints require JWT Bearer token authentication unless otherwise noted.

## Quick Start

### 1. Authentication

First, obtain authentication tokens:

```bash
curl -X POST http://localhost:8000/api/auth/login/json \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user@example.com",
    "password": "yourpassword"
  }'
```

Response includes `access_token` and `refresh_token`:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 2. Use Token for Authenticated Requests

```bash
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

### 3. Refresh Token When Expired

```bash
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<REFRESH_TOKEN>"}'
```

---

## API Guides

### [Authentication API](AUTH_API.md)
User authentication, token management, and authorization.

**Key Endpoints:**
- `POST /auth/login` - Login with form data
- `POST /auth/login/json` - Login with JSON
- `POST /auth/logout` - Logout and blacklist token
- `POST /auth/refresh` - Refresh access token
- `GET /auth/me` - Get current user info
- `POST /auth/register` - Register new user
- `GET /auth/users` - List all users (admin only)

**Tasks Covered (1-8):**
1. Read auth.py
2. Create AUTH_API.md comprehensive guide
3. Document login/logout endpoints
4. Document token refresh flow
5. Document password reset flow
6. Add authentication error codes
7. Create curl examples
8. Add rate limiting documentation

---

### [People API](PEOPLE_API.md)
Manage residents and faculty, including credentials and qualifications.

**Key Endpoints:**
- `GET /people` - List people with filtering
- `GET /people/residents` - List residents by PGY level
- `GET /people/faculty` - List faculty by specialty
- `GET /people/{person_id}` - Get person details
- `POST /people` - Create person
- `PUT /people/{person_id}` - Update person
- `DELETE /people/{person_id}` - Delete person
- `GET /people/{person_id}/credentials` - Get faculty credentials
- `GET /people/{person_id}/credentials/summary` - Get credential summary
- `GET /people/{person_id}/procedures` - Get qualified procedures

**Tasks Covered (9-16):**
9. Read people.py
10. Create PEOPLE_API.md comprehensive guide
11. Document CRUD operations with examples
12. Document role management endpoints
13. Document credential verification endpoints
14. Document availability endpoints
15. Add response schema documentation
16. Create curl examples

---

### [Assignments API](ASSIGNMENTS_API.md)
Manage schedule assignments with ACGME compliance validation.

**Key Endpoints:**
- `GET /assignments` - List assignments with filtering/pagination
- `GET /assignments/{assignment_id}` - Get assignment
- `POST /assignments` - Create assignment with validation
- `PUT /assignments/{assignment_id}` - Update assignment
- `DELETE /assignments/{assignment_id}` - Delete assignment
- `DELETE /assignments?start_date=X&end_date=Y` - Bulk delete

**ACGME Compliance:**
- 80-hour rule validation
- 1-in-7 days off validation
- Supervision ratio validation
- Violation warnings and error handling

**Tasks Covered (27-34):**
27. Read assignments.py
28. Create ASSIGNMENTS_API.md comprehensive guide
29. Document assignment CRUD operations
30. Document bulk assignment operations
31. Document assignment validation
32. Document assignment conflict resolution
33. Add filtering and search documentation
34. Create curl examples

---

### [Schedule API](SCHEDULE_API.md)
Schedule generation, validation, import, and analysis.

**Key Endpoints:**
- `POST /schedule/generate` - Generate schedule with multiple algorithms
- `GET /schedule/validate` - Validate ACGME compliance
- `POST /schedule/emergency-coverage` - Handle emergency absences
- `GET /schedule/{start_date}/{end_date}` - Get schedule for date range
- `POST /schedule/import/analyze` - Analyze imported Excel schedules
- `POST /schedule/import/analyze-file` - Quick analysis of single file
- `POST /schedule/import/block` - Parse specific block from Excel
- `POST /schedule/swaps/find` - Find swap candidates from FMIT file
- `POST /schedule/swaps/candidates` - Find swap candidates via JSON
- `POST /schedule/faculty-outpatient/generate` - Generate faculty assignments

**Scheduling Algorithms:**
- Greedy: Fast heuristic (< 1 second)
- CP-SAT: Constraint programming (5-30 seconds)
- PuLP: Linear programming (1-10 seconds)
- Hybrid: Combined approach (10-60 seconds)

**Tasks Covered (17-26):**
17. Read schedule.py
18. Create SCHEDULE_API.md comprehensive guide
19. Document schedule generation endpoint
20. Document schedule retrieval endpoints
21. Document schedule publication flow
22. Document conflict detection endpoint
23. Document bulk operations
24. Add query parameter documentation
25. Document pagination patterns
26. Create curl examples

---

### [Swaps API](SWAPS_API.md)
Faculty shift exchanges and FMIT rotation swaps.

**Key Endpoints:**
- `POST /swaps/execute` - Execute swap between faculty
- `POST /swaps/validate` - Validate swap without executing
- `GET /swaps/history` - Get swap history with filtering
- Plus swap finder endpoints in Schedule API

**Swap Types:**
- One-to-one swap: Direct exchange
- Absorb: One faculty takes assignment, other freed

**Tasks Covered (35-40):**
35. Read swap.py
36. Create SWAPS_API.md comprehensive guide
37. Document swap request creation
38. Document swap matching algorithm
39. Document swap execution
40. Document swap rollback

---

### [Resilience API](RESILIENCE_API.md)
System health monitoring, crisis management, and load shedding.

**Key Endpoints:**
- `GET /resilience/health` - Get system health status
- `GET /resilience/health/history` - Get health history
- `POST /resilience/crisis/activate` - Activate crisis mode
- `POST /resilience/crisis/deactivate` - Deactivate crisis mode
- `POST /resilience/fallback/activate` - Activate fallback schedule
- `POST /resilience/fallback/deactivate` - Deactivate fallback
- `GET /resilience/fallback/list` - List fallback schedules
- `GET /resilience/events/history` - Get event history
- `GET /resilience/vulnerabilities` - Identify system weaknesses
- `POST /resilience/load-shedding/activate` - Activate load shedding
- `POST /resilience/load-shedding/deactivate` - Deactivate load shedding

**Defense Levels:**
1. GREEN (< 60% utilization) - Optimal
2. YELLOW (60-75%) - Elevated
3. ORANGE (75-85%) - High
4. RED (85-95%) - Critical
5. BLACK (> 95% or crisis) - Emergency

**Tasks Covered (41-46):**
41. Read resilience.py
42. Create RESILIENCE_API.md comprehensive guide
43. Document health check endpoints
44. Document metrics endpoints
45. Document alert endpoints
46. Document contingency analysis endpoints

---

## OpenAPI Specification

### [openapi.yaml](openapi.yaml)

Complete OpenAPI 3.0 specification for all endpoints. Use with:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Code Generators**: OpenAPI Generator, Swagger Codegen, etc.

**Tasks Covered (47-49):**
47. Create openapi.yaml specification file
48. Add all endpoint definitions with schemas
49. Add security schemes

---

## Postman Collection

### [postman_collection.json](postman_collection.json)

Import this collection into Postman for interactive API testing:

1. Open Postman
2. Click "Import"
3. Select `postman_collection.json`
4. Set environment variables:
   - `base_url`: http://localhost:8000
   - `access_token`: (obtained from login)
   - `refresh_token`: (obtained from login)
   - `person_id`: (UUID from people list)
   - `assignment_id`: (UUID from assignments list)
   - etc.

**Features:**
- Pre-configured authentication flow
- Automatic token storage from login responses
- Example requests for all endpoints
- Environment variables for easy switching between dev/prod
- Test scripts for validation

**Task Covered (50):**
50. Create Postman collection export

---

## Common Workflows

### Generate Monthly Schedule

```bash
# 1. Generate schedule
RESPONSE=$(curl -X POST http://localhost:8000/api/schedule/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "start_date": "2025-01-01",
    "end_date": "2025-01-31",
    "algorithm": "cp_sat"
  }')

RUN_ID=$(echo $RESPONSE | jq -r '.run_id')
echo "Schedule Run ID: $RUN_ID"

# 2. Validate schedule
curl -X GET "http://localhost:8000/api/schedule/validate?start_date=2025-01-01&end_date=2025-01-31" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.'

# 3. View schedule
curl -X GET "http://localhost:8000/api/schedule/2025-01-01/2025-01-31" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.schedule'
```

### Handle Emergency Coverage

```bash
# 1. Detect who needs coverage
PERSON_ID="550e8400-e29b-41d4-a716-446655440001"
START="2025-02-01"
END="2025-02-07"

# 2. Request emergency coverage
curl -X POST http://localhost:8000/api/schedule/emergency-coverage \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d "{
    \"person_id\": \"$PERSON_ID\",
    \"start_date\": \"$START\",
    \"end_date\": \"$END\",
    \"reason\": \"Medical emergency\",
    \"is_deployment\": false
  }" | jq '.details.replacement_suggestions'

# 3. If manual review needed, activate crisis mode
curl -X POST http://localhost:8000/api/resilience/crisis/activate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "reason": "Emergency coverage for absent faculty",
    "expected_duration_hours": 24
  }'
```

### Perform Faculty Swap

```bash
# 1. Find swap candidates
curl -X POST http://localhost:8000/api/schedule/swaps/candidates \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "person_id": "faculty_id",
    "assignment_id": "assignment_id",
    "max_candidates": 10
  }' | jq '.candidates[0]'

# 2. Validate swap
curl -X POST http://localhost:8000/api/swaps/validate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "source_faculty_id": "faculty_1",
    "source_week": "2025-02-01",
    "target_faculty_id": "faculty_2",
    "target_week": "2025-03-01",
    "swap_type": "one_to_one",
    "reason": "Conference"
  }' | jq '.valid'

# 3. Execute swap if valid
curl -X POST http://localhost:8000/api/swaps/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{...}'
```

---

## Error Handling

All endpoints return standard HTTP status codes:

| Code | Meaning | Typical Cause |
|------|---------|---------------|
| 200 | OK | Request succeeded |
| 201 | Created | Resource created successfully |
| 204 | No Content | Deletion succeeded |
| 207 | Multi-Status | Partial success (e.g., schedule with gaps) |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Concurrent modification or duplicate request |
| 422 | Unprocessable Entity | Request conflict (e.g., ACGME violation without override) |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Server Error | Internal server error |

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **Login**: 5 attempts per 15 minutes
- **Registration**: 10 attempts per hour
- **General**: 1000 requests per hour per IP

Rate limit headers included in responses:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1704067200
```

---

## Authentication Best Practices

### For Frontend Applications

```javascript
// 1. Login and store tokens
const loginResponse = await fetch('/api/auth/login/json', {
  method: 'POST',
  credentials: 'include',  // Include httpOnly cookie
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username, password })
});

const data = await loginResponse.json();
localStorage.setItem('refresh_token', data.refresh_token);

// 2. Make authenticated requests
const apiResponse = await fetch('/api/auth/me', {
  credentials: 'include'  // Include httpOnly cookie
});

// 3. Refresh token on 401
if (apiResponse.status === 401) {
  const refreshResponse = await fetch('/api/auth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      refresh_token: localStorage.getItem('refresh_token')
    })
  });

  const newData = await refreshResponse.json();
  localStorage.setItem('refresh_token', newData.refresh_token);
  // Retry original request
}
```

### For CLI Tools

```bash
#!/bin/bash

# Get tokens
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/auth/login/json \
  -H "Content-Type: application/json" \
  -d '{"username":"user@example.com","password":"pass"}')

ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')
REFRESH_TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.refresh_token')

# Make authenticated request
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# Refresh token
REFRESH_RESPONSE=$(curl -s -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\":\"$REFRESH_TOKEN\"}")

NEW_TOKEN=$(echo $REFRESH_RESPONSE | jq -r '.access_token')
```

---

## Resources

- **[OpenAPI Specification](openapi.yaml)** - Machine-readable API definition
- **[Postman Collection](postman_collection.json)** - Interactive API testing
- **[CLAUDE.md](../../CLAUDE.md)** - Project guidelines and architecture
- **[ACGME Compliance](../architecture/ACGME_COMPLIANCE.md)** - Regulatory requirements
- **[Solver Algorithm](../architecture/SOLVER_ALGORITHM.md)** - Schedule generation details
- **[Resilience Framework](../architecture/cross-disciplinary-resilience.md)** - System resilience concepts

---

## Support

For API questions or issues:

1. Check the relevant API guide above
2. Review the OpenAPI specification
3. Test with the Postman collection
4. Check error messages and status codes
5. Review server logs for detailed error information

---

## API Versions

This documentation covers API v1.0.0.

Current version: `/api`

Future versions (if applicable): `/api/v2`, `/api/v3`, etc.

---

## Summary

**Total API Endpoints:** 50+ endpoints across 6 major categories

**Total Documentation Tasks Completed:** 50

1. ✅ AUTH_API.md (Tasks 1-8)
2. ✅ PEOPLE_API.md (Tasks 9-16)
3. ✅ ASSIGNMENTS_API.md (Tasks 27-34)
4. ✅ SCHEDULE_API.md (Tasks 17-26)
5. ✅ SWAPS_API.md (Tasks 35-40)
6. ✅ RESILIENCE_API.md (Tasks 41-46)
7. ✅ openapi.yaml (Tasks 47-49)
8. ✅ postman_collection.json (Task 50)

All API endpoints are fully documented with:
- Detailed descriptions
- Request/response examples
- Curl command examples
- Parameter documentation
- Error handling guide
- Best practices
- Common workflows
