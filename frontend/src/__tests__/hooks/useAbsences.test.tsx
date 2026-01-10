/**
 * useAbsences Hook Tests
 *
 * Tests for the useAbsences, useCreateAbsence, and related hooks
 * using jest.mock() for API mocking.
 */
import { renderHook, waitFor } from '@/test-utils'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactNode } from 'react'
import { useAbsences, useCreateAbsence } from '@/lib/hooks'
import * as api from '@/lib/api'

import { AbsenceType } from '@/types/api'

// Mock data (defined locally to avoid MSW dependency)
const mockAbsences = [
  {
    id: 'absence-1',
    personId: 'person-1',
    startDate: '2024-03-15',
    endDate: '2024-03-22',
    absenceType: AbsenceType.VACATION,
    isAwayFromProgram: true,
    deploymentOrders: false,
    tdyLocation: null,
    replacementActivity: null,
    notes: 'Spring vacation',
    createdAt: '2024-01-15T00:00:00Z',
  },
  {
    id: 'absence-2',
    personId: 'person-2',
    startDate: '2024-04-01',
    endDate: '2024-04-03',
    absenceType: AbsenceType.CONFERENCE,
    isAwayFromProgram: true,
    deploymentOrders: false,
    tdyLocation: 'Chicago, IL',
    replacementActivity: null,
    notes: 'Medical conference',
    createdAt: '2024-02-01T00:00:00Z',
  },
  {
    id: 'absence-3',
    personId: 'person-1',
    startDate: '2024-05-10',
    endDate: '2024-05-12',
    absenceType: AbsenceType.SICK,
    isAwayFromProgram: false,
    deploymentOrders: false,
    tdyLocation: null,
    replacementActivity: null,
    notes: null,
    createdAt: '2024-05-09T00:00:00Z',
  },
]

// Mock the api module
jest.mock('@/lib/api')

const mockedApi = api as jest.Mocked<typeof api>

// Create a fresh QueryClient for each test
function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
        staleTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  })
}

// Wrapper component with QueryClientProvider
function createWrapper() {
  const queryClient = createTestQueryClient()
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    )
  }
}

