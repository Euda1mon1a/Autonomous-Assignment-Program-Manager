# Sprint 2 - Copy-Paste Prompts for Comet Assistant

## READY FOR COMET - 25 TERMINAL PROMPTS

Generated: 2025-12-15

---

## AUTO-SPAWN PROMPTS (Terminals 1-5)

### Terminal 1: Analytics API
```
Create REST API endpoints for analytics in backend/app/api/routes/analytics.py

FILES TO CREATE:
- backend/app/api/routes/analytics.py
- backend/tests/test_analytics_api.py

ENDPOINTS:
- GET /api/analytics/dashboard - Overall analytics summary
- GET /api/analytics/workload/{person_id} - Person workload stats
- GET /api/analytics/compliance/summary - Compliance metrics
- GET /api/analytics/trends - Historical trends data

REQUIREMENTS:
- Use existing analytics engine from backend/app/analytics/
- Add router to backend/app/api/routes/__init__.py
- Include pagination for large datasets
- Add date range filtering
- Write pytest tests for all endpoints

DO NOT modify any files outside your scope.
```

### Terminal 2: Notifications API
```
Create REST API endpoints for notifications in backend/app/api/routes/notifications.py

FILES TO CREATE:
- backend/app/api/routes/notifications.py
- backend/tests/test_notifications_api.py

ENDPOINTS:
- GET /api/notifications - List user notifications
- POST /api/notifications/preferences - Update notification preferences
- POST /api/notifications/test - Send test notification
- DELETE /api/notifications/{id} - Dismiss notification
- PATCH /api/notifications/{id}/read - Mark as read

REQUIREMENTS:
- Use existing notification service from backend/app/notifications/
- Add router to backend/app/api/routes/__init__.py
- Support filtering by read/unread status
- Include pagination
- Write pytest tests

DO NOT modify any files outside your scope.
```

### Terminal 3: Maintenance API
```
Create REST API endpoints for maintenance operations in backend/app/api/routes/maintenance.py

FILES TO CREATE:
- backend/app/api/routes/maintenance.py
- backend/tests/test_maintenance_api.py

ENDPOINTS:
- POST /api/maintenance/backup - Trigger backup
- POST /api/maintenance/restore - Restore from backup
- GET /api/maintenance/backups - List available backups
- GET /api/maintenance/health - System health check
- DELETE /api/maintenance/backups/{id} - Delete backup

REQUIREMENTS:
- Use existing maintenance module from backend/app/maintenance/
- Add router to backend/app/api/routes/__init__.py
- Require admin role for all endpoints
- Include backup metadata (size, timestamp, type)
- Write pytest tests

DO NOT modify any files outside your scope.
```

### Terminal 4: PDF Export Service
```
Create PDF export service for schedules and reports in backend/app/services/pdf_export.py

FILES TO CREATE:
- backend/app/services/pdf_export.py
- backend/tests/test_pdf_export.py

FEATURES:
- Schedule PDF export (weekly/monthly views)
- Compliance report PDF
- Person schedule card PDF
- Multi-page support
- Header/footer with metadata

REQUIREMENTS:
- Use reportlab (already in requirements.txt)
- Create PDFExportService class
- Support date range selection
- Include branding/logo placeholder
- Generate professional-looking output
- Write pytest tests with PDF verification

DO NOT modify any files outside your scope.
```

### Terminal 5: iCal Export Service
```
Create iCalendar export service in backend/app/services/ical_export.py

FILES TO CREATE:
- backend/app/services/ical_export.py
- backend/tests/test_ical_export.py

FEATURES:
- Personal schedule to .ics file
- Block assignments as calendar events
- Absence events
- All-day vs timed events
- Event descriptions with details

REQUIREMENTS:
- Use icalendar library (add to requirements if needed)
- Create ICalExportService class
- Support single person or full schedule export
- Include event reminders
- Generate RFC 5545 compliant output
- Write pytest tests

DO NOT modify any files outside your scope.
```

---

## COMET ROUND A PROMPTS (Terminals 6-9)

