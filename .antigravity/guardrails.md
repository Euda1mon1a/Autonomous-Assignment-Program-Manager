***REMOVED*** Antigravity Autopilot Guardrails

> **Purpose:** Operations that require human confirmation even in Autopilot mode
> **Last Updated:** 2025-12-22

---

***REMOVED******REMOVED*** Critical Operations (ALWAYS Confirm)

These operations will pause Autopilot and request confirmation:

***REMOVED******REMOVED******REMOVED*** 1. Git Operations
- `git push` to any branch
- `git push --force` (BLOCKED - never allow)
- `git commit --amend` (requires explicit confirmation)
- `git rebase` (BLOCKED in autopilot)
- `git reset --hard` (BLOCKED - never allow)
- Creating/deleting branches on remote

***REMOVED******REMOVED******REMOVED*** 2. Database Operations
- Running Alembic migrations (`alembic upgrade`, `alembic downgrade`)
- Direct SQL execution
- Any operation on production database URLs
- Dropping tables or columns
- Truncating data

***REMOVED******REMOVED******REMOVED*** 3. Destructive File Operations
- Deleting files outside of `__pycache__`, `.pytest_cache`, `node_modules`
- Overwriting files in `backend/app/core/` (security-critical)
- Modifying `.env` files
- Changing `docker-compose.yml` or `Dockerfile.*`

***REMOVED******REMOVED******REMOVED*** 4. Security-Sensitive Areas
- Any file in `backend/app/core/security.py`
- Authentication routes (`backend/app/api/routes/auth.py`)
- JWT/token handling code
- Password hashing logic
- Rate limiting configuration

***REMOVED******REMOVED******REMOVED*** 5. ACGME Compliance Code
- `backend/app/scheduling/acgme_validator.py`
- `backend/app/scheduling/engine.py`
- Any file matching `*compliance*` or `*acgme*`

***REMOVED******REMOVED******REMOVED*** 6. External Communications
- API calls to external services
- Webhook triggers
- Email sending
- Slack/notification dispatches

---

***REMOVED******REMOVED*** Allowed Operations (Auto-Approve in Autopilot)

These operations proceed without confirmation:

***REMOVED******REMOVED******REMOVED*** File Operations
- Reading any file
- Creating new files in `tests/`
- Editing test files
- Creating new files in `docs/`
- Editing documentation
- Running linters and formatters

***REMOVED******REMOVED******REMOVED*** Development Commands
- `pytest` (all variations)
- `ruff check` / `ruff format`
- `black`
- `mypy`
- `npm test` / `npm run lint`
- `docker compose logs`
- `docker compose ps`

***REMOVED******REMOVED******REMOVED*** Git Operations (Read-Only)
- `git status`
- `git diff`
- `git log`
- `git branch` (list only)
- `git fetch` (not pull)

***REMOVED******REMOVED******REMOVED*** Analysis Operations
- MCP tool calls (read-only resources)
- Grep/search operations
- Code analysis

---

***REMOVED******REMOVED*** Escalation Triggers

Immediately pause and escalate to human when:

1. **Multiple Failures** - Same operation fails 2+ times
2. **Test Regression** - Tests that passed now fail after a change
3. **Circular Fixes** - Fix A breaks B, fix B breaks A
4. **Unknown Errors** - Error messages not in known patterns
5. **Time Threshold** - Single task taking >15 minutes
6. **Scope Creep** - Task requires touching >10 files

---

***REMOVED******REMOVED*** Recovery Actions

When guardrail is triggered:

1. **Log the attempted operation** (see `.antigravity/logs/`)
2. **Preserve current state** (stash if needed)
3. **Display clear prompt** explaining what was blocked and why
4. **Wait for human decision** - proceed, modify, or abort

---

***REMOVED******REMOVED*** Configuration

To modify these guardrails, edit this file. Changes take effect on next Autopilot session.

***REMOVED******REMOVED******REMOVED*** Strictness Levels

```yaml
***REMOVED*** .antigravity/settings.json
{
  "guardrails": {
    "level": "strict"  ***REMOVED*** Options: strict, moderate, relaxed
  }
}
```

| Level | Behavior |
|-------|----------|
| `strict` | All guardrails enforced, no overrides |
| `moderate` | Guardrails enforced, can override with confirmation |
| `relaxed` | Only critical guardrails (git push, delete, db) enforced |

---

***REMOVED******REMOVED*** Audit Trail

All guardrail triggers are logged to `.antigravity/logs/guardrail-triggers.log`:

```
2025-12-22T10:30:00Z | BLOCKED | git push origin main | Reason: push requires confirmation
2025-12-22T10:32:00Z | CONFIRMED | alembic upgrade head | User: approved
2025-12-22T10:35:00Z | ESCALATED | circular fix detected | Files: service.py, test_service.py
```
