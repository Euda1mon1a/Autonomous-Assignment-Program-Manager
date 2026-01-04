# Script Ownership Matrix

> **Purpose:** Standing context for AI agents mapping scripts to their owning agents
> **Last Updated:** 2026-01-03
> **Authority:** COORD_OPS
> **References:** ADR-011 (CI_LIAISON owns container management)

---

## Overview

This document maps all executable scripts in the repository to their owning agents, trigger conditions, CLI options, and pre-requisites. It serves as standing context for all AI agents working in this codebase.

**Ownership Categories:**
- **Infrastructure Scripts** (ARCHITECT domain via COORD_PLATFORM): Docker, builds, system setup
- **Operations Scripts** (CI_LIAISON domain via COORD_OPS): CI/CD, health checks, deployments
- **Database Scripts** (DBA domain via COORD_PLATFORM): Backups, migrations, seeding
- **Security Scripts** (SECURITY_AUDITOR domain via COORD_RESILIENCE): PII scans, audits
- **Scheduling Scripts** (SCHEDULER domain via COORD_ENGINE): Schedule generation, validation

---

## Script Ownership Matrix

### Infrastructure Scripts (ARCHITECT Domain)

| Script | Owner Agent | Coordinator | Purpose | Trigger Condition |
|--------|-------------|-------------|---------|-------------------|
| `scripts/start-mcp.sh` | CI_LIAISON | COORD_OPS | Start MCP server with backend health check | MCP server needed for AI tooling |
| `scripts/build-wheelhouse.sh` | CI_LIAISON | COORD_OPS | Pre-download Python packages for offline deployment | Air-gapped deployment, Docker build optimization |

### Container & CI/CD Scripts (CI_LIAISON Domain per ADR-011)

| Script | Owner Agent | Coordinator | Purpose | Trigger Condition |
|--------|-------------|-------------|---------|-------------------|
| `scripts/start-local.sh` | CI_LIAISON | COORD_OPS | **Full stack startup** - DB, Redis, Celery, MCP, API, Frontend | Session start, development environment setup |
| `scripts/stack-health.sh` | CI_LIAISON | COORD_OPS | **Unified health check** - API, frontend, DB, Redis, containers | Pre-flight checks, session-end validation, troubleshooting |
| `scripts/health-check.sh` | CI_LIAISON | COORD_OPS | Verify all services are running and healthy | Pre-flight checks, monitoring, troubleshooting |
| `scripts/validate-mcp-config.sh` | CI_LIAISON | COORD_OPS | Validate MCP configuration for transport/auth issues | Pre-commit, CI/CD, MCP troubleshooting |
| `scripts/start-celery.sh` | CI_LIAISON | COORD_OPS | Start Celery worker and beat scheduler | Background task processing needed |
| `scripts/pre-deploy-validate.sh` | CI_LIAISON | COORD_OPS | Pre-deployment validation and safety checks | Before any production deployment |
| `scripts/test-mcp-integration.sh` | CI_LIAISON | COORD_OPS | Integration testing for MCP server | After MCP changes, CI validation |

### Database Scripts (DBA Domain)

| Script | Owner Agent | Coordinator | Purpose | Trigger Condition |
|--------|-------------|-------------|---------|-------------------|
| `scripts/stack-backup.sh` | DBA | COORD_PLATFORM | **Unified** backup/restore with immaculate fallback | Before risky operations, recovery, emergency |
| `scripts/backup-db.sh` | DBA | COORD_PLATFORM | Create compressed PostgreSQL backups with rotation | Scheduled backups, before destructive operations |
| `scripts/backup_full_stack.sh` | DBA | COORD_PLATFORM | **DEPRECATED** - Use stack-backup.sh | Legacy |
| `scripts/full-stack-backup.sh` | DBA | COORD_PLATFORM | **DEPRECATED** - Use stack-backup.sh | Legacy |
| `scripts/restore_full_stack.sh` | DBA | COORD_PLATFORM | **DEPRECATED** - Use stack-backup.sh | Legacy |

