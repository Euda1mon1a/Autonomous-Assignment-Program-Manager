# Backend API Route Testing Checklist
## SESSION 8 BURN: FastAPI Endpoint Quality Gates

**Generated:** 2025-12-31
**Based On:** SESSION_1_BACKEND/backend-api-routes.md
**Status:** COMPREHENSIVE TESTING CHECKLIST

---

## Executive Summary

**572 total endpoints** across 71 route files require testing framework:
- ✅ **Thin routing compliance:** 92/100 (excellent)
- ⚠️ **Error consistency:** 60/100 (needs standardization)
- ⚠️ **Route bloat:** 3 files > 1,400 lines (refactor recommended)
- ✅ **Security headers:** 95/100 (excellent)

This checklist provides quality gates for every API endpoint.

---

## SECTION 1: AUTHENTICATION & AUTHORIZATION TESTING

### Checklist: Authentication Coverage

For **every protected endpoint**, verify:

```python
# Template for testing protected routes
@pytest.mark.asyncio
async def test_endpoint_requires_auth(client):
    """Verify endpoint requires authentication."""
    response = client.get("/api/v1/assignments")
    assert response.status_code == 401  # Unauthorized

@pytest.mark.asyncio
async def test_endpoint_with_valid_auth(client, auth_header):
    """Verify endpoint works with valid auth."""
    response = client.get(
        "/api/v1/assignments",
        headers=auth_header
    )
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_endpoint_with_invalid_token(client):
    """Verify endpoint rejects invalid token."""
    response = client.get(
        "/api/v1/assignments",
        headers={"Authorization": "Bearer invalid"}
    )
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_endpoint_with_expired_token(client):
    """Verify endpoint rejects expired token."""
    response = client.get(
        "/api/v1/assignments",
        headers={"Authorization": f"Bearer {EXPIRED_TOKEN}"}
    )
    assert response.status_code == 401
```

### Checklist: Role-Based Authorization

For **admin-only endpoints**:

```python
@pytest.mark.asyncio
async def test_admin_endpoint_requires_admin_role(
    client,
    resident_auth_header,
    admin_auth_header
):
    """Verify admin endpoints enforce role."""
    # Resident should be denied
    response = client.delete(
        "/api/v1/admin/users/user-123",
        headers=resident_auth_header
    )
    assert response.status_code == 403  # Forbidden

    # Admin should succeed
    response = client.delete(
        "/api/v1/admin/users/user-123",
        headers=admin_auth_header
    )
    assert response.status_code == 204  # No Content
```

### Checklist: Rate Limiting

For **sensitive endpoints** (login, password reset):

```python
@pytest.mark.asyncio
async def test_login_rate_limit(client):
    """Verify login endpoint rate limiting."""
    for attempt in range(10):  # Exceed limit
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "test", "password": "wrong"}
        )

    # Should hit rate limit
    assert response.status_code == 429  # Too Many Requests
    assert "Retry-After" in response.headers
```

---

## SECTION 2: REQUEST VALIDATION TESTING

### Checklist: Input Validation

For **every endpoint accepting input**, test:

```python
# Template: Validation error cases
@pytest.mark.parametrize("invalid_input", [
    {"block_id": "invalid-uuid"},           # Bad UUID
    {"block_id": None},                      # Missing required
    {"block_id": ""},                        # Empty string
    {"block_id": "000-000-000-000"},        # Wrong format
])
@pytest.mark.asyncio
async def test_create_assignment_invalid_input(client, invalid_input, auth_header):
    """Verify validation rejects invalid inputs."""
    response = client.post(
        "/api/v1/assignments",
        json=invalid_input,
        headers=auth_header
    )
    assert response.status_code == 422  # Unprocessable Entity
    body = response.json()
    assert "errors" in body or "detail" in body

@pytest.mark.asyncio
async def test_create_assignment_missing_required_field(client, auth_header):
    """Verify required fields are enforced."""
    response = client.post(
        "/api/v1/assignments",
        json={"block_id": str(uuid4())},  # Missing person_id
        headers=auth_header
    )
    assert response.status_code == 422
    body = response.json()
    # Verify error mentions the missing field
    assert "person_id" in str(body).lower()
```

