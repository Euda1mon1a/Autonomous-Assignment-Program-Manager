/**
 * useBackup Hook Tests
 *
 * Tests for backup snapshot operations including create, restore, and list.
 */
import { renderHook, waitFor } from '@/test-utils'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactNode } from 'react'
import * as api from '@/lib/api'
import {
  useSnapshots,
  useCreateSnapshot,
  useRestoreSnapshot,
  useWithBackup,
  type SnapshotListResponse,
  type SnapshotResponse,
  type RestoreResponse,
} from '@/hooks/useBackup'

// Mock the api module
jest.mock('@/lib/api')

const mockedApi = api as jest.Mocked<typeof api>

// Mock data
const mockSnapshots: SnapshotResponse[] = [
  {
    snapshotId: 'rotationTemplates_20260205_120000',
    table: 'rotation_templates',
    rowCount: 42,
    filePath: '/backups/rotationTemplates_20260205_120000.json',
    createdAt: '2026-02-05T12:00:00Z',
    createdBy: 'user-123',
    reason: 'Before bulk delete',
  },
  {
    snapshotId: 'assignments_20260205_100000',
    table: 'assignments',
    rowCount: 157,
    filePath: '/backups/assignments_20260205_100000.json',
    createdAt: '2026-02-05T10:00:00Z',
    createdBy: 'user-456',
    reason: 'Before schedule regeneration',
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

describe('useSnapshots', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch snapshots for all tables when no table specified', async () => {
    const mockResponse: SnapshotListResponse = {
      snapshots: mockSnapshots,
      total: mockSnapshots.length,
    }
    mockedApi.get.mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(
      () => useSnapshots(undefined, true),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.snapshots).toHaveLength(2)
    expect(result.current.data?.total).toBe(2)
    expect(mockedApi.get).toHaveBeenCalledWith('/backup/snapshots')
  })

  it('should fetch snapshots filtered by table name', async () => {
    const filteredSnapshots = mockSnapshots.filter(s => s.table === 'rotation_templates')
    const mockResponse: SnapshotListResponse = {
      snapshots: filteredSnapshots,
      total: filteredSnapshots.length,
    }
    mockedApi.get.mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(
      () => useSnapshots('rotation_templates', true),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.snapshots).toHaveLength(1)
    expect(result.current.data?.snapshots[0].table).toBe('rotation_templates')
    expect(mockedApi.get).toHaveBeenCalledWith('/backup/snapshots?table=rotation_templates')
  })

  it('should respect enabled flag and not fetch when disabled', async () => {
    const { result } = renderHook(
      () => useSnapshots('rotation_templates', false),
      { wrapper: createWrapper() }
    )

    // Should not fetch
    expect(result.current.isFetching).toBe(false)
    expect(mockedApi.get).not.toHaveBeenCalled()
  })

  it('should handle empty snapshot list', async () => {
    const mockResponse: SnapshotListResponse = {
      snapshots: [],
      total: 0,
    }
    mockedApi.get.mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(
      () => useSnapshots(undefined, true),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.snapshots).toHaveLength(0)
    expect(result.current.data?.total).toBe(0)
  })

  it('should handle API errors gracefully', async () => {
    const apiError = Object.assign(
      new Error('Failed to fetch snapshots'),
      { status: 500 }
    )
    mockedApi.get.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useSnapshots(undefined, true),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })
})

describe('useCreateSnapshot', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should create a snapshot successfully', async () => {
    const mockResponse: SnapshotResponse = mockSnapshots[0]
    mockedApi.post.mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(
      () => useCreateSnapshot(),
      { wrapper: createWrapper() }
    )

    const snapshotRequest = {
      table: 'rotation_templates',
      reason: 'Before bulk delete of 5 templates',
    }

    result.current.mutate(snapshotRequest)

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockResponse)
    expect(mockedApi.post).toHaveBeenCalledWith('/backup/snapshot', snapshotRequest)
  })

  it('should handle snapshot creation errors', async () => {
    const apiError = Object.assign(
      new Error('Insufficient disk space'),
      { status: 507 }
    )
    mockedApi.post.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useCreateSnapshot(),
      { wrapper: createWrapper() }
    )

    result.current.mutate({
      table: 'rotation_templates',
      reason: 'Test snapshot',
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })

  it('should invalidate snapshot queries on success', async () => {
    const queryClient = createTestQueryClient()
    const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries')

    const mockResponse: SnapshotResponse = mockSnapshots[0]
    mockedApi.post.mockResolvedValueOnce(mockResponse)

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    )

    const { result } = renderHook(() => useCreateSnapshot(), { wrapper })

    result.current.mutate({
      table: 'rotation_templates',
      reason: 'Test snapshot',
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['backup', 'snapshots', 'rotation_templates'],
    })
  })
})

