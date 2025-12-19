# Parallel 25 Terminals Work Plan

> **Date:** 2025-12-19
> **Branch:** `claude/plan-parallel-work-Rubnh`
> **Purpose:** Coordinate 25 parallel work terminals without interference
> **Context:** Scheduling tool only - NO patient data (MyEvaluations handles ACGME/DoD/DHA compliance)

---

## Executive Summary

This is a **scheduling offload tool** - no PHI, no patient data. MyEvaluations handles all compliance-related data. Priorities focus on:

1. **Developer Productivity** - GitHub Actions, autonomous workflows
2. **Performance** - Docker optimization, CI speed, image sizes
3. **Code Quality** - Hook refactoring, testing, documentation
4. **Feature Development** - MCP server for scheduling domain

---

## Refactored Priority Tiers

### Tier 1: Immediate Value (Do First)
| Terminal | Task | Impact |
|----------|------|--------|
| 4 | GitHub Actions Design | Autonomous workflow foundation |
| 23 | GitHub Actions Implementation | Immediate automation |
| 1 | Gordon AI - Performance Focus | Docker optimization |
| 11-13 | Frontend Hook Refactoring (Auth, Schedule, Swaps) | Code quality |

### Tier 2: High Value (Do Second)
| Terminal | Task | Impact |
|----------|------|--------|
| 3 | MCP Server Specification | AI integration foundation |
| 16 | Swap Marketplace Tests | Core feature coverage |
| 20 | Constraint Service Tests | Backend stability |
| 8 | API Design Documentation | Developer onboarding |

### Tier 3: Medium Value (Do Third)
| Terminal | Task | Impact |
|----------|------|--------|
| 2 | FastMCP Research | MCP implementation prep |
| 14-15 | Hook Refactoring (Absences, People) | Code organization |
| 17-19 | Feature Tests | Coverage expansion |
| 21-22 | Backend Tests | Service stability |

### Tier 4: Lower Priority (If Time Permits)
| Terminal | Task | Impact |
|----------|------|--------|
| 5 | Slack Integration | Future enhancement |
| 6 | Mobile App Research | v1.2.0 planning |
| 7, 9-10 | Documentation | Nice to have |
| 24-25 | Scripts, Alerts | Operational tooling |

---

## Interference Prevention Strategy

### File Ownership Matrix

| Terminal Group | Owned Directories/Files |
|----------------|------------------------|
| Research (1-6) | `docs/planning/research/` (new) |
| Documentation (7-10) | `docs/guides/`, `docs/architecture/` |
| Frontend Hooks (11-15) | `frontend/src/hooks/` (new files only) |
| Frontend Tests (16-19) | `frontend/__tests__/features/` |
| Backend Tests (20-22) | `backend/tests/unit/` (new files) |
| Infrastructure (23-25) | `.github/`, `scripts/`, `monitoring/` |

---

## Terminal Assignments

### Tier 1: Immediate Value

#### Terminal 1: Gordon AI - Performance & Optimization Focus
**Priority:** IMMEDIATE
**Files:** `docs/planning/research/GORDON_EVALUATION_RESULTS.md`
**Task:** Execute Gordon AI commands focused on performance optimization

**Gordon AI Questions (Reordered by Priority):**
```bash
# Performance & Image Size (HIGHEST PRIORITY)
docker ai "How can I reduce the size of my frontend Docker image?"
docker ai "How can I reduce the size of my backend Docker image?"
docker ai "Optimize my multi-stage builds for faster CI builds"
docker ai "What BuildKit features should I use for better caching?"
docker ai "Are there unnecessary layers in my Dockerfiles?"

# Resource Optimization
docker ai "Are my resource limits appropriate for FastAPI + Celery + PostgreSQL?"
docker ai "Review memory and CPU settings in docker-compose.prod.yml"
docker ai "How can I optimize Redis memory usage?"

# Compose Best Practices
docker ai "Review docker-compose.prod.yml for production best practices"
docker ai "Review network configuration in docker-compose.yml"
docker ai "Are my health check intervals optimal?"

# Troubleshooting Context
docker ai "What are common issues with Celery + Redis + PostgreSQL in Docker?"
docker ai "How should I debug container networking issues?"
docker ai "What logging configuration is recommended?"

# General Optimization
docker ai "Rate and optimize backend/Dockerfile for production"
docker ai "Rate and optimize frontend/Dockerfile for production"
docker ai "Rate nginx/Dockerfile configuration"
```

**Deliverables:**
- Image size reduction recommendations
- CI build speed improvements
- Resource optimization suggestions

---

