/**
 * useAdminTemplates Hook Tests
 *
 * Tests for admin rotation template management hooks including
 * CRUD operations, bulk actions, and preference management.
 */
import { renderHook, waitFor } from '@/test-utils'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactNode } from 'react'
import * as api from '@/lib/api'
import {
  useAdminTemplates,
  useAdminTemplate,
  useCreateTemplate,
  useUpdateTemplate,
  useDeleteTemplate,
  useBulkDeleteTemplates,
  useBulkUpdateTemplates,
  useTemplatePreferences,
  useReplaceTemplatePreferences,
  useTemplatesMap,
  useBulkCreateTemplates,
  useCheckConflicts,
  useExportTemplates,
  useArchiveTemplate,
  useRestoreTemplate,
  useBulkArchiveTemplates,
  useBulkRestoreTemplates,
  useInlineUpdateTemplate,
  adminTemplatesQueryKeys,
} from '@/hooks/useAdminTemplates'
import type {
  RotationTemplate,
  RotationTemplateListResponse,
  RotationPreference,
  BatchTemplateResponse,
  ConflictCheckResponse,
  TemplateExportResponse,
} from '@/types/admin-templates'

// Mock the api module
jest.mock('@/lib/api')

const mockedApi = api as jest.Mocked<typeof api>

// Mock data
const mockTemplate: RotationTemplate = {
  id: 'template-1',
  name: 'FM Clinic',
  description: 'Family medicine clinic rotation',
  activityType: 'fm_clinic',
  isActive: true,
  isArchived: false,
  createdAt: '2024-01-01T00:00:00Z',
  updatedAt: '2024-01-01T00:00:00Z',
}

const mockTemplateListResponse: RotationTemplateListResponse = {
  items: [mockTemplate],
  total: 1,
}

const mockPreference: RotationPreference = {
  id: 'pref-1',
  templateId: 'template-1',
  personId: 'person-1',
  preferenceLevel: 5,
  notes: 'Preferred rotation',
  createdAt: '2024-01-01T00:00:00Z',
  updatedAt: '2024-01-01T00:00:00Z',
}

const mockBatchResponse: BatchTemplateResponse = {
  success: true,
  successCount: 2,
  failCount: 0,
  results: [
    { templateId: 'template-1', success: true, message: 'Updated' },
    { templateId: 'template-2', success: true, message: 'Updated' },
  ],
}

const mockConflictResponse: ConflictCheckResponse = {
  hasConflicts: false,
  conflicts: [],
}

const mockExportResponse: TemplateExportResponse = {
  templates: [mockTemplate],
  exportDate: '2024-01-01T00:00:00Z',
  format: 'json',
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

describe('useAdminTemplates', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch all templates successfully', async () => {
    mockedApi.get.mockResolvedValueOnce(mockTemplateListResponse)

    const { result } = renderHook(
      () => useAdminTemplates(),
      { wrapper: createWrapper() }
    )

    expect(result.current.isLoading).toBe(true)

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockTemplateListResponse)
    expect(mockedApi.get).toHaveBeenCalledWith('/rotation-templates')
  })

  it('should filter templates by activity type', async () => {
    mockedApi.get.mockResolvedValueOnce(mockTemplateListResponse)

    const { result } = renderHook(
      () => useAdminTemplates('fm_clinic'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith('/rotation-templates?activity_type=fm_clinic')
  })

  it('should include archived templates when requested', async () => {
    mockedApi.get.mockResolvedValueOnce(mockTemplateListResponse)

    const { result } = renderHook(
      () => useAdminTemplates(undefined, { includeArchived: true }),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith('/rotation-templates?include_archived=true')
  })

  it('should handle API errors', async () => {
    const apiError = { message: 'Server error', status: 500 }
    mockedApi.get.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useAdminTemplates(),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })
})

describe('useAdminTemplate', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch single template successfully', async () => {
    mockedApi.get.mockResolvedValueOnce(mockTemplate)

    const { result } = renderHook(
      () => useAdminTemplate('template-1'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockTemplate)
    expect(mockedApi.get).toHaveBeenCalledWith('/rotation-templates/template-1')
  })

  it('should not fetch when templateId is empty', async () => {
    const { result } = renderHook(
      () => useAdminTemplate(''),
      { wrapper: createWrapper() }
    )

    expect(result.current.isPending).toBe(true)
    expect(mockedApi.get).not.toHaveBeenCalled()
  })
})

describe('useCreateTemplate', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should create template successfully', async () => {
    mockedApi.post.mockResolvedValueOnce(mockTemplate)

    const queryClient = createTestQueryClient()
    const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries')

    const { result } = renderHook(
      () => useCreateTemplate(),
      { wrapper: ({ children }) => (
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      )}
    )

    result.current.mutate({
      name: 'FM Clinic',
      description: 'Family medicine clinic rotation',
      activityType: 'fm_clinic',
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.post).toHaveBeenCalledWith(
      '/rotation-templates',
      {
        name: 'FM Clinic',
        description: 'Family medicine clinic rotation',
        activityType: 'fm_clinic',
      }
    )
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: adminTemplatesQueryKeys.all,
    })
  })
})

