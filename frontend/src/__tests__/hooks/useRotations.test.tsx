/**
 * useRotations Hook Tests
 *
 * Tests for the useRotationTemplates, useRotationTemplate, useCreateTemplate,
 * useUpdateTemplate, and useDeleteTemplate hooks using jest.mock() for API mocking.
 */
import { renderHook, waitFor } from '@/test-utils'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactNode } from 'react'
import {
  useRotationTemplates,
  useRotationTemplate,
  useCreateTemplate,
  useUpdateTemplate,
  useDeleteTemplate,
} from '@/lib/hooks'
import * as api from '@/lib/api'

// Mock the api module
jest.mock('@/lib/api')

const mockedApi = api as jest.Mocked<typeof api>

// Mock data for rotation templates
const mockRotationTemplates = [
  {
    id: 'template-1',
    name: 'Cardiology Clinic',
    activityType: 'clinic',
    abbreviation: 'CARD',
    clinicLocation: 'Building A, Floor 2',
    maxResidents: 4,
    requiresSpecialty: 'Cardiology',
    requiresProcedureCredential: true,
    supervisionRequired: true,
    maxSupervisionRatio: 2,
    createdAt: '2024-01-01T00:00:00Z',
  },
  {
    id: 'template-2',
    name: 'Emergency Department',
    activityType: 'emergency',
    abbreviation: 'ED',
    clinicLocation: 'Emergency Wing',
    maxResidents: 6,
    requiresSpecialty: null,
    requiresProcedureCredential: false,
    supervisionRequired: true,
    maxSupervisionRatio: 3,
    createdAt: '2024-01-02T00:00:00Z',
  },
  {
    id: 'template-3',
    name: 'Internal Medicine Ward',
    activityType: 'inpatient',
    abbreviation: 'IM',
    clinicLocation: null,
    maxResidents: 8,
    requiresSpecialty: 'Internal Medicine',
    requiresProcedureCredential: false,
    supervisionRequired: true,
    maxSupervisionRatio: 4,
    createdAt: '2024-01-03T00:00:00Z',
  },
]

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

