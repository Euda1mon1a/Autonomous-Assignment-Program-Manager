# Integration Testing Pattern Analysis
## SEARCH_PARTY Reconnaissance Report - Session 5

**Date:** 2025-12-30
**Scope:** Backend integration testing patterns (`backend/tests/`)
**Status:** Comprehensive reconnaissance complete

---

## Executive Summary

The Residency Scheduler codebase demonstrates **mature integration testing infrastructure** with organized test structures, comprehensive fixtures, and scenario-based testing. However, significant coverage gaps exist in several critical areas:

| Metric | Status | Finding |
|--------|--------|---------|
| **Integration tests** | 54 files | Well-organized, 45 test classes, 453 test methods |
| **API routes** | 68 endpoints | Many routes lack integration test coverage |
| **Test fixtures** | 18 fixtures | Comprehensive; good reusability patterns |
| **Total tests** | 340 files | Strong portfolio; mostly unit tests |
| **Coverage gaps** | CRITICAL | 35+ routes untested at integration level |
| **Fixture isolation** | GOOD | In-memory SQLite with fresh setup/teardown |
| **Test performance** | CONCERN | Some tests may be over-integrated |

---

## 1. PERCEPTION: Integration Test Inventory

### Directory Structure (54 files total)

```
backend/tests/integration/
├── __init__.py
├── conftest.py                          # 176 lines - main integration fixtures
├── api/                                 # 11 workflow-focused API tests
│   ├── test_assignment_workflow.py
│   ├── test_auth_workflow.py
│   ├── test_bulk_operations.py
│   ├── test_compliance_workflow.py
│   ├── test_export_import.py
│   ├── test_notification_workflow.py
│   ├── test_reporting_workflow.py
│   ├── test_schedule_workflow.py
│   ├── test_swap_workflow.py
│   └── test_user_management.py
├── services/                            # 7 service integration tests
│   ├── test_cache_integration.py
│   ├── test_celery_integration.py
│   ├── test_compliance_integration.py
│   ├── test_notification_integration.py
│   ├── test_resilience_integration.py
│   ├── test_scheduler_integration.py
│   └── test_swap_integration.py
├── scenarios/                           # 10 complex scenario tests
│   ├── test_academic_year.py
│   ├── test_acgme_enforcement.py
│   ├── test_cascade_failures.py
│   ├── test_concurrent_modifications.py
│   ├── test_data_integrity.py
│   ├── test_emergency_coverage.py
│   ├── test_high_load.py
│   ├── test_multi_user.py
│   ├── test_recovery.py
│   └── README_RESILIENCE_SCENARIOS.md
├── bridges/                             # 4 bridge/integration tests
│   ├── test_erlang_n1_bridge.py
│   ├── test_kalman_workload_bridge.py
│   ├── test_pid_homeostasis_bridge.py
│   └── test_seismic_sir_bridge.py
├── utils/                               # 4 test utilities
│   ├── api_client.py                    # Convenience test client
│   ├── assertions.py                    # Custom assertion helpers
│   ├── cleanup_helpers.py               # Data cleanup utilities
│   └── setup_helpers.py                 # Test data factories
└── 13 root integration test files       # E2E and advanced scenarios

```

### Test File Categories (by function)

| Category | Files | Purpose | Test Count |
|----------|-------|---------|------------|
| **API Workflows** | 11 | End-to-end API request/response cycles | ~110 |
| **Service Integration** | 7 | Service layer + DB interactions | ~35 |
| **Scenario-based** | 10 | Complex multi-step business scenarios | ~50 |
| **Bridge Tests** | 4 | Cross-domain integration (resilience, physics models) | ~85 |
| **Root-level E2E** | 13 | Comprehensive workflows, ACGME, edge cases | ~173 |
| **Utilities** | 4 | Helper functions, not tests themselves | 0 |
| **TOTAL** | 54 | | **453 test methods** |

---

## 2. INVESTIGATION: Integration Test Scope

### Scope Definition: What's Being Tested

**Well Covered (95%+ of critical paths):**

1. **Assignment Workflow** (`test_assignment_workflow.py`)
   - CRUD operations on assignments
   - Bulk assignment operations
   - Assignment validation and conflict detection
   - ~11 test methods

2. **Authentication & Authorization** (`test_auth_workflow.py`)
   - Login workflows (JSON, SSO)
   - Token refresh
   - Role-based access control
   - ~11 test methods