describe('useRestoreSnapshot', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should restore from snapshot successfully', async () => {
    const mockResponse: RestoreResponse = {
      snapshotId: 'rotationTemplates_20260205_120000',
      table: 'rotation_templates',
      rowsRestored: 42,
      dryRun: false,
      message: 'Successfully restored 42 rows',
    }
    mockedApi.post.mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(
      () => useRestoreSnapshot(),
      { wrapper: createWrapper() }
    )

    const restoreRequest = {
      snapshotId: 'rotationTemplates_20260205_120000',
      dryRun: false,
    }

    result.current.mutate(restoreRequest)

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockResponse)
    expect(mockedApi.post).toHaveBeenCalledWith('/backup/restore', restoreRequest)
  })

  it('should support dry run mode', async () => {
    const mockResponse: RestoreResponse = {
      snapshotId: 'rotationTemplates_20260205_120000',
      table: 'rotation_templates',
      rowsRestored: 42,
      dryRun: true,
      message: 'Dry run: would restore 42 rows',
    }
    mockedApi.post.mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(
      () => useRestoreSnapshot(),
      { wrapper: createWrapper() }
    )

    result.current.mutate({
      snapshotId: 'rotationTemplates_20260205_120000',
      dryRun: true,
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.dryRun).toBe(true)
    expect(result.current.data?.message).toContain('Dry run')
  })

  it('should handle restore errors', async () => {
    const apiError = Object.assign(
      new Error('Snapshot not found'),
      { status: 404 }
    )
    mockedApi.post.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useRestoreSnapshot(),
      { wrapper: createWrapper() }
    )

    result.current.mutate({
      snapshotId: 'nonexistent_snapshot',
      dryRun: false,
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })

  it('should invalidate all queries on successful restore', async () => {
    const queryClient = createTestQueryClient()
    const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries')

    const mockResponse: RestoreResponse = {
      snapshotId: 'rotationTemplates_20260205_120000',
      table: 'rotation_templates',
      rowsRestored: 42,
      dryRun: false,
      message: 'Success',
    }
    mockedApi.post.mockResolvedValueOnce(mockResponse)

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    )

    const { result } = renderHook(() => useRestoreSnapshot(), { wrapper })

    result.current.mutate({
      snapshotId: 'rotationTemplates_20260205_120000',
      dryRun: false,
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    // Should invalidate all queries since data changed
    expect(invalidateSpy).toHaveBeenCalledWith()
  })
})

describe('useWithBackup', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should create snapshot before executing operation', async () => {
    const mockSnapshot: SnapshotResponse = mockSnapshots[0]
    const mockOperationResult = { success: true, deletedCount: 5 }

    mockedApi.post.mockResolvedValueOnce(mockSnapshot)

    const { result } = renderHook(
      () => useWithBackup(),
      { wrapper: createWrapper() }
    )

    const operation = jest.fn().mockResolvedValue(mockOperationResult)

    const executePromise = result.current.execute(
      {
        table: 'rotation_templates',
        reason: 'Before bulk delete',
      },
      operation
    )

    await waitFor(() => {
      expect(result.current.isCreatingSnapshot).toBe(false)
    })

    const executeResult = await executePromise

    expect(executeResult.snapshot).toEqual(mockSnapshot)
    expect(executeResult.result).toEqual(mockOperationResult)
    expect(operation).toHaveBeenCalled()
    expect(mockedApi.post).toHaveBeenCalledWith('/backup/snapshot', {
      table: 'rotation_templates',
      reason: 'Before bulk delete',
    })
  })

  it('should show isCreatingSnapshot during snapshot creation', async () => {
    const mockSnapshot: SnapshotResponse = mockSnapshots[0]

    mockedApi.post.mockImplementation(() =>
      new Promise(resolve => setTimeout(() => resolve(mockSnapshot), 100))
    )

    const { result } = renderHook(
      () => useWithBackup(),
      { wrapper: createWrapper() }
    )

    const operation = jest.fn().mockResolvedValue({ success: true })

    result.current.execute(
      { table: 'rotation_templates', reason: 'Test' },
      operation
    )

    await waitFor(() => {
      expect(result.current.isCreatingSnapshot).toBe(true)
    })

    await waitFor(() => {
      expect(result.current.isCreatingSnapshot).toBe(false)
    })
  })

  it('should not execute operation if snapshot fails', async () => {
    const apiError = Object.assign(
      new Error('Snapshot creation failed'),
      { status: 500 }
    )
    mockedApi.post.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useWithBackup(),
      { wrapper: createWrapper() }
    )

    const operation = jest.fn().mockResolvedValue({ success: true })

    await expect(
      result.current.execute(
        { table: 'rotation_templates', reason: 'Test' },
        operation
      )
    ).rejects.toEqual(apiError)

    expect(operation).not.toHaveBeenCalled()
  })

  it('should expose snapshot error when creation fails', async () => {
    const apiError = Object.assign(
      new Error('Disk full'),
      { status: 507 }
    )
    mockedApi.post.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useWithBackup(),
      { wrapper: createWrapper() }
    )

    const operation = jest.fn()

    try {
      await result.current.execute(
        { table: 'rotation_templates', reason: 'Test' },
        operation
      )
    } catch {
      // Expected to throw
    }

    await waitFor(() => {
      expect(result.current.snapshotError).toEqual(apiError)
    })
  })

  it('should handle operation failure after successful snapshot', async () => {
    const mockSnapshot: SnapshotResponse = mockSnapshots[0]
    const operationError = new Error('Operation failed')

    mockedApi.post.mockResolvedValueOnce(mockSnapshot)

    const { result } = renderHook(
      () => useWithBackup(),
      { wrapper: createWrapper() }
    )

    const operation = jest.fn().mockRejectedValue(operationError)

    await expect(
      result.current.execute(
        { table: 'rotation_templates', reason: 'Test' },
        operation
      )
    ).rejects.toEqual(operationError)

    // Snapshot should have been created
    expect(mockedApi.post).toHaveBeenCalledWith('/backup/snapshot', {
      table: 'rotation_templates',
      reason: 'Test',
    })
    expect(operation).toHaveBeenCalled()
  })
})
