# AI Rules of Engagement

These rules apply to Claude Code, Codex, and any AI agent working in this repo.

---

## Core Policy

- Full autonomy for local work is allowed.
- All changes destined for GitHub must go through a PR.
- No direct commits or pushes to `main` / `origin/main` unless explicitly approved.

---

## Environment Detection: Adapt Your Behavior

**Before making any changes, AI agents MUST detect their environment and adapt accordingly.**

### Step 1: Identify Your Interface Type

| Interface Type | How to Identify | Behavior Mode |
|----------------|-----------------|---------------|
| **Web App** | No file system access, conversation only | Suggestion Mode |
| **CLI/Terminal** | Can run `pwd`, `ls`, read files | Direct Edit Mode |
| **IDE Extension** | Inside VS Code, Cursor, etc. | Direct Edit Mode |

### Step 2: Detect Git Context

Run these checks before any file modifications:

```bash
# Check if in a git repository
git rev-parse --is-inside-work-tree

# Check current branch
git branch --show-current

# Check if we're on main/master
git branch --show-current | grep -E '^(main|master)$'

# Check remote configuration
git remote -v

# Check if there are uncommitted changes
git status --porcelain
```

### Step 3: Adapt Behavior Based on Environment

#### If on `main` or `master` branch:
1. **STOP** - Do not make direct commits
2. Create a feature branch: `git checkout -b feature/descriptive-name`
3. Make changes on the feature branch only

#### If connected to a remote (origin):
1. Never `git push` directly to main
2. Always create PRs for review
3. Never use `--force` without explicit approval

#### If in Web/Suggestion Mode:
1. Provide code snippets with clear file paths
2. Explain where changes should be applied
3. Do not assume knowledge of existing file contents

---

## CLI/IDE: Adopt Web-Like Safety Patterns

**CLI agents should adopt the safety patterns of web applications:**

### The PR-First Principle

Even though CLI has the power to push directly, **pretend you can only suggest changes** like a web interface:

1. **Always branch first** - Never commit to main
2. **Always PR** - Create a Pull Request for every change
3. **Always wait** - Do not merge your own PRs
4. **Always review** - Show `git diff` before committing

### Destructive Command Blocklist

**Never execute without explicit user approval:**

| Command | Risk | Required Approval |
|---------|------|-------------------|
| `git push origin main` | Breaks main branch | "Push to main? (type YES)" |
| `git push --force` | Destroys history | Explicit written approval |
| `git reset --hard` | Loses uncommitted work | "Delete uncommitted changes?" |
| `git branch -D` | Deletes branches | Confirm branch name |
| `rm -rf` | Permanent deletion | Full path confirmation |
| `DROP TABLE` / `DELETE FROM` | Data loss | Query review required |

### Safe Default Commands

These are always safe to run:
```bash
git status
git diff
git log
git branch
git fetch origin
git stash
```

---

## Branching and PR Workflow

1) Create a feature branch off `origin/main` for any change.
2) Commit changes on the feature branch only.
3) Push the feature branch to GitHub.
4) Open a PR and wait for approval before merging.

### PR Creation Checklist

Before creating a PR:
- [ ] All tests pass locally
- [ ] Linters have been run (ruff, npm lint)
- [ ] Changes are on a feature branch (not main)
- [ ] Commit messages are descriptive
- [ ] No secrets or sensitive data in commits

---

## Guardrails

- Do not use `--allow-unrelated-histories` unless explicitly approved.
- Avoid merge commits on `main`; use rebase for sync.
- If histories diverge or an orphaned branch is detected, stop and ask.

### Hard Stops

If any of these conditions are detected, **STOP and ask the user:**

1. **Divergent histories** - Local and remote have unrelated commits
2. **Force push required** - Normal push is rejected
3. **Protected branch** - Attempting to modify main/master
4. **Merge conflicts** - Cannot auto-resolve
5. **Missing remote** - Origin not configured
6. **Dirty working tree before destructive op** - Uncommitted changes at risk

---

## Session Awareness

### Parallel Session Detection

If you detect signs of another AI session (unexpected file changes, git conflicts), **STOP and alert the user:**

```
WARNING: Detected unexpected changes to [filename].
Another process may be modifying this file.
Please confirm no other AI sessions are active.
```

### Session Handoff Protocol

When ending a session that another AI might continue:
1. Commit all changes with descriptive message
2. Run `git status` to confirm clean state
3. Document any in-progress work
4. Do not leave uncommitted changes