### Terminal 6: Reports Feature
```
Create reports dashboard feature in frontend/src/features/reports/

FILES TO CREATE:
- frontend/src/features/reports/ReportsDashboard.tsx
- frontend/src/features/reports/ReportCard.tsx
- frontend/src/features/reports/ReportGenerator.tsx
- frontend/src/features/reports/index.ts

COMPONENTS:
- ReportsDashboard: Main container with report type grid
- ReportCard: Individual report type card with icon/description
- ReportGenerator: Form for date range and export options

REQUIREMENTS:
- Use existing UI components from frontend/src/components/
- Use Tailwind CSS for styling
- Support report types: Schedule, Compliance, Workload, Audit
- Include date range picker
- Export format selection (PDF, Excel, CSV)
- Loading states during generation

DO NOT modify any files outside your scope.
```

### Terminal 7: Notification Center Feature
```
Create notification center feature in frontend/src/features/notifications/

FILES TO CREATE:
- frontend/src/features/notifications/NotificationCenter.tsx
- frontend/src/features/notifications/NotificationList.tsx
- frontend/src/features/notifications/NotificationPreferences.tsx
- frontend/src/features/notifications/NotificationItem.tsx
- frontend/src/features/notifications/index.ts

COMPONENTS:
- NotificationCenter: Bell icon with badge and dropdown
- NotificationList: Scrollable list of notifications
- NotificationItem: Individual notification with actions
- NotificationPreferences: Settings for notification types

REQUIREMENTS:
- Use existing UI components
- Badge shows unread count
- Mark as read on click
- Mark all as read button
- Filter by type (schedule, compliance, system)
- Empty state for no notifications

DO NOT modify any files outside your scope.
```

### Terminal 8: User Preferences Feature
```
Create user preferences feature in frontend/src/features/preferences/

FILES TO CREATE:
- frontend/src/features/preferences/PreferencesPanel.tsx
- frontend/src/features/preferences/ThemeSelector.tsx
- frontend/src/features/preferences/CalendarSettings.tsx
- frontend/src/features/preferences/ExportDefaults.tsx
- frontend/src/features/preferences/index.ts

COMPONENTS:
- PreferencesPanel: Main container with sections
- ThemeSelector: Light/dark/system theme toggle
- CalendarSettings: Default view, week start, time format
- ExportDefaults: Default export format preferences

REQUIREMENTS:
- Use existing UI components
- Persist preferences to localStorage
- Apply theme immediately on change
- Group settings into logical sections
- Save/Cancel buttons

DO NOT modify any files outside your scope.
```

### Terminal 9: Analytics Dashboard Feature
```
Create analytics dashboard feature in frontend/src/features/analytics/

FILES TO CREATE:
- frontend/src/features/analytics/AnalyticsDashboard.tsx
- frontend/src/features/analytics/WorkloadChart.tsx
- frontend/src/features/analytics/ComplianceGauge.tsx
- frontend/src/features/analytics/TrendLine.tsx
- frontend/src/features/analytics/index.ts

COMPONENTS:
- AnalyticsDashboard: Grid layout of analytics widgets
- WorkloadChart: Bar chart showing assignments per person
- ComplianceGauge: Circular gauge for compliance percentage
- TrendLine: Line chart for historical trends

REQUIREMENTS:
- Use placeholder data (API may not exist yet)
- Use CSS/SVG for simple charts (no external lib required)
- Responsive grid layout
- Date range selector
- Loading skeletons
- Refresh button

DO NOT modify any files outside your scope.
```

---

## COMET ROUND B PROMPTS (Terminals 10-13)

### Terminal 10: Schedule E2E Tests
```
Create E2E tests for schedule functionality in frontend/e2e/schedule.spec.ts

FILE TO CREATE:
- frontend/e2e/schedule.spec.ts

TEST CASES:
- View schedule page loads correctly
- Navigate to next/previous week
- Navigate to next/previous month
- Filter by person
- Filter by rotation type
- Click on assignment shows details
- Schedule generation flow (if accessible)
- Empty state when no assignments

REQUIREMENTS:
- Use Playwright (already configured)
- Follow existing e2e test patterns in frontend/e2e/
- Add test IDs to components if needed via comments
- Test both authenticated and unauthenticated states
- Include mobile viewport tests

DO NOT modify any files outside frontend/e2e/schedule.spec.ts
```

