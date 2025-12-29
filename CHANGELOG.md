# Changelog

All notable changes to the Residency Scheduler project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

#### Session 015 - Solver Verification & Documentation (2025-12-29)

**All 4 Solvers Verified Operational:**
- Comprehensive diagnostic verification after 2025-12-24 template balance fixes
- 3 Explore agents + 4 QA_TESTER agents deployed for parallel verification
- 21/21 solver tests passing across all solver implementations

**Verification Results:**
| Solver | Tests | Balance Distribution |
|--------|-------|---------------------|
| Greedy | 7/7 pass | 7,7,6 (balanced) |
| CP-SAT | 4/4 pass | 9,9 (balanced) |
| PuLP | 5/5 pass | 9,9 (balanced) |
| Hybrid | 5/5 pass | Fallback chain working |

**Test Coverage Gap Identified:**
- No explicit balance behavior tests exist
- Balance verified implicitly through assignment distribution
- Recommendation documented for future `test_template_balance_*` tests

**Documentation Updated:**
- `HUMAN_TODO.md`: Solver section marked VERIFIED with test results
- `.claude/Scratchpad/SESSION_015_SOLVER_VERIFICATION.md`: Full session report

#### Time Crystal Scheduling Tools (December 2025)

**Anti-Churn Schedule Optimization:**
- New `backend/app/scheduling/periodicity/` module implementing time-crystal-inspired scheduling
- `anti_churn.py`: Hamming distance, rigidity scoring, combined time crystal objective
- `subharmonic_detector.py`: Autocorrelation-based detection of natural periodicities (7d, 14d, 28d cycles)
- `stroboscopic_manager.py`: Checkpoint-based state management for consistent schedule observation
- Tests in `backend/tests/scheduling/periodicity/`

**New MCP Tools (5 tools):**
- `analyze_schedule_rigidity_tool`: Compare schedule stability between versions
- `analyze_schedule_periodicity_tool`: Detect natural cycles (weekly, biweekly, ACGME 4-week)
- `calculate_time_crystal_objective_tool`: Combined optimization score (constraints + rigidity + fairness)
- `get_checkpoint_status_tool`: Stroboscopic state info
- `get_time_crystal_health_tool`: Component health monitoring

**Key Concepts:**
- Time Crystal Objective: `score = (1-α-β)·constraints + α·rigidity + β·fairness`
- Rigidity scoring prevents unnecessary churn during schedule regeneration
- Subharmonic detection preserves emergent patterns (Q4 call, alternating weekends)
- Stroboscopic checkpoints ensure consistent state observation

**Files Added:**
- `backend/app/scheduling/periodicity/__init__.py`
- `backend/app/scheduling/periodicity/anti_churn.py`
- `backend/app/scheduling/periodicity/subharmonic_detector.py`
- `backend/app/scheduling/periodicity/stroboscopic_manager.py`
- `mcp-server/src/scheduler_mcp/time_crystal_tools.py`
- `docs/architecture/TIME_CRYSTAL_ANTI_CHURN.md`

**References:**
- SYNERGY_ANALYSIS.md Section 11: Time Crystal Dynamics
- Shleyfman et al. (2025). Planning with Minimal Disruption. arXiv:2508.15358

#### Observability & Resilience Hardening (December 2025)

**Pre-Solver Constraint Saturation Validator:**
- New `PreSolverValidator` class in `backend/app/scheduling/pre_solver_validator.py`
- Detects obviously infeasible scheduling problems BEFORE solver runs
- Validates: hour balance, coverage ratios, availability conflicts, mutual exclusions
- Provides complexity estimation and runtime predictions
- Fast-fails with actionable error messages instead of expensive solver timeouts
- Tests in `backend/tests/scheduling/test_pre_solver_validator.py`

**OpenTelemetry Export Backend:**
- Enhanced `backend/app/telemetry/tracer.py` with production-ready exporters
- Supports OTLP gRPC/HTTP, Jaeger, Zipkin, and Console exporters
- New config settings: `TELEMETRY_EXPORTER_TYPE`, `TELEMETRY_EXPORTER_ENDPOINT`
- BatchSpanProcessor for efficient trace batching
- Authentication headers support for cloud observability platforms
- Tests in `backend/tests/telemetry/test_otel_exporter.py`