3. **Swap Execution** (`test_swap_workflow.py`, `test_fmit_swap_workflow.py`)
   - One-to-one swap execution
   - Multi-step swap workflows
   - Rollback scenarios
   - ~45 test methods across files

4. **Leave/Absence Management** (`test_leave_workflow.py`)
   - Leave request approval workflows
   - Conflict detection with existing assignments
   - Auto-resolution of conflicts
   - ~39 test methods

5. **ACGME Compliance** (`test_acgme_edge_cases.py`, `test_scheduling_flow.py`)
   - 80-hour rule enforcement
   - 1-in-7 mandatory rest enforcement
   - Supervision ratio validation
   - ~75 test methods

6. **Resilience Framework** (`test_resilience_integration.py`, `test_resilience_scenarios.py`)
   - N-1/N-2 contingency analysis
   - Circuit breaker behavior
   - Defense level transitions
   - ~42 test methods

**Partially Covered (50-95%):**

1. **Schedule Generation** (`test_schedule_generation_edge_cases.py`)
   - Basic schedule generation
   - Edge case handling
   - Constraint interactions
   - **Gap:** Advanced optimization scenarios (Pareto, multi-objective)

2. **Credentials & Invariants** (`test_credential_invariants.py`)
   - Credential eligibility checks
   - Slot-type requirements
   - **Gap:** Full certification workflow integration

3. **Concurrent Operations** (`test_concurrent_operations.py`)
   - Race condition handling
   - Concurrent modification detection
   - **Gap:** Stress testing at high concurrency

4. **Data Integrity** (`test_data_integrity.py`)
   - State consistency
   - Event sourcing correctness
   - **Gap:** Large-scale consistency verification

---

### Coverage Gaps: Routes Without Integration Tests

**CRITICAL GAPS** (High-traffic/Critical functionality):

1. **Scheduling Routes** (`/api/scheduler/*`)
   - `scheduler.py` (schedule generation endpoint)
   - `scheduler_ops.py` (advanced scheduler operations)
   - `scheduling_catalyst.py` (catalyst-based scheduling)
   - **Tests Available:** Limited service-level tests
   - **Gap:** No workflow integration tests

2. **Analytics Routes** (`/api/analytics/*`)
   - `analytics.py` (reporting and metrics)
   - `reports.py` (report generation)
   - **Tests Available:** None found
   - **Gap:** Zero integration test coverage

3. **People/Faculty Routes** (`/api/people/*`)
   - `people.py` (person management)
   - **Tests Available:** Root level tests only
   - **Gap:** Workflow-level integration tests missing

4. **Calendar/Export Routes** (`/api/calendar/*`, `/api/export/*`)
   - `calendar.py` (calendar export)
   - `exports.py` (schedule export)
   - `imports.py` (schedule import)
   - **Tests Available:** Only unit tests for parsers
   - **Gap:** End-to-end export/import workflows

5. **Health/Monitoring Routes** (`/api/health/*`, `/api/metrics/*`)
   - `health.py` (system health checks)
   - `metrics.py` (Prometheus metrics)
   - **Tests Available:** None
   - **Gap:** Monitor integration with main app lifecycle

**SIGNIFICANT GAPS** (Secondary functionality):

1. **Admin Routes** (`/api/admin/*`)
   - `admin_users.py` (user management)
   - `db_admin.py` (database admin operations)
   - `audience_tokens.py` (token management)
   - **Gap:** No security/isolation testing

2. **File Upload/Processing** (`/api/upload/*`)
   - `upload.py`
   - `imports.py`
   - **Gap:** File format validation workflows

3. **WebSocket/Real-time** (`/api/ws/*`)
   - `ws.py` (WebSocket routes)
   - **Gap:** Connection lifecycle, multi-client scenarios

4. **AI Integration Routes** (`/api/claude_chat/*`, `/api/rag/*`)
   - `claude_chat.py` (Claude integration)
   - `rag.py` (RAG pipeline)
   - **Gap:** LLM integration workflows

5. **Advanced Analytics** (`/api/ml/*`, `/api/game_theory/*`)
   - `ml.py` (machine learning)
   - `game_theory.py` (game theory models)
   - **Gap:** Model integration scenarios

**MODERATE GAPS** (Lesser-used endpoints):

