***REMOVED*** API Documentation Ownership Matrix

This document defines the ownership and maintenance responsibilities for the API documentation files.

***REMOVED******REMOVED*** File Ownership

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

***REMOVED******REMOVED*** Directory Structure

```
docs/api/
├── README.md                    ***REMOVED*** Main index and quick start guide
├── authentication.md            ***REMOVED*** Authentication and authorization
├── errors.md                    ***REMOVED*** Error handling reference
├── rate-limiting.md             ***REMOVED*** Rate limiting documentation
├── versioning.md                ***REMOVED*** API versioning strategy
├── schemas.md                   ***REMOVED*** Data schemas and types
├── OWNERSHIP.md                 ***REMOVED*** This file
└── endpoints/
    ├── auth.md                  ***REMOVED*** /api/auth endpoints
    ├── people.md                ***REMOVED*** /api/people endpoints
    ├── blocks.md                ***REMOVED*** /api/blocks endpoints
    ├── rotation-templates.md    ***REMOVED*** /api/rotation-templates endpoints
    ├── assignments.md           ***REMOVED*** /api/assignments endpoints
    ├── absences.md              ***REMOVED*** /api/absences endpoints
    ├── schedule.md              ***REMOVED*** /api/schedule endpoints
    ├── settings.md              ***REMOVED*** /api/settings endpoints
    └── export.md                ***REMOVED*** /api/export endpoints
```

***REMOVED******REMOVED*** Maintenance Responsibilities

***REMOVED******REMOVED******REMOVED*** Primary Responsibilities

| Area | Responsible Team | Backup |
|------|------------------|--------|
| Endpoint Documentation | @api-docs-team | @backend-team |
| Schema Definitions | @api-docs-team | @backend-team |
| Authentication Docs | @api-docs-team | @security-team |
| Error Handling Docs | @api-docs-team | @backend-team |

***REMOVED******REMOVED******REMOVED*** Update Triggers

Documentation must be updated when:

1. **New Endpoints Added**: Add new endpoint documentation file or section
2. **Schema Changes**: Update schemas.md and relevant endpoint docs
3. **Error Code Changes**: Update errors.md
4. **Authentication Changes**: Update authentication.md
5. **Rate Limit Changes**: Update rate-limiting.md
6. **Breaking Changes**: Update versioning.md with migration guide

***REMOVED******REMOVED*** Review Process

1. All documentation changes require PR review
2. Changes to endpoint docs should be reviewed by backend team
3. Changes to authentication docs should be reviewed by security team
4. Version updates require sign-off from tech lead

***REMOVED******REMOVED*** Contact

For questions or updates to this documentation:

- **API Documentation Team**: @api-docs-team
- **Backend Team**: @backend-team
- **Security Team**: @security-team

***REMOVED******REMOVED*** Change Log

| Date | Change | Author |
|------|--------|--------|
| 2024-12 | Initial API documentation created | Claude |

---

***REMOVED******REMOVED*** Code-to-Documentation Mapping

***REMOVED******REMOVED******REMOVED*** Backend Routes to Documentation

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

***REMOVED******REMOVED******REMOVED*** Schema Files to Documentation

| Backend Schema File | Documentation Section |
|--------------------|----------------------|
| `backend/app/schemas/user.py` | `docs/api/schemas.md***REMOVED***authentication-schemas` |
| `backend/app/schemas/person.py` | `docs/api/schemas.md***REMOVED***person-schemas` |
| `backend/app/schemas/block.py` | `docs/api/schemas.md***REMOVED***block-schemas` |
| `backend/app/schemas/rotation_template.py` | `docs/api/schemas.md***REMOVED***rotation-template-schemas` |
| `backend/app/schemas/assignment.py` | `docs/api/schemas.md***REMOVED***assignment-schemas` |
| `backend/app/schemas/absence.py` | `docs/api/schemas.md***REMOVED***absence-schemas` |
| `backend/app/schemas/schedule.py` | `docs/api/schemas.md***REMOVED***schedule-schemas` |
| `backend/app/schemas/settings.py` | `docs/api/schemas.md***REMOVED***settings-schema` |

---

*This ownership matrix should be updated whenever documentation files are added, removed, or reassigned.*
