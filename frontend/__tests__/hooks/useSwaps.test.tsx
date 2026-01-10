/**
 * Tests for useSwaps hook
 * Tests swap request management, approvals, rejections, and auto-matching
 */
import { renderHook, waitFor, act } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
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
} from '@/hooks/useSwaps'
import * as api from '@/lib/api'
import React from 'react'

// Mock API module
jest.mock('@/lib/api')

const mockedApi = api as jest.Mocked<typeof api>

// Create wrapper with QueryClient
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('useSwapRequest', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Initial State', () => {
    it('should initialize with loading state', () => {
      mockedApi.get.mockImplementation(() => new Promise(() => {}))

      const { result } = renderHook(() => useSwapRequest('swap-123'), {
        wrapper: createWrapper(),
      })

      expect(result.current.isLoading).toBe(true)
      expect(result.current.data).toBeUndefined()
      expect(result.current.error).toBeNull()
    })

    it('should not fetch when id is empty', () => {
      const { result } = renderHook(() => useSwapRequest(''), {
        wrapper: createWrapper(),
      })

      expect(result.current.isLoading).toBe(false)
      expect(mockedApi.get).not.toHaveBeenCalled()
    })
  })

  describe('Success Scenarios', () => {
    it('should fetch swap request successfully', async () => {
      const mockSwap = {
        id: 'swap-123',
        sourceFacultyId: 'faculty-1',
        sourceFacultyName: 'Dr. Smith',
        sourceWeek: '2024-01-01',
        swapType: SwapType.ONE_TO_ONE,
        status: SwapStatus.PENDING,
        requestedAt: '2024-01-01T10:00:00Z',
      }

      mockedApi.get.mockResolvedValue(mockSwap)

      const { result } = renderHook(() => useSwapRequest('swap-123'), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data).toEqual(mockSwap)
      expect(mockedApi.get).toHaveBeenCalledWith('/swaps/swap-123')
    })

    it('should fetch swap with target faculty', async () => {
      const mockSwap = {
        id: 'swap-123',
        sourceFacultyId: 'faculty-1',
        sourceFacultyName: 'Dr. Smith',
        sourceWeek: '2024-01-01',
        targetFacultyId: 'faculty-2',
        targetFacultyName: 'Dr. Jones',
        targetWeek: '2024-01-08',
        swapType: SwapType.ONE_TO_ONE,
        status: SwapStatus.APPROVED,
        requestedAt: '2024-01-01T10:00:00Z',
        approved_at: '2024-01-02T10:00:00Z',
      }

      mockedApi.get.mockResolvedValue(mockSwap)

      const { result } = renderHook(() => useSwapRequest('swap-123'), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data?.targetFacultyId).toBe('faculty-2')
      expect(result.current.data?.status).toBe(SwapStatus.APPROVED)
    })
  })

  describe('Error Handling', () => {
    it('should handle fetch errors', async () => {
      const error = { message: 'Swap not found', status: 404 }
      mockedApi.get.mockRejectedValue(error)

      const { result } = renderHook(() => useSwapRequest('swap-123'), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error).toEqual(error)
    })

    it('should handle unauthorized errors', async () => {
      const error = { message: 'Unauthorized', status: 401 }
      mockedApi.get.mockRejectedValue(error)

      const { result } = renderHook(() => useSwapRequest('swap-123'), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error?.status).toBe(401)
    })
  })

  describe('Loading States', () => {
    it('should show loading during fetch', async () => {
      let resolvePromise: (value: any) => void
      const promise = new Promise((resolve) => {
        resolvePromise = resolve
      })

      mockedApi.get.mockReturnValue(promise as any)

      const { result } = renderHook(() => useSwapRequest('swap-123'), {
        wrapper: createWrapper(),
      })

      expect(result.current.isLoading).toBe(true)
      expect(result.current.isFetching).toBe(true)

      act(() => {
        resolvePromise!({
          id: 'swap-123',
          sourceFacultyId: 'faculty-1',
          status: SwapStatus.PENDING,
        })
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })
    })
  })

  describe('Edge Cases', () => {
    it('should handle absorb swap type', async () => {
      const mockSwap = {
        id: 'swap-123',
        sourceFacultyId: 'faculty-1',
        sourceFacultyName: 'Dr. Smith',
        sourceWeek: '2024-01-01',
        swapType: SwapType.ABSORB,
        status: SwapStatus.PENDING,
        requestedAt: '2024-01-01T10:00:00Z',
      }

      mockedApi.get.mockResolvedValue(mockSwap)

      const { result } = renderHook(() => useSwapRequest('swap-123'), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data?.swapType).toBe(SwapType.ABSORB)
      expect(result.current.data?.targetFacultyId).toBeUndefined()
    })
  })
})

