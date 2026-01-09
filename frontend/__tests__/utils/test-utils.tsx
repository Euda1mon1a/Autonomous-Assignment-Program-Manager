import React, { ReactNode } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { PersonType, AbsenceType, AssignmentRole } from '@/types/api'

/**
 * Create a fresh QueryClient for testing
 * Disables retries for deterministic tests
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
 * Uses proper enum values to satisfy TypeScript type checking
 */
export const mockFactories = {
  person: (overrides = {}) => ({
    id: 'person-1',
    name: 'Dr. John Smith',
    email: 'john.smith@hospital.org',
    type: PersonType.RESIDENT,
    pgyLevel: 2,
    performsProcedures: true,
    specialties: ['Internal Medicine'],
    primaryDuty: null,
    facultyRole: null,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
    ...overrides,
  }),

  absence: (overrides = {}) => ({
    id: 'absence-1',
    personId: 'person-1',
    startDate: '2024-02-01',
    endDate: '2024-02-07',
    absenceType: AbsenceType.VACATION,
    deploymentOrders: false,
    tdyLocation: null,
    replacementActivity: null,
    notes: null,
    isAwayFromProgram: true,
    createdAt: '2024-01-15T00:00:00Z',
    ...overrides,
  }),

  rotationTemplate: (overrides = {}) => ({
    id: 'template-1',
    name: 'Inpatient Medicine',
    activityType: 'inpatient',
    templateCategory: 'rotation' as const,
    abbreviation: 'IM',
    displayAbbreviation: 'IM',
    fontColor: null,
    backgroundColor: null,
    clinicLocation: null,
    maxResidents: 4,
    requiresSpecialty: null,
    requiresProcedureCredential: false,
    supervisionRequired: true,
    maxSupervisionRatio: 4,
    createdAt: '2024-01-01T00:00:00Z',
    ...overrides,
  }),

  assignment: (overrides = {}) => ({
    id: 'assignment-1',
    blockId: 'block-1',
    personId: 'person-1',
    rotationTemplateId: 'template-1',
    role: AssignmentRole.PRIMARY,
    activityOverride: null,
    notes: null,
    createdBy: null,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
    ...overrides,
  }),

  validation: (overrides = {}) => ({
    valid: true,
    totalViolations: 0,
    violations: [],
    coverageRate: 100,
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
      mockFactories.person({ id: 'person-2', name: 'Dr. Jane Doe', pgyLevel: 1 }),
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
      mockFactories.rotationTemplate({ id: 'template-2', name: 'Outpatient Clinic', activityType: 'outpatient' }),
    ],
    total: 2,
  },

  listAssignments: {
    items: [mockFactories.assignment()],
    total: 1,
  },
}
