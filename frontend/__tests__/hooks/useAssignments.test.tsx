/**
 * Tests for useAssignments, useCreateAssignment, useUpdateAssignment, useDeleteAssignment hooks
 * Tests assignment fetching, filtering, and CRUD operations
 */
import { renderHook, waitFor, act } from '@/test-utils'
import {
  useAssignments,
  useCreateAssignment,
  useUpdateAssignment,
  useDeleteAssignment,
  useEmergencyCoverage,
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

describe('useAssignments', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch all assignments', async () => {
    mockedApi.get.mockResolvedValueOnce(mockResponses.listAssignments)

    const { result } = renderHook(
      () => useAssignments(),
      { wrapper: createWrapper() }
    )

    expect(result.current.isLoading).toBe(true)

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith('/assignments')
    expect(result.current.data?.items).toHaveLength(1)
  })

  it('should filter by date range', async () => {
    mockedApi.get.mockResolvedValueOnce(mockResponses.listAssignments)

    const { result } = renderHook(
      () => useAssignments({ start_date: '2024-02-01', end_date: '2024-02-28' }),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith('/assignments?start_date=2024-02-01&end_date=2024-02-28')
  })

  it('should filter by person ID', async () => {
    mockedApi.get.mockResolvedValueOnce(mockResponses.listAssignments)

    const { result } = renderHook(
      () => useAssignments({ person_id: 'person-1' }),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith('/assignments?person_id=person-1')
  })

  it('should filter by role', async () => {
    mockedApi.get.mockResolvedValueOnce(mockResponses.listAssignments)

    const { result } = renderHook(
      () => useAssignments({ role: 'supervising' }),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith('/assignments?role=supervising')
  })

  it('should handle API errors', async () => {
    const apiError = { message: 'Server error', status: 500 }
    mockedApi.get.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useAssignments(),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })
})

describe('useCreateAssignment', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should create a new assignment', async () => {
    const newAssignment = mockFactories.assignment()
    mockedApi.post.mockResolvedValueOnce(newAssignment)

    const { result } = renderHook(
      () => useCreateAssignment(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate({
        block_id: 'block-1',
        person_id: 'person-1',
        role: 'primary',
        rotation_template_id: 'template-1',
      })
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.post).toHaveBeenCalledWith('/assignments', {
      block_id: 'block-1',
      person_id: 'person-1',
      role: 'primary',
      rotation_template_id: 'template-1',
    })
    expect(result.current.data).toEqual(newAssignment)
  })

  it('should create assignment with activity override', async () => {
    const overrideAssignment = mockFactories.assignment({
      activity_override: 'Special Coverage',
    })
    mockedApi.post.mockResolvedValueOnce(overrideAssignment)

    const { result } = renderHook(
      () => useCreateAssignment(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate({
        block_id: 'block-1',
        person_id: 'person-1',
        role: 'backup',
        activity_override: 'Special Coverage',
        notes: 'Emergency backup for Dr. Smith',
      })
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.post).toHaveBeenCalledWith('/assignments', expect.objectContaining({
      activity_override: 'Special Coverage',
    }))
  })

  it('should handle duplicate assignment errors', async () => {
    const apiError = { message: 'Person already assigned to this block', status: 400 }
    mockedApi.post.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useCreateAssignment(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate({
        block_id: 'block-1',
        person_id: 'person-1',
        role: 'primary',
      })
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })
})

describe('useUpdateAssignment', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should update an existing assignment', async () => {
    const updatedAssignment = mockFactories.assignment({ role: 'supervising' })
    mockedApi.put.mockResolvedValueOnce(updatedAssignment)

    const { result } = renderHook(
      () => useUpdateAssignment(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate({
        id: 'assignment-1',
        data: { role: 'supervising' },
      })
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.put).toHaveBeenCalledWith('/assignments/assignment-1', { role: 'supervising' })
    expect(result.current.data?.role).toBe('supervising')
  })

  it('should update assignment notes', async () => {
    const updatedAssignment = mockFactories.assignment({ notes: 'Updated notes' })
    mockedApi.put.mockResolvedValueOnce(updatedAssignment)

    const { result } = renderHook(
      () => useUpdateAssignment(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate({
        id: 'assignment-1',
        data: { notes: 'Updated notes' },
      })
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.notes).toBe('Updated notes')
  })

  it('should handle not found errors', async () => {
    const apiError = { message: 'Assignment not found', status: 404 }
    mockedApi.put.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useUpdateAssignment(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate({
        id: 'non-existent',
        data: { role: 'backup' },
      })
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })
})

describe('useDeleteAssignment', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should delete an assignment', async () => {
    mockedApi.del.mockResolvedValueOnce(undefined)

    const { result } = renderHook(
      () => useDeleteAssignment(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate('assignment-1')
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.del).toHaveBeenCalledWith('/assignments/assignment-1')
  })

  it('should handle not found errors', async () => {
    const apiError = { message: 'Assignment not found', status: 404 }
    mockedApi.del.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useDeleteAssignment(),
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

describe('useEmergencyCoverage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should handle emergency coverage request', async () => {
    const mockResponse = {
      status: 'success',
      replacements_found: 5,
      coverage_gaps: 0,
      requires_manual_review: false,
      details: [
        {
          date: '2024-02-01',
          original_assignment: 'Inpatient Medicine',
          replacement: 'Dr. Jane Doe',
          status: 'covered',
        },
      ],
    }
    mockedApi.post.mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(
      () => useEmergencyCoverage(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate({
        person_id: 'person-1',
        start_date: '2024-02-01',
        end_date: '2024-02-07',
        reason: 'Family emergency',
      })
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.post).toHaveBeenCalledWith('/schedule/emergency-coverage', {
      person_id: 'person-1',
      start_date: '2024-02-01',
      end_date: '2024-02-07',
      reason: 'Family emergency',
    })
    expect(result.current.data?.status).toBe('success')
    expect(result.current.data?.replacements_found).toBe(5)
  })

  it('should handle deployment emergency', async () => {
    const mockResponse = {
      status: 'partial',
      replacements_found: 8,
      coverage_gaps: 2,
      requires_manual_review: true,
      details: [],
    }
    mockedApi.post.mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(
      () => useEmergencyCoverage(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate({
        person_id: 'person-1',
        start_date: '2024-03-01',
        end_date: '2024-06-30',
        reason: 'Military deployment',
        is_deployment: true,
      })
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.post).toHaveBeenCalledWith('/schedule/emergency-coverage', expect.objectContaining({
      is_deployment: true,
    }))
    expect(result.current.data?.requires_manual_review).toBe(true)
  })

  it('should handle coverage failure', async () => {
    const apiError = { message: 'Unable to find coverage', status: 500 }
    mockedApi.post.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useEmergencyCoverage(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate({
        person_id: 'person-1',
        start_date: '2024-02-01',
        end_date: '2024-02-07',
        reason: 'Medical leave',
      })
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })
})