describe('useSwapList', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Success Scenarios', () => {
    it('should fetch swap list successfully', async () => {
      const mockSwaps = {
        items: [
          {
            id: 'swap-1',
            sourceFacultyId: 'faculty-1',
            status: SwapStatus.PENDING,
            swapType: SwapType.ONE_TO_ONE,
          },
          {
            id: 'swap-2',
            sourceFacultyId: 'faculty-2',
            status: SwapStatus.APPROVED,
            swapType: SwapType.ABSORB,
          },
        ],
        total: 2,
      }

      mockedApi.get.mockResolvedValue(mockSwaps)

      const { result } = renderHook(() => useSwapList(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data).toEqual(mockSwaps)
      expect(result.current.data?.items).toHaveLength(2)
    })

    it('should filter by status', async () => {
      mockedApi.get.mockResolvedValue({ items: [], total: 0 })

      const { result } = renderHook(
        () =>
          useSwapList({
            status: [SwapStatus.PENDING],
          }),
        {
          wrapper: createWrapper(),
        }
      )

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('status=pending')
      )
    })

    it('should filter by swap type', async () => {
      mockedApi.get.mockResolvedValue({ items: [], total: 0 })

      const { result } = renderHook(
        () =>
          useSwapList({
            swapType: [SwapType.ONE_TO_ONE],
          }),
        {
          wrapper: createWrapper(),
        }
      )

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('swapType=oneToOne')
      )
    })

    it('should filter by date range', async () => {
      mockedApi.get.mockResolvedValue({ items: [], total: 0 })

      const { result } = renderHook(
        () =>
          useSwapList({
            startDate: '2024-01-01',
            endDate: '2024-01-31',
          }),
        {
          wrapper: createWrapper(),
        }
      )

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('startDate=2024-01-01')
      )
    })

    it('should filter by source faculty', async () => {
      mockedApi.get.mockResolvedValue({ items: [], total: 0 })

      const { result } = renderHook(
        () =>
          useSwapList({
            sourceFacultyId: 'faculty-1',
          }),
        {
          wrapper: createWrapper(),
        }
      )

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('sourceFacultyId=faculty-1')
      )
    })
  })

  describe('Error Handling', () => {
    it('should handle fetch errors', async () => {
      const error = { message: 'Failed to fetch swaps', status: 500 }
      mockedApi.get.mockRejectedValue(error)

      const { result } = renderHook(() => useSwapList(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error).toEqual(error)
    })
  })

  describe('Edge Cases', () => {
    it('should handle empty swap list', async () => {
      mockedApi.get.mockResolvedValue({ items: [], total: 0 })

      const { result } = renderHook(() => useSwapList(), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data?.items).toEqual([])
      expect(result.current.data?.total).toBe(0)
    })
  })
})

describe('useSwapCandidates', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Success Scenarios', () => {
    it('should fetch swap candidates', async () => {
      const mockCandidates = {
        items: [
          {
            facultyId: 'faculty-2',
            facultyName: 'Dr. Jones',
            available_weeks: ['2024-01-08', '2024-01-15'],
            compatibility_score: 0.85,
            constraints_met: true,
          },
        ],
        total: 1,
      }

      mockedApi.get.mockResolvedValue(mockCandidates)

      const { result } = renderHook(
        () => useSwapCandidates('faculty-1', '2024-01-01'),
        {
          wrapper: createWrapper(),
        }
      )

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data).toEqual(mockCandidates)
      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('sourceFacultyId=faculty-1')
      )
    })

    it('should not fetch when parameters are missing', () => {
      const { result } = renderHook(() => useSwapCandidates('', ''), {
        wrapper: createWrapper(),
      })

      expect(result.current.isLoading).toBe(false)
      expect(mockedApi.get).not.toHaveBeenCalled()
    })
  })

  describe('Error Handling', () => {
    it('should handle no candidates found', async () => {
      mockedApi.get.mockResolvedValue({ items: [], total: 0 })

      const { result } = renderHook(
        () => useSwapCandidates('faculty-1', '2024-01-01'),
        {
          wrapper: createWrapper(),
        }
      )

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data?.items).toHaveLength(0)
    })
  })
})