**Circuit Breaker Health Integration:**
- New `CircuitBreakerHealthCheck` in `backend/app/health/checks/circuit_breaker.py`
- Integrated into `/health/detailed` and `/health/services/circuit_breakers` endpoints
- Reports: total breakers, open/half-open/closed counts, failure rates
- Health status: HEALTHY (none open) → DEGRADED (some open) → UNHEALTHY (critical open)
- Tests in `backend/tests/health/test_circuit_breaker_health.py`

**Recovery Distance (RD) Resilience Metric:**
- New `RecoveryDistanceCalculator` in `backend/app/resilience/recovery_distance.py`
- Measures minimum edits needed to recover from n-1 shocks (single resource loss)
- Event types: faculty absence, resident sick day, room closure
- Aggregate metrics: RD mean, median, P95, max, breakglass count
- Bounded depth-first search with timeout protection
- Integrated into resilience framework exports
- Tests in `backend/tests/resilience/test_recovery_distance.py`

**Security Review & Documentation:**
- Updated `docs/security/SECURITY_PATTERN_AUDIT.md` with dependency vulnerability analysis
- CVE-2023-30533 & CVE-2024-22363 (SheetJS xlsx) analyzed - confirmed false positive
- Documented frontend Excel export uses TSV workaround, not SheetJS library
- Backend uses `openpyxl` (Python) for all Excel operations
- New `docs/architecture/import-export-system.md` documenting export architecture
- Identified `.xls` extension mismatch (frontend accepts, backend rejects)
#### Excel Import with Backend-First Parsing (December 2025)

**Full Excel (.xlsx) Import Support:**
- Added `POST /imports/parse-xlsx` endpoint for Excel file parsing
- Added `POST /imports/parse-xlsx/sheets` endpoint for listing workbook sheets
- Backend uses `openpyxl` for full Excel support including:
  - Date cell conversion to ISO format
  - Merged cell handling
  - Cell color detection (for color-coded schedules)
  - Duplicate header detection with automatic renaming
  - Empty row filtering
- Frontend uses SheetJS as client-side fallback when backend is unavailable
- Warning banner shown when using client-side fallback mode

**Frontend Changes:**
- Added `xlsx` (SheetJS) package for client-side fallback parsing
- Updated `useImport` hook with hybrid backend/client parsing logic
- Added `xlsxFallbackUsed` and `xlsxWarnings` state tracking
- Updated `BulkImportModal` with fallback warning display

**Files Added:**
- `backend/app/api/routes/imports.py` - New import parsing endpoints
- `backend/tests/routes/test_imports.py` - Endpoint tests

**Files Modified:**
- `frontend/src/features/import-export/useImport.ts` - Hybrid parsing logic
- `frontend/src/features/import-export/BulkImportModal.tsx` - Warning banners
- `docs/user-guide/imports.md` - Updated documentation

#### Faculty Outpatient Scheduling Improvements (December 2025)

**Adjunct Faculty Role:**
- Added `ADJUNCT` role to `FacultyRole` enum for external/adjunct faculty
- Adjunct faculty have `weekly_clinic_limit = 0` (not auto-scheduled)
- Excluded from `FacultyOutpatientAssignmentService` auto-scheduling
- Can still be manually pre-loaded to FMIT via block schedule
- Full frontend support in Add/Edit Person modals with faculty role dropdown

**Frontend Person Management:**
- Added `FacultyRole` enum to frontend TypeScript types
- Added `faculty_role` field to `Person`, `PersonCreate`, `PersonUpdate` interfaces
- Added faculty role dropdown to `AddPersonModal` (shown when type = faculty)
- Added faculty role dropdown to `EditPersonModal` with pre-population

### Fixed

#### Supervision Calculation Bug (December 2025) - CRITICAL

**Problem:** Faculty supervision calculation overcounted required faculty in mixed PGY scenarios by applying ceiling operations separately to each PGY group.

**Solution:** Switched to fractional supervision load approach:
- PGY-1: 0.5 supervision load each (1:2 ratio)
- PGY-2/3: 0.25 supervision load each (1:4 ratio)
- Sum all loads THEN apply ceiling

**Example:** 1 PGY-1 + 1 PGY-2 now correctly requires 1 faculty (not 2).

**Files Fixed:**
- `backend/app/services/faculty_outpatient_service.py`
- `backend/app/scheduling/engine.py`
- `backend/app/scheduling/constraints/acgme.py`

**Tests Added:**
- `test_calculate_required_faculty_fractional_load()` in `test_constraints.py`

