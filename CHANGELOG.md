# Changelog

All notable changes to the Residency Scheduler project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-01-15

### Added

#### Core Scheduling System
- **Scheduling Engine**: Greedy algorithm with constraint-based assignment for optimal schedule generation
- **Block Management**: Automatic generation of 730 scheduling blocks per academic year (365 days × AM/PM)
- **Rotation Templates**: Reusable activity patterns with configurable constraints
  - Activity types: clinic, inpatient, procedure, conference
  - Capacity limits per activity
  - Specialty and procedure requirements
  - Supervision requirements
- **Assignment System**: Full CRUD operations for schedule assignments
  - Role types: primary, supervising, backup
  - Activity overrides
  - Audit trail with timestamps

#### ACGME Compliance
- **80-Hour Rule Validator**: Enforces maximum 80 hours/week averaged over rolling 4-week periods
- **1-in-7 Rule Validator**: Ensures minimum one 24-hour period off every 7 days
- **Supervision Ratio Validation**:
  - PGY-1: 1 faculty per 2 residents
  - PGY-2/3: 1 faculty per 4 residents
- **Violation Tracking**: Severity-based alerts (Critical, High, Medium, Low)
- **Coverage Rate Calculations**: Percentage of blocks with valid assignments

#### User Management
- **Authentication System**: JWT-based authentication with bcrypt password hashing
- **Role-Based Access Control**:
  - Admin: Full system access
  - Coordinator: Manage schedules and people
  - Faculty: View schedules, manage own availability
- **User Registration**: Self-registration with first user becoming admin
- **Session Management**: 24-hour token expiration with secure token handling

#### People Management
- **Resident Management**: Track PGY level (1-3), email, and assignments
- **Faculty Management**: Track specialties, procedure credentials, and supervision capacity
- **Filtering**: Filter by type (resident/faculty), PGY level, specialty

#### Absence Management
- **Multiple Absence Types**: vacation, deployment, TDY, medical, family_emergency, conference
- **Military-Specific Fields**: Deployment orders, TDY locations
- **Calendar View**: Visual representation of absences
- **List View**: Tabular absence management with filtering
- **Automatic Availability Updates**: Scheduling engine respects absences

#### Emergency Coverage System
- **Emergency Absence Handling**: Automatic replacement finding
- **Priority System**: Critical services protected (inpatient, call, emergency, procedures)
- **Coverage Gap Reporting**: Identify and flag unresolved gaps
- **Manual Review Flagging**: Flag complex situations for coordinator review

#### Dashboard
- **Schedule Summary**: Overview of current period's schedule status
- **Compliance Alerts**: Real-time ACGME violation notifications
- **Upcoming Absences Widget**: Preview of scheduled absences
- **Quick Actions Panel**: Common tasks accessible from dashboard

#### API
- **RESTful API**: Complete REST API with FastAPI
- **OpenAPI Documentation**: Auto-generated Swagger UI and ReDoc
- **40+ Endpoints**: Comprehensive coverage of all features
- **Request Validation**: Pydantic schemas for all requests/responses

#### Frontend
- **Next.js 14 Application**: Modern React framework with App Router
- **Responsive Design**: Mobile-friendly interface with TailwindCSS
- **9 Main Pages**: Dashboard, Login, People, Templates, Absences, Compliance, Settings
- **33 Reusable Components**: Modular UI component library
- **React Query Integration**: Efficient data fetching and caching

#### Database
- **PostgreSQL 15**: Production-grade relational database
- **SQLAlchemy 2.0 ORM**: Modern async-capable ORM
- **Alembic Migrations**: Version-controlled database schema
- **8 Core Models**: Person, User, Block, Assignment, RotationTemplate, Absence, CallAssignment, ScheduleRun

#### DevOps
- **Docker Support**: Multi-container setup with Docker Compose
- **Production Dockerfile**: Optimized multi-stage builds
- **Development Configuration**: Hot-reload enabled development setup
- **Environment Configuration**: Secure environment variable management

#### Testing
- **Backend Tests**: pytest with async support
- **Frontend Unit Tests**: Jest with React Testing Library
- **E2E Tests**: Playwright for end-to-end testing
- **API Mocking**: MSW for frontend API mocking
- **70% Coverage Requirement**: Enforced minimum test coverage

#### Documentation
- **API Reference**: Complete endpoint documentation
- **Architecture Guide**: System design and component overview
- **Authentication Documentation**: Security implementation details
- **Scheduling Algorithm Guide**: Algorithm details and optimization strategies
- **Deployment Guide**: Production deployment instructions
- **Testing Guide**: Test setup and execution instructions
- **Error Handling Guide**: Error codes and handling patterns
- **Caching Strategy**: Performance optimization documentation

