# Dependency Security Review - January 2026

> **Review Date:** 2026-01-25
> **Reviewer:** Claude (Automated)
> **Scope:** FastAPI, OR-Tools, PuLP, SQLAlchemy, PostgreSQL, Redis, Prometheus, JWT libraries

---

## Executive Summary

A dependency security scan was evaluated against this repository's tech stack. **One critical finding** (Redis CVE) was identified as partially mitigated, with several docker-compose files still using unpinned Redis images. Most other dependencies are current and secure.

**Overall Risk Level:** ⚠️ MEDIUM (pending Redis image pinning across all environments)

---

## Findings

### Critical Priority

#### CVE-2025-49844: Redis Lua Sandbox Escape (CVSS 9.9)

| Attribute | Value |
|-----------|-------|
| Severity | **CRITICAL** |
| Type | Remote Code Execution |
| Affected | Redis server with Lua scripting enabled |
| Fix | Redis 7.4.2+ or 8.2.2+ |

**Current State:**

| File | Image | Status |
|------|-------|--------|
| `docker-compose.yml` | `redis:7.4.2-alpine` | ✅ Patched |
| `docker-compose.local.yml` | `redis:7-alpine` | ⚠️ Unpinned |
| `.docker/docker-compose.prod.yml` | `redis:7-alpine` | ⚠️ Unpinned |
| `load-tests/docker/docker-compose.load-test.yml` | `redis:7-alpine` | ⚠️ Unpinned |

**Recommendation:** Pin all Redis images to `redis:7.4.2-alpine` or newer.

---

### Verified Secure

| Component | Version | Status | Notes |
|-----------|---------|--------|-------|
| **redis-py** | 7.1.0 | ✅ Current | Ahead of report's 7.0.1 |
| **FastAPI** | 0.128.0 | ✅ Current | CVE-2024-27304 / CVE-2023-50447 affect older versions |
| **SQLAlchemy** | 2.0.45 | ✅ Current | Using 2.x API patterns |
| **OR-Tools** | 9.8 (pinned) | ✅ Intentional | Pinned to avoid 9.9+ breaking changes |
| **python-jose** | 3.5.0 | ✅ Current | No new advisories |
| **Prometheus client** | 7.1.0 | ✅ N/A | Using instrumentator, not server |

---

### Low Priority / Maintenance

#### PuLP Version

- **Current:** ≥2.7.0
- **Available:** 3.3.0
- **Risk:** Low - no breaking changes reported
- **Recommendation:** Consider upgrade after testing optimization code

#### SQLAlchemy Deprecations

- **Status:** Using 2.0.45 with current patterns
- **Risk:** Low - baked queries and legacy patterns removed in 2.x
- **Recommendation:** Audit for any remaining 1.x patterns during routine maintenance

---

## Items Reviewed - Not Applicable

| Technology | Reason Not Applicable |
|------------|----------------------|
| dbForge 2025.3 | SQL Server tool; this repo uses PostgreSQL |
| AWS Aurora wrappers | Not using Aurora-specific tooling |

---

## Dependency Matrix

### Backend (Python 3.11+)

| Package | Pinned Version | Latest Scanned | Gap |
|---------|---------------|----------------|-----|
| fastapi | 0.128.0 | - | Current |
| sqlalchemy | 2.0.45 | - | Current |
| redis | 7.1.0 | 7.0.1 | Ahead |
| ortools | ≥9.8,<9.9 | 9.12 | Intentionally pinned |
| pulp | ≥2.7.0 | 3.3.0 | Minor gap |
| python-jose | 3.5.0 | - | Current |
| pydantic | 2.5.3 | - | Current |

### Infrastructure

| Component | Version | Security Status |
|-----------|---------|-----------------|
| PostgreSQL | 15 | No new advisories |
| Redis Server | 7.4.2 (main) | ✅ Patched |
| Redis Server | 7-alpine (others) | ⚠️ Unpinned |

---

## Action Items

### Immediate (This PR)

- [ ] Document findings (this file)
- [ ] No code changes required for this review PR

### Follow-up Tasks

1. **[HIGH]** Pin Redis images across all docker-compose files
2. **[LOW]** Evaluate PuLP 3.3.0 upgrade
3. **[LOW]** Audit for SQLAlchemy 1.x deprecated patterns

---

## References

- [Redis Security Advisories](https://github.com/redis/redis/security/advisories)
- [FastAPI Releases](https://github.com/tiangolo/fastapi/releases)
- [SQLAlchemy 2.0 Migration Guide](https://docs.sqlalchemy.org/en/20/changelog/migration_20.html)
- [OR-Tools Release Notes](https://github.com/google/or-tools/releases)

---

*This review was generated as part of routine dependency security monitoring.*
