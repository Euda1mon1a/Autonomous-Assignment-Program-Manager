***REMOVED*** API Versioning

This document describes the versioning strategy for the Residency Scheduler API.

***REMOVED******REMOVED*** Current Version

**API Version:** 1.0.0

**Release Date:** December 2024

***REMOVED******REMOVED*** Versioning Strategy

The API uses **URL path versioning** with semantic versioning principles for the version number.

***REMOVED******REMOVED******REMOVED*** URL Structure

```
https://your-domain.com/api/v{major}/resource
```

**Current Version (v1):**
```
https://your-domain.com/api/people
https://your-domain.com/api/schedule
```

**Future Version (v2):**
```
https://your-domain.com/api/v2/people
https://your-domain.com/api/v2/schedule
```

***REMOVED******REMOVED******REMOVED*** Version Placement

For the initial v1 API, the version is implicit in the `/api` prefix. Future major versions will include an explicit version number.

| Version | Base Path | Status |
|---------|-----------|--------|
| v1 | `/api` | Current |
| v2 | `/api/v2` | Future |
| v3 | `/api/v3` | Future |

***REMOVED******REMOVED*** Semantic Versioning

The API follows [Semantic Versioning 2.0.0](https://semver.org/):

```
MAJOR.MINOR.PATCH
```

| Component | Description | Example Change |
|-----------|-------------|----------------|
| MAJOR | Breaking changes | Removing endpoints, changing response format |
| MINOR | Backward-compatible additions | New endpoints, new optional fields |
| PATCH | Backward-compatible fixes | Bug fixes, documentation updates |

***REMOVED******REMOVED******REMOVED*** Version Examples

| Version | Changes |
|---------|---------|
| 1.0.0 | Initial release |
| 1.1.0 | Added export endpoints |
| 1.1.1 | Fixed validation bug |
| 1.2.0 | Added batch operations |
| 2.0.0 | Restructured response format (breaking) |

***REMOVED******REMOVED*** Breaking Changes

The following changes are considered **breaking** and require a major version bump:

***REMOVED******REMOVED******REMOVED*** Endpoint Changes
- Removing an endpoint
- Changing an endpoint's HTTP method
- Changing URL path structure
- Removing required functionality

***REMOVED******REMOVED******REMOVED*** Request Changes
- Adding a new required field
- Removing an optional field that clients may use
- Changing field validation rules (stricter)
- Changing field types

***REMOVED******REMOVED******REMOVED*** Response Changes
- Removing a field from responses
- Changing field types
- Changing response structure
- Changing error response format

***REMOVED******REMOVED******REMOVED*** Authentication Changes
- Changing authentication mechanism
- Changing token format
- Removing authentication methods

***REMOVED******REMOVED*** Non-Breaking Changes

The following changes are **non-breaking** and can be made in minor versions:

***REMOVED******REMOVED******REMOVED*** Additions
- New endpoints
- New optional request fields
- New response fields
- New query parameters
- New HTTP methods on existing resources

***REMOVED******REMOVED******REMOVED*** Deprecations
- Marking endpoints as deprecated (with warning)
- Marking fields as deprecated (with warning)

***REMOVED******REMOVED******REMOVED*** Other
- Performance improvements
- Bug fixes (that don't change behavior)
- Documentation updates

***REMOVED******REMOVED*** Deprecation Policy

***REMOVED******REMOVED******REMOVED*** Deprecation Timeline

1. **Announcement**: Feature marked deprecated with warning
2. **Warning Period**: 6 months of continued support
3. **Sunset**: Feature removed in next major version

***REMOVED******REMOVED******REMOVED*** Deprecation Notices

Deprecated features return a warning header:

```http
HTTP/1.1 200 OK
X-API-Deprecation: true
X-API-Deprecation-Date: 2024-06-01
X-API-Deprecation-Info: This endpoint is deprecated. Use /api/v2/people instead.

{
  "items": [...],
  "total": 10
}
```

***REMOVED******REMOVED******REMOVED*** Example: Endpoint Deprecation

```bash
***REMOVED*** Deprecated endpoint
curl http://localhost:8000/api/legacy-endpoint

***REMOVED*** Response includes deprecation headers
***REMOVED*** X-API-Deprecation: true
***REMOVED*** X-API-Deprecation-Date: 2024-06-01
***REMOVED*** X-API-Deprecation-Info: Use /api/v2/new-endpoint instead

***REMOVED*** Response body remains functional during deprecation period
```

***REMOVED******REMOVED*** Version Discovery

***REMOVED******REMOVED******REMOVED*** Health Endpoint

The root endpoint returns the current API version:

```bash
curl http://localhost:8000/

***REMOVED*** Response:
{
  "name": "Residency Scheduler API",
  "version": "1.0.0",
  "status": "healthy"
}
```

***REMOVED******REMOVED******REMOVED*** OpenAPI Specification

The OpenAPI spec includes version information:

```yaml
openapi: 3.0.0
info:
  title: Residency Scheduler API
  version: 1.0.0
  description: API for medical residency scheduling
```

Access at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

***REMOVED******REMOVED*** Compatibility Headers

***REMOVED******REMOVED******REMOVED*** Request Version Header

Clients can request a specific API version behavior using headers:

```bash
curl http://localhost:8000/api/people \
  -H "X-API-Version: 1.0"
```

***REMOVED******REMOVED******REMOVED*** Response Version Header

Responses include the API version used:

```http
HTTP/1.1 200 OK
X-API-Version: 1.0.0
```

***REMOVED******REMOVED*** Migration Guides

***REMOVED******REMOVED******REMOVED*** Migrating to v2 (Future)

When v2 is released, migration guides will be provided:

```markdown
***REMOVED******REMOVED*** v1 to v2 Migration Guide

***REMOVED******REMOVED******REMOVED*** Changed Endpoints
- `GET /api/people` → `GET /api/v2/persons`
- `GET /api/schedule/{start}/{end}` → `GET /api/v2/schedules?start_date={start}&end_date={end}`

***REMOVED******REMOVED******REMOVED*** Changed Response Format
The list response format changes from:
{
  "items": [...],
  "total": 100
}

To:
{
  "data": [...],
  "meta": {
    "total": 100,
    "page": 1,
    "per_page": 50
  }
}

***REMOVED******REMOVED******REMOVED*** Removed Fields
- `person.legacy_id` removed
- `assignment.created_by` moved to `assignment.audit.created_by`
```

***REMOVED******REMOVED*** Multiple Version Support

When multiple major versions are available:

***REMOVED******REMOVED******REMOVED*** Parallel Operation

Both versions will operate simultaneously:

```
/api/people          ***REMOVED*** v1 (current)
/api/v2/persons      ***REMOVED*** v2 (new)
```

***REMOVED******REMOVED******REMOVED*** Version Sunset

Old versions will be sunset according to the deprecation policy:

| Version | Status | Sunset Date |
|---------|--------|-------------|
| v1 | Current | TBD |
| v2 | Future | N/A |

***REMOVED******REMOVED*** Client Best Practices

***REMOVED******REMOVED******REMOVED*** 1. Check API Version

Always verify the API version on startup:

```python
def check_api_version():
    response = requests.get(f"{BASE_URL}/")
    data = response.json()
    version = data.get("version", "unknown")

    if not version.startswith("1."):
        logger.warning(f"API version {version} may not be compatible")
```

***REMOVED******REMOVED******REMOVED*** 2. Handle Deprecation Warnings

Monitor for deprecation headers:

```python
def handle_deprecation(response):
    if response.headers.get("X-API-Deprecation") == "true":
        date = response.headers.get("X-API-Deprecation-Date")
        info = response.headers.get("X-API-Deprecation-Info")
        logger.warning(f"Deprecated endpoint! Sunset: {date}. {info}")
```

***REMOVED******REMOVED******REMOVED*** 3. Use Stable Field Names

Only depend on documented fields:

```python
***REMOVED*** Good - uses documented field
person_name = response["name"]

***REMOVED*** Bad - uses undocumented internal field
person_name = response["_internal_name"]
```

***REMOVED******REMOVED******REMOVED*** 4. Handle Unknown Fields

Be tolerant of new fields in responses:

```python
***REMOVED*** Good - ignores unknown fields
person = Person(**{k: v for k, v in data.items() if k in Person.fields})

***REMOVED*** Bad - fails on unknown fields
person = Person(**data)  ***REMOVED*** Raises error on new fields
```

***REMOVED******REMOVED*** Changelog

***REMOVED******REMOVED******REMOVED*** Version 1.0.0 (December 2024)

**Initial Release**

Features:
- Authentication (JWT)
- People management (residents, faculty)
- Block management (AM/PM slots)
- Rotation templates
- Assignments with ACGME validation
- Absence tracking
- Schedule generation (multiple algorithms)
- Export functionality (CSV, JSON, XLSX)
- Settings management

---

*For questions about API versioning, contact the development team.*