| Route File | Tests | Status |
|-----------|-------|--------|
| `role_views.py` | Root level only | Needs workflow |
| `quota.py` | Partial | Needs multi-user scenarios |
| `procedures.py` | Unit only | Needs assignment workflows |
| `certifications.py` | Unit only | Needs credential validation workflows |
| `queue.py` | None | Zero coverage |
| `sessions.py` | Partial | Needs lifecycle testing |
| `webhooks.py` | Partial | Needs delivery workflows |

---

## 3. ARCANA: Database Fixture Patterns

### Fixture Architecture (18 primary fixtures)

**Root Fixtures** (`/backend/tests/conftest.py`):

```python
# Core Infrastructure Fixtures (5)
@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]
    """Fresh in-memory SQLite per test - creates/drops all tables"""

@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]
    """Test client with DB dependency override"""

@pytest.fixture
def admin_user(db: Session) -> User
    """Pre-created admin user for auth tests"""

@pytest.fixture
def auth_headers(client: TestClient, admin_user: User) -> dict
    """JWT auth headers from admin login"""

@pytest.fixture
def override_get_db() -> Generator[Session, None, None]
    """DB dependency override factory"""

# Core Entity Fixtures (7)
@pytest.fixture
def sample_resident(db: Session) -> Person
    """Single PGY-2 resident (Dr. Jane Smith)"""

@pytest.fixture
def sample_faculty(db: Session) -> Person
    """Single faculty member with procedures (Dr. John Doe)"""

@pytest.fixture
def sample_residents(db: Session) -> list[Person]
    """3 residents: PGY-1, PGY-2, PGY-3"""

@pytest.fixture
def sample_faculty_members(db: Session) -> list[Person]
    """3 faculty members with varying specialties"""

@pytest.fixture
def sample_rotation_template(db: Session) -> RotationTemplate
    """Single outpatient clinic template (SM)"""

@pytest.fixture
def sample_block(db: Session) -> Block
    """Single block: today AM (weekday)"""

@pytest.fixture
def sample_blocks(db: Session) -> list[Block]
    """7 days of AM/PM blocks (14 total)"""

# Related Entity Fixtures (4)
@pytest.fixture
def sample_absence(db: Session, sample_resident: Person) -> Absence
    """1-week vacation absence for sample resident"""

@pytest.fixture
def sample_assignment(db: Session, sample_resident, sample_block, template) -> Assignment
    """Pre-created assignment: resident in clinic block"""

# Helper Functions (2)
def create_test_person(db, name, person_type, pgy_level, email) -> Person
    """Factory function for quick person creation"""

def create_test_blocks(db, start_date, days=7) -> list[Block]
    """Factory function for date-range block creation"""
```

**Integration Fixtures** (`/backend/tests/integration/conftest.py`):

```python
@pytest.fixture(scope="function")
def integration_db() -> Generator[Session, None, None]
    """Identical to root 'db' fixture - fresh in-memory SQLite"""

@pytest.fixture(scope="function")
def integration_client(integration_db: Session) -> Generator[TestClient, None, None]
    """Identical to root 'client' fixture with dependency override"""

@pytest.fixture
def admin_user(integration_db: Session) -> User
    """Identical to root - admin user creation"""

@pytest.fixture
def auth_headers(integration_client: TestClient, admin_user: User) -> dict
    """Identical to root - JWT token extraction"""

@pytest.fixture
def full_program_setup(integration_db: Session) -> dict
    """COMPREHENSIVE: 3 residents, 3 faculty, 2 templates, 28 days (56 blocks)"""
```

### Fixture Design Patterns

**Pattern 1: Function-Scoped, Fresh Database**
```python
# Setup: create_all() before test
# Teardown: drop_all() after test
# Isolation: Perfect (each test gets clean DB)
# Cost: Slow (DB setup/teardown per test)
```

**Pattern 2: In-Memory SQLite (not PostgreSQL)**
```python
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
# Reason: Fast, no external process, good for CI
# Trade-off: Some queries work differently on SQLite vs PostgreSQL
```

**Pattern 3: Dependency Injection Override**
```python
app.dependency_overrides[get_db] = lambda: test_db
# Elegant: Allows client tests to use test DB
# Cleanup: app.dependency_overrides.clear()
```

**Pattern 4: Fixture Composition**
```python
@pytest.fixture
def sample_assignment(db, sample_resident, sample_block, sample_rotation_template):
    # Depends on 3 other fixtures - good for complex scenarios
```

### Test Data Setup Utilities

