# Residency Scheduler API

## Overview

The Residency Scheduler API is a RESTful API for managing medical residency program schedules with ACGME compliance validation. It provides comprehensive functionality for:

- Managing residents and faculty
- Scheduling rotations and assignments
- Tracking absences (vacations, deployments, TDY, medical, etc.)
- Validating ACGME work hour and supervision requirements
- Generating optimized schedules using constraint-based algorithms
- Handling emergency coverage situations
- Exporting schedules in multiple formats (CSV, JSON, Excel)

## Base URL

The API is served at:

```
http://localhost:8000/api
```

For production deployments, the base URL should be configured via the `DATABASE_URL` and CORS settings in your environment.

## API Versioning

**Current Version:** 1.0.0

The API follows semantic versioning. The version is included in the API metadata and can be retrieved from the root endpoint:

```bash
GET http://localhost:8000/
```

Version information is also available in the OpenAPI documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Quick Start Guide

### 1. Authentication

First, create an account or login to get a JWT token:

```bash
# Login with JSON body
curl -X POST http://localhost:8000/api/auth/login/json \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "your-password"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 2. Make Authenticated Requests

Include the token in the Authorization header for all protected endpoints:

```bash
curl -X GET http://localhost:8000/api/people \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### 3. Create People (Residents and Faculty)

```bash
# Create a resident
curl -X POST http://localhost:8000/api/people \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Dr. Jane Smith",
    "type": "resident",
    "email": "jane.smith@example.com",
    "pgy_level": 2
  }'

# Create a faculty member
curl -X POST http://localhost:8000/api/people \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Dr. John Doe",
    "type": "faculty",
    "email": "john.doe@example.com",
    "specialties": ["cardiology"],
    "performs_procedures": true
  }'
```

### 4. Generate Blocks

Blocks represent time slots (AM/PM) for scheduling:

```bash
curl -X POST "http://localhost:8000/api/blocks/generate?start_date=2024-01-01&end_date=2024-01-28&base_block_number=1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 5. Create Rotation Templates

Define rotation types for assignments:

```bash
curl -X POST http://localhost:8000/api/rotation-templates \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Cardiology Clinic",
    "activity_type": "clinic",
    "abbreviation": "CARD",
    "supervision_required": true,
    "max_supervision_ratio": 4
  }'
```

### 6. Generate a Schedule

Use the scheduling engine to automatically create assignments:

```bash
curl -X POST http://localhost:8000/api/schedule/generate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-01-01",
    "end_date": "2024-01-28",
    "algorithm": "greedy",
    "timeout_seconds": 60
  }'
```

### 7. Validate ACGME Compliance

Check schedule compliance with work hour rules:

```bash
curl -X GET "http://localhost:8000/api/schedule/validate?start_date=2024-01-01&end_date=2024-01-28" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Common Use Cases

### Managing Absences

Track vacations, deployments, and other absences:

```bash
curl -X POST http://localhost:8000/api/absences \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "person_id": "uuid-here",
    "start_date": "2024-02-01",
    "end_date": "2024-02-07",
    "absence_type": "vacation",
    "notes": "Pre-planned vacation"
  }'
```

### Emergency Coverage

Handle last-minute absences with automatic replacement:

```bash
curl -X POST http://localhost:8000/api/schedule/emergency-coverage \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "person_id": "uuid-here",
    "start_date": "2024-02-15",
    "end_date": "2024-02-20",
    "reason": "Family emergency",
    "is_deployment": false
  }'
```

### Export Schedule

Download schedule in various formats:

```bash
# CSV export
curl -X GET "http://localhost:8000/api/export/schedule?format=csv&start_date=2024-01-01&end_date=2024-01-28" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o schedule.csv

# Excel export
curl -X GET "http://localhost:8000/api/export/schedule/xlsx?start_date=2024-01-01&end_date=2024-01-28" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o schedule.xlsx
```

## Response Formats

All API responses use JSON format with consistent structure:

**Success Response:**
```json
{
  "id": "uuid",
  "name": "Resource Name",
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:00:00"
}
```

**List Response:**
```json
{
  "items": [...],
  "total": 10
}
```

**Error Response:**
```json
{
  "detail": "Error message describing what went wrong"
}
```

## HTTP Status Codes

- `200 OK` - Successful GET, PUT, PATCH requests
- `201 Created` - Successful POST request creating a resource
- `204 No Content` - Successful DELETE request
- `207 Multi-Status` - Partial success (e.g., schedule generated with warnings)
- `400 Bad Request` - Invalid input data
- `401 Unauthorized` - Missing or invalid authentication
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - Duplicate resource or optimistic locking failure
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

## Rate Limiting

Currently, no rate limiting is enforced. For production deployments, consider implementing rate limiting based on your infrastructure requirements.

## Further Documentation

- [Endpoints Reference](./endpoints.md) - Detailed endpoint documentation
- [Authentication Guide](./authentication.md) - Authentication and authorization
- [Schemas Reference](./schemas.md) - Request/response schemas and TypeScript types

## OpenAPI Documentation

Interactive API documentation is available at:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Support and Issues

For bug reports and feature requests, please use the project's issue tracker.