---

## Required Checks

- Run repo-standard linters before PR:
  - Backend: `ruff check . --fix` and `ruff format .`
  - Frontend: `npm run lint:fix`
- Ensure CI passes before merge.

---

## Exceptions

- Emergency fixes can be pushed directly to `main` **only** with explicit approval.
- The user must type "EMERGENCY PUSH APPROVED" for direct main pushes.

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────┐
│              AI AGENT DECISION TREE                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Am I on main/master?                                   │
│     YES → Create feature branch FIRST                   │
│     NO  → Proceed                                       │
│                                                         │
│  Does this change need to go to GitHub?                 │
│     YES → Must use Pull Request                         │
│     NO  → Can commit locally                            │
│                                                         │
│  Is push being rejected?                                │
│     YES → STOP. Do not force push. Ask user.            │
│     NO  → Proceed                                       │
│                                                         │
│  Are there uncommitted changes I didn't make?           │
│     YES → STOP. Another session may be active.          │
│     NO  → Proceed                                       │
│                                                         │
│  Default stance: Suggest via PR, never force.           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## CI/CD Integration for AI Branches

### Branch Naming Conventions

AI agents (Claude Code, Codex, etc.) use specific branch naming patterns:

| Agent | Branch Pattern | Example |
|-------|---------------|---------|
| Claude Code | `claude/<task>-<session-id>` | `claude/fix-auth-bug-EwUPf` |
| Codex | `codex/<task>-<id>` | `codex/add-feature-123` |
| Other AI | `ai/<agent>/<task>` | `ai/copilot/refactor-utils` |

### CI/CD Workflow Triggers

The following workflows are configured to run on AI branches:

```yaml
# Workflows that trigger on claude/** branches:
- ci.yml              # Main test suite
- ci-enhanced.yml     # Matrix testing
- ci-comprehensive.yml # Full quality checks
- code-quality.yml    # Linting and formatting
```

These workflows use this trigger pattern:
```yaml
on:
  push:
    branches:
      - main
      - master
      - 'claude/**'  # AI-created branches
```

### Before Pushing AI Branches

AI agents MUST verify CI will trigger:

1. **Check branch name matches pattern**: `git branch --show-current` should show `claude/*` or similar
2. **Verify workflows exist**: Confirm `.github/workflows/*.yml` have appropriate triggers
3. **Run local checks first**:
   ```bash
   # Backend
   cd backend && ruff check . && pytest

   # Frontend
   cd frontend && npm run lint && npm test
   ```

---

## Preventing Parallel Development Conflicts

### The Single-Session Rule

**CRITICAL**: Only ONE AI session should work on a codebase at a time.

### Pre-Session Checks

Before starting work, AI agents MUST:

```bash
# 1. Fetch latest state
git fetch origin

# 2. Check for other AI branches in progress
git branch -r | grep -E 'claude/|codex/|ai/' | head -10

# 3. Check for recent activity
git log --oneline --all --since="1 hour ago" --author-date-order

# 4. Check for uncommitted changes
git status --porcelain
```

### If Parallel Work Detected

If another AI session is detected:

1. **DO NOT** create overlapping changes
2. **STOP** and inform the user:
   ```
   WARNING: Detected active AI branch: claude/other-task-XYZ
   Last commit: 15 minutes ago
   Please confirm this session should proceed.
   ```
3. **WAIT** for user confirmation before continuing

### Session Isolation Strategies

| Strategy | When to Use | Implementation |
|----------|-------------|----------------|
| **Stacking** | Same feature area | Create branch from existing AI branch |
| **Isolation** | Different features | Create independent branch from main |
| **Takeover** | Previous session stalled | Checkout and continue existing branch |

### Avoiding Merge Conflicts

1. **Small, focused changes** - One logical change per branch
2. **Immediate PR creation** - Push and create PR as soon as work is complete
3. **Clean handoff** - If pausing, commit with message: `WIP: <description>`
4. **Rebase before push** - Always `git pull --rebase origin main` before pushing

### Branch Cleanup

After PR is merged, AI agents should NOT:
- Delete remote branches (leave for human review)
- Force-push to branches with open PRs
- Reuse old branch names

---

## Related Documentation

- [AI Interface Guide](../admin-manual/ai-interface-guide.md) - Web vs CLI comparison
- [Git Safe Sync Checklist](CLAUDE_GIT_SAFE_SYNC_CHECKLIST.md) - Daily sync procedures
