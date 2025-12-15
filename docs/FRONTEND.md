# Frontend Architecture Documentation

Comprehensive documentation of the Residency Scheduler frontend application architecture.

## Table of Contents

1. [Overview](#overview)
2. [Component Structure](#component-structure)
3. [State Management](#state-management)
4. [Authentication Flow](#authentication-flow)
5. [Routing](#routing)
6. [Styling Conventions](#styling-conventions)
7. [API Integration](#api-integration)
8. [Form Handling](#form-handling)
9. [Type Definitions](#type-definitions)

---

## Overview

### Technology Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| Next.js | 14.0.4 | React framework with App Router |
| TypeScript | 5.x | Type-safe JavaScript |
| React Query | 5.x | Server state management |
| Tailwind CSS | 3.3 | Utility-first CSS framework |
| Axios | 1.6.3 | HTTP client |
| Lucide React | - | Icon library |
| date-fns | 3.1 | Date manipulation |

### Directory Structure

```
frontend/src/
├── app/                      # Next.js App Router pages
│   ├── layout.tsx            # Root layout with providers
│   ├── page.tsx              # Dashboard (home) page
│   ├── login/page.tsx        # Authentication page
│   ├── people/page.tsx       # People management
│   ├── templates/page.tsx    # Rotation templates
│   ├── absences/page.tsx     # Absence management
│   ├── compliance/page.tsx   # ACGME compliance view
│   ├── settings/page.tsx     # Application settings
│   └── providers.tsx         # Client-side providers
├── components/               # Reusable components
│   ├── dashboard/            # Dashboard-specific components
│   ├── forms/                # Form input components
│   ├── skeletons/            # Loading skeleton components
│   ├── ErrorBoundary.tsx     # Error boundary wrapper
│   ├── LoginForm.tsx         # Login form component
│   ├── Modal.tsx             # Modal dialog component
│   ├── Navigation.tsx        # Main navigation bar
│   └── ProtectedRoute.tsx    # Route protection wrapper
├── contexts/                 # React Context providers
│   └── AuthContext.tsx       # Authentication context
├── lib/                      # Utilities and hooks
│   ├── api.ts                # Axios configuration
│   ├── auth.ts               # Authentication utilities
│   ├── hooks.ts              # React Query hooks
│   └── validation.ts         # Form validation
└── types/                    # TypeScript definitions
    ├── api.ts                # API response types
    └── index.ts              # Domain model types
```

---

## Component Structure

### Component Organization

Components are organized by feature and reusability:

- **Page Components** (`app/`): Next.js pages using App Router
- **Feature Components** (`components/dashboard/`, etc.): Domain-specific components
- **Form Components** (`components/forms/`): Reusable form inputs
- **Skeleton Components** (`components/skeletons/`): Loading placeholders
- **Core Components** (`components/`): Shared UI components

### Key Components

#### ProtectedRoute

Wrapper component that enforces authentication.

```tsx
// Usage
import { ProtectedRoute } from '@/components/ProtectedRoute'

export default function SecurePage() {
  return (
    <ProtectedRoute>
      <YourContent />
    </ProtectedRoute>
  )
}

// With admin requirement
<ProtectedRoute requireAdmin={true}>
  <AdminContent />
</ProtectedRoute>
```

**Behavior:**
- Redirects unauthenticated users to `/login`
- Shows loading spinner during authentication check
- Optional `requireAdmin` prop for admin-only pages

#### Navigation

Main application navigation bar with role-based filtering.

```tsx
// Navigation items structure
const navItems: NavItem[] = [
  { href: '/', label: 'Dashboard', icon: Calendar },
  { href: '/people', label: 'People', icon: Users },
  { href: '/templates', label: 'Templates', icon: FileText },
  { href: '/absences', label: 'Absences', icon: CalendarOff },
  { href: '/compliance', label: 'Compliance', icon: AlertTriangle },
  { href: '/settings', label: 'Settings', icon: Settings, adminOnly: true },
]
```

**Features:**
- Active route highlighting via `usePathname()`
- Admin-only items hidden for non-admin users
- Responsive design with mobile menu

#### Modal

Accessible modal dialog with focus management.

```tsx
import { Modal } from '@/components/Modal'

function MyComponent() {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <>
      <button onClick={() => setIsOpen(true)}>Open Modal</button>
      <Modal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        title="Modal Title"
      >
        <p>Modal content goes here</p>
      </Modal>
    </>
  )
}
```

**Accessibility Features:**
- `role="dialog"` and `aria-modal="true"`
- `aria-labelledby` linked to title
- Focus trapping within modal
- Escape key to close
- Click outside to close

#### ErrorBoundary

React error boundary for graceful error handling.

```tsx
import { ErrorBoundary } from '@/components/ErrorBoundary'

<ErrorBoundary>
  <ComponentThatMightError />
</ErrorBoundary>
```

### Form Components

Located in `components/forms/`:

| Component | Purpose |
|-----------|---------|
| `Input` | Text input with label and error handling |
| `Select` | Dropdown select with options |
| `TextArea` | Multi-line text input |
| `DatePicker` | Date selection input |

```tsx
import { Input, Select, DatePicker } from '@/components/forms'

<Input
  label="Name"
  name="name"
  value={name}
  onChange={(e) => setName(e.target.value)}
  error={errors.name}
  required
/>

<Select
  label="Type"
  name="type"
  value={type}
  onChange={(e) => setType(e.target.value)}
  options={[
    { value: 'resident', label: 'Resident' },
    { value: 'faculty', label: 'Faculty' },
  ]}
/>

<DatePicker
  label="Start Date"
  name="startDate"
  value={startDate}
  onChange={(e) => setStartDate(e.target.value)}
/>
```

### Dashboard Components

Located in `components/dashboard/`:

| Component | Purpose |
|-----------|---------|
| `DashboardSummary` | Key metrics overview |
| `DashboardAlerts` | Compliance alerts and notifications |
| `UpcomingAbsences` | Upcoming absence calendar |
| `QuickActions` | Common action shortcuts |

---

## State Management

### React Query Setup

Server state is managed using TanStack Query (React Query).

#### Configuration

```tsx
// app/providers.tsx
'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000,        // 1 minute default
      refetchOnWindowFocus: false,  // Disable auto-refetch on focus
    },
  },
})

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}
```

#### Query Keys

Centralized query key management in `lib/hooks.ts`:

```typescript
export const queryKeys = {
  // Schedule
  schedule: (startDate: string, endDate: string) =>
    ['schedule', startDate, endDate] as const,

  // People
  people: (filters?: PeopleFilters) =>
    ['people', filters] as const,
  person: (id: string) =>
    ['people', id] as const,
  residents: (pgyLevel?: number) =>
    ['residents', pgyLevel] as const,
  faculty: (specialty?: string) =>
    ['faculty', specialty] as const,

  // Absences
  absences: (filters?: AbsenceFilters) =>
    ['absences', filters] as const,
  absence: (id: string) =>
    ['absences', id] as const,

  // Rotation Templates
  rotationTemplates: (activityType?: string) =>
    ['rotation-templates', activityType] as const,

  // Assignments
  assignments: (filters?: AssignmentFilters) =>
    ['assignments', filters] as const,

  // Validation
  validation: (startDate: string, endDate: string) =>
    ['validation', startDate, endDate] as const,
}
```

### Custom Hooks

#### Data Fetching Hooks

```typescript
// lib/hooks.ts

// Schedule
export function useSchedule(startDate: string, endDate: string) {
  return useQuery({
    queryKey: queryKeys.schedule(startDate, endDate),
    queryFn: () => api.get<ScheduleResponse>(
      `/schedule/${startDate}/${endDate}`
    ),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

// People
export function usePeople(filters?: PeopleFilters) {
  return useQuery({
    queryKey: queryKeys.people(filters),
    queryFn: () => api.get<ListResponse<Person>>('/people', { params: filters }),
    staleTime: 5 * 60 * 1000,
  })
}

// Absences
export function useAbsences(personId?: string) {
  return useQuery({
    queryKey: queryKeys.absences({ person_id: personId }),
    queryFn: () => api.get<ListResponse<Absence>>('/absences', {
      params: personId ? { person_id: personId } : undefined,
    }),
    staleTime: 5 * 60 * 1000,
  })
}

// Rotation Templates
export function useRotationTemplates() {
  return useQuery({
    queryKey: queryKeys.rotationTemplates(),
    queryFn: () => api.get<ListResponse<RotationTemplate>>('/rotation-templates'),
    staleTime: 10 * 60 * 1000, // 10 minutes
  })
}
```

#### Mutation Hooks

```typescript
// Create Person
export function useCreatePerson() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreatePersonRequest) =>
      api.post<Person>('/people', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['people'] })
      queryClient.invalidateQueries({ queryKey: ['residents'] })
      queryClient.invalidateQueries({ queryKey: ['faculty'] })
    },
  })
}

// Update Person
export function useUpdatePerson() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdatePersonRequest }) =>
      api.put<Person>(`/people/${id}`, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['people'] })
      queryClient.invalidateQueries({ queryKey: ['people', id] })
    },
  })
}

// Delete Person
export function useDeletePerson() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => api.del(`/people/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['people'] })
    },
  })
}

// Generate Schedule
export function useGenerateSchedule() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: GenerateScheduleRequest) =>
      api.post<ScheduleGenerateResponse>('/schedule/generate', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schedule'] })
      queryClient.invalidateQueries({ queryKey: ['assignments'] })
      queryClient.invalidateQueries({ queryKey: ['validation'] })
    },
  })
}

