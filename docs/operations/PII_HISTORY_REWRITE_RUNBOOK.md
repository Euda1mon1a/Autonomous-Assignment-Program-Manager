# PII History Rewrite Runbook

This runbook provides a controlled process for removing PII from git history
using `git filter-repo`. It includes a helper script, coordination steps, and
explicit warnings about force-pushing rewritten history.

## ⚠️ WARNING: HISTORY REWRITE (FORCE-PUSH REQUIRED)

Rewriting git history will change commit SHAs for all rewritten commits. This
requires a force-push and **every collaborator must re-clone or hard reset**.
Do not proceed without explicit coordination and approval.

## Prerequisites

- `git` installed
- `git filter-repo` installed
  - Install: `pipx install git-filter-repo` or `pip install git-filter-repo`
- Administrative access to the remote repository
- Maintenance window coordinated with all collaborators

## Checklist (Do Not Skip)

- Identify PII patterns (filenames and/or content strings).
- Notify all collaborators of the rewrite window and required re-clone.
- Create a backup branch on the remote.
- Ensure no one is pushing during the window.
- Run the script locally (DO NOT run in CI).
- Validate the repo state and scans.
- Force-push rewritten history.
- Confirm all collaborators re-clone.

## Commands (Copy/Paste)

### 1) Create a backup branch (local and remote)

```bash
git fetch origin
git checkout main
git pull --ff-only origin main
git branch backup/pre_pii_rewrite_$(date +%Y%m%d)
git push origin backup/pre_pii_rewrite_$(date +%Y%m%d)
```

### 2) Run the helper script (local only)

Edit and run:

```bash
./scripts/cleanup_pii_history.sh
```

### 3) Verify rewrite locally

```bash
git log --oneline -n 5
git status
```

If you have scanning tools (e.g., `gitleaks`), re-run them here.

### 4) Force-push rewritten history

```bash
git push --force --all origin
git push --force --tags origin
```

### 5) Collaborator re-clone steps (send to team)

```bash
rm -rf <repo-dir>
git clone <repo-url>
cd <repo-dir>
```

If a re-clone is impossible, the minimum safe alternative is:

```bash
git fetch origin
git checkout main
git reset --hard origin/main
git clean -fdx
```

## Notes

- The backup branch preserves the pre-rewrite history for recovery.
- If the repo is protected by branch rules, temporarily relax them for the
  force-push, then restore immediately after.
- Consider updating any references to old SHAs in tickets or docs.

## Rollback Plan

If the rewrite fails or data integrity is compromised:

```bash
git fetch origin
git checkout backup/pre_pii_rewrite_YYYYMMDD
git push --force origin backup/pre_pii_rewrite_YYYYMMDD:main
```

Coordinate rollback with the same level of caution and re-clone steps.