### Checklist: Query Parameter Validation

For **GET endpoints with filters**:

```python
@pytest.mark.asyncio
async def test_list_with_invalid_date_format(client, auth_header):
    """Verify date format validation."""
    response = client.get(
        "/api/v1/assignments?start_date=invalid-date",
        headers=auth_header
    )
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_list_with_pagination_limits(client, auth_header):
    """Verify pagination limits enforced."""
    # Exceeds max page size (500)
    response = client.get(
        "/api/v1/assignments?page_size=1000",
        headers=auth_header
    )
    assert response.status_code == 422

    # Valid max page size
    response = client.get(
        "/api/v1/assignments?page_size=500",
        headers=auth_header
    )
    assert response.status_code == 200
```

---

## SECTION 3: RESPONSE FORMAT TESTING

### Checklist: RFC 7807 Compliance (Error Responses)

For **every error response**, verify:

```python
@pytest.mark.asyncio
async def test_error_response_format(client):
    """Verify error responses follow RFC 7807."""
    response = client.get("/api/v1/assignments/invalid-id")

    assert response.status_code == 422
    body = response.json()

    # [ ] RFC 7807 required fields
    assert "type" in body
    assert "title" in body
    assert "status" in body
    assert "detail" in body
    assert "instance" in body or "path" in body

    # [ ] Custom fields
    assert "error_code" in body
    assert "error_id" in body
    assert "timestamp" in body

    # [ ] Verify values
    assert body["status"] == 422
    assert body["title"] in ["Validation Failed", "Unprocessable Entity"]
```

### Checklist: Success Response Format

For **every success response**, verify:

```python
@pytest.mark.asyncio
async def test_create_assignment_response_format(client, auth_header):
    """Verify success response includes required fields."""
    response = client.post(
        "/api/v1/assignments",
        json={
            "block_id": BLOCK_ID,
            "person_id": PERSON_ID,
            "rotation_template_id": ROTATION_ID,
        },
        headers=auth_header
    )

    assert response.status_code == 201
    body = response.json()

    # [ ] Response model fields
    assert "id" in body
    assert "block_id" in body
    assert "person_id" in body
    assert "created_at" in body

    # [ ] Status code consistency
    assert response.headers["Content-Type"] == "application/json"

    # [ ] Location header for creation
    assert "Location" in response.headers or response.status_code != 201
```

### Checklist: Pagination Response Format

For **list endpoints**:

```python
@pytest.mark.asyncio
async def test_list_response_pagination_format(client, auth_header):
    """Verify paginated list response includes pagination metadata."""
    response = client.get(
        "/api/v1/assignments?page=1&page_size=50",
        headers=auth_header
    )

    assert response.status_code == 200
    body = response.json()

    # [ ] Pagination fields
    assert "items" in body or "data" in body
    assert "total" in body or "total_count" in body
    assert "page" in body or "offset" in body

    # [ ] Verify values
    items = body.get("items") or body.get("data")
    assert isinstance(items, list)
    assert len(items) <= 50
```

---

## SECTION 4: HTTP METHOD & STATUS CODE TESTING

### Checklist: GET Requests (Read)

```python
@pytest.mark.asyncio
async def test_get_single_resource(client, auth_header):
    """Test: GET /resource/{id} returns 200 with single object."""
    response = client.get(f"/api/v1/assignments/{ASSIGNMENT_ID}", headers=auth_header)
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == ASSIGNMENT_ID

@pytest.mark.asyncio
async def test_get_nonexistent_resource(client, auth_header):
    """Test: GET /resource/{invalid-id} returns 404."""
    response = client.get(
        f"/api/v1/assignments/{uuid4()}",
        headers=auth_header
    )
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_get_list_resources(client, auth_header):
    """Test: GET /resources returns 200 with list."""
    response = client.get("/api/v1/assignments", headers=auth_header)
    assert response.status_code == 200
    body = response.json()
    assert "items" in body or "data" in body
```

