# CORE - Skill Metadata and Routing

> **Purpose:** Central registry of all available skills and routing logic for skill selection
> **Version:** 1.0.0
> **Last Updated:** 2025-12-26

---

## I. PURPOSE

This CORE skill provides:
1. **Skill Registry**: Authoritative list of all available skills
2. **Routing Logic**: Rules for selecting appropriate skills based on task context
3. **Delegation Protocols**: When and how to invoke other skills or spawn subagents
4. **Progressive Disclosure**: Layered approach to skill activation

---

## II. AVAILABLE SKILLS

### A. Domain-Specific Skills

#### 1. ACGME Compliance (`acgme-compliance`)

**Purpose:** ACGME regulatory compliance expertise for medical residency scheduling

**Triggers:**
- Validating schedules against work hour limits
- Checking supervision ratios
- Investigating compliance violations
- Answering regulatory questions about ACGME rules

**Key Capabilities:**
- 80-hour rule validation (rolling 4-week average)
- 1-in-7 rule checking (24-hour free periods)
- Supervision ratio enforcement (PGY-1: 1:2, PGY-2/3: 1:4)
- Exception handling and variance tracking
- Integration with MCP validation tools

**Dependencies:** None (foundational skill)

**Example Invocation:**
```
Task: "Validate this schedule for ACGME compliance"
→ Activate: acgme-compliance
Reason: Direct ACGME validation request
```

---

#### 2. Schedule Optimization (`schedule-optimization`)

**Purpose:** Multi-objective schedule optimization using constraint programming

**Triggers:**
- Generating new schedules
- Improving coverage or balancing workloads
- Resolving scheduling conflicts
- Optimizing for fairness, continuity, or learning objectives

**Key Capabilities:**
- OR-Tools solver integration
- Pareto optimization for competing objectives
- Constraint hierarchy enforcement (Tier 1→4)
- Integration with resilience framework
- Coverage gap detection and resolution

**Dependencies:**
- `acgme-compliance` (for validation)
- `safe-schedule-generation` (for backup requirements)

**Example Invocation:**
```
Task: "Generate Q4 2025 schedule with balanced call distribution"
→ Activate: schedule-optimization
Reason: Schedule generation is core purpose of this skill
```

---

#### 3. Swap Management (`swap-management`)

**Purpose:** Schedule swap workflow expertise for faculty and resident exchanges

**Triggers:**
- Processing swap requests
- Finding compatible swap matches
- Validating swap feasibility
- Resolving scheduling conflicts via swaps

**Key Capabilities:**
- One-to-one and absorb swap types
- Auto-matching compatible candidates
- ACGME compliance preservation during swaps
- 24-hour rollback window management
- Integration with MCP swap tools

**Dependencies:**
- `acgme-compliance` (swap must maintain compliance)

**Example Invocation:**
```
Task: "Find faculty who can swap clinic day with Dr. Smith on 2025-03-15"
→ Activate: swap-management
Reason: Swap matching is core expertise
```

---

#### 4. Safe Schedule Generation (`safe-schedule-generation`)

**Purpose:** Safe schedule generation with mandatory database backup

**Triggers:**
- Generating any schedule that writes to database
- Bulk assignment operations
- Executing swap batches
- Any operation modifying assignment tables

**Key Capabilities:**
- Pre-generation database backup enforcement
- Rollback verification
- Backup integrity checking
- Recovery procedure documentation

**Dependencies:**
- `database-migration` (for backup/restore procedures)

**Example Invocation:**
```
Task: "Apply Block 10 schedule assignments to production database"
→ Activate: safe-schedule-generation
Reason: Writing to assignment table requires backup
```

---

#### 5. Schedule Verification (`schedule-verification`)

**Purpose:** Human verification checklist for generated schedules

**Triggers:**
- Reviewing newly generated schedules before approval
- Sanity-checking solver output
- Validating Block 10 or other critical schedules

**Key Capabilities:**
- Operational sense checking (FMIT, call, Night Float)
- Clinic day distribution review
- Absence handling verification
- Cross-rotation conflict detection

