# Frontend Lint Ratchet — Overnight Automation

> For: Mac Mini overnight runs
> Goal: Reduce ESLint warnings from ~1,745 to 0 in directory-scoped batches
> Rule: ONE batch per run. Do NOT combine batches.

## Preflight

```bash
git fetch origin && git checkout origin/main && git checkout -b mini/claude/lint-ratchet-$(date +%Y%m%d)-BATCH_NAME
cd frontend
```

## Batch Order (largest → smallest)

Run ONE batch per overnight session. Pick the first incomplete batch.

| Batch | Directory | ~Warnings | Primary Rule |
|-------|-----------|-----------|--------------|
| 1 | `src/__tests__/integration/` | 488 | naming-convention |
| 2 | `src/__tests__/hooks/` | 142 | naming-convention |
| 3 | `src/components/schedule/` | 102 | naming-convention |
| 4 | `src/components/admin/` | 58 | naming-convention |
| 5 | `src/features/voxel-schedule/` | 45 | naming-convention |
| 6 | `src/components/__tests__/` | 41 | naming-convention |
| 7 | `src/lib/` | 62 | naming-convention, no-explicit-any |
| 8 | `src/features/conflicts/` | 37 | naming-convention |
| 9 | `src/hooks/` (all files) | 160 | naming-convention, no-explicit-any |
| 10 | `src/features/resilience/` | 31 | naming-convention |
| 11 | `src/components/ui/` | 24 | naming-convention |
| 12 | `src/features/swap-marketplace/` | 17 | naming-convention |
| 13 | `src/features/templates/` | 17 | naming-convention |
| 14 | `src/features/wellness/` | 15 | naming-convention |
| 15 | `src/components/` (remaining files) | 70 | mixed |
| 16 | `src/app/` | 40 | mixed |
| 17 | `src/types/` (non-generated) | 30 | naming-convention |
| 18 | Remaining stragglers | ~50 | mixed |

## Rules for Each Batch

### naming-convention fixes (95% of warnings)

These are `@typescript-eslint/naming-convention` violations — snake_case property names in interfaces/types that should be camelCase.

**CRITICAL CONTEXT:** The axios interceptor in `src/lib/api.ts` auto-converts snake_case API keys to camelCase. TypeScript interfaces MUST use camelCase to match runtime data. This is NOT cosmetic — snake_case types cause `undefined` at runtime.

**EXCEPTION — Enum values stay snake_case.** See CLAUDE.md "Gorgon's Gaze" section. Values like `swap_type: 'one_to_one'` are correct. Only KEYS get converted.

**EXCEPTION — URL query params stay snake_case.** See CLAUDE.md "Couatl Killer" section. Params like `{ block_id: '123' }` go directly to the API.

When renaming a property:
1. Rename in the interface/type definition
2. Update ALL usages of that property across the codebase
3. Do NOT rename if it's an enum value or URL query param
4. If unsure, add `// @gorgon-ok` comment rather than rename

### no-explicit-any (241 warnings)

Replace `any` with proper types:
- For API responses: use types from `src/types/api-generated.ts`
- For event handlers: use `React.MouseEvent`, `React.ChangeEvent<HTMLInputElement>`, etc.
- For unknown data: use `unknown` and narrow with type guards
- If genuinely unknowable: use `// eslint-disable-next-line @typescript-eslint/no-explicit-any`

### no-unused-vars (175 warnings)

- Remove unused imports and variables
- If a variable is intentionally unused (destructuring), prefix with `_`
- NEVER remove `# noqa` or lint suppression comments

### a11y warnings (61 total)

- `click-events-have-key-events`: Add `onKeyDown` handler alongside `onClick`
- `interactive-supports-focus`: Add `tabIndex={0}` to interactive non-button elements

## Verification (MUST pass before commit)

```bash
# Count warnings in your batch directory
npx eslint src/YOUR_BATCH_DIR/ --format json 2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
w = sum(1 for f in data for m in f.get('messages',[]) if m.get('severity')==1)
print(f'Warnings remaining: {w}')
"

# Full lint must not INCREASE warning count
npx eslint src/ --format json 2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
w = sum(1 for f in data for m in f.get('messages',[]) if m.get('severity')==1)
e = sum(1 for f in data for m in f.get('messages',[]) if m.get('severity')==2)
print(f'Total warnings: {w}  Errors: {e}')
assert e == 0, 'ERRORS introduced!'
assert w <= 1745, f'Warning count INCREASED from 1745 to {w}!'
"

# TypeScript must still compile
npm run type-check

# Tests must still pass
npm test -- --passWithNoTests
```

## Commit Format

```
fix(frontend): reduce ESLint warnings in BATCH_DIR

Batch N of lint ratchet: fix naming-convention/no-explicit-any/etc
in src/BATCH_DIR/. Warnings: BEFORE → AFTER.
```
