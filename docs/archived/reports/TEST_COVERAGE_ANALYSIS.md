# Backend Test Coverage Analysis - Session 025

**Date:** 2025-12-30
**Goal:** Increase coverage from 21% to 80%
**Current Status:** Unable to run pytest due to dependency conflicts (cryptography/cffi)

## Executive Summary

Based on static code analysis of the codebase structure:

- **Total Application Files:** 767
- **Total Service Files:** 81
- **Total Route Files:** 67
- **Total Controller Files:** 10
- **Test Files Found:** 234

### Coverage Estimates by Layer

| Layer | Files | With Tests | Without Tests | Coverage |
|-------|-------|------------|---------------|----------|
| **Routes** | 67 | 57 | 10 | **85.1%** |
| **Controllers** | 10 | 0 | 10 | **0.0%** ⚠️ |
| **Services** | 81 | 40 | 41 | **49.4%** |
| **Overall Estimate** | ~767 | ~300 | ~467 | **~39%** |

## Critical Gaps (Priority 1 - Must Fix)

### 1. Controllers - 0% Coverage ⚠️ CRITICAL

All 10 controllers lack tests. Controllers are the orchestration layer between routes and services.

**Missing Controller Tests:**
```
tests/controllers/
├── test_absence_controller.py          (MISSING)
├── test_assignment_controller.py       (MISSING)
├── test_auth_controller.py             (MISSING) ← Security critical
├── test_block_controller.py            (MISSING)
├── test_block_scheduler_controller.py  (MISSING)
├── test_call_assignment_controller.py  (MISSING)
├── test_certification_controller.py    (MISSING)
├── test_credential_controller.py       (MISSING)
├── test_person_controller.py           (MISSING)
└── test_procedure_controller.py        (MISSING)
```

**Impact:** High - Controllers orchestrate business logic
**Effort:** 20-30 hours (2-3 hours per controller)

### 2. Core Services - High Business Logic Complexity

**Top 10 Priority Services (by criticality):**

1. **`auth_service.py`** ⚠️ Security Critical
   - Authentication & registration logic
   - Token generation
   - User management
   - **Effort:** 4 hours
   - **Tests needed:** authenticate(), register_user(), token validation

2. **`academic_block_service.py`** - Large (578 lines)
   - Block matrix generation
   - ACGME compliance calculations
   - Rotation assignment logic
   - **Effort:** 6 hours
   - **Tests needed:** get_block_matrix(), ACGME validation, rotation assignment

3. **`calendar_service.py`** - Large (615 lines)
   - ICS calendar generation
   - Subscription management
   - Multi-person/rotation calendars
   - **Effort:** 5 hours
   - **Tests needed:** generate_ics_*(), subscription CRUD, token validation

4. **`claude_service.py`**
   - AI integration
   - Streaming task execution
   - System prompt generation
   - **Effort:** 3 hours
   - **Tests needed:** stream_task(), execute_task(), prompt building

5. **`credential_service.py`**
   - Credential management
   - Slot-type invariant validation
   - Expiration tracking
   - **Effort:** 4 hours
   - **Tests needed:** eligibility checks, expiration warnings, hard/soft constraints

6. **`batch/batch_service.py`**
   - Bulk operations
   - Transaction management
   - Rollback handling
   - **Effort:** 4 hours
   - **Tests needed:** batch processing, error handling, atomicity

7. **`embedding_service.py`**
   - RAG (Retrieval Augmented Generation)
   - Vector embeddings
   - Semantic search
   - **Effort:** 3 hours
   - **Tests needed:** embedding generation, similarity search

8. **`idempotency_service.py`**
   - Duplicate request detection
   - Request fingerprinting
   - Cache management
   - **Effort:** 3 hours
   - **Tests needed:** idempotency key validation, cache behavior

9. **`workflow_service.py`**
   - State machine transitions
   - Workflow orchestration
   - **Effort:** 4 hours
   - **Tests needed:** state transitions, validation rules

10. **`export/csv_exporter.py`** + **`export/json_exporter.py`** + **`export/xml_exporter.py`**
    - Data export in multiple formats
    - **Effort:** 3 hours (all three)
    - **Tests needed:** format validation, data integrity

## Moderate Priority (Priority 2)

### Services with Existing Partial Coverage

**Services to expand coverage:**

1. **`certification_service.py`** - Certification tracking
2. **`procedure_service.py`** - Procedure credentialing
3. **`freeze_horizon_service.py`** - Schedule freeze logic
4. **`game_theory.py`** - Shapley values, fairness calculations
5. **`unified_heatmap_service.py`** - Heatmap generation
6. **`faculty_outpatient_service.py`** - Faculty scheduling
7. **`cached_schedule_service.py`** - Caching layer
8. **`block_markdown.py`** - Markdown generation
9. **`role_view_service.py`** - RBAC view filtering