describe('useRotationTemplates', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch rotation templates successfully', async () => {
    mockedApi.get.mockResolvedValueOnce({
      items: mockRotationTemplates,
      total: mockRotationTemplates.length,
    })

    const { result } = renderHook(() => useRotationTemplates(), {
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
    expect(result.current.data?.items).toHaveLength(mockRotationTemplates.length)
    expect(result.current.data?.total).toBe(mockRotationTemplates.length)
    expect(result.current.data?.items[0].name).toBe('Cardiology Clinic')
    expect(mockedApi.get).toHaveBeenCalledWith('/rotation-templates')
  })

  it('should show loading state while fetching', async () => {
    mockedApi.get.mockResolvedValueOnce({
      items: mockRotationTemplates,
      total: mockRotationTemplates.length,
    })

    const { result } = renderHook(() => useRotationTemplates(), {
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

  it('should return templates with correct structure', async () => {
    mockedApi.get.mockResolvedValueOnce({
      items: mockRotationTemplates,
      total: mockRotationTemplates.length,
    })

    const { result } = renderHook(() => useRotationTemplates(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    const firstTemplate = result.current.data?.items[0]
    expect(firstTemplate).toMatchObject({
      id: expect.any(String),
      name: expect.any(String),
      activityType: expect.any(String),
      supervisionRequired: expect.any(Boolean),
      maxSupervisionRatio: expect.any(Number),
    })
  })

  it('should handle API errors gracefully', async () => {
    const apiError = { message: 'Network error', status: 500 }
    mockedApi.get.mockRejectedValueOnce(apiError)

    const { result } = renderHook(() => useRotationTemplates(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })

  it('should handle empty template list', async () => {
    mockedApi.get.mockResolvedValueOnce({
      items: [],
      total: 0,
    })

    const { result } = renderHook(() => useRotationTemplates(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.items).toHaveLength(0)
    expect(result.current.data?.total).toBe(0)
  })
})

describe('useRotationTemplate', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch a single rotation template by ID', async () => {
    mockedApi.get.mockResolvedValueOnce(mockRotationTemplates[0])

    const { result } = renderHook(() => useRotationTemplate('template-1'), {
      wrapper: createWrapper(),
    })

    // Initially loading
    expect(result.current.isLoading).toBe(true)

    // Wait for data to load
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    // Check data
    expect(result.current.data?.id).toBe('template-1')
    expect(result.current.data?.name).toBe('Cardiology Clinic')
    expect(result.current.data?.abbreviation).toBe('CARD')
    expect(mockedApi.get).toHaveBeenCalledWith('/rotation-templates/template-1')
  })

  it('should handle not found error', async () => {
    const apiError = { message: 'Rotation template not found', status: 404 }
    mockedApi.get.mockRejectedValueOnce(apiError)

    const { result } = renderHook(() => useRotationTemplate('nonexistent'), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error?.message).toContain('not found')
  })
})

describe('useCreateTemplate', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should create a new rotation template successfully', async () => {
    const newTemplate = {
      id: 'template-new',
      name: 'Surgery Rotation',
      activityType: 'surgical',
      abbreviation: 'SURG',
      clinicLocation: null,
      maxResidents: 5,
      requiresSpecialty: 'Surgery',
      requiresProcedureCredential: true,
      supervisionRequired: true,
      maxSupervisionRatio: 2,
      createdAt: '2024-01-04T00:00:00Z',
    }

    mockedApi.post.mockResolvedValueOnce(newTemplate)

    const { result } = renderHook(() => useCreateTemplate(), {
      wrapper: createWrapper(),
    })

    // Execute mutation
    result.current.mutate({
      name: 'Surgery Rotation',
      activityType: 'surgical',
      abbreviation: 'SURG',
      maxResidents: 5,
      requiresSpecialty: 'Surgery',
      requiresProcedureCredential: true,
      supervisionRequired: true,
      maxSupervisionRatio: 2,
    })

    // Wait for mutation to complete
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    // Check response
    expect(result.current.data?.name).toBe('Surgery Rotation')
    expect(result.current.data?.abbreviation).toBe('SURG')
    expect(result.current.data?.id).toBeDefined()
    expect(mockedApi.post).toHaveBeenCalledWith('/rotation-templates', expect.objectContaining({
      name: 'Surgery Rotation',
      activityType: 'surgical',
    }))
  })

  it('should handle validation errors', async () => {
    const apiError = { message: 'Name is required', status: 400 }
    mockedApi.post.mockRejectedValueOnce(apiError)

    const { result } = renderHook(() => useCreateTemplate(), {
      wrapper: createWrapper(),
    })

    // Execute mutation without required fields
    result.current.mutate({
      name: '',
      activityType: 'clinic',
    })

    // Wait for error
    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error?.message).toBe('Name is required')
  })

  it('should support optional fields', async () => {
    const minimalTemplate = {
      id: 'template-minimal',
      name: 'Minimal Rotation',
      activityType: 'other',
      abbreviation: null,
      clinicLocation: null,
      maxResidents: null,
      requiresSpecialty: null,
      requiresProcedureCredential: false,
      supervisionRequired: false,
      maxSupervisionRatio: 0,
      createdAt: '2024-01-04T00:00:00Z',
    }

    mockedApi.post.mockResolvedValueOnce(minimalTemplate)

    const { result } = renderHook(() => useCreateTemplate(), {
      wrapper: createWrapper(),
    })

    result.current.mutate({
      name: 'Minimal Rotation',
      activityType: 'other',
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.name).toBe('Minimal Rotation')
  })
})

describe('useUpdateTemplate', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should update an existing rotation template', async () => {
    const updatedTemplate = {
      ...mockRotationTemplates[0],
      name: 'Advanced Cardiology Clinic',
      maxResidents: 6,
    }

    mockedApi.put.mockResolvedValueOnce(updatedTemplate)

    const { result } = renderHook(() => useUpdateTemplate(), {
      wrapper: createWrapper(),
    })

    // Execute mutation
    result.current.mutate({
      id: 'template-1',
      data: {
        name: 'Advanced Cardiology Clinic',
        maxResidents: 6,
      },
    })

    // Wait for mutation to complete
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    // Check response
    expect(result.current.data?.name).toBe('Advanced Cardiology Clinic')
    expect(result.current.data?.maxResidents).toBe(6)
    expect(mockedApi.put).toHaveBeenCalledWith('/rotation-templates/template-1', expect.objectContaining({
      name: 'Advanced Cardiology Clinic',
      maxResidents: 6,
    }))
  })

  it('should handle update errors', async () => {
    const apiError = { message: 'Template not found', status: 404 }
    mockedApi.put.mockRejectedValueOnce(apiError)

    const { result } = renderHook(() => useUpdateTemplate(), {
      wrapper: createWrapper(),
    })

    result.current.mutate({
      id: 'nonexistent',
      data: { name: 'Updated Name' },
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error?.message).toContain('not found')
  })

  it('should support partial updates', async () => {
    const partialUpdate = {
      ...mockRotationTemplates[0],
      abbreviation: 'CARDIO',
    }

    mockedApi.put.mockResolvedValueOnce(partialUpdate)

    const { result } = renderHook(() => useUpdateTemplate(), {
      wrapper: createWrapper(),
    })

    result.current.mutate({
      id: 'template-1',
      data: {
        abbreviation: 'CARDIO',
      },
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.abbreviation).toBe('CARDIO')
  })
})

describe('useDeleteTemplate', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should delete a rotation template successfully', async () => {
    mockedApi.del.mockResolvedValueOnce(undefined)

    const { result } = renderHook(() => useDeleteTemplate(), {
      wrapper: createWrapper(),
    })

    // Execute mutation
    result.current.mutate('template-1')

    // Wait for mutation to complete
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.del).toHaveBeenCalledWith('/rotation-templates/template-1')
  })

  it('should handle delete errors', async () => {
    const apiError = { message: 'Cannot delete template in use', status: 409 }
    mockedApi.del.mockRejectedValueOnce(apiError)

    const { result } = renderHook(() => useDeleteTemplate(), {
      wrapper: createWrapper(),
    })

    result.current.mutate('template-1')

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error?.message).toContain('in use')
  })

  it('should handle not found error', async () => {
    const apiError = { message: 'Template not found', status: 404 }
    mockedApi.del.mockRejectedValueOnce(apiError)

    const { result } = renderHook(() => useDeleteTemplate(), {
      wrapper: createWrapper(),
    })

    result.current.mutate('nonexistent')

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error?.message).toContain('not found')
  })
})
