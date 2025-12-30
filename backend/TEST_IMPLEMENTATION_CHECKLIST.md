# Test Implementation Checklist - Backend Service Tests

**Session 025 - Marathon Execution Plan**
**Target:** 21% → 80% coverage in 3 weeks (110 hours)

## Pre-Implementation Setup

- [ ] Fix dependency installation (cryptography/cffi conflict)
- [ ] Run pytest to get accurate baseline coverage number
- [ ] Create `tests/controllers/` directory
- [ ] Set up reusable fixtures in `tests/conftest.py`
- [ ] Configure CI coverage threshold enforcement

## Phase 1: Critical Infrastructure (Week 1) - 40 hours

### Controllers (20 hours) - PRIORITY 1 ⚠️

- [ ] `tests/controllers/test_auth_controller.py` (3h)
  - [ ] Test authentication flow
  - [ ] Test authorization checks
  - [ ] Test token refresh
  - [ ] Test error scenarios

- [ ] `tests/controllers/test_person_controller.py` (2h)
  - [ ] Test CRUD operations
  - [ ] Test validation
  - [ ] Test permissions

- [ ] `tests/controllers/test_assignment_controller.py` (3h)
  - [ ] Test assignment creation
  - [ ] Test conflict detection
  - [ ] Test ACGME validation
  - [ ] Test bulk operations

- [ ] `tests/controllers/test_block_controller.py` (2h)
  - [ ] Test block creation
  - [ ] Test block queries
  - [ ] Test date range validation

- [ ] `tests/controllers/test_credential_controller.py` (2h)
  - [ ] Test credential CRUD
  - [ ] Test expiration checks
  - [ ] Test eligibility validation

- [ ] `tests/controllers/test_certification_controller.py` (2h)
  - [ ] Test certification tracking
  - [ ] Test renewal reminders

- [ ] `tests/controllers/test_procedure_controller.py` (2h)
  - [ ] Test procedure logging
  - [ ] Test volume tracking

- [ ] `tests/controllers/test_call_assignment_controller.py` (2h)
  - [ ] Test call scheduling
  - [ ] Test equity distribution

- [ ] `tests/controllers/test_absence_controller.py` (2h)
  - [ ] Test leave requests
  - [ ] Test conflict detection

- [ ] `tests/controllers/test_block_scheduler_controller.py` (2h)
  - [ ] Test schedule generation
  - [ ] Test constraint validation

### Critical Services (20 hours)

- [ ] `tests/services/test_auth_service.py` (4h) ⚠️
  - [ ] Test authenticate() with valid credentials
  - [ ] Test authenticate() with invalid credentials
  - [ ] Test register_user() - first user becomes admin
  - [ ] Test register_user() - requires admin for subsequent users
  - [ ] Test username/email uniqueness
  - [ ] Test password hashing
  - [ ] Test token generation (JWT)
  - [ ] Test last_login update

- [ ] `tests/services/test_academic_block_service.py` (6h)
  - [ ] Test get_block_matrix()
  - [ ] Test list_academic_blocks()
  - [ ] Test _parse_academic_year() with valid/invalid formats
  - [ ] Test _generate_academic_blocks()
  - [ ] Test _get_residents() with PGY filtering
  - [ ] Test _build_matrix_cells()
  - [ ] Test _check_acgme_compliance()
  - [ ] Test _calculate_matrix_summary()
  - [ ] Test rotation assignment logic
  - [ ] Test edge cases (leap year, partial blocks)

- [ ] `tests/services/test_calendar_service.py` (5h)
  - [ ] Test generate_ics_for_person()
  - [ ] Test generate_ics_for_rotation()
  - [ ] Test generate_ics_all()
  - [ ] Test create_subscription()
  - [ ] Test validate_subscription_token()
  - [ ] Test revoke_subscription()
  - [ ] Test timezone handling (Pacific/Honolulu)
  - [ ] Test AM/PM block times
  - [ ] Test ICS format compliance

- [ ] `tests/services/test_credential_service.py` (4h)
  - [ ] Test credential CRUD operations
  - [ ] Test eligibility checks (hard constraints)
  - [ ] Test eligibility checks (soft constraints)
  - [ ] Test expiration tracking
  - [ ] Test slot-type invariant validation
  - [ ] Test penalty calculations
  - [ ] Test grace period handling

- [ ] `tests/services/test_claude_service.py` (3h)
  - [ ] Test stream_task() success
  - [ ] Test stream_task() with API error
  - [ ] Test execute_task() success
  - [ ] Test execute_task() error handling
  - [ ] Test _build_system_prompt() for each action type
  - [ ] Test _build_user_message()
  - [ ] Mock Anthropic API calls

## Phase 2: Business Logic Services (Week 2) - 40 hours

### Batch & Workflow (8 hours)

- [ ] `tests/services/batch/test_batch_service.py` (4h)
  - [ ] Test batch processing
  - [ ] Test transaction management
  - [ ] Test rollback handling
  - [ ] Test error aggregation
  - [ ] Test atomicity guarantees

- [ ] `tests/services/test_workflow_service.py` (4h)
  - [ ] Test state machine transitions
  - [ ] Test validation rules
  - [ ] Test workflow orchestration

### Export Services (8 hours)

- [ ] `tests/services/export/test_csv_exporter.py` (2h)
  - [ ] Test CSV generation
  - [ ] Test encoding
  - [ ] Test special characters

- [ ] `tests/services/export/test_json_exporter.py` (2h)
  - [ ] Test JSON formatting
  - [ ] Test nested structures
  - [ ] Test date serialization

