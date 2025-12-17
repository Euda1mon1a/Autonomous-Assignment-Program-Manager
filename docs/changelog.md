# Changelog

All notable changes to Residency Scheduler.

This project follows [Semantic Versioning](https://semver.org/).

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
