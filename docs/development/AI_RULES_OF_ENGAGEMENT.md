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

## Related Documentation

- [AI Interface Guide](../admin-manual/ai-interface-guide.md) - Web vs CLI comparison
- [Git Safe Sync Checklist](CLAUDE_GIT_SAFE_SYNC_CHECKLIST.md) - Daily sync procedures