### Checklist: POST Requests (Create)

```python
@pytest.mark.asyncio
async def test_post_create_success(client, auth_header):
    """Test: POST /resource returns 201 Created."""
    response = client.post(
        "/api/v1/assignments",
        json={
            "block_id": BLOCK_ID,
            "person_id": PERSON_ID,
        },
        headers=auth_header
    )
    assert response.status_code == 201
    body = response.json()
    assert "id" in body

@pytest.mark.asyncio
async def test_post_duplicate_conflict(client, auth_header):
    """Test: POST duplicate returns 409 Conflict."""
    # Create first
    client.post(
        "/api/v1/assignments",
        json={"block_id": BLOCK_ID, "person_id": PERSON_ID},
        headers=auth_header
    )

    # Try to create duplicate
    response = client.post(
        "/api/v1/assignments",
        json={"block_id": BLOCK_ID, "person_id": PERSON_ID},
        headers=auth_header
    )
    assert response.status_code == 409  # Conflict
```

### Checklist: PUT Requests (Full Update)

```python
@pytest.mark.asyncio
async def test_put_full_update(client, auth_header):
    """Test: PUT /resource/{id} updates all fields."""
    response = client.put(
        f"/api/v1/assignments/{ASSIGNMENT_ID}",
        json={
            "block_id": NEW_BLOCK_ID,
            "person_id": NEW_PERSON_ID,
            "rotation_template_id": NEW_ROTATION_ID,
        },
        headers=auth_header
    )
    assert response.status_code == 200
    body = response.json()
    assert body["block_id"] == NEW_BLOCK_ID
```

### Checklist: DELETE Requests

```python
@pytest.mark.asyncio
async def test_delete_success(client, auth_header):
    """Test: DELETE /resource/{id} returns 204 No Content."""
    response = client.delete(
        f"/api/v1/assignments/{ASSIGNMENT_ID}",
        headers=auth_header
    )
    assert response.status_code == 204
    assert response.content == b""  # No body

@pytest.mark.asyncio
async def test_delete_nonexistent(client, auth_header):
    """Test: DELETE nonexistent returns 404."""
    response = client.delete(
        f"/api/v1/assignments/{uuid4()}",
        headers=auth_header
    )
    assert response.status_code == 404
```

---

## SECTION 5: BUSINESS LOGIC TESTING

### Checklist: ACGME Compliance

For **schedule-related endpoints**:

```python
@pytest.mark.asyncio
async def test_create_assignment_violates_80_hour_rule(client, auth_header):
    """Test: Creating assignment exceeding 80 hours returns 409."""
    # Resident already has 75 hours this week
    # Adding 10-hour block would exceed 80-hour limit

    response = client.post(
        "/api/v1/assignments",
        json={
            "block_id": BLOCK_10_HOURS,
            "person_id": RESIDENT_WITH_75_HOURS,
        },
        headers=auth_header
    )

    assert response.status_code == 409
    body = response.json()
    assert "80_hour" in body.get("error_code", "").lower()

@pytest.mark.asyncio
async def test_create_assignment_violates_1_in_7_rule(client, auth_header):
    """Test: 1-in-7 rest day violation returns 409."""
    response = client.post(
        "/api/v1/assignments",
        json={
            "block_id": BLOCK_VIOLATING_1_IN_7,
            "person_id": RESIDENT_ID,
        },
        headers=auth_header
    )

    assert response.status_code == 409
    body = response.json()
    assert "1_in_7" in body.get("error_code", "").lower()
```

### Checklist: Swap Operations

For **swap endpoints**:

