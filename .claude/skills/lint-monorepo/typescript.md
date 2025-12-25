# TypeScript Linting Reference (ESLint)

ESLint and TypeScript-specific patterns and fixes for the frontend Next.js codebase.

## Tools Overview

The frontend uses multiple tools:
- **ESLint** - Linting and code quality
- **TypeScript (tsc)** - Type checking (separate from ESLint)
- **next lint** - Next.js-specific ESLint config
- **Prettier** - Code formatting (if configured)

## Quick Reference

```bash
cd /home/user/Autonomous-Assignment-Program-Manager/frontend

# ESLint check only
npm run lint

# ESLint auto-fix
npm run lint:fix

# TypeScript type check (NOT ESLint)
npm run type-check

# Check specific file
npx eslint src/components/MyComponent.tsx

# Auto-fix specific file
npx eslint src/components/MyComponent.tsx --fix

# See what rules apply to a file
npx eslint --print-config src/components/MyComponent.tsx
```

## ESLint vs TypeScript Errors

**Important distinction:**

| Error Pattern | Source | Fix With |
|---------------|--------|----------|
| `error: ...` (no code) | ESLint | `npm run lint:fix` |
| `TS2xxx:` | TypeScript | Fix types, see `react-typescript` skill |
| `@typescript-eslint/...` | ESLint TS rules | `npm run lint:fix` |

## Common ESLint Rules

### Core ESLint Rules

| Rule | Auto-fix | Description |
|------|----------|-------------|
| `no-unused-vars` | No | Variable declared but never used |
| `no-console` | No | `console.log` in production code |
| `no-debugger` | Yes | `debugger` statement |
| `eqeqeq` | Yes | Require `===` instead of `==` |
| `prefer-const` | Yes | Use `const` when variable isn't reassigned |
| `no-var` | Yes | Use `let`/`const` instead of `var` |

### React Rules

| Rule | Auto-fix | Description |
|------|----------|-------------|
| `react/jsx-key` | No | Missing `key` prop in list |
| `react/no-unescaped-entities` | No | Unescaped `'` or `"` in JSX |
| `react/jsx-no-target-blank` | Yes | Security: `target="_blank"` without `rel` |
| `react/prop-types` | No | Missing prop types (TS handles this) |
| `react-hooks/rules-of-hooks` | No | Invalid hook usage |
| `react-hooks/exhaustive-deps` | No | Missing dependencies in hooks |

### TypeScript-ESLint Rules

| Rule | Auto-fix | Description |
|------|----------|-------------|
| `@typescript-eslint/no-unused-vars` | No | Unused variable (TS-aware) |
| `@typescript-eslint/no-explicit-any` | No | Using `any` type |
| `@typescript-eslint/explicit-function-return-type` | No | Missing return type |
| `@typescript-eslint/no-non-null-assertion` | No | Using `!` assertion |
| `@typescript-eslint/prefer-nullish-coalescing` | Yes | Use `??` instead of `||` |
| `@typescript-eslint/prefer-optional-chain` | Yes | Use `?.` optional chain |

### Next.js Rules

| Rule | Auto-fix | Description |
|------|----------|-------------|
| `@next/next/no-html-link-for-pages` | No | Use `<Link>` not `<a>` for internal |
| `@next/next/no-img-element` | No | Use `<Image>` not `<img>` |
| `@next/next/no-head-import-in-document` | No | Wrong `Head` import |

## Detailed Fix Patterns

### no-unused-vars / @typescript-eslint/no-unused-vars

```typescript
// BEFORE
import { useState, useEffect, useCallback } from 'react'; // useCallback unused

function Component({ data, onUpdate }) { // onUpdate unused
  const [value, setValue] = useState(data);
  const unused = 'something'; // unused variable

  return <div>{value}</div>;
}

// AFTER - Remove unused imports and variables
import { useState } from 'react';

function Component({ data }) {
  const [value] = useState(data); // Remove setValue if unused

  return <div>{value}</div>;
}

// IF intentionally unused (e.g., rest props)
function Component({ data, onUpdate: _onUpdate, ...rest }) {
  // Prefix with _ to indicate intentional
}
```

