/**
 * Tests for useSchedule hook
 * Tests schedule fetching, date formatting, and refetch behavior
 */
import { renderHook, waitFor, act } from '@testing-library/react'
import { useSchedule, useGenerateSchedule, useValidateSchedule } from '@/lib/hooks'
import { createWrapper, mockFactories, mockResponses } from '../utils/test-utils'
import * as api from '@/lib/api'

// Mock the api module
jest.mock('@/lib/api', () => ({
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  del: jest.fn(),
}))

const mockedApi = api as jest.Mocked<typeof api>

describe('useSchedule', () => {
  const startDate = new Date('2024-02-01')
  const endDate = new Date('2024-02-28')

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch schedule data for date range', async () => {
    mockedApi.get.mockResolvedValueOnce(mockResponses.listAssignments)

    const { result } = renderHook(
      () => useSchedule(startDate, endDate),
      { wrapper: createWrapper() }
    )

    expect(result.current.isLoading).toBe(true)

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith(
      '/api/assignments?start_date=2024-02-01&end_date=2024-02-28'
    )
    expect(result.current.data).toEqual(mockResponses.listAssignments)
  })

  it('should handle API errors gracefully', async () => {
    const apiError = { message: 'Server error', status: 500 }
    mockedApi.get.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useSchedule(startDate, endDate),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })

  it('should refetch when dates change', async () => {
    mockedApi.get.mockResolvedValue(mockResponses.listAssignments)

    const { result, rerender } = renderHook(
      ({ start, end }) => useSchedule(start, end),
      {
        wrapper: createWrapper(),
        initialProps: { start: startDate, end: endDate },
      }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledTimes(1)

    // Change dates
    const newStartDate = new Date('2024-03-01')
    const newEndDate = new Date('2024-03-31')

    rerender({ start: newStartDate, end: newEndDate })

    await waitFor(() => {
      expect(mockedApi.get).toHaveBeenCalledTimes(2)
    })

    expect(mockedApi.get).toHaveBeenLastCalledWith(
      '/api/assignments?start_date=2024-03-01&end_date=2024-03-31'
    )
  })
})

describe('useGenerateSchedule', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should generate schedule with correct parameters', async () => {
    const mockResponse = {
      status: 'success',
      message: 'Schedule generated successfully',
      total_blocks_assigned: 100,
      total_blocks: 100,
      validation: mockFactories.validation(),
      run_id: 'run-123',
    }
    mockedApi.post.mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(
      () => useGenerateSchedule(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate({
        start_date: '2024-02-01',
        end_date: '2024-02-28',
        algorithm: 'greedy',
      })
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.post).toHaveBeenCalledWith(
      '/schedule/generate',
      {
        start_date: '2024-02-01',
        end_date: '2024-02-28',
        algorithm: 'greedy',
      }
    )
    expect(result.current.data).toEqual(mockResponse)
  })

  it('should handle generation errors', async () => {
    const apiError = { message: 'Generation failed', status: 500 }
    mockedApi.post.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useGenerateSchedule(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate({
        start_date: '2024-02-01',
        end_date: '2024-02-28',
      })
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })
})

describe('useValidateSchedule', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should validate schedule for date range', async () => {
    const mockValidation = mockFactories.validation()
    mockedApi.get.mockResolvedValueOnce(mockValidation)

    const { result } = renderHook(
      () => useValidateSchedule('2024-02-01', '2024-02-28'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith(
      '/schedule/validate?start_date=2024-02-01&end_date=2024-02-28'
    )
    expect(result.current.data).toEqual(mockValidation)
  })

  it('should return violations when schedule is invalid', async () => {
    const mockValidation = mockFactories.validation({
      valid: false,
      total_violations: 2,
      violations: [
        {
          type: 'DUTY_HOUR_VIOLATION',
          severity: 'CRITICAL',
          person_id: 'person-1',
          person_name: 'Dr. Smith',
          message: 'Exceeded 80-hour weekly limit',
        },
      ],
    })
    mockedApi.get.mockResolvedValueOnce(mockValidation)

    const { result } = renderHook(
      () => useValidateSchedule('2024-02-01', '2024-02-28'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.valid).toBe(false)
    expect(result.current.data?.violations).toHaveLength(1)
  })
})