**Dependencies:**
- `acgme-compliance` (for regulatory checks)

**Example Invocation:**
```
Task: "Review Block 10 schedule for operational feasibility"
→ Activate: schedule-verification
Reason: Manual review checklist needed
```

---

### B. Security & Compliance Skills

#### 6. Security Audit (`security-audit`)

**Purpose:** Security-focused code audit for healthcare and military contexts

**Triggers:**
- Reviewing authentication or authorization code
- Checking data handling practices
- HIPAA compliance validation
- OPSEC/PERSEC review for military medical data

**Key Capabilities:**
- PHI handling review
- PERSEC checks (no names in repo)
- OPSEC validation (no operational patterns leaked)
- Authentication/authorization security
- Input validation and injection prevention

**Dependencies:** None (foundational skill)

**Example Invocation:**
```
Task: "Audit this new API endpoint for security vulnerabilities"
→ Activate: security-audit
Reason: Security review explicitly requested
```

---

### C. Development & Code Quality Skills

#### 7. Test Writer (`test-writer`)

**Purpose:** Test generation expertise for Python (pytest) and TypeScript (Jest)

**Triggers:**
- Writing new tests for untested code
- Improving test coverage below 80%
- Creating test fixtures
- Generating edge case tests

**Key Capabilities:**
- pytest patterns (fixtures, parametrize, async)
- Jest/React Testing Library patterns
- Edge case identification
- Error scenario coverage
- Integration test design

**Dependencies:** None (foundational skill)

**Example Invocation:**
```
Task: "Write tests for the new swap_executor service"
→ Activate: test-writer
Reason: Test generation is core purpose
```

---

#### 8. Code Review (`code-review`)

**Purpose:** Review generated code for bugs, security issues, performance, and best practices

**Triggers:**
- Reviewing Claude-generated code before commit
- Checking for security vulnerabilities
- Auditing implementation quality
- Validating code changes before PR

**Key Capabilities:**
- Security vulnerability detection
- Performance anti-pattern identification
- Best practice enforcement
- Architectural consistency checking
- Type safety validation

**Dependencies:**
- `security-audit` (for security-specific checks)

**Example Invocation:**
```
Task: "Review my changes to assignment_service.py before committing"
→ Activate: code-review
Reason: Code review explicitly requested
```

---

#### 9. Automated Code Fixer (`automated-code-fixer`)

**Purpose:** Automated detection and fixing of code issues

**Triggers:**
- Tests failing after changes
- Linting errors preventing commit
- Type-checking failures
- Security vulnerabilities detected

**Key Capabilities:**
- Auto-fix linting errors (Ruff, ESLint)
- Type error resolution
- Import organization
- Security vulnerability patching
- Enforces quality gates before accepting fixes

**Dependencies:**
- `lint-monorepo` (for unified linting)
- `test-writer` (if tests need fixing)

**Example Invocation:**
```
Task: "Fix the failing pytest tests in test_assignments.py"
→ Activate: automated-code-fixer
Reason: Test failure fixing is core purpose
```

---

#### 10. Code Quality Monitor (`code-quality-monitor`)

**Purpose:** Proactive code health monitoring and quality gate enforcement

**Triggers:**
- Validating code changes before commit
- Reviewing PRs for quality standards
- Enforcing coding standards
- Pre-merge quality checks

**Key Capabilities:**
- Coverage threshold enforcement (≥80%)
- Linting and type-checking validation
- Complexity metrics analysis
- Dependency vulnerability scanning
- Quality gate blocking

**Dependencies:**
- `code-review` (for detailed review)
- `automated-code-fixer` (for auto-fixes)

**Example Invocation:**
```
Task: "Check if this PR meets quality standards before merging"
→ Activate: code-quality-monitor
Reason: Quality gate validation needed
```

---

#### 11. Lint Monorepo (`lint-monorepo`)

**Purpose:** Unified linting and auto-fix for Python (Ruff) and TypeScript (ESLint)

