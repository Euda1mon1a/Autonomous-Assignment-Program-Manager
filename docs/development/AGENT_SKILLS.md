# Agent Skills Reference

> **Complete reference for AI Agent Skills in the Residency Scheduler**
>
> Last Updated: 2025-12-26

---

## Overview

Agent Skills are packaged domain expertise that AI assistants (Claude Code, OpenAI Codex, GitHub Copilot, etc.) can use to perform specialized tasks. Skills follow the [Agent Skills specification](https://agentskills.io) for cross-agent compatibility.

### How Skills Work

```
User: "Is this code secure?"
       │
       ▼
┌──────────────────────────────────────┐
│  AI Agent detects "security" keyword │
│  Loads security-audit skill          │
│  Applies skill procedures            │
│  Returns security analysis           │
└──────────────────────────────────────┘
```

Skills provide:
- **Domain Knowledge**: Specialized procedures and best practices
- **Activation Context**: When the skill should be used
- **Integration Points**: How the skill connects with tools and other skills
- **Escalation Rules**: When to ask for human help

---

## Skills Directory

All skills are located in `.claude/skills/`:

```
.claude/skills/
├── acgme-compliance/           # ACGME regulatory compliance
│   ├── SKILL.md
│   ├── thresholds.md
│   └── exceptions.md
├── automated-code-fixer/       # Auto-fix code issues
│   ├── SKILL.md
│   ├── reference.md
│   └── examples.md
├── changelog-generator/        # Release notes from git
│   └── SKILL.md
├── code-quality-monitor/       # Quality gate enforcement
│   └── SKILL.md
├── code-review/                # Code review procedures
│   └── SKILL.md
├── constraint-preflight/       # Constraint verification pre-flight
│   └── SKILL.md
├── docker-containerization/    # Docker development & orchestration
│   ├── SKILL.md
│   ├── security.md
│   └── troubleshooting.md
├── database-migration/         # Alembic migration expertise
│   └── SKILL.md
├── fastapi-production/         # Production FastAPI patterns
│   └── SKILL.md
├── frontend-development/       # Next.js/React/TailwindCSS
│   └── SKILL.md
├── lint-monorepo/              # Unified Python/TypeScript linting
│   ├── SKILL.md
│   ├── python.md
│   └── typescript.md
├── pdf/                        # PDF generation & extraction
│   └── SKILL.md
├── pr-reviewer/                # Pull request review
│   └── SKILL.md
├── production-incident-responder/  # Crisis response
│   └── SKILL.md
├── python-testing-patterns/    # Advanced pytest patterns
│   └── SKILL.md
├── react-typescript/           # TypeScript for React/Next.js
│   └── SKILL.md
├── safe-schedule-generation/   # Backup-first schedule generation
│   └── SKILL.md
├── schedule-optimization/      # Multi-objective optimization
│   └── SKILL.md
├── schedule-verification/      # Human verification checklist
│   └── SKILL.md
├── security-audit/             # Security auditing
│   └── SKILL.md
├── swap-management/            # Shift swap workflows
│   └── SKILL.md
├── session-documentation/      # Comprehensive documentation enforcement
│   └── SKILL.md
├── solver-control/             # Kill-switch & progress monitoring
│   └── SKILL.md
├── systematic-debugger/        # Systematic debugging workflow
│   └── SKILL.md
├── test-writer/                # Test generation
│   └── SKILL.md
└── xlsx/                       # Excel import/export
    └── SKILL.md
```

---

## Skills Reference

### Domain-Specific Skills

| Skill | Description | Primary Use Case |
|-------|-------------|------------------|
| `acgme-compliance` | ACGME regulatory expertise | Schedule validation, compliance checks |
| `schedule-optimization` | Multi-objective optimization | Schedule generation, workload balancing |
| `schedule-verification` | Human verification checklist | Post-generation schedule review |
| `swap-management` | Shift swap workflows | Swap requests, partner matching |

### Development Skills

| Skill | Description | Primary Use Case |
|-------|-------------|------------------|
| `code-review` | Code review procedures | Reviewing generated code, quality checks |
| `constraint-preflight` | Constraint verification pre-flight | Verify constraints are implemented, exported, registered, tested |
| `docker-containerization` | Docker development & orchestration | Dockerfiles, docker-compose, container debugging, image optimization |
| `automated-code-fixer` | Auto-fix code issues | Test failures, linting errors |
| `code-quality-monitor` | Quality gate enforcement | Pre-commit validation, PR checks |
| `lint-monorepo` | Unified Python/TypeScript linting | Auto-fix, root-cause analysis for lint errors |
| `test-writer` | Test generation | Writing pytest/Jest tests |
| `python-testing-patterns` | Advanced pytest patterns | Async tests, fixtures, mocking, flaky tests |
| `database-migration` | Alembic migration expertise | Schema changes, migrations |
| `fastapi-production` | Production FastAPI patterns | API endpoints, SQLAlchemy, error handling |
| `pr-reviewer` | Pull request review | PR validation, merge decisions |
| `security-audit` | Security auditing | HIPAA, OPSEC/PERSEC compliance |
| `changelog-generator` | Release notes from git | Deployment docs, stakeholder updates |
| `session-documentation` | Comprehensive documentation enforcement | Session handoffs, feature completion, PR creation |
| `systematic-debugger` | Systematic debugging workflow | Complex bugs, exploration-first debugging |

### Frontend Skills

| Skill | Description | Primary Use Case |
|-------|-------------|------------------|
| `react-typescript` | TypeScript for React/Next.js | Type errors, component typing, TanStack Query |
| `frontend-development` | Next.js 14, TailwindCSS, React | UI components, pages, performance |

### Document Skills

| Skill | Description | Primary Use Case |
|-------|-------------|------------------|
| `xlsx` | Excel import/export | Schedule imports, compliance reports, coverage matrices |
| `pdf` | PDF generation & extraction | Printable schedules, compliance reports, document parsing |

### Operations Skills

| Skill | Description | Primary Use Case |
|-------|-------------|------------------|
| `production-incident-responder` | Crisis response | System failures, emergency coverage |

---

## Detailed Skill Documentation

### acgme-compliance

**Purpose**: Expert knowledge of ACGME regulations for medical residency scheduling.

**Activates When**:
- Validating schedule compliance
- Checking resident work hours
- Verifying supervision ratios
- Answering ACGME-related questions

**Key Rules Enforced**:
| Rule | Requirement |
|------|-------------|
| 80-Hour Rule | Max 80 hours/week averaged over 4 weeks |
| 1-in-7 Rule | One 24-hour period off every 7 days |
| Supervision | PGY-1: 2:1, PGY-2/3: 4:1 faculty ratio |

**Integration**: Works with MCP tool `validate_acgme_compliance`

---

### automated-code-fixer

**Purpose**: Automatically detect and fix code issues with strict quality controls.

**Activates When**:
- Test failures detected
- Linting errors reported
- Type-checking errors found
- Build failures encountered

**Quality Gates**:
1. All tests must pass after fix
2. Linting must pass (ruff, black)
3. Type checking must pass (mypy)
4. No security issues introduced
5. Architecture compliance maintained

**Escalation Triggers**:
- Fix requires model/migration changes
- Fix affects ACGME compliance logic
- Multiple interdependent failures

---

### code-quality-monitor

**Purpose**: Proactive code health monitoring and quality gate enforcement.

**Activates When**:
- Before committing changes
- During PR reviews
- When validating code health

**Standards Enforced**:
| Metric | Target | Critical |
|--------|--------|----------|
| Test Coverage | >= 80% | >= 70% |
| Type Coverage | 100% public APIs | >= 90% |
| Cyclomatic Complexity | <= 10 | <= 15 |

---

### constraint-preflight

**Purpose**: Pre-flight verification for scheduling constraint development.

**Activates When**:
- Creating new scheduling constraints
- Modifying existing constraints
- Before committing constraint-related changes
- After adding constraints to `__init__.py` exports

**Verification Checklist**:
1. Constraint class implemented with proper methods
2. Constraint exported in `__init__.py`
3. Constraint registered in `ConstraintManager.create_default()`
4. Constraint registered in `ConstraintManager.create_resilience_aware()`
5. Tests verify constraint is registered (not just logic)

**Pre-Flight Command**:
```bash
cd backend && python ../scripts/verify_constraints.py
```

**Key Files**:
| File | Purpose |
|------|---------|
| `scripts/verify_constraints.py` | Pre-flight verification script |
| `backend/tests/test_constraint_registration.py` | CI tests for registration |
| `backend/app/scheduling/constraints/manager.py` | Where constraints are registered |

---

### docker-containerization

**Purpose**: Docker development and container orchestration expertise.

**Activates When**:
- Creating or modifying Dockerfiles
- Setting up docker-compose configurations
- Debugging container build failures or runtime issues
- Optimizing Docker image size or build performance
- Configuring health checks and service dependencies
- Implementing container security hardening
- CI/CD pipeline Docker integration

**Key Capabilities**:
| Capability | Description |
|------------|-------------|
| Multi-Stage Builds | Optimized production images with separate build/runtime stages |
| Docker Compose | Development and production orchestration |
| Health Checks | Service dependency management |
| Security Hardening | Non-root users, read-only filesystems, secrets management |
| Debugging | Container logs, networking issues, build failures |
| Image Optimization | Layer caching, size reduction, .dockerignore |

**Project Docker Files**:
- `/backend/Dockerfile` - Production backend (multi-stage)
- `/frontend/Dockerfile` - Production frontend (multi-stage)
- `docker-compose.yml` - Base configuration
- `docker-compose.dev.yml` - Development overrides
- `.docker/docker-compose.prod.yml` - Hardened production

**Supporting Files**:
- `security.md` - Container security patterns for military contexts
- `troubleshooting.md` - Common issues and solutions

**Quick Commands**:
```bash
# Development
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# View logs
docker compose logs -f backend

# Shell into container
docker compose exec backend bash

# Clean up
docker system prune -af --volumes
```

**Escalation Triggers**:
- Production docker-compose.yml changes
- Secrets management configuration
- Network security policy changes
- Resource limit adjustments for production

---

### code-review

**Purpose**: Structured code review for AI-generated implementations.

**Activates When**:
- Reviewing Claude-generated code
- Auditing for vulnerabilities
- Validating against project standards
- Before committing significant changes

**Review Focus Areas**:
1. Code Quality (structure, naming, DRY)
2. Security & Safety (validation, auth, OWASP)
3. Performance (algorithms, queries, async)
4. Maintainability (tests, types, docs)
5. Standards Compliance (CLAUDE.md rules)

**Output Format**:
- CRITICAL: Must fix before merge
- WARNING: Should fix
- INFO: Nice to have
- GOOD: Well-implemented patterns

---

### database-migration

**Purpose**: Safe database schema evolution using Alembic migrations.

**Activates When**:
- Adding new database models
- Modifying existing fields
- Creating foreign key relationships
- Renaming/dropping columns

**Core Principle**: NEVER modify models without creating a migration.

**Migration Patterns**:
- Adding nullable columns (safe)
- Adding non-nullable columns (requires default)
- Adding indexes
- Adding foreign keys
- Renaming columns
- Dropping columns (dangerous)

**Safety Checklist**:
- [ ] Review autogenerated migration
- [ ] Test upgrade: `alembic upgrade head`
- [ ] Test downgrade: `alembic downgrade -1`
- [ ] Verify data integrity
- [ ] Commit migration with model change

---

### pr-reviewer

**Purpose**: Comprehensive pull request review with quality gates.

**Activates When**:
- Reviewing open PRs
- Creating PR descriptions
- Validating changes before merge

**Review Categories**:
1. Code Quality (architecture, types, docs)
2. Testing (coverage, edge cases)
3. Security (secrets, validation, auth)
4. Architecture (patterns, async, schemas)
5. Documentation (PR description, comments)

**Decision Matrix**:
| Gate | Pass | Block |
|------|------|-------|
| Tests | All pass | Any failure |
| Linting | 0 errors | Any error |
| Security | No issues | Any vulnerability |
| Coverage | >= 70% | < 60% |

**GitHub CLI Integration**:
```bash
gh pr view <number>
gh pr checks <number>
gh pr review <number> --approve
gh pr merge <number> --squash
```

---

### production-incident-responder

**Purpose**: Crisis response for production system failures.

**Activates When**:
- Health check fails
- ACGME violations detected
- Utilization exceeds 80%
- Coverage gaps identified
- Defense level escalates

**Response Protocol**:
1. DETECTION (automated monitoring)
2. DIAGNOSIS (root cause analysis)
3. RESPONSE (human approval required for RED/BLACK)
4. RECOVERY (homeostasis monitoring)

**MCP Tool Integration**:
- `check_utilization_threshold_tool`
- `get_defense_level_tool`
- `run_contingency_analysis_resilience_tool`
- `execute_sacrifice_hierarchy_tool`

---

### schedule-optimization

**Purpose**: Multi-objective schedule optimization using constraint programming.

**Activates When**:
- Generating new schedules
- Optimizing existing schedules
- Balancing workload distribution
- Resolving conflicts

**Optimization Objectives**:
| Type | Objectives |
|------|------------|
| Hard (P0) | ACGME compliance, qualifications, no double-booking |
| Soft | Fairness (0.25), preferences (0.20), continuity (0.20), resilience (0.20), efficiency (0.15) |

**Uses**: Google OR-Tools CP-SAT solver

---

### schedule-verification

**Purpose**: Human verification checklist for generated schedules. Ensures schedules make operational sense before deployment.

**Activates When**:
- After schedule generation completes
- Before deploying a new schedule to production
- When reviewing any academic block schedule
- When a human asks "does this schedule make sense?"
- After constraint changes to verify behavior

**Verification Checks**:
| Check | What to Verify |
|-------|----------------|
| FMIT faculty pattern | No back-to-back FMIT weeks |
| FMIT mandatory call | Fri+Sat call during FMIT week |
| Post-FMIT Sunday | No Sunday call after FMIT week |
| Night Float headcount | Exactly 1 resident on NF |
| FMIT resident headcount | 1 per PGY level (3 total) |
| Call spacing | No back-to-back call weeks |
| PGY clinic days | PGY-1→Wed AM, PGY-2→Tue PM, PGY-3→Mon PM |
| Absence conflicts | No assignments during leave/TDY |
| Weekend coverage | Inpatient coverage exists |
| ACGME compliance | 0 violations |

**MANDATORY Reporting**:
Every time this skill runs, it MUST:
1. Print visible PASS/FAIL for each check
2. Show actual data found (not just "checked")
3. Generate summary table
4. Save report to `docs/reports/schedule-verification-{block}-{date}.md`

**CLI Tool**:
```bash
cd backend
python ../scripts/verify_schedule.py --block 10 --start 2026-03-10 --end 2026-04-06
```

**Integration**: Works with `acgme-compliance` skill and generates reports to `docs/reports/`.

---

### solver-control

**Purpose**: Kill-switch and progress monitoring for schedule generation solvers.

**Activates When**:
- Solver is taking too long and needs to be stopped
- Monitoring progress of long-running schedule generation
- Integrating abort checks into solver code
- Debugging solver performance or stuck jobs
- Emergency situations requiring immediate solver termination

**Key Features**:
| Feature | Description |
|---------|-------------|
| Abort Signal | Redis-backed kill-switch for graceful solver termination |
| Progress Tracking | Real-time iteration, score, and violation monitoring |
| Partial Results | Save best solution when interrupted |
| Active Run List | Monitor all running solver jobs |

**API Endpoints**:
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/scheduler/runs/{run_id}/abort` | POST | Signal solver to abort |
| `/scheduler/runs/{run_id}/progress` | GET | Get current progress |
| `/scheduler/runs/active` | GET | List active solvers |

**Key Files**:
- `backend/app/scheduling/solver_control.py` - SolverControl class
- `backend/app/api/routes/scheduler_ops.py` - API endpoints

**Quick Abort**:
```bash
curl -X POST http://localhost:8000/scheduler/runs/{run_id}/abort \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"reason": "taking too long", "requested_by": "admin"}'
```

---

### session-documentation

**Purpose**: Enforce comprehensive documentation as part of work completion.

**Activates When**:
- Feature implementation completed
- Bug fix committed
- Significant code change made
- Session ending
- Handoff requested
- PR ready for creation

**Why This Skill Exists**:
Documentation debt compounds session over session. Without proactive documentation:
- Future sessions rebuild context from scratch (~50K tokens)
- Handoff errors occur (e.g., constraints implemented but not registered)
- Users must prompt 3x for comprehensive docs

**Required Outputs**:

| Category | Required | Contents |
|----------|----------|----------|
| What Was Done | Always | Bullet list, files modified, tests added |
| Why It Was Done | Always | Context, problem solved, references |
| How to Verify | Always | Commands, expected output |
| What Remains | Always | Incomplete tasks, limitations |
| Decisions Made | Recommended | Design choices, alternatives rejected |
| Gotchas | Recommended | Pitfalls, non-obvious behavior |

**Session Handoff Format**:
```markdown
## Session Summary
- Current State (working/broken)
- Completed This Session (with commit hashes)
- Blocked Items (with reasons)
- Next Steps (prioritized)
- Verification Commands
- Key Files table
```

**Anti-Pattern**:
```
BAD: "Fixed the bug in scheduler.py"
GOOD: [Full documentation with files, verification, root cause]
```

**Integration**: Works with `pr-reviewer` (docs in PR), `changelog-generator` (user-facing notes).

---

### security-audit

**Purpose**: Security auditing for healthcare and military contexts.

**Activates When**:
- Auth/authz code changes
- PHI data handling
- Military schedule data
- API endpoint review
- Pre-deployment checks

**Security Domains**:
1. HIPAA Compliance (access control, audit logging, encryption)
2. OPSEC/PERSEC (never commit real names, schedules, TDY data)
3. OWASP Top 10 (injection, auth, crypto, etc.)

**Never Commit**:
| Data Type | Risk |
|-----------|------|
| Resident/Faculty Names | PERSEC |
| Schedule Assignments | OPSEC |
| TDY/Deployment Data | OPSEC |

---

### swap-management

**Purpose**: Expert procedures for managing schedule swaps.

**Activates When**:
- Processing swap requests
- Finding compatible partners
- Resolving conflicts
- Emergency coverage

**Swap Types**:
1. One-to-One (direct exchange)
2. Absorb (give away shift)
3. Three-Way (circular exchange)

**Validation Checklist**:
- [ ] Both parties consent
- [ ] Qualifications verified
- [ ] 80-hour limit maintained
- [ ] 1-in-7 day off preserved
- [ ] Supervision ratios valid

---

### test-writer

**Purpose**: Generate comprehensive test suites for Python and TypeScript.

**Activates When**:
- New code without tests
- Coverage below threshold
- Bug fix needs regression test
- Complex logic needs coverage

**Test Categories**:
1. Unit Tests (single function/method)
2. Service Tests (business logic)
3. API Tests (HTTP endpoints)
4. Integration Tests (database operations)

**Coverage Requirements**:
| Layer | Target | Minimum |
|-------|--------|---------|
| Services | 90% | 80% |
| Controllers | 85% | 75% |
| Models | 80% | 70% |

**Frameworks**:
- Python: pytest with async support
- TypeScript: Jest + React Testing Library

---

### xlsx

**Purpose**: Excel spreadsheet import and export for schedules, coverage matrices, and compliance reports.

**Activates When**:
- Importing schedules from Excel files
- Exporting schedules to Excel format
- Creating coverage matrices or rotation calendars
- Generating ACGME compliance reports in spreadsheet format
- Bulk data imports (residents, faculty, rotations)

**Key Libraries**:
| Library | Use Case |
|---------|----------|
| `pandas` | Data analysis, basic read/write |
| `openpyxl` | Formulas, formatting, Excel-specific features |

**Core Principles**:
1. Use Excel formulas, not hardcoded calculated values
2. Cell indices are 1-based in openpyxl
3. Use `data_only=True` only for read-only analysis (loses formulas)

**Import Patterns**:
- Bulk resident import (Name, Email, PGY Level, Start Date)
- Schedule assignment import (person × date grid)
- Validation helpers for headers and date formats

**Export Patterns**:
- Weekly schedule with formatting
- Coverage matrix with totals
- ACGME compliance report with conditional formatting

---

### pdf

**Purpose**: PDF generation and manipulation for printable schedules, compliance reports, and document extraction.

**Activates When**:
- Generating printable schedule PDFs
- Creating ACGME compliance reports
- Extracting data from uploaded PDF documents
- Merging, splitting, or watermarking PDFs

**Key Libraries**:
| Library | Use Case |
|---------|----------|
| `reportlab` | PDF generation (Platypus for tables) |
| `pypdf` | Read, merge, split, watermark |
| `pdfplumber` | Text and table extraction |

**Generation Patterns**:
- Schedule report (landscape, table with styling)
- ACGME compliance report (summary + individual details)
- Watermarked documents

**Extraction Patterns**:
- Text extraction with `pdfplumber`
- Table extraction to DataFrames
- OCR for scanned documents (optional pytesseract)

**Security**:
- Validate uploaded files are actually PDFs (magic bytes)
- Sanitize extracted text (remove control characters)

---

### changelog-generator

**Purpose**: Automatically generate user-friendly changelogs from git commit history.

**Activates When**:
- Preparing release notes for deployment
- Creating weekly/monthly change summaries
- Documenting updates for non-technical stakeholders
- Generating app store update descriptions

**Commit Categories**:
| Category | Prefixes | Label |
|----------|----------|-------|
| Features | `feat:`, `add:` | New Features |
| Fixes | `fix:`, `bugfix:` | Bug Fixes |
| Breaking | `BREAKING:` | Breaking Changes |
| Security | `security:` | Security Updates |
| Performance | `perf:` | Performance |

**Filtered Out (Internal)**:
- `refactor:`, `test:`, `chore:`, `ci:`, `docs:`, `style:`
- Merge commits

**Transformation Rules**:
- "Implement X endpoint" → "Added X feature"
- "Fix N+1 query" → "Improved loading speed"
- "Add validation" → "Enhanced reliability"

**Output Formats**:
- Standard changelog (markdown with sections)
- Compact format (bullet points for app stores)

---

### lint-monorepo

**Purpose**: Unified linting and auto-fix for Python (Ruff) and TypeScript (ESLint) in monorepo.

**Activates When**:
- Lint errors reported in CI/CD
- Pre-commit quality checks
- Code review identifies style issues
- `ruff check` or `npm run lint` fails
- Persistent lint errors after auto-fix attempts

**Workflow**:
1. **Auto-fix first**: Always try `--fix` before manual intervention
2. **Triage remaining**: Categorize errors (unsafe fixes, logic errors, type errors)
3. **Root-cause analysis**: For persistent errors, investigate why
4. **Targeted fix**: Apply fixes based on root cause

**Supporting Files**:
- `python.md` - Ruff error codes (F401, E712, B006, S105, etc.)
- `typescript.md` - ESLint/TypeScript patterns

**Integration**: Primary linting skill, invoked by `code-quality-monitor`.

---

### react-typescript

**Purpose**: TypeScript expertise for React/Next.js development.

**Activates When**:
- TypeScript compilation errors in React components
- Writing new React components with proper typing
- Handling generic components and hooks
- Working with TanStack Query type inference
- Fixing `any` type issues

**Common Error Patterns**:
| Error | Cause | Fix |
|-------|-------|-----|
| TS2307 | Cannot find module 'react' | Reinstall `@types/react` |
| TS7006 | Parameter implicitly has 'any' | Add explicit type annotation |
| TS7026 | JSX element implicitly has 'any' | Check tsconfig jsx setting |
| TS2322 | Type 'unknown' not assignable | Add generic type to useQuery |

**Key Patterns**:
- Component props interfaces
- Generic components with trailing comma (`<T,>`)
- Event handler types (React.ChangeEvent, etc.)
- TanStack Query typed hooks

**Validated Against Real Errors** (Dec 2025):
This skill was created and validated against actual TypeScript errors in the frontend codebase:

| Error Code | Count | Pattern Covered |
|------------|-------|-----------------|
| TS2322 (`unknown` to `ReactNode`) | 3+ | Section 4 |
| TS7053 (index signature) | 5 | Section 7 |
| TS2339 (property doesn't exist) | 4 | Section 5 |
| TS2769 (overload matching) | 2 | Section 6 |

All common frontend TypeScript errors in this project are addressed by this skill.

---

### frontend-development

**Purpose**: Modern frontend development with Next.js 14, React 18, TailwindCSS.

**Activates When**:
- Building new React components or pages
- Implementing Next.js App Router patterns
- Styling with TailwindCSS
- Data fetching with TanStack Query
- Performance optimization

**Key Patterns**:
| Pattern | Use Case |
|---------|----------|
| App Router pages | `page.tsx`, `layout.tsx`, `loading.tsx`, `error.tsx` |
| Compound components | DataTable, Modal, Card |
| TanStack Query hooks | `useQuery`, `useMutation` with query keys |
| TailwindCSS utilities | Mobile-first, dark mode, responsive |

**Integration**: Works with `react-typescript` for type-specific patterns.

---

### python-testing-patterns

**Purpose**: Advanced pytest patterns for Python backend testing.

**Activates When**:
- Debugging flaky or failing tests
- Complex async testing scenarios
- Database transaction isolation issues
- Mocking external services
- Test performance optimization

**Key Patterns**:
| Pattern | Use Case |
|---------|----------|
| Factory fixtures | Create test data with customization |
| Fixture composition | Build complex test scenarios |
| AsyncMock | Mock async functions and context managers |
| Parametrized tests | Test multiple inputs systematically |
| Transaction isolation | Prevent test pollution |

**Complements**: `test-writer` generates basic tests; this skill handles advanced scenarios.

---

### fastapi-production

**Purpose**: Production-grade FastAPI patterns for async APIs.

**Activates When**:
- Building new API endpoints
- Database query optimization
- Error handling and validation
- Middleware implementation
- Authentication/authorization patterns

**Architecture**:
```
Route (thin) → Controller → Service → Repository → Model
```

**Key Patterns**:
| Pattern | Purpose |
|---------|---------|
| Pydantic schemas | Request/response validation |
| Dependency injection | Database sessions, auth |
| Custom exceptions | Structured error handling |
| Eager loading | Prevent N+1 queries |
| Row locking | Handle concurrent updates |

**Integration**: Works with `database-migration` for schema changes.

---

### systematic-debugger

**Purpose**: Systematic debugging for complex issues.

**Activates When**:
- Complex bugs requiring investigation
- Unclear root cause
- Multiple potential failure points
- Test failures with non-obvious causes

**Four-Phase Workflow**:
1. **Exploration** (DO NOT FIX YET) - Read code, understand system
2. **Planning** - Use extended thinking, create hypothesis list
3. **Implementation** - Apply fixes, verify edge cases
4. **Commit** - Document what was fixed and why

**Extended Thinking Triggers** (in order of computational budget):
- `"think"` < `"think hard"` < `"think harder"` < `"ultrathink"`

---

### safe-schedule-generation

**Purpose**: Schedule generation with mandatory backup before write operations.

**Activates When**:
- Generating new schedules
- Bulk assignment operations
- Executing swaps
- Any MCP tool that modifies schedule data

**Safety Protocol**:
1. Verify recent backup exists (< 2 hours)
2. If no backup, create one first
3. Check backend health
4. Get user approval
5. Execute operation
6. Verify results (violations < 5, coverage > 80%)
7. Offer rollback if results are bad

**Critical Rule**: NEVER execute schedule-modifying MCP tools without backup verification.

---

## Creating Custom Skills

### Step 1: Create Directory

```bash
mkdir -p .claude/skills/my-skill
```

### Step 2: Create SKILL.md

```markdown
---
name: my-skill
description: Brief description for skill matching
---

# My Skill

Detailed instructions...

## When This Skill Activates
- Condition 1
- Condition 2

## Procedures
1. Step one
2. Step two

## Escalation Rules
**Escalate to human when:**
1. Condition A
2. Condition B
```

### Step 3: Add Supporting Files (Optional)

- `reference.md` - Detailed procedures
- `examples.md` - Example scenarios
- `thresholds.md` - Configurable values

### Step 4: Test

Ask Claude about the skill topic and verify it activates.

---

## Skill Specification

Skills follow the [Agent Skills Specification](https://agentskills.io):

### SKILL.md Format

```yaml
---
name: skill-name          # Required: kebab-case identifier
description: Brief desc   # Required: Used for skill matching
---

# Skill Title

[Markdown content with procedures, rules, examples]
```

### Progressive Loading

- **At startup**: Only frontmatter loaded (~100 tokens)
- **On activation**: Full markdown content loaded
- **Benefits**: Fast startup, low memory, context-efficient

### Cross-Agent Compatibility

Skills work with:
- Claude Code (Web, CLI, IDE)
- OpenAI Codex
- GitHub Copilot
- Google Antigravity
- Any MCP-compatible client

---

## Integration with MCP Tools

Many skills integrate with MCP (Model Context Protocol) tools:

| Skill | Primary MCP Tools |
|-------|-------------------|
| acgme-compliance | `validate_acgme_compliance` |
| production-incident-responder | `check_utilization_threshold_tool`, `get_defense_level_tool` |
| swap-management | `analyze_swap_compatibility`, `validate_swap` |
| schedule-optimization | `generate_schedule`, `optimize_schedule` |

See `mcp-server/` for tool implementations.

---

## Best Practices

### Skill Design

1. **Clear activation triggers**: Description should match user queries
2. **Structured procedures**: Step-by-step workflows
3. **Escalation rules**: Define when to ask humans
4. **Integration points**: Connect with tools and other skills

### Skill Maintenance

1. **Version control**: Skills evolve with codebase
2. **Team alignment**: Shared standards across developers
3. **Documentation**: Keep SKILL.md current
4. **Testing**: Verify skill activation with example queries

---

## Agent-to-Agent Critique Schema

When AI agents review each other's work (e.g., one agent reviewing code generated by another), use this structured feedback format to prevent cascading misinterpretations.

### Minimal Contract

```json
{
  "defect": "One clear problem statement",
  "proposal": "Smallest concrete change to fix it",
  "confidence": 0.85
}
```

### Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `defect` | string | Single, clear problem statement |
| `proposal` | string | Minimal concrete change to fix the defect |
| `confidence` | float (0-1) | Confidence score for gating/sorting changes |

### Confidence Thresholds

| Score | Action |
|-------|--------|
| < 0.6 | Route to human review |
| 0.6 - 0.85 | Apply in sandbox, verify before production |
| > 0.85 | Safe to apply directly |

### Examples

**Scheduling Rule Violation:**
```json
{
  "defect": "Inpatient faculty assigned Wed call despite 'no call Sun-Thu during inpatient week' constraint.",
  "proposal": "Unassign Wed call from person_id=abc123 and reassign to person_id=def456 (eligible pool).",
  "confidence": 0.86
}
```

**Prompt Fix:**
```json
{
  "defect": "Agent writes free text instead of selecting Faculty record IDs.",
  "proposal": "Append system rule: 'All updates MUST reference {table}:{record_id} only; no free text names.'",
  "confidence": 0.92
}
```

**Code Quality Issue:**
```json
{
  "defect": "N+1 query in get_all_assignments() fetching persons in loop.",
  "proposal": "Replace loop with selectinload(Assignment.person) in initial query.",
  "confidence": 0.88
}
```

### Router Logic (n8n/Workflow Example)

```javascript
return items.map(it => {
  const {defect, proposal, confidence} = it.json;

  // Schema validation
  if (typeof defect !== 'string' || typeof proposal !== 'string' || typeof confidence !== 'number') {
    return {json: {route: "reject", reason: "schema_invalid"}};
  }

  // Confidence-based routing
  const route = confidence < 0.6 ? "review"
              : confidence < 0.85 ? "sandbox"
              : "apply";

  return {json: {route, defect, proposal, confidence}};
});
```

### Guardrails

1. **Reject if proposal contains plain names** where record ID expected
2. **Whitelist tables** by default (persons, assignments, rotations)
3. **Audit log all critiques**: `{defect, proposal, confidence, applied, actor, timestamp}`
4. **Never auto-apply** changes affecting ACGME compliance logic

---

## Agent Model Selection

When spawning subagents, ORCHESTRATOR selects the optimal Claude model tier based on task complexity.

### Model Tiers

| Tier | Model | Cost | Use Case |
|------|-------|------|----------|
| Fast | **Haiku** | 1x | Simple tasks, metadata updates, auditing |
| Balanced | **Sonnet** | 10x | Code generation, testing, analysis |
| Complex | **Opus** | 100x | Architecture, coordination, multi-agent synthesis |

### Agent Tier Assignments

All agents have a `> **Model Tier:**` field in their spec headers:

| Tier | Agents |
|------|--------|
| **Haiku** (4) | DELEGATION_AUDITOR, META_UPDATER, DBA, SYNTHESIZER |
| **Sonnet** (11) | QA_TESTER, SCHEDULER, FRONTEND_ENGINEER, BACKEND_ENGINEER, RELEASE_MANAGER, TOOLSMITH, RESILIENCE_ENGINEER, COMPLIANCE_AUDITOR, BURNOUT_SENTINEL, CAPACITY_OPTIMIZER, EPIDEMIC_ANALYST |
| **Opus** (10) | ORCHESTRATOR, ARCHITECT, AGENT_FACTORY, OPTIMIZATION_SPECIALIST, COORD_* |

### Vector-Based Selection (pgvector)

The system uses embeddings to learn optimal agent/model combinations:

1. **Task embedding** - Embed task description using sentence-transformers (384 dims)
2. **Similarity query** - Find similar successful historical tasks
3. **Model recommendation** - Choose cheapest model that reliably handles this task type
4. **Learning** - Record outcomes to improve future recommendations

See [Agent Model Selection](AGENT_MODEL_SELECTION.md) for full documentation.

### Agent Skill Matcher Service (NEW)

The `AgentMatcher` service (`backend/app/services/agent_matcher.py`) provides ML-powered agent selection:

```python
from app.services.agent_matcher import match_task_to_agent, get_agent_matcher

# Simple usage - get best agent for a task
agent, model = match_task_to_agent("Validate ACGME compliance for schedule")
# Returns: ("ACGME_VALIDATOR", "haiku")

# Advanced usage - get multiple matches with explanations
matcher = get_agent_matcher()
explanation = matcher.explain_match("Generate a compliant resident schedule")
# Returns: {
#   "task": "Generate a compliant resident schedule",
#   "matches": [{"agent": "SCHEDULER", "score": 0.82, ...}, ...],
#   "recommendation": "SCHEDULER",
#   "confidence": "high"
# }
```

**How It Works:**
1. Loads agent specifications from `.claude/Agents/*.md`
2. Extracts capabilities from Charter and Primary Responsibilities sections
3. Pre-computes 384-dim embeddings for each agent using sentence-transformers
4. Matches incoming task descriptions via cosine similarity
5. Returns ranked list of agents with model tier recommendations

**Model Tier Recommendations by Archetype:**
| Archetype | Model | Rationale |
|-----------|-------|-----------|
| Researcher | sonnet | Thorough analysis needs |
| Validator | haiku | Rule-based checks, fast |
| Generator | sonnet | Creative output needs |
| Critic | sonnet | Adversarial analysis |
| Synthesizer | opus | Complex integration |

---

## ML Research Roadmap

For comprehensive ML enhancement opportunities across the PAI system, see:
**[ML Research for PAI Advancement](../planning/ML_RESEARCH_PAI_ADVANCEMENT.md)**

This document outlines 100 tasks across 10 research areas:
- Agent Meta-Learning
- Burnout Prediction & Prevention
- Solver Intelligence
- Preference Learning & Personalization
- ACGME Compliance Intelligence
- Swap Matching & Optimization
- Resilience & Network Analysis
- Performance & Fatigue Modeling
- Document & Knowledge Intelligence
- Autonomous Agent Evolution

---

## Related Documentation

- [Agent Model Selection](AGENT_MODEL_SELECTION.md) - Vector-based model selection
- [ML Research for PAI Advancement](../planning/ML_RESEARCH_PAI_ADVANCEMENT.md) - 100-task ML roadmap
- [AI Agent User Guide](../guides/AI_AGENT_USER_GUIDE.md) - Complete agent setup
- [AI Rules of Engagement](AI_RULES_OF_ENGAGEMENT.md) - Git and workflow rules
- [CLAUDE.md](../../CLAUDE.md) - Project guidelines
- [Agent Skills Specification](https://agentskills.io) - External spec
