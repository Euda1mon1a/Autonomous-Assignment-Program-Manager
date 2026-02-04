---
name: codex-local-triage
description: Scan local Codex worktrees for uncommitted changes worth reviewing
version: 1.0.0
author: Claude Opus 4.5
invocation: user
arguments:
  - name: details
    type: boolean
    default: false
    description: Show file-level details for each worktree
  - name: save
    type: boolean
    default: false
    description: Save report to docs/reports/automation/
---

# Codex Local Triage

Scan local Codex worktrees for uncommitted changes and generate a triage report.

## Usage

```
/codex-local-triage           # Quick summary
/codex-local-triage --details # Show file lists
/codex-local-triage --save    # Save report to docs/reports/automation/
```

## Instructions

<codex-local-triage>

### Step 1: Find Codex Worktrees

Scan for worktrees at `~/.codex/worktrees/*/Autonomous-Assignment-Program-Manager`:

```bash
WORKTREE_ROOT="$HOME/.codex/worktrees"
REPO_NAME="Autonomous-Assignment-Program-Manager"

# Find all worktrees for this repo
find "$WORKTREE_ROOT" -maxdepth 2 -type d -name "$REPO_NAME" 2>/dev/null
```

### Step 2: Analyze Each Worktree

For each worktree found, gather:

1. **Worktree ID**: Extract from path (e.g., `5f9a` from `.../5f9a/Autonomous-Assignment-Program-Manager`)
2. **Last commit**: `git log -1 --oneline`
3. **Uncommitted changes**: `git status --short`
4. **Diff stats**: `git diff --stat` (if changes exist)

### Step 3: Classify Changes

Classify files as **signal** (worth reviewing) or **noise** (skip):

**Signal** (count these):
- `backend/**/*.py` - Python code
- `frontend/**/*.ts` or `*.tsx` - TypeScript
- `tests/**/*` - Tests
- `docs/**/*.md` - Documentation
- `*.yml` or `*.yaml` - Config

**Noise** (ignore):
- `__pycache__/`, `*.pyc`
- `node_modules/`, `.next/`
- `*.log`, `*.tmp`
- `.coverage`, `htmlcov/`

### Step 4: Generate Report

Output a markdown table:

```markdown
## Codex Local Worktrees

| ID | Last Commit | Changes | Signal |
|----|-------------|---------|--------|
| 5f9a | `df29c3de fix(security)...` | 1 | 1 |
| ef2c | `90a1e3d8 test(cpsat)...` | 10 | 10 |
```

If `--details` flag is set, also show file list for each worktree.

If `--save` flag is set, write report to:
`docs/reports/automation/codex_local_triage_YYYYMMDD-HHMM.md`

### Step 5: Recommendations

After the table, add recommendations:

- If signal > 0: "Review worktree {ID} - has {N} files worth checking"
- If all signal = 0: "All worktrees clean or only noise files"

</codex-local-triage>

## Example Output

```
## Codex Local Worktrees (3 found)

| ID | Last Commit | Changes | Signal |
|----|-------------|---------|--------|
| 5f9a | `df29c3de fix(security)...` | 1 | 1 |
| ef2c | `90a1e3d8 test(cpsat)...` | 10 | 10 |
| 7e49 | `df29c3de fix(security)...` | 4 | 4 |

### Recommendations

- **ef2c**: 10 signal files - review for cherry-pick
- **7e49**: 4 signal files - may overlap with ef2c

Use `--details` to see file lists.
```
