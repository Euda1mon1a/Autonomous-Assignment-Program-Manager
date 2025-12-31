/**
 * Tests for useSwaps hooks
 * Tests swap request management, approvals, rejections, and auto-matching
 */
import { renderHook, waitFor, act } from '@/test-utils'
import {
  useSwapRequest,
  useSwapList,
  useSwapCandidates,
  useSwapCreate,
  useSwapApprove,
  useSwapReject,
  useAutoMatch,
  SwapStatus,
  SwapType,
  type SwapRequest,
  type SwapCandidate,
} from '@/hooks/useSwaps'
import { createWrapper } from '../utils/test-utils'
import * as api from '@/lib/api'

// Mock the api module
jest.mock('@/lib/api', () => ({
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  del: jest.fn(),
}))

const mockedApi = api as jest.Mocked<typeof api>

// ============================================================================
// Mock Data Factories
// ============================================================================

const createMockSwapRequest = (overrides?: Partial<SwapRequest>): SwapRequest => ({
  id: 'swap-123',
  source_faculty_id: 'faculty-1',
  source_faculty_name: 'Dr. Smith',
  source_week: '2024-03-01',
  target_faculty_id: 'faculty-2',
  target_faculty_name: 'Dr. Jones',
  target_week: '2024-03-08',
  swap_type: SwapType.ONE_TO_ONE,
  status: SwapStatus.PENDING,
  requested_at: '2024-02-15T10:00:00Z',
  requested_by_id: 'faculty-1',
  reason: 'Family emergency',
  ...overrides,
})

const createMockSwapCandidate = (overrides?: Partial<SwapCandidate>): SwapCandidate => ({
  faculty_id: 'faculty-3',
  faculty_name: 'Dr. Johnson',
  available_weeks: ['2024-03-01', '2024-03-08'],
  compatibility_score: 0.95,
  constraints_met: true,
  ...overrides,
})

// ============================================================================
// Query Hook Tests
// ============================================================================

describe('useSwapRequest', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch single swap request by ID', async () => {
    const mockSwap = createMockSwapRequest()
    mockedApi.get.mockResolvedValueOnce(mockSwap)

    const { result } = renderHook(
      () => useSwapRequest('swap-123'),
      { wrapper: createWrapper() }
    )

    expect(result.current.isLoading).toBe(true)

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith('/swaps/swap-123')
    expect(result.current.data).toEqual(mockSwap)
  })

  it('should handle API errors gracefully', async () => {
    const apiError = { message: 'Swap not found', status: 404 }
    mockedApi.get.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useSwapRequest('nonexistent-id'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })

  it('should not fetch if ID is empty', async () => {
    const { result } = renderHook(
      () => useSwapRequest(''),
      { wrapper: createWrapper() }
    )

    // Should not fetch when ID is empty (disabled)
    expect(mockedApi.get).not.toHaveBeenCalled()
    expect(result.current.isLoading).toBe(false)
  })

  it('should refetch when swap ID changes', async () => {
    const mockSwap1 = createMockSwapRequest({ id: 'swap-1' })
    const mockSwap2 = createMockSwapRequest({ id: 'swap-2' })

    mockedApi.get
      .mockResolvedValueOnce(mockSwap1)
      .mockResolvedValueOnce(mockSwap2)

    const { result, rerender } = renderHook(
      ({ id }) => useSwapRequest(id),
      {
        wrapper: createWrapper(),
        initialProps: { id: 'swap-1' },
      }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith('/swaps/swap-1')
    expect(result.current.data?.id).toBe('swap-1')

    // Change ID
    rerender({ id: 'swap-2' })

    // Wait for the new data to be fetched and loaded
    await waitFor(() => {
      expect(mockedApi.get).toHaveBeenCalledWith('/swaps/swap-2')
    })

    await waitFor(() => {
      expect(result.current.data?.id).toBe('swap-2')
    })
  })
})

describe('useSwapList', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch list of swap requests', async () => {
    const mockResponse = {
      items: [
        createMockSwapRequest({ id: 'swap-1' }),
        createMockSwapRequest({ id: 'swap-2' }),
      ],
      total: 2,
    }
    mockedApi.get.mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(
      () => useSwapList(),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith('/swaps')
    expect(result.current.data).toEqual(mockResponse)
    expect(result.current.data?.items).toHaveLength(2)
  })

  it('should apply status filters', async () => {
    const mockResponse = {
      items: [createMockSwapRequest({ status: SwapStatus.PENDING })],
      total: 1,
    }
    mockedApi.get.mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(
      () => useSwapList({ status: [SwapStatus.PENDING] }),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith('/swaps?status=pending')
  })

  it('should apply multiple filters', async () => {
    const mockResponse = { items: [], total: 0 }
    mockedApi.get.mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(
      () => useSwapList({
        status: [SwapStatus.PENDING, SwapStatus.APPROVED],
        swap_type: [SwapType.ONE_TO_ONE],
        source_faculty_id: 'faculty-123',
        start_date: '2024-01-01',
        end_date: '2024-12-31',
      }),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    // Check that URL contains expected parameters
    const calledUrl = mockedApi.get.mock.calls[0][0]
    expect(calledUrl).toContain('status=pending')
    expect(calledUrl).toContain('status=approved')
    expect(calledUrl).toContain('swap_type=one_to_one')
    expect(calledUrl).toContain('source_faculty_id=faculty-123')
    expect(calledUrl).toContain('start_date=2024-01-01')
    expect(calledUrl).toContain('end_date=2024-12-31')
  })

  it('should handle empty results', async () => {
    const mockResponse = { items: [], total: 0 }
    mockedApi.get.mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(
      () => useSwapList({ status: [SwapStatus.EXECUTED] }),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.items).toEqual([])
    expect(result.current.data?.total).toBe(0)
  })
})

