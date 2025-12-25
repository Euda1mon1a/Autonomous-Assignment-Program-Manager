***REMOVED*** TypeScript Linting Reference (ESLint)

ESLint and TypeScript-specific patterns and fixes for the frontend Next.js codebase.

***REMOVED******REMOVED*** Tools Overview

The frontend uses multiple tools:
- **ESLint** - Linting and code quality
- **TypeScript (tsc)** - Type checking (separate from ESLint)
- **next lint** - Next.js-specific ESLint config
- **Prettier** - Code formatting (if configured)

***REMOVED******REMOVED*** Quick Reference

```bash
cd /home/user/Autonomous-Assignment-Program-Manager/frontend

***REMOVED*** ESLint check only
npm run lint

***REMOVED*** ESLint auto-fix
npm run lint:fix

***REMOVED*** TypeScript type check (NOT ESLint)
npm run type-check

***REMOVED*** Check specific file
npx eslint src/components/MyComponent.tsx

***REMOVED*** Auto-fix specific file
npx eslint src/components/MyComponent.tsx --fix

***REMOVED*** See what rules apply to a file
npx eslint --print-config src/components/MyComponent.tsx
```

***REMOVED******REMOVED*** ESLint vs TypeScript Errors

**Important distinction:**

| Error Pattern | Source | Fix With |
|---------------|--------|----------|
| `error: ...` (no code) | ESLint | `npm run lint:fix` |
| `TS2xxx:` | TypeScript | Fix types, see `react-typescript` skill |
| `@typescript-eslint/...` | ESLint TS rules | `npm run lint:fix` |

***REMOVED******REMOVED*** Common ESLint Rules

***REMOVED******REMOVED******REMOVED*** Core ESLint Rules

| Rule | Auto-fix | Description |
|------|----------|-------------|
| `no-unused-vars` | No | Variable declared but never used |
| `no-console` | No | `console.log` in production code |
| `no-debugger` | Yes | `debugger` statement |
| `eqeqeq` | Yes | Require `===` instead of `==` |
| `prefer-const` | Yes | Use `const` when variable isn't reassigned |
| `no-var` | Yes | Use `let`/`const` instead of `var` |

***REMOVED******REMOVED******REMOVED*** React Rules

| Rule | Auto-fix | Description |
|------|----------|-------------|
| `react/jsx-key` | No | Missing `key` prop in list |
| `react/no-unescaped-entities` | No | Unescaped `'` or `"` in JSX |
| `react/jsx-no-target-blank` | Yes | Security: `target="_blank"` without `rel` |
| `react/prop-types` | No | Missing prop types (TS handles this) |
| `react-hooks/rules-of-hooks` | No | Invalid hook usage |
| `react-hooks/exhaustive-deps` | No | Missing dependencies in hooks |

***REMOVED******REMOVED******REMOVED*** TypeScript-ESLint Rules

| Rule | Auto-fix | Description |
|------|----------|-------------|
| `@typescript-eslint/no-unused-vars` | No | Unused variable (TS-aware) |
| `@typescript-eslint/no-explicit-any` | No | Using `any` type |
| `@typescript-eslint/explicit-function-return-type` | No | Missing return type |
| `@typescript-eslint/no-non-null-assertion` | No | Using `!` assertion |
| `@typescript-eslint/prefer-nullish-coalescing` | Yes | Use `??` instead of `||` |
| `@typescript-eslint/prefer-optional-chain` | Yes | Use `?.` optional chain |

***REMOVED******REMOVED******REMOVED*** Next.js Rules

| Rule | Auto-fix | Description |
|------|----------|-------------|
| `@next/next/no-html-link-for-pages` | No | Use `<Link>` not `<a>` for internal |
| `@next/next/no-img-element` | No | Use `<Image>` not `<img>` |
| `@next/next/no-head-import-in-document` | No | Wrong `Head` import |

***REMOVED******REMOVED*** Detailed Fix Patterns

***REMOVED******REMOVED******REMOVED*** no-unused-vars / @typescript-eslint/no-unused-vars

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

***REMOVED******REMOVED******REMOVED*** react-hooks/exhaustive-deps

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

***REMOVED******REMOVED******REMOVED*** react-hooks/rules-of-hooks

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

***REMOVED******REMOVED******REMOVED*** @typescript-eslint/no-explicit-any

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

***REMOVED******REMOVED******REMOVED*** react/jsx-key

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

***REMOVED******REMOVED******REMOVED*** react/no-unescaped-entities