### Security Scripts (SECURITY_AUDITOR Domain)

| Script | Owner Agent | Coordinator | Purpose | Trigger Condition |
|--------|-------------|-------------|---------|-------------------|
| `scripts/pii-scan.sh` | SECURITY_AUDITOR | COORD_RESILIENCE | PII/OPSEC/PERSEC pre-commit scanner | Pre-commit hook, PR validation, security audits |
| `scripts/audit-fix.sh` | SECURITY_AUDITOR | COORD_RESILIENCE | Fix npm security vulnerabilities in frontend | npm audit findings, security review |

### AI/Agent Scripts (COORD_OPS Domain)

| Script | Owner Agent | Coordinator | Purpose | Trigger Condition |
|--------|-------------|-------------|---------|-------------------|
| `.claude/scripts/ccw-validation-gate.sh` | CI_LIAISON | COORD_OPS | CCW (Claude Code Work) validation gate after burns | Every ~20 CCW tasks, before PR |

---

## Detailed Script Documentation

### `scripts/stack-backup.sh` ⭐ PRIMARY

**Owner:** DBA
**Coordinator:** COORD_PLATFORM

**Description:**
Unified backup, restore, and emergency recovery script. Consolidates `backup_full_stack.sh`, `full-stack-backup.sh`, and `restore_full_stack.sh`. Includes immaculate baseline verification and emergency restore capability.

**Modes:**
```bash
backup     # Create comprehensive backup
restore    # Restore from a backup
emergency  # Break glass: restore from immaculate baseline
```

**CLI Options:**
```bash
# Backup mode
./scripts/stack-backup.sh backup                      # Timestamped backup
./scripts/stack-backup.sh backup --name pre-refactor  # Named backup
./scripts/stack-backup.sh backup --include-redis      # Include Redis volume

# Restore mode
./scripts/stack-backup.sh restore                     # List & prompt
./scripts/stack-backup.sh restore backup_20260103     # Restore specific

# Emergency mode (immaculate fallback)
./scripts/stack-backup.sh emergency --confirm         # Break glass
```

**Safety Features:**
- Disk space pre-check (1GB minimum)
- Verifies immaculate baseline exists (warns if missing)
- Generates SHA256 checksums
- Creates pre-restore snapshot before any restore
- Compares Alembic versions (warns on mismatch)
- Redis flush option on restore
- Double confirmation for emergency restore

**Backup Contents:**
- `database/dump.sql.gz` - PostgreSQL dump
- `database/alembic_version.txt` - Schema version
- `volumes/postgres_volume.tar.gz` - Volume backup
- `volumes/redis_volume.tar.gz` - Optional
- `docker/images/*.tar.gz` - Docker images
- `git/HEAD_COMMIT`, `UNCOMMITTED.patch` - Git state
- `config/` - requirements.txt, package.json, .mcp.json
- `MANIFEST.md` - Restore instructions
- `CHECKSUM.sha256` - Integrity verification

**Pre-requisites:**
- Docker Compose stack running
- 1GB+ free disk space
- For emergency: immaculate baseline images tagged

**Examples:**
```bash
# Before risky migration
./scripts/stack-backup.sh backup --name before-migration-051

# Something broke, restore
./scripts/stack-backup.sh restore before-migration-051

# Everything is REALLY broken
./scripts/stack-backup.sh emergency --confirm
# Then re-ingest RAG: ./scripts/init_rag_embeddings.py
```

---

### `scripts/backup-db.sh`

**Owner:** DBA
**Coordinator:** COORD_PLATFORM

**Description:**
Creates compressed PostgreSQL backups with timestamp, automatic rotation, and optional S3 upload.

**CLI Options:**
```bash
--docker         # Use Docker container for backup
--retention N    # Keep last N days of backups (default: 30)
--s3             # Upload to S3 (requires AWS_* env vars)
--email EMAIL    # Send notification email on completion
```

**Pre-requisites:**
- PostgreSQL database running
- pg_dump available (or Docker if using --docker)
- gzip installed
- AWS CLI if using --s3