// Validate Schedule
export function useValidateSchedule(startDate: string, endDate: string) {
  return useQuery({
    queryKey: queryKeys.validation(startDate, endDate),
    queryFn: () => api.get<ValidationResult>('/schedule/validate', {
      params: { start_date: startDate, end_date: endDate },
    }),
    enabled: !!startDate && !!endDate,
  })
}
```

### Usage Patterns

#### Loading States

```tsx
function PeopleList() {
  const { data, isLoading, isError, error, refetch } = usePeople()

  if (isLoading) return <PeopleListSkeleton />
  if (isError) return <ErrorMessage error={error} onRetry={refetch} />

  return (
    <ul>
      {data?.items.map((person) => (
        <PersonCard key={person.id} person={person} />
      ))}
    </ul>
  )
}
```

#### Mutations with Optimistic Updates

```tsx
function PersonCard({ person }: { person: Person }) {
  const { mutate: deletePerson, isPending } = useDeletePerson()

  const handleDelete = () => {
    if (confirm('Are you sure?')) {
      deletePerson(person.id)
    }
  }

  return (
    <div className="card">
      <h3>{person.name}</h3>
      <button
        onClick={handleDelete}
        disabled={isPending}
        className="btn-danger"
      >
        {isPending ? 'Deleting...' : 'Delete'}
      </button>
    </div>
  )
}
```

---

## Authentication Flow

### Architecture

Authentication uses JWT tokens with React Context for state management.

### AuthContext

```typescript
// contexts/AuthContext.tsx