```tsx
// BEFORE
<p>Don't use unescaped apostrophes</p>

// AFTER - Option 1: HTML entity
<p>Don&apos;t use unescaped apostrophes</p>

// AFTER - Option 2: JavaScript string
<p>{"Don't use unescaped apostrophes"}</p>
```

***REMOVED******REMOVED******REMOVED*** @next/next/no-img-element

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

***REMOVED******REMOVED*** JSX in .tsx Files

***REMOVED******REMOVED******REMOVED*** Generic Components

```tsx
// BEFORE - Looks like JSX tag, causes parser error
const Component = <T>(props: Props<T>) => { ... }

// AFTER - Add trailing comma to disambiguate
const Component = <T,>(props: Props<T>) => { ... }

// OR - Use extends
const Component = <T extends unknown>(props: Props<T>) => { ... }
```

***REMOVED******REMOVED******REMOVED*** Type Assertions

```tsx
// BEFORE - Angle bracket syntax conflicts with JSX
const value = <string>someValue;

// AFTER - Use 'as' keyword
const value = someValue as string;
```

***REMOVED******REMOVED*** Project-Specific Patterns

***REMOVED******REMOVED******REMOVED*** TanStack Query Types

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

***REMOVED******REMOVED******REMOVED*** Event Handler Types

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

***REMOVED******REMOVED******REMOVED*** Component Props

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

***REMOVED******REMOVED******REMOVED*** Async Components (Next.js App Router)

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

***REMOVED******REMOVED*** Disable Rules

***REMOVED******REMOVED******REMOVED*** Inline Disable

```typescript
// Disable for next line
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const data: any = externalApi.response;

// Disable for specific rule on same line
const data: any = response; // eslint-disable-line @typescript-eslint/no-explicit-any

// Disable multiple rules
// eslint-disable-next-line @typescript-eslint/no-explicit-any, @typescript-eslint/no-unused-vars
```

***REMOVED******REMOVED******REMOVED*** Block Disable

```typescript
/* eslint-disable @typescript-eslint/no-explicit-any */
// All code here ignores the rule
const a: any = 1;
const b: any = 2;
/* eslint-enable @typescript-eslint/no-explicit-any */
```

***REMOVED******REMOVED******REMOVED*** File Disable

```typescript
// At top of file
/* eslint-disable @typescript-eslint/no-explicit-any */

// Rest of file ignores the rule
```

***REMOVED******REMOVED*** Configuration

***REMOVED******REMOVED******REMOVED*** .eslintrc.js Example

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

***REMOVED******REMOVED*** Troubleshooting

***REMOVED******REMOVED******REMOVED*** ESLint Can't Find Module

```bash
***REMOVED*** Clear ESLint cache
npx eslint --cache --cache-location node_modules/.cache/eslint --cache-strategy content .

***REMOVED*** Or remove cache
rm -rf node_modules/.cache/eslint

***REMOVED*** Reinstall
rm -rf node_modules package-lock.json
npm install
```

***REMOVED******REMOVED******REMOVED*** Rule Not Being Applied

```bash
***REMOVED*** Check what config applies to file
npx eslint --print-config src/components/MyComponent.tsx | grep "rule-name"

***REMOVED*** Check if file is ignored
npx eslint --debug src/components/MyComponent.tsx 2>&1 | grep -i ignore
```

***REMOVED******REMOVED******REMOVED*** Type Errors vs Lint Errors

```bash
***REMOVED*** If you see TS2xxx errors, that's TypeScript, not ESLint
***REMOVED*** Run type check separately
npm run type-check

***REMOVED*** ESLint errors look like:
***REMOVED*** error  'x' is defined but never used  @typescript-eslint/no-unused-vars
```

***REMOVED******REMOVED******REMOVED*** Auto-fix Made Things Worse

```bash
***REMOVED*** Revert changes
git checkout -- src/path/to/file.tsx

***REMOVED*** Preview fixes first
npx eslint src/path/to/file.tsx --fix-dry-run

***REMOVED*** Fix only specific rules
npx eslint src/path/to/file.tsx --fix --rule '@typescript-eslint/prefer-const: error'
```

***REMOVED******REMOVED*** Integration with Prettier

If Prettier is configured, formatting conflicts can occur:

```bash
***REMOVED*** Check for conflicts
npx eslint-config-prettier src/components/MyComponent.tsx

***REMOVED*** Format with Prettier first, then lint
npx prettier --write src/components/MyComponent.tsx
npx eslint src/components/MyComponent.tsx --fix
```

***REMOVED******REMOVED*** CI/CD Integration

```yaml
***REMOVED*** GitHub Actions
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
