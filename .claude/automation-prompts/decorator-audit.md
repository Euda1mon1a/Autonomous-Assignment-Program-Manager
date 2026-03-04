# Decorator Audit Prompt Template

> For: type-hygiene, daily-bug-scan
> Paste the preflight block from `preflight.md` first, then this.

## Decorator Factory Audit

Scan for two high-value patterns in ONE directory per run:

### Pattern 1: Missing return types on decorator factories

Find functions that return decorators but lack return type annotations:

```bash
# Find decorator factories (functions that define and return inner functions)
grep -rn "def decorator\|def wrapper" backend/app/<directory>/ | head -20
```

Add `ParamSpec`/`TypeVar` typing where missing. Use the pattern from PR #1149.

### Pattern 2: `async def` on decorator factories (BUG)

Find decorator factories incorrectly marked as `async def`:

```bash
grep -rn "async def.*operation.*metadata\|async def.*timeout\|async def.*decorator" backend/app/<directory>/ | grep -v "wrapper\|inner"
```

A decorator FACTORY should be `def`, not `async def`. The inner WRAPPER can be `async def`.
If the factory is `async def`, using `@factory(args)` returns a coroutine object instead of a decorator.

Fix: Change `async def factory_name(...)` to `def factory_name(...)`. Keep the inner wrapper as `async def`.

### Verification

After changes:

```bash
python3 .codex/scripts/codex_worktree_env_exec.py -- python -m py_compile <changed_file>
python3 .codex/scripts/codex_worktree_env_exec.py -- pytest <related_test_file> -v
```