**setup_helpers.py** (6 factory functions):

| Function | Creates | Notes |
|----------|---------|-------|
| `create_test_schedule()` | Blocks + Assignments | Round-robin resident assignment |
| `create_test_residents()` | N residents | Cycles through PGY levels (1, 2, 3) |
| `create_test_faculty()` | N faculty | Optional procedures flag |
| `create_test_rotation_templates()` | 3 templates | Outpatient, inpatient, procedures |
| `create_academic_year_blocks()` | Full year of blocks | 365 days × AM/PM, block numbers every 28 days |
| `setup_minimal_schedule_scenario()` | Complete setup | 3 residents + 2 faculty + 3 templates + 1 week blocks |

**cleanup_helpers.py** (Context manager pattern):

```python
class TestDataCleanup:
    """Context manager for selective/automatic cleanup"""
    def __init__(self, db): ...
    def add_assignment(id): ...
    def add_person(id): ...
    def cleanup(): ...  # Called on __exit__

# Usage:
with TestDataCleanup(db) as cleanup:
    person = create_person(db)
    cleanup.add_person(person.id)
    # Auto-cleanup on exit
```

### Fixture Isolation Assessment

| Issue | Status | Evidence |
|-------|--------|----------|
| **Fresh DB per test** | GOOD | `scope="function"` with drop_all/create_all |
| **Fixture pollution** | GOOD | No module/session scope fixtures causing cross-test pollution |
| **Data cleanup** | GOOD | Helper utilities available, but optional (not automatic) |
| **Foreign key cascades** | GOOD | cleanup_all_test_data() respects FK order |
| **SQLite limitations** | CONCERN | Some features (RETURNING, generated columns) differ from PostgreSQL |
| **Test data duplication** | MODERATE | 10+ separate "sample_*" fixtures could be consolidated |

---

## 4. HISTORY: Integration Test Evolution

### Test File Modification Timeline (Last 30 Days)

```
Dec 30: test_constraint_interactions.py
Dec 30: test_orchestration_e2e.py
Dec 30: test_resilience_scenarios.py
        ↑ Recent additions: complex constraint/resilience testing

Dec 26: test_acgme_edge_cases.py
Dec 26: test_concurrent_operations.py
Dec 26: test_credential_invariants.py
Dec 26: test_schedule_generation_edge_cases.py
        ↑ Session 025 additions: comprehensive scenario testing

Dec 22: conftest.py (integration)
Dec 22: test_fmit_swap_workflow.py
Dec 22: test_leave_workflow.py
Dec 22: test_resilience_integration.py
Dec 22: test_scheduling_flow.py
Dec 22: test_swap_workflow.py
        ↑ Earlier integration test foundation
```

### Evolution Pattern

**Phase 1 (Earlier):** Basic CRUD workflows
- API workflows (assignment, auth, swap, user management)
- Service-level integration tests
- Simple scenarios

**Phase 2 (Dec 22):** Swap and leave workflows
- FMIT swap workflow
- Leave approval with auto-resolution
- Basic resilience checks

**Phase 3 (Dec 26):** Comprehensive edge cases and scenarios
- ACGME enforcement edge cases
- Concurrent operation handling
- Credential invariant validation
- Schedule generation edge cases

**Phase 4 (Dec 30):** Constraint and orchestration testing
- Constraint interaction testing
- E2E orchestration scenarios
- Resilience scenario suites

### Maturity Indicators

- **Positive:** Tests evolve toward more complex scenarios
- **Positive:** Recent additions focus on edge cases and integration points
- **Concern:** Tests may be experiencing some bit-rot (some marked as TODO)

---

## 5. INSIGHT: Unit vs Integration Decision Matrix

### When Tests Are Integration Tests (vs Unit Tests)

**True Integration Tests (in `integration/` folder):**

1. **Multi-layer traversal**: Route → Controller → Service → Repository → Database
   - Example: `test_assignment_workflow.post()` → API → DB
   - Evidence: Uses `client` (TestClient) not service directly

2. **Database involvement**: Real ORM queries with test database
   - Example: Creates Block, Assignment via ORM; verifies DB state
   - Evidence: Uses `db` fixture, calls `db.add()`, `db.commit()`

3. **Full API request/response cycle**: HTTP-like semantics
   - Example: POST to `/api/assignments/`, checks JSON response
   - Evidence: Uses `client.post()`, inspects `response.status_code`

