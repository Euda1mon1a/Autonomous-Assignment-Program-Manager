/**
 * useSchedule Hook Tests
 *
 * Tests for the useSchedule, useGenerateSchedule, and useValidateSchedule hooks
 * using jest.mock() for API mocking.
 */
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactNode } from 'react'
import { useSchedule, useGenerateSchedule, useValidateSchedule } from '@/lib/hooks'
import * as api from '@/lib/api'

// Mock the api module
jest.mock('@/lib/api')

const mockedApi = api as jest.Mocked<typeof api>

// Mock data for assignments
const mockAssignments = [
  {
    id: 'assignment-1',
    block_id: 'block-1',
    person_id: 'person-1',
    rotation_template_id: 'template-1',
    role: 'primary' as const,
    activity_override: null,
    notes: null,
    created_by: 'admin-1',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'assignment-2',
    block_id: 'block-2',
    person_id: 'person-2',
    rotation_template_id: 'template-2',
    role: 'supervising' as const,
    activity_override: null,
    notes: 'Supervising rotation',
    created_by: 'admin-1',
    created_at: '2024-01-02T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z',
  },
]

// Mock validation result
const mockValidationResult = {
  valid: true,
  total_violations: 0,
  violations: [],
  coverage_rate: 0.95,
  statistics: {
    total_blocks: 100,
    assigned_blocks: 95,
  },
}

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

describe('useSchedule', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch schedule data successfully', async () => {
    mockedApi.get.mockResolvedValueOnce({
      items: mockAssignments,
      total: mockAssignments.length,
    })

    const startDate = new Date('2024-01-01')
    const endDate = new Date('2024-01-31')

    const { result } = renderHook(
      () => useSchedule(startDate, endDate),
      { wrapper: createWrapper() }
    )

    // Initially loading
    expect(result.current.isLoading).toBe(true)
    expect(result.current.data).toBeUndefined()

    // Wait for data to load
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    // Check data
    expect(result.current.data?.items).toHaveLength(mockAssignments.length)
    expect(result.current.data?.total).toBe(mockAssignments.length)
    expect(result.current.data?.items[0].role).toBe('primary')
    expect(mockedApi.get).toHaveBeenCalledWith('/assignments?start_date=2024-01-01&end_date=2024-01-31')
  })

  it('should show loading state while fetching', async () => {
    mockedApi.get.mockResolvedValueOnce({
      items: mockAssignments,
      total: mockAssignments.length,
    })

    const startDate = new Date('2024-01-01')
    const endDate = new Date('2024-01-31')

    const { result } = renderHook(
      () => useSchedule(startDate, endDate),
      { wrapper: createWrapper() }
    )

    // Check initial loading state
    expect(result.current.isLoading).toBe(true)
    expect(result.current.isFetching).toBe(true)

    // Wait for completion
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })
  })

  it('should handle API errors gracefully', async () => {
    const apiError = { message: 'Network error', status: 500 }
    mockedApi.get.mockRejectedValueOnce(apiError)

    const startDate = new Date('2024-01-01')
    const endDate = new Date('2024-01-31')

    const { result } = renderHook(
      () => useSchedule(startDate, endDate),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })

  it('should return correct assignment structure', async () => {
    mockedApi.get.mockResolvedValueOnce({
      items: mockAssignments,
      total: mockAssignments.length,
    })

    const startDate = new Date('2024-01-01')
    const endDate = new Date('2024-01-31')

    const { result } = renderHook(
      () => useSchedule(startDate, endDate),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    const firstAssignment = result.current.data?.items[0]
    expect(firstAssignment).toMatchObject({
      id: expect.any(String),
      block_id: expect.any(String),
      person_id: expect.any(String),
      role: expect.any(String),
    })
  })

  it('should handle empty schedule results', async () => {
    mockedApi.get.mockResolvedValueOnce({
      items: [],
      total: 0,
    })

    const startDate = new Date('2024-01-01')
    const endDate = new Date('2024-01-31')

    const { result } = renderHook(
      () => useSchedule(startDate, endDate),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.items).toHaveLength(0)
    expect(result.current.data?.total).toBe(0)
  })
})

