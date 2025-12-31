# AGENT ACCESS CONTROL MODEL

**Version:** 1.0
**Last Updated:** 2025-12-31
**Purpose:** Define permission tiers, scope boundaries, and access controls for all agent types

---

## 1. PERMISSION TIERS

All agents operate within one of three permission tiers, with escalating capabilities:

### Tier 1: READ_ONLY

**Capabilities:**
- Read files (code, tests, documentation)
- Search codebase (Grep, Glob)
- Run read-only commands (git status, git log, git diff)
- Analyze code patterns and architecture
- Generate reports and summaries

**Restrictions:**
- Cannot modify files
- Cannot execute write operations
- Cannot run tests or build commands
- Cannot make git commits
- Cannot execute shell commands that modify state
- Cannot access secrets or environment files

**Agent Types:** Analyzers, Researchers, Validators (code review)

**Example Agents:**
- Code Analyzer (surface-level search)
- Architecture Mapper (understand structure)
- Compliance Checker (read-only validation)

---

### Tier 2: READ_WRITE

**Capabilities:**
- All Tier 1 capabilities plus:
- Modify code files (with restrictions)
- Create/modify tests
- Create/modify documentation
- Run linters and auto-fix tools (Ruff, ESLint)
- Execute pytest and Jest tests
- Stage and commit git changes to feature branches
- Push to feature branches (not main/master)
- Create pull requests

**Restrictions:**
- Cannot push to main/master/protected branches
- Cannot use `git push --force`
- Cannot modify security/config core files (see Critical Files)
- Cannot execute database operations directly
- Cannot run docker-compose up/down without approval
- Cannot delete branches or rewrite history
- Cannot merge PRs
- Cannot modify ACGME compliance rules

**Agent Types:** Developers, Code Generators, Test Writers, Auto-fixers

**Example Agents:**
- Code Generator (implement features)
- Test Writer (pytest/Jest)
- Linter (auto-fix)
- PR Creator (push feature branches)

---

### Tier 3: ADMIN

**Capabilities:**
- All Tier 1 and Tier 2 capabilities plus:
- Modify critical system files (with approval)
- Execute database migrations (alembic)
- Docker operations (up/down/restart)
- Manage environment configuration
- Merge pull requests to main
- Access to secret management operations
- Execute load tests and performance analysis

**Restrictions:**
- Requires explicit user approval for destructive operations
- Cannot use `git push --force` to main without emergency approval
- Cannot execute `DROP TABLE` or `TRUNCATE` operations without backup
- Must maintain audit trail of all operations
- Cannot delete backups or migration history

**Agent Types:** DevOps, Database Administrators, Senior Architects

**Example Agents:**
- Database Migration Manager
- Infrastructure Engineer
- Release Manager

---

## 2. CRITICAL FILES - NEVER MODIFY

These files are protected and cannot be modified by Tier 2 agents. Tier 3 modification requires approval.

### Security & Auth

```
backend/app/core/security.py         # Password hashing, JWT
backend/app/core/config.py           # App configuration
backend/app/api/deps.py              # Auth dependencies
backend/app/api/routes/auth.py       # Authentication endpoints
```

### Database Core

```
backend/app/db/base.py               # Base DB config
backend/app/db/session.py            # Session management
backend/alembic/versions/*.py        # Applied migrations (read-only)
```

### Application Core

```
backend/app/main.py                  # FastAPI app init
backend/app/core/rate_limit.py       # Rate limiting config
frontend/next.config.js              # Next.js config
```

### ACGME Compliance

```
backend/app/scheduling/acgme_validator.py  # Regulatory rules
backend/app/scheduling/constraints/*.py    # Constraint definitions
```

### Resilience Framework

```
backend/app/resilience/*.py          # Resilience subsystem
backend/app/resilience/framework.py  # Core framework
```

### Environment & Secrets

```
.env                                 # Secrets (locked)
.env.local                           # Local overrides (locked)
docker-compose.yml                   # Production config (review-required)
```

---

## 3. FILE PATH RESTRICTIONS

### By Agent Type

#### Analyzer / Researcher Agents (READ_ONLY)

**Allowed:**
```
✓ backend/app/**/*.py                # All backend code
✓ frontend/src/**/*.{ts,tsx}         # All frontend code
✓ tests/**/*.py                      # Test files
✓ docs/**/*.md                       # Documentation
✓ .claude/**/*.md                    # Agent docs
✓ (no restrictions on reading)
```

**Denied:**
```
✗ .env                               # Secrets
✗ .env.local                         # Local secrets
✗ .secrets/                          # Secret directory
✗ docker-compose.override.yml        # Local overrides
```

#### Developer Agents (READ_WRITE)