describe('useSwapCreate', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Success Scenarios', () => {
    it('should create one-to-one swap', async () => {
      const mockResponse = {
        success: true,
        requestId: 'swap-123',
        message: 'Swap request created',
      }

      mockedApi.post.mockResolvedValue(mockResponse)

      const { result } = renderHook(() => useSwapCreate(), {
        wrapper: createWrapper(),
      })

      act(() => {
        result.current.mutate({
          sourceFacultyId: 'faculty-1',
          sourceWeek: '2024-01-01',
          targetFacultyId: 'faculty-2',
          targetWeek: '2024-01-08',
          swapType: SwapType.ONE_TO_ONE,
        })
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data).toEqual(mockResponse)
    })

    it('should create absorb swap with auto-match', async () => {
      const mockResponse = {
        success: true,
        requestId: 'swap-123',
        message: 'Swap request created',
        candidatesNotified: 5,
      }

      mockedApi.post.mockResolvedValue(mockResponse)

      const { result } = renderHook(() => useSwapCreate(), {
        wrapper: createWrapper(),
      })

      act(() => {
        result.current.mutate({
          sourceFacultyId: 'faculty-1',
          sourceWeek: '2024-01-01',
          swapType: SwapType.ABSORB,
          auto_match: true,
        })
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data?.candidatesNotified).toBe(5)
    })
  })

  describe('Error Handling', () => {
    it('should handle validation errors', async () => {
      const error = { message: 'Invalid swap request', status: 400 }
      mockedApi.post.mockRejectedValue(error)

      const { result } = renderHook(() => useSwapCreate(), {
        wrapper: createWrapper(),
      })

      act(() => {
        result.current.mutate({
          sourceFacultyId: 'faculty-1',
          sourceWeek: '2024-01-01',
          swapType: SwapType.ONE_TO_ONE,
        })
      })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error).toEqual(error)
    })

    it('should handle conflict errors', async () => {
      const error = { message: 'Swap conflicts with existing request', status: 409 }
      mockedApi.post.mockRejectedValue(error)

      const { result } = renderHook(() => useSwapCreate(), {
        wrapper: createWrapper(),
      })

      act(() => {
        result.current.mutate({
          sourceFacultyId: 'faculty-1',
          sourceWeek: '2024-01-01',
          swapType: SwapType.ABSORB,
        })
      })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error?.status).toBe(409)
    })
  })

  describe('Loading States', () => {
    it('should show pending during creation', async () => {
      let resolvePromise: (value: any) => void
      const promise = new Promise((resolve) => {
        resolvePromise = resolve
      })

      mockedApi.post.mockReturnValue(promise as any)

      const { result } = renderHook(() => useSwapCreate(), {
        wrapper: createWrapper(),
      })

      act(() => {
        result.current.mutate({
          sourceFacultyId: 'faculty-1',
          sourceWeek: '2024-01-01',
          swapType: SwapType.ABSORB,
        })
      })

      expect(result.current.isPending).toBe(true)

      act(() => {
        resolvePromise!({
          success: true,
          requestId: 'swap-123',
          message: 'Created',
        })
      })

      await waitFor(() => {
        expect(result.current.isPending).toBe(false)
      })
    })
  })
})

describe('useSwapApprove', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Success Scenarios', () => {
    it('should approve swap successfully', async () => {
      const mockResponse = {
        success: true,
        message: 'Swap approved',
        swapId: 'swap-123',
      }

      mockedApi.post.mockResolvedValue(mockResponse)

      const { result } = renderHook(() => useSwapApprove(), {
        wrapper: createWrapper(),
      })

      act(() => {
        result.current.mutate({
          swapId: 'swap-123',
          notes: 'Approved - coverage confirmed',
        })
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data).toEqual(mockResponse)
    })
  })

  describe('Error Handling', () => {
    it('should handle ACGME violations', async () => {
      const error = { message: 'Creates ACGME violation', status: 409 }
      mockedApi.post.mockRejectedValue(error)

      const { result } = renderHook(() => useSwapApprove(), {
        wrapper: createWrapper(),
      })

      act(() => {
        result.current.mutate({
          swapId: 'swap-123',
        })
      })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error?.status).toBe(409)
    })
  })
})