**Documentation Updated:**
- Fixed supervision example in `docs/architecture/FACULTY_SCHEDULING_SPECIFICATION.md`
- Updated diagnostic report at `docs/planning/FACULTY_OUTPATIENT_DIAGNOSTIC_REPORT.md`

### Added

#### Personal AI Infrastructure (PAI) - December 2025

**Major AI-Assisted Development Platform:**
- **34 Agent Skills** organized by tier for specialized scheduling tasks
  - Tier 1 (10 skills): Core development (test-writer, code-review, database-migration, etc.)
  - Tier 2 (8 skills): Scheduling-specific (acgme-compliance, swap-management, schedule-optimization)
  - Tier 3 (10 skills): Advanced operations (production-incident-responder, security-audit)
  - Tier 4 (6 skills): Experimental (solver-control, constraint-preflight)
- **27 Slash Commands** for rapid task execution
  - Scheduling: `/generate-schedule`, `/verify-schedule`, `/optimize-schedule`, `/check-constraints`
  - Quality: `/write-tests`, `/review-code`, `/fix-code`, `/quality-check`
  - Operations: `/docker-help`, `/incident`, `/solver`, `/swap`
- **4 Operational Modes**: Interactive, Autonomous, Review, Emergency
- **Multi-Agent Orchestration**: Parallel task execution with up to 10 terminals

**Documentation:**
- `docs/guides/AI_AGENT_USER_GUIDE.md`: Comprehensive AI interface guide
- `docs/development/AGENT_SKILLS.md`: Complete skills reference
- `docs/development/SLASH_COMMANDS.md`: Command reference
- `.claude/skills/*/SKILL.md`: Individual skill documentation

#### MCP Server Expansion (December 2025)

**Expanded from 4 to 34 MCP Tools:**
- **Scheduling Tools (10)**: `generate_schedule`, `validate_schedule`, `detect_conflicts`, `optimize_schedule`, etc.
- **Resilience Tools (12)**: `run_contingency_analysis`, `check_utilization_threshold`, `get_defense_level`, `analyze_homeostasis`, etc.
- **Swap Tools (6)**: `analyze_swap_candidates`, `execute_swap`, `find_swap_matches`, etc.
- **Analytics Tools (6)**: `get_schedule_metrics`, `get_compliance_summary`, `get_workload_distribution`, etc.

**Backend Integration:**
- 7 tools fully integrated with backend APIs
- 10 placeholder implementations with graceful fallback
- Response mapping between MCP and backend formats
- See `docs/planning/MCP_PLACEHOLDER_IMPLEMENTATION_PLAN.md` for implementation roadmap

#### Docker Security Hardening (December 2025)

**Production-Ready Container Security:**
- **Non-root Users**: All containers run as non-privileged users
- **Multi-stage Builds**: Reduced image sizes, removed build dependencies
- **Read-only Filesystems**: Where applicable
- **Secret Management**: Improved `.env` handling
- **Health Checks**: Container-level health monitoring

**Files Changed:**
- `docker-compose.yml`: Security-hardened service definitions
- `backend/Dockerfile`: Multi-stage build with non-root user
- `frontend/Dockerfile`: Optimized Next.js production build
- `mcp-server/Dockerfile`: Minimal Python image

#### Solver Operational Controls (December 2025)

**Kill-Switch & Progress Monitoring:**
- **Solver Kill-Switch**: Abort runaway schedule generation via Celery task revocation
- **Progress Monitoring**: Real-time progress updates during long-running solves
- **Prometheus Metrics**: Solver execution time, constraint violations, optimization scores
- **Timeout Protection**: Configurable solver timeouts (default: 5 minutes)

**Files:**
- `backend/app/scheduling/solver_control.py`: Kill-switch implementation
- `.claude/skills/solver-control/SKILL.md`: Solver management skill

#### Cross-Disciplinary Research (December 2025)

**10+ Bridge Specifications for Resilience Framework:**
- `docs/bridges/forestry-burnout-fire-index.md`: CFFDRS adaptation for burnout prediction
- `docs/bridges/telecommunications-erlang-coverage.md`: Queuing theory for specialist staffing
- `docs/bridges/epidemiology-sir-burnout.md`: SIR models for burnout spread
- `docs/bridges/seismic-sta-lta-detection.md`: Early warning algorithms
- `docs/bridges/materials-science-creep-fatigue.md`: Larson-Miller parameter adaptation
- `docs/bridges/semiconductor-spc-monitoring.md`: Western Electric rules for schedule quality
- `docs/bridges/power-grid-n1-contingency.md`: N-1/N-2 analysis
- `docs/bridges/chemistry-le-chatelier.md`: Equilibrium analysis