interface AuthContextType {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (credentials: LoginCredentials) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
}

interface User {
  id: string
  username: string
  email: string
  role: 'admin' | 'coordinator' | 'faculty' | 'resident'
  is_active: boolean
}

interface LoginCredentials {
  username: string
  password: string
}
```

### Token Storage

```typescript
// lib/auth.ts

const TOKEN_KEY = 'auth_token'

export function getStoredToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem(TOKEN_KEY)
}

export function setStoredToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

export function removeStoredToken(): void {
  localStorage.removeItem(TOKEN_KEY)
}

export function hasStoredToken(): boolean {
  return !!getStoredToken()
}
```

### Authentication Flow

```
1. App Initialization
   ├── AuthProvider mounts
   ├── Check localStorage for existing token
   ├── If token exists, validate with /auth/me
   └── Set user state (valid user or null)

2. Login Flow
   ├── User submits credentials via LoginForm
   ├── POST /api/auth/login with OAuth2 form data
   ├── Receive JWT token in response
   ├── Store token in localStorage
   └── Load user data from response

3. Protected Route Access
   ├── ProtectedRoute checks isAuthenticated
   ├── If not authenticated, redirect to /login
   └── If authenticated, render children

4. Logout Flow
   ├── POST /api/auth/logout
   ├── Remove token from localStorage
   ├── Clear user state
   └── Redirect to /login

