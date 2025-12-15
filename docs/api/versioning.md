# API Versioning

This document describes the versioning strategy for the Residency Scheduler API.

## Current Version

**API Version:** 1.0.0

**Release Date:** December 2024

## Versioning Strategy

The API uses **URL path versioning** with semantic versioning principles for the version number.

### URL Structure

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

### Version Placement

For the initial v1 API, the version is implicit in the `/api` prefix. Future major versions will include an explicit version number.

| Version | Base Path | Status |
|---------|-----------|--------|
| v1 | `/api` | Current |
| v2 | `/api/v2` | Future |
| v3 | `/api/v3` | Future |

## Semantic Versioning

The API follows [Semantic Versioning 2.0.0](https://semver.org/):

```
MAJOR.MINOR.PATCH
```

| Component | Description | Example Change |
|-----------|-------------|----------------|
| MAJOR | Breaking changes | Removing endpoints, changing response format |
| MINOR | Backward-compatible additions | New endpoints, new optional fields |
| PATCH | Backward-compatible fixes | Bug fixes, documentation updates |

### Version Examples

| Version | Changes |
|---------|---------|
| 1.0.0 | Initial release |
| 1.1.0 | Added export endpoints |
| 1.1.1 | Fixed validation bug |
| 1.2.0 | Added batch operations |
| 2.0.0 | Restructured response format (breaking) |

## Breaking Changes

The following changes are considered **breaking** and require a major version bump:

### Endpoint Changes
- Removing an endpoint
- Changing an endpoint's HTTP method
- Changing URL path structure
- Removing required functionality

### Request Changes
- Adding a new required field
- Removing an optional field that clients may use
- Changing field validation rules (stricter)
- Changing field types

### Response Changes
- Removing a field from responses
- Changing field types
- Changing response structure
- Changing error response format

### Authentication Changes
- Changing authentication mechanism
- Changing token format
- Removing authentication methods

## Non-Breaking Changes

The following changes are **non-breaking** and can be made in minor versions:

### Additions
- New endpoints
- New optional request fields
- New response fields
- New query parameters
- New HTTP methods on existing resources

### Deprecations
- Marking endpoints as deprecated (with warning)
- Marking fields as deprecated (with warning)

### Other
- Performance improvements
- Bug fixes (that don't change behavior)
- Documentation updates

## Deprecation Policy

### Deprecation Timeline

1. **Announcement**: Feature marked deprecated with warning
2. **Warning Period**: 6 months of continued support
3. **Sunset**: Feature removed in next major version

### Deprecation Notices

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

### Example: Endpoint Deprecation

```bash
# Deprecated endpoint
curl http://localhost:8000/api/legacy-endpoint

# Response includes deprecation headers
# X-API-Deprecation: true
# X-API-Deprecation-Date: 2024-06-01
# X-API-Deprecation-Info: Use /api/v2/new-endpoint instead

# Response body remains functional during deprecation period
```

## Version Discovery

### Health Endpoint

The root endpoint returns the current API version:

```bash
curl http://localhost:8000/

# Response:
{
  "name": "Residency Scheduler API",
  "version": "1.0.0",
  "status": "healthy"
}
```

### OpenAPI Specification

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

## Compatibility Headers

### Request Version Header

Clients can request a specific API version behavior using headers:

```bash
curl http://localhost:8000/api/people \
  -H "X-API-Version: 1.0"
```

### Response Version Header

Responses include the API version used:

```http
HTTP/1.1 200 OK
X-API-Version: 1.0.0
```

## Migration Guides

### Migrating to v2 (Future)

When v2 is released, migration guides will be provided:

```markdown
## v1 to v2 Migration Guide

### Changed Endpoints
- `GET /api/people` → `GET /api/v2/persons`
- `GET /api/schedule/{start}/{end}` → `GET /api/v2/schedules?start_date={start}&end_date={end}`

### Changed Response Format
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

### Removed Fields
- `person.legacy_id` removed
- `assignment.created_by` moved to `assignment.audit.created_by`
```

## Multiple Version Support

When multiple major versions are available:

### Parallel Operation

Both versions will operate simultaneously:

```
/api/people          # v1 (current)
/api/v2/persons      # v2 (new)
```

### Version Sunset

Old versions will be sunset according to the deprecation policy:

| Version | Status | Sunset Date |
|---------|--------|-------------|
| v1 | Current | TBD |
| v2 | Future | N/A |

## Client Best Practices

### 1. Check API Version

Always verify the API version on startup:

```python
def check_api_version():
    response = requests.get(f"{BASE_URL}/")
    data = response.json()
    version = data.get("version", "unknown")

    if not version.startswith("1."):
        logger.warning(f"API version {version} may not be compatible")
```

### 2. Handle Deprecation Warnings

Monitor for deprecation headers:

```python
def handle_deprecation(response):
    if response.headers.get("X-API-Deprecation") == "true":
        date = response.headers.get("X-API-Deprecation-Date")
        info = response.headers.get("X-API-Deprecation-Info")
        logger.warning(f"Deprecated endpoint! Sunset: {date}. {info}")
```

### 3. Use Stable Field Names

Only depend on documented fields:

```python
# Good - uses documented field
person_name = response["name"]

# Bad - uses undocumented internal field
person_name = response["_internal_name"]
```

### 4. Handle Unknown Fields

Be tolerant of new fields in responses:

```python
# Good - ignores unknown fields
person = Person(**{k: v for k, v in data.items() if k in Person.fields})

# Bad - fails on unknown fields
person = Person(**data)  # Raises error on new fields
```

## Changelog

### Version 1.0.0 (December 2024)

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