describe('useUpdateTemplate', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should update template successfully', async () => {
    mockedApi.put.mockResolvedValueOnce(mockTemplate)

    const queryClient = createTestQueryClient()
    const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries')

    const { result } = renderHook(
      () => useUpdateTemplate(),
      { wrapper: ({ children }) => (
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      )}
    )

    result.current.mutate({
      templateId: 'template-1',
      data: { name: 'Updated FM Clinic' },
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.put).toHaveBeenCalledWith(
      '/rotation-templates/template-1',
      { name: 'Updated FM Clinic' }
    )
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: adminTemplatesQueryKeys.all,
    })
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: adminTemplatesQueryKeys.detail('template-1'),
    })
  })
})

describe('useDeleteTemplate', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should delete template successfully', async () => {
    mockedApi.del.mockResolvedValueOnce(undefined)

    const queryClient = createTestQueryClient()
    const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries')

    const { result } = renderHook(
      () => useDeleteTemplate(),
      { wrapper: ({ children }) => (
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      )}
    )

    result.current.mutate('template-1')

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.del).toHaveBeenCalledWith('/rotation-templates/template-1')
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: adminTemplatesQueryKeys.all,
    })
  })
})

describe('useBulkDeleteTemplates', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should delete multiple templates atomically', async () => {
    mockedApi.del.mockResolvedValueOnce(mockBatchResponse)

    const { result } = renderHook(
      () => useBulkDeleteTemplates(),
      { wrapper: createWrapper() }
    )

    result.current.mutate(['template-1', 'template-2'])

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    const callArgs = mockedApi.del.mock.calls[0]
    expect(callArgs[0]).toBe('/rotation-templates/batch')
    expect(callArgs[1]).toMatchObject({
      data: {
        templateIds: ['template-1', 'template-2'],
        dryRun: false,
      },
    })
  })
})

describe('useBulkUpdateTemplates', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should update multiple templates atomically', async () => {
    mockedApi.put.mockResolvedValueOnce(mockBatchResponse)

    const { result } = renderHook(
      () => useBulkUpdateTemplates(),
      { wrapper: createWrapper() }
    )

    result.current.mutate({
      templateIds: ['template-1', 'template-2'],
      updates: { isActive: false },
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    const callArgs = mockedApi.put.mock.calls[0]
    expect(callArgs[0]).toBe('/rotation-templates/batch')
    expect(callArgs[1]).toMatchObject({
      templates: [
        { templateId: 'template-1', updates: { isActive: false } },
        { templateId: 'template-2', updates: { isActive: false } },
      ],
      dryRun: false,
    })
  })
})

describe('useTemplatePreferences', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch preferences for template successfully', async () => {
    mockedApi.get.mockResolvedValueOnce([mockPreference])

    const { result } = renderHook(
      () => useTemplatePreferences('template-1'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual([mockPreference])
    expect(mockedApi.get).toHaveBeenCalledWith('/rotation-templates/template-1/preferences')
  })

  it('should not fetch when templateId is empty', async () => {
    const { result } = renderHook(
      () => useTemplatePreferences(''),
      { wrapper: createWrapper() }
    )

    expect(result.current.isPending).toBe(true)
    expect(mockedApi.get).not.toHaveBeenCalled()
  })
})

describe('useReplaceTemplatePreferences', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should replace preferences successfully', async () => {
    mockedApi.put.mockResolvedValueOnce([mockPreference])

    const { result } = renderHook(
      () => useReplaceTemplatePreferences(),
      { wrapper: createWrapper() }
    )

    result.current.mutate({
      templateId: 'template-1',
      preferences: [
        { personId: 'person-1', preferenceLevel: 5 },
      ],
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.put).toHaveBeenCalledWith(
      '/rotation-templates/template-1/preferences',
      [{ personId: 'person-1', preferenceLevel: 5 }]
    )
  })
})

describe('useTemplatesMap', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should return map of template IDs to templates', async () => {
    const templates = [
      mockTemplate,
      { ...mockTemplate, id: 'template-2', name: 'ER' },
    ]
    mockedApi.get.mockResolvedValueOnce({ items: templates, total: 2 })

    const { result } = renderHook(
      () => useTemplatesMap(),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current).toBeDefined()
    })

    /* eslint-disable @typescript-eslint/naming-convention -- ID keys */
    expect(result.current).toEqual({
      'template-1': templates[0],
      'template-2': templates[1],
    })
    /* eslint-enable @typescript-eslint/naming-convention */
  })
})