5. Token Expiration
   ├── API returns 401 Unauthorized
   ├── Axios interceptor catches error
   ├── Remove token from localStorage
   └── Redirect to /login
```

### Usage

```tsx
// Using authentication in components
import { useAuth } from '@/contexts/AuthContext'

function ProfileButton() {
  const { user, isAuthenticated, logout } = useAuth()

  if (!isAuthenticated) {
    return <Link href="/login">Login</Link>
  }

  return (
    <div>
      <span>Welcome, {user?.username}</span>
      <button onClick={logout}>Logout</button>
    </div>
  )
}

// Role-based rendering
function AdminPanel() {
  const { user } = useAuth()

  if (user?.role !== 'admin') {
    return null
  }

  return <AdminContent />
}
```

---

## Routing

### App Router Structure

Using Next.js 14 App Router with file-based routing.

```
app/
├── layout.tsx          # Root layout
├── page.tsx            # / (Dashboard)
├── login/
│   └── page.tsx        # /login
├── people/
│   └── page.tsx        # /people
├── templates/
│   └── page.tsx        # /templates
├── absences/
│   └── page.tsx        # /absences
├── compliance/
│   └── page.tsx        # /compliance
└── settings/
    └── page.tsx        # /settings
```

### Route Protection

```tsx
// app/people/page.tsx
'use client'

import { ProtectedRoute } from '@/components/ProtectedRoute'
import { PeopleManager } from '@/components/PeopleManager'

export default function PeoplePage() {
  return (
    <ProtectedRoute>
      <PeopleManager />
    </ProtectedRoute>
  )
}

// app/settings/page.tsx (admin only)
'use client'

import { ProtectedRoute } from '@/components/ProtectedRoute'
import { Settings } from '@/components/Settings'

export default function SettingsPage() {
  return (
    <ProtectedRoute requireAdmin={true}>
      <Settings />
    </ProtectedRoute>
  )
}
```

### Navigation

```tsx
import Link from 'next/link'
import { usePathname } from 'next/navigation'

function NavLink({ href, children }: { href: string; children: React.ReactNode }) {
  const pathname = usePathname()
  const isActive = pathname === href

  return (
    <Link
      href={href}
      className={`nav-link ${isActive ? 'nav-link-active' : ''}`}
    >
      {children}
    </Link>
  )
}
```

### Programmatic Navigation

```tsx
import { useRouter } from 'next/navigation'

function LoginForm() {
  const router = useRouter()

  const handleSuccess = () => {
    router.push('/') // Navigate to dashboard
  }

  // ...
}
```

---

## Styling Conventions

### Tailwind CSS Configuration

```typescript
// tailwind.config.ts
import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      colors: {
        // Activity type colors
        clinic: {
          light: '#dbeafe',
          DEFAULT: '#3b82f6',
          dark: '#1d4ed8',
        },
        inpatient: {
          light: '#ede9fe',
          DEFAULT: '#8b5cf6',
          dark: '#6d28d9',
        },
        call: {
          light: '#fee2e2',
          DEFAULT: '#ef4444',
          dark: '#b91c1c',
        },
        leave: {
          light: '#fef3c7',
          DEFAULT: '#f59e0b',
          dark: '#d97706',
        },
      },
    },
  },
  plugins: [],
}