**Triggers:**
- Fixing lint errors across codebase
- Running pre-commit checks
- Diagnosing persistent linting issues

**Key Capabilities:**
- Python linting with Ruff (fast, comprehensive)
- TypeScript/React linting with ESLint
- Auto-fix orchestration (fix first, then diagnose)
- Root-cause analysis for persistent issues
- Pre-commit hook integration

**Dependencies:** None (foundational skill)

**Example Invocation:**
```
Task: "Fix all linting errors in the backend"
→ Activate: lint-monorepo
Reason: Lint fixing is core purpose
```

---

#### 12. Systematic Debugger (`systematic-debugger`)

**Purpose:** Systematic debugging workflow for complex issues

**Triggers:**
- Encountering bugs with unclear root cause
- Test failures not immediately obvious
- Unexpected behavior in production
- Complex multi-system issues

**Key Capabilities:**
- Explore-plan-debug-fix workflow enforcement
- Prevents premature fixes
- Root cause analysis methodology
- Debugging runbook creation
- Pattern recognition for recurring issues

**Dependencies:**
- `test-writer` (for TDD debugging)
- `code-review` (for fix validation)

**Example Invocation:**
```
Task: "Debug why residents are being double-booked on overnight shifts"
→ Activate: systematic-debugger
Reason: Complex bug requiring systematic approach
```

---

### D. Infrastructure & Operations Skills

#### 13. Database Migration (`database-migration`)

**Purpose:** Database schema change and Alembic migration expertise

**Triggers:**
- Modifying database models
- Creating new migrations
- Handling rollbacks
- Troubleshooting migration issues

**Key Capabilities:**
- Alembic workflow guidance
- Migration autogeneration and review
- Rollback procedure verification
- Data integrity checks
- Backup/restore coordination

**Dependencies:**
- `safe-schedule-generation` (uses backup procedures)

**Example Invocation:**
```
Task: "Create migration to add middle_name field to Person model"
→ Activate: database-migration
Reason: Database schema change
```

---

#### 14. Docker Containerization (`docker-containerization`)

**Purpose:** Docker development and container orchestration expertise

**Triggers:**
- Creating or modifying Dockerfiles
- Updating docker-compose configurations
- Debugging container issues
- Optimizing image sizes

**Key Capabilities:**
- Dockerfile best practices
- Multi-stage builds
- Docker Compose orchestration
- Container debugging
- Security scanning integration

**Dependencies:** None (foundational skill)

**Example Invocation:**
```
Task: "Optimize the backend Docker image build time"
→ Activate: docker-containerization
Reason: Docker optimization is core expertise
```

---

#### 15. FastAPI Production (`fastapi-production`)

**Purpose:** Production-grade FastAPI patterns for async APIs and robust error handling

**Triggers:**
- Building new API endpoints
- Handling database operations in routes
- Implementing middleware
- Optimizing API performance

**Key Capabilities:**
- FastAPI async patterns
- SQLAlchemy 2.0 integration
- Pydantic v2 schemas
- Dependency injection patterns
- Error handling middleware

**Dependencies:**
- `database-migration` (for DB operations)
- `test-writer` (for endpoint tests)

**Example Invocation:**
```
Task: "Create a new FastAPI endpoint for bulk assignment creation"
→ Activate: fastapi-production
Reason: FastAPI endpoint creation is core purpose
```

---

#### 16. Frontend Development (`frontend-development`)

**Purpose:** Modern frontend development with Next.js 14, React 18, and TailwindCSS

**Triggers:**
- Building UI components
- Implementing pages or routes
- Optimizing frontend performance
- Following Next.js App Router patterns

**Key Capabilities:**
- Next.js 14 App Router
- React 18 patterns (Server Components, Suspense)
- TailwindCSS utility-first styling
- TanStack Query data fetching
- TypeScript strict mode

**Dependencies:**
- `react-typescript` (for type safety)
- `test-writer` (for component tests)

**Example Invocation:**
```
Task: "Create a new schedule dashboard page with Next.js"
→ Activate: frontend-development
Reason: Frontend page creation
```

