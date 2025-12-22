# 10-Year Survivability Audit

> **Purpose**: Identify issues that could prevent system operation on an air-gapped network for 10+ years
> **Audit Date**: 2024-12
> **Related**: See `OFFLINE_OPERATIONS.md` for deployment guide

---

## Executive Summary

This audit evaluated the Residency Scheduler codebase for long-term maintainability on an air-gapped network. The system is **fundamentally sound** for offline operation, with core scheduling, ACGME validation, and all essential features working without internet access.

**20 findings identified:**
- 4 Critical (must fix before deployment)
- 6 High (should fix soon)
- 6 Medium (address when convenient)
- 4 Low (nice to have)

---

## Critical Findings (Must Fix)

### C1. Hardcoded Deprecation Dates

**Location**: `backend/app/core/config.py`, various validators
**Issue**: Some validation logic uses hardcoded dates that will fail after certain years
**Impact**: System may reject valid data or behave unexpectedly after date thresholds
**Recommendation**: Use relative date calculations or configurable date parameters

### C2. External Telemetry Dependencies

**Location**: `backend/app/core/telemetry.py`
**Issue**: Telemetry initialization may block startup if external endpoints unreachable
**Impact**: Application startup could hang or fail on air-gapped network
**Recommendation**: Add timeout/fallback for telemetry, graceful degradation when offline

### C3. Undocumented Migration Recovery

**Location**: `backend/alembic/versions/`
**Issue**: No documentation for recovering from failed migrations without internet
**Impact**: Database schema issues could be unrecoverable without external help
**Recommendation**: Add `docs/admin-manual/MIGRATION_RECOVERY.md` with step-by-step procedures

### C4. Missing Seed Data Reproducibility

**Location**: `backend/app/db/seed.py`
**Issue**: Seed scripts may depend on specific data that isn't version-controlled
**Impact**: Fresh installation may fail or produce inconsistent state
**Recommendation**: Ensure all seed data is self-contained and documented

---

## High Severity Findings (Should Fix Soon)

### H1. Python Package Version Pinning

**Location**: `backend/requirements.txt`
**Issue**: Some packages use >= version constraints instead of exact pins
**Impact**: Future pip installs (if ever online) could introduce breaking changes
**Recommendation**: Pin all versions exactly, vendor wheels in `vendor/wheels/`

### H2. Docker Base Image References

**Location**: `backend/Dockerfile`, `frontend/Dockerfile`
**Issue**: Uses `python:3.12-slim` without SHA digest pinning
**Impact**: Image rebuilds may pull different base image versions
**Recommendation**: Pin base images by SHA256 digest for reproducibility

### H3. Frontend Build Dependencies

**Location**: `frontend/package.json`
**Issue**: Node modules not vendored for offline installation
**Impact**: Cannot rebuild frontend without internet access
**Recommendation**: Include `node_modules` archive or use `npm pack` for dependencies

### H4. JWT Secret Rotation Documentation

**Location**: `docs/admin-manual/`
**Issue**: No procedure documented for rotating JWT secrets
**Impact**: Security incident response hindered without clear procedures
**Recommendation**: Document secret rotation process for air-gapped environment

### H5. Database Backup Automation

**Location**: `scripts/`
**Issue**: Backup scripts exist but no automated scheduling documented
**Impact**: Manual backups may be forgotten, risking data loss
**Recommendation**: Add cron job examples and backup verification procedures

### H6. Error Message Localization

**Location**: Various backend files
**Issue**: Error messages are English-only hardcoded strings
**Impact**: Future internationalization would require significant refactoring
**Recommendation**: Low priority, but consider i18n infrastructure

---

## Medium Severity Findings (Address When Convenient)

### M1. Logging Configuration

**Location**: `backend/app/core/logging.py`
**Issue**: Log rotation and retention not configured for long-term operation
**Impact**: Disk space could fill with logs over years of operation
**Recommendation**: Configure logrotate or similar log management

