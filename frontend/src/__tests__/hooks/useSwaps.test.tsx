/**
 * useSwaps Hook Tests
 *
 * Tests for swap management hooks including list queries, single swap queries,
 * candidate queries, and mutations for creating, approving, rejecting, executing,
 * and rolling back swaps.
 */
import { renderHook, waitFor } from '@/test-utils'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactNode } from 'react'
import * as api from '@/lib/api'
import {
  useSwapRequest,
  useSwapList,
  useSwapCandidates,
  useSwapCreate,
  useSwapApprove,
  useSwapReject,
  useAutoMatch,
  useValidateSwap,
  useExecuteSwap,
  useRollbackSwap,
  SwapStatus,
  SwapType,
  type SwapRequest,
  type SwapCandidate,
  type SwapCreateRequest,
  type SwapCreateResponse,
  type SwapActionResponse,
  type SwapApproveRequest,
  type SwapRejectRequest,
  type AutoMatchRequest,
  type AutoMatchResponse,
  type SwapExecuteRequest,
  type SwapExecuteResponse,
  type SwapValidationResult,
  type SwapRollbackRequest,
  type SwapRollbackResponse,
  type ListResponse,
} from '@/hooks/useSwaps'

// Mock the api module
jest.mock('@/lib/api')

const mockedApi = api as jest.Mocked<typeof api>

// Mock data
const mockSwapRequest: SwapRequest = {
  id: 'swap-123',
  sourceFacultyId: 'faculty-1',
  sourceFacultyName: 'Dr. Smith',
  sourceWeek: '2024-03-01',
  targetFacultyId: 'faculty-2',
  targetFacultyName: 'Dr. Jones',
  targetWeek: '2024-03-08',
  swapType: SwapType.ONE_TO_ONE,
  status: SwapStatus.PENDING,
  requestedAt: '2024-02-01T10:00:00Z',
  requestedById: 'user-1',
  reason: 'Family emergency',
}

const mockApprovedSwap: SwapRequest = {
  ...mockSwapRequest,
  id: 'swap-456',
  status: SwapStatus.APPROVED,
  approved_at: '2024-02-02T10:00:00Z',
  approved_by_id: 'admin-1',
}

const mockSwapListResponse: ListResponse<SwapRequest> = {
  items: [mockSwapRequest, mockApprovedSwap],
  total: 2,
}

const mockSwapCandidate: SwapCandidate = {
  facultyId: 'faculty-3',
  facultyName: 'Dr. Wilson',
  available_weeks: ['2024-03-08', '2024-03-15'],
  compatibility_score: 0.85,
  constraints_met: true,
  reason: 'Good match',
}

const mockCandidatesResponse: ListResponse<SwapCandidate> = {
  items: [mockSwapCandidate],
  total: 1,
}

const mockSwapCreateResponse: SwapCreateResponse = {
  success: true,
  requestId: 'swap-789',
  message: 'Swap request created',
  candidatesNotified: 3,
}

const mockSwapActionResponse: SwapActionResponse = {
  success: true,
  message: 'Swap approved',
  swapId: 'swap-123',
}

const mockAutoMatchResponse: AutoMatchResponse = {
  success: true,
  candidates: [mockSwapCandidate],
  total_candidates: 1,
  message: 'Found 1 compatible candidate',
}

const mockValidationResult: SwapValidationResult = {
  valid: true,
  errors: [],
  warnings: [],
  backToBackConflict: false,
}

const mockSwapExecuteResponse: SwapExecuteResponse = {
  success: true,
  swapId: 'swap-999',
  message: 'Swap executed successfully',
  validation: mockValidationResult,
}

