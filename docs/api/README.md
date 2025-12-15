# Residency Scheduler API Documentation

Comprehensive REST API documentation for the Residency Scheduler backend service.

## Overview

The Residency Scheduler API is a RESTful service built with FastAPI that manages medical residency scheduling with ACGME compliance. It provides endpoints for managing people (residents and faculty), schedule blocks, rotation templates, assignments, absences, and automated schedule generation.

**Base URL:** `http://localhost:8000/api`

**API Version:** 1.0.0

**OpenAPI Spec:** Available at `/docs` (Swagger UI) and `/redoc` (ReDoc)

## Quick Start

### 1. Health Check

```bash
curl http://localhost:8000/health
```

### 2. Register a User

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@hospital.org",
    "password": "SecurePassword123!"
  }'
```

### 3. Login and Get Token

```bash
curl -X POST http://localhost:8000/api/auth/login/json \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "SecurePassword123!"
  }'
```

### 4. Use the Token

```bash
curl http://localhost:8000/api/people \
  -H "Authorization: Bearer <your_jwt_token>"
```

## Documentation Index

| Document | Description |
|----------|-------------|
| [Authentication](./authentication.md) | JWT authentication flows, token management, and role-based access |
| [Error Handling](./errors.md) | HTTP status codes, error formats, and common error scenarios |
| [Rate Limiting](./rate-limiting.md) | Request limits, headers, and throttling behavior |
| [API Versioning](./versioning.md) | Version strategy, compatibility, and migration guides |
| [Schemas](./schemas.md) | Request/response schemas and data types |

### Endpoint Documentation

| Resource | Base Path | Description |
|----------|-----------|-------------|
| [Authentication](./endpoints/auth.md) | `/api/auth` | User registration, login, logout |
| [People](./endpoints/people.md) | `/api/people` | Manage residents and faculty |
| [Blocks](./endpoints/blocks.md) | `/api/blocks` | Schedule time blocks (AM/PM slots) |
| [Rotation Templates](./endpoints/rotation-templates.md) | `/api/rotation-templates` | Clinic and activity definitions |
| [Assignments](./endpoints/assignments.md) | `/api/assignments` | Person-to-block assignments |
| [Absences](./endpoints/absences.md) | `/api/absences` | Vacation, deployment, TDY tracking |
| [Schedule](./endpoints/schedule.md) | `/api/schedule` | Schedule generation and validation |
| [Settings](./endpoints/settings.md) | `/api/settings` | System configuration |
| [Export](./endpoints/export.md) | `/api/export` | Data export (CSV, JSON, XLSX) |

## API Features

### ACGME Compliance

The API enforces ACGME (Accreditation Council for Graduate Medical Education) requirements:

- **80-hour rule**: Maximum 80 hours/week averaged over 4 weeks
- **1-in-7 rule**: Minimum one day off per seven consecutive days
- **Supervision ratios**: PGY-1 (1:2), PGY-2/3 (1:4)
- **Consecutive duty limits**: Maximum consecutive working days

### Scheduling Algorithms

Multiple scheduling algorithms are available:

| Algorithm | Description | Use Case |
|-----------|-------------|----------|
| `greedy` | Fast heuristic assignment | Quick schedule generation |
| `cp_sat` | OR-Tools constraint programming | Optimal schedules |
| `pulp` | PuLP linear programming | Alternative optimizer |
| `hybrid` | Combined approach | Balanced performance |

### Data Export

Export schedule data in multiple formats:

- **CSV**: Comma-separated values for spreadsheet import
- **JSON**: Structured data for programmatic access
- **XLSX**: Excel workbook with formatting (legacy support)

## Common Headers

### Request Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Content-Type` | Yes (POST/PUT) | `application/json` for JSON bodies |
| `Authorization` | Conditional | `Bearer <token>` for protected endpoints |
| `Accept` | No | Response format preference |

### Response Headers

| Header | Description |
|--------|-------------|
| `Content-Type` | Response format (`application/json`) |
| `X-RateLimit-Limit` | Maximum requests allowed |
| `X-RateLimit-Remaining` | Remaining requests in window |
| `X-RateLimit-Reset` | Unix timestamp when limit resets |

## Response Format

### Success Response

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Example Resource",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### List Response

```json
{
  "items": [...],
  "total": 100
}
```

### Error Response

```json
{
  "detail": "Error message describing what went wrong"
}
```

## Data Types

| Type | Format | Example |
|------|--------|---------|
| UUID | UUID v4 | `550e8400-e29b-41d4-a716-446655440000` |
| Date | ISO 8601 | `2024-01-15` |
| DateTime | ISO 8601 with TZ | `2024-01-15T10:30:00Z` |
| Boolean | JSON boolean | `true` / `false` |

## SDKs and Client Libraries

While official SDKs are not yet available, the API follows REST conventions and can be accessed using:

- **curl**: Command-line HTTP client
- **Postman**: API testing and development
- **Python requests**: `pip install requests`
- **JavaScript fetch**: Native browser API

## Support

For API issues or questions:

1. Check the [Error Handling](./errors.md) documentation
2. Review the OpenAPI spec at `/docs`
3. Contact the development team

---

*Last Updated: December 2024*
