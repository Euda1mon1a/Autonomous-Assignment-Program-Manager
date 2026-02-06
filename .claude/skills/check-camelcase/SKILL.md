---
name: check-camelcase
description: >
  Scan TypeScript files for naming convention violations. Wraps Couatl Killer
  (snake_case query params) and Gorgon's Gaze (snake_case enum values) plus
  ESLint @typescript-eslint/naming-convention rule.
model_tier: haiku
user_invocable: true
---

# Check camelCase Convention

Scan frontend TypeScript files for naming convention violations that cause runtime failures.

## What This Checks

This skill enforces three critical naming conventions in the frontend:

| Violation | Tool | Why It Matters |
|-----------|------|----------------|
| **Interface property names** | ESLint | Axios converts API responses to camelCase; snake_case properties access `undefined` |
| **URL query parameters** | Couatl Killer | Query params bypass axios interceptor; backend expects snake_case |
| **Enum values** | Gorgon's Gaze | Axios converts keys not values; camelCase enums never match backend snake_case |

## Running Checks

### 1. ESLint Naming Convention

```bash
cd frontend
npm run lint
```

Checks for snake_case in TypeScript interface properties.

### 2. Couatl Killer (Query Params)

```bash
./scripts/couatl-killer.sh
```

Detects camelCase query parameters like `?personId=` or `URLSearchParams({ blockId: '123' })`.

**Common violations:**
```typescript
// BAD - Backend expects snake_case
router.push(`/schedule?personId=${id}`);
new URLSearchParams({ startDate: '2026-01-01' });

// GOOD
router.push(`/schedule?person_id=${id}`);
new URLSearchParams({ start_date: '2026-01-01' });
```

### 3. Gorgon's Gaze (Enum Values)

```bash
./scripts/gorgons-gaze.sh
```

Detects camelCase enum values in type definitions and comparisons.

**Common violations:**
```typescript
// BAD - Never matches backend 'one_to_one'
type SwapType = 'oneToOne' | 'absorb';
if (swap.swapType === 'oneToOne') { /* never true */ }

// GOOD - Matches backend values
type SwapType = 'one_to_one' | 'absorb';
if (swap.swapType === 'one_to_one') { /* works */ }
```

## Suppression Comments

For false positives, use suppression comments:

```typescript
// ESLint naming convention
interface Props {
  API_KEY: string;  // eslint-disable-line @typescript-eslint/naming-convention
}

// Couatl Killer (query params)
const url = `${API_URL}?createdAt=2026-01-01`;  // @query-param-ok (external API)

// Gorgon's Gaze (enum values)
type HttpStatus = 'notFound' | 'internalError';  // @enum-ok (HTTP standard)
// @gorgon-ok also works
```

## Why These Rules Exist

The axios interceptor in `frontend/src/lib/api.ts` converts API responses:
- **Keys**: snake_case → camelCase (e.g., `created_at` → `createdAt`)
- **Values**: Pass through unchanged (e.g., enum `'cp_sat'` stays `'cp_sat'`)

**Result:**
1. Interface properties must use camelCase to match converted keys
2. Query params must use snake_case (bypass interceptor)
3. Enum values must use snake_case to match backend database values

## Related Documentation

- `CLAUDE.md` sections:
  - "API Type Naming Convention (CRITICAL)"
  - "URL Query Parameters (Couatl Killer)"
  - "Enum Values Stay snake_case (Gorgon's Gaze)"
- Pre-commit hooks auto-run Couatl Killer and Gorgon's Gaze
- ESLint runs in CI and on `npm run lint`