---

#### 17. React TypeScript (`react-typescript`)

**Purpose:** TypeScript expertise for React/Next.js development

**Triggers:**
- Writing React components with strict typing
- Fixing TypeScript errors in frontend
- Handling generic components
- Working with TanStack Query types

**Key Capabilities:**
- React TypeScript patterns
- Generic component typing
- Hook type safety
- Event handler types
- Common TypeScript pitfall avoidance

**Dependencies:** None (foundational skill)

**Example Invocation:**
```
Task: "Fix TypeScript errors in the AssignmentList component"
→ Activate: react-typescript
Reason: TypeScript error fixing
```

---

#### 18. Python Testing Patterns (`python-testing-patterns`)

**Purpose:** Advanced pytest patterns for Python backend testing

**Triggers:**
- Dealing with async tests
- Complex fixture requirements
- Mocking strategies
- Database testing patterns
- Debugging flaky tests

**Key Capabilities:**
- Async test patterns
- Fixture dependency management
- Mocking best practices
- Database isolation techniques
- Parametrized test design

**Dependencies:**
- `test-writer` (complements with deeper patterns)

**Example Invocation:**
```
Task: "Fix flaky async tests in test_schedule_generation.py"
→ Activate: python-testing-patterns
Reason: Advanced async testing expertise needed
```

---

### E. Workflow & Process Skills

#### 19. PR Reviewer (`pr-reviewer`)

**Purpose:** Pull request review expertise with focus on context and quality gates

**Triggers:**
- Reviewing pull requests before merge
- Validating changes meet team standards
- Generating PR descriptions

**Key Capabilities:**
- Context-aware PR review
- Quality gate validation
- Team standards enforcement
- gh CLI integration for GitHub operations
- PR description generation

**Dependencies:**
- `code-review` (for code-level review)
- `code-quality-monitor` (for quality gates)

**Example Invocation:**
```
Task: "Review PR #123 before merging"
→ Activate: pr-reviewer
Reason: PR review explicitly requested
```

---

#### 20. Changelog Generator (`changelog-generator`)

**Purpose:** Automatically generate user-friendly changelogs from git history

**Triggers:**
- Preparing release notes
- Documenting changes for stakeholders
- Creating app store descriptions

**Key Capabilities:**
- Git commit history analysis
- User-friendly changelog formatting
- Breaking change detection
- Feature grouping and categorization

**Dependencies:** None (foundational skill)

**Example Invocation:**
```
Task: "Generate changelog for v2.0.0 release"
→ Activate: changelog-generator
Reason: Release notes generation
```

---

#### 21. Constraint Preflight (`constraint-preflight`)

**Purpose:** Pre-flight verification for scheduling constraint development

**Triggers:**
- Adding new scheduling constraints
- Modifying existing constraints
- Testing constraint behavior before commit

**Key Capabilities:**
- Constraint implementation verification
- Export and registration checking
- Test coverage validation
- Integration testing

**Dependencies:**
- `test-writer` (for constraint tests)
- `schedule-optimization` (for integration)

**Example Invocation:**
```
Task: "Add new constraint for pediatrics continuity clinic"
→ Activate: constraint-preflight
Reason: New constraint development
```

---

#### 22. Solver Control (`solver-control`)

**Purpose:** Solver kill-switch and progress monitoring for schedule generation

**Triggers:**
- Aborting runaway solvers
- Monitoring long-running schedule generation
- Integrating abort checks into solver loops

**Key Capabilities:**
- Solver progress monitoring
- Timeout enforcement
- Graceful solver termination
- Abort signal integration

**Dependencies:**
- `schedule-optimization` (solver management)

**Example Invocation:**
```
Task: "Monitor and abort solver if schedule generation exceeds 10 minutes"
→ Activate: solver-control
Reason: Solver monitoring and control
```

---

### F. Emergency & Incident Response Skills

#### 23. Production Incident Responder (`production-incident-responder`)