describe('useAbsences', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch absences list successfully', async () => {
    mockedApi.get.mockResolvedValueOnce({
      items: mockAbsences,
      total: mockAbsences.length,
    })

    const { result } = renderHook(() => useAbsences(), {
      wrapper: createWrapper(),
    })

    // Initially loading
    expect(result.current.isLoading).toBe(true)
    expect(result.current.data).toBeUndefined()

    // Wait for data to load
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    // Check data
    expect(result.current.data?.items).toHaveLength(mockAbsences.length)
    expect(result.current.data?.total).toBe(mockAbsences.length)
    expect(result.current.data?.items[0].absenceType).toBe('vacation')
    expect(mockedApi.get).toHaveBeenCalledWith('/absences')
  })

  it('should show loading state while fetching', async () => {
    mockedApi.get.mockResolvedValueOnce({
      items: mockAbsences,
      total: mockAbsences.length,
    })

    const { result } = renderHook(() => useAbsences(), {
      wrapper: createWrapper(),
    })

    // Check initial loading state
    expect(result.current.isLoading).toBe(true)
    expect(result.current.isFetching).toBe(true)

    // Wait for completion
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })
  })

  it('should return absence details with correct structure', async () => {
    mockedApi.get.mockResolvedValueOnce({
      items: mockAbsences,
      total: mockAbsences.length,
    })

    const { result } = renderHook(() => useAbsences(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    const firstAbsence = result.current.data?.items[0]
    expect(firstAbsence).toMatchObject({
      id: expect.any(String),
      personId: expect.any(String),
      startDate: expect.any(String),
      endDate: expect.any(String),
      absenceType: expect.any(String),
    })
  })

  it('should handle API errors gracefully', async () => {
    const apiError = { message: 'Network error', status: 500 }
    mockedApi.get.mockRejectedValueOnce(apiError)

    const { result } = renderHook(() => useAbsences(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })
})

describe('useCreateAbsence', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should create a new absence successfully', async () => {
    const newAbsence = {
      id: 'absence-new',
      personId: 'person-1',
      startDate: '2024-04-01',
      endDate: '2024-04-05',
      absenceType: AbsenceType.VACATION,
      isAwayFromProgram: true,
      deploymentOrders: false,
      tdyLocation: null,
      replacementActivity: null,
      notes: 'Spring break',
      createdAt: '2024-01-01T00:00:00Z',
    }

    mockedApi.post.mockResolvedValueOnce(newAbsence)

    const { result } = renderHook(() => useCreateAbsence(), {
      wrapper: createWrapper(),
    })

    // Execute mutation
    result.current.mutate({
      personId: 'person-1',
      startDate: '2024-04-01',
      endDate: '2024-04-05',
      absenceType: AbsenceType.VACATION,
      notes: 'Spring break',
    })

    // Wait for mutation to complete
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    // Check response
    expect(result.current.data?.personId).toBe('person-1')
    expect(result.current.data?.startDate).toBe('2024-04-01')
    expect(result.current.data?.endDate).toBe('2024-04-05')
    expect(result.current.data?.absenceType).toBe('vacation')
    expect(result.current.data?.id).toBeDefined()
    expect(mockedApi.post).toHaveBeenCalledWith('/absences', expect.objectContaining({
      personId: 'person-1',
      startDate: '2024-04-01',
      absenceType: 'vacation',
    }))
  })

  it('should complete mutation successfully for conference absence', async () => {
    const newAbsence = {
      id: 'absence-test',
      personId: 'person-1',
      startDate: '2024-05-01',
      endDate: '2024-05-03',
      absenceType: AbsenceType.CONFERENCE,
      isAwayFromProgram: true,
      deploymentOrders: false,
      tdyLocation: null,
      replacementActivity: null,
      notes: null,
      createdAt: '2024-01-01T00:00:00Z',
    }

    mockedApi.post.mockResolvedValueOnce(newAbsence)

    const { result } = renderHook(() => useCreateAbsence(), {
      wrapper: createWrapper(),
    })

    // Start mutation
    result.current.mutate({
      personId: 'person-1',
      startDate: '2024-05-01',
      endDate: '2024-05-03',
      absenceType: AbsenceType.CONFERENCE,
    })

    // Wait for completion
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    // Check response
    expect(result.current.data?.absenceType).toBe('conference')
    expect(result.current.data?.personId).toBe('person-1')
  })

  it('should handle API error when personId is missing', async () => {
    const apiError = { message: 'Person ID is required', status: 400 }
    mockedApi.post.mockRejectedValueOnce(apiError)

    const { result } = renderHook(() => useCreateAbsence(), {
      wrapper: createWrapper(),
    })

    // Execute mutation without personId
    result.current.mutate({
      personId: '',
      startDate: '2024-04-01',
      endDate: '2024-04-05',
      absenceType: AbsenceType.VACATION,
    })

    // Wait for error
    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error?.message).toContain('Person ID is required')
  })

  it('should handle API error when dates are missing', async () => {
    const apiError = { message: 'Start and end dates are required', status: 400 }
    mockedApi.post.mockRejectedValueOnce(apiError)

    const { result } = renderHook(() => useCreateAbsence(), {
      wrapper: createWrapper(),
    })

    // Execute mutation without dates
    result.current.mutate({
      personId: 'person-1',
      startDate: '',
      endDate: '',
      absenceType: AbsenceType.VACATION,
    })

    // Wait for error
    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error?.message).toContain('dates are required')
  })

  it('should handle API error when end date is before start date', async () => {
    const apiError = { message: 'End date must be after start date', status: 400 }
    mockedApi.post.mockRejectedValueOnce(apiError)

    const { result } = renderHook(() => useCreateAbsence(), {
      wrapper: createWrapper(),
    })

    // Execute mutation with invalid date range
    result.current.mutate({
      personId: 'person-1',
      startDate: '2024-04-10',
      endDate: '2024-04-01', // Before start date
      absenceType: AbsenceType.VACATION,
    })

    // Wait for error
    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error?.message).toContain('End date must be after start date')
  })

  it('should support different absence types', async () => {
    const newAbsence = {
      id: 'absence-conf',
      personId: 'person-2',
      startDate: '2024-06-01',
      endDate: '2024-06-03',
      absenceType: AbsenceType.CONFERENCE,
      isAwayFromProgram: true,
      deploymentOrders: false,
      tdyLocation: null,
      replacementActivity: null,
      notes: 'Annual medical conference',
      createdAt: '2024-01-01T00:00:00Z',
    }

    mockedApi.post.mockResolvedValueOnce(newAbsence)

    const { result } = renderHook(() => useCreateAbsence(), {
      wrapper: createWrapper(),
    })

    // Create a conference absence
    result.current.mutate({
      personId: 'person-2',
      startDate: '2024-06-01',
      endDate: '2024-06-03',
      absenceType: AbsenceType.CONFERENCE,
      notes: 'Annual medical conference',
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.absenceType).toBe('conference')
    expect(result.current.data?.notes).toBe('Annual medical conference')
  })
})