describe('useSwapCandidates', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch swap candidates for source faculty and week', async () => {
    const mockResponse = {
      items: [
        createMockSwapCandidate({ faculty_id: 'faculty-1' }),
        createMockSwapCandidate({ faculty_id: 'faculty-2' }),
      ],
      total: 2,
    }
    mockedApi.get.mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(
      () => useSwapCandidates('faculty-123', '2024-03-01'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith(
      '/swaps/candidates?source_faculty_id=faculty-123&source_week=2024-03-01'
    )
    expect(result.current.data?.items).toHaveLength(2)
  })

  it('should not fetch if parameters are missing', async () => {
    const { result } = renderHook(
      () => useSwapCandidates('', '2024-03-01'),
      { wrapper: createWrapper() }
    )

    expect(mockedApi.get).not.toHaveBeenCalled()
    expect(result.current.isLoading).toBe(false)
  })

  it('should return candidates sorted by compatibility score', async () => {
    const mockResponse = {
      items: [
        createMockSwapCandidate({
          faculty_id: 'faculty-1',
          compatibility_score: 0.95
        }),
        createMockSwapCandidate({
          faculty_id: 'faculty-2',
          compatibility_score: 0.80
        }),
      ],
      total: 2,
    }
    mockedApi.get.mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(
      () => useSwapCandidates('faculty-123', '2024-03-01'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    const candidates = result.current.data?.items || []
    expect(candidates[0].compatibility_score).toBe(0.95)
    expect(candidates[1].compatibility_score).toBe(0.80)
  })
})

// ============================================================================
// Mutation Hook Tests
// ============================================================================

describe('useSwapCreate', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should create one-to-one swap request', async () => {
    const mockResponse = {
      success: true,
      request_id: 'swap-new-123',
      message: 'Swap request created successfully',
      candidates_notified: 1,
    }
    mockedApi.post.mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(
      () => useSwapCreate(),
      { wrapper: createWrapper() }
    )

    const swapRequest = {
      source_faculty_id: 'faculty-1',
      source_week: '2024-03-01',
      target_faculty_id: 'faculty-2',
      target_week: '2024-03-08',
      swap_type: SwapType.ONE_TO_ONE,
      reason: 'Family emergency',
    }

    await act(async () => {
      result.current.mutate(swapRequest)
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.post).toHaveBeenCalledWith('/swaps', swapRequest)
    expect(result.current.data).toEqual(mockResponse)
  })

  it('should create absorb swap with auto-matching', async () => {
    const mockResponse = {
      success: true,
      request_id: 'swap-absorb-456',
      message: 'Swap request created with auto-matching',
      candidates_notified: 5,
    }
    mockedApi.post.mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(
      () => useSwapCreate(),
      { wrapper: createWrapper() }
    )

    const swapRequest = {
      source_faculty_id: 'faculty-1',
      source_week: '2024-03-01',
      swap_type: SwapType.ABSORB,
      auto_match: true,
    }

    await act(async () => {
      result.current.mutate(swapRequest)
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.candidates_notified).toBe(5)
  })

  it('should handle creation errors', async () => {
    const apiError = {
      message: 'Cannot create swap: ACGME violation',
      status: 409
    }
    mockedApi.post.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useSwapCreate(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate({
        source_faculty_id: 'faculty-1',
        source_week: '2024-03-01',
        swap_type: SwapType.ABSORB,
      })
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })
})

describe('useSwapApprove', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should approve swap request', async () => {
    const mockResponse = {
      success: true,
      message: 'Swap request approved',
      swap_id: 'swap-123',
    }
    mockedApi.post.mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(
      () => useSwapApprove(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate({
        swap_id: 'swap-123',
        notes: 'Coverage confirmed',
      })
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.post).toHaveBeenCalledWith(
      '/swaps/swap-123/approve',
      { notes: 'Coverage confirmed' }
    )
    expect(result.current.data).toEqual(mockResponse)
  })

  it('should handle approval conflicts', async () => {
    const apiError = {
      message: 'Cannot approve: creates ACGME violation',
      status: 409,
    }
    mockedApi.post.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useSwapApprove(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate({
        swap_id: 'swap-123',
      })
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error?.status).toBe(409)
  })
})