**Purpose:** Crisis response for production system failures

**Triggers:**
- Production system showing signs of failure
- Emergency situations (data loss, security breach)
- Critical system degradation

**Key Capabilities:**
- MCP resilience tools integration
- Critical failure detection
- Diagnosis and response workflows
- Emergency mitigation procedures

**Dependencies:**
- `systematic-debugger` (for root cause analysis)
- `safe-schedule-generation` (for rollback)

**Example Invocation:**
```
Task: "Production database is showing high error rates"
→ Activate: production-incident-responder
Reason: Production emergency
```

---

### G. Specialized Utility Skills

#### 24. PDF Generation (`pdf`)

**Purpose:** PDF generation and manipulation for compliance reports

**Triggers:**
- Creating printable schedule documents
- Generating compliance reports
- Extracting data from PDFs

**Key Capabilities:**
- Schedule PDF generation
- Compliance report formatting
- PDF parsing and extraction

**Dependencies:** None (utility skill)

**Example Invocation:**
```
Task: "Generate printable PDF of Q4 2025 call schedule"
→ Activate: pdf
Reason: PDF generation explicitly requested
```

---

#### 25. Excel Integration (`xlsx`)

**Purpose:** Excel spreadsheet import/export for schedules and reports

**Triggers:**
- Importing schedule data from Excel
- Generating Excel files for faculty/admin
- Coverage matrix exports

**Key Capabilities:**
- Excel file parsing
- Schedule data import
- Formatted export generation
- Coverage matrix creation

**Dependencies:** None (utility skill)

**Example Invocation:**
```
Task: "Import resident assignments from the Excel file"
→ Activate: xlsx
Reason: Excel import is core purpose
```

---

## III. ROUTING LOGIC

### A. Primary Routing Rules

**Rule 1: Explicit Skill Invocation**
If task explicitly names a skill, activate that skill directly.

```
Task: "Use acgme-compliance to validate this schedule"
→ Activate: acgme-compliance
```

**Rule 2: Domain Keyword Matching**
Match task keywords to skill domains.

| Keywords | Skill |
|----------|-------|
| ACGME, compliance, work hours, supervision | `acgme-compliance` |
| schedule, generate, optimize, coverage | `schedule-optimization` |
| swap, exchange, match, trade | `swap-management` |
| test, pytest, jest, coverage | `test-writer` |
| security, auth, PHI, HIPAA | `security-audit` |
| database, migration, alembic, schema | `database-migration` |
| docker, container, compose | `docker-containerization` |
| debug, investigate, troubleshoot | `systematic-debugger` |
| PR, pull request, review | `pr-reviewer` |

**Rule 3: Task Complexity Assessment**
For multi-step tasks, consider skill composition.

```
Task: "Generate schedule and validate ACGME compliance"
→ Primary: schedule-optimization
→ Secondary: acgme-compliance (invoked by primary)
```

**Rule 4: Safety-Critical Detection**
If task involves critical operations, route to safety skill first.

```
Task: "Apply new assignments to production database"
→ Primary: safe-schedule-generation (enforces backup)
→ Secondary: schedule-optimization (does actual work)
```

**Rule 5: Fallback to General Capabilities**
If no specific skill matches, use general Claude capabilities.

```
Task: "Explain how the scheduling algorithm works"
→ Use: General knowledge + codebase reading
→ No skill needed for explanation-only tasks
```

### B. Routing Decision Tree

```
START
  |
  ├─ Is skill explicitly named? ──YES──> Activate named skill
  |                              |
  |                              NO
  |                              |
  ├─ Does task modify production data? ──YES──> safe-schedule-generation
  |                                     |
  |                                     NO
  |                                     |
  ├─ Is this a code change? ──YES──> code-quality-monitor (pre-check)
  |                          |       |
  |                          |       └──> Appropriate skill based on domain
  |                          |
  |                          NO
  |                          |
  ├─ Is this an emergency? ──YES──> production-incident-responder
  |                         |
  |                         NO
  |                         |
  ├─ Match keywords to domain ──MATCH──> Activate domain skill
  |                             |
  |                             NO MATCH
  |                             |
  └─ Use general capabilities (read, explain, analyze)
```

