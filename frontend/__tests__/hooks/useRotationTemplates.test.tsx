/**
 * Tests for useRotationTemplates, useCreateTemplate, useUpdateTemplate, useDeleteTemplate hooks
 * Tests rotation template fetching and CRUD operations
 */
import { renderHook, waitFor, act } from '@testing-library/react'
import {
  useRotationTemplates,
  useRotationTemplate,
  useCreateTemplate,
  useUpdateTemplate,
  useDeleteTemplate,
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

describe('useRotationTemplates', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch all rotation templates', async () => {
    mockedApi.get.mockResolvedValueOnce(mockResponses.listTemplates)

    const { result } = renderHook(
      () => useRotationTemplates(),
      { wrapper: createWrapper() }
    )

    expect(result.current.isLoading).toBe(true)

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith('/rotation-templates')
    expect(result.current.data?.items).toHaveLength(2)
  })

  it('should have long stale time for infrequently changed data', async () => {
    mockedApi.get.mockResolvedValueOnce(mockResponses.listTemplates)

    const { result } = renderHook(
      () => useRotationTemplates(),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    // Verify the data is cached (only one call)
    expect(mockedApi.get).toHaveBeenCalledTimes(1)
  })

  it('should handle API errors', async () => {
    const apiError = { message: 'Server error', status: 500 }
    mockedApi.get.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useRotationTemplates(),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })
})

describe('useRotationTemplate', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch a single rotation template by ID', async () => {
    const mockTemplate = mockFactories.rotationTemplate()
    mockedApi.get.mockResolvedValueOnce(mockTemplate)

    const { result } = renderHook(
      () => useRotationTemplate('template-1'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith('/rotation-templates/template-1')
    expect(result.current.data).toEqual(mockTemplate)
  })

  it('should not fetch when ID is empty', async () => {
    const { result } = renderHook(
      () => useRotationTemplate(''),
      { wrapper: createWrapper() }
    )

    // Query should not be enabled
    expect(mockedApi.get).not.toHaveBeenCalled()
    expect(result.current.isFetching).toBe(false)
  })
})

describe('useCreateTemplate', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should create a new rotation template', async () => {
    const newTemplate = mockFactories.rotationTemplate()
    mockedApi.post.mockResolvedValueOnce(newTemplate)

    const { result } = renderHook(
      () => useCreateTemplate(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate({
        name: 'Inpatient Medicine',
        activity_type: 'inpatient',
        abbreviation: 'IM',
        supervision_required: true,
        max_supervision_ratio: 4,
      })
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.post).toHaveBeenCalledWith('/rotation-templates', {
      name: 'Inpatient Medicine',
      activity_type: 'inpatient',
      abbreviation: 'IM',
      supervision_required: true,
      max_supervision_ratio: 4,
    })
    expect(result.current.data).toEqual(newTemplate)
  })

  it('should create template requiring procedure credential', async () => {
    const procedureTemplate = mockFactories.rotationTemplate({
      name: 'Interventional Cardiology',
      requires_procedure_credential: true,
    })
    mockedApi.post.mockResolvedValueOnce(procedureTemplate)

    const { result } = renderHook(
      () => useCreateTemplate(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate({
        name: 'Interventional Cardiology',
        activity_type: 'procedure',
        requires_procedure_credential: true,
      })
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.post).toHaveBeenCalledWith('/rotation-templates', expect.objectContaining({
      requires_procedure_credential: true,
    }))
  })

  it('should handle validation errors', async () => {
    const apiError = { message: 'Template name already exists', status: 409 }
    mockedApi.post.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useCreateTemplate(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate({
        name: 'Duplicate Template',
        activity_type: 'inpatient',
      })
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })
})

describe('useUpdateTemplate', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should update an existing rotation template', async () => {
    const updatedTemplate = mockFactories.rotationTemplate({ name: 'Updated Name' })
    mockedApi.put.mockResolvedValueOnce(updatedTemplate)

    const { result } = renderHook(
      () => useUpdateTemplate(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate({
        id: 'template-1',
        data: { name: 'Updated Name' },
      })
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.put).toHaveBeenCalledWith('/rotation-templates/template-1', { name: 'Updated Name' })
    expect(result.current.data).toEqual(updatedTemplate)
  })

  it('should update supervision ratio', async () => {
    const updatedTemplate = mockFactories.rotationTemplate({ max_supervision_ratio: 2 })
    mockedApi.put.mockResolvedValueOnce(updatedTemplate)

    const { result } = renderHook(
      () => useUpdateTemplate(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate({
        id: 'template-1',
        data: { max_supervision_ratio: 2 },
      })
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.max_supervision_ratio).toBe(2)
  })

  it('should handle not found errors', async () => {
    const apiError = { message: 'Rotation template not found', status: 404 }
    mockedApi.put.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useUpdateTemplate(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate({
        id: 'non-existent',
        data: { name: 'New Name' },
      })
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })
})

describe('useDeleteTemplate', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should delete a rotation template', async () => {
    mockedApi.del.mockResolvedValueOnce(undefined)

    const { result } = renderHook(
      () => useDeleteTemplate(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate('template-1')
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.del).toHaveBeenCalledWith('/rotation-templates/template-1')
  })

  it('should handle not found errors', async () => {
    const apiError = { message: 'Rotation template not found', status: 404 }
    mockedApi.del.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useDeleteTemplate(),
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

  it('should handle conflict errors when template is in use', async () => {
    const apiError = { message: 'Cannot delete template that is in use', status: 409 }
    mockedApi.del.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useDeleteTemplate(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate('template-in-use')
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })
})
