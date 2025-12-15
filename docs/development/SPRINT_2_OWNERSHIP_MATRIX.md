# Sprint 2 File Ownership Matrix

## 25 Parallel Terminal Work Areas - ZERO CONFLICTS

Generated: 2025-12-15

---

## Terminal Assignment Summary

| Group | Terminals | Focus Area | Owner |
|-------|-----------|------------|-------|
| **AUTO** | 1-5 | Backend API & Services | Claude Auto-Spawn |
| **ROUND A** | 6-9 | Frontend Features (New) | Comet |
| **ROUND B** | 10-13 | E2E Testing | Comet |
| **ROUND C** | 14-17 | Documentation | Comet |
| **ROUND D** | 18-21 | DevOps & Scripts | Comet |
| **ROUND E** | 22-25 | Frontend Components & Polish | Comet |

---

## AUTO-SPAWN TERMINALS (1-5) - Backend API & Services

### Terminal 1: Analytics API Endpoint
**Files:**
- `backend/app/api/routes/analytics.py` (CREATE)
- `backend/tests/test_analytics_api.py` (CREATE)

**Scope:** Create REST endpoints exposing analytics engine data
- GET /api/analytics/dashboard
- GET /api/analytics/workload/{person_id}
- GET /api/analytics/compliance/summary
- GET /api/analytics/trends

**Duration:** 45-60 min

---

### Terminal 2: Notifications API Endpoint
**Files:**
- `backend/app/api/routes/notifications.py` (CREATE)
- `backend/tests/test_notifications_api.py` (CREATE)

**Scope:** Create REST endpoints for notification management
- GET /api/notifications
- POST /api/notifications/preferences
- POST /api/notifications/test
- DELETE /api/notifications/{id}

**Duration:** 45-60 min

---

### Terminal 3: Maintenance API Endpoint
**Files:**
- `backend/app/api/routes/maintenance.py` (CREATE)
- `backend/tests/test_maintenance_api.py` (CREATE)

**Scope:** Create REST endpoints for backup/restore operations
- POST /api/maintenance/backup
- POST /api/maintenance/restore
- GET /api/maintenance/backups
- GET /api/maintenance/health

**Duration:** 45-60 min

---

### Terminal 4: PDF Export Service
**Files:**
- `backend/app/services/pdf_export.py` (CREATE)
- `backend/tests/test_pdf_export.py` (CREATE)

**Scope:** Create PDF generation for schedules and reports
- Schedule PDF export
- Compliance report PDF
- Person schedule card PDF
- Uses reportlab (already in requirements)

**Duration:** 60-90 min

---

### Terminal 5: iCal Export Service
**Files:**
- `backend/app/services/ical_export.py` (CREATE)
- `backend/tests/test_ical_export.py` (CREATE)

**Scope:** Create iCalendar (.ics) export functionality
- Personal schedule to iCal
- Block assignments to calendar events
- Absence events
- Recurring pattern support

**Duration:** 45-60 min

---

## COMET ROUND A (6-9) - Frontend Features (New)

### Terminal 6: Reports Feature
**Files:**
- `frontend/src/features/reports/ReportsDashboard.tsx` (CREATE)
- `frontend/src/features/reports/ReportCard.tsx` (CREATE)
- `frontend/src/features/reports/ReportGenerator.tsx` (CREATE)
- `frontend/src/features/reports/index.ts` (CREATE)

**Scope:** Reporting dashboard feature
- Report type selection
- Date range picker
- Export format selection (PDF, Excel, CSV)
- Report preview

**Duration:** 60-90 min

---

### Terminal 7: Notification Center Feature
**Files:**
- `frontend/src/features/notifications/NotificationCenter.tsx` (CREATE)
- `frontend/src/features/notifications/NotificationList.tsx` (CREATE)
- `frontend/src/features/notifications/NotificationPreferences.tsx` (CREATE)
- `frontend/src/features/notifications/index.ts` (CREATE)

**Scope:** In-app notification system
- Notification bell/badge
- Notification dropdown
- Mark as read/unread
- Notification preferences

**Duration:** 60-90 min

---

### Terminal 8: User Preferences Feature
**Files:**
- `frontend/src/features/preferences/PreferencesPanel.tsx` (CREATE)
- `frontend/src/features/preferences/ThemeSelector.tsx` (CREATE)
- `frontend/src/features/preferences/CalendarSettings.tsx` (CREATE)
- `frontend/src/features/preferences/index.ts` (CREATE)