### Terminal 11: Templates E2E Tests
```
Create E2E tests for templates functionality in frontend/e2e/templates.spec.ts

FILE TO CREATE:
- frontend/e2e/templates.spec.ts

TEST CASES:
- View templates list page
- Search/filter templates
- View template details
- Create new template flow
- Edit existing template
- Delete template with confirmation
- Apply template to schedule
- Template validation errors

REQUIREMENTS:
- Use Playwright (already configured)
- Follow existing e2e test patterns
- Test CRUD operations
- Test form validation
- Include accessibility checks

DO NOT modify any files outside frontend/e2e/templates.spec.ts
```

### Terminal 12: Compliance E2E Tests
```
Create E2E tests for compliance features in frontend/e2e/compliance.spec.ts

FILE TO CREATE:
- frontend/e2e/compliance.spec.ts

TEST CASES:
- View compliance dashboard
- See violation alerts
- Filter violations by type
- Filter violations by severity
- View violation details
- Override violation with reason
- Compliance report generation
- Historical compliance view

REQUIREMENTS:
- Use Playwright (already configured)
- Follow existing e2e test patterns
- Test warning and error states
- Test override flow with confirmation
- Include date range filtering tests

DO NOT modify any files outside frontend/e2e/compliance.spec.ts
```

### Terminal 13: Settings E2E Tests
```
Create E2E tests for settings page in frontend/e2e/settings.spec.ts

FILE TO CREATE:
- frontend/e2e/settings.spec.ts

TEST CASES:
- View settings page
- Update rotation settings
- Update notification settings
- Update display preferences
- Save settings successfully
- Cancel discards changes
- Validation error handling
- Settings persist after reload

REQUIREMENTS:
- Use Playwright (already configured)
- Follow existing e2e test patterns
- Test form interactions
- Test save/cancel flow
- Verify persistence

DO NOT modify any files outside frontend/e2e/settings.spec.ts
```

---

## COMET ROUND C PROMPTS (Terminals 14-17)

### Terminal 14: Operational Runbooks
```
Create operational runbooks in docs/runbooks/

FILES TO CREATE:
- docs/runbooks/README.md
- docs/runbooks/deployment.md
- docs/runbooks/incident-response.md
- docs/runbooks/backup-restore.md
- docs/runbooks/rollback.md

CONTENT:
- README: Index of all runbooks with quick links
- deployment: Step-by-step deployment procedures
- incident-response: On-call procedures, escalation paths
- backup-restore: Backup procedures, restore steps
- rollback: How to rollback failed deployments

REQUIREMENTS:
- Use clear numbered steps
- Include command examples
- Add troubleshooting sections
- Include contact/escalation info placeholders
- Add estimated time for each procedure
- Cross-reference other docs where relevant

DO NOT modify any files outside docs/runbooks/
```

### Terminal 15: User Tutorials
```
Create step-by-step user tutorials in docs/tutorials/

FILES TO CREATE:
- docs/tutorials/README.md
- docs/tutorials/first-schedule.md
- docs/tutorials/managing-absences.md
- docs/tutorials/using-templates.md
- docs/tutorials/compliance-reports.md

CONTENT:
- README: Tutorial index with difficulty levels
- first-schedule: Creating your first schedule (beginner)
- managing-absences: Adding and managing time-off
- using-templates: Working with rotation templates
- compliance-reports: Generating compliance reports

REQUIREMENTS:
- Step-by-step numbered instructions
- Include screenshots placeholders [Screenshot: description]
- Add "What you'll learn" sections
- Include estimated completion time
- Add "Next steps" at the end of each

DO NOT modify any files outside docs/tutorials/
```

### Terminal 16: Integration Guides
```
Create integration documentation in docs/integrations/

FILES TO CREATE:
- docs/integrations/README.md
- docs/integrations/calendar-sync.md
- docs/integrations/sso-setup.md
- docs/integrations/api-clients.md
- docs/integrations/webhooks.md

CONTENT:
- README: Overview of available integrations
- calendar-sync: Google Calendar and Outlook sync
- sso-setup: SAML/OAuth SSO configuration
- api-clients: Example API clients (Python, JS)
- webhooks: Webhook configuration and payloads

REQUIREMENTS:
- Include configuration examples
- Add code snippets where applicable
- Include troubleshooting sections
- Document required permissions
- Add security considerations

DO NOT modify any files outside docs/integrations/
```