#### Session 15 - Custom Rotation Colors & Mid-Block Splits (2025-12-26)

**Custom Rotation Template Colors:**
- Added `font_color` and `background_color` fields to rotation templates
- Schedule cells render with database-defined inline styles
- Automatic fallback to activity-type colors when not customized
- Files changed: `rotation_template.py` (model), `ScheduleCell.tsx`, `api.ts` (TypeScript types)

**Mid-Block Rotation Split Utility:**
- New `split_combined_rotations.py` script for processing combined rotations
- Splits NF+DERM, NF+FMIT, NF+CARD into proper half-block assignments
- Inserts Post-Call (PC) recovery day at mid-block (day 15)
- Ensures Post-Call constraints trigger correctly at mid-block transitions

**Database Migration:**
- Added merge migration to unify block0 and main alembic heads

#### Immutable Assignment Preservation (2025-12-26)

**Core Engine Enhancement:**
- **6 Preserved Assignment Types**: Solver now respects pre-seeded immutable assignments
  - `inpatient`: FMIT, Night Float, ICU, L&D, NICU
  - `off`: Hilo, Kapiolani, Okinawa (off-site hospitals)
  - `education`: FMO orientation, GME, Lectures
  - `absence`: Leave, Weekend
  - `recovery`: Post-Call Recovery
  - Only `outpatient` and `procedures` are solver-managed

**New Engine Loaders:**
- `_load_fmit_assignments()`: Faculty FMIT teaching weeks
- `_load_resident_inpatient_assignments()`: All resident inpatient rotations
- `_load_absence_assignments()`: Leave, Weekend, TDY
- `_load_offsite_assignments()`: Hilo, Kapiolani, Okinawa
- `_load_recovery_assignments()`: Post-Call Recovery
- `_load_education_assignments()`: FMO, GME, Lectures

**Safety Improvements:**
- Deferred deletion: Old assignments deleted AFTER successful solve (not before)
- Conflict filtering: `_create_assignments_from_result()` skips occupied slots
- Faculty supervision: Excludes faculty with FMIT/absences from clinic assignments

**Documentation:**
- `docs/sessions/SESSION_2025-12-26_IMMUTABLE_ASSIGNMENTS.md`: Full session summary
- `docs/architecture/ACTIVITY_TYPES.md`: 7 activity types reference
- `docs/architecture/FMIT_CONSTRAINTS.md`: FMIT constraint documentation
- `docs/architecture/ENGINE_ASSIGNMENT_FLOW.md`: Preserved assignment flow
- `docs/development/SLASH_COMMANDS.md`: 18 slash commands reference

**New Slash Commands (18):**
- `/generate-schedule`, `/verify-schedule`, `/optimize-schedule`, `/check-constraints`
- `/debug`, `/debug-explore`, `/debug-tdd`
- `/write-tests`, `/review-code`, `/review-pr`, `/fix-code`, `/quality-check`
- `/export-pdf`, `/export-xlsx`
- `/docker-help`, `/incident`, `/solver`, `/swap`, `/changelog`, `/document-session`

**New Skills:**
- `session-documentation`: Comprehensive session documentation generator

**Seeding Scripts:**
- `scripts/seed_rotation_templates.py`: 55 rotation templates by activity type
- `scripts/seed_inpatient_rotations.py`: Block-by-block inpatient assignment loader

### Fixed

#### Missing PostFMITRecoveryConstraint (2025-12-26)

**Bug Discovery:** `PostFMITRecoveryConstraint` existed in `fmit.py` but was NOT registered in the default constraint manager, causing faculty to not get their Friday recovery day blocked after FMIT weeks.

**Fix:** Added to `backend/app/scheduling/constraints/manager.py`:
```python
manager.add(PostFMITRecoveryConstraint())  # Faculty Friday PC after FMIT
manager.add(PostFMITSundayBlockingConstraint())
```

**Verification:** Constraint correctly applies only to faculty (not residents) based on template name matching ("FMIT AM/PM" vs "Family Medicine Inpatient Team Intern/Resident").

#### Block 10 Scheduling Complete (2025-12-25/26)

