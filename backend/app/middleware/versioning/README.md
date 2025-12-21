# API Versioning Middleware

Comprehensive API versioning system with deprecation support, version negotiation, and backward compatibility.

## Features

### 1. Multiple Version Detection Methods

The middleware detects API versions from three sources (in priority order):

1. **URL Path** (highest priority): `/api/v2/users`
2. **Accept-Version Header**: `Accept-Version: v2`
3. **Query Parameter**: `?version=2` or `?api_version=v2`

### 2. Deprecation Management

- RFC 8594-compliant deprecation warnings
- Sunset headers with automatic date enforcement
- Version lifecycle tracking (development → beta → stable → deprecated → sunset → retired)
- Automatic blocking of retired endpoints
- Migration guidance with replacement links

### 3. Version-Aware Routing

- Custom `VersionedAPIRouter` for version-specific endpoints
- Min/max version enforcement per route
- Version dispatch for different implementations

### 4. Response Transformation

- Automatic transformation between API versions
- Date format conversion (V1: simple dates, V2+: ISO 8601)
- Pagination format changes (V1: flat list, V2+: metadata wrapped)
- Field renaming support

## Quick Start

### Basic Setup

```python
from fastapi import FastAPI
from app.middleware.versioning import VersioningMiddleware

app = FastAPI()
app.add_middleware(VersioningMiddleware)
```

### Version-Specific Endpoints

```python
from app.middleware.versioning import VersionedAPIRouter, APIVersion

# Create version-specific routers
v1_router = VersionedAPIRouter(prefix="/api/v1", min_version=APIVersion.V1)
v2_router = VersionedAPIRouter(prefix="/api/v2", min_version=APIVersion.V2)

@v1_router.get("/users")
async def get_users_v1():
    # V1 implementation - flat list
    return [{"id": 1, "name": "User 1"}]

@v2_router.get("/users")
async def get_users_v2():
    # V2 implementation - wrapped with metadata
    return {
        "data": [{"id": 1, "name": "User 1"}],
        "metadata": {"total": 1, "page": 1}
    }

app.include_router(v1_router)
app.include_router(v2_router)
```

### Accessing Current Version

```python
from app.middleware.versioning import get_api_version, APIVersion

@app.get("/endpoint")
async def my_endpoint():
    version = get_api_version()

    if version >= APIVersion.V2:
        # Use V2 features
        return {"enhanced": True}
    else:
        # V1 compatibility
        return {"basic": True}
```

### Registering Deprecations

```python
from app.middleware.versioning import get_deprecation_manager, VersionStatus
from datetime import datetime

dep_mgr = get_deprecation_manager()

dep_mgr.register_deprecation(
    endpoint="/api/v1/legacy-endpoint",
    version="v1",
    status=VersionStatus.DEPRECATED,
    sunset_date=datetime(2025, 12, 31),
    replacement="/api/v2/new-endpoint",
    message="This endpoint will be removed. Please migrate to v2.",
    documentation_url="https://docs.example.com/migration-guide"
)
```

### Response Transformation

```python
from app.middleware.versioning import transform_response, APIVersion

@app.get("/data")
async def get_data():
    data = {
        "created_at": datetime.now(),
        "items": [1, 2, 3]
    }

    # Auto-transform based on current API version
    return transform_response(data)
```

## API Versions

### V1 (Stable)
- Initial API release
- Simple date formats (YYYY-MM-DD)
- Flat list responses
- Basic CRUD operations

### V2 (Stable)
- Enhanced with metadata
- ISO 8601 date formats
- Paginated responses with metadata
- Batch operations
- Real-time WebSocket support

### V3 (Beta)
- AI-powered features
- Advanced analytics
- Multi-tenant support
- OAuth2 authentication

## Version Detection Priority

1. URL path: `/api/v2/endpoint` → v2
2. Header: `Accept-Version: v2` → v2
3. Query: `?version=2` → v2
4. Default: v1

## Deprecation Headers

Deprecated endpoints automatically include:

- `Deprecation: true` (RFC 8594)
- `Sunset: <date>` (RFC 8594)
- `Warning: <message>` (RFC 7234)
- `Link: <replacement>; rel="alternate"`
- `X-API-Deprecation: <metadata>`
- `X-Days-Until-Sunset: <days>`

## Response Headers

All responses include:

- `X-API-Version: v2` - Version used for this request
- `X-API-Latest-Version: v2` - Latest stable version

## Testing

Run the test suite:

```bash
cd backend
pytest tests/test_versioning_middleware.py -v
```

## Version Changelog

Access the complete changelog:

```python
from app.middleware.versioning.middleware import version_changelog

changelog = version_changelog()
# Returns detailed changelog for all versions
```

## Best Practices

1. **Always specify version in URLs** for clarity
2. **Use header versioning** for programmatic clients
3. **Check deprecation warnings** in development
4. **Plan migrations** before sunset dates
5. **Test with multiple versions** during development
6. **Document breaking changes** in changelog

## Migration Guide

When migrating from V1 to V2:

1. Update date parsing to handle ISO 8601 format
2. Handle paginated response format (data + metadata)
3. Update field names (check field mappings)
4. Test with `Accept-Version: v2` header first
5. Update API calls to use `/api/v2/` prefix

## Advanced Usage

### Version Dispatch

Handle different versions with different implementations:

```python
from app.middleware.versioning.router import version_dispatch

@app.get("/endpoint")
async def endpoint(request: Request):
    return await version_dispatch({
        APIVersion.V1: handle_v1,
        APIVersion.V2: handle_v2,
        APIVersion.V3: handle_v3,
    })(request)
```

### Custom Transformers

Create custom response transformers:

```python
from app.middleware.versioning import ResponseTransformer, register_transformer

@register_transformer("custom")
class CustomTransformer(ResponseTransformer):
    def transform(self, data, target_version):
        # Custom transformation logic
        return transformed_data

    def supports_version(self, version):
        return version >= APIVersion.V2
```

### Backward Compatible Fields

```python
from app.middleware.versioning.transformers import backward_compatible_field

response = {
    "id": user.id,
    **backward_compatible_field(
        old_name="userName",  # V1
        new_name="username",   # V2+
        value=user.username,
        min_version=APIVersion.V2
    )
}
```

## Architecture

```
Request
  ↓
VersioningMiddleware (detects version)
  ↓
Request State (version stored)
  ↓
VersionedRoute (enforces min/max version)
  ↓
Endpoint Handler (uses get_api_version())
  ↓
Response
  ↓
ResponseTransformer (converts format)
  ↓
DeprecationManager (adds headers)
  ↓
Client
```

## Related Files

- `middleware.py` - Core versioning middleware
- `router.py` - Version-aware routing
- `deprecation.py` - Deprecation management
- `transformers.py` - Response transformation
- `__init__.py` - Public API exports

## Support

For questions or issues, refer to:
- Project documentation: `/docs/api/versioning.md`
- Test examples: `/tests/test_versioning_middleware.py`
- CLAUDE.md: Project guidelines