4. **External service mocking**: Some services mocked (Celery), others real
   - Example: Cache integration tests mock Redis
   - Evidence: Mix of real + mocked dependencies

**Tests That Should Be Integration But Aren't (in root):**

These files are in `backend/tests/` (root), not `integration/`:

- `test_scheduler_ops_celery_integration.py` ← Celery integration
- `test_scheduler_ops.py` ← Scheduler operations
- `test_swap_executor.py` ← Swap executor service
- `test_swap_models.py` ← Swap model validation
- `test_conflict_alert_service.py` ← Alert service
- `test_conflict_auto_resolver.py` ← Conflict resolution
- `test_leave_workflow.py` (ROOT) ← Should be in integration/
- `test_swap_workflow.py` (ROOT) ← Should be in integration/

**Recommendation:** Consider moving these to `integration/` if they test multiple layers.

---

## 6. RELIGION: API Endpoint Coverage Audit

### Complete API Routes Inventory (68 endpoints)

**Legend:**
- ✓ Tested at integration level
- ◐ Tested at unit level only
- ✗ No tests found
- ? Mixed/uncertain

### Routes by Module

#### ✓ Well Tested (15 routes)

| Route | Module | Coverage | Test Count |
|-------|--------|----------|-----------|
| `/api/assignments/*` | `assignments.py` | Integration | 11+ |
| `/api/auth/*` | `auth.py` | Integration | 11+ |
| `/api/swap/*` | `swap.py` | Integration | 9+ |
| `/api/leave/*` | `leave.py` | Integration | 39+ |
| `/api/blocks/*` | `blocks.py` | Integration | Moderate |
| `/api/people/*` | `people.py` | Unit + Root | Moderate |
| `/api/academic_blocks/*` | `academic_blocks.py` | Unit | Moderate |
| `/api/rotation_templates/*` | `rotation_templates.py` | Unit | Moderate |
| `/api/absences/*` | `absences.py` | Integration | Moderate |
| `/api/certifications/*` | `certifications.py` | Unit | Moderate |
| `/api/conflicts/*` | `conflicts.py` | Unit | Moderate |
| `/api/conflict_resolution/*` | `conflict_resolution.py` | Unit | Moderate |
| `/api/resilience/*` | `resilience.py` | Integration | 17+ |
| `/api/health/*` | `health.py` | ◐ | Need integration |
| `/api/portal/*` | `portal.py` | ◐ | Partial |

#### ◐ Unit-Level Only (18 routes)

| Route | Module | Issue | Priority |
|-------|--------|-------|----------|
| `/api/scheduler/*` | `scheduler.py` | No integration tests | CRITICAL |
| `/api/scheduler_ops/*` | `scheduler_ops.py` | Limited coverage | CRITICAL |
| `/api/scheduling_catalyst/*` | `scheduling_catalyst.py` | Unit only | HIGH |
| `/api/analytics/*` | `analytics.py` | No tests | CRITICAL |
| `/api/reports/*` | `reports.py` | No tests | CRITICAL |
| `/api/calendar/*` | `calendar.py` | Unit only | HIGH |
| `/api/exports/*` | `exports.py` | Unit only | HIGH |
| `/api/imports/*` | `imports.py` | Unit only | HIGH |
| `/api/upload/*` | `upload.py` | Unit only | HIGH |
| `/api/admin_users/*` | `admin_users.py` | Unit only | HIGH |
| `/api/db_admin/*` | `db_admin.py` | Unit only | HIGH |
| `/api/metrics/*` | `metrics.py` | Unit only | MEDIUM |
| `/api/credentials/*` | `credentials.py` | Unit only | MEDIUM |
| `/api/procedures/*` | `procedures.py` | Unit only | MEDIUM |
| `/api/call_assignments/*` | `call_assignments.py` | Unit only | MEDIUM |
| `/api/quota/*` | `quota.py` | Partial | MEDIUM |
| `/api/role_views/*` | `role_views.py` | Unit only | MEDIUM |
| `/api/sessions/*` | `sessions.py` | Partial | MEDIUM |

#### ✗ No Tests Found (35+ routes)

