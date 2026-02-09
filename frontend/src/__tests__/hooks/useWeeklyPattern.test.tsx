/**
 * useWeeklyPattern Hook Tests
 *
 * Tests for weekly pattern fetching and management hooks
 * using jest.mock() for API mocking.
 */
import { renderHook, waitFor } from '@/test-utils'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactNode } from 'react'
import * as api from '@/lib/api'
import {
  useWeeklyPattern,
  useUpdateWeeklyPattern,
  useAvailableTemplates,
  useBulkUpdateWeeklyPatterns,
  weeklyPatternQueryKeys,
} from '@/hooks/useWeeklyPattern'
import type { WeeklyPatternGrid, WeeklyPatternResponse, DayOfWeek } from '@/types/weekly-pattern'

// Mock the api module
jest.mock('@/lib/api')

const mockedApi = api as jest.Mocked<typeof api>

// Mock data
const mockTemplateId = 'template-123'

const mockBackendPatterns = [
  {
    id: 'pattern-1',
    rotationTemplateId: mockTemplateId,
    dayOfWeek: 0,
    timeOfDay: 'AM' as const,
    activityType: 'scheduled',
    linkedTemplateId: 'rotation-a',
    isProtected: false,
    notes: null,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  },
  {
    id: 'pattern-2',
    rotationTemplateId: mockTemplateId,
    dayOfWeek: 0,
    timeOfDay: 'PM' as const,
    activityType: 'scheduled',
    linkedTemplateId: 'rotation-b',
    isProtected: false,
    notes: 'PM rotation',
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  },
]

const mockTemplates = {
  items: [
    {
      id: 'rotation-a',
      name: 'Rotation A',
      activityType: 'scheduled',
      abbreviation: 'RA',
      displayAbbreviation: 'RA',
      fontColor: '#000000',
      backgroundColor: '#FFFFFF',
    },
    {
      id: 'rotation-b',
      name: 'Rotation B',
      activityType: 'scheduled',
      abbreviation: 'RB',
      displayAbbreviation: 'RB',
      fontColor: '#FFFFFF',
      backgroundColor: '#000000',
    },
  ],
  total: 2,
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

describe('useWeeklyPattern', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch weekly pattern successfully', async () => {
    mockedApi.get.mockResolvedValueOnce(mockBackendPatterns)

    const { result } = renderHook(
      () => useWeeklyPattern(mockTemplateId),
      { wrapper: createWrapper() }
    )

    // Initially loading
    expect(result.current.isLoading).toBe(true)
    expect(result.current.data).toBeUndefined()

    // Wait for data to load
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    // Check data structure
    expect(result.current.data?.templateId).toBe(mockTemplateId)
    expect(result.current.data?.pattern.slots).toHaveLength(14) // 7 days * 2 times
    expect(mockedApi.get).toHaveBeenCalledWith(`/rotation-templates/${mockTemplateId}/patterns`)
  })

  it('should show loading state while fetching', async () => {
    mockedApi.get.mockResolvedValueOnce(mockBackendPatterns)

    const { result } = renderHook(
      () => useWeeklyPattern(mockTemplateId),
      { wrapper: createWrapper() }
    )

    expect(result.current.isLoading).toBe(true)
    expect(result.current.isFetching).toBe(true)

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })
  })

  it('should handle empty pattern response', async () => {
    mockedApi.get.mockResolvedValueOnce([])

    const { result } = renderHook(
      () => useWeeklyPattern(mockTemplateId),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    // Should have 14 slots but all empty
    expect(result.current.data?.pattern.slots).toHaveLength(14)
    expect(result.current.data?.pattern.slots.every(s => s.rotationTemplateId === null)).toBe(true)
  })

  it('should handle API errors gracefully', async () => {
    const apiError = Object.assign(new Error('Failed to fetch patterns'), { status: 500 })
    mockedApi.get.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useWeeklyPattern(mockTemplateId),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error?.message).toBe('Failed to fetch patterns')
  })

  it('should not fetch when templateId is empty', async () => {
    const { result } = renderHook(
      () => useWeeklyPattern(''),
      { wrapper: createWrapper() }
    )

    // Should not trigger fetch
    expect(result.current.isLoading).toBe(false)
    expect(result.current.data).toBeUndefined()
    expect(mockedApi.get).not.toHaveBeenCalled()
  })

  it('should convert backend patterns to frontend grid format', async () => {
    mockedApi.get.mockResolvedValueOnce(mockBackendPatterns)

    const { result } = renderHook(
      () => useWeeklyPattern(mockTemplateId),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    const pattern = result.current.data?.pattern
    // Monday AM (day 0, slot 0)
    expect(pattern?.slots[0].rotationTemplateId).toBe('rotation-a')
    expect(pattern?.slots[0].dayOfWeek).toBe(0)
    expect(pattern?.slots[0].timeOfDay).toBe('AM')

    // Monday PM (day 0, slot 1)
    expect(pattern?.slots[1].rotationTemplateId).toBe('rotation-b')
    expect(pattern?.slots[1].notes).toBe('PM rotation')
  })

  it('should preserve protected status from backend', async () => {
    const protectedPattern = [{
      ...mockBackendPatterns[0],
      isProtected: true,
    }]
    mockedApi.get.mockResolvedValueOnce(protectedPattern)

    const { result } = renderHook(
      () => useWeeklyPattern(mockTemplateId),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.pattern.slots[0].isProtected).toBe(true)
  })
})