export default config
```

### Component Classes

Defined in `globals.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer components {
  /* Buttons */
  .btn-primary {
    @apply bg-blue-600 text-white px-4 py-2 rounded-md
           hover:bg-blue-700 transition-colors
           disabled:opacity-50 disabled:cursor-not-allowed;
  }

  .btn-secondary {
    @apply bg-gray-200 text-gray-800 px-4 py-2 rounded-md
           hover:bg-gray-300 transition-colors;
  }

  .btn-danger {
    @apply bg-red-600 text-white px-4 py-2 rounded-md
           hover:bg-red-700 transition-colors;
  }

  /* Forms */
  .input-field {
    @apply w-full px-3 py-2 border border-gray-300 rounded-md
           shadow-sm focus:outline-none focus:ring-2
           focus:ring-blue-500 focus:border-blue-500;
  }

  .input-error {
    @apply border-red-500 focus:ring-red-500 focus:border-red-500;
  }

  /* Cards */
  .card {
    @apply bg-white rounded-lg shadow-md p-6;
  }

  .card-header {
    @apply text-lg font-semibold text-gray-900 mb-4;
  }

  /* Schedule */
  .schedule-cell {
    @apply p-2 border-r cursor-pointer
           hover:ring-2 hover:ring-blue-400 transition-all;
  }

  /* Navigation */
  .nav-link {
    @apply flex items-center gap-2 px-3 py-2 rounded-md
           text-gray-700 hover:bg-gray-100 transition-colors;
  }

  .nav-link-active {
    @apply bg-blue-50 text-blue-700 font-medium;
  }
}
```

### Typography

| Element | Classes |
|---------|---------|
| Page title | `text-2xl font-bold text-gray-900` |
| Section header | `text-lg font-semibold text-gray-900` |
| Body text | `text-sm text-gray-600` |
| Helper text | `text-xs text-gray-400` |
| Error text | `text-sm text-red-600` |

### Layout Patterns

```tsx
// Page container
<div className="max-w-7xl mx-auto px-4 py-8">
  {/* Page content */}
</div>

// Responsive grid
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
  {items.map(item => <Card key={item.id} />)}
</div>

// Flex header with actions
<div className="flex items-center justify-between mb-6">
  <h1 className="text-2xl font-bold text-gray-900">Page Title</h1>
  <button className="btn-primary">Add New</button>
</div>
```

### Status Indicators

```tsx
// Success/Healthy
<span className="px-2 py-1 bg-green-50 text-green-700 rounded-full text-sm">
  Active
</span>

// Error/Critical
<span className="px-2 py-1 bg-red-50 text-red-600 rounded-full text-sm">
  Violation
</span>

// Warning
<span className="px-2 py-1 bg-amber-50 text-amber-700 rounded-full text-sm">
  Pending
</span>

// Info/Neutral
<span className="px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-sm">
  Scheduled
</span>
```

### Loading States

```tsx
// Skeleton loading
<div className="animate-pulse">
  <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
  <div className="h-4 bg-gray-200 rounded w-1/2"></div>
</div>

// Spinner
<Loader2 className="h-6 w-6 animate-spin text-blue-600" />
```

---

## API Integration

### Axios Configuration

```typescript
// lib/api.ts
import axios, { AxiosError, AxiosInstance } from 'axios'
import { getStoredToken, removeStoredToken } from './auth'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'

const axiosInstance: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor - attach auth token
axiosInstance.interceptors.request.use((config) => {
  const token = getStoredToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor - handle errors
axiosInstance.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      removeStoredToken()
      window.location.href = '/login'
    }
    return Promise.reject(transformError(error))
  }
)

function transformError(error: AxiosError): ApiError {
  if (error.response) {
    const status = error.response.status
    const data = error.response.data as { detail?: string }

    return {
      message: data.detail || getDefaultMessage(status),
      status,
      detail: data.detail,
    }
  }

  return {
    message: 'Network error. Please check your connection.',
    status: 0,
  }
}