**Scope:** User preference management
- Theme selection (light/dark)
- Calendar view defaults
- Notification preferences
- Export defaults

**Duration:** 45-60 min

---

### Terminal 9: Analytics Dashboard Feature
**Files:**
- `frontend/src/features/analytics/AnalyticsDashboard.tsx` (CREATE)
- `frontend/src/features/analytics/WorkloadChart.tsx` (CREATE)
- `frontend/src/features/analytics/ComplianceGauge.tsx` (CREATE)
- `frontend/src/features/analytics/index.ts` (CREATE)

**Scope:** Analytics visualization dashboard
- Workload distribution charts
- Compliance status gauges
- Trend visualizations
- Date range filtering

**Duration:** 60-90 min

---

## COMET ROUND B (10-13) - E2E Testing

### Terminal 10: Schedule E2E Tests
**Files:**
- `frontend/e2e/schedule.spec.ts` (CREATE)

**Scope:** E2E tests for schedule functionality
- View schedule page
- Navigate between dates
- Filter by person/rotation
- Schedule generation flow

**Duration:** 45-60 min

---

### Terminal 11: Templates E2E Tests
**Files:**
- `frontend/e2e/templates.spec.ts` (CREATE)

**Scope:** E2E tests for template management
- View templates list
- Create new template
- Edit template
- Apply template to schedule

**Duration:** 45-60 min

---

### Terminal 12: Compliance E2E Tests
**Files:**
- `frontend/e2e/compliance.spec.ts` (CREATE)

**Scope:** E2E tests for compliance features
- View compliance dashboard
- Check violation alerts
- Override violations
- Compliance reports

**Duration:** 45-60 min

---

### Terminal 13: Settings E2E Tests
**Files:**
- `frontend/e2e/settings.spec.ts` (CREATE)

**Scope:** E2E tests for settings page
- View settings
- Update rotation settings
- Update notification settings
- Save and persist settings

**Duration:** 30-45 min

---

## COMET ROUND C (14-17) - Documentation

### Terminal 14: Operational Runbooks
**Files:**
- `docs/runbooks/README.md` (CREATE)
- `docs/runbooks/deployment.md` (CREATE)
- `docs/runbooks/incident-response.md` (CREATE)
- `docs/runbooks/backup-restore.md` (CREATE)

**Scope:** Operational procedures documentation
- Step-by-step deployment guide
- Incident response procedures
- Backup/restore procedures
- Rollback procedures

**Duration:** 45-60 min

---

### Terminal 15: User Tutorials
**Files:**
- `docs/tutorials/README.md` (CREATE)
- `docs/tutorials/first-schedule.md` (CREATE)
- `docs/tutorials/managing-absences.md` (CREATE)
- `docs/tutorials/using-templates.md` (CREATE)

**Scope:** Step-by-step user tutorials
- Creating your first schedule
- Managing absences and time-off
- Working with rotation templates
- Generating compliance reports

**Duration:** 45-60 min

---

### Terminal 16: Integration Guides
**Files:**
- `docs/integrations/README.md` (CREATE)
- `docs/integrations/calendar-sync.md` (CREATE)
- `docs/integrations/sso-setup.md` (CREATE)
- `docs/integrations/api-clients.md` (CREATE)

**Scope:** Integration documentation
- Calendar sync (Google, Outlook)
- SSO/SAML setup guide
- API client examples
- Webhook configuration

**Duration:** 45-60 min

---

### Terminal 17: Video Script Outlines
**Files:**
- `docs/video-scripts/README.md` (CREATE)
- `docs/video-scripts/quick-start.md` (CREATE)
- `docs/video-scripts/admin-overview.md` (CREATE)
- `docs/video-scripts/advanced-features.md` (CREATE)

**Scope:** Video tutorial script outlines
- Quick start walkthrough
- Admin features overview
- Advanced scheduling features
- Compliance management

**Duration:** 30-45 min

---

## COMET ROUND D (18-21) - DevOps & Scripts

### Terminal 18: Data Migration Scripts
**Files:**
- `scripts/data-migration/README.md` (CREATE)
- `scripts/data-migration/export_data.py` (CREATE)
- `scripts/data-migration/import_data.py` (CREATE)
- `scripts/data-migration/validate_migration.py` (CREATE)

