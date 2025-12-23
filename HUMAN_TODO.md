# Human TODO

> Tasks that require human action (external accounts, manual configuration, etc.)

---

## Slack Integration Setup

- [ ] **Test Slack Webhook Connection**
  - Workspace: (obtain invite link from team lead - do not commit to repo)
  - Create an Incoming Webhook in the workspace
  - Test with a simple curl command
  - Add `SLACK_WEBHOOK_URL` to `monitoring/.env`

- [ ] **Set Up Slack App for ChatOps** (optional, for slash commands)
  - Create Slack App at https://api.slack.com/apps
  - Add slash command `/scheduler`
  - Add Bot Token Scopes: `chat:write`, `commands`, `users:read`
  - Install app to workspace
  - Copy Bot User OAuth Token for n8n

- [ ] **Create Slack Channels for Alerts**
  - `#alerts-critical`
  - `#alerts-warning`
  - `#alerts-database`
  - `#alerts-infrastructure`
  - `#residency-scheduler`
  - `#compliance-alerts`

---

## Documentation Cleanup

- [x] **Move CELERY_PRODUCTION_CHECKLIST.md out of archived** ✅ Completed 2025-12-21
  - Moved to: `docs/deployment/CELERY_PRODUCTION_CHECKLIST.md`
  - Reason: Contains pending production tasks (email implementation, SMTP config, monitoring)
  - Per archived/README.md, active checklists should not be archived

---

## Other Pending Tasks

<<<<<<< HEAD
### Backend Fix: Faculty Assignments Missing rotation_template_id

**Priority:** Medium
**Found:** Session 14 (2025-12-22)
**Location:** Schedule generation engine or seeder

**Issue:** Faculty-Inpatient Year View shows all zeros because faculty assignments are created without `rotation_template_id`.

Database verification:
```
 total_assignments | with_template | without_template |   type
-------------------+---------------+------------------+----------
                40 |             0 |               40 | faculty
                40 |            40 |                0 | resident
```

**Root Cause:** The schedule generator creates faculty assignments without linking rotation templates. The frontend correctly filters by `activity_type === 'inpatient'`, but faculty assignments have `activity_type = NULL` because no template is assigned.

**Files to investigate:**
- `backend/app/scheduling/engine.py` - Faculty assignment creation logic
- Seed scripts that generate test data

**Frontend code (working correctly):**
```typescript
// FacultyInpatientWeeksView.tsx:92-94
if (
  (am && am.activityType?.toLowerCase() === 'inpatient') ||
  (pm && pm.activityType?.toLowerCase() === 'inpatient')
) {
  count++
```

---
=======
_(Add other human-required tasks here)_
>>>>>>> origin/docs/session-14-summary

---

## Cleanup Session Report (2025-12-21 Overnight)

### Completed Autonomously

- [x] Moved `CELERY_PRODUCTION_CHECKLIST.md` from archived to `docs/deployment/`
- [x] Renamed session 11 docs to avoid confusion:
  - `SESSION_011_PARALLEL_HIGH_YIELD_TODOS.md` → `SESSION_11A_MCP_AND_OPTIMIZATION.md`
  - `SESSION_11_PARALLEL_HIGH_YIELD_TODOS.md` → `SESSION_11B_TEST_COVERAGE.md`
- [x] Updated all cross-references in docs/sessions/README.md, docs/README.md, CHANGELOG.md
- [x] Verified .gitignore is properly configured (no committed secrets/artifacts)

### Broken Documentation Links (Need Decision)

The following links in `README.md` point to non-existent files:

| Broken Link | Suggested Fix |
|-------------|---------------|
| `docs/api/endpoints/credentials.md` (line 81) | → `docs/api/authentication.md` |
| `docs/SETUP.md` (line 180) | → `docs/getting-started/installation.md` |
| `docs/API_REFERENCE.md` (line 376) | → `docs/api/index.md` |

**Decision needed:** Fix links to existing files, or create the missing files?

### Big Ideas (Deferred for Morning Review)

1. **Linting Enforcement**: Ruff is configured in `pyproject.toml` but not run in CI. Consider adding `ruff check --fix` to pre-commit or CI.

2. **Session Naming Convention**: Sessions 7-9 are in `docs/archived/sessions/` while 10+ are in `docs/sessions/`. Consider consolidating.

3. **Remaining Backend TODOs (from TODO_TRACKER.md)**:
   - Portal Dashboard Data (`portal.py:863`) - Faculty dashboard returns stub data
   - MCP Sampling Call (`agent_server.py:263`) - Placeholder LLM response
   - Server Cleanup Logic (`server.py:1121`) - DB connection cleanup on shutdown

### Skipped (Too Invasive for Rest Mode)

- Automated unused import cleanup (would require code changes)
- Large refactoring or architectural changes

---

*Last updated: 2025-12-21*
