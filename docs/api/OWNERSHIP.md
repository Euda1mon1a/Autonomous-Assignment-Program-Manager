# API Documentation Ownership Matrix

This document defines the ownership and maintenance responsibilities for the API documentation files.

## File Ownership

| File Path | Owner | Description | Last Updated |
|-----------|-------|-------------|--------------|
| `docs/api/README.md` | @api-docs-team | API documentation index and quick start | 2024-12 |
| `docs/api/authentication.md` | @api-docs-team | JWT authentication flows and RBAC | 2024-12 |
| `docs/api/errors.md` | @api-docs-team | Error handling and HTTP status codes | 2024-12 |
| `docs/api/rate-limiting.md` | @api-docs-team | Rate limiting policies and headers | 2024-12 |
| `docs/api/versioning.md` | @api-docs-team | API versioning strategy | 2024-12 |
| `docs/api/schemas.md` | @api-docs-team | Request/response schema definitions | 2024-12 |
| `docs/api/endpoints/auth.md` | @api-docs-team | Authentication endpoints | 2024-12 |
| `docs/api/endpoints/people.md` | @api-docs-team | People management endpoints | 2024-12 |
| `docs/api/endpoints/blocks.md` | @api-docs-team | Block management endpoints | 2024-12 |
| `docs/api/endpoints/rotation-templates.md` | @api-docs-team | Rotation template endpoints | 2024-12 |
| `docs/api/endpoints/assignments.md` | @api-docs-team | Assignment management endpoints | 2024-12 |
| `docs/api/endpoints/absences.md` | @api-docs-team | Absence tracking endpoints | 2024-12 |
| `docs/api/endpoints/schedule.md` | @api-docs-team | Schedule generation endpoints | 2024-12 |
| `docs/api/endpoints/settings.md` | @api-docs-team | Settings management endpoints | 2024-12 |
| `docs/api/endpoints/export.md` | @api-docs-team | Data export endpoints | 2024-12 |
| `docs/api/OWNERSHIP.md` | @api-docs-team | This ownership matrix | 2024-12 |

## Directory Structure

```
docs/api/
├── README.md                    # Main index and quick start guide
├── authentication.md            # Authentication and authorization
├── errors.md                    # Error handling reference
├── rate-limiting.md             # Rate limiting documentation
├── versioning.md                # API versioning strategy
├── schemas.md                   # Data schemas and types
├── OWNERSHIP.md                 # This file
└── endpoints/
    ├── auth.md                  # /api/auth endpoints
    ├── people.md                # /api/people endpoints
    ├── blocks.md                # /api/blocks endpoints
    ├── rotation-templates.md    # /api/rotation-templates endpoints
    ├── assignments.md           # /api/assignments endpoints
    ├── absences.md              # /api/absences endpoints
    ├── schedule.md              # /api/schedule endpoints
    ├── settings.md              # /api/settings endpoints
    └── export.md                # /api/export endpoints
```

## Maintenance Responsibilities

### Primary Responsibilities

| Area | Responsible Team | Backup |
|------|------------------|--------|
| Endpoint Documentation | @api-docs-team | @backend-team |
| Schema Definitions | @api-docs-team | @backend-team |
| Authentication Docs | @api-docs-team | @security-team |
| Error Handling Docs | @api-docs-team | @backend-team |

### Update Triggers

Documentation must be updated when:

1. **New Endpoints Added**: Add new endpoint documentation file or section
2. **Schema Changes**: Update schemas.md and relevant endpoint docs
3. **Error Code Changes**: Update errors.md
4. **Authentication Changes**: Update authentication.md
5. **Rate Limit Changes**: Update rate-limiting.md
6. **Breaking Changes**: Update versioning.md with migration guide

## Review Process

1. All documentation changes require PR review
2. Changes to endpoint docs should be reviewed by backend team
3. Changes to authentication docs should be reviewed by security team
4. Version updates require sign-off from tech lead

## Contact

For questions or updates to this documentation:

- **API Documentation Team**: @api-docs-team
- **Backend Team**: @backend-team
- **Security Team**: @security-team

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2024-12 | Initial API documentation created | Claude |

---

## Code-to-Documentation Mapping

### Backend Routes to Documentation

| Backend Route File | Documentation File |
|--------------------|-------------------|
| `backend/app/api/routes/auth.py` | `docs/api/endpoints/auth.md` |
| `backend/app/api/routes/people.py` | `docs/api/endpoints/people.md` |
| `backend/app/api/routes/blocks.py` | `docs/api/endpoints/blocks.md` |
| `backend/app/api/routes/rotation_templates.py` | `docs/api/endpoints/rotation-templates.md` |
| `backend/app/api/routes/assignments.py` | `docs/api/endpoints/assignments.md` |
| `backend/app/api/routes/absences.py` | `docs/api/endpoints/absences.md` |
| `backend/app/api/routes/schedule.py` | `docs/api/endpoints/schedule.md` |
| `backend/app/api/routes/settings.py` | `docs/api/endpoints/settings.md` |
| `backend/app/api/routes/export.py` | `docs/api/endpoints/export.md` |

### Schema Files to Documentation

| Backend Schema File | Documentation Section |
|--------------------|----------------------|
| `backend/app/schemas/user.py` | `docs/api/schemas.md#authentication-schemas` |
| `backend/app/schemas/person.py` | `docs/api/schemas.md#person-schemas` |
| `backend/app/schemas/block.py` | `docs/api/schemas.md#block-schemas` |
| `backend/app/schemas/rotation_template.py` | `docs/api/schemas.md#rotation-template-schemas` |
| `backend/app/schemas/assignment.py` | `docs/api/schemas.md#assignment-schemas` |
| `backend/app/schemas/absence.py` | `docs/api/schemas.md#absence-schemas` |
| `backend/app/schemas/schedule.py` | `docs/api/schemas.md#schedule-schemas` |
| `backend/app/schemas/settings.py` | `docs/api/schemas.md#settings-schema` |

---

*This ownership matrix should be updated whenever documentation files are added, removed, or reassigned.*
