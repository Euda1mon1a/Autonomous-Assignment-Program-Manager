# GUI Development Workflow

## Overview

For GUI-related work (troubleshooting, visual bugs, UI testing, frontend edits), use **Antigravity** for direct browser interaction. Claude handles backend, commits, and PR review.

## Workflow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Antigravity   │────▶│     Claude      │────▶│   GitHub PR     │
│  (GUI work)     │     │ (commit/review) │     │  (merge)        │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### 1. Antigravity Phase
- Direct browser interaction at `http://localhost:3000`
- Visual debugging and troubleshooting
- Frontend code edits
- Real-time UI testing
- Screenshot issues

### 2. Claude Phase
- Review changes made by Antigravity
- Run linters: `npm run lint:fix`
- Run tests: `npm test`
- Commit with proper message
- Create PR when ready

### 3. Review Phase
- Claude reviews diff before PR
- Check for security issues
- Verify no PII/OPSEC violations
- Ensure tests pass

## When to Use This Workflow

| Task | Tool |
|------|------|
| Visual bugs | Antigravity |
| Layout issues | Antigravity |
| Click-through testing | Antigravity |
| Component styling | Antigravity |
| API integration bugs | Claude |
| Backend fixes | Claude |
| Commits & PRs | Claude |
| Code review | Claude |

## Handoff Protocol

### Antigravity → Claude
```
"Ready for commit review. Changes in [files]. Testing [feature]."
```

### Claude Checklist
- [ ] `git diff` review
- [ ] `npm run lint:fix`
- [ ] `npm test`
- [ ] No console.log/debugger left
- [ ] No hardcoded secrets
- [ ] Commit with descriptive message

## Test Data Available

For GUI testing:
- **Login:** `admin` / `admin123`
- **URL:** `http://localhost:3000`
- **People:** 45 (30 residents, 15 faculty)
- **Blocks:** 14 (0-13)
- **Activities:** 730 half-day slots
- **Academic Year:** 2025-07-01 to 2026-06-30

## Related Resources

- Pentest prompt: `.claude/prompts/gemini-flash-gui-pentest.md`
- Frontend code: `frontend/src/`
- API endpoints: `backend/app/api/routes/`