describe('useSwapReject', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Success Scenarios', () => {
    it('should reject swap successfully', async () => {
      const mockResponse = {
        success: true,
        message: 'Swap rejected',
        swapId: 'swap-123',
      }

      mockedApi.post.mockResolvedValue(mockResponse)

      const { result } = renderHook(() => useSwapReject(), {
        wrapper: createWrapper(),
      })

      act(() => {
        result.current.mutate({
          swapId: 'swap-123',
          reason: 'Coverage not available',
          notes: 'Rejected due to staffing constraints',
        })
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data).toEqual(mockResponse)
    })
  })

  describe('Error Handling', () => {
    it('should handle rejection errors', async () => {
      const error = { message: 'Cannot reject executed swap', status: 400 }
      mockedApi.post.mockRejectedValue(error)

      const { result } = renderHook(() => useSwapReject(), {
        wrapper: createWrapper(),
      })

      act(() => {
        result.current.mutate({
          swapId: 'swap-123',
          reason: 'Invalid',
        })
      })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error).toEqual(error)
    })
  })
})

describe('useAutoMatch', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Success Scenarios', () => {
    it('should auto-match candidates successfully', async () => {
      const mockResponse = {
        success: true,
        candidates: [
          {
            facultyId: 'faculty-2',
            facultyName: 'Dr. Jones',
            available_weeks: ['2024-01-08'],
            compatibility_score: 0.9,
            constraints_met: true,
          },
        ],
        total_candidates: 1,
        message: 'Found 1 compatible candidate',
      }

      mockedApi.post.mockResolvedValue(mockResponse)

      const { result } = renderHook(() => useAutoMatch(), {
        wrapper: createWrapper(),
      })

      act(() => {
        result.current.mutate({
          sourceFacultyId: 'faculty-1',
          sourceWeek: '2024-01-01',
          max_candidates: 10,
          prefer_oneToOne: true,
        })
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data).toEqual(mockResponse)
      expect(result.current.data?.total_candidates).toBe(1)
    })

    it('should handle no candidates found', async () => {
      const mockResponse = {
        success: true,
        candidates: [],
        total_candidates: 0,
        message: 'No compatible candidates found',
      }

      mockedApi.post.mockResolvedValue(mockResponse)

      const { result } = renderHook(() => useAutoMatch(), {
        wrapper: createWrapper(),
      })

      act(() => {
        result.current.mutate({
          sourceFacultyId: 'faculty-1',
          sourceWeek: '2024-01-01',
        })
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data?.total_candidates).toBe(0)
    })
  })

  describe('Error Handling', () => {
    it('should handle auto-match errors', async () => {
      const error = { message: 'Auto-match failed', status: 500 }
      mockedApi.post.mockRejectedValue(error)

      const { result } = renderHook(() => useAutoMatch(), {
        wrapper: createWrapper(),
      })

      act(() => {
        result.current.mutate({
          sourceFacultyId: 'faculty-1',
          sourceWeek: '2024-01-01',
        })
      })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error).toEqual(error)
    })
  })

  describe('Edge Cases', () => {
    it('should handle large candidate lists', async () => {
      const mockResponse = {
        success: true,
        candidates: Array.from({ length: 50 }, (_, i) => ({
          facultyId: `faculty-${i}`,
          facultyName: `Dr. ${i}`,
          available_weeks: ['2024-01-08'],
          compatibility_score: 0.8,
          constraints_met: true,
        })),
        total_candidates: 50,
        message: 'Found 50 compatible candidates',
      }

      mockedApi.post.mockResolvedValue(mockResponse)

      const { result } = renderHook(() => useAutoMatch(), {
        wrapper: createWrapper(),
      })

      act(() => {
        result.current.mutate({
          sourceFacultyId: 'faculty-1',
          sourceWeek: '2024-01-01',
          max_candidates: 100,
        })
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data?.candidates).toHaveLength(50)
    })
  })
})
