# Antigravity Recovery Procedures

> **Purpose:** Handling failures and recovering from errors in Autopilot mode
> **Last Updated:** 2025-12-22

---

## Recovery Hierarchy

When something goes wrong, follow this priority order:

### Level 1: Immediate Rollback
**Trigger:** Single file edit caused failure
**Action:**
```bash
git checkout -- <file>
```
**Resume:** Re-analyze and try different approach

### Level 2: Stash and Reset
**Trigger:** Multiple files changed, tests failing
**Action:**
```bash
git stash push -m "autopilot-recovery-$(date +%Y%m%d-%H%M%S)"
```
**Resume:** Start fresh, retrieve stash if needed

### Level 3: Full Session Reset
**Trigger:** Circular failures, unclear state
**Action:**
```bash
git stash push -m "autopilot-recovery-$(date +%Y%m%d-%H%M%S)"
git checkout -- .
docker compose -f docker-compose.local.yml restart
```
**Resume:** Escalate to human with full context

### Level 4: Human Required
**Trigger:** Database corruption, security issue, unknown error
**Action:**
```
1. STOP all operations
2. Log current state
3. Alert human immediately
4. Do NOT attempt further fixes
```

---

## Common Failure Patterns

### Pattern: Test Passes Locally, Fails in CI
**Symptoms:** Tests pass when run alone, fail in full suite
**Recovery:**
1. Run full test suite: `pytest -v`
2. Check for shared state/fixtures
3. Look for missing `@pytest.mark.asyncio`
4. Verify database cleanup between tests

### Pattern: Import Errors After Edit
**Symptoms:** `ImportError: cannot import name 'X'`
**Recovery:**
1. Check `__init__.py` exports
2. Verify circular import isn't created
3. Run: `python -c "from app.X import Y"`
4. If still broken, revert and re-approach

### Pattern: Docker File Sync Issues
**Symptoms:** Container sees old file content
**Recovery:**
1. Force rebuild: `docker compose up -d --build`
2. If persists, restart Docker Desktop
3. Verify with: `docker compose exec backend cat <file>`

### Pattern: Migration Chain Broken
**Symptoms:** Alembic revision errors
**Recovery:**
1. Check `down_revision` in latest migration
2. Run: `alembic history`
3. DO NOT modify existing migrations
4. Create new migration if needed

### Pattern: Type Checker vs Runtime Mismatch
**Symptoms:** mypy passes, runtime fails (or vice versa)
**Recovery:**
1. Check for `TYPE_CHECKING` blocks
2. Verify runtime imports match type imports
3. Check for `Any` type escapes
4. Run both: `mypy app/ && pytest`

---

## Recovery Checkpoints

Before major operations, create checkpoint:

```bash
# Create named checkpoint
git stash push -m "checkpoint-before-<operation>"

# Or create lightweight tag
git tag -a "checkpoint-$(date +%Y%m%d-%H%M%S)" -m "Before <operation>"
```

### When to Checkpoint
- Before database migrations
- Before multi-file refactors
- Before security-related changes
- Before any operation involving >5 files

---

## Rollback Commands

### Single File
```bash
git checkout -- <file>
```

### Multiple Files (keep in staging)
```bash
git checkout HEAD -- <file1> <file2>
```

### Everything Since Last Commit
```bash
git checkout -- .
```

### Undo Last Commit (keep changes)
```bash
git reset --soft HEAD~1
```

### Full Hard Reset (DESTRUCTIVE - use with caution)
```bash
git reset --hard HEAD
```

---

## Recovery Logging

All recovery actions logged to `.antigravity/logs/recovery.log`:

```
[2025-12-22T10:00:00Z] RECOVERY_TRIGGERED
  - Reason: test_swap.py::test_execute failed after edit
  - Files affected: backend/app/services/swap.py
  - Action taken: git checkout -- backend/app/services/swap.py
  - Outcome: reverted, tests passing

[2025-12-22T11:00:00Z] RECOVERY_TRIGGERED
  - Reason: circular fix detected (3 iterations)
  - Files affected: swap.py, test_swap.py, fixtures.py
  - Action taken: git stash, escalated to human
  - Outcome: awaiting human guidance
```

---

## Post-Recovery Verification

After any recovery action:

1. **Verify Clean State**
   ```bash
   git status
   git diff
   ```

2. **Run Smoke Tests**
   ```bash
   pytest tests/test_health.py -v
   ```

3. **Check Service Health**
   ```bash
   curl http://localhost:8000/health
   ```

4. **Document What Happened**
   - What was attempted
   - Why it failed
   - What was recovered
   - Recommendations for next attempt

---

## Emergency Contacts

When recovery fails and human intervention required:

1. **Stop Autopilot** - Cmd+Shift+P → "Stop Autopilot"
2. **Save Logs** - Copy `.antigravity/logs/` content
3. **Document State** - Git status, docker status, error messages
4. **Alert Human** - Clear summary of situation

---

## Recovery Metrics

Track recovery patterns to improve reliability:

| Metric | Target | Current |
|--------|--------|---------|
| Recovery success rate | >95% | Tracking... |
| Time to recovery (L1) | <30 sec | Tracking... |
| Time to recovery (L2) | <2 min | Tracking... |
| Escalations per session | <2 | Tracking... |
