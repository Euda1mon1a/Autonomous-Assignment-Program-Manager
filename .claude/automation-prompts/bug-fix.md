# Bug Fix Automation Prompt Template

> For: daily-bug-scan, check-for-bandit-issues
> Paste the preflight block from `preflight.md` first, then this.

```
## Bug Fix Rules

1. ONE-FILE-FIRST pattern:
   - Apply the fix to ONE file first
   - Verify it works (syntax check, import check, or test)
   - THEN apply to remaining files in the same directory

2. Contract-aware changes (CRITICAL):
   - If changing error response keys in backend routes:
     grep the frontend for the old key name BEFORE changing it
     Example: changing "error" to "detail" in HTTPException
     → search: grep -r '"error"' frontend/src/hooks/
   - If changing datetime functions:
     Fix BOTH sides: the .now() call AND any .utcfromtimestamp() / DB reads
     Naive DB columns need: .replace(tzinfo=UTC) before comparison
   - If changing FastAPI HTTPException detail:
     detail=string is correct; detail={"detail": "..."} creates double nesting

3. Framework context:
   - FastAPI: HTTPException(detail=X) wraps as {"detail": X} on the wire
   - SQLAlchemy: Use ~column for boolean negation, NOT "not column"
   - Tailwind: Class names must be static strings, not template literals

4. Scope: Fix bugs in ONE directory per run. Never touch 50+ files.

5. Env preflight for backend commands:
   python3 scripts/ops/codex_worktree_env_exec.py -- <backend command>
```
