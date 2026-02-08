/**
 * useFacultyActivities Hook Tests
 *
 * Tests for faculty weekly activity management hooks including
 * templates, overrides, effective weeks, permissions, and matrix views.
 */
import { renderHook, waitFor } from '@/test-utils'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactNode } from 'react'
import * as api from '@/lib/api'
import {
  useFacultyTemplate,
  useUpdateFacultyTemplate,
  useUpsertTemplateSlot,
  useDeleteTemplateSlot,
  useFacultyOverrides,
  useCreateFacultyOverride,
  useDeleteFacultyOverride,
  useEffectiveFacultyWeek,
  usePermittedActivities,
  useFacultyMatrix,
  useInvalidateFacultyActivities,
  facultyActivityQueryKeys,
} from '@/hooks/useFacultyActivities'
import type {
  FacultyTemplateResponse,
  FacultyTemplateSlot,
  FacultyOverridesResponse,
  FacultyOverride,
  EffectiveWeekResponse,
  PermittedActivitiesResponse,
  FacultyMatrixResponse,
} from '@/types/faculty-activity'

// Mock the api module
jest.mock('@/lib/api')

const mockedApi = api as jest.Mocked<typeof api>

// Mock data
const mockTemplateSlot: FacultyTemplateSlot = {
  id: 'slot-1',
  personId: 'person-1',
  dayOfWeek: 1,
  timeOfDay: 'AM',
  weekNumber: 1,
  activityId: 'activity-1',
  isLocked: false,
  priority: 50,
  notes: 'Test slot',
  createdAt: '2024-01-01T00:00:00Z',
  updatedAt: '2024-01-01T00:00:00Z',
}

const mockTemplateResponse: FacultyTemplateResponse = {
  personId: 'person-1',
  slots: [mockTemplateSlot],
  createdAt: '2024-01-01T00:00:00Z',
  updatedAt: '2024-01-01T00:00:00Z',
}

const mockOverride: FacultyOverride = {
  id: 'override-1',
  personId: 'person-1',
  effectiveDate: '2024-01-08',
  dayOfWeek: 1,
  timeOfDay: 'AM',
  activityId: 'activity-2',
  isLocked: false,
  overrideReason: 'Conference',
  createdAt: '2024-01-01T00:00:00Z',
  updatedAt: '2024-01-01T00:00:00Z',
}

const mockOverridesResponse: FacultyOverridesResponse = {
  personId: 'person-1',
  weekStart: '2024-01-08',
  overrides: [mockOverride],
}

const mockEffectiveWeekResponse: EffectiveWeekResponse = {
  personId: 'person-1',
  weekStart: '2024-01-08',
  weekNumber: 1,
  slots: [mockTemplateSlot],
  appliedOverrides: [],
}

const mockPermittedActivitiesResponse: PermittedActivitiesResponse = {
  role: 'pd',
  activities: [
    { id: 'activity-1', name: 'Clinic', code: 'CLINIC' },
    { id: 'activity-2', name: 'Admin', code: 'ADMIN' },
  ],
  defaultActivities: ['activity-1'],
}

const mockMatrixResponse: FacultyMatrixResponse = {
  startDate: '2024-01-08',
  endDate: '2024-02-04',
  faculty: [
    {
      personId: 'person-1',
      name: 'Dr. Smith',
      role: 'pd',
      weeks: [
        {
          weekStart: '2024-01-08',
          weekNumber: 1,
          slots: [mockTemplateSlot],
        },
      ],
    },
  ],
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

describe('useFacultyTemplate', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch faculty template successfully', async () => {
    mockedApi.get.mockResolvedValueOnce(mockTemplateResponse)

    const { result } = renderHook(
      () => useFacultyTemplate('person-1'),
      { wrapper: createWrapper() }
    )

    expect(result.current.isLoading).toBe(true)

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockTemplateResponse)
    expect(mockedApi.get).toHaveBeenCalledWith('/faculty/person-1/weekly-template')
  })

  it('should fetch template with week number filter', async () => {
    mockedApi.get.mockResolvedValueOnce(mockTemplateResponse)

    const { result } = renderHook(
      () => useFacultyTemplate('person-1', 2),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith('/faculty/person-1/weekly-template?week_number=2')
  })

  it('should not fetch when personId is empty', async () => {
    const { result } = renderHook(
      () => useFacultyTemplate(''),
      { wrapper: createWrapper() }
    )

    expect(result.current.isPending).toBe(true)
    expect(mockedApi.get).not.toHaveBeenCalled()
  })

  it('should handle API errors', async () => {
    const apiError = { message: 'Not found', status: 404 }
    mockedApi.get.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useFacultyTemplate('person-1'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })
})