### M2. Health Check Endpoints

**Location**: `backend/app/api/routes/health.py`
**Issue**: Health checks don't verify all critical subsystems
**Impact**: Partial failures may go undetected
**Recommendation**: Add comprehensive health checks for DB, Redis, Celery

### M3. Configuration Documentation

**Location**: `.env.example`
**Issue**: Some environment variables lack documentation
**Impact**: Future administrators may misconfigure system
**Recommendation**: Add comments explaining each variable's purpose and valid values

### M4. Test Data Independence

**Location**: `backend/tests/`
**Issue**: Some tests may assume specific database state
**Impact**: Tests could fail on fresh installation
**Recommendation**: Ensure all tests use fixtures and are self-contained

### M5. Celery Task Idempotency

**Location**: `backend/app/core/celery_app.py`
**Issue**: Not all background tasks are idempotent
**Impact**: Task retries could cause duplicate processing
**Recommendation**: Add idempotency keys to critical tasks

### M6. API Versioning Strategy

**Location**: `backend/app/api/`
**Issue**: No API versioning strategy documented
**Impact**: Future changes may break existing integrations
**Recommendation**: Document versioning approach (URL prefix vs header)

---

## Low Severity Findings (Nice to Have)

### L1. Code Comment Currency

**Location**: Various files
**Issue**: Some comments reference external URLs or services
**Impact**: Comments may become misleading when offline
**Recommendation**: Replace external references with local documentation paths

### L2. Development vs Production Parity

**Location**: `docker-compose.yml` vs `docker-compose.local.yml`
**Issue**: Slight differences between dev and prod configurations
**Impact**: Bugs may only appear in production
**Recommendation**: Minimize configuration drift

### L3. Monitoring Dashboard Export

**Location**: Grafana dashboards
**Issue**: Dashboards may not be exported as JSON for version control
**Impact**: Dashboard configuration could be lost
**Recommendation**: Export and version control Grafana dashboard definitions

### L4. Keyboard Shortcut Documentation

**Location**: Frontend, VBA module
**Issue**: Keyboard shortcuts not comprehensively documented
**Impact**: Users may not discover productivity features
**Recommendation**: Add keyboard shortcut reference guide

---

## Already Addressed

The following survivability concerns have been addressed:

| Concern | Solution |
|---------|----------|
| LLM dependency | Autonomous loop works without LLM (advisory only) |
| Cloud database | PostgreSQL runs locally in Docker |
| External auth | JWT auth is fully local |
| Package downloads | Wheels can be pre-vendored |
| Docker images | Can be saved/loaded for air-gapped transfer |
| Excel integration | VBA module has zero external dependencies |
| Core scheduling | Constraint solver runs entirely locally |
| ACGME validation | All rules implemented in local Python code |

---

## Recommended Priority Order

1. **Immediate**: C1-C4 (Critical findings)
2. **Before deployment**: H1-H5 (High severity)
3. **First maintenance window**: M1-M6 (Medium severity)
4. **Opportunistic**: L1-L4 (Low severity)

---

## Audit Methodology

This audit examined:
- All Python source files for external dependencies
- Docker configurations for reproducibility
- Database migrations for recovery procedures
- Configuration files for hardcoded values
- Documentation for completeness
- Test suites for portability

Tools used:
- Static code analysis (grep, ripgrep)
- Dependency tree inspection
- Docker layer analysis
- Documentation review

---

## Conclusion

The Residency Scheduler is well-architected for long-term offline operation. The core scheduling engine, ACGME compliance validation, and all essential features work without internet access. The critical findings should be addressed before air-gapped deployment, but none represent fundamental architectural issues.

The system follows the principle of **"Python is authoritative, LLM is advisory"** - all decision-making logic is in deterministic Python code that will work identically in 10 years as it does today.

---

*This audit should be repeated annually or when major changes are made to the codebase.*