**Milestone: Block 10 schedule generation fully operational**
- **87 assignments** generated with **0 ACGME violations** and **112.5% coverage**
- All 25 scheduling constraints active and verified

**New Constraints Implemented:**
- `ResidentInpatientHeadcountConstraint` (Hard): Enforces FMIT=1 per PGY level, NF=1 concurrent
- `PostFMITSundayBlockingConstraint` (Hard): Blocks Sunday call after FMIT week
- `CallSpacingConstraint` (Soft, weight=8.0): Penalizes back-to-back call weeks
- `FMITResidentClinicDayConstraint` (Hard): PGY-specific clinic days (relies on pre-loading)

**Engine Enhancements:**
- `preserve_resident_inpatient` parameter: Protects resident FMIT/NF/NICU assignments
- `preserve_absence` parameter: Protects Leave/Weekend assignments from solver
- `_load_resident_inpatient_assignments()`: Loads inpatient assignments before solving
- `_load_absence_assignments()`: Loads absence records as unavailability

**Test Coverage:**
- 64+ new constraint tests across 4 test files
- `test_constraint_registration.py`: Verifies all constraints registered in manager
- `test_fmit_constraints.py`: 32 tests for FMIT timeline and blocking
- `test_call_equity_constraints.py`: 32 tests for call spacing and equity
- `test_phase4_constraints.py`: 20+ tests for SM alignment and post-call

**Documentation:**
- `BLOCK_SCHEDULE_ARCHITECTURE.md`: Comprehensive 313-line architecture guide
- Time hierarchy: 730 half-day slots → 13 blocks → 1 Academic Year
- Solver architecture with 3D boolean variables documented

**Merged PRs:** #440-#445

### Fixed

#### Security & Bug Fixes (Session 13 - 2025-12-21)