describe('useUpdateFacultyTemplate', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should update template successfully', async () => {
    mockedApi.put.mockResolvedValueOnce(mockTemplateResponse)

    const queryClient = createTestQueryClient()
    const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries')

    const { result } = renderHook(
      () => useUpdateFacultyTemplate(),
      { wrapper: ({ children }) => (
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      )}
    )

    result.current.mutate({
      personId: 'person-1',
      slots: [{ dayOfWeek: 1, timeOfDay: 'AM', activityId: 'activity-1' }],
      clearExisting: false,
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.put).toHaveBeenCalledWith(
      '/faculty/person-1/weekly-template',
      {
        slots: [{ dayOfWeek: 1, timeOfDay: 'AM', activityId: 'activity-1' }],
        clearExisting: false,
      }
    )
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: facultyActivityQueryKeys.templates(),
    })
  })

  it('should invalidate effective week queries after update', async () => {
    mockedApi.put.mockResolvedValueOnce(mockTemplateResponse)

    const queryClient = createTestQueryClient()
    const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries')

    const { result } = renderHook(
      () => useUpdateFacultyTemplate(),
      { wrapper: ({ children }) => (
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      )}
    )

    result.current.mutate({
      personId: 'person-1',
      slots: [],
      clearExisting: true,
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: [...facultyActivityQueryKeys.effective(), 'person-1'],
    })
  })
})

describe('useUpsertTemplateSlot', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should create template slot successfully', async () => {
    mockedApi.post.mockResolvedValueOnce(mockTemplateSlot)

    const { result } = renderHook(
      () => useUpsertTemplateSlot(),
      { wrapper: createWrapper() }
    )

    result.current.mutate({
      personId: 'person-1',
      slot: {
        dayOfWeek: 1,
        timeOfDay: 'AM',
        activityId: 'activity-1',
        isLocked: false,
        priority: 50,
      },
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    const callArgs = mockedApi.post.mock.calls[0]
    expect(callArgs[0]).toBe('/faculty/person-1/weekly-template/slots')
    expect(callArgs[1]).toMatchObject({
      dayOfWeek: 1,
      timeOfDay: 'AM',
      activity_id: 'activity-1',
      isLocked: false,
      priority: 50,
    })
  })
})

describe('useDeleteTemplateSlot', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should delete template slot successfully', async () => {
    mockedApi.del.mockResolvedValueOnce(undefined)

    const { result } = renderHook(
      () => useDeleteTemplateSlot(),
      { wrapper: createWrapper() }
    )

    result.current.mutate({
      personId: 'person-1',
      dayOfWeek: 1,
      timeOfDay: 'AM',
      weekNumber: 1,
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.del).toHaveBeenCalledWith(
      '/faculty/person-1/weekly-template/slots?day_of_week=1&time_of_day=AM&week_number=1'
    )
  })

  it('should delete slot without week number', async () => {
    mockedApi.del.mockResolvedValueOnce(undefined)

    const { result } = renderHook(
      () => useDeleteTemplateSlot(),
      { wrapper: createWrapper() }
    )

    result.current.mutate({
      personId: 'person-1',
      dayOfWeek: 2,
      timeOfDay: 'PM',
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.del).toHaveBeenCalledWith(
      '/faculty/person-1/weekly-template/slots?day_of_week=2&time_of_day=PM'
    )
  })
})

describe('useFacultyOverrides', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch overrides for a week successfully', async () => {
    mockedApi.get.mockResolvedValueOnce(mockOverridesResponse)

    const { result } = renderHook(
      () => useFacultyOverrides('person-1', '2024-01-08'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockOverridesResponse)
    expect(mockedApi.get).toHaveBeenCalledWith(
      '/faculty/person-1/weekly-overrides?week_start=2024-01-08'
    )
  })

  it('should not fetch when personId or weekStart is empty', async () => {
    const { result: noPersonId } = renderHook(
      () => useFacultyOverrides('', '2024-01-08'),
      { wrapper: createWrapper() }
    )

    const { result: noWeekStart } = renderHook(
      () => useFacultyOverrides('person-1', ''),
      { wrapper: createWrapper() }
    )

    expect(noPersonId.current.isPending).toBe(true)
    expect(noWeekStart.current.isPending).toBe(true)
    expect(mockedApi.get).not.toHaveBeenCalled()
  })
})

