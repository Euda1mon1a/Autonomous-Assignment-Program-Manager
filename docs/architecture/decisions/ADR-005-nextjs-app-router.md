***REMOVED*** ADR-005: Next.js 14 App Router (Frontend)

**Date:** 2024-12
**Status:** Adopted

***REMOVED******REMOVED*** Context

The Residency Scheduler frontend requires a modern React framework that provides:
- **Server-side rendering (SSR)**: Fast initial page loads for schedule views
- **SEO capabilities**: Proper meta tags for institutional pages
- **Streaming and progressive enhancement**: Large schedule tables load incrementally
- **Type-safe routing**: Compile-time route validation
- **Developer experience**: Hot reload, clear conventions, minimal configuration

Traditional client-side React applications have slow initial loads and require complex hydration patterns for large data tables.

***REMOVED******REMOVED*** Decision

Use **Next.js 14** with the **App Router** paradigm:
- Next.js 14 as the React framework
- App Router (not Pages Router) for file-based routing
- React Server Components for server-side data fetching
- TanStack Query for client-side state management
- TailwindCSS for utility-first styling

***REMOVED******REMOVED*** Consequences

***REMOVED******REMOVED******REMOVED*** Positive
- **Server-side rendering**: Fast initial page loads, especially for schedule views
- **Type-safe routing**: File-based routing with TypeScript integration
- **Automatic code splitting**: Only load JavaScript for current route
- **React Server Components**: Simplify data fetching without client-side waterfalls
- **Streaming**: Progressive rendering for large schedule tables
- **Modern developer experience**: Fast refresh, clear conventions

***REMOVED******REMOVED******REMOVED*** Negative
- **App Router is newer paradigm**: Less mature ecosystem than Pages Router
- **Server vs client components**: Requires careful separation of concerns
- **Learning curve**: Server Components introduce new mental model
- **Build complexity**: SSR requires understanding of hydration boundaries
- **Deployment constraints**: Requires Node.js runtime (cannot use static export for all routes)

***REMOVED******REMOVED*** Implementation Notes

***REMOVED******REMOVED******REMOVED*** App Router Structure
```
frontend/app/
├── layout.tsx           ***REMOVED*** Root layout (wraps all pages)
├── page.tsx             ***REMOVED*** Home page (/)
├── schedules/
│   ├── page.tsx         ***REMOVED*** Schedules list (/schedules)
│   └── [id]/
│       └── page.tsx     ***REMOVED*** Schedule detail (/schedules/:id)
└── api/
    └── route.ts         ***REMOVED*** API route handlers
```

***REMOVED******REMOVED******REMOVED*** Server Component Pattern
```tsx
// app/schedules/page.tsx (Server Component)
import { getSchedules } from '@/lib/api';

export default async function SchedulesPage() {
  // Data fetching happens on server
  const schedules = await getSchedules();

  return (
    <div>
      <h1>Schedules</h1>
      <ScheduleList schedules={schedules} />
    </div>
  );
}
```

***REMOVED******REMOVED******REMOVED*** Client Component Pattern
```tsx
// components/ScheduleList.tsx (Client Component)
'use client';

import { useQuery } from '@tanstack/react-query';

export function ScheduleList({ initialData }) {
  // Client-side state management with TanStack Query
  const { data, isLoading } = useQuery({
    queryKey: ['schedules'],
    queryFn: fetchSchedules,
    initialData
  });

  // Interactive UI with client-side state
  return <div>{/* ... */}</div>;
}
```

***REMOVED******REMOVED******REMOVED*** TailwindCSS Integration
```tsx
// Utility-first styling
<div className="flex flex-col gap-4 p-6 bg-white rounded-lg shadow">
  <h2 className="text-2xl font-bold text-gray-900">Schedule</h2>
  <p className="text-gray-600">Details...</p>
</div>
```

***REMOVED******REMOVED*** References

- [Next.js 14 Documentation](https://nextjs.org/docs)
- [App Router Guide](https://nextjs.org/docs/app)
- [React Server Components](https://react.dev/blog/2023/03/22/react-labs-what-we-have-been-working-on-march-2023***REMOVED***react-server-components)
- [TanStack Query](https://tanstack.com/query/latest)
- `frontend/app/` - App Router implementation
- `frontend/components/` - Reusable React components
