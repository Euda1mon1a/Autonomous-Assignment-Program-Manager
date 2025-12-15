# Opus Round 6 - 5 Parallel Instances (Production Ready)

Project is at 98%! This final round focuses on production deployment, documentation, and edge cases.

Run these 5 prompts in separate terminals simultaneously.

---

## Terminal 1: Opus-Docker-Deployment

```
You are Opus-Docker-Deployment. Your task is to add Docker containerization for production deployment.

STRICT FILE OWNERSHIP - Only modify files in these paths:
- docker-compose.yml (CREATE)
- docker-compose.dev.yml (CREATE)
- backend/Dockerfile (CREATE)
- frontend/Dockerfile (CREATE)
- .dockerignore (CREATE)
- .env.example (CREATE)

IMPLEMENTATION REQUIREMENTS:

1. docker-compose.yml (production):
   ```yaml
   version: '3.8'
   services:
     backend:
       build: ./backend
       ports:
         - "8000:8000"
       environment:
         - DATABASE_URL=postgresql://...
       depends_on:
         - db
     frontend:
       build: ./frontend
       ports:
         - "3000:3000"
       depends_on:
         - backend
     db:
       image: postgres:15-alpine
       volumes:
         - postgres_data:/var/lib/postgresql/data
       environment:
         - POSTGRES_USER=scheduler
         - POSTGRES_PASSWORD=${DB_PASSWORD}
         - POSTGRES_DB=residency_scheduler
   volumes:
     postgres_data:
   ```

2. backend/Dockerfile:
   - Python 3.11 slim base
   - Install requirements.txt
   - Run with uvicorn
   - Health check endpoint

3. frontend/Dockerfile:
   - Node 20 alpine base
   - Multi-stage build (builder + production)
   - Next.js standalone output
   - Minimal production image

4. docker-compose.dev.yml:
   - Mount source as volumes for hot reload
   - Development environment variables

5. .env.example:
   - All required environment variables with placeholders
   - Comments explaining each variable

6. .dockerignore:
   - node_modules, __pycache__, .git, etc.

DO NOT modify any source code files.
Commit with prefix: [Opus-Docker]
```

---

## Terminal 2: Opus-API-Documentation

```
You are Opus-API-Documentation. Your task is to add comprehensive API documentation.

STRICT FILE OWNERSHIP - Only modify files in these paths:
- docs/API.md (CREATE)
- docs/FRONTEND.md (CREATE)
- backend/app/main.py (UPDATE - add OpenAPI metadata)

IMPLEMENTATION REQUIREMENTS:

1. docs/API.md - Complete API reference:
   ## Authentication
   - POST /auth/login
   - POST /auth/register
   - GET /auth/me
   - POST /auth/logout

   ## People
   - GET /people
   - POST /people
   - GET /people/{id}
   - PUT /people/{id}
   - DELETE /people/{id}

   ## Rotation Templates
   - GET /rotation-templates
   - POST /rotation-templates
   - PUT /rotation-templates/{id}
   - DELETE /rotation-templates/{id}

   ## Absences
   - GET /absences
   - POST /absences
   - PUT /absences/{id}
   - DELETE /absences/{id}

   ## Schedule
   - GET /schedule
   - POST /schedule/generate
   - GET /schedule/compliance

   For each endpoint include:
   - Method and path
   - Description
   - Request body (if applicable)
   - Response schema
   - Example curl command

2. docs/FRONTEND.md - Frontend architecture:
   - Component structure
   - State management (React Query)
   - Authentication flow
   - Routing
   - Styling conventions

3. Update backend/app/main.py:
   ```python
   app = FastAPI(
       title="Residency Scheduler API",
       description="API for medical residency scheduling with ACGME compliance",
       version="1.0.0",
       docs_url="/docs",
       redoc_url="/redoc",
   )
   ```

DO NOT modify any other source files.
Commit with prefix: [Opus-APIDocs]
```

---

## Terminal 3: Opus-Error-Messages

```
You are Opus-Error-Messages. Your task is to improve error messages and user feedback throughout the app.

STRICT FILE OWNERSHIP - Only modify files in these paths:
- frontend/src/lib/errors.ts (CREATE)
- frontend/src/components/ErrorAlert.tsx (UPDATE)
- frontend/src/components/Toast.tsx (CREATE)
- frontend/src/contexts/ToastContext.tsx (CREATE)
- frontend/src/app/providers.tsx (UPDATE - add ToastProvider)

IMPLEMENTATION REQUIREMENTS:

1. frontend/src/lib/errors.ts:
   ```typescript
   export function getErrorMessage(error: unknown): string {
     // Handle axios errors
     // Handle network errors
     // Handle validation errors
     // Return user-friendly messages
   }

   export const ERROR_MESSAGES = {
     NETWORK_ERROR: 'Unable to connect to server. Please check your connection.',
     UNAUTHORIZED: 'Your session has expired. Please log in again.',
     FORBIDDEN: 'You do not have permission to perform this action.',
     NOT_FOUND: 'The requested resource was not found.',
     VALIDATION_ERROR: 'Please check your input and try again.',
     SERVER_ERROR: 'Something went wrong. Please try again later.',
   }
   ```

2. frontend/src/components/Toast.tsx:
   - Toast notification component
   - Types: success, error, warning, info
   - Auto-dismiss after 5 seconds
   - Manual dismiss button
   - Slide-in animation from top-right

3. frontend/src/contexts/ToastContext.tsx:
   ```typescript
   interface ToastContextType {
     showToast: (message: string, type: 'success' | 'error' | 'warning' | 'info') => void
     showError: (error: unknown) => void
     showSuccess: (message: string) => void
   }
   ```

4. Update ErrorAlert.tsx:
   - Use getErrorMessage for consistent messaging
   - Add toast notification option

5. Update providers.tsx:
   - Wrap with ToastProvider
   - Export useToast hook

Usage example:
```typescript
const { showSuccess, showError } = useToast()
try {
  await createPerson(data)
  showSuccess('Person created successfully')
} catch (error) {
  showError(error)
}
```

DO NOT modify page components directly.
Commit with prefix: [Opus-Errors]
```

