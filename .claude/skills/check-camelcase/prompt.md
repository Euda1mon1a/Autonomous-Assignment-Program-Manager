---
name: check-camelcase
description: Scan TypeScript files for snake_case property names that should be camelCase
user_invocable: true
---

# Check camelCase Convention

Scan frontend TypeScript files for snake_case property names that violate the camelCase convention.

## Context

The axios interceptor in `frontend/src/lib/api.ts` automatically converts:
- **Response:** snake_case → camelCase (from backend)
- **Request:** camelCase → snake_case (to backend)

TypeScript interfaces and object literals MUST use camelCase. If they use snake_case, runtime property access returns `undefined` because the actual data has camelCase keys.

**History:** Session 079, 080 fixed 180+ violations across 41 files.

## Actions

1. **Scan for snake_case in interfaces:**
```bash
grep -rn "_[a-z].*:" frontend/src/types/ frontend/src/features/ --include="*.ts" --include="*.tsx" | grep -v "node_modules" | head -20
```

2. **Scan for snake_case in mock data:**
```bash
grep -rn "_[a-z].*:" frontend/__tests__/ --include="*.ts" --include="*.tsx" | grep -v "node_modules" | head -20
```

3. **Run ESLint naming convention check:**
```bash
cd frontend && npm run lint -- --rule '@typescript-eslint/naming-convention: error' 2>&1 | head -50
```

## Common Violations

| Pattern | Fix |
|---------|-----|
| `person_id: string` | `personId: string` |
| `created_at: string` | `createdAt: string` |
| `pgy_level: number` | `pgyLevel: number` |
| `start_date: string` | `startDate: string` |

## Exceptions

These are OK:
- HTTP headers: `Content-Type`, `Authorization`
- Query parameters sent via URL (not body)
- Constants in UPPER_SNAKE_CASE

## Output

Report all violations with file:line and suggest fixes. If no violations found, confirm codebase is clean.