describe('useUpdateWeeklyPattern', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should update weekly pattern successfully', async () => {
    const mockPattern: WeeklyPatternGrid = {
      slots: Array(14).fill(null).map((_, i) => ({
        dayOfWeek: Math.floor(i / 2) as DayOfWeek,
        timeOfDay: (i % 2 === 0 ? 'AM' : 'PM'),
        rotationTemplateId: i === 0 ? 'rotation-a' : null,
        activityType: i === 0 ? 'scheduled' : undefined,
        isProtected: false,
        notes: null,
      })),
    }

    mockedApi.put.mockResolvedValueOnce([mockBackendPatterns[0]])

    const queryClient = createTestQueryClient()
    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    )

    const { result } = renderHook(() => useUpdateWeeklyPattern(), { wrapper })

    result.current.mutate({
      templateId: mockTemplateId,
      pattern: mockPattern,
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.put).toHaveBeenCalledWith(
      `/rotation-templates/${mockTemplateId}/patterns`,
      expect.objectContaining({
        patterns: expect.arrayContaining([
          expect.objectContaining({
            dayOfWeek: 0,
            timeOfDay: 'AM',
            linkedTemplateId: 'rotation-a',
          }),
        ]),
      })
    )
  })

  it('should invalidate queries on success', async () => {
    mockedApi.put.mockResolvedValueOnce(mockBackendPatterns)

    const queryClient = createTestQueryClient()
    const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries')

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    )

    const { result } = renderHook(() => useUpdateWeeklyPattern(), { wrapper })

    const mockPattern: WeeklyPatternGrid = {
      slots: Array(14).fill(null).map((_, i) => ({
        dayOfWeek: Math.floor(i / 2) as DayOfWeek,
        timeOfDay: (i % 2 === 0 ? 'AM' : 'PM'),
        rotationTemplateId: null,
        activityType: undefined,
        isProtected: false,
        notes: null,
      })),
    }

    result.current.mutate({
      templateId: mockTemplateId,
      pattern: mockPattern,
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: weeklyPatternQueryKeys.pattern(mockTemplateId),
    })
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['rotation-templates'],
    })
  })

  it('should handle update errors', async () => {
    const apiError = Object.assign(new Error('Update failed'), { status: 400 })
    mockedApi.put.mockRejectedValueOnce(apiError)

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={createTestQueryClient()}>
        {children}
      </QueryClientProvider>
    )

    const { result } = renderHook(() => useUpdateWeeklyPattern(), { wrapper })

    const mockPattern: WeeklyPatternGrid = {
      slots: Array(14).fill(null).map((_, i) => ({
        dayOfWeek: Math.floor(i / 2) as DayOfWeek,
        timeOfDay: (i % 2 === 0 ? 'AM' : 'PM'),
        rotationTemplateId: null,
        activityType: undefined,
        isProtected: false,
        notes: null,
      })),
    }

    result.current.mutate({
      templateId: mockTemplateId,
      pattern: mockPattern,
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error?.message).toBe('Update failed')
  })
})

describe('useAvailableTemplates', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch available templates successfully', async () => {
    mockedApi.get.mockResolvedValueOnce(mockTemplates)

    const { result } = renderHook(
      () => useAvailableTemplates(),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toHaveLength(2)
    expect(result.current.data?.[0]).toMatchObject({
      id: 'rotation-a',
      name: 'Rotation A',
      displayAbbreviation: 'RA',
    })
    expect(mockedApi.get).toHaveBeenCalledWith('/rotation-templates')
  })

  it('should convert backend template format to frontend refs', async () => {
    mockedApi.get.mockResolvedValueOnce(mockTemplates)

    const { result } = renderHook(
      () => useAvailableTemplates(),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    const template = result.current.data?.[0]
    expect(template).toEqual({
      id: 'rotation-a',
      name: 'Rotation A',
      displayAbbreviation: 'RA',
      backgroundColor: '#FFFFFF',
      fontColor: '#000000',
    })
  })

  it('should handle empty template list', async () => {
    mockedApi.get.mockResolvedValueOnce({ items: [], total: 0 })

    const { result } = renderHook(
      () => useAvailableTemplates(),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toHaveLength(0)
  })

  it('should handle API errors', async () => {
    const apiError = Object.assign(new Error('Failed to fetch templates'), { status: 500 })
    mockedApi.get.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useAvailableTemplates(),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error?.message).toBe('Failed to fetch templates')
  })
})