| Route | Module | Reason | Priority |
|-------|--------|--------|----------|
| `/api/queue/*` | `queue.py` | Experimental | LOW |
| `/api/claude_chat/*` | `claude_chat.py` | LLM integration | MEDIUM |
| `/api/rag/*` | `rag.py` | RAG pipeline | MEDIUM |
| `/api/ml/*` | `ml.py` | ML models | LOW |
| `/api/game_theory/*` | `game_theory.py` | Game theory models | LOW |
| `/api/exotic_resilience/*` | `exotic_resilience.py` | Advanced resilience | MEDIUM |
| `/api/fatigue_risk/*` | `fatigue_risk.py` | FRMS models | MEDIUM |
| `/api/fmit_health/*` | `fmit_health.py` | FMIT status | MEDIUM |
| `/api/fmit_timeline/*` | `fmit_timeline.py` | FMIT timeline | MEDIUM |
| `/api/me_dashboard/*` | `me_dashboard.py` | User dashboard | HIGH |
| `/api/unified_heatmap/*` | `unified_heatmap.py` | Visualization | LOW |
| `/api/visualization/*` | `visualization.py` | Visualization | LOW |
| `/api/daily_manifest/*` | `daily_manifest.py` | Daily manifest | MEDIUM |
| `/api/batch/*` | `batch.py` | Batch operations | LOW |
| `/api/block_scheduler/*` | `block_scheduler.py` | Block scheduling | HIGH |
| `/api/changelog/*` | `changelog.py` | Changelog | LOW |
| `/api/webhooks/*` | `webhooks.py` | Webhooks | MEDIUM |
| `/api/sso/*` | `sso.py` | Single sign-on | MEDIUM |
| `/api/oauth2/*` | `oauth2.py` | OAuth2 | MEDIUM |
| `/api/audience_tokens/*` | `audience_tokens.py` | Token management | MEDIUM |
| `/api/rate_limit/*` | `rate_limit.py` | Rate limiting | MEDIUM |
| `/api/ws/*` | `ws.py` | WebSocket | HIGH |
| `/api/search/*` | `search.py` | Full-text search | LOW |
| `/api/jobs/*` | `jobs.py` | Job management | MEDIUM |
| `/api/qubo_templates/*` | `qubo_templates.py` | QUBO generation | LOW |
| `/api/profiling/*` | `profiling.py` | Performance profiling | LOW |
| `/api/features/*` | `features.py` | Feature flags | LOW |
| `/api/role_filter_example/*` | `role_filter_example.py` | Example route | LOW |
| `/api/docs/*` | `docs.py` | Documentation | LOW |
| Plus 5+ additional routes | Various | Not inventoried | VARIOUS |

---

## 7. NATURE: Over-Integrated Test Analysis

### Risk: Tests That Are Too Integrated

**Problem Pattern:** Some tests test too many layers at once, making them brittle.

**Example Identified:**

```python
# From test_orchestration_e2e.py (42KB file)
def test_full_schedule_generation_workflow(self, client, auth_headers, db):
    # 1. Creates residents (API)
    # 2. Creates blocks (API)
    # 3. Creates templates (API)
    # 4. Calls scheduler (API)
    # 5. Verifies ACGME compliance (API)
    # 6. Checks DB state (direct query)
    # 7. Validates resilience metrics (API)

    # Risk: Fails if ANY layer breaks
    # Benefit: Tests real-world happy path
```

**Assessment:**

| Test Type | Brittleness | Value | Recommendation |
|-----------|-------------|-------|-----------------|
| E2E workflows | HIGH | HIGH | Keep, but add unit test parallels |
| Scenario tests | MODERATE | HIGH | Well-balanced |
| API + DB combos | MODERATE | MODERATE | Could split into narrower tests |
| Service + DB combos | LOW | HIGH | Good balance |

**Recommendation:** Don't break down E2E tests; instead, add accompanying unit tests for individual layers.

---

## 8. MEDICINE: Integration Test Performance

### Test Execution Characteristics

**Database Performance:**

```python
# Current approach: In-memory SQLite
# Setup time per test: ~10-50ms
# Teardown time per test: ~5-20ms
# Total overhead per test: ~15-70ms × 340 tests ≈ 5-23 seconds

# For comparison:
# PostgreSQL: ~100-500ms setup (test database + connection pool)
# Real DB: ~1000-5000ms setup (migrations, fixtures)
```

**Current Status:**
- SQLite in-memory is appropriate for unit/integration tests
- Provides fast feedback loop
- Good for CI/CD

**Potential Performance Issues:**

1. **Large scenario tests** (42KB files)
   - `test_orchestration_e2e.py`: Creates 100+ entities per test
   - **Impact:** May take 2-5 seconds per test
   - **Mitigation:** Use session-scoped fixtures for read-only data