### Terminal 17: Video Script Outlines
```
Create video tutorial script outlines in docs/video-scripts/

FILES TO CREATE:
- docs/video-scripts/README.md
- docs/video-scripts/quick-start.md
- docs/video-scripts/admin-overview.md
- docs/video-scripts/advanced-features.md
- docs/video-scripts/troubleshooting.md

CONTENT:
- README: Video series overview and production notes
- quick-start: 5-minute getting started (script + shot list)
- admin-overview: Admin features walkthrough
- advanced-features: Power user features
- troubleshooting: Common issues and solutions

REQUIREMENTS:
- Include timing for each section
- Add [SCREEN: description] markers
- Add [VOICEOVER: script] sections
- Include B-roll suggestions
- Keep scripts concise and scannable

DO NOT modify any files outside docs/video-scripts/
```

---

## COMET ROUND D PROMPTS (Terminals 18-21)

### Terminal 18: Data Migration Scripts
```
Create data migration scripts in scripts/data-migration/

FILES TO CREATE:
- scripts/data-migration/README.md
- scripts/data-migration/export_data.py
- scripts/data-migration/import_data.py
- scripts/data-migration/validate_migration.py
- scripts/data-migration/requirements.txt

FEATURES:
- export_data.py: Export all data to JSON/CSV
- import_data.py: Import from legacy formats
- validate_migration.py: Verify data integrity post-migration

REQUIREMENTS:
- Use Python 3.11+
- Include CLI arguments (argparse)
- Add progress bars for large datasets
- Include dry-run mode
- Add detailed logging
- Handle errors gracefully with rollback

DO NOT modify any files outside scripts/data-migration/
```

### Terminal 19: Health Check Scripts
```
Create health check scripts in scripts/health-checks/

FILES TO CREATE:
- scripts/health-checks/README.md
- scripts/health-checks/check_api.sh
- scripts/health-checks/check_database.sh
- scripts/health-checks/check_services.sh
- scripts/health-checks/run_all_checks.sh

FEATURES:
- check_api.sh: API endpoint health checks
- check_database.sh: Database connectivity and performance
- check_services.sh: External service dependencies
- run_all_checks.sh: Aggregated health report

REQUIREMENTS:
- Use bash with proper error handling
- Return proper exit codes
- Output JSON for programmatic use
- Include timeout handling
- Add verbose mode flag
- Color-coded output for terminals

DO NOT modify any files outside scripts/health-checks/
```

### Terminal 20: Performance Testing
```
Create performance testing workflow in .github/workflows/ and scripts/

FILES TO CREATE:
- .github/workflows/performance.yml
- scripts/performance/load_test.py
- scripts/performance/README.md
- scripts/performance/requirements.txt

FEATURES:
- GitHub Action for performance testing
- Load test script using locust
- Configurable concurrent users
- Response time thresholds
- Results reporting

REQUIREMENTS:
- Run on manual trigger or schedule
- Use locust for load testing
- Test critical API endpoints
- Generate HTML report
- Fail if thresholds exceeded
- Store results as artifacts

DO NOT modify any files outside your scope.
```

### Terminal 21: Database Seeding Scripts
```
Create database seeding scripts in scripts/seed/

FILES TO CREATE:
- scripts/seed/README.md
- scripts/seed/seed_demo_data.py
- scripts/seed/seed_test_data.py
- scripts/seed/clear_data.py
- scripts/seed/requirements.txt

FEATURES:
- seed_demo_data.py: Realistic demo data for presentations
- seed_test_data.py: Test fixtures for development
- clear_data.py: Clean database (with confirmation)

REQUIREMENTS:
- Use Python 3.11+
- Use faker for realistic data
- Create related data (people, schedules, absences)
- Include CLI arguments
- Add confirmation for destructive operations
- Support different data volumes (small/medium/large)

DO NOT modify any files outside scripts/seed/
```

---

## COMET ROUND E PROMPTS (Terminals 22-25)

