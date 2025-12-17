# Frontend Design

Next.js application architecture.

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| Framework | Next.js 14 |
| UI Library | React 18 |
| Type Safety | TypeScript |
| Styling | TailwindCSS |
| State | TanStack Query |
| Animation | Framer Motion |

---

## Directory Structure

```
frontend/src/
├── app/              # Next.js App Router
├── features/         # Feature modules
│   ├── analytics/
│   ├── audit/
│   ├── schedule/
│   └── swap-marketplace/
├── components/       # Reusable components
├── contexts/         # React Context
├── lib/              # Utilities, API client
└── types/            # TypeScript types
```

---

## Key Patterns

- **Feature-based** modularization
- **Server Components** for static content
- **Client Components** for interactivity
- **TanStack Query** for server state
