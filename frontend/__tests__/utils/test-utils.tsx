import React, { ReactNode } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

/**
 * Create a fresh QueryClient for testing
 * Disables retries and logging for deterministic tests
 */
export function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
        // Keep staleTime > 0 to prevent immediate refetches that would ignore cached data
        staleTime: 5 * 60 * 1000, // 5 minutes
      },
      mutations: {
        retry: false,
      },
    },
    logger: {
      log: () => {},
      warn: () => {},
      error: () => {},
    },
  })
}

/**
 * Wrapper component for testing hooks with React Query
 */
export function createWrapper() {
  const queryClient = createTestQueryClient()

  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    )
  }
}

/**
 * Mock data factories
 */
export const mockFactories = {
  person: (overrides = {}) => ({
    id: 'person-1',
    name: 'Dr. John Smith',
    email: 'john.smith@hospital.org',
    type: 'resident' as const,
    pgy_level: 2,
    performs_procedures: true,
    specialties: ['Internal Medicine'],
    primary_duty: null,
    faculty_role: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    ...overrides,
  }),

  absence: (overrides = {}) => ({
    id: 'absence-1',
    person_id: 'person-1',
    start_date: '2024-02-01',
    end_date: '2024-02-07',
    absence_type: 'vacation' as const,
    deployment_orders: false,
    tdy_location: null,
    replacement_activity: null,
    notes: null,
    is_away_from_program: true,
    created_at: '2024-01-15T00:00:00Z',
    ...overrides,
  }),

  rotationTemplate: (overrides = {}) => ({
    id: 'template-1',
    name: 'Inpatient Medicine',
    activity_type: 'inpatient',
    template_category: 'rotation' as const,
    abbreviation: 'IM',
    display_abbreviation: 'IM',
    font_color: null,
    background_color: null,
    clinic_location: null,
    max_residents: 4,
    requires_specialty: null,
    requires_procedure_credential: false,
    supervision_required: true,
    max_supervision_ratio: 4,
    created_at: '2024-01-01T00:00:00Z',
    ...overrides,
  }),

  assignment: (overrides = {}) => ({
    id: 'assignment-1',
    block_id: 'block-1',
    person_id: 'person-1',
    rotation_template_id: 'template-1',
    role: 'primary' as const,
    activity_override: null,
    notes: null,
    created_by: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    ...overrides,
  }),

  validation: (overrides = {}) => ({
    valid: true,
    total_violations: 0,
    violations: [],
    coverage_rate: 100,
    statistics: null,
    ...overrides,
  }),
}

/**
 * Mock API responses
 */
export const mockResponses = {
  listPeople: {
    items: [
      mockFactories.person(),
      mockFactories.person({ id: 'person-2', name: 'Dr. Jane Doe', pgy_level: 1 }),
    ],
    total: 2,
  },

  listAbsences: {
    items: [mockFactories.absence()],
    total: 1,
  },

  listTemplates: {
    items: [
      mockFactories.rotationTemplate(),
      mockFactories.rotationTemplate({ id: 'template-2', name: 'Outpatient Clinic', activity_type: 'outpatient' }),
    ],
    total: 2,
  },

  listAssignments: {
    items: [mockFactories.assignment()],
    total: 1,
  },
}