#### Export Functionality
- **Excel Export**: Generate schedule spreadsheets using openpyxl
- **Abbreviation Support**: Rotation template abbreviations for compact exports

### Security
- **Password Hashing**: bcrypt with secure salt generation
- **JWT Tokens**: Secure token-based authentication
- **CORS Configuration**: Configurable cross-origin resource sharing
- **Input Validation**: Comprehensive request validation with Pydantic
- **SQL Injection Prevention**: SQLAlchemy ORM protections

### Performance
- **Query Optimization**: Efficient database queries with proper indexing
- **React Query Caching**: Frontend data caching to reduce API calls
- **Lazy Loading**: Component-level code splitting
- **Optimized Docker Images**: Multi-stage builds for minimal image size

---

## [Unreleased]

### Added

#### Development Tooling & Documentation (Session 7 - 2025-12-18)
- **Pre-Deployment Validation Script**: `scripts/pre-deploy-validate.sh` with security checks, env validation, debug detection
- **NPM Audit Fix Script**: `scripts/audit-fix.sh` for automated vulnerability remediation
- **TODO Tracker**: `docs/TODO_TRACKER.md` documenting all 13 backend TODOs with implementation guidance
- **Code Complexity Analysis**: `docs/CODE_COMPLEXITY_ANALYSIS.md` with refactoring recommendations
- **Security Scanning Guide**: `docs/SECURITY_SCANNING.md` with OWASP guidelines and tool recommendations
- **Implementation Tracker**: `docs/IMPLEMENTATION_TRACKER.md` for swap system completion tracking
- **CI/CD Recommendations**: `docs/CI_CD_RECOMMENDATIONS.md` with 10 pipeline improvements
- **ESLint v9 Configuration**: `frontend/eslint.config.js` flat config for modern ESLint compatibility
- **TypeScript Type-Check Config**: `frontend/tsconfig.typecheck.json` for source-only type checking (excludes tests)

#### New Frontend Scripts
- `npm run type-check` - Type check source files only
- `npm run type-check:all` - Type check all files including tests
- `npm run lint:fix` - Auto-fix ESLint issues
- `npm run test:ci` - CI-optimized test runner
- `npm run audit` - Run npm security audit
- `npm run audit:fix` - Fix npm vulnerabilities
- `npm run validate` - Run type-check, lint, and tests together

#### Session 9 Parallel Work Setup (2025-12-18)

**Planning & Documentation**
- **SESSION_9_PARALLEL_PRIORITIES.md**: 10 independent workstreams for parallel terminal execution
- **STRATEGIC_DECISIONS.md**: Strategic direction document requiring human input
  - Documents 7 key decisions: target user base, feature priorities, deployment model, integration priorities, licensing, market focus, AI investment
  - Includes decision matrix and recommended default path
