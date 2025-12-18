# Roadmap

> **Last Updated:** 2025-12-18

This document outlines the planned features and improvements for the Residency Scheduler project.

---

## Current Release: v1.0.0 (Production Ready)

The current release includes:
- ✅ Complete scheduling engine with ACGME compliance
- ✅ Role-based access control (8 roles)
- ✅ Absence management with military-specific tracking
- ✅ Procedure credentialing and certification tracking
- ✅ 3-tier resilience framework
- ✅ Analytics dashboard with fairness metrics
- ✅ Swap marketplace with auto-matching
- ✅ Audit logging system
- ✅ Rate limiting and security hardening
- ✅ Export functionality (Excel, PDF, ICS)

---

## Upcoming: v1.1.0 (Q1 2026)

### Email Notifications
- [ ] SMTP integration for automated alerts
- [ ] Certification expiration reminders
- [ ] Schedule change notifications
- [ ] Swap request notifications
- [ ] Configurable notification preferences

### Bulk Import/Export Enhancements
- [ ] Batch schedule import from Excel
- [ ] Template-based bulk assignment
- [ ] Export scheduling analytics to PDF
- [ ] Integration with external calendar systems

### FMIT Integration Improvements
- [ ] Enhanced FMIT week detection
- [ ] Automated conflict resolution for FMIT swaps
- [ ] FMIT-specific reporting

---

## Planned: v1.2.0 (Q2 2026)

### Mobile Application
- [ ] React Native mobile app
- [ ] Push notifications
- [ ] Offline schedule viewing
- [ ] Quick swap requests from mobile

### Advanced Analytics
- [ ] Predictive scheduling recommendations
- [ ] Historical trend analysis
- [ ] Workload forecasting
- [ ] Custom report builder

---

## Future Considerations (v2.0+)

### Enterprise Features
- [ ] LDAP/Active Directory integration
- [ ] SAML/SSO authentication
- [ ] Multi-program support
- [ ] Cross-institutional scheduling
- [ ] Custom workflow automation

### AI/ML Enhancements
- [ ] AI-powered schedule optimization
- [ ] Anomaly detection in scheduling patterns
- [ ] Natural language schedule queries
- [ ] Automated compliance recommendations

### Integration Ecosystem
- [ ] MyEvaluations integration
- [ ] EMR system connectivity
- [ ] Time tracking system sync
- [ ] External API for third-party apps

---

## Technical Debt & Infrastructure

### High Priority
- [ ] Refactor oversized route files (resilience.py, constraints.py)
- [ ] Add frontend feature tests (8 features untested)
- [ ] Consolidate documentation (docs/ vs wiki/)
- [x] Fix npm security vulnerabilities - See `scripts/audit-fix.sh`

### Medium Priority
- [ ] Split frontend hooks.ts by domain
- [ ] Improve frontend type documentation
- [x] Standardize error response formats - Documented in `docs/CI_CD_RECOMMENDATIONS.md`
- [x] Add comprehensive API documentation - Added multiple docs in this session

### Low Priority
- [ ] Frontend component reorganization
- [ ] Backend service grouping standardization
- [x] Enhanced ESLint configuration - Added `eslint.config.js` for ESLint v9
- [ ] Playwright test expansion

### Recently Completed
- [x] Pre-deployment validation script (`scripts/pre-deploy-validate.sh`)
- [x] TODO tracking documentation (`docs/TODO_TRACKER.md`)
- [x] Code complexity analysis (`docs/CODE_COMPLEXITY_ANALYSIS.md`)
- [x] Security scanning guide (`docs/SECURITY_SCANNING.md`)
- [x] CI/CD improvement recommendations (`docs/CI_CD_RECOMMENDATIONS.md`)
- [x] Implementation tracker for swap system (`docs/IMPLEMENTATION_TRACKER.md`)
- [x] TypeScript type-check configuration (`frontend/tsconfig.typecheck.json`)

---

## Contributing to the Roadmap

We welcome community input on prioritization and feature requests. Please:

1. Open a GitHub Issue for new feature suggestions
2. Comment on existing issues to show interest
3. Submit PRs for items marked as "Help Wanted"

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

---

## Version History

| Version | Release Date | Highlights |
|---------|--------------|------------|
| v1.0.0 | 2025-01-15 | Initial production release |

---

## Release Philosophy

- **Semantic Versioning**: We follow semver (MAJOR.MINOR.PATCH)
- **Quarterly Releases**: Major features targeted quarterly
- **Continuous Improvements**: Security and bug fixes released as needed
- **Backwards Compatibility**: Breaking changes only in major versions
