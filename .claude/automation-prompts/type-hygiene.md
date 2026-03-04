# Type Hygiene Prompt Template

> For: check-for-mypy-issues
> Paste the preflight block from `preflight.md` first, then this.

```
## Type Hygiene Rules

1. REAL annotations only:
   - Add proper type annotations (return types, parameter types)
   - NEVER add "# type: ignore" suppression comments
   - If a type is genuinely complex, add a TypeAlias or Protocol instead
   - If you can't properly annotate something, SKIP the file

2. Directory-scoped:
   - Work on ONE directory per run (e.g., backend/app/services/)
   - Do NOT touch 50 files across the entire repo

3. Import additions:
   - Use TYPE_CHECKING for import-only types:
     from __future__ import annotations
     from typing import TYPE_CHECKING
     if TYPE_CHECKING:
         from app.models.person import Person

4. Common patterns for this codebase:
   - SQLAlchemy models: Column types map to Python types
   - Pydantic schemas: Already typed, usually don't need changes
   - FastAPI routes: Use Depends() typing, Response models
   - Async functions: Return Awaitable[T] or just T with async def

5. Verify after changes:
   python3 .codex/scripts/codex_worktree_env_exec.py -- python -m mypy <directory> --ignore-missing-imports

6. Lint suppression comments:
   - NEVER remove `# noqa`, `# type: ignore`, `// eslint-disable`, or `@ts-expect-error` comments
   - These exist because the developer hit a real type system limitation
   - If you think you've fixed the underlying issue, verify with the type checker FIRST:
     Backend: python -m mypy <file> --ignore-missing-imports
     Frontend: npx tsc --noEmit 2>&1 | grep <filename>
   - Only remove the suppression comment if the type checker passes WITHOUT it
```