- **docs/sessions/**: Session archive directory with README.md for tracking historical parallel development sessions

**Terminal Assignments:**

| Terminal | Focus Area |
|----------|------------|
| T1 | Strategic Direction (human input) |
| T2 | Email Notification Infrastructure |
| T3 | N+1 Query Elimination |
| T4 | Constraints Module Modularization |
| T5 | TypedDict Type Safety |
| T6 | MTF Compliance Type Safety |
| T7 | Hook JSDoc Documentation |
| T8 | Keyboard Navigation |
| T9 | E2E Test Expansion |
| T10 | Documentation Sync |

#### 10 Parallel Improvements (Session 7 - 2025-12-18)

**Backend Testing**
- **Notification Service Tests** (`backend/tests/test_notification_service.py`): 38 test methods covering send, bulk, schedule, mark-as-read, preferences, and integration workflows
- **Health Check Endpoint Tests** (`backend/tests/test_health_routes.py`): 37 test cases for `/health`, `/`, and `/health/resilience` endpoints with error scenarios and performance testing

**Backend Code Quality**
- **Scheduling Module Docstrings**: Google-style docstrings for all public functions/classes in `backend/app/scheduling/` (constraints.py, engine.py, solvers.py, optimizer.py, validator.py, explainability.py) with ACGME context and algorithm explanations
- **Maintenance Module Error Handling**: Custom exception hierarchy (BackupError, RestoreError, SchedulerError) with disk space validation, permission checks, and structured logging in `backend/app/maintenance/`
- **Certification Repository Validation**: Input validation for all methods in `backend/app/repositories/certification.py` with UUID, string, integer, and boolean type checking

**Frontend Improvements**
- **Analytics Accessibility**: WCAG 2.1 compliant ARIA labels, roles, and states for all components in `frontend/src/features/analytics/` (MetricsCard, FairnessTrend, VersionComparison, WhatIfAnalysis, AnalyticsDashboard)
- **TypeScript Enum Types**: Converted string literals to proper enums with JSDoc documentation in `frontend/src/types/` (PersonType, TimeOfDay, AssignmentRole, AbsenceType, ViolationSeverity, SchedulingAlgorithm, ScheduleStatus)
- **Settings Page Tests** (`frontend/src/__tests__/pages/settings.test.tsx`): 53 test cases covering rendering, validation, save/update, error states, and accessibility

**Documentation**
- **ROADMAP Enhancement**: Technical implementation details for all planned features including database schemas, API changes, and migration considerations
- **Prometheus Metrics Documentation** (`docs/operations/metrics.md`): Complete metric catalog with PromQL queries, Grafana dashboard recommendations, and alert thresholds

#### Comprehensive Security Hardening (Session 6 - 2025-12-17)
- **Path Traversal Prevention**: New `file_security.py` module with path validation, backup ID sanitization
- **httpOnly Cookie Authentication**: Migrated JWT from localStorage to secure httpOnly cookies
- **File Upload Validation**: Size limits, extension checks, magic byte verification for Excel uploads
- **Password Strength Enforcement**: 12+ chars, 3/4 complexity types, common password blacklist
- **Admin Authorization**: Added `require_admin()` to 13 endpoints across 5 route files
- **Global Exception Handler**: Prevents error message leakage, logs full errors server-side
- **Redis Authentication**: Password-protected Redis with `--requirepass` in all configurations
- **API Documentation Protection**: `/docs`, `/redoc` disabled in production, IP-restricted metrics
- **XSS Fixes**: HTML escaping in PDF exports, URL validation for calendar sync

### Security
- **Secret Validation**: Startup validation rejects insecure/default SECRET_KEY and WEBHOOK_SECRET
- **Default Credentials Removed**: N8N "resilience", Grafana "admin" defaults eliminated
- **CORS Hardening**: Explicit method/header whitelists recommended
- **Monitoring Protection**: Prometheus admin API disabled, metrics restricted to internal IPs
- **Custom Exceptions**: Safe exception classes prevent internal details exposure

#### Security Hardening (Session 5 - 2025-12-17)
- **Authentication on People API**: All 7 endpoints now require authentication (PII protection)
- **Authentication on Settings API**: GET requires auth, POST/PATCH/DELETE require admin role
- **Authentication on Role Views API**: All 6 endpoints secured + fixed TODO for auth integration
- **Rate Limiting System**: Redis-based sliding window rate limiter for brute force protection
  - Login endpoints: 5 requests per minute
  - Registration endpoint: 3 requests per minute
  - HTTP 429 responses with standard rate limit headers

#### Portal API Implementation (Session 5)
- **Faculty Schedule View**: Query FMIT assignments by week with conflict detection
- **Swap Management**: Full CRUD for swap requests with auto-find candidates
- **Swap Response**: Accept/reject with counter-offer support
- **Faculty Preferences**: Query and update FacultyPreference with partial update support
- **Marketplace**: Query open swaps with compatibility checking
- **Swap History API**: Full query support with filtering (faculty, status, date range), pagination

#### Frontend Test Coverage (Session 5)
- **Analytics Feature Tests**: 165 test cases across 8 files (~2,500 lines)
  - MetricsCard, FairnessTrend, VersionComparison, WhatIfAnalysis, AnalyticsDashboard
- **Audit Feature Tests**: 264 test cases across 9 files (~4,200 lines)
  - AuditLogTable, AuditLogFilters, AuditLogExport, AuditTimeline, ChangeComparison
- **Swap Marketplace Tests**: 186 test cases across 8 files (~3,100 lines)
  - SwapRequestCard, SwapFilters, SwapRequestForm, MySwapRequests, SwapMarketplace

#### Backend Service Tests (Session 5)
- **Absence Service Tests**: 23 test cases for CRUD, date filtering, validation
- **Assignment Service Tests**: 22 test cases for CRUD, ACGME validation, optimistic locking
- **Person Service Tests**: 37 test cases for CRUD, filtering by type/PGY/specialty
- **Block Service Tests**: 31 test cases for CRUD, block generation, date filtering

#### Block Schedule Drag GUI
- **Resident Academic Year View**: Full academic year (July-June) schedule view for all residents
  - Residents grouped by PGY level (PGY-1, PGY-2, PGY-3)
  - 52 weeks with month headers and week numbers
  - Drag-and-drop to reschedule assignments within a resident's row
  - Compact/normal zoom toggle
  - Today navigation with auto-scroll
- **Faculty Inpatient Weeks View**: Dedicated view for faculty inpatient service management
  - Faculty sorted by inpatient week count
  - Summary statistics (total, average, max, min inpatient weeks)
  - Toggle between all activities or inpatient-only filter
  - Drag-and-drop functionality
- **Drag-and-Drop Infrastructure**: Using dnd-kit library
  - ScheduleDragProvider context for drag state management
  - DraggableBlockCell component with visual feedback
  - Optimistic UI updates with API sync
  - Toast notifications for success/warning/error feedback
- **ViewToggle Enhancement**: Added annual view buttons (Res./Fac.) with visual separator
- **New Dependencies**: @dnd-kit/core, @dnd-kit/utilities, @dnd-kit/sortable, @dnd-kit/modifiers

#### Resilience Framework
- **Tier 1 Resilience**: Database tables and basic resilience tracking (#129, #130)
- **Tier 2 Resilience**: Extended resilience capabilities (#131)
- **Tier 3 Resilience**: Full database persistence and advanced resilience features (#132, #133)
- **Resilience Integration**: Resilience data integrated into scheduling constraints (#136)
- **Cross-Industry Concepts**: 80% utilization threshold, N-1/N-2 contingency analysis, defense in depth

#### Procedure Credentialing
- **Faculty Credentialing System**: Track procedure credentials for faculty supervision (#135, #137)
- **Supervision Tracking**: Ensure credentialed faculty supervise procedures
- **Database Migration**: Added certification tracking tables (#137)

#### Scheduler Improvements
- **Explainability Module**: Transparent decision-making with explanations for scheduling choices (#138)
- **Algorithm Documentation**: Detailed scheduling optimization documentation

#### Testing Infrastructure
- **Playwright E2E Tests**: End-to-end tests for complete user journeys (#120)
- **MSW Test Infrastructure**: Mock Service Worker setup for frontend API mocking (#121)

#### Documentation
- **Data Storage Documentation**: Added to admin manual (#134)
- **Launch Lessons Learned**: Post-deployment lessons from macOS launch (#113)
- **ChatGPT Review Topics**: External perspective document for architectural review (#141)

### Changed

#### Architecture
- **Backend Layered Architecture**: Reorganized backend into clean layered architecture (#124, #126-128)
- **Frontend Error Handling**: Replaced console statements with proper error handling (#119)
- **Notification System**: Added proper logging to notification system (#143)

#### Dependencies
- **Frontend Protection**: Protected frontend deps from breaking updates (#118)
- **Redis Upgrade**: Bumped redis from 5.0.1 to 7.1.0 (#90)

### Fixed
- **Mac Compatibility**: Resolved dependency conflicts and type errors for Mac (#122, #123)
- **Docker Build**: Fixed Docker build and TypeScript compilation errors (#112)
- **Dependabot PRs**: Reviewed and consolidated dependency updates (#111)

---

## Planned Features
- ~~Calendar drag-and-drop interface~~ ✓ Implemented (Block Schedule Drag GUI)
- Email notifications for schedule changes
- Bulk import/export for people and absences
- ~~Advanced reporting and analytics~~ ✓ Implemented (Analytics Dashboard + Pareto Optimization)
- ~~Schedule conflict resolution wizard~~ ✓ Implemented (Conflict Auto-Resolver Service)
- Mobile application (React Native)
- LDAP/SSO integration
- ~~Audit log dashboard~~ ✓ Implemented (Full Audit API + Frontend)
- Schedule template cloning
- Multi-program support
- ~~Rate limiting for authentication~~ ✓ Implemented (Session 5)
- ~~Faculty self-service portal~~ ✓ Implemented (Portal API - Session 5)

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.0.0 | 2024-01-15 | Initial release with full scheduling capabilities |

---

## Migration Notes

### Upgrading to 1.0.0

This is the initial release. For new installations:

1. Copy `.env.example` to `.env` and configure
2. Run database migrations: `alembic upgrade head`
3. Create first admin user via registration
4. Configure rotation templates
5. Add residents and faculty
6. Generate initial schedule

---

## Deprecation Notices

No deprecations in current version.

---

## Support

For issues or questions:
- GitHub Issues: [Report a bug](https://github.com/your-org/residency-scheduler/issues)
- Documentation: [docs/](docs/)

---

[1.0.0]: https://github.com/your-org/residency-scheduler/releases/tag/v1.0.0
[Unreleased]: https://github.com/your-org/residency-scheduler/compare/v1.0.0...HEAD
