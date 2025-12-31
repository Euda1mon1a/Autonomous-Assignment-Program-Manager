# Scripts Guide

Comprehensive guide to operational, development, deployment, and scheduling scripts.

## Table of Contents

- [Overview](#overview)
- [Script Categories](#script-categories)
- [Operations Scripts](#operations-scripts)
- [Development Scripts](#development-scripts)
- [Deployment Scripts](#deployment-scripts)
- [Scheduling Scripts](#scheduling-scripts)
- [Usage Patterns](#usage-patterns)

---

## Overview

This document describes standalone scripts located in the `scripts/` directory. These scripts provide:

- Operational utilities (health checks, backups, secret rotation)
- Development tools (environment setup, test data generation)
- Deployment verification (pre-deploy checks, validation)
- Scheduling utilities (schedule generation, validation, export)

### Script Organization

```
scripts/
├── ops/              # Operations scripts
├── dev/              # Development scripts
├── deploy/           # Deployment scripts
└── scheduling/       # Scheduling utilities
```

### General Requirements

Most scripts require the backend environment:

```bash
cd backend
source venv/bin/activate
python ../scripts/[category]/[script].py [args]
```

---

## Operations Scripts

### health_check.py

Comprehensive system health verification.

**Location:** `scripts/ops/health_check.py`

**Purpose:** Check system health before/after deployment or during monitoring.

**Usage:**
```bash
# Basic health check
python scripts/ops/health_check.py

# JSON output for monitoring systems
python scripts/ops/health_check.py --format json --output health.json

# Critical checks only (faster)
python scripts/ops/health_check.py --critical-only
```

**Checks:**
- Database connectivity and performance
- Redis connectivity
- Celery worker status
- Disk space
- Memory usage
- Configuration validity

**Exit Codes:**
- `0` - All checks passed (healthy)
- `1` - Critical issues found
- `2` - Warnings found

**Example Integration:**
```bash
# CI/CD pipeline
if ! python scripts/ops/health_check.py --critical-only; then
    echo "Health check failed - aborting deployment"
    exit 1
fi
```

---

### backup_database.py

Create PostgreSQL database backups with compression and retention management.

**Location:** `scripts/ops/backup_database.py`

**Purpose:** Automated database backups for disaster recovery.

**Usage:**
```bash
# Create backup with default settings
python scripts/ops/backup_database.py

# Custom backup location
python scripts/ops/backup_database.py --output /backups/manual_backup.dump

# Set retention policy
python scripts/ops/backup_database.py --retention-days 30

# Disable compression (faster but larger)
python scripts/ops/backup_database.py --no-compress

# Verbose output
python scripts/ops/backup_database.py --verbose
```

**Features:**
- Automatic timestamped filenames
- Configurable compression (pg_dump -Z 9)
- Retention policy cleanup
- Custom backup directory

**Automation:**
```bash
# Cron job for daily backups at 2 AM
0 2 * * * cd /app && python scripts/ops/backup_database.py --retention-days 30
```

---

### restore_database.py

Restore database from backup file.

**Location:** `scripts/ops/restore_database.py` (to be created)

**Warning:** This operation will replace all data in the database.

---

### rotate_secrets.py

Rotate application secrets safely.

**Location:** `scripts/ops/rotate_secrets.py`

**Purpose:** Regular security maintenance by rotating secrets.

**Usage:**
```bash
# Rotate all secrets
python scripts/ops/rotate_secrets.py --secret-type all

# Rotate specific secret type
python scripts/ops/rotate_secrets.py --secret-type jwt
python scripts/ops/rotate_secrets.py --secret-type webhook
python scripts/ops/rotate_secrets.py --secret-type redis

# Dry run to preview changes
python scripts/ops/rotate_secrets.py --secret-type all --dry-run

# Create backup before rotation
python scripts/ops/rotate_secrets.py --secret-type all --backup

# Custom .env file location
python scripts/ops/rotate_secrets.py --secret-type all --env-file /path/to/.env
```

**Features:**
- Generates cryptographically secure random secrets
- Backs up .env file before changes
- Dry run mode for testing
- Updates .env file atomically

**Secret Types:**
- `jwt` - JWT secret key (SECRET_KEY)
- `webhook` - Webhook secret (WEBHOOK_SECRET)
- `redis` - Redis password (REDIS_PASSWORD)
- `all` - All of the above

**Post-Rotation Steps:**
```bash
# After rotation, restart services
docker-compose restart backend
docker-compose restart celery-worker
docker-compose restart celery-beat

# If Redis password changed, update Redis container
docker-compose restart redis
```

---

### cleanup_old_data.py

Clean up old data from database.

**Location:** `scripts/ops/cleanup_old_data.py` (to be created)

**Purpose:** Manage database size by removing old records.

---

### export_audit_logs.py

Export audit logs for compliance.

**Location:** `scripts/ops/export_audit_logs.py` (to be created)

**Purpose:** Extract audit trail for reporting or archival.

---

### validate_config.py

Validate system configuration.

**Location:** `scripts/ops/validate_config.py` (to be created)

**Purpose:** Ensure configuration files are valid before deployment.

---

## Development Scripts

### setup_dev_env.py

Automated development environment setup.

**Location:** `scripts/dev/setup_dev_env.py`

**Purpose:** One-command setup for new developers.

**Usage:**
```bash
# Full setup (backend + frontend + database + seed data)
python scripts/dev/setup_dev_env.py

# Backend only
python scripts/dev/setup_dev_env.py --backend-only

# Frontend only
python scripts/dev/setup_dev_env.py --frontend-only

# Skip database initialization
python scripts/dev/setup_dev_env.py --skip-db

# Skip test data seeding
python scripts/dev/setup_dev_env.py --skip-seed
```

**What It Does:**
1. Creates Python virtual environment
2. Installs backend dependencies
3. Installs frontend dependencies (npm)
4. Creates .env file from .env.example
5. Runs database migrations
6. Seeds test data (optional)

**First-Time Setup:**
```bash
# Clone repository
git clone https://github.com/your-org/residency-scheduler.git
cd residency-scheduler

# Start Docker services
docker-compose up -d db redis

# Run setup script
python scripts/dev/setup_dev_env.py

# Start development servers
cd backend && uvicorn app.main:app --reload
cd frontend && npm run dev
```

---

### generate_test_data.py

Generate realistic test data for development.

**Location:** `scripts/dev/generate_test_data.py`

**Purpose:** Create test datasets of various sizes.

**Usage:**
```bash
# Use preset configuration
python scripts/dev/generate_test_data.py --preset small   # 18 residents, 10 faculty
python scripts/dev/generate_test_data.py --preset medium  # 30 residents, 15 faculty
python scripts/dev/generate_test_data.py --preset large   # 50 residents, 20 faculty

# Custom configuration
python scripts/dev/generate_test_data.py --residents 24 --faculty 12

# Specify academic year
python scripts/dev/generate_test_data.py --academic-year 2025

# Generate with assignments (experimental)
python scripts/dev/generate_test_data.py --preset medium --with-assignments

# Clear existing data first
python scripts/dev/generate_test_data.py --preset small --clear-first
```

**Generated Data:**
- People (residents and faculty with realistic names)
- Rotation templates
- Blocks for academic year
- Assignments (optional)

**Example Workflow:**
```bash
# Reset test database
python scripts/dev/generate_test_data.py --preset small --clear-first

# Test with larger dataset
python scripts/dev/generate_test_data.py --preset large

# Generate schedule for testing
python scripts/scheduling/generate_schedule.py --block 10
```

---

### seed_database.py

Seed database with predefined test data.

**Location:** `scripts/dev/seed_database.py` (to be created)

**Purpose:** Quick database seeding with known data.

---

### run_migrations.py

Run database migrations with enhanced output.

**Location:** `scripts/dev/run_migrations.py` (to be created)

**Purpose:** Wrapper around Alembic migrations with better UX.

---

### check_dependencies.py

Check for outdated or vulnerable dependencies.

**Location:** `scripts/dev/check_dependencies.py` (to be created)

**Purpose:** Security and maintenance checks for dependencies.

---

### format_code.py

Format code using black, isort, prettier.

**Location:** `scripts/dev/format_code.py` (to be created)

**Purpose:** Automated code formatting.

---

### run_quality_checks.py

Run linters, type checkers, security scanners.

**Location:** `scripts/dev/run_quality_checks.py` (to be created)

**Purpose:** Quality gate before committing code.

---

## Deployment Scripts

### pre_deploy_check.py

Pre-deployment verification and validation.

**Location:** `scripts/deploy/pre_deploy_check.py`

**Purpose:** Ensure system is ready for deployment.

**Usage:**
```bash
# Run all checks
python scripts/deploy/pre_deploy_check.py

# Skip tests (faster but less thorough)
python scripts/deploy/pre_deploy_check.py --skip-tests

# Strict mode (fail on warnings)
python scripts/deploy/pre_deploy_check.py --strict
```

**Checks:**
- Configuration validation
- Database connectivity
- Migration status (up to date?)
- Secret validation (strong secrets?)
- Dependency check (no conflicts?)
- Test execution
- Security audit

**Exit Codes:**
- `0` - All checks passed
- `1` - One or more checks failed

**CI/CD Integration:**
```yaml
# GitHub Actions
- name: Pre-deployment verification
  run: python scripts/deploy/pre_deploy_check.py --strict
```

---

### post_deploy_verify.py

Post-deployment verification.

**Location:** `scripts/deploy/post_deploy_verify.py` (to be created)

**Purpose:** Verify deployment succeeded.

---

### rollback.py

Rollback deployment.

**Location:** `scripts/deploy/rollback.py` (to be created)

**Purpose:** Automated rollback to previous version.

---

### blue_green_switch.py

Blue-green deployment switch.

**Location:** `scripts/deploy/blue_green_switch.py` (to be created)

**Purpose:** Zero-downtime deployment switching.

---

### canary_promote.py

Promote canary deployment.

**Location:** `scripts/deploy/canary_promote.py` (to be created)

**Purpose:** Gradual rollout promotion.

---

## Scheduling Scripts

### generate_schedule.py

CLI schedule generation without running full application.

**Location:** `scripts/scheduling/generate_schedule.py`

**Purpose:** Standalone schedule generation for automation.

**Usage:**
```bash
# Generate for date range
python scripts/scheduling/generate_schedule.py \
    --start 2025-07-01 --end 2025-09-30

# Generate for specific block
python scripts/scheduling/generate_schedule.py --block 10

# Use specific algorithm
python scripts/scheduling/generate_schedule.py \
    --start 2025-07-01 --end 2025-09-30 \
    --algorithm cp_sat --timeout 300

# Save to file
python scripts/scheduling/generate_schedule.py \
    --block 10 --output schedule.json

# Dry run (don't save to database)
python scripts/scheduling/generate_schedule.py \
    --block 10 --dry-run

# Verbose output
python scripts/scheduling/generate_schedule.py \
    --block 10 --verbose
```

**Features:**
- Multiple algorithm choices (greedy, cp_sat, pulp, hybrid)
- Configurable solver timeout
- JSON export
- Dry run mode
- Violation reporting

**Automation:**
```bash
# Cron job to pre-generate upcoming block schedule
0 0 1 * * cd /app && python scripts/scheduling/generate_schedule.py --block 12 --algorithm cp_sat
```

---

### validate_schedule.py

Validate schedule for compliance and operational requirements.

**Location:** `scripts/scheduling/validate_schedule.py` (exists)

**Purpose:** Human-facing schedule verification.

---

### export_schedule.py

Export schedule to various formats.

**Location:** `scripts/scheduling/export_schedule.py` (to be created)

**Purpose:** Convert schedule to Excel, PDF, iCal, etc.

---

### import_schedule.py

Import schedule from external sources.

**Location:** `scripts/scheduling/import_schedule.py` (to be created)

**Purpose:** Bulk import of schedule data.

---

### compare_schedules.py

Compare two schedules for differences.

**Location:** `scripts/scheduling/compare_schedules.py` (to be created)

**Purpose:** Schedule diff for version comparison.

---

### optimize_schedule.py

Optimize existing schedule.

**Location:** `scripts/scheduling/optimize_schedule.py` (to be created)

**Purpose:** Improve existing schedule without full regeneration.

---

## Usage Patterns

### Daily Operations

```bash
# Morning health check
python scripts/ops/health_check.py

# Check compliance before rounds
python -m app.cli compliance check --verbose

# Export today's schedule
python -m app.cli schedule export \
    --format pdf --output daily_schedule.pdf
```

### Weekly Maintenance

```bash
# Sunday night backup
python scripts/ops/backup_database.py --retention-days 30

# Check for data cleanup
python -m app.cli maintenance cleanup --days 90 --confirm

# Vacuum database
python -m app.cli maintenance vacuum
```

### Monthly Tasks

```bash
# Rotate secrets (first Monday of month)
python scripts/ops/rotate_secrets.py --secret-type all --backup

# Generate compliance report
python -m app.cli compliance report \
    --start $(date -d "1 month ago" +%Y-%m-%d) \
    --format pdf --output monthly_compliance.pdf

# Database statistics
python -m app.cli maintenance stats
```

### Pre-Deployment Checklist

```bash
# 1. Pre-deployment verification
python scripts/deploy/pre_deploy_check.py --strict

# 2. Create backup
python scripts/ops/backup_database.py --output pre_deploy_backup.dump

# 3. Run migrations (if needed)
python -m app.cli schema upgrade

# 4. Post-deployment verification
python scripts/ops/health_check.py

# 5. Validate schedule integrity
python -m app.cli schedule validate --block 10
```

### Development Workflow

```bash
# 1. Set up environment (first time)
python scripts/dev/setup_dev_env.py

# 2. Generate test data
python scripts/dev/generate_test_data.py --preset small

# 3. Test schedule generation
python scripts/scheduling/generate_schedule.py --block 10 --dry-run --verbose

# 4. Run quality checks
python scripts/dev/run_quality_checks.py

# 5. Format code
python scripts/dev/format_code.py
```

---

## Error Handling

All scripts follow consistent exit code conventions:

| Exit Code | Meaning |
|-----------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Warning (degraded but functional) |
| 130 | Interrupted by user (Ctrl+C) |

### Example Error Handling

```bash
# Bash script example
set -e  # Exit on error

if ! python scripts/ops/health_check.py; then
    echo "Health check failed" >&2
    python scripts/ops/backup_database.py  # Emergency backup
    exit 1
fi

# Continue with deployment...
```

```python
# Python script example
import subprocess
import sys

result = subprocess.run(
    ["python", "scripts/ops/health_check.py"],
    capture_output=True,
)

if result.returncode != 0:
    print("Health check failed", file=sys.stderr)
    print(result.stderr.decode(), file=sys.stderr)
    sys.exit(1)

# Continue...
```

---

## Logging and Monitoring

### Capturing Script Output

```bash
# Redirect to log file
python scripts/ops/health_check.py > health.log 2>&1

# Tee to both console and file
python scripts/ops/health_check.py 2>&1 | tee health.log

# Structured logging (JSON format)
python scripts/ops/health_check.py --format json > health.json
```

### Monitoring Integration

```bash
# Prometheus metric export (example)
python scripts/ops/health_check.py --format json | \
    python scripts/monitoring/metrics_exporter.py

# Slack notification on failure
if ! python scripts/ops/health_check.py; then
    curl -X POST $SLACK_WEBHOOK \
        -d '{"text":"Health check failed!"}'
fi
```

---

## See Also

- [CLI Reference](cli-reference.md) - Command-line interface documentation
- [API Documentation](../api/README.md) - REST API reference
- [Deployment Guide](../admin-manual/deployment.md) - Deployment procedures
- [Development Guide](../development/setup.md) - Development setup
