---
name: check-camelcase
description: >
  Scan TypeScript files for naming convention violations. Runs Couatl Killer
  (camelCase query params), Gorgon's Gaze (camelCase enum values), and ESLint
  naming convention checks.
user_invocable: true
---

# Check camelCase Convention

Scan frontend TypeScript files for three types of naming violations that cause runtime failures.

## Context

The axios interceptor in `frontend/src/lib/api.ts` converts:
- **Object keys:** snake_case ↔ camelCase (API ↔ frontend)
- **Enum values:** Pass through unchanged (must match backend snake_case)
- **Query params:** Bypass interceptor entirely (must use snake_case)

## Actions

### 1. Run Couatl Killer (Query Parameters)

Check for camelCase in URL query parameters (must be snake_case).

```bash
cd /Users/aaronmontgomery/Autonomous-Assignment-Program-Manager
./scripts/couatl-killer.sh
```

**What it catches:**
```typescript
// BAD - Backend expects snake_case
router.push(`/schedule?personId=${id}`);
new URLSearchParams({ startDate: '2026-01-01', blockId: '5' });

// GOOD
router.push(`/schedule?person_id=${id}`);
new URLSearchParams({ start_date: '2026-01-01', block_id: '5' });
```

**Suppression:** Add `// @query-param-ok` comment for false positives.

### 2. Run Gorgon's Gaze (Enum Values)

Check for camelCase in enum type definitions and string literals (must be snake_case).

```bash
cd /Users/aaronmontgomery/Autonomous-Assignment-Program-Manager
./scripts/gorgons-gaze.sh
```

**What it catches:**
```typescript
// BAD - Never matches backend 'one_to_one'
type SwapType = 'oneToOne' | 'absorb';
if (swap.swapType === 'oneToOne') { /* never true */ }

// GOOD - Matches backend values
type SwapType = 'one_to_one' | 'absorb';
if (swap.swapType === 'one_to_one') { /* works */ }
```

**Suppression:** Add `// @enum-ok` or `// @gorgon-ok` comment.

### 3. Run ESLint Naming Convention

Check for snake_case in TypeScript interface properties (must be camelCase).

```bash
cd frontend && npm run lint
```

**What it catches:**
```typescript
// BAD - Axios converts to camelCase, property access fails
interface Person {
  person_id: string;  // Violation
  created_at: string; // Violation
}

// GOOD - Matches axios-converted response
interface Person {
  personId: string;
  createdAt: string;
}
```

**Suppression:** Add `// eslint-disable-line @typescript-eslint/naming-convention`.

## Output Format

Report results for all three checks:

```markdown
## camelCase Convention Check Results

### Couatl Killer (Query Parameters)
[✓ PASS / ✗ FAIL]

Violations:
- `file:line` - Description
  Fix: `?personId=` → `?person_id=`

### Gorgon's Gaze (Enum Values)
[✓ PASS / ✗ FAIL]

Violations:
- `file:line` - Description
  Fix: `'oneToOne'` → `'one_to_one'`

### ESLint Naming Convention (Interface Properties)
[✓ PASS / ✗ FAIL]

Violations:
- `file:line` - Description
  Fix: `person_id:` → `personId:`

## Summary
- Total violations: N
- Query param issues: N
- Enum value issues: N
- Interface property issues: N

[If all pass: "✓ All naming conventions correct. No violations found."]
```

## Why These Rules Matter

| Rule | Reason |
|------|--------|
| Interface props = camelCase | Axios converts API response keys to camelCase; snake_case accesses `undefined` |
| Query params = snake_case | Query strings bypass axios interceptor; backend expects snake_case |
| Enum values = snake_case | Axios converts keys not values; camelCase never matches backend database values |

## Related Files

- `scripts/couatl-killer.sh` - Query param scanner
- `scripts/gorgons-gaze.sh` - Enum value scanner
- `frontend/.eslintrc.json` - ESLint naming rule config
- `CLAUDE.md` - Full documentation of all three rules
