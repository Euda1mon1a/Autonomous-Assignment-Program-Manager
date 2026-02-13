# Test Gap Detection Prompt Template

> For: test-gap-detection
> Paste the preflight block from `preflight.md` first, then this.

```
## Test Gap Rules

1. ONLY test code that exists on main:
   git log origin/main --oneline -- <file-path>
   If the file/function is not on main, DO NOT write tests for it.
   Never test un-merged feature branches.

2. Dedup before writing:
   Search existing test files FIRST:
   find backend/tests/ -name "test_*.py" | xargs grep -l "<function_name>"
   find frontend/__tests__/ -name "*.test.*" | xargs grep -l "<component>"
   If tests already exist, extend them instead of creating new files.

3. Use existing fixtures:
   - Backend: Use conftest.py fixtures, don't create parallel infrastructure
   - Frontend: Use existing test utilities from __tests__/utils/

4. Size limit: Keep test files under 500 lines.

5. Test file naming:
   - Backend: backend/tests/<layer>/test_<module>.py
   - Frontend: frontend/__tests__/<layer>/<Module>.test.tsx

6. Env preflight for backend test runs:
   python3 scripts/ops/codex_worktree_env_exec.py -- pytest <test_file> -v
```