---

## Terminal 4: Opus-Data-Export

```
You are Opus-Data-Export. Your task is to add data export functionality.

STRICT FILE OWNERSHIP - Only modify files in these paths:
- frontend/src/lib/export.ts (CREATE)
- frontend/src/components/ExportButton.tsx (CREATE)
- frontend/src/app/people/page.tsx (UPDATE - add export button)
- frontend/src/app/absences/page.tsx (UPDATE - add export button)
- backend/app/api/routes/export.py (CREATE)
- backend/app/api/routes/__init__.py (UPDATE - add export router)

IMPLEMENTATION REQUIREMENTS:

1. frontend/src/lib/export.ts:
   ```typescript
   export function exportToCSV(data: any[], filename: string, columns: Column[])
   export function exportToJSON(data: any[], filename: string)
   export function downloadFile(content: string, filename: string, mimeType: string)
   ```

2. frontend/src/components/ExportButton.tsx:
   - Dropdown with CSV/JSON options
   - Download icon
   - Loading state during export
   - Props: data, filename, columns

3. Update people/page.tsx:
   - Add ExportButton next to "Add Person"
   - Export columns: Name, Type, PGY Level, Email

4. Update absences/page.tsx:
   - Add ExportButton next to "Add Absence"
   - Export columns: Person, Type, Start Date, End Date, Notes

5. backend/app/api/routes/export.py:
   - GET /export/people - returns CSV
   - GET /export/absences - returns CSV
   - GET /export/schedule - returns CSV
   - Accept format query param (csv/json)

Example CSV export:
```typescript
const columns = [
  { key: 'name', header: 'Name' },
  { key: 'type', header: 'Type' },
  { key: 'pgy_level', header: 'PGY Level' },
]
<ExportButton data={people} filename="people" columns={columns} />
```

DO NOT modify other components or backend routes.
Commit with prefix: [Opus-Export]
```

---

## Terminal 5: Opus-README-Update

```
You are Opus-README-Update. Your task is to create a comprehensive README and update documentation.

STRICT FILE OWNERSHIP - Only modify files in these paths:
- README.md (UPDATE - complete rewrite)
- CONTRIBUTING.md (CREATE)
- CHANGELOG.md (CREATE)
- docs/SETUP.md (CREATE)

IMPLEMENTATION REQUIREMENTS:

1. README.md - Complete project documentation:
   # Residency Scheduler

   ## Overview
   Medical residency scheduling system with ACGME compliance validation.

   ## Features
   - Schedule generation with constraint satisfaction
   - ACGME compliance monitoring
   - Absence management
   - User authentication
   - Export functionality

   ## Tech Stack
   - Frontend: Next.js 14, React 18, TailwindCSS, React Query
   - Backend: FastAPI, SQLAlchemy, PostgreSQL
   - Auth: JWT with python-jose

   ## Quick Start
   ```bash
   # Clone repository
   # Install dependencies
   # Set up environment
   # Run with Docker
   ```

   ## Screenshots
   (placeholders for dashboard, schedule, people pages)

   ## Documentation
   - [API Reference](docs/API.md)
   - [Frontend Guide](docs/FRONTEND.md)
   - [Setup Guide](docs/SETUP.md)

   ## License
   MIT

2. CONTRIBUTING.md:
   - How to contribute
   - Development setup
   - Code style guidelines
   - Pull request process
   - Issue reporting

3. CHANGELOG.md:
   - Version 1.0.0 (current)
   - List all features implemented
   - Group by: Added, Changed, Fixed

4. docs/SETUP.md:
   - Detailed installation instructions
   - Environment configuration
   - Database setup
   - Running tests
   - Troubleshooting common issues

Make the README professional and suitable for open-source.
Commit with prefix: [Opus-README]
```

---

## Merge Order

After all 5 complete:
1. Opus-README-Update (documentation only)
2. Opus-API-Documentation (documentation only)
3. Opus-Error-Messages (foundational)
4. Opus-Data-Export (new feature)
5. Opus-Docker-Deployment (deployment config)

## Conflict Prevention

Each Opus has strict file ownership:
- `providers.tsx` - Only Opus-Error-Messages modifies
- `__init__.py` (routes) - Only Opus-Data-Export modifies
- `people/page.tsx` - Only Opus-Data-Export modifies
- `absences/page.tsx` - Only Opus-Data-Export modifies

No expected conflicts - strict separation.

---

## Expected Deliverables

| Opus Instance | New Files | Updated Files |
|--------------|-----------|---------------|
| Docker-Deployment | 6 files | 0 files |
| API-Documentation | 2 files | 1 file |
| Error-Messages | 3 files | 2 files |
| Data-Export | 3 files | 3 files |
| README-Update | 4 files | 0 files |

**Total: 18 new files, 6 updated files**

After this round: **100% production ready!**