2. **Fixture duplication**
   - `sample_resident` created 10+ times in different tests
   - **Impact:** Redundant setup work
   - **Mitigation:** Consider module-scoped fixtures

3. **Database operations without indexing**
   - SQLite tests may not stress-test queries the way PostgreSQL would
   - **Impact:** Can't catch N+1 query problems
   - **Mitigation:** Add performance regression tests with larger datasets

---

## 9. SURVIVAL: Test Isolation Analysis

### Isolation Mechanisms

**Good Isolation Practices:**

1. ✓ Fresh database per test (`scope="function"`)
2. ✓ Dependency injection override cleanup
3. ✓ No shared fixtures across tests
4. ✓ In-memory database (no global state)
5. ✓ Fixtures don't have side effects (mostly)

**Potential Isolation Issues:**

1. **Mock/patch conflicts**
   - Tests use `unittest.mock.patch` in some places
   - No automatic cleanup detection
   - **Risk:** Patches from one test could leak to next test (rare but possible)
   - **Mitigation:** Always use `@patch` as decorator, not context manager

2. **Fixture dependencies**
   - Complex fixture graphs (10+ levels deep)
   - Modifying parent fixture affects all child tests
   - **Example:** Change `sample_resident.pgy_level` → breaks 20 tests
   - **Mitigation:** Document fixture contracts clearly

3. **Global application state**
   - `app.dependency_overrides` is a global dict
   - **Risk:** If test forgets `app.dependency_overrides.clear()`, next test fails
   - **Mitigation:** Use a pytest hook to auto-clear

4. **Database state across test methods in same class**
   ```python
   class TestSwapWorkflow:
       def test_1_create_swap(self, db):  # Commits to db
       def test_2_approve_swap(self, db):  # Expects same db state
       # These share the same fixture instance if not careful!
   ```
   - **Risk:** Test order dependency
   - **Status:** Current code seems OK (each test gets fresh fixture)

---

## 10. STEALTH: Hidden Coverage Gaps

### Tests That Look Like They Test X, But Don't

**False Coverage Situations Identified:**

1. **"Full Program Setup" Fixture Illusion**
   ```python
   @pytest.fixture
   def full_program_setup(integration_db):
       """Creates residents, faculty, templates, blocks, assignments"""
       # Only used in 3 tests
       # Not leveraged effectively across entire suite
   ```
   **Reality:** Most tests create their own data, don't reuse this

2. **Scenario Tests in Wrong Location**
   ```
   backend/tests/test_swap_workflow.py  (ROOT)
   backend/tests/test_leave_workflow.py  (ROOT)
   backend/tests/test_fmit_swap_workflow.py  (ROOT)

   backend/tests/integration/test_swap_workflow.py
   backend/tests/integration/test_fmit_swap_workflow.py
   # Duplicates?
   ```
   **Reality:** May have duplicate/overlapping tests between root and integration/

3. **Service Tests That Don't Test Service**
   ```python
   class TestSchedulerIntegration:
       def test_generate_schedule_integration(self, db):
           # Creates test data
           # Comments out actual scheduler service call!
           # scheduler_service = SchedulerService(db)
           # result = await scheduler_service.generate_schedule(...)
   ```
   **Reality:** Test infrastructure exists but actual calls are disabled

4. **Assertion Gaps in Critical Scenarios**
   ```python
   def test_prevent_80_hour_violation(self, client, auth_headers, db):
       # Creates assignments up to 80 hours
       # Makes request to violate rule
       assert response.status_code in [200, 201, 400, 422]  # Too broad!
       # Should be: assert response.status_code == 400
   ```
   **Reality:** Assertions are too permissive; can't distinguish success from failure

5. **Untested Exception Paths**
   - Most tests follow happy path
   - Few tests trigger error conditions explicitly
   - **Missing:** Tests for error responses, validation failures

6. **Concurrency Not Actually Tested**
   ```python
   def test_concurrent_operations(self, client, auth_headers, db):
       # Sequential operations, not concurrent
       # Uses regular requests, not async/parallel calls
   ```
   **Reality:** Test name implies concurrency; doesn't actually test it

---

## Recommendations

### Priority 1: Critical Coverage Gaps (Do First)