```python
@pytest.mark.asyncio
async def test_swap_requires_valid_assignments(client, auth_header):
    """Test: Swapping invalid assignments returns 404."""
    response = client.post(
        "/api/v1/swaps/execute",
        json={
            "source_faculty_id": FACULTY_A,
            "source_week": WEEK_1,
            "target_faculty_id": FACULTY_B,
            "target_week": WEEK_2,
        },
        headers=auth_header
    )

    # Should fail if assignments don't exist
    assert response.status_code in [404, 409]

@pytest.mark.asyncio
async def test_swap_24hr_rollback_window(client, auth_header):
    """Test: Swap can be rolled back within 24 hours."""
    # Create swap
    swap_response = client.post(
        "/api/v1/swaps/execute",
        json={...},
        headers=auth_header
    )
    swap_id = swap_response.json()["id"]

    # Rollback within 24 hours should succeed
    response = client.post(
        f"/api/v1/swaps/{swap_id}/rollback",
        headers=auth_header
    )
    assert response.status_code == 200

    # After 24 hours should fail
    # (requires time manipulation in tests)
```

---

## SECTION 6: CONCURRENCY & DATA INTEGRITY

### Checklist: Optimistic Locking

For **endpoints modifying existing resources**:

```python
@pytest.mark.asyncio
async def test_concurrent_update_conflict(client, auth_header):
    """Test: Concurrent updates detect conflict."""
    # Get assignment (version 1)
    assignment = client.get(
        f"/api/v1/assignments/{ASSIGNMENT_ID}",
        headers=auth_header
    ).json()

    # User A modifies
    update1 = client.put(
        f"/api/v1/assignments/{ASSIGNMENT_ID}",
        json={**assignment, "rotation_template_id": NEW_ROTATION_1},
        headers=auth_header
    )
    assert update1.status_code == 200

    # User B tries to modify (with old version)
    update2 = client.put(
        f"/api/v1/assignments/{ASSIGNMENT_ID}",
        json={**assignment, "rotation_template_id": NEW_ROTATION_2},
        headers=auth_header
    )

    # Should detect version mismatch
    assert update2.status_code == 409  # Conflict
```

### Checklist: Idempotency

For **critical create/update operations**:

```python
@pytest.mark.asyncio
async def test_create_with_idempotency_key(client, auth_header):
    """Test: Idempotency key prevents duplicate creates."""
    idempotency_key = str(uuid4())

    # First request
    response1 = client.post(
        "/api/v1/assignments",
        json={"block_id": BLOCK_ID, "person_id": PERSON_ID},
        headers={**auth_header, "Idempotency-Key": idempotency_key}
    )
    assignment_id_1 = response1.json()["id"]

    # Retry with same key
    response2 = client.post(
        "/api/v1/assignments",
        json={"block_id": BLOCK_ID, "person_id": PERSON_ID},
        headers={**auth_header, "Idempotency-Key": idempotency_key}
    )
    assignment_id_2 = response2.json()["id"]

    # Should return same resource
    assert assignment_id_1 == assignment_id_2
    assert response1.status_code == response2.status_code
```

---

## SECTION 7: EDGE CASES & BOUNDARY CONDITIONS

### Checklist: Date/Time Boundaries

For **date-based filtering**:

```python
@pytest.mark.asyncio
async def test_list_assignments_boundary_dates(client, auth_header):
    """Test: Boundary date filtering includes correct records."""
    # List assignments on exact date
    response = client.get(
        f"/api/v1/assignments?start_date=2025-12-31&end_date=2025-12-31",
        headers=auth_header
    )
    assert response.status_code == 200

    # List with time component (should ignore time)
    response = client.get(
        f"/api/v1/assignments?start_date=2025-12-31T00:00:00Z",
        headers=auth_header
    )
    assert response.status_code == 200
```

### Checklist: Empty Results

For **list endpoints**:

```python
@pytest.mark.asyncio
async def test_list_empty_results(client, auth_header):
    """Test: Empty list returns proper format with 0 items."""
    response = client.get(
        "/api/v1/assignments?person_id=nonexistent-id",
        headers=auth_header
    )

    assert response.status_code == 200
    body = response.json()
    assert body["items"] == [] or body["data"] == []
    assert body["total"] == 0
```