**Allowed:**
```
✓ backend/app/**/*.py                # Backend code (except core/*)
✓ backend/tests/**/*.py              # Backend tests
✓ backend/alembic/versions/*.py      # NEW migrations only
✓ frontend/src/**/*.{ts,tsx}         # Frontend code
✓ frontend/tests/**/*.{ts,tsx}       # Frontend tests
✓ docs/**/*.md                       # Documentation
✓ .claude/**/*.md                    # Agent docs
```

**Denied:**
```
✗ backend/app/core/security.py       # Auth system
✗ backend/app/core/config.py         # Configuration
✗ backend/app/main.py                # App initialization
✗ backend/app/db/*.py                # Database core
✗ backend/app/scheduling/acgme_validator.py  # ACGME rules
✗ backend/app/resilience/**/*.py     # Resilience subsystem
✗ .env                               # Secrets
✗ docker-compose.yml                 # Production config
✗ Applied alembic versions (read-only)
```

#### DevOps/Admin Agents (ADMIN)

**Allowed:**
```
✓ All file paths (with approval)
✓ backend/**/*.py
✓ frontend/**/*.{ts,tsx}
✓ .env (read-only, never modify)
✓ docker-compose.yml (with approval)
✓ .claude/**/*.md
```

**Denied:**
```
✗ git push --force to main/master
✗ Direct database write operations without backup
```

---

## 4. SCOPE BOUNDARIES

### Code Modification Scope

**Backend Modifications:**
- Feature implementation in service layer
- New API routes and controllers
- Test creation and updates
- Documentation updates
- Schema/model additions (with migrations)

**NOT Allowed:**
- Core auth system changes
- Database session layer modifications
- ACGME compliance rule changes
- Resilience framework changes
- Rate limiting modifications

**Frontend Modifications:**
- Component development
- Page creation
- Test creation
- Styling (TailwindCSS)
- Hook development

**NOT Allowed:**
- Next.js core configuration
- Build system modifications
- TypeScript strict config changes
- Authentication flow modifications

### Git Operations Scope

| Operation | Tier 1 | Tier 2 | Tier 3 |
|-----------|--------|--------|--------|
| `git status` | ✓ | ✓ | ✓ |
| `git log` | ✓ | ✓ | ✓ |
| `git diff` | ✓ | ✓ | ✓ |
| `git add` | ✗ | ✓ | ✓ |
| `git commit` | ✗ | ✓ | ✓ |
| `git push` (feature) | ✗ | ✓ | ✓ |
| `git push origin main` | ✗ | ✗ | ✗* |
| `git merge main` | ✗ | Ask | ✓ |
| `git rebase` | ✗ | Ask | ✓ |
| `git push --force` | ✗ | ✗ | ✗* |
| `git reset --hard` | ✗ | ✗ | Ask |

*Can only be done with emergency user approval

---

## 5. RBAC MATRIX (47 Agents)

### Agent Classification

#### Core Analysis Agents (5)

| Agent | Tier | Capabilities | File Access |
|-------|------|--------------|------------|
| Architecture Mapper | READ_ONLY | Analyze code structure, create diagrams | All code |
| Code Reviewer | READ_ONLY | Review PRs, identify issues | Pull requests |
| Compliance Validator | READ_ONLY | Check ACGME, security patterns | All code, tests |
| Security Auditor | READ_ONLY | Security review, vulnerability scan | All code |
| Test Coverage Analyzer | READ_ONLY | Analyze test coverage, gaps | Tests, code |

#### Development Agents (12)

