# Test Files Summary

## test_people_routes.py

**Total Test Functions:** 65
**Total Test Classes:** 12

### Test Classes and Coverage:

1. **TestListPeopleEndpoint** - Tests for GET /api/people
   - Empty list
   - List with data
   - Filter by type (resident/faculty)
   - Filter by PGY level
   - Combined filters
   - Authentication required

2. **TestListResidentsEndpoint** - Tests for GET /api/people/residents
   - List all residents
   - Filter by PGY level
   - Empty results
   - Excludes faculty
   - Authentication required

3. **TestListFacultyEndpoint** - Tests for GET /api/people/faculty
   - List all faculty
   - Filter by specialty
   - Empty results
   - Excludes residents
   - Authentication required

4. **TestGetPersonEndpoint** - Tests for GET /api/people/{person_id}
   - Get resident success
   - Get faculty success
   - Person not found (404)
   - Invalid UUID (422)
   - Authentication required
   - Includes timestamps

5. **TestCreatePersonEndpoint** - Tests for POST /api/people
   - Create resident success
   - Create faculty success
   - Invalid type validation
   - Invalid PGY level validation
   - Missing required fields
   - Duplicate email handling
   - Authentication required
   - Faculty with role

6. **TestUpdatePersonEndpoint** - Tests for PUT /api/people/{person_id}
   - Update name
   - Update PGY level
   - Update specialties
   - Person not found
   - Invalid UUID
   - Authentication required
   - Partial updates

7. **TestDeletePersonEndpoint** - Tests for DELETE /api/people/{person_id}
   - Delete success
   - Person not found
   - Invalid UUID
   - Authentication required
   - Delete twice (idempotency)

8. **TestPersonCredentialsEndpoint** - Tests for GET /api/people/{person_id}/credentials
   - Empty credentials
   - Person not found
   - Filter by status
   - Include expired
   - Authentication required

9. **TestPersonCredentialSummaryEndpoint** - Tests for GET /api/people/{person_id}/credentials/summary
   - Get summary success
   - Person not found
   - Invalid UUID
   - Authentication required

10. **TestPersonProceduresEndpoint** - Tests for GET /api/people/{person_id}/procedures
    - Empty procedures
    - Person not found
    - Invalid UUID
    - Authentication required

11. **TestPersonResponseStructure** - Response validation tests
    - All required fields present
    - Resident has PGY level
    - Faculty has specialties
    - Valid type values

12. **TestPersonEdgeCases** - Edge case tests
    - Create without email
    - Create faculty without specialties
    - PGY level boundary values
    - Update with empty body
    - Very long name

---

## test_calendar_routes.py

**Total Test Functions:** 51
**Total Test Classes:** 10

### Test Classes and Coverage:

1. **TestExportAllCalendarsEndpoint** - Tests for GET /api/calendar/export/ics
   - Export success
   - Filter by person_ids
   - Filter by rotation_ids
   - Missing dates validation
   - Invalid date range
   - Empty range
   - Filename format

2. **TestExportPersonICSEndpoint** - Tests for GET /api/calendar/export/ics/{person_id}
   - Export success
   - Person not found
   - Invalid UUID
   - Missing dates
   - Include types filter
   - Filename format

3. **TestExportPersonCalendarEndpoint** - Tests for GET /api/calendar/export/person/{person_id}
   - Export success
   - Person not found
   - Invalid UUID
   - Long date range

4. **TestExportRotationCalendarEndpoint** - Tests for GET /api/calendar/export/rotation/{rotation_id}
   - Export success
   - Rotation not found
   - Invalid UUID
   - Missing dates
   - Filename format

5. **TestCreateSubscriptionEndpoint** - Tests for POST /api/calendar/subscribe
   - Create success
   - With custom expiration
   - Person not found
   - Missing person_id
   - Authentication required
   - Webcal URL format

6. **TestGetSubscriptionFeedEndpoint** - Tests for GET /api/calendar/subscribe/{token}
   - Feed success
   - Invalid token
   - Expired token
   - Inactive token
   - No auth required (token-based)
   - Cache headers

7. **TestListSubscriptionsEndpoint** - Tests for GET /api/calendar/subscriptions
   - Empty list
   - List with data
   - Filter by person
   - Active only filter
   - Authentication required
   - Includes URLs

8. **TestRevokeSubscriptionEndpoint** - Tests for DELETE /api/calendar/subscribe/{token}
   - Revoke success
   - Not found
   - Authentication required
   - Unauthorized (different user)

9. **TestCalendarICSContent** - ICS format validation
   - VCALENDAR wrapper
   - VERSION property
   - PRODID property

10. **TestCalendarEdgeCases** - Edge case tests
    - Same day range
    - Very long range
    - Token uniqueness
    - Empty person_ids list

---

## Test Coverage Summary

### People Routes (10 endpoints)
- ✓ GET /api/people
- ✓ GET /api/people/residents
- ✓ GET /api/people/faculty
- ✓ GET /api/people/{person_id}
- ✓ POST /api/people
- ✓ PUT /api/people/{person_id}
- ✓ DELETE /api/people/{person_id}
- ✓ GET /api/people/{person_id}/credentials
- ✓ GET /api/people/{person_id}/credentials/summary
- ✓ GET /api/people/{person_id}/procedures

**All endpoints covered with:**
- Success cases
- Error cases (404, 422)
- Authentication tests
- Filter/parameter tests
- Edge cases

### Calendar Routes (8 main endpoints + 1 legacy)
- ✓ GET /api/calendar/export/ics
- ✓ GET /api/calendar/export/ics/{person_id}
- ✓ GET /api/calendar/export/person/{person_id}
- ✓ GET /api/calendar/export/rotation/{rotation_id}
- ✓ POST /api/calendar/subscribe
- ✓ GET /api/calendar/subscribe/{token}
- ✓ GET /api/calendar/subscriptions
- ✓ DELETE /api/calendar/subscribe/{token}

**All endpoints covered with:**
- ICS content-type validation
- Date filtering tests
- Token-based authentication
- User authorization
- Cache header validation
- Edge cases

---

## Test Patterns Used

Following the established pattern from `test_blocks_routes.py`:

1. **Class-based organization** - One class per endpoint or feature
2. **Comprehensive fixtures** - Using conftest.py fixtures (client, db, auth_headers, sample data)
3. **Clear test names** - Descriptive names indicating what's being tested
4. **HTTP assertions** - Status code, response structure, headers
5. **Error coverage** - 404, 422, 401, 403 responses
6. **Edge case testing** - Boundary conditions, empty data, invalid input

---

## Running the Tests

```bash
# Run all people route tests
pytest tests/test_people_routes.py -v

# Run all calendar route tests
pytest tests/test_calendar_routes.py -v

# Run specific test class
pytest tests/test_people_routes.py::TestCreatePersonEndpoint -v

# Run with coverage
pytest tests/test_people_routes.py --cov=app.api.routes.people
pytest tests/test_calendar_routes.py --cov=app.api.routes.calendar
```

---

## Notes

- All People API tests require authentication (using `auth_headers` fixture)
- Calendar export endpoints (ICS files) do not require authentication
- Calendar subscription management requires authentication
- Subscription feed access uses token-based auth (no headers needed)
- Both test files validate response structure, error handling, and edge cases
