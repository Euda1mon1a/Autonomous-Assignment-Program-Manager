# API Reference

Complete REST API documentation for Residency Scheduler.

---

## Overview

The Residency Scheduler API is a RESTful JSON API built with FastAPI.

- **Base URL**: `http://localhost:8000/api/v1`
- **Authentication**: JWT Bearer tokens
- **Content-Type**: `application/json`

### Interactive Documentation

| Format | URL |
|--------|-----|
| **Swagger UI** | http://localhost:8000/docs |
| **ReDoc** | http://localhost:8000/redoc |
| **OpenAPI JSON** | http://localhost:8000/openapi.json |

---

## API Sections

<div class="feature-grid" markdown>

<div class="feature-card" markdown>
### :material-key: [Authentication](authentication.md)
Login, registration, and token management.
</div>

<div class="feature-card" markdown>
### :material-calendar: [Schedule](schedule.md)
Schedule generation and management endpoints.
</div>

<div class="feature-card" markdown>
### :material-account-group: [People](people.md)
User and personnel management.
</div>

<div class="feature-card" markdown>
### :material-calendar-remove: [Absences](absences.md)
Absence recording and retrieval.
</div>

<div class="feature-card" markdown>
### :material-swap-horizontal: [Swaps](swaps.md)
Swap marketplace operations.
</div>

<div class="feature-card" markdown>
### :material-chart-line: [Analytics](analytics.md)
Metrics and reporting endpoints.
</div>

<div class="feature-card" markdown>
### :material-gamepad-variant: [Game Theory](game-theory.md)
Configuration testing via Axelrod tournaments.
</div>

</div>

---

## Quick Reference

### Authentication

```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'

# Response
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}

# Authenticated request
curl http://localhost:8000/api/v1/people \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

### Common Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| <span class="endpoint-badge post">POST</span> | `/auth/login` | Authenticate user |
| <span class="endpoint-badge get">GET</span> | `/people` | List all people |
| <span class="endpoint-badge get">GET</span> | `/schedule/{date}` | Get schedule for date |
| <span class="endpoint-badge post">POST</span> | `/schedule/generate` | Generate new schedule |
| <span class="endpoint-badge get">GET</span> | `/absences` | List absences |
| <span class="endpoint-badge post">POST</span> | `/swaps` | Create swap request |

### Response Codes

| Code | Description |
|------|-------------|
| `200` | Success |
| `201` | Created |
| `400` | Bad Request |
| `401` | Unauthorized |
| `403` | Forbidden |
| `404` | Not Found |
| `422` | Validation Error |
| `429` | Too Many Requests |
| `500` | Server Error |

---

## Rate Limiting

Authentication endpoints are rate limited:

| Endpoint | Limit |
|----------|-------|
| `/auth/login` | 5 requests/minute |
| `/auth/register` | 3 requests/minute |

Rate limit headers:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Time until limit resets

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message",
  "code": "ERROR_CODE"
}
```

Validation errors include field details:

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "Invalid email format",
      "type": "value_error"
    }
  ]
}
```
