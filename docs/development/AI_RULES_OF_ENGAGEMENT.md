***REMOVED*** AI Rules of Engagement

These rules apply to Claude Code, Codex, and any AI agent working in this repo.

***REMOVED******REMOVED*** Core Policy

- Full autonomy for local work is allowed.
- All changes destined for GitHub must go through a PR.
- No direct commits or pushes to `main` / `origin/main` unless explicitly approved.

***REMOVED******REMOVED*** Branching and PR Workflow

1) Create a feature branch off `origin/main` for any change.
2) Commit changes on the feature branch only.
3) Push the feature branch to GitHub.
4) Open a PR and wait for approval before merging.

***REMOVED******REMOVED*** Guardrails

- Do not use `--allow-unrelated-histories` unless explicitly approved.
- Avoid merge commits on `main`; use rebase for sync.
- If histories diverge or an orphaned branch is detected, stop and ask.

***REMOVED******REMOVED*** Required Checks

- Run repo-standard linters before PR:
  - Backend: `ruff check . --fix` and `ruff format .`
  - Frontend: `npm run lint:fix`
- Ensure CI passes before merge.

***REMOVED******REMOVED*** Exceptions

- Emergency fixes can be pushed directly to `main` **only** with explicit approval.