### Terminal 22: Chart Components
```
Create reusable chart components in frontend/src/components/charts/

FILES TO CREATE:
- frontend/src/components/charts/BarChart.tsx
- frontend/src/components/charts/LineChart.tsx
- frontend/src/components/charts/PieChart.tsx
- frontend/src/components/charts/ChartContainer.tsx
- frontend/src/components/charts/index.ts

COMPONENTS:
- BarChart: Horizontal/vertical bar chart
- LineChart: Time series line chart
- PieChart: Pie/donut chart
- ChartContainer: Wrapper with title and legend

REQUIREMENTS:
- Use SVG for rendering (no external chart library)
- Support dark/light themes
- Responsive sizing
- Animated transitions (CSS)
- Accessible with ARIA labels
- Accept data as props with TypeScript types

DO NOT modify any files outside frontend/src/components/charts/
```

### Terminal 23: Print & Export UI
```
Create print styles and export UI in frontend/src/

FILES TO CREATE:
- frontend/src/styles/print.css
- frontend/src/components/PrintableSchedule.tsx
- frontend/src/components/ExportButton.tsx
- frontend/src/components/ExportModal.tsx

FEATURES:
- print.css: Print-optimized stylesheet
- PrintableSchedule: Schedule view optimized for printing
- ExportButton: Dropdown with export options
- ExportModal: Export configuration dialog

REQUIREMENTS:
- Hide navigation/interactive elements in print
- Page break handling
- Black and white friendly
- Export format selection (PDF, Excel, iCal)
- Date range selection in modal

DO NOT modify any files outside your scope.
```

### Terminal 24: Accessibility Components
```
Create accessibility utility components in frontend/src/components/a11y/

FILES TO CREATE:
- frontend/src/components/a11y/SkipLink.tsx
- frontend/src/components/a11y/FocusTrap.tsx
- frontend/src/components/a11y/ScreenReaderOnly.tsx
- frontend/src/components/a11y/LiveRegion.tsx
- frontend/src/components/a11y/index.ts

COMPONENTS:
- SkipLink: Skip to main content link
- FocusTrap: Trap focus within modals
- ScreenReaderOnly: Visually hidden but accessible text
- LiveRegion: Announce dynamic content changes

REQUIREMENTS:
- Follow WCAG 2.1 AA guidelines
- Use semantic HTML
- Proper ARIA attributes
- Keyboard navigation support
- Test with screen reader patterns

DO NOT modify any files outside frontend/src/components/a11y/
```

### Terminal 25: Help System Components
```
Create help system components in frontend/src/components/help/

FILES TO CREATE:
- frontend/src/components/help/HelpTooltip.tsx
- frontend/src/components/help/ContextualHelp.tsx
- frontend/src/components/help/KeyboardShortcuts.tsx
- frontend/src/components/help/HelpPanel.tsx
- frontend/src/components/help/index.ts

COMPONENTS:
- HelpTooltip: Info icon with hover tooltip
- ContextualHelp: Expandable help section
- KeyboardShortcuts: Keyboard shortcut reference modal
- HelpPanel: Slide-out help panel

REQUIREMENTS:
- Use existing UI components
- Support markdown in help content
- Keyboard accessible (Escape to close)
- Persist "don't show again" preferences
- Link to full documentation

DO NOT modify any files outside frontend/src/components/help/
```

---

## Execution Checklist

### Before Starting
- [ ] Confirm all terminals have unique file assignments
- [ ] Verify no existing files will be overwritten
- [ ] Ensure stable internet connection
- [ ] Close unnecessary applications

### During Execution
- [ ] Monitor terminal output for conflicts
- [ ] Check for merge conflicts immediately
- [ ] Note any terminals that finish early

### After Completion
- [ ] Run full test suite
- [ ] Check for TypeScript errors
- [ ] Verify all new files are committed
- [ ] Review generated code quality

---

## Estimated Timeline

| Phase | Duration | Terminals |
|-------|----------|-----------|
| Auto-spawn | 60-90 min | 1-5 |
| Round A | 60-90 min | 6-9 |
| Round B | 45-60 min | 10-13 |
| Round C | 45-60 min | 14-17 |
| Round D | 60-90 min | 18-21 |
| Round E | 60-90 min | 22-25 |

**Total Estimated Time:** 5.5 - 8 hours (parallel execution)
