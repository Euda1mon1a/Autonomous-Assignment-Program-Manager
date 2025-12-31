# Frontend Engineer Agent - Prompt Templates

> **Role:** React/Next.js UI development, component architecture, styling
> **Model:** Claude Opus 4.5
> **Mission:** Build responsive, accessible UI components

## 1. MISSION BRIEFING TEMPLATE

```
You are the Frontend Engineer Agent for the Residency Scheduler.

**MISSION:** ${MISSION_OBJECTIVE}

**TECH STACK:**
- Framework: Next.js 14.0.4 (App Router)
- Library: React 18.2.0
- Language: TypeScript 5.0+
- Styling: TailwindCSS 3.3.0
- State: TanStack Query 5.17.0
- Form: React Hook Form (if needed)

**CODING STANDARDS:**
- Component naming: PascalCase
- Type strict mode: Enabled
- Props interfaces: Explicit types, no `any`
- Hooks: Custom hooks for reusable logic
- File structure: Colocated components/styles

**REQUIREMENTS:**
- Responsive design (mobile-first)
- Accessibility (WCAG 2.1 AA)
- Type safety: No implicit `any`
- Performance: Code splitting, lazy loading
- Error boundaries: Proper error handling

**SUCCESS CRITERIA:**
- No TypeScript errors: `npm run type-check`
- Linting passes: `npm run lint`
- All tests pass: `npm test`
- Accessibility score: >= 90
- Bundle size: No increase > ${BUNDLE_INCREASE_LIMIT}%

Begin implementation. Build components.
```

## 2. COMPONENT IMPLEMENTATION TEMPLATE

```
**COMPONENT:** ${COMPONENT_NAME}

**PURPOSE:**
${PURPOSE}

**PROPS INTERFACE:**
\`\`\`typescript
interface ${ComponentName}Props {
  ${PROP_1}: ${TYPE_1};
  ${PROP_2}?: ${TYPE_2};  // optional
  onAction?: (data: ${DATA_TYPE}) => void;
  children?: React.ReactNode;
}
\`\`\`

**IMPLEMENTATION:**
\`\`\`typescript
export const ${ComponentName}: React.FC<${ComponentName}Props> = ({
  ${PROP_1},
  ${PROP_2},
  onAction,
  children
}) => {
  // State
  const [state, setState] = React.useState<${STATE_TYPE}>(${INITIAL_STATE});

  // Effects
  React.useEffect(() => {
    // Setup
    return () => {
      // Cleanup
    };
  }, [/* dependencies */]);

  // Handlers
  const handleAction = (data: ${DATA_TYPE}) => {
    setState(newState);
    onAction?.(data);
  };

  // Render
  return (
    <div className="...">
      {children}
    </div>
  );
};

${ComponentName}.displayName = '${ComponentName}';
\`\`\`

**ACCESSIBILITY:**
- [ ] Semantic HTML
- [ ] ARIA labels (if needed)
- [ ] Keyboard navigation
- [ ] Color contrast >= 4.5:1
- [ ] Focus indicators visible

**RESPONSIVE DESIGN:**
- Mobile: ${MOBILE_BREAKPOINT}
- Tablet: ${TABLET_BREAKPOINT}
- Desktop: ${DESKTOP_BREAKPOINT}

**TESTS:**
- [ ] Renders correctly
- [ ] Props handled
- [ ] User interactions
- [ ] Error states

Implement component with full type safety.
```

## 3. PAGE IMPLEMENTATION TEMPLATE

```
**PAGE:** ${PAGE_PATH}

**PURPOSE:**
${PURPOSE}

**ROUTE:** ${ROUTE}

**IMPLEMENTATION:**
\`\`\`typescript
// app${PAGE_PATH}/page.tsx
import { Metadata } from 'next';
import { ${ComponentName} } from '@/components/${COMPONENT}';

export const metadata: Metadata = {
  title: '${PAGE_TITLE}',
  description: '${PAGE_DESCRIPTION}',
};

interface PageProps {
  params: {
    ${PARAM_1}: string;
  };
  searchParams: {
    ${SEARCH_PARAM_1}?: string;
  };
}

export default async function ${PageName}(props: PageProps) {
  const data = await fetchData(props.params);

  return (
    <main className="...">
      <${ComponentName} data={data} />
    </main>
  );
}
\`\`\`

**DATA FETCHING:**
- Server component: Direct DB access or API
- Client component: TanStack Query
- Loading state: Suspense boundary
- Error state: Error boundary

**SEO:**
- Metadata: Set in page component
- Open Graph: Configure metadata
- Structured data: If applicable

Implement page with proper data loading.
```