### Checklist: Large Result Sets

For **pagination**:

```python
@pytest.mark.asyncio
async def test_list_large_result_set_performance(client, auth_header):
    """Test: Large result sets return within time limit."""
    import time

    start = time.time()
    response = client.get(
        "/api/v1/assignments?page_size=500",
        headers=auth_header
    )
    duration = time.time() - start

    assert response.status_code == 200
    assert duration < 5.0  # Should complete in < 5 seconds
```

---

## SECTION 8: SECURITY TESTING

### Checklist: Header Security

```python
@pytest.mark.asyncio
async def test_security_headers_present(client):
    """Verify security headers in responses."""
    response = client.get("/api/v1/health")

    # [ ] HSTS
    assert "Strict-Transport-Security" in response.headers

    # [ ] X-Content-Type-Options
    assert response.headers.get("X-Content-Type-Options") == "nosniff"

    # [ ] X-Frame-Options
    assert response.headers.get("X-Frame-Options") == "DENY"

    # [ ] CSP (if applicable)
    if "Content-Security-Policy" in response.headers:
        assert "script-src" in response.headers["Content-Security-Policy"]
```

### Checklist: CORS

```python
@pytest.mark.asyncio
async def test_cors_allowed_origins(client):
    """Test: CORS headers set correctly."""
    response = client.get(
        "/api/v1/assignments",
        headers={"Origin": "https://trusted-domain.com"}
    )

    # Should allow from trusted origin
    assert response.headers.get("Access-Control-Allow-Origin") == "https://trusted-domain.com"

@pytest.mark.asyncio
async def test_cors_untrusted_origin(client):
    """Test: Untrusted origin denied."""
    response = client.get(
        "/api/v1/assignments",
        headers={"Origin": "https://untrusted.com"}
    )

    # Should not allow from untrusted origin
    assert "Access-Control-Allow-Origin" not in response.headers
```

### Checklist: No Sensitive Data Exposure

```python
@pytest.mark.asyncio
async def test_error_response_no_database_details(client):
    """Verify error responses don't leak database schema."""
    response = client.post(
        "/api/v1/assignments",
        json={"block_id": "invalid"}
    )

    body = response.json()

    # [ ] No SQL syntax in error
    assert "SELECT" not in str(body).upper()
    assert "INSERT" not in str(body).upper()

    # [ ] No table names
    assert "assignment" not in str(body).lower() or "table" not in str(body).lower()

    # [ ] No internal paths
    assert "/app/" not in str(body)
    assert "File" not in str(body)
```

---

## SECTION 9: PERFORMANCE TESTING

### Checklist: Response Time SLAs

```python
@pytest.mark.asyncio
async def test_list_assignments_response_time(client, auth_header):
    """Test: List endpoint meets response time SLA (< 1s)."""
    import time

    start = time.time()
    response = client.get("/api/v1/assignments?page_size=100", headers=auth_header)
    duration = (time.time() - start) * 1000  # ms

    assert response.status_code == 200
    assert duration < 1000  # SLA: < 1 second

@pytest.mark.asyncio
async def test_create_assignment_response_time(client, auth_header):
    """Test: Create endpoint meets response time SLA (< 500ms)."""
    import time

    start = time.time()
    response = client.post(
        "/api/v1/assignments",
        json={"block_id": BLOCK_ID, "person_id": PERSON_ID},
        headers=auth_header
    )
    duration = (time.time() - start) * 1000

    assert response.status_code == 201
    assert duration < 500  # SLA: < 500ms
```

---

## SECTION 10: COMPREHENSIVE CHECKLIST TEMPLATE

Use this checklist for **every API endpoint**:

