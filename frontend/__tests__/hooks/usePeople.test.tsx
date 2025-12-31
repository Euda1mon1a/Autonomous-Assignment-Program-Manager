/**
 * Tests for usePeople, useCreatePerson, useUpdatePerson, useDeletePerson hooks
 * Tests people fetching, filtering, and CRUD operations
 */
import { renderHook, waitFor, act } from '@/test-utils'
import {
  usePeople,
  usePerson,
  useResidents,
  useFaculty,
  useCreatePerson,
  useUpdatePerson,
  useDeletePerson,
  useCertifications,
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

    expect(mockedApi.get).toHaveBeenCalledWith('/people')
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

    expect(mockedApi.get).toHaveBeenCalledWith('/people?role=resident')
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

    expect(mockedApi.get).toHaveBeenCalledWith('/people?pgy_level=2')
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

    expect(mockedApi.get).toHaveBeenLastCalledWith('/people?role=faculty')
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

  it('should handle conflict errors when person has assignments', async () => {
    const apiError = {
      message: 'Cannot delete person with existing assignments',
      status: 409
    }
    mockedApi.del.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useDeletePerson(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate('person-with-assignments')
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error?.status).toBe(409)
  })
})

describe('useCertifications', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  const mockCertification = {
    id: 'cert-1',
    person_id: 'person-1',
    certification_type_id: 'type-1',
    certification_number: 'BLS-12345',
    issued_date: '2024-01-01',
    expiration_date: '2026-01-01',
    status: 'current' as const,
    days_until_expiration: 730,
    is_expired: false,
    is_expiring_soon: false,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    certification_type: {
      id: 'type-1',
      name: 'BLS',
      full_name: 'Basic Life Support',
    },
  }

  const mockExpiringSoonCertification = {
    ...mockCertification,
    id: 'cert-2',
    expiration_date: '2024-03-01',
    status: 'expiring_soon' as const,
    days_until_expiration: 45,
    is_expiring_soon: true,
  }

  const mockExpiredCertification = {
    ...mockCertification,
    id: 'cert-3',
    expiration_date: '2023-12-31',
    status: 'expired' as const,
    days_until_expiration: -30,
    is_expired: true,
  }

  it('should fetch certifications for a person', async () => {
    const mockResponse = {
      items: [mockCertification],
      total: 1,
    }
    mockedApi.get.mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(
      () => useCertifications('person-1'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith('/certifications/by-person/person-1')
    expect(result.current.data?.items).toHaveLength(1)
    expect(result.current.data?.items[0]).toEqual(mockCertification)
  })

  it('should not fetch when person ID is empty', async () => {
    const { result } = renderHook(
      () => useCertifications(''),
      { wrapper: createWrapper() }
    )

    expect(mockedApi.get).not.toHaveBeenCalled()
    expect(result.current.isFetching).toBe(false)
  })

  it('should handle empty certification list', async () => {
    const mockResponse = {
      items: [],
      total: 0,
    }
    mockedApi.get.mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(
      () => useCertifications('person-1'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.items).toHaveLength(0)
    expect(result.current.data?.total).toBe(0)
  })

  it('should handle API errors gracefully', async () => {
    const apiError = { message: 'Person not found', status: 404 }
    mockedApi.get.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useCertifications('non-existent'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })

  it('should distinguish between current, expiring, and expired certifications', async () => {
    const mockResponse = {
      items: [
        mockCertification,
        mockExpiringSoonCertification,
        mockExpiredCertification,
      ],
      total: 3,
    }
    mockedApi.get.mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(
      () => useCertifications('person-1'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    const certs = result.current.data?.items || []
    const current = certs.filter(c => c.status === 'current')
    const expiring = certs.filter(c => c.is_expiring_soon)
    const expired = certs.filter(c => c.is_expired)

    expect(current).toHaveLength(1)
    expect(expiring).toHaveLength(1)
    expect(expired).toHaveLength(1)
  })
})

describe('usePeople - Additional Edge Cases', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should handle empty results', async () => {
    mockedApi.get.mockResolvedValueOnce({ items: [], total: 0 })

    const { result } = renderHook(
      () => usePeople(),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.items).toHaveLength(0)
    expect(result.current.data?.total).toBe(0)
  })

  it('should handle multiple filters simultaneously', async () => {
    mockedApi.get.mockResolvedValueOnce({
      items: [mockFactories.person({ type: 'resident', pgy_level: 2 })],
      total: 1,
    })

    const { result } = renderHook(
      () => usePeople({ role: 'resident', pgy_level: 2 }),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith('/people?role=resident&pgy_level=2')
  })

  it('should handle network errors', async () => {
    const networkError = { message: 'Network error - unable to reach server', status: 0 }
    mockedApi.get.mockRejectedValueOnce(networkError)

    const { result } = renderHook(
      () => usePeople(),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error?.status).toBe(0)
  })
})

describe('useCreatePerson - Additional Validation', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should create a faculty member without PGY level', async () => {
    const newFaculty = mockFactories.person({
      type: 'faculty',
      pgy_level: null,
      specialties: ['Cardiology'],
    })
    mockedApi.post.mockResolvedValueOnce(newFaculty)

    const { result } = renderHook(
      () => useCreatePerson(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate({
        name: 'Dr. Jane Faculty',
        type: 'faculty',
        specialties: ['Cardiology'],
        performs_procedures: true,
      })
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.type).toBe('faculty')
  })

  it('should handle duplicate email errors', async () => {
    const apiError = {
      message: 'Email already exists',
      status: 409,
      detail: 'A person with this email already exists',
    }
    mockedApi.post.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useCreatePerson(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate({
        name: 'Dr. Duplicate',
        type: 'resident',
        email: 'existing@example.com',
      })
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error?.status).toBe(409)
  })
})

describe('useUpdatePerson - PGY Level Advancement', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should advance resident to next PGY level', async () => {
    const advancedResident = mockFactories.person({ pgy_level: 3 })
    mockedApi.put.mockResolvedValueOnce(advancedResident)

    const { result } = renderHook(
      () => useUpdatePerson(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate({
        id: 'resident-1',
        data: { pgy_level: 3 },
      })
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.pgy_level).toBe(3)
  })

  it('should handle partial updates', async () => {
    const updatedPerson = mockFactories.person({ email: 'newemail@example.com' })
    mockedApi.put.mockResolvedValueOnce(updatedPerson)

    const { result } = renderHook(
      () => useUpdatePerson(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate({
        id: 'person-1',
        data: { email: 'newemail@example.com' },
      })
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.put).toHaveBeenCalledWith(
      '/people/person-1',
      { email: 'newemail@example.com' }
    )
  })
})

describe('useResidents - Filtering and Edge Cases', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should handle invalid PGY level gracefully', async () => {
    const apiError = { message: 'Invalid PGY level', status: 400 }
    mockedApi.get.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useResidents(99), // Invalid PGY level
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error?.status).toBe(400)
  })
})

describe('useFaculty - Specialty Filtering', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should properly encode specialty parameter', async () => {
    const specialtyWithSpaces = 'Sports Medicine'
    mockedApi.get.mockResolvedValueOnce({
      items: [mockFactories.person({ type: 'faculty', specialties: [specialtyWithSpaces] })],
      total: 1,
    })

    const { result } = renderHook(
      () => useFaculty(specialtyWithSpaces),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith('/people/faculty?specialty=Sports%20Medicine')
  })
})