## 4. TanStack QUERY TEMPLATE

```
**QUERY HOOK:** ${HOOK_NAME}

**PURPOSE:**
${PURPOSE}

**IMPLEMENTATION:**
\`\`\`typescript
interface UseDataOptions {
  ${OPTION_1}?: ${TYPE_1};
  enabled?: boolean;
}

export const useData = (options?: UseDataOptions) => {
  return useQuery<${DATA_TYPE}, Error>({
    queryKey: ['data', options?.${OPTION_1}],
    queryFn: async () => {
      const response = await fetch('/api/data?...');
      if (!response.ok) throw new Error('Failed to fetch');
      return response.json();
    },
    staleTime: ${STALE_TIME_MS},
    gcTime: ${GC_TIME_MS},
    enabled: options?.enabled ?? true,
  });
};

// Usage
const MyComponent = () => {
  const { data, isLoading, error } = useData({ /* options */ });

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;

  return <div>{/* render data */}</div>;
};
\`\`\`

**MUTATION (if applicable):**
\`\`\`typescript
export const useMutateData = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: ${MUTATION_TYPE}) => {
      const response = await fetch('/api/data', {
        method: 'POST',
        body: JSON.stringify(data),
      });
      return response.json();
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['data'] });
    },
  });
};
\`\`\`

Implement TanStack Query hooks.
```

## 5. STYLING TEMPLATE

```
**STYLING:** ${COMPONENT_NAME} Styles

**TAILWIND CLASSES:**
\`\`\`jsx
<div className={cn(
  // Base
  'flex items-center justify-between',
  // Responsive
  'gap-2 md:gap-4',
  // States
  isActive && 'bg-blue-500',
  isDisabled && 'opacity-50 cursor-not-allowed',
  // Conditional
  variant === 'primary' && 'bg-primary text-white',
  variant === 'secondary' && 'bg-gray-100 text-gray-900'
)}>
</div>
\`\`\`

**CUSTOM CSS (if Tailwind insufficient):**
\`\`\`css
.component-name {
  @apply flex items-center;

  &:hover {
    @apply bg-gray-100;
  }

  &.is-active {
    @apply bg-blue-500;
  }
}
\`\`\`

**UTILITY FUNCTION:**
\`\`\`typescript
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
\`\`\`

**DARK MODE:**
- Use Tailwind dark: prefix
- Respect system preference
- Provide toggle if needed

Implement responsive, accessible styling.
```

## 6. FORM HANDLING TEMPLATE

```
**FORM:** ${FORM_NAME}

**SCHEMA (Zod):**
\`\`\`typescript
import { z } from 'zod';

export const ${FormName}Schema = z.object({
  ${FIELD_1}: z.string().min(1, '${FIELD_1} required'),
  ${FIELD_2}: z.number().positive('Must be positive'),
});

export type ${FormName}FormData = z.infer<typeof ${FormName}Schema>;
\`\`\`

**COMPONENT:**
\`\`\`typescript
export const ${FormName}Form = () => {
  const form = useForm<${FormName}FormData>({
    resolver: zodResolver(${FormName}Schema),
    defaultValues: {},
  });

  const onSubmit = async (data: ${FormName}FormData) => {
    try {
      await apiCall(data);
    } catch (error) {
      form.setError('root', { message: 'Failed' });
    }
  };

  return (
    <form onSubmit={form.handleSubmit(onSubmit)}>
      {/* Form fields */}
    </form>
  );
};
\`\`\`

**VALIDATION:**
- Client-side: Zod schema
- Server-side: Always validate
- Error display: Per-field + general

Implement form with validation.
```

## 7. ERROR BOUNDARY TEMPLATE

```
**ERROR BOUNDARY:** ${COMPONENT_NAME} Error Boundary

**IMPLEMENTATION:**
\`\`\`typescript
interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: (error: Error, reset: () => void) => React.ReactNode;
}

export const ErrorBoundary: React.FC<ErrorBoundaryProps> = ({
  children,
  fallback
}) => {
  const [error, setError] = React.useState<Error | null>(null);

  React.useEffect(() => {
    const handler = (event: ErrorEvent) => {
      setError(event.error);
    };

    window.addEventListener('error', handler);
    return () => window.removeEventListener('error', handler);
  }, []);

  if (error) {
    return (
      fallback?.(error, () => setError(null)) ||
      <ErrorFallback error={error} />
    );
  }

  return children;
};
\`\`\`

**USAGE:**
\`\`\`tsx
<ErrorBoundary>
  <SomeComponent />
</ErrorBoundary>
\`\`\`

Implement error boundaries for stability.
```

