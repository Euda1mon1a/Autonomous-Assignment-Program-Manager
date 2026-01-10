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
import { AssignmentRole } from '@/types/api'
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
      () => useAssignments({ startDate: '2024-02-01', endDate: '2024-02-28' }),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith('/assignments?startDate=2024-02-01&endDate=2024-02-28')
  })

  it('should filter by person ID', async () => {
    mockedApi.get.mockResolvedValueOnce(mockResponses.listAssignments)

    const { result } = renderHook(
      () => useAssignments({ personId: 'person-1' }),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith('/assignments?personId=person-1')
  })

  it('should filter by role', async () => {
    mockedApi.get.mockResolvedValueOnce(mockResponses.listAssignments)

    const { result } = renderHook(
      () => useAssignments({ role: AssignmentRole.SUPERVISING }),
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
        blockId: 'block-1',
        personId: 'person-1',
        role: AssignmentRole.PRIMARY,
        rotationTemplateId: 'template-1',
      })
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.post).toHaveBeenCalledWith('/assignments', {
      blockId: 'block-1',
      personId: 'person-1',
      role: AssignmentRole.PRIMARY,
      rotationTemplateId: 'template-1',
    })
    expect(result.current.data).toEqual(newAssignment)
  })

  it('should create assignment with activity override', async () => {
    const overrideAssignment = mockFactories.assignment({
      activityOverride: 'Special Coverage',
    })
    mockedApi.post.mockResolvedValueOnce(overrideAssignment)

    const { result } = renderHook(
      () => useCreateAssignment(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate({
        blockId: 'block-1',
        personId: 'person-1',
        role: AssignmentRole.BACKUP,
        activityOverride: 'Special Coverage',
        notes: 'Emergency backup for Dr. Smith',
      })
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.post).toHaveBeenCalledWith('/assignments', expect.objectContaining({
      activityOverride: 'Special Coverage',
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
        blockId: 'block-1',
        personId: 'person-1',
        role: AssignmentRole.PRIMARY,
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
    const updatedAssignment = mockFactories.assignment({ role: AssignmentRole.SUPERVISING })
    mockedApi.put.mockResolvedValueOnce(updatedAssignment)

    const { result } = renderHook(
      () => useUpdateAssignment(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate({
        id: 'assignment-1',
        data: { role: AssignmentRole.SUPERVISING },
      })
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.put).toHaveBeenCalledWith('/assignments/assignment-1', { role: AssignmentRole.SUPERVISING })
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
        data: { role: AssignmentRole.BACKUP },
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
      replacementsFound: 5,
      coverageGaps: 0,
      requiresManualReview: false,
      details: [
        {
          date: '2024-02-01',
          originalAssignment: 'Inpatient Medicine',
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
        personId: 'person-1',
        startDate: '2024-02-01',
        endDate: '2024-02-07',
        reason: 'Family emergency',
        isDeployment: false,
      })
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.post).toHaveBeenCalledWith('/schedule/emergency-coverage', {
      personId: 'person-1',
      startDate: '2024-02-01',
      endDate: '2024-02-07',
      reason: 'Family emergency',
      isDeployment: false,
    })
    expect(result.current.data?.status).toBe('success')
    expect(result.current.data?.replacementsFound).toBe(5)
  })

  it('should handle deployment emergency', async () => {
    const mockResponse = {
      status: 'partial',
      replacementsFound: 8,
      coverageGaps: 2,
      requiresManualReview: true,
      details: [],
    }
    mockedApi.post.mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(
      () => useEmergencyCoverage(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate({
        personId: 'person-1',
        startDate: '2024-03-01',
        endDate: '2024-06-30',
        reason: 'Military deployment',
        isDeployment: true,
      })
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.post).toHaveBeenCalledWith('/schedule/emergency-coverage', expect.objectContaining({
      isDeployment: true,
    }))
    expect(result.current.data?.requiresManualReview).toBe(true)
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
        personId: 'person-1',
        startDate: '2024-02-01',
        endDate: '2024-02-07',
        reason: 'Medical leave',
        isDeployment: false,
      })
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })
})