describe('useCreateFacultyOverride', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should create override successfully', async () => {
    mockedApi.post.mockResolvedValueOnce(mockOverride)

    const { result } = renderHook(
      () => useCreateFacultyOverride(),
      { wrapper: createWrapper() }
    )

    result.current.mutate({
      personId: 'person-1',
      override: {
        effectiveDate: '2024-01-08',
        dayOfWeek: 1,
        timeOfDay: 'AM',
        activityId: 'activity-2',
        overrideReason: 'Conference',
      },
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    const callArgs = mockedApi.post.mock.calls[0]
    expect(callArgs[0]).toBe('/faculty/person-1/weekly-overrides')
    expect(callArgs[1]).toMatchObject({
      effective_date: '2024-01-08',
      dayOfWeek: 1,
      timeOfDay: 'AM',
      activity_id: 'activity-2',
      overrideReason: 'Conference',
    })
  })
})

describe('useDeleteFacultyOverride', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should delete override successfully', async () => {
    mockedApi.del.mockResolvedValueOnce(undefined)

    const { result } = renderHook(
      () => useDeleteFacultyOverride(),
      { wrapper: createWrapper() }
    )

    result.current.mutate({
      personId: 'person-1',
      overrideId: 'override-1',
      weekStart: '2024-01-08',
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.del).toHaveBeenCalledWith(
      '/faculty/person-1/weekly-overrides/override-1'
    )
  })
})

describe('useEffectiveFacultyWeek', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch effective week successfully', async () => {
    mockedApi.get.mockResolvedValueOnce(mockEffectiveWeekResponse)

    const { result } = renderHook(
      () => useEffectiveFacultyWeek('person-1', '2024-01-08', 1),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockEffectiveWeekResponse)
    expect(mockedApi.get).toHaveBeenCalledWith(
      '/faculty/person-1/weekly-template/effective?week_start=2024-01-08&week_number=1'
    )
  })

  it('should use default week number of 1', async () => {
    mockedApi.get.mockResolvedValueOnce(mockEffectiveWeekResponse)

    const { result } = renderHook(
      () => useEffectiveFacultyWeek('person-1', '2024-01-08'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith(
      '/faculty/person-1/weekly-template/effective?week_start=2024-01-08&week_number=1'
    )
  })
})

describe('usePermittedActivities', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch permitted activities for role successfully', async () => {
    mockedApi.get.mockResolvedValueOnce(mockPermittedActivitiesResponse)

    const { result } = renderHook(
      () => usePermittedActivities('pd'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockPermittedActivitiesResponse)
    expect(mockedApi.get).toHaveBeenCalledWith('/faculty/activities/permitted?role=pd')
  })

  it('should not fetch when role is empty', async () => {
    const { result } = renderHook(
      () => usePermittedActivities('' as any),
      { wrapper: createWrapper() }
    )

    expect(result.current.isPending).toBe(true)
    expect(mockedApi.get).not.toHaveBeenCalled()
  })
})

describe('useFacultyMatrix', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch matrix successfully', async () => {
    mockedApi.get.mockResolvedValueOnce(mockMatrixResponse)

    const { result } = renderHook(
      () => useFacultyMatrix('2024-01-08', '2024-02-04'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockMatrixResponse)
    expect(mockedApi.get).toHaveBeenCalledWith(
      '/faculty/activities/matrix?start_date=2024-01-08&end_date=2024-02-04'
    )
  })

  it('should include adjunct faculty when requested', async () => {
    mockedApi.get.mockResolvedValueOnce(mockMatrixResponse)

    const { result } = renderHook(
      () => useFacultyMatrix('2024-01-08', '2024-02-04', true),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith(
      '/faculty/activities/matrix?start_date=2024-01-08&end_date=2024-02-04&include_adjunct=true'
    )
  })

  it('should not fetch when dates are empty', async () => {
    const { result } = renderHook(
      () => useFacultyMatrix('', '2024-02-04'),
      { wrapper: createWrapper() }
    )

    expect(result.current.isPending).toBe(true)
    expect(mockedApi.get).not.toHaveBeenCalled()
  })
})

describe('useInvalidateFacultyActivities', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should invalidate all faculty activity queries', async () => {
    const queryClient = createTestQueryClient()
    const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries')

    const { result } = renderHook(
      () => useInvalidateFacultyActivities(),
      { wrapper: ({ children }) => (
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      )}
    )

    result.current()

    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: facultyActivityQueryKeys.all,
    })
  })
})
