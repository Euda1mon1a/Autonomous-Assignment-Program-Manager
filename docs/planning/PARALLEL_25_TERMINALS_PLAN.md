# Parallel 25 Terminals Work Plan

> **Date:** 2025-12-18
> **Branch:** `claude/plan-parallel-work-Rubnh`
> **Purpose:** Coordinate 25 parallel work terminals without interference

---

## Executive Summary

This document outlines a strategy for executing 25 independent work streams in parallel. Each terminal is assigned a unique task that operates on distinct files/directories to ensure zero conflicts. Tasks are prioritized based on current project needs and strategic value.

---

## Interference Prevention Strategy

### Key Principles

1. **File Isolation**: Each terminal works on distinct files/directories
2. **No Shared Edits**: No two terminals modify the same file
3. **Git Safety**: Each terminal creates isolated commits
4. **Domain Separation**: Tasks grouped by domain to minimize overlap
5. **Coordination Points**: Defined handoff points where integration is needed

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

### Research & Evaluation (Terminals 1-6)

#### Terminal 1: Gordon AI Deep Evaluation
**Priority:** High
**Files:** `docs/planning/research/GORDON_EVALUATION_RESULTS.md`
**Task:** Execute Gordon AI commands on all Dockerfiles and compile results

**Gordon AI Questions to Ask:**
```bash
# Dockerfile Optimization
docker ai "Rate and optimize backend/Dockerfile for production use"
docker ai "Rate and optimize frontend/Dockerfile for production use"
docker ai "Rate and optimize nginx/Dockerfile"
docker ai "Rate and optimize load-tests/Dockerfile.k6"

# Security Analysis
docker ai "Check backend/Dockerfile for security vulnerabilities and CVE exposure"
docker ai "Scan for exposed secrets in my Docker configuration"
docker ai "What security improvements can I make to my containers for HIPAA compliance?"
docker ai "Are my non-root user configurations correct?"

# Compose Analysis
docker ai "Review docker-compose.prod.yml for production best practices"
docker ai "Are my resource limits appropriate for FastAPI + Celery + PostgreSQL?"
docker ai "Review network isolation in docker-compose.yml"

# Performance
docker ai "How can I reduce the size of my frontend image?"
docker ai "Optimize my multi-stage builds for faster CI builds"
docker ai "What BuildKit features could I use?"

# Troubleshooting Context
docker ai "What are common issues with Celery + Redis + PostgreSQL in Docker?"
docker ai "How should I debug networking issues between backend and db containers?"
```

**Deliverables:**
- Comprehensive results document
- Actionable recommendations list
- Security findings summary
- Size/performance metrics before/after

---

#### Terminal 2: FastMCP Implementation Research
**Priority:** Medium
**Files:** `docs/planning/research/FASTMCP_IMPLEMENTATION_PLAN.md`
**Task:** Deep dive into FastMCP 2.0 for MCP server implementation

**Research Questions:**
1. How does FastMCP handle authentication with existing JWT tokens?
2. Can FastMCP integrate with existing FastAPI routes?
3. What's the best approach for exposing read-only vs write resources?
4. How to handle async database operations in FastMCP tools?
5. Security model for PHI-sensitive resources

**Deliverables:**
- Implementation architecture diagram
- Code scaffolding plan
- Security considerations document
- Integration test strategy

---

#### Terminal 3: MCP Server Design Specification
**Priority:** High
**Files:** `docs/planning/research/MCP_SERVER_SPECIFICATION.md`
**Task:** Design complete MCP server specification for scheduling domain

**Design Elements:**
1. **Resources to Expose:**
   - `schedule://current` - Current academic year schedule
   - `schedule://person/{id}` - Individual person schedules
   - `compliance://acgme` - ACGME compliance metrics
   - `resilience://health` - System health status
   - `analytics://fairness` - Fairness distribution metrics

2. **Tools to Implement:**
   - `validate_schedule` - Check schedule for ACGME compliance
   - `check_swap_feasibility` - Pre-validate swap requests
   - `analyze_contingency` - N-1/N-2 vulnerability analysis
   - `suggest_resolution` - Conflict resolution suggestions

3. **Security Model:**
   - JWT token validation
   - Role-based resource access
   - PHI field filtering
   - Audit logging