```
Endpoint: POST /api/v1/assignments
Method: POST
Status: [ ] Complete

AUTHENTICATION & AUTHORIZATION
  [ ] Requires valid JWT token
  [ ] Rejects missing token (401)
  [ ] Rejects expired token (401)
  [ ] Rejects invalid token (401)
  [ ] Correct role/permission required (403 if wrong role)

REQUEST VALIDATION
  [ ] Validates required fields (422 if missing)
  [ ] Validates data types (422 if wrong type)
  [ ] Validates UUID format (422 if malformed)
  [ ] Validates enum values (422 if invalid)
  [ ] Validates value ranges (422 if out of range)

RESPONSE FORMAT
  [ ] Success response (201)
  [ ] Response model matches schema
  [ ] Error responses follow RFC 7807
  [ ] Status codes correct for all cases

BUSINESS LOGIC
  [ ] ACGME compliance validated
  [ ] Duplicate check performed
  [ ] Related resources exist (404 if missing)
  [ ] Cascade effects handled correctly

DATA INTEGRITY
  [ ] Transaction rollback on error
  [ ] Optimistic locking (if applicable)
  [ ] Audit trail logged

SECURITY
  [ ] No sensitive data in error messages
  [ ] Input sanitized (no SQL injection risk)
  [ ] Rate limiting applied (if applicable)
  [ ] Security headers present

PERFORMANCE
  [ ] Response time < SLA
  [ ] No N+1 queries
  [ ] Pagination working (if applicable)
  [ ] Indexes used correctly

EDGE CASES
  [ ] Empty input handling
  [ ] Large result sets
  [ ] Boundary values
  [ ] Special characters
  [ ] Concurrency scenarios
```

---

## SECTION 11: CONTINUOUS TESTING

### Pre-Commit Testing

```bash
# Run before committing changes to routes
cd backend

# 1. Lint
ruff check . --fix

# 2. Type check
mypy app/api/routes

# 3. Unit tests for route
pytest tests/routes/ -v

# 4. Integration tests
pytest tests/integration/api/ -v --maxfail=1
```

### CI/CD Testing

```yaml
# .github/workflows/api-tests.yml
name: API Route Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2

      - name: Install dependencies
        run: pip install -r backend/requirements.txt

      - name: Run API tests
        run: |
          cd backend
          pytest tests/routes/ \
            -v \
            --tb=short \
            --maxfail=5 \
            --cov=app.api.routes

      - name: Security scanning
        run: |
          cd backend
          bandit -r app/api/routes
```

---

## SECTION 12: REFERENCE CHECKLIST BY ROUTE FILE

| Route File | Endpoints | Priority | Test Status |
|------------|-----------|----------|------------|
| `auth.py` | 10 | P0 | [ ] Complete |
| `assignments.py` | 12 | P0 | [ ] Complete |
| `swap.py` | 8 | P0 | [ ] Complete |
| `people.py` | 15 | P0 | [ ] Complete |
| `resilience.py` | 54 | P1 | [ ] Complete |
| `schedule.py` | 10 | P0 | [ ] Complete |
| `health.py` | 8 | P2 | [ ] Complete |
| `audit.py` | 12 | P1 | [ ] Complete |
| `analytics.py` | 20 | P2 | [ ] Complete |
| `portal.py` | 25 | P1 | [ ] Complete |

---

## SECTION 13: AUTOMATED TEST GENERATION

### Generate Test Stubs from OpenAPI Schema

```bash
# Generate test file from OpenAPI spec
openapi-generator-cli generate \
  -i backend/openapi.json \
  -g python-pytest \
  -o backend/tests/generated/

# Then customize with business logic assertions
```

---

## SECTION 14: SUMMARY & GOALS

**Testing Goals for SESSION 8:**
- [ ] 80%+ test coverage for all routes
- [ ] 100% authentication testing
- [ ] 100% error response validation
- [ ] Performance testing for critical paths
- [ ] Security header validation
- [ ] ACGME compliance testing

**Timeline:**
- Week 1: Foundation (auth, validation)
- Week 2: Business logic (ACGME, swaps)
- Week 3: Edge cases & performance
- Week 4: Security & integration

---

*Generated by SESSION 8 BURN - Backend Improvements*
*Reference: SESSION_1_BACKEND/backend-api-routes.md*