const mockSwapRollbackResponse: SwapRollbackResponse = {
  success: true,
  message: 'Swap rolled back',
  swapId: 'swap-123',
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

describe('useSwapRequest', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch a single swap request successfully', async () => {
    mockedApi.get.mockResolvedValueOnce(mockSwapRequest)

    const { result } = renderHook(
      () => useSwapRequest('swap-123'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockSwapRequest)
    expect(result.current.data?.sourceFacultyName).toBe('Dr. Smith')
    expect(mockedApi.get).toHaveBeenCalledWith('/swaps/swap-123')
  })

  it('should show loading state while fetching', async () => {
    mockedApi.get.mockResolvedValueOnce(mockSwapRequest)

    const { result } = renderHook(
      () => useSwapRequest('swap-123'),
      { wrapper: createWrapper() }
    )

    expect(result.current.isLoading).toBe(true)

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })
  })

  it('should handle error when fetching swap', async () => {
    const error = Object.assign(new Error('Not found'), { status: 404 })
    mockedApi.get.mockRejectedValueOnce(error)

    const { result } = renderHook(
      () => useSwapRequest('swap-999'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(error)
  })

  it('should respect enabled flag', async () => {
    const { result } = renderHook(
      () => useSwapRequest('swap-123', { enabled: false }),
      { wrapper: createWrapper() }
    )

    expect(result.current.isFetching).toBe(false)
    expect(mockedApi.get).not.toHaveBeenCalled()
  })

  it('should not fetch when id is empty', async () => {
    const { result } = renderHook(
      () => useSwapRequest(''),
      { wrapper: createWrapper() }
    )

    expect(result.current.isFetching).toBe(false)
    expect(mockedApi.get).not.toHaveBeenCalled()
  })
})

describe('useSwapList', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch swap list without filters', async () => {
    mockedApi.get.mockResolvedValueOnce(mockSwapListResponse)

    const { result } = renderHook(
      () => useSwapList(),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockSwapListResponse)
    expect(result.current.data?.items).toHaveLength(2)
    expect(result.current.data?.total).toBe(2)
    expect(mockedApi.get).toHaveBeenCalledWith('/swaps')
  })

  it('should fetch swap list with status filter', async () => {
    mockedApi.get.mockResolvedValueOnce(mockSwapListResponse)

    const { result } = renderHook(
      () => useSwapList({ status: [SwapStatus.PENDING] }),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith('/swaps?status=pending')
  })

  it('should fetch swap list with multiple filters', async () => {
    mockedApi.get.mockResolvedValueOnce(mockSwapListResponse)

    const { result } = renderHook(
      () => useSwapList({
        status: [SwapStatus.PENDING, SwapStatus.APPROVED],
        swapType: [SwapType.ONE_TO_ONE],
        sourceFacultyId: 'faculty-1',
        startDate: '2024-01-01',
        endDate: '2024-12-31',
      }),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith(
      expect.stringContaining('/swaps?')
    )
    const call = mockedApi.get.mock.calls[0][0]
    expect(call).toContain('status=pending')
    expect(call).toContain('status=approved')
    expect(call).toContain('swap_type=one_to_one')
    expect(call).toContain('source_faculty_id=faculty-1')
    expect(call).toContain('start_date=2024-01-01')
    expect(call).toContain('end_date=2024-12-31')
  })

  it('should handle error when fetching swap list', async () => {
    const error = Object.assign(new Error('Server error'), { status: 500 })
    mockedApi.get.mockRejectedValueOnce(error)

    const { result } = renderHook(
      () => useSwapList(),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(error)
  })

  it('should respect enabled flag', async () => {
    const { result } = renderHook(
      () => useSwapList(undefined, { enabled: false }),
      { wrapper: createWrapper() }
    )

    expect(result.current.isFetching).toBe(false)
    expect(mockedApi.get).not.toHaveBeenCalled()
  })
})

describe('useSwapCandidates', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch swap candidates successfully', async () => {
    mockedApi.get.mockResolvedValueOnce(mockCandidatesResponse)

    const { result } = renderHook(
      () => useSwapCandidates('faculty-1', '2024-03-01'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockCandidatesResponse)
    expect(result.current.data?.items[0].facultyName).toBe('Dr. Wilson')
    expect(mockedApi.get).toHaveBeenCalledWith(
      '/swaps/candidates?source_faculty_id=faculty-1&source_week=2024-03-01'
    )
  })

  it('should not fetch when sourceId is empty', async () => {
    const { result } = renderHook(
      () => useSwapCandidates('', '2024-03-01'),
      { wrapper: createWrapper() }
    )

    expect(result.current.isFetching).toBe(false)
    expect(mockedApi.get).not.toHaveBeenCalled()
  })

  it('should not fetch when sourceWeek is empty', async () => {
    const { result } = renderHook(
      () => useSwapCandidates('faculty-1', ''),
      { wrapper: createWrapper() }
    )

    expect(result.current.isFetching).toBe(false)
    expect(mockedApi.get).not.toHaveBeenCalled()
  })

  it('should handle error when fetching candidates', async () => {
    const error = Object.assign(new Error('No candidates found'), { status: 404 })
    mockedApi.get.mockRejectedValueOnce(error)

    const { result } = renderHook(
      () => useSwapCandidates('faculty-1', '2024-03-01'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(error)
  })

  it('should respect enabled flag', async () => {
    const { result } = renderHook(
      () => useSwapCandidates('faculty-1', '2024-03-01', { enabled: false }),
      { wrapper: createWrapper() }
    )

    expect(result.current.isFetching).toBe(false)
    expect(mockedApi.get).not.toHaveBeenCalled()
  })
})

describe('useSwapCreate', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should create a swap request successfully', async () => {
    mockedApi.post.mockResolvedValueOnce(mockSwapCreateResponse)

    const { result } = renderHook(
      () => useSwapCreate(),
      { wrapper: createWrapper() }
    )

    const createRequest: SwapCreateRequest = {
      sourceFacultyId: 'faculty-1',
      sourceWeek: '2024-03-01',
      targetFacultyId: 'faculty-2',
      targetWeek: '2024-03-08',
      swapType: SwapType.ONE_TO_ONE,
      reason: 'Family emergency',
    }

    result.current.mutate(createRequest)

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockSwapCreateResponse)
    expect(mockedApi.post).toHaveBeenCalledWith('/swaps', createRequest)
  })

  it('should create absorb swap with auto-match', async () => {
    mockedApi.post.mockResolvedValueOnce(mockSwapCreateResponse)

    const { result } = renderHook(
      () => useSwapCreate(),
      { wrapper: createWrapper() }
    )

    const createRequest: SwapCreateRequest = {
      sourceFacultyId: 'faculty-1',
      sourceWeek: '2024-03-01',
      swapType: SwapType.ABSORB,
      auto_match: true,
    }

    result.current.mutate(createRequest)

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.post).toHaveBeenCalledWith('/swaps', createRequest)
  })

  it('should handle error when creating swap', async () => {
    const error = Object.assign(new Error('Conflict detected'), { status: 409 })
    mockedApi.post.mockRejectedValueOnce(error)

    const { result } = renderHook(
      () => useSwapCreate(),
      { wrapper: createWrapper() }
    )

    const createRequest: SwapCreateRequest = {
      sourceFacultyId: 'faculty-1',
      sourceWeek: '2024-03-01',
      swapType: SwapType.ABSORB,
    }

    result.current.mutate(createRequest)

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(error)
  })
})