**Deliverables:**
- Complete MCP server specification
- Resource schema definitions (JSON Schema)
- Tool interface definitions
- Security architecture document

---

#### Terminal 4: GitHub Actions Autonomous Workflow Design
**Priority:** Immediate
**Files:** `docs/planning/research/GITHUB_ACTIONS_DESIGN.md`
**Task:** Design complete GitHub Actions workflow for autonomous operations

**Workflow Components:**
1. **TODO Scanner Workflow** (daily)
   - Scan codebase for TODO comments
   - Create GitHub issues for new TODOs
   - Update existing issues with context

2. **Autonomous PR Review** (on PR)
   - Run Claude Code on changed files
   - Comment review findings
   - Suggest improvements

3. **Stale Issue Checker** (weekly)
   - Find stale issues
   - Add reminders or auto-close

**Deliverables:**
- Complete workflow YAML designs
- GitHub Actions secret requirements
- Branch protection rule recommendations
- Rollback/safety procedures

---

#### Terminal 5: Slack Integration Architecture
**Priority:** Medium
**Files:** `docs/planning/research/SLACK_INTEGRATION_ARCHITECTURE.md`
**Task:** Design Slack bot integration for natural language coding requests

**Architecture Components:**
1. **Slack Events API** - Listen for mentions
2. **Message Parser** - Extract intent using Claude
3. **GitHub Router** - Create issues/PRs from requests
4. **Response Handler** - Update Slack threads with progress

**Deliverables:**
- Architecture diagram
- Slack App manifest
- Required OAuth scopes
- Message flow documentation

---

#### Terminal 6: Mobile App Architecture Research
**Priority:** Low
**Files:** `docs/planning/research/MOBILE_APP_ARCHITECTURE.md`
**Task:** Research React Native/Expo architecture for mobile app

**Research Areas:**
1. Expo managed vs bare workflow
2. Offline-first data synchronization
3. Push notification infrastructure
4. Biometric authentication patterns
5. HIPAA compliance for mobile

**Deliverables:**
- Technology recommendation
- Architecture proposal
- Development timeline estimate
- Key technical risks

---

### Documentation Tasks (Terminals 7-10)

#### Terminal 7: Installation Guide Modernization
**Priority:** Medium
**Files:** `docs/guides/installation.md`
**Task:** Create comprehensive installation guide

**Sections:**
1. Prerequisites (OS, Docker, Node, Python versions)
2. Quick Start (Docker Compose)
3. Development Setup (manual)
4. Environment Configuration
5. Database Setup and Migrations
6. Troubleshooting Common Issues

**Deliverables:**
- Complete installation guide
- Troubleshooting FAQ
- Platform-specific notes (macOS, Linux, Windows)

---

#### Terminal 8: API Design Documentation
**Priority:** High
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

#### Terminal 9: Scheduling Workflow Guide
**Priority:** High
**Files:** `docs/guides/scheduling-workflow.md`
**Task:** Document complete scheduling workflow

**Sections:**
1. Schedule creation process
2. ACGME compliance validation
3. Conflict detection and resolution
4. Swap request workflow
5. Emergency coverage procedures
6. Resilience framework integration

**Deliverables:**
- Step-by-step workflow guide
- Decision flowcharts
- Common scenarios documentation

---

#### Terminal 10: Contributing Guide Enhancement
**Priority:** Medium
**Files:** `docs/development/contributing.md`
**Task:** Create comprehensive contributor guide

**Sections:**
1. Development environment setup
2. Code style guidelines
3. Testing requirements
4. PR review process
5. Commit message conventions
6. Release process

**Deliverables:**
- Complete contributing guide
- PR template updates
- Issue template updates

---

### Frontend Hook Refactoring (Terminals 11-15)

**Note:** These terminals create NEW files only. They do NOT modify `frontend/src/lib/hooks.ts`. A separate consolidation task will update imports and deprecate the old file.

#### Terminal 11: Create useAuth Hook Module
**Priority:** High
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
**Priority:** High
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
**Priority:** High
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

#### Terminal 14: Create useAbsences Hook Module
**Priority:** Medium
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
**Priority:** Medium
**Files:** `frontend/src/hooks/usePeople.ts` (NEW)
**Task:** Extract people/resident management hooks to dedicated module

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