### react-hooks/exhaustive-deps

```typescript
// BEFORE - Missing dependency
useEffect(() => {
  fetchData(userId);
}, []); // Warning: userId is missing

// AFTER - Add dependency
useEffect(() => {
  fetchData(userId);
}, [userId]);

// IF you truly want to run once (be careful!)
useEffect(() => {
  fetchData(userId);
  // eslint-disable-next-line react-hooks/exhaustive-deps
}, []);
```

### react-hooks/rules-of-hooks

```typescript
// BEFORE - Conditional hook (ILLEGAL)
function Component({ shouldFetch }) {
  if (shouldFetch) {
    const data = useFetch(); // ERROR: Hook in conditional
  }
}

// AFTER - Hook always called
function Component({ shouldFetch }) {
  const data = useFetch();

  if (!shouldFetch) {
    return null;
  }

  return <div>{data}</div>;
}
```

### @typescript-eslint/no-explicit-any

```typescript
// BEFORE
function process(data: any) {
  return data.value;
}

// AFTER - Proper type
interface DataType {
  value: string;
}

function process(data: DataType) {
  return data.value;
}

// IF type is truly unknown
function process(data: unknown) {
  if (typeof data === 'object' && data !== null && 'value' in data) {
    return (data as { value: string }).value;
  }
  throw new Error('Invalid data');
}
```

### react/jsx-key

```typescript
// BEFORE
{items.map(item => (
  <ListItem>{item.name}</ListItem>  // Missing key
))}

// AFTER
{items.map(item => (
  <ListItem key={item.id}>{item.name}</ListItem>
))}

// For index (only if no stable ID available)
{items.map((item, index) => (
  <ListItem key={index}>{item.name}</ListItem>
))}
```

### react/no-unescaped-entities

```tsx
// BEFORE
<p>Don't use unescaped apostrophes</p>

// AFTER - Option 1: HTML entity
<p>Don&apos;t use unescaped apostrophes</p>

// AFTER - Option 2: JavaScript string
<p>{"Don't use unescaped apostrophes"}</p>
```

### @next/next/no-img-element

```tsx
// BEFORE
<img src="/hero.jpg" alt="Hero" />

// AFTER
import Image from 'next/image';

<Image
  src="/hero.jpg"
  alt="Hero"
  width={800}
  height={600}
/>

// For external images, configure domains in next.config.js
```

## JSX in .tsx Files

### Generic Components

```tsx
// BEFORE - Looks like JSX tag, causes parser error
const Component = <T>(props: Props<T>) => { ... }

// AFTER - Add trailing comma to disambiguate
const Component = <T,>(props: Props<T>) => { ... }

// OR - Use extends
const Component = <T extends unknown>(props: Props<T>) => { ... }
```

### Type Assertions

```tsx
// BEFORE - Angle bracket syntax conflicts with JSX
const value = <string>someValue;

// AFTER - Use 'as' keyword
const value = someValue as string;
```

## Project-Specific Patterns

### TanStack Query Types

```typescript
// BEFORE - Type inference issues
const { data } = useQuery({
  queryKey: ['items'],
  queryFn: fetchItems,
});
// data is unknown

// AFTER - Explicit generic
interface Item {
  id: string;
  name: string;
}

const { data } = useQuery<Item[]>({
  queryKey: ['items'],
  queryFn: async (): Promise<Item[]> => {
    const res = await fetch('/api/items');
    return res.json();
  },
});
// data is Item[] | undefined
```

### Event Handler Types

```typescript
// Common event types for React
const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
  setValue(e.target.value);
};

const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
  e.preventDefault();
};

const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
  // ...
};

const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
  if (e.key === 'Enter') submit();
};
```

### Component Props

```typescript
// Always define explicit interfaces
interface ScheduleCardProps {
  schedule: Schedule;
  onEdit?: (id: string) => void;
  className?: string;
  children?: React.ReactNode;
}

export function ScheduleCard({
  schedule,
  onEdit,
  className,
  children,
}: ScheduleCardProps) {
  return (/* ... */);
}
```