describe('useSwapApprove', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should approve a swap successfully', async () => {
    mockedApi.post.mockResolvedValueOnce(mockSwapActionResponse)

    const { result } = renderHook(
      () => useSwapApprove(),
      { wrapper: createWrapper() }
    )

    const approveRequest: SwapApproveRequest = {
      swapId: 'swap-123',
      notes: 'Approved - coverage confirmed',
    }

    result.current.mutate(approveRequest)

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockSwapActionResponse)
    expect(mockedApi.post).toHaveBeenCalledWith(
      '/swaps/swap-123/approve',
      { notes: 'Approved - coverage confirmed' }
    )
  })

  it('should approve swap without notes', async () => {
    mockedApi.post.mockResolvedValueOnce(mockSwapActionResponse)

    const { result } = renderHook(
      () => useSwapApprove(),
      { wrapper: createWrapper() }
    )

    const approveRequest: SwapApproveRequest = {
      swapId: 'swap-123',
    }

    result.current.mutate(approveRequest)

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.post).toHaveBeenCalledWith(
      '/swaps/swap-123/approve',
      { notes: undefined }
    )
  })

  it('should handle ACGME violation error', async () => {
    const error = Object.assign(new Error('ACGME violation'), { status: 409 })
    mockedApi.post.mockRejectedValueOnce(error)

    const { result } = renderHook(
      () => useSwapApprove(),
      { wrapper: createWrapper() }
    )

    const approveRequest: SwapApproveRequest = {
      swapId: 'swap-123',
    }

    result.current.mutate(approveRequest)

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(error)
  })
})

