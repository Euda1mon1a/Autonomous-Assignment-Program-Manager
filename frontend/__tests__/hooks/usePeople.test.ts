/**
 * Tests for usePeople, useCreatePerson, useUpdatePerson, useDeletePerson hooks
 * Tests people fetching, filtering, and CRUD operations
 */
import { renderHook, waitFor, act } from '@testing-library/react'
import {
  usePeople,
  usePerson,
  useResidents,
  useFaculty,
  useCreatePerson,
  useUpdatePerson,
  useDeletePerson,
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

describe('usePeople', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch all people', async () => {
    mockedApi.get.mockResolvedValueOnce(mockResponses.listPeople)

    const { result } = renderHook(
      () => usePeople(),
      { wrapper: createWrapper() }
    )

    expect(result.current.isLoading).toBe(true)

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith('/api/people')
    expect(result.current.data?.items).toHaveLength(2)
  })

  it('should filter by role', async () => {
    mockedApi.get.mockResolvedValueOnce({
      items: [mockFactories.person({ type: 'resident' })],
      total: 1,
    })

    const { result } = renderHook(
      () => usePeople({ role: 'resident' }),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith('/api/people?role=resident')
  })

  it('should filter by PGY level', async () => {
    mockedApi.get.mockResolvedValueOnce({
      items: [mockFactories.person({ pgy_level: 2 })],
      total: 1,
    })

    const { result } = renderHook(
      () => usePeople({ pgy_level: 2 }),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith('/api/people?pgy_level=2')
  })

  it('should handle API errors', async () => {
    const apiError = { message: 'Network error', status: 0 }
    mockedApi.get.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => usePeople(),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })

  it('should refetch when filter changes', async () => {
    mockedApi.get.mockResolvedValue(mockResponses.listPeople)

    const { result, rerender } = renderHook(
      ({ filters }) => usePeople(filters),
      {
        wrapper: createWrapper(),
        initialProps: { filters: undefined as { role?: string } | undefined },
      }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    rerender({ filters: { role: 'faculty' } })

    await waitFor(() => {
      expect(mockedApi.get).toHaveBeenCalledTimes(2)
    })

    expect(mockedApi.get).toHaveBeenLastCalledWith('/api/people?role=faculty')
  })
})

describe('usePerson', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch a single person by ID', async () => {
    const mockPerson = mockFactories.person()
    mockedApi.get.mockResolvedValueOnce(mockPerson)

    const { result } = renderHook(
      () => usePerson('person-1'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith('/people/person-1')
    expect(result.current.data).toEqual(mockPerson)
  })

  it('should not fetch when ID is empty', async () => {
    const { result } = renderHook(
      () => usePerson(''),
      { wrapper: createWrapper() }
    )

    // Query should not be enabled
    expect(mockedApi.get).not.toHaveBeenCalled()
    expect(result.current.isFetching).toBe(false)
  })
})

describe('useResidents', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch all residents', async () => {
    mockedApi.get.mockResolvedValueOnce(mockResponses.listPeople)

    const { result } = renderHook(
      () => useResidents(),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith('/people/residents')
  })

  it('should filter by PGY level', async () => {
    mockedApi.get.mockResolvedValueOnce({
      items: [mockFactories.person({ pgy_level: 1 })],
      total: 1,
    })

    const { result } = renderHook(
      () => useResidents(1),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith('/people/residents?pgy_level=1')
  })
})

describe('useFaculty', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch all faculty', async () => {
    const facultyResponse = {
      items: [mockFactories.person({ type: 'faculty', pgy_level: null })],
      total: 1,
    }
    mockedApi.get.mockResolvedValueOnce(facultyResponse)

    const { result } = renderHook(
      () => useFaculty(),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith('/people/faculty')
  })

  it('should filter by specialty', async () => {
    mockedApi.get.mockResolvedValueOnce({
      items: [mockFactories.person({ type: 'faculty', specialties: ['Cardiology'] })],
      total: 1,
    })

    const { result } = renderHook(
      () => useFaculty('Cardiology'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith('/people/faculty?specialty=Cardiology')
  })
})

describe('useCreatePerson', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should create a new person', async () => {
    const newPerson = mockFactories.person()
    mockedApi.post.mockResolvedValueOnce(newPerson)

    const { result } = renderHook(
      () => useCreatePerson(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate({
        name: 'Dr. John Smith',
        type: 'resident',
        pgy_level: 2,
      })
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.post).toHaveBeenCalledWith('/people', {
      name: 'Dr. John Smith',
      type: 'resident',
      pgy_level: 2,
    })
    expect(result.current.data).toEqual(newPerson)
  })

  it('should handle validation errors', async () => {
    const apiError = { message: 'PGY level required for residents', status: 400 }
    mockedApi.post.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useCreatePerson(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate({
        name: 'Dr. John Smith',
        type: 'resident',
      })
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })
})

describe('useUpdatePerson', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should update an existing person', async () => {
    const updatedPerson = mockFactories.person({ name: 'Dr. Jane Smith' })
    mockedApi.put.mockResolvedValueOnce(updatedPerson)

    const { result } = renderHook(
      () => useUpdatePerson(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate({
        id: 'person-1',
        data: { name: 'Dr. Jane Smith' },
      })
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.put).toHaveBeenCalledWith('/people/person-1', { name: 'Dr. Jane Smith' })
    expect(result.current.data).toEqual(updatedPerson)
  })

  it('should handle not found errors', async () => {
    const apiError = { message: 'Person not found', status: 404 }
    mockedApi.put.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useUpdatePerson(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate({
        id: 'non-existent',
        data: { name: 'Dr. Nobody' },
      })
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })
})

describe('useDeletePerson', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should delete a person', async () => {
    mockedApi.del.mockResolvedValueOnce(undefined)

    const { result } = renderHook(
      () => useDeletePerson(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate('person-1')
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.del).toHaveBeenCalledWith('/people/person-1')
  })

  it('should handle not found errors', async () => {
    const apiError = { message: 'Person not found', status: 404 }
    mockedApi.del.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useDeletePerson(),
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