### C. Progressive Disclosure

**Principle:** Start with lightweight analysis, escalate to specialized skills only when needed.

**Level 1: General Analysis**
- Read code
- Review documentation
- Basic pattern matching

**Level 2: Specialized Reading**
- Activate skill in "read-only" mode
- Gather context without making changes

**Level 3: Active Skill Engagement**
- Full skill activation
- Make changes, run operations

**Example:**
```
User: "Why is the schedule generation failing?"

Level 1 (General):
- Read error logs
- Check recent commits
- Review test output

Level 2 (Specialized Reading):
├─ Activate: systematic-debugger (exploration mode)
└─ Activate: schedule-optimization (read constraints)

Level 3 (Active Engagement):
├─ systematic-debugger: Run diagnostic tests
├─ automated-code-fixer: Apply fixes
└─ test-writer: Create regression tests
```

---

## IV. SKILL COMPOSITION PATTERNS

### A. Sequential Composition

**Pattern:** Skills executed one after another, each depending on previous result.

**Example - Schedule Generation Pipeline:**
```
1. safe-schedule-generation (create backup)
   ↓
2. schedule-optimization (generate assignments)
   ↓
3. acgme-compliance (validate result)
   ↓
4. schedule-verification (human checklist)
```

**Implementation:**
```python
# Pseudocode
backup_result = invoke_skill("safe-schedule-generation", {"action": "backup"})
if not backup_result.success:
    return error("Backup failed")

schedule_result = invoke_skill("schedule-optimization", {"params": params})
if not schedule_result.success:
    invoke_skill("safe-schedule-generation", {"action": "rollback"})
    return error("Generation failed")

validation = invoke_skill("acgme-compliance", {"schedule": schedule_result.data})
if validation.violations:
    return error("ACGME violations detected")

return success(schedule_result.data)
```

### B. Parallel Composition

**Pattern:** Skills executed simultaneously, results merged.

**Example - Comprehensive Code Review:**
```
┌─ code-review (general quality)
├─ security-audit (security focus)
├─ test-writer (coverage check)
└─ lint-monorepo (style check)
   ↓
  MERGE RESULTS
```

**Implementation:**
```python
# Pseudocode
results = await parallel_invoke([
    ("code-review", {"files": changed_files}),
    ("security-audit", {"files": changed_files}),
    ("test-writer", {"action": "check_coverage"}),
    ("lint-monorepo", {"action": "check"})
])

combined_report = merge_reports(results)
return combined_report
```

### C. Conditional Composition

**Pattern:** Skill selection based on runtime conditions.

**Example - Adaptive Debugging:**
```
IF error_type == "database":
    invoke_skill("database-migration", {"action": "diagnose"})
ELIF error_type == "solver":
    invoke_skill("solver-control", {"action": "analyze"})
ELIF error_type == "compliance":
    invoke_skill("acgme-compliance", {"action": "investigate"})
ELSE:
    invoke_skill("systematic-debugger", {"mode": "explore"})
```

### D. Recursive Composition

**Pattern:** Skill invokes itself or other skills recursively until condition met.

**Example - Iterative Constraint Refinement:**
```
def refine_constraints(schedule, max_iterations=5):
    for i in range(max_iterations):
        violations = invoke_skill("acgme-compliance", {"schedule": schedule})
        if not violations:
            return success(schedule)

        fixed_schedule = invoke_skill("schedule-optimization", {
            "schedule": schedule,
            "constraints": violations.to_constraints()
        })

        schedule = fixed_schedule

    return error("Could not resolve violations")
```

---

## V. DELEGATION PROTOCOLS

### A. When to Delegate

**Delegate to Subagent When:**
1. **Parallel Work Possible**: Multiple independent tasks
2. **Specialization Needed**: Task requires deep domain expertise
3. **Isolation Beneficial**: Risk of breaking main agent's context
4. **Long-Running Task**: Frees main agent for other work
5. **Different Permission Level**: Subagent needs restricted access