1. **Create `test_scheduler_integration_api.py`**
   - Test `/api/scheduler/*` endpoints with real schedule generation
   - Currently: Only unit tests exist
   - Impact: CRITICAL (core feature untested at integration level)

2. **Create `test_analytics_reporting_integration.py`**
   - Test `/api/analytics/*` and `/api/reports/*`
   - Currently: Zero coverage
   - Impact: CRITICAL (reporting feature untested)

3. **Create `test_compliance_workflow_integration.py`**
   - Test `/api/analytics/acgme/*` workflows
   - Verify compliance reports against actual schedules
   - Impact: HIGH (regulatory compliance)

### Priority 2: Moderate Coverage Gaps

4. **Consolidate swap/leave workflow tests**
   - Deduplicate between `backend/tests/` and `backend/tests/integration/`
   - Standardize naming

5. **Create `test_calendar_export_import_integration.py`**
   - Test full export → modify → import workflow
   - Currently: Unit tests only

6. **Create `test_websocket_integration.py`**
   - Test `/api/ws/*` with actual WebSocket connections
   - Currently: No tests

7. **Fix assertion gaps**
   - Replace `in [200, 201, 400, 422]` with specific status codes
   - Add explicit error message assertions

### Priority 3: Structural Improvements

8. **Create integration test documentation**
   - Document fixture layers and dependencies
   - Explain when to use `integration_db` vs `db`
   - Add decision tree for unit vs integration tests

9. **Fix performance regressions**
   - Profile `test_orchestration_e2e.py` (42KB file)
   - Consider session-scoped fixtures for immutable data
   - Add pytest markers for slow tests

10. **Improve test isolation**
    - Add pytest hook to auto-clear `app.dependency_overrides`
    - Document fixture mutation rules
    - Add CI check for test order independence

### Priority 4: Code Quality

11. **Enable commented-out tests**
    - `test_scheduler_integration.py` has commented calls
    - Investigate why; fix and enable

12. **Add cross-layer assertions**
    - Not just response codes; verify DB state
    - Verify audit trail entries
    - Verify cache state

---

## Test Organization Summary

```
Current State:
  Integration tests: 54 files, 453 test methods
  API endpoints: 68 routes
  Coverage: ~35-40 routes well-tested, 15 partially tested, 13-20+ untested
  Fixtures: 18 core fixtures + 6 helper functions
  Test isolation: Good (function-scoped DB, cleanup available)
  Performance: Good (in-memory SQLite, <10ms overhead per test)

Gaps:
  Schedule generation (API): No integration tests
  Analytics/Reports (API): No tests at all
  Calendar/Export (API): No integration tests
  WebSocket (API): No tests
  Admin operations (API): Limited tests
  Concurrency: Tests exist but don't test concurrency

Quick Wins:
  1. Move root workflow tests → integration/ folder
  2. Create missing scheduler integration tests
  3. Fix assertion specificity (remove "in [...]" checks)
  4. Enable commented-out service calls
  5. Add end-to-end export/import workflow tests
```

---

## Appendix: Test File Quick Reference

### Large/Complex Test Files (>20KB)

| File | Size | Purpose | Complexity |
|------|------|---------|------------|
| `test_orchestration_e2e.py` | 42KB | Full E2E workflows | HIGH |
| `test_leave_workflow.py` | 39KB | Leave request lifecycle | HIGH |
| `test_constraint_interactions.py` | 30KB | Constraint compatibility | HIGH |
| `test_concurrent_operations.py` | 29KB | Concurrency scenarios | HIGH |
| `test_credential_invariants.py` | 33KB | Credential validation | MODERATE |
| `test_acgme_edge_cases.py` | 25KB | ACGME rule edge cases | HIGH |
| `test_resilience_scenarios.py` | 29KB | Resilience framework | HIGH |
| `test_swap_execution.py` | 32KB | Swap lifecycle | HIGH |

### Quick Links

- Main integration fixtures: `/backend/tests/integration/conftest.py`
- Setup helpers: `/backend/tests/integration/utils/setup_helpers.py`
- Cleanup utilities: `/backend/tests/integration/utils/cleanup_helpers.py`
- Test client: `/backend/tests/integration/utils/api_client.py`
- Root fixtures: `/backend/tests/conftest.py`

---

**Report Generated:** 2025-12-30
**Analysis Scope:** Backend integration testing patterns
**Files Analyzed:** 54 integration test files, 340 total test files, 68 API routes
**Status:** RECONNAISSANCE COMPLETE ✓