**Scope:** Data migration tooling
- Export existing data
- Import from legacy systems
- Validate data integrity
- Rollback support

**Duration:** 60-90 min

---

### Terminal 19: Health Check Scripts
**Files:**
- `scripts/health-checks/README.md` (CREATE)
- `scripts/health-checks/check_api.sh` (CREATE)
- `scripts/health-checks/check_database.sh` (CREATE)
- `scripts/health-checks/check_services.sh` (CREATE)

**Scope:** System health monitoring scripts
- API endpoint health
- Database connectivity
- External service status
- Aggregated health report

**Duration:** 30-45 min

---

### Terminal 20: Performance Testing Workflow
**Files:**
- `.github/workflows/performance.yml` (CREATE)
- `scripts/performance/load_test.py` (CREATE)
- `scripts/performance/README.md` (CREATE)

**Scope:** Performance testing automation
- Load testing with locust
- Performance benchmarks
- Automated performance regression tests
- Results reporting

**Duration:** 45-60 min

---

### Terminal 21: Database Seeding Scripts
**Files:**
- `scripts/seed/README.md` (CREATE)
- `scripts/seed/seed_demo_data.py` (CREATE)
- `scripts/seed/seed_test_data.py` (CREATE)
- `scripts/seed/clear_data.py` (CREATE)

**Scope:** Database seeding for dev/test
- Demo data generation
- Test fixture creation
- Data cleanup utilities
- Realistic sample schedules

**Duration:** 45-60 min

---

## COMET ROUND E (22-25) - Frontend Components & Polish

### Terminal 22: Chart Components
**Files:**
- `frontend/src/components/charts/BarChart.tsx` (CREATE)
- `frontend/src/components/charts/LineChart.tsx` (CREATE)
- `frontend/src/components/charts/PieChart.tsx` (CREATE)
- `frontend/src/components/charts/index.ts` (CREATE)

**Scope:** Reusable chart components
- Bar chart for workload
- Line chart for trends
- Pie chart for distribution
- Consistent styling/theming

**Duration:** 60-90 min

---

### Terminal 23: Print Styles & Export UI
**Files:**
- `frontend/src/styles/print.css` (CREATE)
- `frontend/src/components/PrintableSchedule.tsx` (CREATE)
- `frontend/src/components/ExportButton.tsx` (CREATE)

**Scope:** Print and export functionality
- Print-optimized CSS
- Printable schedule view
- Export dropdown component
- Format selection UI

**Duration:** 45-60 min

---

### Terminal 24: Accessibility Improvements
**Files:**
- `frontend/src/components/a11y/SkipLink.tsx` (CREATE)
- `frontend/src/components/a11y/FocusTrap.tsx` (CREATE)
- `frontend/src/components/a11y/ScreenReaderOnly.tsx` (CREATE)
- `frontend/src/components/a11y/index.ts` (CREATE)

**Scope:** Accessibility enhancements
- Skip to content links
- Focus management
- Screen reader utilities
- ARIA improvements

**Duration:** 45-60 min

---

### Terminal 25: Help System Components
**Files:**
- `frontend/src/components/help/HelpTooltip.tsx` (CREATE)
- `frontend/src/components/help/ContextualHelp.tsx` (CREATE)
- `frontend/src/components/help/KeyboardShortcuts.tsx` (CREATE)
- `frontend/src/components/help/index.ts` (CREATE)

**Scope:** In-app help system
- Contextual help tooltips
- Keyboard shortcut reference
- Feature hints/tours
- Help panel component

**Duration:** 45-60 min

---

## Conflict Prevention Rules

1. **No shared file editing** - Each terminal owns specific files
2. **No cross-directory dependencies** - Features are self-contained
3. **Import only from existing stable code** - Don't import from other terminal's new code
4. **Create index.ts files** - Each feature exports through index.ts
5. **Use placeholder data** - Don't depend on other terminal's API endpoints

---

## Pre-Flight Checklist

- [ ] All 25 areas confirmed as NEW (no existing files)
- [ ] No file path overlaps between terminals
- [ ] Each terminal has <5 primary files
- [ ] Duration estimates: 30-90 minutes each
- [ ] Dependencies only on existing stable code