function getDefaultMessage(status: number): string {
  switch (status) {
    case 400: return 'Invalid request'
    case 401: return 'Please log in to continue'
    case 403: return 'You do not have permission'
    case 404: return 'Resource not found'
    case 500: return 'Server error. Please try again later.'
    default: return 'An unexpected error occurred'
  }
}

// Typed API methods
export const api = {
  get: <T>(url: string, config?: object) =>
    axiosInstance.get<T>(url, config).then((res) => res.data),

  post: <T>(url: string, data?: object, config?: object) =>
    axiosInstance.post<T>(url, data, config).then((res) => res.data),

  put: <T>(url: string, data?: object, config?: object) =>
    axiosInstance.put<T>(url, data, config).then((res) => res.data),

  patch: <T>(url: string, data?: object, config?: object) =>
    axiosInstance.patch<T>(url, data, config).then((res) => res.data),

  del: (url: string, config?: object) =>
    axiosInstance.delete(url, config),
}

export interface ApiError {
  message: string
  status: number
  detail?: string
  errors?: Record<string, string[]>
}
```

---

## Form Handling

### Validation Utilities

```typescript
// lib/validation.ts

export function validateEmail(email: string): string | null {
  if (!email) return 'Email is required'
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(email)) return 'Invalid email format'
  return null
}

export function validateRequired(
  value: string | number | null | undefined,
  fieldName: string
): string | null {
  if (value === null || value === undefined || value === '') {
    return `${fieldName} is required`
  }
  return null
}

export function validateDateRange(
  startDate: string,
  endDate: string
): string | null {
  if (!startDate || !endDate) return null
  if (new Date(endDate) < new Date(startDate)) {
    return 'End date must be after start date'
  }
  return null
}

export function validatePassword(password: string): string | null {
  if (!password) return 'Password is required'
  if (password.length < 8) return 'Password must be at least 8 characters'
  return null
}

export function validateMinLength(
  value: string,
  minLength: number,
  fieldName: string
): string | null {
  if (value && value.length < minLength) {
    return `${fieldName} must be at least ${minLength} characters`
  }
  return null
}

export function validatePgyLevel(level: number | null): string | null {
  if (level === null || level === undefined) return 'PGY level is required'
  if (level < 1 || level > 8) return 'PGY level must be between 1 and 8'
  return null
}
```

### Form Pattern

```tsx
function PersonForm({ onSuccess }: { onSuccess: () => void }) {
  const [formData, setFormData] = useState({
    name: '',
    type: 'resident',
    email: '',
    pgy_level: null as number | null,
  })
  const [touched, setTouched] = useState<Record<string, boolean>>({})
  const { mutate: createPerson, isPending } = useCreatePerson()

  // Validation
  const errors = useMemo(() => ({
    name: validateRequired(formData.name, 'Name'),
    email: formData.email ? validateEmail(formData.email) : null,
    pgy_level: formData.type === 'resident'
      ? validatePgyLevel(formData.pgy_level)
      : null,
  }), [formData])

  const isValid = Object.values(errors).every((error) => !error)

  const handleChange = (field: string, value: string | number) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
  }

  const handleBlur = (field: string) => {
    setTouched((prev) => ({ ...prev, [field]: true }))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!isValid) return

    createPerson(formData, {
      onSuccess: () => {
        onSuccess()
      },
    })
  }

  return (
    <form onSubmit={handleSubmit}>
      <Input
        label="Name"
        name="name"
        value={formData.name}
        onChange={(e) => handleChange('name', e.target.value)}
        onBlur={() => handleBlur('name')}
        error={touched.name ? errors.name : null}
        required
      />

      <Select
        label="Type"
        name="type"
        value={formData.type}
        onChange={(e) => handleChange('type', e.target.value)}
        options={[
          { value: 'resident', label: 'Resident' },
          { value: 'faculty', label: 'Faculty' },
        ]}
      />

      {formData.type === 'resident' && (
        <Select
          label="PGY Level"
          name="pgy_level"
          value={formData.pgy_level?.toString() || ''}
          onChange={(e) => handleChange('pgy_level', parseInt(e.target.value))}
          onBlur={() => handleBlur('pgy_level')}
          error={touched.pgy_level ? errors.pgy_level : null}
          options={[
            { value: '1', label: 'PGY-1' },
            { value: '2', label: 'PGY-2' },
            { value: '3', label: 'PGY-3' },
          ]}
          required
        />
      )}

      <Input
        label="Email"
        name="email"
        type="email"
        value={formData.email}
        onChange={(e) => handleChange('email', e.target.value)}
        onBlur={() => handleBlur('email')}
        error={touched.email ? errors.email : null}
      />

      <button
        type="submit"
        disabled={!isValid || isPending}
        className="btn-primary"
      >
        {isPending ? 'Creating...' : 'Create Person'}
      </button>
    </form>
  )
}
```

---

## Type Definitions

### Domain Models

```typescript
// types/index.ts

