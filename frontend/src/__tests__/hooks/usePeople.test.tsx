/**
 * usePeople Hook Tests
 *
 * Tests for the usePeople, useCreatePerson, and related hooks
 * using jest.mock() for API mocking.
 */
import { renderHook, waitFor } from '@/test-utils'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactNode } from 'react'
import { usePeople, useCreatePerson } from '@/lib/hooks'
import * as api from '@/lib/api'
import { PersonType } from '@/types/api'

// Mock data (defined locally to avoid MSW dependency)
const mockPeople = [
  {
    id: 'person-1',
    name: 'Dr. John Smith',
    email: 'john.smith@hospital.org',
    type: 'resident' as const,
    pgyLevel: 2,
    performsProcedures: true,
    specialties: ['Internal Medicine'],
    primaryDuty: null,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  },
  {
    id: 'person-2',
    name: 'Dr. Jane Doe',
    email: 'jane.doe@hospital.org',
    type: 'resident' as const,
    pgyLevel: 1,
    performsProcedures: false,
    specialties: ['Internal Medicine'],
    primaryDuty: null,
    createdAt: '2024-01-02T00:00:00Z',
    updatedAt: '2024-01-02T00:00:00Z',
  },
  {
    id: 'person-3',
    name: 'Dr. Robert Faculty',
    email: 'robert.faculty@hospital.org',
    type: 'faculty' as const,
    pgyLevel: null,
    performsProcedures: true,
    specialties: ['Cardiology', 'Internal Medicine'],
    primaryDuty: 'Attending Physician',
    createdAt: '2024-01-03T00:00:00Z',
    updatedAt: '2024-01-03T00:00:00Z',
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

describe('usePeople', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch people list successfully', async () => {
    mockedApi.get.mockResolvedValueOnce({
      items: mockPeople,
      total: mockPeople.length,
    })

    const { result } = renderHook(() => usePeople(), {
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
    expect(result.current.data?.items).toHaveLength(mockPeople.length)
    expect(result.current.data?.total).toBe(mockPeople.length)
    expect(result.current.data?.items[0].name).toBe('Dr. John Smith')
    expect(mockedApi.get).toHaveBeenCalledWith('/people')
  })

  it('should show loading state while fetching', async () => {
    mockedApi.get.mockResolvedValueOnce({
      items: mockPeople,
      total: mockPeople.length,
    })

    const { result } = renderHook(() => usePeople(), {
      wrapper: createWrapper(),
    })

    // Check initial loading state
    expect(result.current.isLoading).toBe(true)
    expect(result.current.isFetching).toBe(true)
    expect(result.current.data).toBeUndefined()

    // Wait for completion
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })
  })

  it('should filter by role when provided', async () => {
    const residents = mockPeople.filter(p => p.type === 'resident')
    mockedApi.get.mockResolvedValueOnce({
      items: residents,
      total: residents.length,
    })

    const { result } = renderHook(
      () => usePeople({ role: 'resident' }),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    // Only residents should be returned
    expect(result.current.data?.items.every(p => p.type === 'resident')).toBe(true)
    expect(mockedApi.get).toHaveBeenCalledWith('/people?role=resident')
  })

  it('should filter by PGY level when provided', async () => {
    const pgy2Residents = mockPeople.filter(p => p.pgyLevel === 2)
    mockedApi.get.mockResolvedValueOnce({
      items: pgy2Residents,
      total: pgy2Residents.length,
    })

    const { result } = renderHook(
      () => usePeople({ pgyLevel: 2 }),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    // Only PGY-2 residents should be returned
    expect(result.current.data?.items.every(p => p.pgyLevel === 2)).toBe(true)
    expect(mockedApi.get).toHaveBeenCalledWith('/people?pgyLevel=2')
  })

  it('should handle API errors gracefully', async () => {
    const apiError = { message: 'Network error', status: 500 }
    mockedApi.get.mockRejectedValueOnce(apiError)

    const { result } = renderHook(() => usePeople(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })
})

describe('useCreatePerson', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should create a new person successfully', async () => {
    const newPerson = {
      id: 'person-new',
      name: 'Dr. New Person',
      email: 'new.person@hospital.org',
      type: 'resident' as const,
      pgyLevel: 3,
      performsProcedures: true,
      specialties: null,
      primaryDuty: null,
      createdAt: '2024-01-01T00:00:00Z',
      updatedAt: '2024-01-01T00:00:00Z',
    }

    mockedApi.post.mockResolvedValueOnce(newPerson)

    const { result } = renderHook(() => useCreatePerson(), {
      wrapper: createWrapper(),
    })

    // Execute mutation
    result.current.mutate({
      name: 'Dr. New Person',
      email: 'new.person@hospital.org',
      type: PersonType.RESIDENT,
      pgyLevel: 3,
      performsProcedures: true,
    })

    // Wait for mutation to complete
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    // Check response
    expect(result.current.data?.name).toBe('Dr. New Person')
    expect(result.current.data?.type).toBe('resident')
    expect(result.current.data?.pgyLevel).toBe(3)
    expect(result.current.data?.id).toBeDefined()
    expect(mockedApi.post).toHaveBeenCalledWith('/people', expect.objectContaining({
      name: 'Dr. New Person',
      type: 'resident',
      pgyLevel: 3,
    }))
  })

  it('should complete mutation successfully for faculty', async () => {
    const newPerson = {
      id: 'person-test',
      name: 'Dr. Test',
      email: null,
      type: 'faculty' as const,
      pgyLevel: null,
      performsProcedures: false,
      specialties: null,
      primaryDuty: null,
      createdAt: '2024-01-01T00:00:00Z',
      updatedAt: '2024-01-01T00:00:00Z',
    }

    mockedApi.post.mockResolvedValueOnce(newPerson)

    const { result } = renderHook(() => useCreatePerson(), {
      wrapper: createWrapper(),
    })

    // Start mutation
    result.current.mutate({
      name: 'Dr. Test',
      type: PersonType.FACULTY,
    })

    // Wait for completion
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    // Check response
    expect(result.current.data?.type).toBe('faculty')
    expect(result.current.data?.pgyLevel).toBeNull()
  })

  it('should handle API errors during creation', async () => {
    const apiError = { message: 'Name is required', status: 400 }
    mockedApi.post.mockRejectedValueOnce(apiError)

    const { result } = renderHook(() => useCreatePerson(), {
      wrapper: createWrapper(),
    })

    // Execute mutation without required fields
    result.current.mutate({
      name: '',
      type: PersonType.RESIDENT,
    })

    // Wait for error
    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error?.message).toBe('Name is required')
  })

  it('should handle validation error for residents without PGY level', async () => {
    const apiError = { message: 'PGY level is required for residents', status: 400 }
    mockedApi.post.mockRejectedValueOnce(apiError)

    const { result } = renderHook(() => useCreatePerson(), {
      wrapper: createWrapper(),
    })

    // Execute mutation without pgyLevel for resident
    result.current.mutate({
      name: 'Dr. Missing PGY',
      type: PersonType.RESIDENT,
    })

    // Wait for error
    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error?.message).toContain('PGY level is required')
  })
})