describe('useGenerateSchedule', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should generate schedule successfully', async () => {
    const generateResponse = {
      status: 'success' as const,
      message: 'Schedule generated successfully',
      total_blocks_assigned: 95,
      total_blocks: 100,
      validation: mockValidationResult,
      run_id: 'run-123',
      solver_stats: {
        total_blocks: 100,
        total_residents: 10,
        coverage_rate: 0.95,
        solve_time: 5.2,
        iterations: 150,
        branches: null,
        conflicts: null,
      },
    }

    mockedApi.post.mockResolvedValueOnce(generateResponse)

    const { result } = renderHook(() => useGenerateSchedule(), {
      wrapper: createWrapper(),
    })

    // Execute mutation
    result.current.mutate({
      start_date: '2024-01-01',
      end_date: '2024-01-31',
      algorithm: 'greedy',
      pgy_levels: [1, 2, 3],
    })

    // Wait for mutation to complete
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    // Check response
    expect(result.current.data?.status).toBe('success')
    expect(result.current.data?.total_blocks_assigned).toBe(95)
    expect(result.current.data?.total_blocks).toBe(100)
    expect(result.current.data?.run_id).toBe('run-123')
    expect(mockedApi.post).toHaveBeenCalledWith('/schedule/generate', expect.objectContaining({
      start_date: '2024-01-01',
      end_date: '2024-01-31',
      algorithm: 'greedy',
    }))
  })

  it('should handle partial schedule generation', async () => {
    const generateResponse = {
      status: 'partial' as const,
      message: 'Schedule partially generated',
      total_blocks_assigned: 70,
      total_blocks: 100,
      validation: {
        valid: false,
        total_violations: 5,
        violations: [],
        coverage_rate: 0.7,
        statistics: null,
      },
      run_id: 'run-124',
      solver_stats: null,
    }

    mockedApi.post.mockResolvedValueOnce(generateResponse)

    const { result } = renderHook(() => useGenerateSchedule(), {
      wrapper: createWrapper(),
    })

    result.current.mutate({
      start_date: '2024-01-01',
      end_date: '2024-01-31',
      algorithm: 'cp_sat',
      timeout_seconds: 60,
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.status).toBe('partial')
    expect(result.current.data?.total_blocks_assigned).toBe(70)
  })

  it('should handle API error during generation', async () => {
    const apiError = { message: 'Insufficient residents for scheduling', status: 400 }
    mockedApi.post.mockRejectedValueOnce(apiError)

    const { result } = renderHook(() => useGenerateSchedule(), {
      wrapper: createWrapper(),
    })

    result.current.mutate({
      start_date: '2024-01-01',
      end_date: '2024-01-31',
      algorithm: 'greedy',
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error?.message).toContain('Insufficient residents')
  })

  it('should support different scheduling algorithms', async () => {
    const generateResponse = {
      status: 'success' as const,
      message: 'Schedule generated with CP-SAT',
      total_blocks_assigned: 98,
      total_blocks: 100,
      validation: mockValidationResult,
      run_id: 'run-125',
      solver_stats: null,
    }

    mockedApi.post.mockResolvedValueOnce(generateResponse)

    const { result } = renderHook(() => useGenerateSchedule(), {
      wrapper: createWrapper(),
    })

    result.current.mutate({
      start_date: '2024-01-01',
      end_date: '2024-01-31',
      algorithm: 'cp_sat',
      rotation_template_ids: ['template-1', 'template-2'],
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.post).toHaveBeenCalledWith('/schedule/generate', expect.objectContaining({
      algorithm: 'cp_sat',
      rotation_template_ids: ['template-1', 'template-2'],
    }))
  })
})

describe('useValidateSchedule', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should validate schedule successfully with no violations', async () => {
    mockedApi.get.mockResolvedValueOnce(mockValidationResult)

    const { result } = renderHook(
      () => useValidateSchedule('2024-01-01', '2024-01-31'),
      { wrapper: createWrapper() }
    )

    // Initially loading
    expect(result.current.isLoading).toBe(true)

    // Wait for data to load
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    // Check validation result
    expect(result.current.data?.valid).toBe(true)
    expect(result.current.data?.total_violations).toBe(0)
    expect(result.current.data?.coverage_rate).toBe(0.95)
    expect(mockedApi.get).toHaveBeenCalledWith('/schedule/validate?start_date=2024-01-01&end_date=2024-01-31')
  })

  it('should return violations when schedule is invalid', async () => {
    const invalidResult = {
      valid: false,
      total_violations: 3,
      violations: [
        {
          type: 'ACGME_HOURS',
          severity: 'CRITICAL' as const,
          person_id: 'person-1',
          person_name: 'Dr. Smith',
          block_id: 'block-1',
          message: 'Weekly hours exceed 80',
          details: { weekly_hours: 85 },
        },
        {
          type: 'SUPERVISION',
          severity: 'HIGH' as const,
          person_id: 'person-2',
          person_name: 'Dr. Jones',
          block_id: 'block-2',
          message: 'Insufficient supervision ratio',
          details: { ratio: 1.5 },
        },
      ],
      coverage_rate: 0.88,
      statistics: { total_blocks: 100 },
    }

    mockedApi.get.mockResolvedValueOnce(invalidResult)

    const { result } = renderHook(
      () => useValidateSchedule('2024-01-01', '2024-01-31'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.valid).toBe(false)
    expect(result.current.data?.total_violations).toBe(3)
    expect(result.current.data?.violations).toHaveLength(2)
    expect(result.current.data?.violations[0].severity).toBe('CRITICAL')
  })

  it('should handle API errors during validation', async () => {
    const apiError = { message: 'Validation service unavailable', status: 503 }
    mockedApi.get.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useValidateSchedule('2024-01-01', '2024-01-31'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })

  it('should return coverage statistics', async () => {
    const validationWithStats = {
      ...mockValidationResult,
      statistics: {
        total_blocks: 100,
        assigned_blocks: 95,
        unassigned_blocks: 5,
        coverage_by_pgy: {
          pgy1: 0.92,
          pgy2: 0.96,
          pgy3: 0.98,
        },
      },
    }

    mockedApi.get.mockResolvedValueOnce(validationWithStats)

    const { result } = renderHook(
      () => useValidateSchedule('2024-01-01', '2024-01-31'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.statistics).toBeDefined()
    expect(result.current.data?.statistics?.total_blocks).toBe(100)
  })
})