**Total Effort:** ~18 hours (2 hours each)

### Report Generation (PDF/Templates)

**Missing tests:**
```
tests/services/reports/
├── test_pdf_generator.py              (MISSING)
├── test_analytics_report.py           (MISSING)
├── test_compliance_report.py          (EXISTS)
├── test_faculty_summary_report.py     (MISSING)
└── test_schedule_report.py            (MISSING)
```

**Effort:** 8 hours (4 templates × 2 hours)

## Lower Priority (Priority 3)

### Infrastructure Services

1. **Job Monitor** (`job_monitor/*`)
   - Celery job monitoring
   - Job history tracking
   - **Effort:** 4 hours

2. **Search Infrastructure** (`search/*`)
   - Full-text search backends
   - Analyzers and indexers
   - **Effort:** 5 hours

3. **Upload Services** (`upload/*`)
   - File processors
   - Storage abstraction
   - **Effort:** 4 hours

4. **Leave Providers** (`leave_providers/*`)
   - CSV provider
   - Database provider
   - Factory pattern
   - **Effort:** 3 hours

## Routes Needing Tests

**10 routes without tests:**

1. **`admin_users.py`** - User administration (Security critical)
2. **`audience_tokens.py`** - Token management
3. **`call_assignments.py`** - Call scheduling
4. **`claude_chat.py`** - AI chat integration
5. **`exotic_resilience.py`** - Advanced resilience metrics
6. **`fatigue_risk.py`** - FRMS (Fatigue Risk Management)
7. **`game_theory.py`** - Game theory endpoints
8. **`qubo_templates.py`** - QUBO template management
9. **`role_filter_example.py`** - Example/demo route (low priority)
10. **`ws.py`** - WebSocket connections

**Effort:** 15 hours (1.5 hours per route)

## Test Implementation Roadmap

### Phase 1: Critical Infrastructure (Week 1) - 40 hours

**Priority: Security & Core Business Logic**

1. **Controller Layer** (20 hours)
   - `test_auth_controller.py` (3 hours) ⚠️
   - `test_person_controller.py` (2 hours)
   - `test_assignment_controller.py` (3 hours)
   - `test_block_controller.py` (2 hours)
   - `test_credential_controller.py` (2 hours)
   - `test_certification_controller.py` (2 hours)
   - `test_procedure_controller.py` (2 hours)
   - `test_call_assignment_controller.py` (2 hours)
   - `test_absence_controller.py` (2 hours)

2. **Critical Services** (20 hours)
   - `test_auth_service.py` (4 hours) ⚠️
   - `test_academic_block_service.py` (6 hours)
   - `test_calendar_service.py` (5 hours)
   - `test_credential_service.py` (4 hours)
   - `test_claude_service.py` (3 hours)

**Expected Coverage Increase:** 21% → 45% (+24%)

### Phase 2: Business Logic Services (Week 2) - 40 hours

**Priority: Service Layer Completion**

1. **Batch & Workflow** (8 hours)
   - `test_batch_service.py` (4 hours)
   - `test_workflow_service.py` (4 hours)

2. **Export & Import** (8 hours)
   - `test_csv_exporter.py` (2 hours)
   - `test_json_exporter.py` (2 hours)
   - `test_xml_exporter.py` (2 hours)
   - `test_export_factory.py` (2 hours)

3. **Specialized Services** (15 hours)
   - `test_embedding_service.py` (3 hours)
   - `test_idempotency_service.py` (3 hours)
   - `test_certification_service.py` (2 hours)
   - `test_procedure_service.py` (2 hours)
   - `test_freeze_horizon_service.py` (2 hours)
   - `test_unified_heatmap_service.py` (3 hours)

4. **Routes** (9 hours)
   - `test_admin_users.py` (2 hours) ⚠️
   - `test_call_assignments.py` (2 hours)
   - `test_claude_chat.py` (2 hours)
   - `test_fatigue_risk.py` (2 hours)
   - `test_ws.py` (1 hour)

**Expected Coverage Increase:** 45% → 65% (+20%)

### Phase 3: Infrastructure & Polish (Week 3) - 30 hours

**Priority: Remaining Gaps**

1. **Report Generation** (8 hours)
   - `test_pdf_generator.py` (2 hours)
   - `test_analytics_report.py` (2 hours)
   - `test_faculty_summary_report.py` (2 hours)
   - `test_schedule_report.py` (2 hours)

2. **Infrastructure Services** (12 hours)
   - `test_job_monitor.py` (4 hours)
   - `test_search_backends.py` (5 hours)
   - `test_upload_services.py` (4 hours)

3. **Remaining Routes** (5 hours)
   - `test_exotic_resilience.py` (2 hours)
   - `test_game_theory.py` (2 hours)
   - `test_qubo_templates.py` (1 hour)

4. **Expand Existing Tests** (5 hours)
   - Increase edge case coverage in existing tests
   - Add integration tests for critical paths

