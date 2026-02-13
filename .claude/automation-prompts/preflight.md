# Universal Preflight Block

> Paste this at the TOP of every automation.toml prompt. It prevents the 5 recurring failure patterns from the Feb 2026 branch triage.

```
## Mandatory Preflight (do these BEFORE any code changes)

1. Clean tree check:
   git status --porcelain
   If ANY output, run: git stash -m "automation-preflight-$(date +%s)"
   Do NOT create a feature branch from a dirty tree.

2. Fetch and dedup:
   git fetch origin
   git log origin/main --oneline -20 | grep -i "<your-task-keyword>"
   gh pr list --search "<your-task-keyword>"
   If the feature/fix already exists on main or has an open PR, SKIP this task entirely.

3. Scope constraint:
   Work on ONE specific directory or subsystem per run.
   Do NOT apply changes across the entire repo.

4. Contract awareness:
   If changing backend error keys, CHECK frontend error parsing first.
   If changing datetime functions, fix BOTH sides of every comparison.
   If changing API response shapes, regenerate frontend types.
   If writing migration downgrade, only drop objects YOUR migration created.

5. Proof block (include at end of your commit message or PR body):
   - Changed files: <list>
   - Test command: <command>
   - Test result: PASS/FAIL
   - Unresolved risks: <any>
```
