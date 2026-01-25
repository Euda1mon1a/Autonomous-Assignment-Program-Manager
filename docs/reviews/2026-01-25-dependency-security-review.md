# Dependency Security Review - January 2026

> **Review Date:** 2026-01-25
> **Reviewer:** Claude (Automated)
> **Scope:** FastAPI, OR-Tools, PuLP, SQLAlchemy, PostgreSQL, Redis, Prometheus, JWT libraries, FHIR R5

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
| **FastAPI** | 0.128.0 | ✅ Current | Pydantic V2 only; V1 dropped |
| **Pydantic** | 2.12.5 | ✅ Current | Well above 2.7.0 minimum |
| **Python** | 3.11+ | ✅ Current | Well above 3.9 minimum |
| **OR-Tools** | 9.8 (pinned) | ✅ Intentional | Pinned to avoid 9.9+ breaking changes |
| **python-jose** | 3.5.0 | ✅ Current | No new advisories |
| **Prometheus client** | 7.1.0 | ✅ N/A | Using instrumentator, not server |

---

### Low Priority / Maintenance

#### SQLAlchemy 2.0.46 Available (Released 2026-01-21)

- **Current:** 2.0.45
- **Available:** 2.0.46
- **Changes:** PostgreSQL JSONB operator fixes, improved type-checker integration, Unicode FK reflection
- **Risk:** Low - patch release with bug fixes
- **Recommendation:** Upgrade to get PostgreSQL JSONB fixes

#### PuLP Version

- **Current:** ≥2.7.0
- **Available:** 3.3.0
- **Risk:** Low - no breaking changes reported
- **Recommendation:** Consider upgrade after testing optimization code

---

### Compatibility Verified

#### FastAPI 0.128.0 + Pydantic V2 Requirement

FastAPI 0.128.0 dropped all `pydantic.v1` compatibility and requires Pydantic ≥2.7.0.

| Requirement | This Repo | Status |
|-------------|-----------|--------|
| Pydantic ≥2.7.0 | 2.12.5 | ✅ Compliant |
| Python ≥3.9 | 3.11+ | ✅ Compliant |
| No pydantic.v1 imports | N/A | ✅ Using V2 syntax |

**No action required** - repo already uses Pydantic V2 patterns throughout.

---

## Items Reviewed - Not Applicable

| Technology | Reason Not Applicable |
|------------|----------------------|
| dbForge 2025.3 | SQL Server tool; this repo uses PostgreSQL |
| AWS Aurora wrappers | Not using Aurora-specific tooling |
| Pydantic V1 migration | Already on V2 (2.12.5) |

---

## Dependency Matrix

### Backend (Python 3.11+)

| Package | Pinned Version | Latest Available | Gap |
|---------|---------------|------------------|-----|
| fastapi | 0.128.0 | 0.128.0 | ✅ Current |
| pydantic | 2.12.5 | 2.12.5 | ✅ Current |
| sqlalchemy | 2.0.45 | 2.0.46 | ⚠️ Patch available |
| redis | 7.1.0 | 7.0.1 (report) | ✅ Ahead |
| ortools | ≥9.8,<9.9 | 9.12 | ✅ Intentionally pinned |
| pulp | ≥2.7.0 | 3.3.0 | ⚠️ Minor gap |
| python-jose | 3.5.0 | 3.5.0 | ✅ Current |

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
2. **[MEDIUM]** Upgrade SQLAlchemy 2.0.45 → 2.0.46 (PostgreSQL JSONB fixes)
3. **[LOW]** Evaluate PuLP 3.3.0 upgrade

---

## Future Considerations

### FHIR R5 Scheduling Model

FHIR R5 introduces scheduling capabilities that align closely with residency block scheduling patterns. This could enable native interoperability with enterprise clinical systems.

#### Relevant R5 Enhancements

| Feature | Benefit for Residency Scheduling |
|---------|----------------------------------|
| **Multi-actor Schedule** | Schedule resource can reference multiple practitioners, locations, teams | Models duty blocks and shared coverage natively |
| **Resource groupings** | Represents groups of resources and responsibilities | Maps directly to rotation blocks, call pools |
| **Standardized availability queries** | Provider search across systems | Could integrate with hospital credentialing/privileging |
| **Slot holds** | Temporary reservations before confirmation | Supports swap workflows, tentative assignments |

#### Architectural Implications

**Current State:** Custom mapping layers between scheduling engine and clinical systems.

**Potential Future State:** FHIR R5-native scheduling could:
- Eliminate custom adapters for clinical system integration
- Enable direct queries of provider availability across enterprise
- Standardize block schedule representation for interoperability
- Support automated credentialing verification via FHIR

#### Recommendation

**Priority:** Low (research/planning phase)

1. Monitor FHIR R5 Scheduling Implementation Guide development
2. Evaluate alignment with current `Block`, `Assignment`, `RotationSchedule` models
3. Consider FHIR facade layer for enterprise integration (future phase)

**Note:** This is forward-looking architecture exploration, not an immediate action item.

---

## References

- [Redis Security Advisories](https://github.com/redis/redis/security/advisories)
- [FastAPI Releases](https://github.com/tiangolo/fastapi/releases)
- [SQLAlchemy 2.0 Migration Guide](https://docs.sqlalchemy.org/en/20/changelog/migration_20.html)
- [OR-Tools Release Notes](https://github.com/google/or-tools/releases)
- [FHIR R5 Schedule Resource](https://hl7.org/fhir/R5/schedule.html)
- [FHIR Scheduling Implementation Guide](https://build.fhir.org/ig/HL7/fhir-scheduling/)

---

*This review was generated as part of routine dependency security monitoring.*