**Example:**
```
Task: "Generate schedule, review code changes, and update documentation"

Main Agent:
├─ Subagent 1: schedule-optimization (schedule generation)
├─ Subagent 2: code-review (review changes)
└─ Subagent 3: changelog-generator (update docs)

Main agent synthesizes results from all three.
```

### B. Delegation Message Format

**Request to Subagent:**
```json
{
  "task_id": "uuid-v4",
  "parent_agent": "main",
  "skill": "schedule-optimization",
  "action": "generate",
  "parameters": {
    "start_date": "2025-04-01",
    "end_date": "2025-06-30",
    "constraints": ["ACGME", "institutional"]
  },
  "timeout_seconds": 600,
  "priority": "high"
}
```

**Response from Subagent:**
```json
{
  "task_id": "uuid-v4",
  "status": "success" | "error" | "partial",
  "result": {
    "schedule": {...},
    "metrics": {...}
  },
  "errors": [],
  "warnings": ["Utilization at 82%, above threshold"],
  "execution_time_seconds": 145
}
```

### C. Result Synthesis

**When Multiple Subagents Return:**
1. **Collect All Results**: Wait for all or timeout
2. **Check Consistency**: Verify results don't contradict
3. **Merge Data**: Combine non-conflicting data
4. **Prioritize by Reliability**: Trust safety-critical skills first
5. **Report Conflicts**: Escalate contradictions to human

**Example - Code Quality Report:**
```python
def synthesize_quality_reports(results):
    report = {
        "overall_status": "unknown",
        "issues": [],
        "metrics": {}
    }

    # Collect all issues
    for skill_result in results:
        report["issues"].extend(skill_result.issues)

    # Worst status wins (error > warning > success)
    statuses = [r.status for r in results]
    if "error" in statuses:
        report["overall_status"] = "error"
    elif "warning" in statuses:
        report["overall_status"] = "warning"
    else:
        report["overall_status"] = "success"

    # Merge metrics
    for skill_result in results:
        report["metrics"][skill_result.skill_name] = skill_result.metrics

    return report
```

---

## VI. ERROR HANDLING IN ROUTING

### A. Skill Not Available

**Scenario:** Requested skill doesn't exist or failed to load.

**Response:**
```
ERROR: Skill "xyz-skill" not found in registry.

Available skills in this domain:
- schedule-optimization
- acgme-compliance
- swap-management

Did you mean one of these?
```

### B. Skill Prerequisites Not Met

**Scenario:** Skill requires data or context not available.

**Response:**
```
ERROR: Skill "schedule-optimization" requires:
  - Database connection (MISSING)
  - Valid date range (MISSING)

Please provide:
  1. Ensure database is running: docker-compose up -d db
  2. Specify date range: {"start": "2025-04-01", "end": "2025-06-30"}
```

### C. Skill Execution Failure

**Scenario:** Skill activated but encountered error during execution.

**Response:**
```
ERROR: Skill "acgme-compliance" execution failed.

Root Cause: Missing assignments for PGY-1 residents in week 3
Impact: Cannot calculate work hours without assignment data
Recovery: Generate assignments for missing weeks first

Suggested Command:
  invoke_skill("schedule-optimization", {
    "date_range": "2025-04-15 to 2025-04-21",
    "residents": ["PGY1-01", "PGY1-02"]
  })
```

---

## VII. SKILL VERSIONING

### A. Version Compatibility

**Format:** `MAJOR.MINOR.PATCH` (Semantic Versioning)

- **MAJOR**: Breaking changes to skill interface
- **MINOR**: New capabilities, backward-compatible
- **PATCH**: Bug fixes, no interface changes

**Example:**
```yaml
skill: acgme-compliance
version: 2.1.0
compatibility:
  min_core_version: 1.0.0
  max_core_version: 3.x.x
deprecated: false
sunset_date: null
```

### B. Deprecation Policy

