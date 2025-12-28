<!--
Review essential documentation and context at session start.
Load AI rules, git state, and pending tasks.
-->

Invoke the **startup** skill to initialize this session.

## Actions Required

### 1. Review Core Documentation

Read these files in order:
1. `CLAUDE.md` - Project guidelines
2. `docs/development/AI_RULES_OF_ENGAGEMENT.md` - Git/PR workflow rules
3. `HUMAN_TODO.md` - Current tasks and priorities

### 2. Check Git Context

```bash
git branch --show-current
git log --oneline -5
git status --porcelain
git branch -r | grep -E 'claude/|codex/|ai/' | head -5
git fetch origin main && git rev-list --count HEAD..origin/main
```

### 3. Check Codex Feedback (if PR exists)

```bash
PR_NUMBER=$(gh pr view --json number -q '.number' 2>/dev/null)
if [ -n "$PR_NUMBER" ]; then
  REPO=$(gh repo view --json nameWithOwner -q '.nameWithOwner')
  CODEX_COUNT=$(gh api repos/${REPO}/pulls/${PR_NUMBER}/comments \
    --jq '[.[] | select(.user.login == "chatgpt-codex-connector[bot]")] | length' 2>/dev/null || echo "0")
  if [ "$CODEX_COUNT" -gt 0 ]; then
    echo "Codex Feedback: ${CODEX_COUNT} comment(s) pending - run /check-codex"
  fi
fi
```

### 4. Check System Health (Optional)

```bash
docker compose ps 2>/dev/null || echo "Docker not running"
curl -s http://localhost:8000/health 2>/dev/null || echo "Backend not available"
```

## Output Format

```markdown
## Session Ready

**Branch:** `[branch-name]`
**Status:** Clean working tree / X uncommitted changes
**Behind main:** 0 commits / X commits (rebase needed)

### Codex Feedback
- [Status of Codex feedback if PR exists]

### Key Rules Acknowledged
- origin/main is sacred - PRs only
- Backup before database modifications
- Run linters before PR (ruff, npm lint)

### Current Priorities (from HUMAN_TODO.md)
1. [Priority item 1]
2. [Priority item 2]
3. [Priority item 3]

### Blockers/In-Progress
- [Any blocked items or WIP]

Ready to work. What's the task?
```