### Async Components (Next.js App Router)

```tsx
// Server Component with async
async function SchedulePage({ params }: { params: { id: string } }) {
  const schedule = await getSchedule(params.id);

  return <ScheduleView schedule={schedule} />;
}

// Client Component - cannot be async
'use client';

function ScheduleClient({ scheduleId }: { scheduleId: string }) {
  const { data } = useSchedule(scheduleId);

  return <ScheduleView schedule={data} />;
}
```

## Disable Rules

### Inline Disable

```typescript
// Disable for next line
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const data: any = externalApi.response;

// Disable for specific rule on same line
const data: any = response; // eslint-disable-line @typescript-eslint/no-explicit-any

// Disable multiple rules
// eslint-disable-next-line @typescript-eslint/no-explicit-any, @typescript-eslint/no-unused-vars
```

### Block Disable

```typescript
/* eslint-disable @typescript-eslint/no-explicit-any */
// All code here ignores the rule
const a: any = 1;
const b: any = 2;
/* eslint-enable @typescript-eslint/no-explicit-any */
```

### File Disable

```typescript
// At top of file
/* eslint-disable @typescript-eslint/no-explicit-any */

// Rest of file ignores the rule
```

## Configuration

### .eslintrc.js Example

```javascript
module.exports = {
  extends: [
    'next/core-web-vitals',
    'plugin:@typescript-eslint/recommended',
  ],
  rules: {
    // Customize rules
    '@typescript-eslint/no-unused-vars': ['error', {
      argsIgnorePattern: '^_',
      varsIgnorePattern: '^_',
    }],
    'react/no-unescaped-entities': 'off',
    '@typescript-eslint/no-explicit-any': 'warn', // Warn instead of error
  },
  overrides: [
    {
      files: ['**/__tests__/**/*', '**/*.test.*'],
      rules: {
        '@typescript-eslint/no-explicit-any': 'off',
      },
    },
  ],
};
```

## Troubleshooting

### ESLint Can't Find Module

```bash
# Clear ESLint cache
npx eslint --cache --cache-location node_modules/.cache/eslint --cache-strategy content .

# Or remove cache
rm -rf node_modules/.cache/eslint

# Reinstall
rm -rf node_modules package-lock.json
npm install
```

### Rule Not Being Applied

```bash
# Check what config applies to file
npx eslint --print-config src/components/MyComponent.tsx | grep "rule-name"

# Check if file is ignored
npx eslint --debug src/components/MyComponent.tsx 2>&1 | grep -i ignore
```

### Type Errors vs Lint Errors

```bash
# If you see TS2xxx errors, that's TypeScript, not ESLint
# Run type check separately
npm run type-check

# ESLint errors look like:
# error  'x' is defined but never used  @typescript-eslint/no-unused-vars
```

### Auto-fix Made Things Worse

```bash
# Revert changes
git checkout -- src/path/to/file.tsx

# Preview fixes first
npx eslint src/path/to/file.tsx --fix-dry-run

# Fix only specific rules
npx eslint src/path/to/file.tsx --fix --rule '@typescript-eslint/prefer-const: error'
```

## Integration with Prettier

If Prettier is configured, formatting conflicts can occur:

```bash
# Check for conflicts
npx eslint-config-prettier src/components/MyComponent.tsx

# Format with Prettier first, then lint
npx prettier --write src/components/MyComponent.tsx
npx eslint src/components/MyComponent.tsx --fix
```

## CI/CD Integration

```yaml
# GitHub Actions
- name: Lint Frontend
  run: |
    cd frontend
    npm run lint
    npm run type-check

- name: Lint with annotations
  run: |
    cd frontend
    npx eslint . --format=@microsoft/eslint-formatter-sarif --output-file=eslint.sarif
  continue-on-error: true

- name: Upload SARIF
  uses: github/codeql-action/upload-sarif@v2
  with:
    sarif_file: frontend/eslint.sarif
```