**Example:**
```bash
./scripts/backup-db.sh --docker --retention 7
```

---

### `scripts/health-check.sh`

**Owner:** CI_LIAISON
**Coordinator:** COORD_OPS

**Description:**
Verifies all services (PostgreSQL, Redis, Backend API, Frontend, Celery) are running and healthy.

**CLI Options:**
```bash
--verbose, -v    # Show detailed output
--docker, -d     # Check Docker containers instead of local services
```

**Exit Codes:**
- 0: All services healthy
- 1: One or more services unhealthy (degraded)
- 2: Critical service failure

**Pre-requisites:**
- curl installed (for HTTP health checks)
- Docker if using --docker mode
- Services should be running

**Example:**
```bash
./scripts/health-check.sh --docker --verbose
```

---

### `scripts/start-celery.sh`

**Owner:** CI_LIAISON
**Coordinator:** COORD_OPS

**Description:**
Starts Celery worker and/or beat scheduler with proper configuration. Must be run from backend directory.

**CLI Options:**
```bash
worker    # Start worker only
beat      # Start beat scheduler only
both      # Start both (default)
```

**Environment Variables:**
- `CELERY_LOG_LEVEL` - Logging level (default: info)
- `CELERY_WORKER_CONCURRENCY` - Worker concurrency (default: 4)
- `CELERY_QUEUES` - Queues to process (default: default,resilience,notifications)
- `REDIS_URL` - Redis connection URL

**Pre-requisites:**
- Redis running and accessible
- Run from backend directory (`cd backend`)
- Python environment activated

**Example:**
```bash
cd backend && ../scripts/start-celery.sh both
```

---

### `scripts/start-mcp.sh`

**Owner:** CI_LIAISON
**Coordinator:** COORD_OPS

**Description:**
Starts the MCP (Model Context Protocol) server for AI assistant integration. Ensures FastAPI backend is running before starting MCP.