export interface Person {
  id: string
  name: string
  type: 'resident' | 'faculty'
  email: string | null
  pgy_level: number | null
  performs_procedures: boolean
  specialties: string[] | null
  primary_duty: string | null
  created_at: string
  updated_at: string
}

export interface Block {
  id: string
  date: string
  time_of_day: 'AM' | 'PM'
  block_number: number
  is_weekend: boolean
  is_holiday: boolean
  holiday_name: string | null
}

export interface Assignment {
  id: string
  block_id: string
  person_id: string
  rotation_template_id: string | null
  role: 'primary' | 'supervising' | 'backup'
  activity_override: string | null
  notes: string | null
  created_by: string | null
  created_at: string
  updated_at: string
}

export interface Absence {
  id: string
  person_id: string
  start_date: string
  end_date: string
  absence_type: 'vacation' | 'deployment' | 'tdy' | 'medical' | 'family_emergency' | 'conference'
  deployment_orders: boolean
  tdy_location: string | null
  replacement_activity: string | null
  notes: string | null
  created_at: string
}

export interface RotationTemplate {
  id: string
  name: string
  activity_type: 'clinic' | 'inpatient' | 'procedure' | 'conference'
  abbreviation: string | null
  clinic_location: string | null
  max_residents: number | null
  requires_specialty: string | null
  requires_procedure_credential: boolean
  supervision_required: boolean
  max_supervision_ratio: number
  created_at: string
}
```

### API Response Types

```typescript
// types/api.ts

export interface ListResponse<T> {
  items: T[]
  total: number
}

export interface PaginatedResponse<T> extends ListResponse<T> {
  page: number
  per_page: number
  total_pages: number
}

export interface ScheduleResponse {
  start_date: string
  end_date: string
  schedule: Record<string, {
    AM: ScheduleEntry[]
    PM: ScheduleEntry[]
  }>
  total_assignments: number
}

export interface ScheduleEntry {
  id: string
  person: {
    id: string
    name: string
    type: string
    pgy_level: number | null
  }
  role: string
  activity: string
  abbreviation: string | null
}

export interface ScheduleGenerateResponse {
  status: 'success' | 'partial' | 'failed'
  message: string
  total_blocks_assigned: number
  total_blocks: number
  validation: ValidationResult
  run_id: string | null
}

export interface ValidationResult {
  valid: boolean
  total_violations: number
  violations: Violation[]
  coverage_rate: number
  statistics: Record<string, number>
}

export interface Violation {
  type: string
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'
  person_id: string
  person_name: string
  block_id: string | null
  message: string
  details: Record<string, unknown>
}

export interface User {
  id: string
  username: string
  email: string
  role: 'admin' | 'coordinator' | 'faculty' | 'resident'
  is_active: boolean
}

export interface TokenResponse {
  access_token: string
  token_type: string
}
```

---

*End of Frontend Architecture Documentation*