describe('useSwapReject', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should reject swap request', async () => {
    const mockResponse = {
      success: true,
      message: 'Swap request rejected',
      swap_id: 'swap-123',
    }
    mockedApi.post.mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(
      () => useSwapReject(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate({
        swap_id: 'swap-123',
        reason: 'No coverage available',
        notes: 'Checked all options',
      })
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.post).toHaveBeenCalledWith(
      '/swaps/swap-123/reject',
      {
        notes: 'Checked all options',
        reason: 'No coverage available',
      }
    )
    expect(result.current.data).toEqual(mockResponse)
  })

  it('should allow rejection without reason', async () => {
    const mockResponse = {
      success: true,
      message: 'Swap request rejected',
      swap_id: 'swap-456',
    }
    mockedApi.post.mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(
      () => useSwapReject(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate({
        swap_id: 'swap-456',
      })
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.post).toHaveBeenCalledWith(
      '/swaps/swap-456/reject',
      {}
    )
  })
})

describe('useAutoMatch', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should find compatible candidates via auto-matching', async () => {
    const mockResponse = {
      success: true,
      candidates: [
        createMockSwapCandidate({ faculty_id: 'faculty-1', compatibility_score: 0.95 }),
        createMockSwapCandidate({ faculty_id: 'faculty-2', compatibility_score: 0.85 }),
        createMockSwapCandidate({ faculty_id: 'faculty-3', compatibility_score: 0.75 }),
      ],
      total_candidates: 3,
      message: 'Found 3 compatible candidates',
    }
    mockedApi.post.mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(
      () => useAutoMatch(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate({
        source_faculty_id: 'faculty-123',
        source_week: '2024-03-01',
        max_candidates: 10,
        prefer_one_to_one: true,
      })
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.post).toHaveBeenCalledWith('/swaps/auto-match', {
      source_faculty_id: 'faculty-123',
      source_week: '2024-03-01',
      max_candidates: 10,
      prefer_one_to_one: true,
    })
    expect(result.current.data?.total_candidates).toBe(3)
    expect(result.current.data?.candidates).toHaveLength(3)
  })

  it('should handle no candidates found', async () => {
    const mockResponse = {
      success: true,
      candidates: [],
      total_candidates: 0,
      message: 'No compatible candidates found',
    }
    mockedApi.post.mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(
      () => useAutoMatch(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate({
        source_faculty_id: 'faculty-999',
        source_week: '2024-12-25',
      })
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.total_candidates).toBe(0)
    expect(result.current.data?.candidates).toEqual([])
  })

  it('should handle auto-match errors', async () => {
    const apiError = {
      message: 'Auto-match failed: invalid week',
      status: 400,
    }
    mockedApi.post.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useAutoMatch(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      result.current.mutate({
        source_faculty_id: 'faculty-123',
        source_week: 'invalid-date',
      })
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(apiError)
  })
})

// ============================================================================
// Integration Tests
// ============================================================================

describe('Swap workflow integration', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should support complete swap creation and approval flow', async () => {
    // Step 1: Create swap
    const createResponse = {
      success: true,
      request_id: 'swap-new',
      message: 'Swap created',
    }
    mockedApi.post.mockResolvedValueOnce(createResponse)

    const { result: createResult } = renderHook(
      () => useSwapCreate(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      createResult.current.mutate({
        source_faculty_id: 'faculty-1',
        source_week: '2024-03-01',
        swap_type: SwapType.ABSORB,
      })
    })

    await waitFor(() => {
      expect(createResult.current.isSuccess).toBe(true)
    })

    const swapId = createResult.current.data?.request_id

    // Step 2: Fetch created swap
    const mockSwap = createMockSwapRequest({ id: swapId })
    mockedApi.get.mockResolvedValueOnce(mockSwap)

    const { result: fetchResult } = renderHook(
      () => useSwapRequest(swapId!),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(fetchResult.current.isSuccess).toBe(true)
    })

    // Step 3: Approve swap
    const approveResponse = {
      success: true,
      message: 'Swap approved',
      swap_id: swapId!,
    }
    mockedApi.post.mockResolvedValueOnce(approveResponse)

    const { result: approveResult } = renderHook(
      () => useSwapApprove(),
      { wrapper: createWrapper() }
    )

    await act(async () => {
      approveResult.current.mutate({
        swap_id: swapId!,
        notes: 'Approved',
      })
    })

    await waitFor(() => {
      expect(approveResult.current.isSuccess).toBe(true)
    })

    expect(approveResult.current.data?.success).toBe(true)
  })
})
