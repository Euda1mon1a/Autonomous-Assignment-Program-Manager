***REMOVED*** Session Safety Checklist

> Quick reference for Claude Code sessions. The full SessionStart hook was removed to reduce context bloat.

***REMOVED******REMOVED*** Pre-Session Checks

```bash
***REMOVED*** 1. Verify current branch
git branch --show-current

***REMOVED*** 2. Check if branch tracks remote
git rev-parse --abbrev-ref @{u} 2>/dev/null || echo "NO REMOTE - push with: git push -u origin $(git branch --show-current)"

***REMOVED*** 3. Check for uncommitted changes
git status --porcelain
```

***REMOVED******REMOVED*** Branch Rules

- **Never commit directly to main** - Create a feature branch first
- **Always push with tracking**: `git push -u origin <branch-name>`
- **Before PR**: `git fetch origin && git rebase origin/main`

***REMOVED******REMOVED*** Key Files to Know

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Project guidelines, architecture, code style |
| `docs/development/AI_RULES_OF_ENGAGEMENT.md` | Git workflow, safety rules |
| `docs/development/CLAUDE_GIT_SAFE_SYNC_CHECKLIST.md` | Daily sync procedures |

***REMOVED******REMOVED*** Quick Safety Rules

1. **All GitHub changes go through PRs** - Never push directly to main
2. **Run tests before commit**: `cd backend && pytest` / `cd frontend && npm test`
3. **Run linters before PR**: `ruff check . --fix` / `npm run lint:fix`
4. **Never use**: `--force`, `--allow-unrelated-histories`, `reset --hard`
5. **Never commit**: `.env`, PII data, database dumps

***REMOVED******REMOVED*** If Something Goes Wrong

```bash
***REMOVED*** Undo last commit (keep changes)
git reset --soft HEAD~1

***REMOVED*** Stash work and switch branches
git stash push -m "WIP: description"

***REMOVED*** Check reflog if you lose commits
git reflog
```

---

*Previously this info was output by the SessionStart hook. Removed to reduce context size.*