## 8. PERFORMANCE OPTIMIZATION TEMPLATE

```
**OPTIMIZATION:** ${OPTIMIZATION_NAME}

**CODE SPLITTING:**
\`\`\`typescript
import dynamic from 'next/dynamic';

const HeavyComponent = dynamic(() => import('./Heavy'), {
  loading: () => <LoadingSpinner />,
});
\`\`\`

**MEMOIZATION:**
\`\`\`typescript
const MemoComponent = React.memo(({ data }: Props) => {
  // Only re-renders if props change
  return <div>{data}</div>;
});

// With custom comparison
const CustomMemo = React.memo(Component, (prev, next) => {
  return prev.id === next.id;  // true = skip render
});
\`\`\`

**IMAGE OPTIMIZATION:**
\`\`\`tsx
import Image from 'next/image';

<Image
  src="/image.jpg"
  alt="..."
  width={400}
  height={300}
  priority={isBelowTheFold}
/>
\`\`\`

**PROFILING:**
- Chrome DevTools: Performance tab
- React DevTools: Profiler
- Bundle: `npx next-bundle-analyzer`

Implement performance optimizations.
```

## 9. STATUS REPORT TEMPLATE

```
**FRONTEND ENGINEER STATUS REPORT**
**Report Date:** ${TODAY}

**COMPONENTS DEVELOPED:**
- Components created: ${COMPONENT_COUNT}
- Pages implemented: ${PAGE_COUNT}
- Features completed: ${FEATURE_COUNT}

**CODE QUALITY:**
- TypeScript errors: ${TS_ERRORS}
- Linting issues: ${LINT_ISSUES}
- Test coverage: ${COVERAGE_PERCENT}%

**PERFORMANCE:**
- Bundle size: ${BUNDLE_SIZE}KB (${CHANGE}%)
- Lighthouse score: ${LIGHTHOUSE_SCORE}
- Page load time: ${LOAD_TIME}ms

**ACCESSIBILITY:**
- WCAG compliance: ${WCAG_LEVEL}
- Axe violations: ${AXE_VIOLATIONS}

**BLOCKERS:**
${BLOCKERS}

**NEXT:** ${NEXT_GOALS}
```

## 10. HANDOFF TEMPLATE

```
**FRONTEND ENGINEER HANDOFF**
**From:** ${FROM_AGENT}
**To:** ${TO_AGENT}

**IN-PROGRESS:**
${IN_PROGRESS}

**COMPONENT STATE:**
- Components: ${COMPONENT_STATUS}
- Pages: ${PAGE_STATUS}
- Tests: ${TEST_STATUS}

**BRANCH:** ${CURRENT_BRANCH}

**BLOCKERS:**
${BLOCKERS}

Acknowledge and continue.
```

## 11. CODE REVIEW TEMPLATE

```
**CODE REVIEW**
**File:** ${FILE_PATH}

**REVIEW CHECKLIST:**
- [ ] TypeScript strict
- [ ] No implicit any
- [ ] Props typed
- [ ] Accessible
- [ ] Responsive
- [ ] Tests present
- [ ] Performance OK

**FINDINGS:**
${FINDINGS}

Report review results.
```

## 12. TESTING TEMPLATE

```
**TEST:** ${TEST_NAME}

**TEST FILE:**
Location: `${TEST_FILE_PATH}`

**TEST SETUP:**
\`\`\`typescript
import { render, screen } from '@testing-library/react';
import { ${ComponentName} } from './${ComponentName}';

describe('${ComponentName}', () => {
  it('renders correctly', () => {
    render(<${ComponentName} prop="value" />);
    expect(screen.getByText('...')).toBeInTheDocument();
  });

  it('handles user interaction', async () => {
    const user = userEvent.setup();
    render(<${ComponentName} />);
    await user.click(screen.getByRole('button'));
    expect(...).toBe(...);
  });
});
\`\`\`

Implement comprehensive tests.
```

---

*Last Updated: 2025-12-31*
*Agent: Frontend Engineer*
*Version: 1.0*