describe('useBulkCreateTemplates', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should create multiple templates atomically', async () => {
    mockedApi.post.mockResolvedValueOnce(mockBatchResponse)

    const { result } = renderHook(
      () => useBulkCreateTemplates(),
      { wrapper: createWrapper() }
    )

    result.current.mutate([
      { name: 'Template 1', activityType: 'fm_clinic' },
      { name: 'Template 2', activityType: 'er' },
    ])

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    const callArgs = mockedApi.post.mock.calls[0]
    expect(callArgs[0]).toBe('/rotation-templates/batch')
    expect(callArgs[1]).toMatchObject({
      templates: [
        { name: 'Template 1', activityType: 'fm_clinic' },
        { name: 'Template 2', activityType: 'er' },
      ],
      dryRun: false,
    })
  })
})

describe('useCheckConflicts', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should check for conflicts successfully', async () => {
    mockedApi.post.mockResolvedValueOnce(mockConflictResponse)

    const { result } = renderHook(
      () => useCheckConflicts(),
      { wrapper: createWrapper() }
    )

    result.current.mutate({
      templateIds: ['template-1', 'template-2'],
      operation: 'delete',
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockConflictResponse)
    expect(mockedApi.post).toHaveBeenCalledWith(
      '/rotation-templates/batch/conflicts',
      {
        templateIds: ['template-1', 'template-2'],
        operation: 'delete',
      }
    )
  })
})

describe('useExportTemplates', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should export templates successfully', async () => {
    mockedApi.post.mockResolvedValueOnce(mockExportResponse)

    const { result } = renderHook(
      () => useExportTemplates(),
      { wrapper: createWrapper() }
    )

    result.current.mutate({
      templateIds: ['template-1'],
      format: 'json',
      includePatterns: true,
      includePreferences: true,
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockExportResponse)
    expect(mockedApi.post).toHaveBeenCalledWith(
      '/rotation-templates/export',
      {
        templateIds: ['template-1'],
        format: 'json',
        includePatterns: true,
        includePreferences: true,
      }
    )
  })
})

describe('useArchiveTemplate', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should archive template successfully', async () => {
    const archivedTemplate = { ...mockTemplate, isArchived: true }
    mockedApi.put.mockResolvedValueOnce(archivedTemplate)

    const { result } = renderHook(
      () => useArchiveTemplate(),
      { wrapper: createWrapper() }
    )

    result.current.mutate('template-1')

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.put).toHaveBeenCalledWith(
      '/rotation-templates/template-1/archive',
      {}
    )
  })
})

describe('useRestoreTemplate', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should restore archived template successfully', async () => {
    mockedApi.put.mockResolvedValueOnce(mockTemplate)

    const { result } = renderHook(
      () => useRestoreTemplate(),
      { wrapper: createWrapper() }
    )

    result.current.mutate('template-1')

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.put).toHaveBeenCalledWith(
      '/rotation-templates/template-1/restore',
      {}
    )
  })
})

describe('useBulkArchiveTemplates', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should archive multiple templates atomically', async () => {
    mockedApi.put.mockResolvedValueOnce(mockBatchResponse)

    const { result } = renderHook(
      () => useBulkArchiveTemplates(),
      { wrapper: createWrapper() }
    )

    result.current.mutate(['template-1', 'template-2'])

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    const callArgs = mockedApi.put.mock.calls[0]
    expect(callArgs[0]).toBe('/rotation-templates/batch/archive')
    expect(callArgs[1]).toMatchObject({
      templateIds: ['template-1', 'template-2'],
      dryRun: false,
    })
  })
})

describe('useBulkRestoreTemplates', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should restore multiple templates atomically', async () => {
    mockedApi.put.mockResolvedValueOnce(mockBatchResponse)

    const { result } = renderHook(
      () => useBulkRestoreTemplates(),
      { wrapper: createWrapper() }
    )

    result.current.mutate(['template-1', 'template-2'])

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    const callArgs = mockedApi.put.mock.calls[0]
    expect(callArgs[0]).toBe('/rotation-templates/batch/restore')
    expect(callArgs[1]).toMatchObject({
      templateIds: ['template-1', 'template-2'],
      dryRun: false,
    })
  })
})

describe('useInlineUpdateTemplate', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should update single field inline successfully', async () => {
    mockedApi.put.mockResolvedValueOnce(mockBatchResponse)

    const { result } = renderHook(
      () => useInlineUpdateTemplate(),
      { wrapper: createWrapper() }
    )

    result.current.mutate({
      templateId: 'template-1',
      field: 'name',
      value: 'Updated Name',
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    const callArgs = mockedApi.put.mock.calls[0]
    expect(callArgs[0]).toBe('/rotation-templates/batch')
    expect(callArgs[1]).toMatchObject({
      templates: [
        {
          templateId: 'template-1',
          updates: { name: 'Updated Name' },
        },
      ],
      dryRun: false,
    })
  })
})