#### Terminal 4: GitHub Actions Autonomous Workflow Design
**Priority:** IMMEDIATE
**Files:** `docs/planning/research/GITHUB_ACTIONS_DESIGN.md`
**Task:** Design complete GitHub Actions workflow for autonomous operations

**Workflow Components:**
1. **TODO Scanner Workflow** (daily)
   - Scan codebase for TODO comments
   - Create GitHub issues for new TODOs
   - Track resolution progress

2. **Autonomous PR Review** (on PR)
   - Run Claude Code on changed files
   - Comment review findings
   - Suggest improvements

3. **CI Optimization** (on push)
   - Parallel test execution
   - Cached dependency installation
   - Fast feedback loop

**Deliverables:**
- Complete workflow YAML designs
- GitHub Actions secret requirements
- CI optimization recommendations

---

#### Terminal 23: GitHub Actions Workflow Implementation
**Priority:** IMMEDIATE
**Files:** `.github/workflows/autonomous-tasks.yml` (NEW)
**Task:** Implement GitHub Actions for autonomous tasks

**Workflow Implementation:**
```yaml
name: Autonomous Tasks
on:
  schedule:
    - cron: '0 6 * * *'  # Daily at 6 AM UTC
  workflow_dispatch:

jobs:
  scan-todos:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Scan for TODO comments
        run: |
          grep -r "TODO" --include="*.py" --include="*.ts" --include="*.tsx" . > todos.txt || true
      - name: Create issues for new TODOs
        # Implementation details
```

**Deliverables:**
- Complete workflow file
- Documentation for secrets setup
- Testing procedure

---

#### Terminal 11: Create useAuth Hook Module
**Priority:** IMMEDIATE
**Files:** `frontend/src/hooks/useAuth.ts` (NEW)
**Task:** Extract authentication hooks to dedicated module

**Hooks to Extract:**
- `useAuth()`
- `useLogin()`
- `useLogout()`
- `useUser()`
- `usePermissions()`
- `useRole()`

**Deliverables:**
- New `useAuth.ts` file with extracted hooks
- Complete JSDoc documentation
- Unit tests in `frontend/__tests__/hooks/useAuth.test.ts`

---

#### Terminal 12: Create useSchedule Hook Module
**Priority:** IMMEDIATE
**Files:** `frontend/src/hooks/useSchedule.ts` (NEW)
**Task:** Extract schedule-related hooks to dedicated module

**Hooks to Extract:**
- `useSchedule()`
- `useScheduleList()`
- `useScheduleCreate()`
- `useScheduleUpdate()`
- `useScheduleValidate()`
- `useBlocks()`
- `useAssignments()`

**Deliverables:**
- New `useSchedule.ts` file
- JSDoc documentation
- Unit tests

---

#### Terminal 13: Create useSwaps Hook Module
**Priority:** IMMEDIATE
**Files:** `frontend/src/hooks/useSwaps.ts` (NEW)
**Task:** Extract swap marketplace hooks to dedicated module

**Hooks to Extract:**
- `useSwapRequest()`
- `useSwapList()`
- `useSwapApprove()`
- `useSwapReject()`
- `useSwapCandidates()`
- `useAutoMatch()`

**Deliverables:**
- New `useSwaps.ts` file
- JSDoc documentation
- Unit tests

---

### Tier 2: High Value

#### Terminal 3: MCP Server Design Specification
**Priority:** HIGH
**Files:** `docs/planning/research/MCP_SERVER_SPECIFICATION.md`
**Task:** Design complete MCP server specification for scheduling domain

**Design Elements:**
1. **Resources to Expose:**
   - `schedule://current` - Current academic year schedule
   - `schedule://person/{id}` - Individual person schedules
   - `schedule://blocks` - Block definitions
   - `resilience://health` - System health status
   - `analytics://fairness` - Fairness distribution metrics
   - `analytics://workload` - Workload metrics

2. **Tools to Implement:**
   - `validate_schedule` - Check schedule constraints
   - `check_swap_feasibility` - Pre-validate swap requests
   - `analyze_contingency` - N-1/N-2 vulnerability analysis
   - `suggest_resolution` - Conflict resolution suggestions
   - `generate_schedule` - Trigger schedule generation

3. **Authentication:**
   - JWT token validation (existing auth system)
   - Role-based resource access

**Deliverables:**
- Complete MCP server specification
- Resource schema definitions (JSON Schema)
- Tool interface definitions

---

#### Terminal 16: Swap Marketplace Feature Tests
**Priority:** HIGH
**Files:** `frontend/__tests__/features/swap-marketplace/`
**Task:** Write comprehensive tests for swap marketplace

