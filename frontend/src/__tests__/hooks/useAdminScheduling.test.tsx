/**
 * useAdminScheduling Hook Tests
 *
 * Tests for admin scheduling hooks including run management,
 * configuration, experimentation, metrics, and manual overrides.
 */
import { renderHook, waitFor } from '@/test-utils'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactNode } from 'react'
import * as api from '@/lib/api'
import {
  useScheduleRuns,
  useScheduleRun,
  useRunComparison,
  useGenerateScheduleRun,
  useConstraintConfigs,
  useScenarioPresets,
  useLockedAssignments,
  useEmergencyHolidays,
  useLockAssignment,
  useUnlockAssignment,
  useCreateEmergencyHoliday,
  useDeleteEmergencyHoliday,
  type RunLogEntry,
  type ScheduleRunsResponse,
  type RunComparisonResponse,
  type ConstraintConfig,
  type ScenarioPreset,
  type LockedAssignment,
  type EmergencyHoliday,
  type RunConfiguration,
  type RunResult,
} from '@/hooks/useAdminScheduling'

// Mock the api module
jest.mock('@/lib/api')

const mockedApi = api as jest.Mocked<typeof api>

// Mock data
const mockRunLogEntry: RunLogEntry = {
  id: 'run-1',
  runId: 'abc-123',
  algorithm: 'cp_sat',
  timestamp: '2026-02-05T12:00:00Z',
  status: 'success',
  configuration: {
    algorithm: 'cp_sat',
    constraints: [],
    preserveFMIT: true,
    nfPostCallEnabled: false,
    academicYear: '2025-2026',
    blockRange: { start: 1, end: 26 },
    timeoutSeconds: 300,
    dryRun: false,
  },
  result: {
    runId: 'abc-123',
    status: 'success',
    coveragePercent: 95,
    acgmeViolations: 0,
    fairnessScore: 0.85,
    swapChurn: 3,
    runtimeSeconds: 45,
    stability: 0.92,
    blocksAssigned: 247,
    totalBlocks: 260,
    timestamp: '2026-02-05T12:00:00Z',
  },
  coverage: 95,
  violations: 0,
  duration: '45s',
  tags: ['production', 'cp-sat'],
}

const mockScheduleRunsResponse: ScheduleRunsResponse = {
  runs: [mockRunLogEntry],
  total: 1,
  page: 1,
  pageSize: 20,
}

const mockComparisonResponse: RunComparisonResponse = {
  comparison: {
    runA: mockRunLogEntry.result,
    runB: {
      ...mockRunLogEntry.result,
      runId: 'def-456',
      coveragePercent: 90,
      fairnessScore: 0.80,
    },
    differences: [
      {
        metric: 'coveragePercent',
        delta: 5,
        percentChange: 5.56,
        winner: 'A',
      },
    ],
  },
  insights: ['Run A has better coverage'],
  recommendation: 'Use Run A configuration',
}

const mockConstraintConfig: ConstraintConfig = {
  id: 'acgme-80hr',
  name: '80-Hour Work Week',
  description: 'ACGME 80-hour work week limit',
  enabled: true,
  weight: 100,
  priority: 1,
  category: 'acgme',
  severity: 'hard',
}

const mockScenarioPreset: ScenarioPreset = {
  id: 'preset-1',
  name: 'Standard Rotation',
  description: 'Standard residency rotation schedule',
  size: 'medium',
  residentCount: 12,
  facultyCount: 8,
  blockCount: 26,
  constraints: ['acgme-80hr'],
}

const mockLockedAssignment: LockedAssignment = {
  id: 'lock-1',
  personId: 'person-1',
  personName: 'Dr. Smith',
  blockId: 'block-1',
  blockDate: '2026-07-01',
  rotationId: 'rotation-1',
  rotationName: 'Emergency Medicine',
  lockedAt: '2026-02-05T12:00:00Z',
  lockedBy: 'admin-1',
  reason: 'Special request',
  expiresAt: '2026-07-31T23:59:59Z',
}

const mockEmergencyHoliday: EmergencyHoliday = {
  id: 'holiday-1',
  date: '2026-07-04',
  name: 'Independence Day',
  type: 'federal',
  affectsScheduling: true,
  createdAt: '2026-02-05T12:00:00Z',
  createdBy: 'admin-1',
}

