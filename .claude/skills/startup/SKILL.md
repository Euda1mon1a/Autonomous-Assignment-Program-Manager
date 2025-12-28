***REMOVED*** Session Startup Skill

> **Purpose:** Review essential documentation and context at the start of each session
> **Created:** 2025-12-27
> **Trigger:** `/startup` command or session start
> **Aliases:** `/session-start`, `/ready`

---

***REMOVED******REMOVED*** When to Use

Run `/startup` at the beginning of every session to:
- Review AI Rules of Engagement
- Check current git state and branch
- Review pending tasks from HUMAN_TODO.md
- Identify blockers or in-progress work
- Confirm readiness to work

---

***REMOVED******REMOVED*** Required Actions

When this skill is invoked, Claude MUST:

***REMOVED******REMOVED******REMOVED*** 1. Review Core Documentation

Read these files in order:

```
1. CLAUDE.md                                    ***REMOVED*** Project guidelines
2. docs/development/AI_RULES_OF_ENGAGEMENT.md   ***REMOVED*** Git/PR workflow rules
3. HUMAN_TODO.md                                ***REMOVED*** Current tasks and priorities
4. docs/development/DEBUGGING_WORKFLOW.md       ***REMOVED*** Debugging methodology (skim)
5. docs/development/CI_CD_TROUBLESHOOTING.md    ***REMOVED*** Common CI issues (skim)
```

***REMOVED******REMOVED******REMOVED*** 2. Check Git Context

Run these commands:

```bash
***REMOVED*** Current branch
git branch --show-current

***REMOVED*** Recent commits on this branch
git log --oneline -5

***REMOVED*** Check for uncommitted changes
git status --porcelain

***REMOVED*** Check for other AI branches in progress
git branch -r | grep -E 'claude/|codex/|ai/' | head -5

***REMOVED*** Check if behind origin/main
git fetch origin main && git rev-list --count HEAD..origin/main
```

***REMOVED******REMOVED******REMOVED*** 3. Check System Health (Optional)

If Docker is running:

```bash
***REMOVED*** Container status
docker compose ps 2>/dev/null || echo "Docker not running"

***REMOVED*** Backend health
curl -s http://localhost:8000/health 2>/dev/null || echo "Backend not available"
```

---

***REMOVED******REMOVED*** Output Format

Provide a concise summary in this format:

```markdown
***REMOVED******REMOVED*** Session Ready

**Branch:** `claude/current-task`
**Status:** Clean working tree / X uncommitted changes
**Behind main:** 0 commits / X commits (rebase needed)

***REMOVED******REMOVED******REMOVED*** Key Rules Acknowledged
- origin/main is sacred - PRs only
- Backup before database modifications
- Run linters before PR (ruff, npm lint)

***REMOVED******REMOVED******REMOVED*** Current Priorities (from HUMAN_TODO.md)
1. [Priority item 1]
2. [Priority item 2]
3. [Priority item 3]

***REMOVED******REMOVED******REMOVED*** Blockers/In-Progress
- [Any blocked items or WIP from previous sessions]

***REMOVED******REMOVED******REMOVED*** System Status
- Backend: Running/Not running
- Database: X assignments in Block Y

Ready to work. What's the task?
```

---

***REMOVED******REMOVED*** Key Rules to Acknowledge

Every startup should confirm understanding of:

***REMOVED******REMOVED******REMOVED*** Git Workflow
- `origin/main` is the single source of truth
- Always create feature branches from `origin/main`
- Never push directly to main - use PRs
- Never force push without explicit approval

***REMOVED******REMOVED******REMOVED*** MCP Safety
- Database-modifying operations require backup + approval
- Read-only operations are always safe

***REMOVED******REMOVED******REMOVED*** Code Quality
- Run `ruff check --fix` and `ruff format .` before PRs
- Run `npm run lint:fix` for frontend
- Tests must pass before commit

***REMOVED******REMOVED******REMOVED*** Debugging Approach
- Explore first, fix second
- Write failing tests before fixing bugs
- Use "think hard" / "ultrathink" for complex issues

---

***REMOVED******REMOVED*** Quick Reference Card

```
HARD STOPS (ask user):
- Divergent histories
- Force push required
- Protected branch modification
- Merge conflicts

SAFE COMMANDS (always OK):
git status, git diff, git log, git branch, git fetch

BEFORE EVERY COMMIT:
cd backend && ruff check . --fix && pytest
cd frontend && npm run lint:fix && npm test
```

---

***REMOVED******REMOVED*** Related Skills

| Skill | When to Use |
|-------|-------------|
| `session-documentation` | End of session handoff |
| `systematic-debugger` | Complex bug investigation |
| `safe-schedule-generation` | Before schedule modifications |
| `pr-reviewer` | Before creating PRs |

---

***REMOVED******REMOVED*** Example Invocation

**User:** `/startup`

**Claude:**
```markdown
***REMOVED******REMOVED*** Session Ready

**Branch:** `claude/fix-mcp-namespace-collision`
**Status:** Clean working tree
**Behind main:** 0 commits

***REMOVED******REMOVED******REMOVED*** Key Rules Acknowledged
- origin/main is sacred - PRs only
- Backup before database modifications
- Run linters before PR

***REMOVED******REMOVED******REMOVED*** Current Priorities (from HUMAN_TODO.md)
1. UI/UX: Frozen headers on schedule grid
2. Heatmap: Add block navigation
3. Backend: Fix faculty rotation_template_id assignment

***REMOVED******REMOVED******REMOVED*** Blockers/In-Progress
- FastMCP upgrade blocked on URI template changes (see MCP_FASTMCP_UPGRADE_NEEDED.md)

***REMOVED******REMOVED******REMOVED*** System Status
- Backend: Running (Docker)
- Database: 87 assignments in Block 10

Ready to work. What's the task?
```

---

*This skill ensures every session starts with proper context and rule awareness.*