Fixes for bugs identified in Codex review of Session 13 PRs (#312):

**Security Fixes**
- **Comprehensive Startup Secret Validation**: Added validation for all service secrets at application startup
  - **REDIS_PASSWORD**: Now required in production (min 16 chars), validates against weak password list
  - **DATABASE_URL**: Extracts and validates database password (min 12 chars), rejects default 'scheduler' password
  - **SECRET_KEY & WEBHOOK_SECRET**: Enhanced validators check weak password list and enforce 32+ char minimum
  - **WEAK_PASSWORDS**: Centralized list of 30+ known weak/default passwords including .env.example placeholders
  - **Development vs Production**: Logs warnings in DEBUG mode, raises errors in production (fail-fast)
  - Application refuses to start if any production secret is weak/default
  - Added 18 new tests in `tests/test_core.py::TestSecretValidation`

- **Refresh Token Privilege Escalation** (PR #327, #328): Fixed critical vulnerability where refresh tokens could be used as access tokens
  - `verify_token()` now explicitly rejects tokens with `type="refresh"`
  - Prevents attackers from using stolen refresh tokens (7-day lifetime) to bypass short access token lifetime (30 min)
  - Added tests: `test_refresh_token_cannot_be_used_as_access_token`, `test_refresh_token_in_cookie_rejected`
  - Fixed test validation to properly clear cookies before testing Authorization header behavior

- **Refresh Token Rotation Blacklisting** (PR #327): Implemented secure refresh token rotation
  - Old refresh tokens are now **immediately blacklisted** when rotation is enabled
  - `verify_refresh_token()` accepts `blacklist_on_use` parameter for atomic rotation
  - Prevents token replay attacks where stolen refresh tokens could be reused indefinitely
  - Added tests: `test_refresh_blacklists_old_token_on_rotation`, `test_refresh_reused_token_rejected`

- **Rate Limit Bypass Prevention**: Fixed X-Forwarded-For header spoofing vulnerability
  - Added `TRUSTED_PROXIES` config option to validate proxy sources
  - Only trust X-Forwarded-For when request comes from configured trusted proxy
  - Prevents attackers from bypassing rate limiting via header manipulation

**Data Integrity Fixes**
- **Cache Key Collision**: Fixed cache key truncation in scheduling caching layer
  - Changed from truncating IDs to first 10 elements (which caused collisions)
  - Now uses SHA-256 hash of all IDs for collision-resistant cache keys
  - Prevents incorrect availability data being served when >10 persons/blocks queried

**Test Reliability Fixes**
- **Hook Mock Results Access**: Fixed mock results array indexing in procedure credentialing tests
  - Changed from `mock.results[0]` to accessing the most recent result
  - Prevents test failures from accumulated mock calls across test runs

**Documentation Updates**
- Added clear documentation for test-local component pattern in swap auto-matching tests
  - Documented that `AutoMatchingCandidates` is a reference implementation
  - Added TODO notes for when production component is created
  - Noted type differences between test mock and production types

### Added

#### API Route Test Coverage (Session 14 - 2025-12-24)
- **15 new API route test files** (~7,591 lines): Comprehensive tests for previously untested routes
  - `test_batch_routes.py`: Batch operations for assignments (4 test classes)
  - `test_conflicts_routes.py`: Conflict analysis and visualizations (9 test classes)
  - `test_credentials_routes.py`: Faculty procedure credentials (12 test classes)
  - `test_daily_manifest_routes.py`: Daily staffing manifest (5 test classes)
  - `test_db_admin_routes.py`: Database admin endpoints (9 test classes)
  - `test_features_routes.py`: Feature flag management (13 test classes)
  - `test_jobs_routes.py`: Background job management (8 test classes)
  - `test_metrics_routes.py`: Prometheus metrics endpoints (7 test classes)
  - `test_profiling_routes.py`: Performance profiling (13 test classes)
  - `test_queue_routes.py`: Celery task queue management (15 test classes)
  - `test_quota_routes.py`: API quota management (10 test classes)
  - `test_rate_limit_routes.py`: Rate limiting management (7 test classes)
  - `test_reports_routes.py`: PDF report generation (5 test classes)
  - `test_search_routes.py`: Full-text search endpoints (8 test classes)
  - `test_upload_routes.py`: File upload management (7 test classes)
- Test patterns: Authentication/authorization testing, success paths, error handling, response structure verification, integration tests, edge cases

#### Test Coverage Expansion (Session 11 - 2025-12-20)
- **Certification Scheduler Tests**: 34 tests for background certification expiration checks
  - Scheduler lifecycle (start/stop), reminder thresholds, admin summary
  - Environment configuration, singleton pattern, exception handling
- **Advanced ACGME Validator Tests**: 41 tests for compliance validation
  - 24+4 hour rule, night float limits, moonlighting hours
  - PGY-specific requirements, duty hours breakdown
- **Email Service Tests**: 32 tests for SMTP notifications
  - Configuration loading, urgency levels (7/30/90/180 days)
  - HTML template generation, compliance summaries
- **Pareto Optimization Tests**: 54 tests for multi-objective scheduling (93% coverage)
  - Objective functions (fairness, coverage, preference satisfaction)
  - Constraint handling, Pareto frontier extraction, hypervolume calculation
- **XLSX Import Tests**: 84 edge case tests for Excel schedule imports
  - Slot type mapping (70+ codes), conflict detection, week calculations
  - Provider scheduling, alternating pattern detection
- **Scheduling Catalyst Integration Tests**: 57 new integration + 21 expanded optimizer tests
  - Full workflow testing, barrier-catalyst matching, chain reactions
  - Multi-objective optimization, constraint satisfaction, Pareto frontier
- **Notification Channels Tests**: 43 tests for delivery channels (93% coverage)
  - InAppChannel, EmailChannel, WebhookChannel
  - Priority handling, HTML formatting, payload structure

#### Documentation Enhancements
- **Portal API Routes**: Comprehensive docstrings for all 11 endpoints
  - Google-style format with Args, Returns, Raises, Business Logic
  - Module-level docstring with authentication and model references
- **MTF Compliance Module**: 8,000+ character documentation expansion
  - Military terminology glossary (DRRS, MFR, RFF, C/P/S-ratings)
  - Detailed algorithm explanations for risk assessment
  - Usage examples for readiness assessment, circuit breaker, RFF drafting

#### Bug Fixes & Implementations
- **Scheduling Catalyst Optimizer**: Fixed missing CatalystType import
- **Experimental Benchmarks**: Resolved 9 TODOs across 3 files
  - Memory tracking via tracemalloc in solver_comparison.py
  - Violation counting with flexible result structure handling
  - Coverage calculation with multiple attribute fallbacks
  - Pathway validation with complete step/barrier/catalyst extraction
  - Baseline and experimental solver execution in harness.py

### Changed
- Expanded test coverage from ~70% to comprehensive coverage in key services
- Enhanced scheduling_catalyst test suite from basic to full integration

### Statistics
- **346+ new tests** across 9 new test files
- **8,514 lines added** (17 files changed)
- **9 TODOs resolved** in experimental benchmarks
- Tests cover: services, validators, notifications, scheduling_catalyst
#### MCP Server Enhancements
- **MCP Tool Implementations**: Full implementations for 4 critical tools:
  - `validate_schedule()`: ACGME compliance validation (80-hour rule, 1-in-7 rule, supervision ratios)
  - `analyze_contingency()`: N-1/N-2 contingency analysis with impact assessment
  - `detect_conflicts()`: Comprehensive conflict detection (double-booking, work hour violations, leave overlaps)
  - `find_swap_matches()`: Intelligent swap matching with multi-factor scoring algorithm
- **MCP Resource Database Queries**: Real database queries replacing placeholder data
  - `get_schedule_status()`: Live assignment data with coverage metrics
  - `get_compliance_summary()`: Full ACGME compliance calculations

#### Type Safety Improvements
- **TypedDict Expansion**: 8 new TypedDict definitions in `core/types.py`:
  - `SwapDetails`, `CoverageReport`, `CoverageReportItem`, `ValidationResultDict`
  - `ScheduleGenerationMetrics`, `ResilienceAnalysisResult`, `WorkloadDistribution`, `AnalyticsReport`
- **MTF Compliance Type Safety**: 6 TypedDict classes for resilience framework:
  - `SystemStateDict`, `MTFComplianceResultDict`, `ContingencyAnalysisDict`
  - `CapacityMetricsDict`, `CascadePredictionDict`, `PositiveFeedbackRiskDict`

#### Performance Optimizations
- **N+1 Query Optimization**: Eager loading patterns across 5 service files
  - `assignment_service.py`: Eager load Person, Block relationships
  - `person_service.py`: New `get_person_with_assignments()` method
  - `block_service.py`: New `get_block_with_assignments()` method
  - `swap_request_service.py`: 7 methods optimized with eager loading
  - `swap_executor.py`: Batch loading for swap execution
  - Performance improvement: 87-99% reduction in database queries

#### Infrastructure
- **Email Notification Enhancement**: Added `template_id` relationship to EmailLog model
- **EmailSendRequest Schema**: New Pydantic schema for API email sending
- **Scheduler Ops Celery Integration**: Real task tracking replacing synthetic metrics
  - Query active/scheduled/reserved tasks via Celery Inspect API
  - Historical task analysis from Redis backend
  - 8 comprehensive test cases

#### Testing & Quality
- **Stress Testing Framework**: Complete implementation in `experimental/benchmarks/`
  - 5 stress levels: NORMAL, ELEVATED, HIGH, CRITICAL, CRISIS
  - Graceful degradation verification
  - ACGME compliance calculation under stress
  - Patient safety master regulator checks
- **Frontend JSDoc Documentation**: Comprehensive documentation for:
  - `api.ts`: API client with all HTTP helpers
  - `auth.ts`: Authentication functions
  - `validation.ts`: Form validation utilities

### Changed
- **Constraints Module**: Modularized from 3,016-line monolithic file to 14 specialized modules (5,613 lines total)

### Documentation
- Added `docs/sessions/SESSION_11A_MCP_AND_OPTIMIZATION.md`
- Added `docs/sessions/SESSION_11B_TEST_COVERAGE.md`
- Added `docs/EMAIL_NOTIFICATION_INFRASTRUCTURE.md`
- Added `SCHEDULER_OPS_CELERY_INTEGRATION_SUMMARY.md`
- Added `backend/experimental/benchmarks/STRESS_TESTING_SUMMARY.md`

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

### Session 9 Improvements (2025-12-18/19)

#### Added
- **Email Infrastructure Models**: EmailLog and EmailTemplate models for v1.1.0 notification system
- **TypedDict Type Definitions**: Core type definitions for schedule metrics, compliance results, and validation contexts
- **MTF Compliance Dataclasses**: Structured types for MTF violation tracking and compliance results
- **Hook Documentation**: Comprehensive JSDoc documentation for all frontend React hooks

#### Changed
- **Query Optimization**: Eliminated N+1 query patterns in portal, resilience, fmit_health, analytics, and fmit_timeline routes using eager loading
- **Type Safety**: Improved type annotations in resilience and analytics modules

#### Documentation
- Session 9 parallel workstream execution documented
- Strategic decisions finalized (MIT license, military-first, email notifications priority)

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
