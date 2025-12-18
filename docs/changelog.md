# Changelog

All notable changes to Residency Scheduler.

This project follows [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

### :test_tube: Load Testing Infrastructure (Session 10)

Added comprehensive load testing framework for healthcare scheduling system validation.

#### k6 Load Testing Framework
- **k6.config.js** - Main configuration with thresholds (p95 < 500ms), stages, and environment configs
- **utils/auth.js** - JWT authentication helpers with token caching for 5 user roles
- **utils/data-generators.js** - Realistic test data generation (persons, assignments, absences)
- **docker-compose.k6.yml** - Containerized k6 with optional InfluxDB/Grafana

#### Load Test Scenarios
- **schedule-generation.js** - Concurrent schedule generation (1→10 users, p95 < 30s)
- **concurrent-users.js** - Multi-user simulation (10→100 VUs with think time)
- **api-baseline.js** - Baseline latency measurements (p50, p95, p99)
- **rate-limit-attack.js** - Security testing (brute force, API flood, distributed attack)
- **auth-security.js** - JWT validation under 100 concurrent users

#### pytest Performance Tests
- **test_acgme_load.py** - ACGME validation performance (100 residents < 5s)
- **test_connection_pool.py** - DB pool saturation, leak detection, recovery
- **test_idempotency_load.py** - Concurrent duplicate prevention (100 requests → 1 record)
- **test_resilience_load.py** - Defense level escalation, N-1/N-2 analysis performance

#### Infrastructure Configuration
- **monitoring/prometheus/rules/load-testing.yml** - SLO alerts and recording rules
- **nginx/conf.d/load-testing.conf** - Enhanced connection pooling (100 keepalive)
- **nginx/snippets/loadtest-locations.conf** - Dedicated load test endpoints

#### SLO Definitions
| Metric | Normal | Under Load | Critical |
|--------|--------|------------|----------|
| API P95 Latency | < 500ms | < 2s | > 5s |
| Schedule Generation P95 | < 180s | < 300s | > 600s |
| ACGME Validation P95 | < 2s | < 5s | > 10s |
| Error Rate | < 0.1% | < 1% | > 5% |
| Availability | 99.99% | 99.9% | < 99% |

---

## [1.0.0] - 2025-01-15

### :sparkles: Features

- **Schedule Management**
    - Block-based scheduling (730 blocks per academic year)
    - Rotation template management with capacity limits
    - Smart assignment using constraint-based algorithms
    - Faculty supervision automatic assignment

- **ACGME Compliance**
    - 80-hour rule monitoring
    - 1-in-7 day off enforcement
    - Supervision ratio validation (PGY-1: 1:2, PGY-2/3: 1:4)
    - Violation tracking with severity levels

- **User Management**
    - JWT-based authentication
    - Role-based access control (8 roles)
    - Rate limiting on auth endpoints

- **Absence Management**
    - Multiple absence types (vacation, deployment, TDY, medical)
    - Calendar and list views
    - Automatic availability updates

- **Swap Marketplace**
    - 5-factor auto-matching algorithm
    - Request/response workflow
    - ACGME compliance validation

- **Resilience Framework**
    - 80% utilization threshold monitoring
    - N-1/N-2 contingency analysis
    - Defense in Depth (5 safety levels)
    - Celery background health checks

- **Analytics Dashboard**
    - Coverage metrics
    - Fairness analysis
    - Workload distribution
    - Pareto optimization

- **Export Functionality**
    - Excel schedule export
    - ICS calendar export
    - WebCal subscriptions
    - PDF reports

---

## Planned Features

See [ROADMAP.md](https://github.com/Euda1mon1a/Autonomous-Assignment-Program-Manager/blob/main/ROADMAP.md) for upcoming features.

### v1.1.0 (Q1 2026)

- [ ] Email notifications
- [ ] Bulk import/export enhancements
- [ ] FMIT integration improvements

### v1.2.0 (Q2 2026)

- [ ] Mobile application
- [ ] Advanced analytics
- [ ] Custom report builder

### v2.0+ (Future)

- [ ] LDAP/SSO integration
- [ ] Multi-program support
- [ ] AI-powered optimization

---

## Version History

<div class="version-timeline">

<div class="version-item latest" markdown>
### v1.0.0
**Released:** January 15, 2025

Initial production release with complete scheduling engine, ACGME compliance, and resilience framework.
</div>

</div>