describe('useSwapReject', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should reject a swap successfully', async () => {
    mockedApi.post.mockResolvedValueOnce({
      ...mockSwapActionResponse,
      message: 'Swap rejected',
    })

    const { result } = renderHook(
      () => useSwapReject(),
      { wrapper: createWrapper() }
    )

    const rejectRequest: SwapRejectRequest = {
      swapId: 'swap-123',
      reason: 'Coverage not available',
      notes: 'Unable to find replacement',
    }

    result.current.mutate(rejectRequest)

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.post).toHaveBeenCalledWith(
      '/swaps/swap-123/reject',
      { notes: 'Unable to find replacement', reason: 'Coverage not available' }
    )
  })

  it('should reject swap with only reason', async () => {
    mockedApi.post.mockResolvedValueOnce({
      ...mockSwapActionResponse,
      message: 'Swap rejected',
    })

    const { result } = renderHook(
      () => useSwapReject(),
      { wrapper: createWrapper() }
    )

    const rejectRequest: SwapRejectRequest = {
      swapId: 'swap-123',
      reason: 'Policy violation',
    }

    result.current.mutate(rejectRequest)

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.post).toHaveBeenCalledWith(
      '/swaps/swap-123/reject',
      { notes: undefined, reason: 'Policy violation' }
    )
  })

  it('should handle error when rejecting swap', async () => {
    const error = Object.assign(new Error('Already processed'), { status: 400 })
    mockedApi.post.mockRejectedValueOnce(error)

    const { result } = renderHook(
      () => useSwapReject(),
      { wrapper: createWrapper() }
    )

    const rejectRequest: SwapRejectRequest = {
      swapId: 'swap-123',
      reason: 'Test',
    }

    result.current.mutate(rejectRequest)

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(error)
  })
})

describe('useAutoMatch', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should perform auto-match successfully', async () => {
    mockedApi.post.mockResolvedValueOnce(mockAutoMatchResponse)

    const { result } = renderHook(
      () => useAutoMatch(),
      { wrapper: createWrapper() }
    )

    const matchRequest: AutoMatchRequest = {
      sourceFacultyId: 'faculty-1',
      sourceWeek: '2024-03-01',
      max_candidates: 10,
      prefer_oneToOne: true,
    }

    result.current.mutate(matchRequest)

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockAutoMatchResponse)
    expect(mockedApi.post).toHaveBeenCalledWith('/swaps/auto-match', matchRequest)
  })

  it('should auto-match with minimal params', async () => {
    mockedApi.post.mockResolvedValueOnce(mockAutoMatchResponse)

    const { result } = renderHook(
      () => useAutoMatch(),
      { wrapper: createWrapper() }
    )

    const matchRequest: AutoMatchRequest = {
      sourceFacultyId: 'faculty-1',
      sourceWeek: '2024-03-01',
    }

    result.current.mutate(matchRequest)

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.post).toHaveBeenCalledWith('/swaps/auto-match', matchRequest)
  })

  it('should handle no candidates found', async () => {
    const noCandidatesResponse: AutoMatchResponse = {
      success: true,
      candidates: [],
      total_candidates: 0,
      message: 'No compatible candidates found',
    }
    mockedApi.post.mockResolvedValueOnce(noCandidatesResponse)

    const { result } = renderHook(
      () => useAutoMatch(),
      { wrapper: createWrapper() }
    )

    const matchRequest: AutoMatchRequest = {
      sourceFacultyId: 'faculty-1',
      sourceWeek: '2024-03-01',
    }

    result.current.mutate(matchRequest)

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.total_candidates).toBe(0)
  })

  it('should handle auto-match error', async () => {
    const error = Object.assign(new Error('Validation failed'), { status: 422 })
    mockedApi.post.mockRejectedValueOnce(error)

    const { result } = renderHook(
      () => useAutoMatch(),
      { wrapper: createWrapper() }
    )

    const matchRequest: AutoMatchRequest = {
      sourceFacultyId: 'faculty-1',
      sourceWeek: '2024-03-01',
    }

    result.current.mutate(matchRequest)

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(error)
  })
})

describe('useValidateSwap', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should validate a swap successfully', async () => {
    mockedApi.post.mockResolvedValueOnce(mockValidationResult)

    const { result } = renderHook(
      () => useValidateSwap(),
      { wrapper: createWrapper() }
    )

    const validateRequest: SwapExecuteRequest = {
      sourceFacultyId: 'faculty-1',
      sourceWeek: '2024-03-01',
      targetFacultyId: 'faculty-2',
      targetWeek: '2024-03-08',
      swapType: SwapType.ONE_TO_ONE,
    }

    result.current.mutate(validateRequest)

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockValidationResult)
    expect(result.current.data?.valid).toBe(true)
    expect(mockedApi.post).toHaveBeenCalledWith('/swaps/validate', validateRequest)
  })

  it('should handle validation with errors', async () => {
    const validationWithErrors: SwapValidationResult = {
      valid: false,
      errors: ['Back-to-back shift violation'],
      warnings: ['High workload for target'],
      backToBackConflict: true,
    }
    mockedApi.post.mockResolvedValueOnce(validationWithErrors)

    const { result } = renderHook(
      () => useValidateSwap(),
      { wrapper: createWrapper() }
    )

    const validateRequest: SwapExecuteRequest = {
      sourceFacultyId: 'faculty-1',
      sourceWeek: '2024-03-01',
      targetFacultyId: 'faculty-2',
      swapType: SwapType.ABSORB,
    }

    result.current.mutate(validateRequest)

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.valid).toBe(false)
    expect(result.current.data?.errors).toHaveLength(1)
    expect(result.current.data?.backToBackConflict).toBe(true)
  })
})