### Frontend Feature Tests (Terminals 16-19)

#### Terminal 16: Swap Marketplace Feature Tests
**Priority:** High
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

#### Terminal 17: Analytics Dashboard Feature Tests
**Priority:** Medium
**Files:** `frontend/__tests__/features/analytics/`
**Task:** Write tests for analytics dashboard

**Test Coverage:**
- FairnessChart component tests
- WorkloadDistribution tests
- ComplianceMetrics tests
- Export functionality tests

**Deliverables:**
- `fairness-chart.test.tsx`
- `workload-distribution.test.tsx`
- `compliance-metrics.test.tsx`

---

#### Terminal 18: Resilience Hub Feature Tests
**Priority:** Medium
**Files:** `frontend/__tests__/features/resilience/`
**Task:** Write tests for resilience hub

**Test Coverage:**
- ResilienceHub dashboard tests
- HealthStatus indicator tests
- ContingencyAnalysis display tests
- Alert threshold tests

**Deliverables:**
- `resilience-hub.test.tsx`
- `health-status.test.tsx`
- `contingency-analysis.test.tsx`

---

#### Terminal 19: Export Functionality Feature Tests
**Priority:** Medium
**Files:** `frontend/__tests__/features/export/`
**Task:** Write tests for export functionality

**Test Coverage:**
- Excel export tests
- PDF export tests
- ICS calendar export tests
- Custom template tests

**Deliverables:**
- `excel-export.test.tsx`
- `pdf-export.test.tsx`
- `ics-export.test.tsx`

---

### Backend Tests (Terminals 20-22)

#### Terminal 20: Constraint Service Unit Tests
**Priority:** High
**Files:** `backend/tests/unit/services/test_constraint_service.py` (NEW)
**Task:** Write unit tests for constraint validation service

**Test Coverage:**
- ACGME 80-hour rule validation
- 1-in-7 day off rule validation
- Supervision ratio validation
- Custom constraint validation
- Error handling

**Deliverables:**
- Comprehensive unit test file
- Edge case coverage
- Mock fixtures

---

#### Terminal 21: Notification Service Unit Tests
**Priority:** Medium
**Files:** `backend/tests/unit/services/test_notification_service.py` (NEW)
**Task:** Write unit tests for notification service

**Test Coverage:**
- Notification creation
- Delivery channel selection
- Template rendering
- Batching logic
- Retry handling

**Deliverables:**
- Complete unit test file
- Mock email/Slack/push providers
- Template fixtures

---

#### Terminal 22: Analytics Service Unit Tests
**Priority:** Medium
**Files:** `backend/tests/unit/services/test_analytics_service.py` (NEW)
**Task:** Write unit tests for analytics service

**Test Coverage:**
- Fairness metric calculation
- Workload distribution analysis
- Trend calculation
- Report generation
- Cache invalidation

**Deliverables:**
- Complete unit test file
- Sample data fixtures
- Performance benchmarks

---

### Infrastructure (Terminals 23-25)

#### Terminal 23: GitHub Actions Workflow Implementation
**Priority:** Immediate
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
        # Claude API integration here
```

**Deliverables:**
- Complete workflow file
- Documentation for secrets setup
- Testing procedure

---

#### Terminal 24: Docker AI Check Script
**Priority:** Low
**Files:** `scripts/docker-ai-check.sh` (NEW)
**Task:** Create helper script for Gordon AI analysis

**Script Contents:**
```bash
#!/bin/bash
# Docker AI Check Script
# Runs Gordon AI analysis on all Dockerfiles

echo "=== Backend Dockerfile Analysis ==="
docker ai "Analyze backend/Dockerfile for optimization"

echo "=== Frontend Dockerfile Analysis ==="
docker ai "Analyze frontend/Dockerfile for optimization"

echo "=== Security Check ==="
docker ai "Check for security issues in Docker configuration"

