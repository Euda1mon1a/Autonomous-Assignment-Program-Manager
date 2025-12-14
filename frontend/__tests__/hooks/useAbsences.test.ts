/**
 * Tests for useAbsences, useCreateAbsence, useUpdateAbsence, useDeleteAbsence hooks
 * Tests absence fetching, filtering, and CRUD operations
 */
import { renderHook, waitFor, act } from '@testing-library/react'
import {
  useAbsences,
  useAbsence,
  useCreateAbsence,
  useUpdateAbsence,
  useDeleteAbsence,
} from '@/lib/hooks'
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

describe('useAbsences', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch all absences', async () => {
    mockedApi.get.mockResolvedValueOnce(mockResponses.listAbsences)

    const { result } = renderHook(
      () => useAbsences(),
      { wrapper: createWrapper() }
    )

    expect(result.current.isLoading).toBe(true)

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith('/api/absences')
    expect(result.current.data?.items).toHaveLength(1)
  })

  it('should filter by person ID', async () => {
    const personAbsences = {
      items: [mockFactories.absence({ person_id: 'person-1' })],
      total: 1,
    }
    mockedApi.get.mockResolvedValueOnce(personAbsences)

    const { result } = renderHook(
      () => useAbsences(1),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith('/api/absences?person_id=1')
    expect(result.current.data).toEqual(personAbsences)
  })

  it('should handle API errors', async () => {
    const apiError = { message: 'Server error', status: 500 }
    mockedApi.get.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useAbsences(),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })

  it('should refetch when person ID changes', async () => {
    mockedApi.get.mockResolvedValue(mockResponses.listAbsences)

    const { result, rerender } = renderHook(
      ({ personId }) => useAbsences(personId),
      {
        wrapper: createWrapper(),
        initialProps: { personId: undefined as number | undefined },
      }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledTimes(1)
    expect(mockedApi.get).toHaveBeenCalledWith('/api/absences')

    // Change person ID
    rerender({ personId: 123 })

    await waitFor(() => {
      expect(mockedApi.get).toHaveBeenCalledTimes(2)
    })

    expect(mockedApi.get).toHaveBeenLastCalledWith('/api/absences?person_id=123')
  })
})

describe('useAbsence', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch a single absence by ID', async () => {
    const mockAbsence = mockFactories.absence()
    mockedApi.get.mockResolvedValueOnce(mockAbsence)

    const { result } = renderHook(
      () => useAbsence('absence-1'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith('/absences/absence-1')
    expect(result.current.data).toEqual(mockAbsence)
  })

  it('should not fetch when ID is empty', async () => {
    const { result } = renderHook(
      () => useAbsence(''),
      { wrapper: createWrapper() }
    )

    // Query should not be enabled
    expect(mockedApi.get).not.toHaveBeenCalled()
    expect(result.current.isFetching).toBe(false)
  })
})

describe('useCreateAbsence', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should create a new absence', async () => {
    const newAbsence = mockFactories.absence()
    mockedApi.post.mockResolvedValueOnce(newAbsence)

    const { result } = renderHook(
      () => useCreateAbsence(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate({
        person_id: 'person-1',
        start_date: '2024-02-01',
        end_date: '2024-02-07',
        absence_type: 'vacation',
      })
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.post).toHaveBeenCalledWith('/absences', {
      person_id: 'person-1',
      start_date: '2024-02-01',
      end_date: '2024-02-07',
      absence_type: 'vacation',
    })
    expect(result.current.data).toEqual(newAbsence)
  })

  it('should create deployment absence with orders', async () => {
    const deploymentAbsence = mockFactories.absence({
      absence_type: 'deployment',
      deployment_orders: true,
    })
    mockedApi.post.mockResolvedValueOnce(deploymentAbsence)

    const { result } = renderHook(
      () => useCreateAbsence(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate({
        person_id: 'person-1',
        start_date: '2024-03-01',
        end_date: '2024-06-30',
        absence_type: 'deployment',
        deployment_orders: true,
        notes: 'Military deployment',
      })
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.post).toHaveBeenCalledWith('/absences', expect.objectContaining({
      absence_type: 'deployment',
      deployment_orders: true,
    }))
  })

  it('should handle validation errors', async () => {
    const apiError = { message: 'End date must be after start date', status: 400 }
    mockedApi.post.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useCreateAbsence(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate({
        person_id: 'person-1',
        start_date: '2024-02-07',
        end_date: '2024-02-01',
        absence_type: 'vacation',
      })
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })
})

describe('useUpdateAbsence', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should update an existing absence', async () => {
    const updatedAbsence = mockFactories.absence({ end_date: '2024-02-14' })
    mockedApi.put.mockResolvedValueOnce(updatedAbsence)

    const { result } = renderHook(
      () => useUpdateAbsence(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate({
        id: 'absence-1',
        data: { end_date: '2024-02-14' },
      })
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.put).toHaveBeenCalledWith('/absences/absence-1', { end_date: '2024-02-14' })
    expect(result.current.data).toEqual(updatedAbsence)
  })

  it('should update absence type', async () => {
    const updatedAbsence = mockFactories.absence({
      absence_type: 'tdy',
      tdy_location: 'San Antonio',
    })
    mockedApi.put.mockResolvedValueOnce(updatedAbsence)

    const { result } = renderHook(
      () => useUpdateAbsence(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate({
        id: 'absence-1',
        data: {
          absence_type: 'tdy',
          tdy_location: 'San Antonio',
        },
      })
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.absence_type).toBe('tdy')
  })

  it('should handle not found errors', async () => {
    const apiError = { message: 'Absence not found', status: 404 }
    mockedApi.put.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useUpdateAbsence(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate({
        id: 'non-existent',
        data: { end_date: '2024-02-14' },
      })
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })
})

describe('useDeleteAbsence', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should delete an absence', async () => {
    mockedApi.del.mockResolvedValueOnce(undefined)

    const { result } = renderHook(
      () => useDeleteAbsence(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate('absence-1')
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.del).toHaveBeenCalledWith('/absences/absence-1')
  })

  it('should handle not found errors', async () => {
    const apiError = { message: 'Absence not found', status: 404 }
    mockedApi.del.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useDeleteAbsence(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate('non-existent')
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })
})