**Expected Coverage Increase:** 65% → 80% (+15%)

## Effort Summary

| Phase | Hours | Coverage Target | Key Deliverables |
|-------|-------|-----------------|------------------|
| Phase 1 | 40 | 21% → 45% | Controllers + Critical Services |
| Phase 2 | 40 | 45% → 65% | Service Layer + Routes |
| Phase 3 | 30 | 65% → 80% | Infrastructure + Polish |
| **Total** | **110 hours** | **21% → 80%** | **Comprehensive test suite** |

**Timeline:** 3 weeks (assumes 1 developer working 35-40 hours/week)

## Test Quality Guidelines

### For Each Test File

1. **Unit Tests** (primary focus)
   - Test each public method
   - Mock external dependencies (DB, Redis, external APIs)
   - Test error conditions and edge cases

2. **Integration Tests** (where appropriate)
   - Test interactions between layers
   - Use test database fixtures
   - Test critical paths end-to-end

3. **Coverage Requirements**
   - Minimum 80% line coverage per module
   - 100% coverage for security-critical code (auth, permissions)
   - All public API methods must have tests

### Example Test Structure

```python
"""Tests for [service/controller name]."""
import pytest
from unittest.mock import Mock, patch

from app.services.example_service import ExampleService


class TestExampleService:
    """Test suite for ExampleService."""

    @pytest.fixture
    def service(self, db):
        """Create service instance with test database."""
        return ExampleService(db)

    def test_method_success(self, service):
        """Test successful execution of method."""
        result = service.method()
        assert result.status == "success"

    def test_method_error_handling(self, service):
        """Test error handling in method."""
        with pytest.raises(ValueError, match="Expected error"):
            service.method(invalid_input)

    @pytest.mark.asyncio
    async def test_async_method(self, service):
        """Test async method execution."""
        result = await service.async_method()
        assert result is not None
```

## Blockers & Risks

### Technical Blockers

1. **Dependency Installation Failure** ⚠️
   - `cryptography` package conflict preventing pytest execution
   - Need to resolve system vs pip package conflicts
   - **Mitigation:** Use Docker container with clean environment

2. **Database Fixtures**
   - Many tests will require complex database fixtures
   - Need standardized fixture patterns
   - **Mitigation:** Create reusable fixture library in `tests/conftest.py`

3. **External Dependencies**
   - Services depend on Redis, Celery, external APIs
   - Need mocking strategy
   - **Mitigation:** Use `pytest-mock` and fixture patterns

### Risks

1. **Time Estimation**
   - Complex services may take longer than estimated
   - Unknown edge cases may emerge
   - **Mitigation:** Start with highest priority items, adjust plan weekly

2. **Breaking Changes**
   - Tests may reveal bugs in existing code
   - Fixes may require refactoring
   - **Mitigation:** Document bugs, create separate fix tickets

## Next Steps

1. **Immediate Actions**
   - ✅ Resolve dependency conflicts (cryptography/cffi)
   - ✅ Run pytest to get baseline coverage number
   - ✅ Create `tests/controllers/` directory structure

2. **Week 1 Setup**
   - Create test fixture library for common scenarios
   - Set up CI to enforce coverage thresholds
   - Begin Phase 1 implementation

3. **Ongoing**
   - Track coverage metrics daily
   - Review PRs for test quality
   - Update this document with actual coverage numbers

## Appendix: Quick Reference

### Services Needing Tests (Full List)

```
HIGH PRIORITY:
- auth_service.py
- academic_block_service.py
- calendar_service.py
- credential_service.py
- claude_service.py

MEDIUM PRIORITY:
- batch/batch_service.py
- batch/batch_processor.py
- batch/batch_validator.py
- embedding_service.py
- idempotency_service.py
- workflow_service.py
- certification_service.py
- procedure_service.py
- freeze_horizon_service.py
- game_theory.py
- unified_heatmap_service.py

LOW PRIORITY:
- export/csv_exporter.py
- export/json_exporter.py
- export/xml_exporter.py
- export/export_factory.py
- export/formatters.py
- reports/pdf_generator.py
- reports/templates/*.py
- job_monitor/*.py
- search/*.py
- upload/*.py
- leave_providers/*.py
- block_markdown.py
- cached_schedule_service.py
- faculty_outpatient_service.py
- role_view_service.py
- xlsx_export.py
```

### All Controllers Need Tests

```
- absence_controller.py
- assignment_controller.py
- auth_controller.py (CRITICAL)
- block_controller.py
- block_scheduler_controller.py
- call_assignment_controller.py
- certification_controller.py
- credential_controller.py
- person_controller.py
- procedure_controller.py
```

---

**Report Generated:** 2025-12-30
**Analysis Method:** Static code structure analysis
**Next Update:** After pytest execution with actual coverage metrics