echo "=== Compose Analysis ==="
docker ai "Review docker-compose.yml for best practices"
```

**Deliverables:**
- Complete script file
- Usage documentation
- Sample output

---

#### Terminal 25: Prometheus Alert Rule Review
**Priority:** Medium
**Files:** `monitoring/prometheus/alert_rules_reviewed.yml` (NEW)
**Task:** Review and enhance Prometheus alert rules

**Enhancement Areas:**
1. SLO-based alerts (latency, error rate, availability)
2. ACGME compliance alerts
3. Resilience framework alerts
4. Database performance alerts
5. Cache hit rate alerts

**Deliverables:**
- Enhanced alert rules file
- Alert documentation
- Runbook references

---

## Coordination Requirements

### Phase 1: Independent Work (Terminals 1-25)
All terminals work independently on assigned files. No coordination needed.

### Phase 2: Integration (After Initial Work)
1. **Hook Module Integration**: After Terminals 11-15 complete, update `frontend/src/lib/hooks.ts` to re-export from new modules
2. **Test Integration**: After Terminals 16-22 complete, run full test suite
3. **Documentation Review**: After Terminals 7-10 complete, cross-link documents

### Handoff Points

| From Terminal | To Terminal | Handoff Item |
|---------------|-------------|--------------|
| 1 (Gordon) | 24 (Script) | Verified commands |
| 2 (FastMCP) | 3 (MCP Design) | Research findings |
| 4 (GitHub Actions) | 23 (Implementation) | Design spec |
| 11-15 (Hooks) | Post-phase | Import consolidation |

---

## Git Strategy

### Branch Management
All terminals commit to: `claude/plan-parallel-work-Rubnh`

### Commit Message Convention
```
<terminal>: <action> <component>

Terminal-01: research Gordon AI Dockerfile analysis
Terminal-11: add useAuth hook module
Terminal-23: implement autonomous GitHub Actions workflow
```

### Merge Strategy
1. Each terminal creates atomic commits
2. All commits are reviewed together
3. Single PR merges all work

---

## Success Criteria

### Research Terminals (1-6)
- [ ] Comprehensive research documents
- [ ] Actionable recommendations
- [ ] Implementation-ready specifications

### Documentation Terminals (7-10)
- [ ] Complete, well-structured guides
- [ ] Cross-referenced documentation
- [ ] Up-to-date with current codebase

### Frontend Hooks (11-15)
- [ ] New hook modules created
- [ ] JSDoc documentation complete
- [ ] Unit tests passing

### Feature Tests (16-19)
- [ ] 80%+ coverage on target features
- [ ] All tests passing
- [ ] Edge cases covered

### Backend Tests (20-22)
- [ ] Unit tests for all service methods
- [ ] Mock fixtures created
- [ ] Documentation complete

### Infrastructure (23-25)
- [ ] Working GitHub Actions workflow
- [ ] Helper scripts functional
- [ ] Alert rules validated

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| File conflicts | Strict file ownership matrix |
| Incomplete work | Clear deliverable checklist |
| Integration failures | Post-work integration phase |
| Test failures | Run full suite after integration |
| Documentation drift | Cross-reference verification |

---

## Gordon AI Priority Questions

Based on the research document, these are the highest-priority questions to ask Gordon AI:

### Security (HIPAA Critical)
1. "What security improvements can I make to my containers for HIPAA compliance?"
2. "Check for exposed secrets in my Docker configuration"
3. "Are my non-root user configurations correct for security?"
4. "Scan my backend image for vulnerabilities using Docker Scout"

### Optimization (Performance)
5. "How can I reduce the size of my frontend Docker image?"
6. "Optimize my multi-stage builds for faster CI builds"
7. "What BuildKit features should I use for better caching?"

### Best Practices (Quality)
8. "Review docker-compose.prod.yml for production best practices"
9. "Are my resource limits appropriate for FastAPI + Celery?"
10. "Review my health check configurations"

### Troubleshooting (Operations)
11. "What are common issues with Celery + Redis + PostgreSQL in Docker?"
12. "How should I debug container networking issues?"
13. "What logging best practices should I follow?"

---

## Timeline

| Phase | Duration | Terminals |
|-------|----------|-----------|
| Parallel Work | 2-4 hours | All 25 |
| Integration | 1 hour | Coordination |
| Testing | 30 min | Full suite |
| Review | 30 min | Documentation |

**Total Estimated Time:** 4-6 hours

---

*Generated: 2025-12-18*
*Last Updated: 2025-12-18*
