# Claude Git Safe Sync Checklist

Use this checklist to avoid orphaned branches or unrelated-history merges.

## Daily Sync

1) Always fetch first
```
git fetch origin
```

2) Update local `main` with a rebase (no merge commits)
```
git checkout main
git pull --rebase origin main
```

3) Verify local `main` is clean
```
git status -sb
```

## Feature Branch Workflow

1) Create feature branch from `origin/main`
```
git fetch origin
git checkout -b feature/my-task origin/main
```

2) Rebase feature branch before merge
```
git fetch origin
git rebase origin/main
```

## Hard Rules

- Do NOT use `--allow-unrelated-histories` unless explicitly approved.
- Avoid `git merge` into `main`; prefer `pull --rebase`.
- Do not amend commits unless explicitly asked.
- If histories diverge, pause and ask for guidance.

## Validation

Check reflog for merges:
```
git reflog --date=local | head -n 20
```
If you see `merge` entries, flag it immediately.