**Test Coverage:**
- SwapRequestForm component tests
- SwapCard display tests
- AutoMatcher algorithm tests
- SwapApproval workflow tests
- Error handling tests

**Deliverables:**
- `swap-request.test.tsx`
- `swap-card.test.tsx`
- `auto-matcher.test.ts`
- `swap-workflow.test.tsx`

---

#### Terminal 20: Constraint Service Unit Tests
**Priority:** HIGH
**Files:** `backend/tests/unit/services/test_constraint_service.py` (NEW)
**Task:** Write unit tests for constraint validation service

**Test Coverage:**
- 80-hour rule validation
- 1-in-7 day off rule validation
- Supervision ratio validation
- Custom constraint validation
- Error handling

**Deliverables:**
- Comprehensive unit test file
- Edge case coverage
- Mock fixtures

---

#### Terminal 8: API Design Documentation
**Priority:** HIGH
**Files:** `docs/architecture/api-design.md`
**Task:** Document API design patterns and standards

**Sections:**
1. RESTful API conventions
2. Error response format (RFC 7807)
3. Authentication patterns
4. Rate limiting policies
5. Versioning strategy
6. Pagination standards

**Deliverables:**
- API design standards document
- Code examples for each pattern
- OpenAPI annotation guidelines

---

### Tier 3: Medium Value

#### Terminal 2: FastMCP Implementation Research
**Priority:** MEDIUM
**Files:** `docs/planning/research/FASTMCP_IMPLEMENTATION_PLAN.md`
**Task:** Deep dive into FastMCP 2.0 for MCP server implementation

**Research Questions:**
1. How does FastMCP handle authentication with existing JWT tokens?
2. Can FastMCP integrate with existing FastAPI routes?
3. What's the best approach for exposing read-only vs write resources?
4. How to handle async database operations in FastMCP tools?

**Deliverables:**
- Implementation architecture diagram
- Code scaffolding plan
- Integration test strategy

---

#### Terminal 14: Create useAbsences Hook Module
**Priority:** MEDIUM
**Files:** `frontend/src/hooks/useAbsences.ts` (NEW)
**Task:** Extract absence management hooks to dedicated module

**Hooks to Extract:**
- `useAbsence()`
- `useAbsenceList()`
- `useAbsenceCreate()`
- `useAbsenceApprove()`
- `useMilitaryLeave()`
- `useLeaveBalance()`

**Deliverables:**
- New `useAbsences.ts` file
- JSDoc documentation
- Unit tests

---

#### Terminal 15: Create usePeople Hook Module
**Priority:** MEDIUM
**Files:** `frontend/src/hooks/usePeople.ts` (NEW)
**Task:** Extract people management hooks to dedicated module

**Hooks to Extract:**
- `usePerson()`
- `usePeopleList()`
- `useResidents()`
- `useFaculty()`
- `usePersonUpdate()`
- `useCertifications()`

**Deliverables:**
- New `usePeople.ts` file
- JSDoc documentation
- Unit tests

---

#### Terminal 17: Analytics Dashboard Feature Tests
**Priority:** MEDIUM
**Files:** `frontend/__tests__/features/analytics/`
**Task:** Write tests for analytics dashboard

**Deliverables:**
- `fairness-chart.test.tsx`
- `workload-distribution.test.tsx`
- `compliance-metrics.test.tsx`

---

#### Terminal 18: Resilience Hub Feature Tests
**Priority:** MEDIUM
**Files:** `frontend/__tests__/features/resilience/`
**Task:** Write tests for resilience hub

**Deliverables:**
- `resilience-hub.test.tsx`
- `health-status.test.tsx`
- `contingency-analysis.test.tsx`

---

#### Terminal 19: Export Functionality Feature Tests
**Priority:** MEDIUM
**Files:** `frontend/__tests__/features/export/`
**Task:** Write tests for export functionality

**Deliverables:**
- `excel-export.test.tsx`
- `pdf-export.test.tsx`
- `ics-export.test.tsx`

---

#### Terminal 21: Notification Service Unit Tests
**Priority:** MEDIUM
**Files:** `backend/tests/unit/services/test_notification_service.py` (NEW)
**Task:** Write unit tests for notification service

**Deliverables:**
- Complete unit test file
- Mock Slack/email providers
- Template fixtures

---

#### Terminal 22: Analytics Service Unit Tests
**Priority:** MEDIUM
**Files:** `backend/tests/unit/services/test_analytics_service.py` (NEW)
**Task:** Write unit tests for analytics service

**Deliverables:**
- Complete unit test file
- Sample data fixtures
- Performance benchmarks

---

### Tier 4: Lower Priority