describe('useExecuteSwap', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should execute a swap successfully', async () => {
    mockedApi.post.mockResolvedValueOnce(mockSwapExecuteResponse)

    const { result } = renderHook(
      () => useExecuteSwap(),
      { wrapper: createWrapper() }
    )

    const executeRequest: SwapExecuteRequest = {
      sourceFacultyId: 'faculty-1',
      sourceWeek: '2024-03-01',
      targetFacultyId: 'faculty-2',
      targetWeek: '2024-03-08',
      swapType: SwapType.ONE_TO_ONE,
      reason: 'Admin force swap',
    }

    result.current.mutate(executeRequest)

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockSwapExecuteResponse)
    expect(result.current.data?.success).toBe(true)
    expect(mockedApi.post).toHaveBeenCalledWith('/swaps/execute', executeRequest)
  })

  it('should execute absorb swap', async () => {
    mockedApi.post.mockResolvedValueOnce(mockSwapExecuteResponse)

    const { result } = renderHook(
      () => useExecuteSwap(),
      { wrapper: createWrapper() }
    )

    const executeRequest: SwapExecuteRequest = {
      sourceFacultyId: 'faculty-1',
      sourceWeek: '2024-03-01',
      targetFacultyId: 'faculty-2',
      swapType: SwapType.ABSORB,
    }

    result.current.mutate(executeRequest)

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.post).toHaveBeenCalledWith('/swaps/execute', executeRequest)
  })

  it('should handle execution error', async () => {
    const error = Object.assign(new Error('Validation failed'), { status: 422 })
    mockedApi.post.mockRejectedValueOnce(error)

    const { result } = renderHook(
      () => useExecuteSwap(),
      { wrapper: createWrapper() }
    )

    const executeRequest: SwapExecuteRequest = {
      sourceFacultyId: 'faculty-1',
      sourceWeek: '2024-03-01',
      targetFacultyId: 'faculty-2',
      swapType: SwapType.ABSORB,
    }

    result.current.mutate(executeRequest)

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(error)
  })
})

describe('useRollbackSwap', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should rollback a swap successfully', async () => {
    mockedApi.post.mockResolvedValueOnce(mockSwapRollbackResponse)

    const { result } = renderHook(
      () => useRollbackSwap(),
      { wrapper: createWrapper() }
    )

    const rollbackRequest: SwapRollbackRequest = {
      swapId: 'swap-123',
      reason: 'Executed in error',
    }

    result.current.mutate(rollbackRequest)

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockSwapRollbackResponse)
    expect(mockedApi.post).toHaveBeenCalledWith(
      '/swaps/swap-123/rollback',
      { reason: 'Executed in error' }
    )
  })

  it('should handle rollback error when outside window', async () => {
    const error = Object.assign(new Error('Rollback window expired'), { status: 400 })
    mockedApi.post.mockRejectedValueOnce(error)

    const { result } = renderHook(
      () => useRollbackSwap(),
      { wrapper: createWrapper() }
    )

    const rollbackRequest: SwapRollbackRequest = {
      swapId: 'swap-123',
      reason: 'Test',
    }

    result.current.mutate(rollbackRequest)

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(error)
  })
})

describe('useCancelSwap', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should cancel a pending swap successfully', async () => {
    const cancelResponse: SwapActionResponse = {
      success: true,
      message: 'Swap cancelled',
      swapId: 'swap-123',
    }
    mockedApi.post.mockResolvedValueOnce(cancelResponse)

    const { result } = renderHook(
      () => useSwapReject(),
      { wrapper: createWrapper() }
    )

    const cancelRequest: SwapRejectRequest = {
      swapId: 'swap-123',
      reason: 'No longer needed',
    }

    result.current.mutate(cancelRequest)

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.post).toHaveBeenCalled()
  })
})