**Environment Variables:**
- `API_BASE_URL` - Backend API URL (default: http://localhost:8000)
- `LOG_LEVEL` - Logging level (default: INFO)

**Pre-requisites:**
- FastAPI backend running on port 8000
- Python environment with scheduler_mcp installed
- curl available for health checks

**Example:**
```bash
./scripts/start-mcp.sh
```

---

### `scripts/pre-deploy-validate.sh`

**Owner:** CI_LIAISON
**Coordinator:** COORD_OPS

**Description:**
Comprehensive validation before production deployment. Checks environment configuration, code quality, security settings, and dependencies.

**Validation Checks:**
1. Environment configuration (.env file, required variables)
2. Code quality (no debug statements, formatting)
3. Security (no hardcoded secrets, CORS configured)
4. Configuration files (docker-compose, requirements)
5. Database migrations (Alembic setup)
6. Dependencies (all required packages listed)

**Exit Codes:**
- 0: All checks passed or warnings only
- 1: Critical errors found (do not deploy)

**Pre-requisites:**
- Run from project root directory
- Docker available (for compose validation)

**Example:**
```bash
./scripts/pre-deploy-validate.sh
```

---

### `scripts/audit-fix.sh`

**Owner:** SECURITY_AUDITOR
**Coordinator:** COORD_RESILIENCE

**Description:**
Fixes npm security vulnerabilities in frontend. Creates backup of package-lock.json before making changes.

**Safety Features:**
- Backs up package-lock.json before changes
- Shows vulnerability report before and after
- Prompts before running `--force` fixes
- Runs tests after force fix to validate

**Exit Codes:**
- 0: All vulnerabilities fixed or no vulnerabilities found
- 1: Some vulnerabilities remain or fix failed

**Pre-requisites:**
- npm installed
- Frontend directory exists

**Example:**
```bash
./scripts/audit-fix.sh
```

---

### `scripts/pii-scan.sh`

**Owner:** SECURITY_AUDITOR
**Coordinator:** COORD_RESILIENCE

**Description:**
Scans codebase for PII (Personally Identifiable Information), OPSEC (Operational Security), and PERSEC (Personnel Security) violations.

**Security Patterns Detected:**
- SSN patterns (###-##-####)
- Military .mil email addresses
- Data files staged for commit (.csv, .dump, .sql)
- .env files being staged

**Defense Layers:**
1. Pre-commit hook (this script)
2. GitHub Actions workflow
3. Periodic security audits

**Exit Codes:**
- 0: No PII/security issues found
- 1: Potential issues found (fails commit)

**Pre-requisites:**
- grep installed
- Git repository (for staged file checks)

**Example:**
```bash
./scripts/pii-scan.sh
```

---

### `.claude/scripts/ccw-validation-gate.sh`

**Owner:** CI_LIAISON
**Coordinator:** COORD_OPS

**Description:**
Claude Code Work (CCW) validation gate to run after every ~20 CCW tasks. Validates type-check, build, and token corruption.

**Gates:**
1. Type Check (`npm run type-check`)
2. Build (`npm run build`)
3. Token Corruption Check (detects patterns like "await sawait ervice")

**Exit Codes:**
- 0: All gates passed - safe to continue burn
- 1: Gate failed - stop burn, diagnose root cause

**Pre-requisites:**
- Run from anywhere (script finds repo root via git)
- Frontend npm dependencies installed

**Example:**
```bash
./.claude/scripts/ccw-validation-gate.sh
```

---

### `scripts/test-mcp-integration.sh`

**Owner:** CI_LIAISON
**Coordinator:** COORD_OPS

**Description:**
Integration testing for MCP server with FastAPI backend. Tests module imports, PII compliance, and domain context functionality.

**Test Categories:**
1. MCP module imports and dependencies
2. PII/security compliance verification
3. Domain context abbreviation expansion
4. Constraint explanation functionality

**Exit Codes:**
- 0: All tests passed
- 1: One or more tests failed

**Pre-requisites:**
- MCP server code in mcp-server/src/
- Python environment with scheduler_mcp installed

**Example:**
```bash
./scripts/test-mcp-integration.sh
```

---

### `scripts/start-local.sh` ⭐ PRIMARY

**Owner:** CI_LIAISON
**Coordinator:** COORD_OPS

**Description:**
Unified script to start the complete local development stack. This is the recommended way to start all services for development.

**Services Started:**
1. PostgreSQL database
2. Redis cache/broker
3. Celery worker
4. Celery beat scheduler
5. MCP server (AI tooling)
6. FastAPI backend
7. Next.js frontend

**CLI Options:**
```bash
./scripts/start-local.sh           # Start all services
./scripts/start-local.sh --no-frontend  # Skip frontend (if running separately)
```

**Pre-requisites:**
- Docker and Docker Compose installed
- docker-compose.local.yml present
- Port availability (5432, 6379, 8000, 3000, 8001)

**Example:**
```bash
./scripts/start-local.sh
# Wait for all services to report healthy
```

---

### `scripts/stack-health.sh` ⭐ PRIMARY

**Owner:** CI_LIAISON
**Coordinator:** COORD_OPS

**Description:**
Unified health check for Docker-based development stack. Checks API, frontend, database, Redis, and container status. Used by session-end validation.

**Checks Performed:**
1. API health endpoint (HTTP 200)
2. Frontend accessibility
3. Database connectivity (via Docker)
4. Redis connectivity (via Docker)
5. Container status and health

**CLI Options:**
```bash
./scripts/stack-health.sh          # Basic health check
./scripts/stack-health.sh --full   # Include lint/typecheck
./scripts/stack-health.sh --json   # JSON output for automation
```

**Exit Codes:**
- 0: All services healthy (GREEN)
- 1: Some services degraded (YELLOW)
- 2: Critical services down (RED)

**Pre-requisites:**
- Docker containers running
- curl available

**Example:**
```bash
./scripts/stack-health.sh --full  # Full check including linting
```

---

### `scripts/validate-mcp-config.sh`

**Owner:** CI_LIAISON
**Coordinator:** COORD_OPS

**Description:**
Validates MCP configuration to prevent transport and authentication issues. Addresses recurring configuration problems documented in project history.

**Validation Checks:**
1. `.mcp.json` syntax validity
2. Transport type ("http" required for Claude Code)
3. Authentication configuration
4. URL accessibility
5. Schema compliance

**When to Run:**
- Before commits (pre-commit hook)
- In CI/CD pipeline
- After MCP configuration changes
- When troubleshooting MCP connectivity

**Exit Codes:**
- 0: Configuration valid
- 1: Configuration errors found

**Pre-requisites:**
- `.mcp.json` exists
- jq installed (for JSON parsing)
- curl available (for URL checks)

**Example:**
```bash
./scripts/validate-mcp-config.sh
```

---

### `scripts/build-wheelhouse.sh`

**Owner:** CI_LIAISON
**Coordinator:** COORD_OPS

**Description:**
Pre-downloads Python packages for offline installation. Creates a wheelhouse directory for air-gapped environments or faster Docker builds.

**Output:**
- `backend/vendor/wheels/` - Downloaded wheel files

**Pre-requisites:**
- Python 3.11+
- pip with wheel support
- `backend/requirements.txt` exists

**Example:**
```bash
./scripts/build-wheelhouse.sh
```

---

## Python Scripts (Additional Reference)

### Seeding & Data Scripts

| Script | Owner | Purpose |
|--------|-------|---------|
| `scripts/seed_people.py` | DBA | Seed person data |
| `scripts/seed_templates.py` | DBA | Seed rotation templates |
| `scripts/seed_feature_flags.py` | DBA | Seed feature flags |
| `scripts/seed_rotation_templates.py` | DBA | Seed rotation template data |
| `scripts/seed_inpatient_rotations.py` | DBA | Seed inpatient rotation data |
| `scripts/generate_blocks.py` | SCHEDULER | Generate schedule blocks |

### Scheduling & Validation Scripts

| Script | Owner | Purpose |
|--------|-------|---------|
| `scripts/verify_schedule.py` | SCHEDULER | Verify schedule correctness |
| `scripts/verify_constraints.py` | SCHEDULER | Verify constraint implementation |

### Development Scripts

| Script | Owner | Purpose |
|--------|-------|---------|
| `scripts/dev/setup_dev_env.py` | CI_LIAISON | Set up development environment |
| `scripts/dev/generate_test_data.py` | QA_TESTER | Generate test data |
| `scripts/import_excel.py` | DBA | Import Excel schedule data |
| `scripts/sanitize_pii.py` | SECURITY_AUDITOR | Sanitize PII from data |

### Deployment Scripts

| Script | Owner | Purpose |
|--------|-------|---------|
| `scripts/deploy/pre_deploy_check.py` | CI_LIAISON | Python pre-deployment checks |

### Monitoring Scripts

| Script | Owner | Purpose |
|--------|-------|---------|
| `scripts/monitoring/collect_metrics.py` | RESILIENCE_ENGINEER | Collect system metrics |
| `scripts/monitoring/compare_benchmarks.py` | RESILIENCE_ENGINEER | Compare benchmark results |
| `scripts/monitoring/generate_report.py` | RESILIENCE_ENGINEER | Generate monitoring reports |
| `scripts/monitoring/alert_on_regression.py` | RESILIENCE_ENGINEER | Alert on performance regressions |

### Operations Scripts

| Script | Owner | Purpose |
|--------|-------|---------|
| `scripts/ops/backup_database.py` | DBA | Python database backup |
| `scripts/ops/health_check.py` | CI_LIAISON | Python health check |
| `scripts/ops/rotate_secrets.py` | SECURITY_AUDITOR | Rotate application secrets |

### RAG Scripts

| Script | Owner | Purpose |
|--------|-------|---------|
| `scripts/init_rag_embeddings.py` | CI_LIAISON | Initialize RAG embeddings |
| `scripts/example_rag_usage.py` | CI_LIAISON | Example RAG usage patterns |

### Backend CLI Scripts (`backend/scripts/`)

| Script | Owner | Purpose |
|--------|-------|---------|
| `backend/scripts/analyze_schedule.py` | SCHEDULER | Analyze Excel schedules for conflicts |
| `backend/scripts/audit_constraints.py` | SCHEDULER | Audit constraint implementations |
| `backend/scripts/constraint_manager_cli.py` | SCHEDULER | CLI for managing constraints |
| `backend/scripts/export_openapi.py` | ARCHITECT | Export OpenAPI schema to JSON |
| `backend/scripts/export_sanitized_metrics.py` | RESILIENCE_ENGINEER | Export sanitized metrics for analysis |
| `backend/scripts/migration_utils.py` | DBA | Alembic migration utilities/helpers |
| `backend/scripts/seed_data.py` | DBA | Database seeding for dev/test |

---

## Escalation Matrix

When a script fails or requires unusual handling:

| Script Category | First Escalate To | Then To | Emergency |
|-----------------|-------------------|---------|-----------|
| Infrastructure | CI_LIAISON | COORD_PLATFORM | ARCHITECT |
| Database | DBA | COORD_PLATFORM | ARCHITECT |
| Security | SECURITY_AUDITOR | COORD_RESILIENCE | Faculty |
| CI/CD | CI_LIAISON | COORD_OPS | ARCHITECT |
| Scheduling | SCHEDULER | COORD_ENGINE | ARCHITECT |

---

## Pre-requisites Summary

### Before Container Operations (CI_LIAISON Scripts)

Per ADR-011, CI_LIAISON must validate before container operations:
1. Required containers running (`docker ps`)
2. Volume mounts accessible
3. Inter-container networking functional
4. Health endpoints responding

### Before Database Operations (DBA Scripts)

1. Backup exists and is < 24 hours old
2. Database is accessible
3. Alembic version is known

### Before Deployment Operations

1. All CI checks passing
2. Pre-deploy validation passing
3. Backup completed
4. Rollback plan documented

---

## Domain Summary for ARCHITECT

### Infrastructure Domain (ARCHITECT Ownership)

Scripts that modify core system configuration or architecture:
- Docker container configurations (docker-compose changes escalate to COORD_PLATFORM)
- Build system modifications
- Package dependency changes

**Key Scripts:**
- `scripts/build-wheelhouse.sh` - Package pre-download

### Operations Domain (COORD_OPS Ownership)

Scripts that execute operational tasks without changing architecture:
- Container lifecycle (start/stop/health)
- CI/CD validation
- Deployment preparation

**Key Scripts:**
- `scripts/health-check.sh`
- `scripts/start-celery.sh`
- `scripts/start-mcp.sh`
- `scripts/pre-deploy-validate.sh`
- `scripts/test-mcp-integration.sh`
- `.claude/scripts/ccw-validation-gate.sh`

### Database Domain (DBA Ownership via COORD_PLATFORM)

Scripts that interact with database state:
- Backups
- Seeding
- Migrations (via Alembic)

**Key Scripts:**
- `scripts/backup-db.sh`
- `scripts/seed_*.py`
- `scripts/ops/backup_database.py`

### Security Domain (SECURITY_AUDITOR Ownership via COORD_RESILIENCE)

Scripts that enforce security policies:
- PII scanning
- Vulnerability fixes
- Secret rotation

**Key Scripts:**
- `scripts/pii-scan.sh`
- `scripts/audit-fix.sh`
- `scripts/sanitize_pii.py`
- `scripts/ops/rotate_secrets.py`

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-01 | COORD_OPS | Initial script ownership matrix |
| 1.1.0 | 2026-01-03 | COORD_OPS | Added stack-backup.sh (unified), deprecated 3 backup scripts |
| 1.2.0 | 2026-01-03 | COORD_OPS | Added start-local.sh, stack-health.sh, validate-mcp-config.sh, backend/scripts/* |

---

*This document is standing context for all AI agents. Update when scripts are added, removed, or ownership changes.*