- [ ] `tests/services/export/test_xml_exporter.py` (2h)
  - [ ] Test XML structure
  - [ ] Test schema validation

- [ ] `tests/services/export/test_export_factory.py` (2h)
  - [ ] Test format selection
  - [ ] Test factory pattern

### Specialized Services (15 hours)

- [ ] `tests/services/test_embedding_service.py` (3h)
  - [ ] Test embedding generation
  - [ ] Test similarity search
  - [ ] Test vector storage

- [ ] `tests/services/test_idempotency_service.py` (3h)
  - [ ] Test duplicate detection
  - [ ] Test request fingerprinting
  - [ ] Test cache management
  - [ ] Test TTL behavior

- [ ] `tests/services/test_certification_service.py` (2h)
  - [ ] Test certification tracking
  - [ ] Test expiration warnings

- [ ] `tests/services/test_procedure_service.py` (2h)
  - [ ] Test procedure logging
  - [ ] Test volume tracking

- [ ] `tests/services/test_freeze_horizon_service.py` (2h)
  - [ ] Test freeze date validation
  - [ ] Test schedule locking

- [ ] `tests/services/test_unified_heatmap_service.py` (3h)
  - [ ] Test heatmap generation
  - [ ] Test aggregation logic
  - [ ] Test color mapping

### Critical Routes (9 hours)

- [ ] `tests/routes/test_admin_users.py` (2h) ⚠️
  - [ ] Test user management endpoints
  - [ ] Test permission checks

- [ ] `tests/routes/test_call_assignments.py` (2h)
  - [ ] Test call scheduling endpoints
  - [ ] Test equity validation

- [ ] `tests/routes/test_claude_chat.py` (2h)
  - [ ] Test streaming endpoints
  - [ ] Test WebSocket connection

- [ ] `tests/routes/test_fatigue_risk.py` (2h)
  - [ ] Test FRMS endpoints
  - [ ] Test risk calculation

- [ ] `tests/routes/test_ws.py` (1h)
  - [ ] Test WebSocket protocol
  - [ ] Test message handling

## Phase 3: Infrastructure & Polish (Week 3) - 30 hours

### Report Generation (8 hours)

- [ ] `tests/services/reports/test_pdf_generator.py` (2h)
  - [ ] Test PDF generation
  - [ ] Test formatting
  - [ ] Test template rendering

- [ ] `tests/services/reports/test_analytics_report.py` (2h)
  - [ ] Test metrics calculation
  - [ ] Test chart generation

- [ ] `tests/services/reports/test_faculty_summary_report.py` (2h)
  - [ ] Test faculty-specific metrics
  - [ ] Test aggregation

- [ ] `tests/services/reports/test_schedule_report.py` (2h)
  - [ ] Test schedule formatting
  - [ ] Test ACGME compliance summary

### Infrastructure Services (12 hours)

- [ ] `tests/services/job_monitor/test_celery_monitor.py` (2h)
  - [ ] Test job status tracking
  - [ ] Test Celery integration

- [ ] `tests/services/job_monitor/test_job_history.py` (1h)
  - [ ] Test history tracking
  - [ ] Test cleanup

- [ ] `tests/services/job_monitor/test_job_stats.py` (1h)
  - [ ] Test statistics calculation
  - [ ] Test aggregation

- [ ] `tests/services/search/test_backends.py` (3h)
  - [ ] Test search backends
  - [ ] Test index management

- [ ] `tests/services/search/test_indexer.py` (2h)
  - [ ] Test indexing logic
  - [ ] Test update handling

- [ ] `tests/services/upload/test_processors.py` (2h)
  - [ ] Test file processing
  - [ ] Test validation

- [ ] `tests/services/upload/test_storage.py` (1h)
  - [ ] Test storage abstraction
  - [ ] Test file operations

### Remaining Routes (5 hours)

- [ ] `tests/routes/test_exotic_resilience.py` (2h)
  - [ ] Test advanced resilience metrics

- [ ] `tests/routes/test_game_theory.py` (2h)
  - [ ] Test Shapley value endpoints
  - [ ] Test fairness calculations

- [ ] `tests/routes/test_qubo_templates.py` (1h)
  - [ ] Test QUBO template management

### Coverage Polish (5 hours)

- [ ] Increase edge case coverage in existing tests
- [ ] Add integration tests for critical paths
- [ ] Fix any coverage gaps identified by reports
- [ ] Document any uncovered edge cases

## Coverage Milestones

- [ ] Baseline coverage measured (currently estimated ~21%)
- [ ] Phase 1 complete: 45% coverage ✓
- [ ] Phase 2 complete: 65% coverage ✓
- [ ] Phase 3 complete: 80% coverage ✓

## Documentation Updates

- [ ] Update TEST_COVERAGE_ANALYSIS.md with actual coverage numbers
- [ ] Document testing patterns in CLAUDE.md
- [ ] Create test fixture documentation
- [ ] Update CI/CD configuration for coverage gates

## Quality Gates

- [ ] All new tests pass
- [ ] Coverage threshold enforced in CI (80% minimum)
- [ ] No skipped tests in critical paths
- [ ] All async tests use proper pytest-asyncio markers
- [ ] All tests use proper fixtures (no hardcoded test data)
- [ ] Mock external dependencies (DB, Redis, APIs)

---

**Progress Tracking:**
- Phase 1: 0/10 controllers, 0/5 critical services
- Phase 2: 0/4 batch, 0/4 export, 0/6 specialized, 0/5 routes
- Phase 3: 0/4 reports, 0/3 infrastructure, 0/3 routes

**Last Updated:** 2025-12-30
**Target Completion:** Week of 2025-01-20