| Agent | Tier | Capabilities | File Access |
|-------|------|--------------|------------|
| Code Generator | READ_WRITE | Create new features | app/**, tests/ |
| Backend Developer | READ_WRITE | Backend implementation | backend/app/**, tests/ |
| Frontend Developer | READ_WRITE | Frontend implementation | frontend/src/**, tests/ |
| Test Writer | READ_WRITE | Create pytest, Jest | tests/ |
| Linter / Auto-fixer | READ_WRITE | Run Ruff, ESLint, fix | backend/**, frontend/** |
| API Designer | READ_WRITE | API routes, schemas | routes/, schemas/ |
| Schema Validator | READ_WRITE | Pydantic/TS schemas | schemas/ |
| Documentation Writer | READ_WRITE | Create/update docs | docs/, README.md |
| Bug Fixer | READ_WRITE | Fix bugs, create fixes | app/**, tests/ |
| Feature Implementer | READ_WRITE | Implement features | app/**, tests/ |
| Refactor Agent | READ_WRITE | Code refactoring | app/** |
| Performance Optimizer | READ_WRITE | Performance tuning | app/** |

#### Specialized Agents (15)

| Agent | Tier | Capabilities | File Access |
|-------|------|--------------|------------|
| Scheduler Engine Dev | READ_WRITE | Scheduling logic | app/scheduling/** |
| ACGME Constraint Dev | READ_WRITE | Add constraints | app/scheduling/constraints/** |
| Resilience Framework Dev | READ_WRITE | Resilience features | app/resilience/** |
| Database Schema Dev | READ_WRITE | Schema updates, migrations | models/**, alembic/versions/new |
| API Integration Dev | READ_WRITE | API integrations | app/api/**, services/ |
| Auth System Dev | ADMIN | Auth modifications | app/core/security.py (approval) |
| Notification Service Dev | READ_WRITE | Notification system | app/notifications/** |
| Analytics Engine Dev | READ_WRITE | Analytics, metrics | app/analytics/** |
| Celery Task Dev | READ_WRITE | Background tasks | app/tasks/** |
| Swap Management Dev | READ_WRITE | Swap system | app/services/swap/** |
| Credential Tracking Dev | READ_WRITE | Procedure tracking | app/services/credentials/** |
| Emergency Coverage Dev | READ_WRITE | Emergency handling | app/services/emergency/** |
| Report Generator Dev | READ_WRITE | Reporting system | app/reporting/** |
| UI Component Dev | READ_WRITE | React components | frontend/components/** |
| Integration Test Dev | READ_WRITE | Integration tests | tests/integration/** |

#### Infrastructure Agents (10)

| Agent | Tier | Capabilities | File Access |
|-------|------|--------------|------------|
| Database Admin | ADMIN | DB migrations, backups | alembic/**, migrations |
| DevOps Engineer | ADMIN | Docker, deployment | docker-compose.yml, infra/ |
| CI/CD Manager | ADMIN | GitHub Actions, pipelines | .github/workflows/** |
| Monitoring/Observability | ADMIN | Prometheus, Grafana | monitoring/**, dashboards/ |
| Load Test Engineer | ADMIN | Performance testing | load-tests/** |
| Security Admin | ADMIN | Security config | backend/app/core/security.py |
| MCP Server Manager | ADMIN | AI tool integration | mcp-server/** |
| Config Manager | ADMIN | Environment config | .env.example, config/** |
| Release Manager | ADMIN | Version management, releases | CHANGELOG.md, VERSION |
| Incident Responder | ADMIN | Emergency fixes | Any (with approval) |

#### Coordination Agents (5)

| Agent | Tier | Capabilities | File Access |
|-------|------|--------------|------------|
| Orchestrator | READ_ONLY | Coordinate multi-agent work | All (read-only) |
| Project Manager | READ_ONLY | Track tasks, progress | All (read-only) |
| Synthesizer | READ_ONLY | Synthesize findings | All (read-only) |
| Decision Engine | READ_ONLY | Make architectural decisions | All (read-only) |
| Validator | READ_WRITE | Pre-commit validation | All (read-only) |

---

## 6. APPROVAL WORKFLOWS

### Changes Requiring Approval

#### Tier 2 → Tier 3 Escalation
- Database schema changes affecting critical tables
- ACGME compliance rule modifications
- Authentication system changes
- Rate limiting configuration changes
- Resilience framework modifications

#### User Approval Required
- Emergency commits to main/master
- Destructive database operations
- Configuration changes to production settings
- Modification of critical files

---

## 7. AUDIT & COMPLIANCE

### Access Logging

All Tier 2 and Tier 3 operations must be logged:

```
Operation: FILE_MODIFY
Agent: Code Generator
File: backend/app/services/swap_executor.py
Timestamp: 2025-12-31 14:30:00 UTC
Status: SUCCESS
Commit: abc123def456
```

### Violation Handling

**Tier 2 Violation (unauthorized file access):**
1. Log violation with timestamp and agent ID
2. Prevent operation
3. Alert user
4. Flag agent for review

**Tier 3 Violation (dangerous operation without approval):**
1. Stop operation immediately
2. Require explicit user confirmation
3. Log confirmation decision
4. Audit trail maintained

---

## 8. PERMISSION CHECKLIST

Before any agent begins work:

- [ ] Agent type identified
- [ ] Permission tier verified
- [ ] File paths checked against restrictions
- [ ] Scope boundaries understood
- [ ] Critical files identified as off-limits
- [ ] Approval requirements documented
- [ ] Audit logging configured

---

## References

- [Agent Isolation Model](AGENT_ISOLATION_MODEL.md)
- [Agent Input Validation](AGENT_INPUT_VALIDATION.md)
- [Agent Data Protection](AGENT_DATA_PROTECTION.md)
- [Security Audit Framework](AGENT_SECURITY_AUDIT.md)
- Project CLAUDE.md AI Rules of Engagement