#### Terminal 5: Slack Integration Architecture
**Priority:** LOW
**Files:** `docs/planning/research/SLACK_INTEGRATION_ARCHITECTURE.md`
**Task:** Design Slack bot integration for natural language coding requests

**Deliverables:**
- Architecture diagram
- Slack App manifest
- Message flow documentation

---

#### Terminal 6: Mobile App Architecture Research
**Priority:** LOW
**Files:** `docs/planning/research/MOBILE_APP_ARCHITECTURE.md`
**Task:** Research React Native/Expo architecture for mobile app

**Research Areas:**
1. Expo managed vs bare workflow
2. Offline-first data synchronization
3. Push notification infrastructure
4. Biometric authentication patterns

**Deliverables:**
- Technology recommendation
- Architecture proposal

---

#### Terminal 7: Installation Guide Modernization
**Priority:** LOW
**Files:** `docs/guides/installation.md`
**Task:** Create comprehensive installation guide

**Deliverables:**
- Complete installation guide
- Troubleshooting FAQ

---

#### Terminal 9: Scheduling Workflow Guide
**Priority:** LOW
**Files:** `docs/guides/scheduling-workflow.md`
**Task:** Document complete scheduling workflow

**Deliverables:**
- Step-by-step workflow guide
- Decision flowcharts

---

#### Terminal 10: Contributing Guide Enhancement
**Priority:** LOW
**Files:** `docs/development/contributing.md`
**Task:** Create comprehensive contributor guide

**Deliverables:**
- Complete contributing guide
- PR/Issue templates

---

#### Terminal 24: Docker AI Check Script
**Priority:** LOW
**Files:** `scripts/docker-ai-check.sh` (NEW)
**Task:** Create helper script for Gordon AI analysis

**Deliverables:**
- Complete script file
- Usage documentation

---

#### Terminal 25: Prometheus Alert Rule Review
**Priority:** LOW
**Files:** `monitoring/prometheus/alert_rules_reviewed.yml` (NEW)
**Task:** Review and enhance Prometheus alert rules

**Deliverables:**
- Enhanced alert rules file
- Alert documentation

---

## Gordon AI Priority Questions (Refactored)

**Focus: Performance & Developer Experience (NOT Security/HIPAA)**

### Image Size & Build Speed (HIGHEST)
1. `docker ai "How can I reduce the size of my frontend Docker image?"`
2. `docker ai "How can I reduce the size of my backend Docker image?"`
3. `docker ai "Optimize multi-stage builds for faster CI builds"`
4. `docker ai "What BuildKit features improve caching?"`

### Resource Optimization
5. `docker ai "Are resource limits appropriate for FastAPI + Celery?"`
6. `docker ai "How can I optimize Redis memory usage?"`
7. `docker ai "Review health check intervals for optimization"`

### Best Practices
8. `docker ai "Review docker-compose.prod.yml for best practices"`
9. `docker ai "What logging configuration is recommended?"`
10. `docker ai "Common issues with Celery + Redis + PostgreSQL?"`

---

## Recommended Execution Order

### Wave 1 (Immediate - Start All)
Terminals: 1, 4, 11, 12, 13, 23
**Focus:** GitHub Actions + Core Hook Refactoring + Docker Optimization

### Wave 2 (After Wave 1 Designs Complete)
Terminals: 3, 8, 16, 20
**Focus:** MCP Design + API Docs + Core Tests

### Wave 3 (Parallel with Wave 2)
Terminals: 2, 14, 15, 17, 18, 19, 21, 22
**Focus:** Research + Remaining Hooks + Remaining Tests

### Wave 4 (If Time Permits)
Terminals: 5, 6, 7, 9, 10, 24, 25
**Focus:** Future planning + Documentation + Scripts

---

## Git Strategy

### Branch Management
All terminals commit to: `claude/plan-parallel-work-Rubnh`

### Commit Message Convention
```
<terminal>: <action> <component>

Terminal-01: research Gordon AI performance optimization
Terminal-11: add useAuth hook module
Terminal-23: implement autonomous GitHub Actions workflow
```

---

## Success Criteria

### Tier 1 (Must Complete)
- [ ] GitHub Actions workflow functional
- [ ] Gordon AI optimization recommendations documented
- [ ] 3 core hook modules created (Auth, Schedule, Swaps)

### Tier 2 (Should Complete)
- [ ] MCP server specification ready for implementation
- [ ] Swap marketplace test coverage > 80%
- [ ] API design documentation complete

### Tier 3 (Nice to Have)
- [ ] All hook modules created
- [ ] All feature tests written
- [ ] Backend service tests complete

---

*Generated: 2025-12-19*
*Refactored: Removed HIPAA focus, prioritized developer productivity and performance*