const mockRunConfiguration: RunConfiguration = {
  algorithm: 'cp_sat',
  constraints: [mockConstraintConfig],
  preserveFMIT: true,
  nfPostCallEnabled: false,
  academicYear: '2025-2026',
  blockRange: { start: 1, end: 26 },
  timeoutSeconds: 300,
  dryRun: false,
}

const mockRunResult: RunResult = {
  runId: 'abc-123',
  status: 'success',
  coveragePercent: 95,
  acgmeViolations: 0,
  fairnessScore: 0.85,
  swapChurn: 3,
  runtimeSeconds: 45,
  stability: 0.92,
  blocksAssigned: 247,
  totalBlocks: 260,
  timestamp: '2026-02-05T12:00:00Z',
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

describe('useScheduleRuns', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch schedule runs without filters', async () => {
    mockedApi.get.mockResolvedValueOnce(mockScheduleRunsResponse)

    const { result } = renderHook(
      () => useScheduleRuns(),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockScheduleRunsResponse)
    expect(mockedApi.get).toHaveBeenCalledWith('/schedule/runs')
  })

  it('should fetch schedule runs with run ID filter', async () => {
    mockedApi.get.mockResolvedValueOnce(mockScheduleRunsResponse)

    const { result } = renderHook(
      () => useScheduleRuns({ runId: 'abc-123' }),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith('/schedule/runs?run_id=abc-123')
  })

  it('should fetch schedule runs with algorithm filters', async () => {
    mockedApi.get.mockResolvedValueOnce(mockScheduleRunsResponse)

    const { result } = renderHook(
      () => useScheduleRuns({ algorithms: ['cp_sat', 'greedy'] }),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith('/schedule/runs?algorithms=cp_sat%2Cgreedy')
  })

  it('should fetch schedule runs with date range filter', async () => {
    mockedApi.get.mockResolvedValueOnce(mockScheduleRunsResponse)

    const { result } = renderHook(
      () => useScheduleRuns({
        dateRange: { start: '2026-01-01', end: '2026-12-31' }
      }),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith(
      '/schedule/runs?start_date=2026-01-01&end_date=2026-12-31'
    )
  })

  it('should fetch schedule runs with status and tag filters', async () => {
    mockedApi.get.mockResolvedValueOnce(mockScheduleRunsResponse)

    const { result } = renderHook(
      () => useScheduleRuns({
        status: ['success', 'partial'],
        tags: ['production']
      }),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith(
      '/schedule/runs?status=success%2Cpartial&tags=production'
    )
  })

  it('should handle error when fetching schedule runs', async () => {
    const mockError = Object.assign(new Error('Failed to fetch'), {
      status: 500,
      message: 'Server error',
    })
    mockedApi.get.mockRejectedValueOnce(mockError)

    const { result } = renderHook(
      () => useScheduleRuns(),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(mockError)
  })
})

describe('useScheduleRun', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch single schedule run by ID', async () => {
    mockedApi.get.mockResolvedValueOnce(mockRunLogEntry)

    const { result } = renderHook(
      () => useScheduleRun('run-1'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockRunLogEntry)
    expect(mockedApi.get).toHaveBeenCalledWith('/schedule/runs/run-1')
  })

  it('should not fetch when ID is empty', async () => {
    const { result } = renderHook(
      () => useScheduleRun(''),
      { wrapper: createWrapper() }
    )

    expect(result.current.isFetching).toBe(false)
    expect(mockedApi.get).not.toHaveBeenCalled()
  })

  it('should handle error when fetching single run', async () => {
    const mockError = Object.assign(new Error('Not found'), {
      status: 404,
      message: 'Run not found',
    })
    mockedApi.get.mockRejectedValueOnce(mockError)

    const { result } = renderHook(
      () => useScheduleRun('run-999'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(mockError)
  })
})

describe('useRunComparison', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch comparison between two runs', async () => {
    mockedApi.get.mockResolvedValueOnce(mockComparisonResponse)

    const { result } = renderHook(
      () => useRunComparison('run-a', 'run-b'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockComparisonResponse)
    expect(mockedApi.get).toHaveBeenCalledWith('/schedule/runs/compare?run_a=run-a&run_b=run-b')
  })

  it('should not fetch when IDs are missing', async () => {
    const { result } = renderHook(
      () => useRunComparison('', 'run-b'),
      { wrapper: createWrapper() }
    )

    expect(result.current.isFetching).toBe(false)
    expect(mockedApi.get).not.toHaveBeenCalled()
  })
})

describe('useConstraintConfigs', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch constraint configurations', async () => {
    const mockConstraints = [mockConstraintConfig]
    mockedApi.get.mockResolvedValueOnce(mockConstraints)

    const { result } = renderHook(
      () => useConstraintConfigs(),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockConstraints)
    expect(mockedApi.get).toHaveBeenCalledWith('/schedule/constraints')
  })
})