**When Deprecating Skill:**
1. Mark as deprecated in registry
2. Set sunset date (minimum 30 days)
3. Document replacement skill
4. Provide migration guide
5. Remove after sunset date

**Deprecated Skill Entry:**
```yaml
skill: old-compliance-checker
version: 1.5.0
deprecated: true
sunset_date: 2025-03-01
replacement: acgme-compliance
migration_guide: docs/skills/migration/old-to-new-compliance.md
```

---

## VIII. MONITORING & METRICS

### A. Skill Performance Tracking

**Metrics to Track:**
- Invocation count
- Success rate
- Average execution time
- Error frequency by type
- User satisfaction (thumbs up/down)

**Dashboard:**
```
Skill: schedule-optimization
├─ Invocations: 1,247 (last 30 days)
├─ Success Rate: 94.3%
├─ Avg Execution: 2m 15s
├─ Errors: 71 (5.7%)
│  ├─ Timeout: 45
│  ├─ Constraint conflict: 18
│  └─ Database error: 8
└─ User Rating: 4.6/5.0
```

### B. Routing Effectiveness

**Metrics:**
- Correct skill selected (first try)
- User overrides (manual skill selection)
- Escalations to human
- Multi-skill composition frequency

**Improvement Loop:**
When routing effectiveness < 90%:
1. Analyze misrouted tasks
2. Update routing keywords
3. Refine decision tree logic
4. Add new skills if gap identified

---

## IX. BEST PRACTICES

### A. Skill Selection

**DO:**
- Choose most specific skill for task
- Consider safety implications first
- Use progressive disclosure (start light, escalate as needed)
- Compose skills when task spans multiple domains

**DON'T:**
- Over-activate (use general capabilities when sufficient)
- Skip safety skills for critical operations
- Ignore skill prerequisites
- Bypass Constitution rules with skill delegation

### B. Skill Development

**When Creating New Skill:**
1. Verify not duplicating existing skill
2. Define clear, narrow purpose
3. Document prerequisites and dependencies
4. Create examples and test cases
5. Register in this CORE/SKILL.md file
6. Add to routing logic with keywords

### C. Skill Maintenance

**Regular Reviews:**
- Quarterly: Review skill usage metrics
- After incidents: Update skills based on lessons learned
- On major releases: Verify all skills compatible
- Deprecation review: Remove unused or obsolete skills

---

## X. QUICK REFERENCE

### A. Skill Selection Cheat Sheet

| Task Type | Primary Skill | Common Secondary Skills |
|-----------|---------------|-------------------------|
| Generate schedule | `schedule-optimization` | `acgme-compliance`, `safe-schedule-generation` |
| Validate compliance | `acgme-compliance` | None |
| Process swap | `swap-management` | `acgme-compliance` |
| Write tests | `test-writer` | `python-testing-patterns` |
| Debug issue | `systematic-debugger` | Varies by domain |
| Review code | `code-review` | `security-audit`, `code-quality-monitor` |
| Database change | `database-migration` | `safe-schedule-generation` |
| API endpoint | `fastapi-production` | `test-writer`, `security-audit` |
| Frontend component | `frontend-development` | `react-typescript`, `test-writer` |
| Production emergency | `production-incident-responder` | `systematic-debugger` |

### B. Common Workflows

**New Feature Development:**
```
1. fastapi-production (create endpoint)
2. test-writer (create tests)
3. code-review (review implementation)
4. code-quality-monitor (quality gates)
5. pr-reviewer (final review)
```

**Schedule Generation:**
```
1. safe-schedule-generation (backup)
2. schedule-optimization (generate)
3. acgme-compliance (validate)
4. schedule-verification (human review)
```

**Incident Response:**
```
1. production-incident-responder (assess)
2. systematic-debugger (root cause)
3. automated-code-fixer (apply fix)
4. test-writer (regression tests)
```

---

**END OF CORE SKILL DOCUMENTATION**

*This registry is the authoritative source for skill routing and delegation. Keep it updated as skills evolve.*