describe('useBulkUpdateWeeklyPatterns', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should bulk update patterns successfully', async () => {
    const mockResponse = {
      successful: 2,
      failed: 0,
      results: [
        { templateId: 'template-1', success: true, error: null },
        { templateId: 'template-2', success: true, error: null },
      ],
    }

    mockedApi.put.mockResolvedValueOnce(mockResponse)

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={createTestQueryClient()}>
        {children}
      </QueryClientProvider>
    )

    const { result } = renderHook(() => useBulkUpdateWeeklyPatterns(), { wrapper })

    result.current.mutate({
      templateIds: ['template-1', 'template-2'],
      mode: 'overlay',
      slots: [
        {
          dayOfWeek: 0,
          timeOfDay: 'AM',
          linkedTemplateId: 'rotation-a',
        },
      ],
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.successful).toBe(2)
    expect(mockedApi.put).toHaveBeenCalledWith(
      '/rotation-templates/batch/patterns',
      expect.objectContaining({
        templateIds: ['template-1', 'template-2'],
        mode: 'overlay',
        slots: expect.any(Array),
      })
    )
  })

  it('should invalidate all affected template queries', async () => {
    const mockResponse = {
      successful: 2,
      failed: 0,
      results: [
        { templateId: 'template-1', success: true, error: null },
        { templateId: 'template-2', success: true, error: null },
      ],
    }

    mockedApi.put.mockResolvedValueOnce(mockResponse)

    const queryClient = createTestQueryClient()
    const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries')

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    )

    const { result } = renderHook(() => useBulkUpdateWeeklyPatterns(), { wrapper })

    result.current.mutate({
      templateIds: ['template-1', 'template-2'],
      mode: 'replace',
      slots: [],
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: weeklyPatternQueryKeys.pattern('template-1'),
    })
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: weeklyPatternQueryKeys.pattern('template-2'),
    })
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['rotation-templates'],
    })
  })

  it('should handle bulk update errors', async () => {
    const apiError = Object.assign(new Error('Bulk update failed'), { status: 400 })
    mockedApi.put.mockRejectedValueOnce(apiError)

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={createTestQueryClient()}>
        {children}
      </QueryClientProvider>
    )

    const { result } = renderHook(() => useBulkUpdateWeeklyPatterns(), { wrapper })

    result.current.mutate({
      templateIds: ['template-1'],
      mode: 'overlay',
      slots: [],
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error?.message).toBe('Bulk update failed')
  })

  it('should support overlay mode', async () => {
    const mockResponse = {
      successful: 1,
      failed: 0,
      results: [{ templateId: 'template-1', success: true, error: null }],
    }

    mockedApi.put.mockResolvedValueOnce(mockResponse)

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={createTestQueryClient()}>
        {children}
      </QueryClientProvider>
    )

    const { result } = renderHook(() => useBulkUpdateWeeklyPatterns(), { wrapper })

    result.current.mutate({
      templateIds: ['template-1'],
      mode: 'overlay',
      slots: [
        { dayOfWeek: 0, timeOfDay: 'AM', linkedTemplateId: 'rotation-a' },
      ],
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.put.mock.calls[0][1]).toMatchObject({
      mode: 'overlay',
    })
  })

  it('should support week number filtering', async () => {
    const mockResponse = {
      successful: 1,
      failed: 0,
      results: [{ templateId: 'template-1', success: true, error: null }],
    }

    mockedApi.put.mockResolvedValueOnce(mockResponse)

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={createTestQueryClient()}>
        {children}
      </QueryClientProvider>
    )

    const { result } = renderHook(() => useBulkUpdateWeeklyPatterns(), { wrapper })

    result.current.mutate({
      templateIds: ['template-1'],
      mode: 'overlay',
      slots: [],
      weekNumbers: [1, 2, 3],
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.put.mock.calls[0][1]).toMatchObject({
      weekNumbers: [1, 2, 3],
    })
  })
})