describe('useScenarioPresets', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch scenario presets', async () => {
    const mockPresets = [mockScenarioPreset]
    mockedApi.get.mockResolvedValueOnce(mockPresets)

    const { result } = renderHook(
      () => useScenarioPresets(),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockPresets)
    expect(mockedApi.get).toHaveBeenCalledWith('/schedule/scenarios')
  })
})

describe('useGenerateScheduleRun', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should trigger schedule generation', async () => {
    mockedApi.post.mockResolvedValueOnce(mockRunResult)

    const { result } = renderHook(
      () => useGenerateScheduleRun(),
      { wrapper: createWrapper() }
    )

    result.current.mutate(mockRunConfiguration)

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.post).toHaveBeenCalledWith(
      '/schedule/generate',
      expect.objectContaining({
        algorithm: 'cp_sat',
        dryRun: false,
        preserveFmit: true,
        nfPostCall: false,
        timeoutSeconds: 300,
      })
    )
  })

  it('should handle generation error', async () => {
    const mockError = Object.assign(new Error('Generation failed'), {
      status: 422,
      message: 'Validation error',
    })
    mockedApi.post.mockRejectedValueOnce(mockError)

    const { result } = renderHook(
      () => useGenerateScheduleRun(),
      { wrapper: createWrapper() }
    )

    result.current.mutate(mockRunConfiguration)

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(mockError)
  })
})

describe('useLockedAssignments', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch locked assignments', async () => {
    const mockLocks = [mockLockedAssignment]
    mockedApi.get.mockResolvedValueOnce(mockLocks)

    const { result } = renderHook(
      () => useLockedAssignments(),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockLocks)
    expect(mockedApi.get).toHaveBeenCalledWith('/schedule/locks')
  })
})

describe('useLockAssignment', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should lock an assignment', async () => {
    mockedApi.post.mockResolvedValueOnce(mockLockedAssignment)

    const { result } = renderHook(
      () => useLockAssignment(),
      { wrapper: createWrapper() }
    )

    result.current.mutate({
      assignmentId: 'assignment-1',
      reason: 'Special request',
      expiresAt: '2026-07-31T23:59:59Z',
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.post).toHaveBeenCalledWith('/schedule/locks', {
      assignmentId: 'assignment-1',
      reason: 'Special request',
      expiresAt: '2026-07-31T23:59:59Z',
    })
  })
})

describe('useUnlockAssignment', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should unlock an assignment', async () => {
    mockedApi.del.mockResolvedValueOnce(undefined)

    const { result } = renderHook(
      () => useUnlockAssignment(),
      { wrapper: createWrapper() }
    )

    result.current.mutate('lock-1')

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.del).toHaveBeenCalledWith('/schedule/locks/lock-1')
  })
})

describe('useEmergencyHolidays', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch emergency holidays', async () => {
    const mockHolidays = [mockEmergencyHoliday]
    mockedApi.get.mockResolvedValueOnce(mockHolidays)

    const { result } = renderHook(
      () => useEmergencyHolidays(),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockHolidays)
    expect(mockedApi.get).toHaveBeenCalledWith('/schedule/holidays')
  })
})

describe('useCreateEmergencyHoliday', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should create emergency holiday', async () => {
    mockedApi.post.mockResolvedValueOnce(mockEmergencyHoliday)

    const { result } = renderHook(
      () => useCreateEmergencyHoliday(),
      { wrapper: createWrapper() }
    )

    result.current.mutate({
      date: '2026-07-04',
      name: 'Independence Day',
      type: 'federal',
      affectsScheduling: true,
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.post).toHaveBeenCalledWith('/schedule/holidays', {
      date: '2026-07-04',
      name: 'Independence Day',
      type: 'federal',
      affectsScheduling: true,
    })
  })
})

describe('useDeleteEmergencyHoliday', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should delete emergency holiday', async () => {
    mockedApi.del.mockResolvedValueOnce(undefined)

    const { result } = renderHook(
      () => useDeleteEmergencyHoliday(),
      { wrapper: createWrapper() }
    )

    result.current.mutate('holiday-1')

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.del).toHaveBeenCalledWith('/schedule/holidays/holiday-1')
  })
})
