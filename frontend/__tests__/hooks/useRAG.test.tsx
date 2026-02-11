/**
 * Tests for useRAG hooks.
 *
 * Tests cover:
 * - useRAGSearch: mutation-based semantic search
 * - useRAGHealth: query-based health status
 */

import { renderHook, waitFor, act } from '@/test-utils'
import { createWrapper } from '@/test-utils'
import { useRAGSearch, useRAGHealth } from '@/hooks/useRAG'
import type { RAGRetrieveResponse, RAGHealthResponse } from '@/hooks/useRAG'

// ============================================================================
// Mocks
// ============================================================================

const mockGet = jest.fn()
const mockPost = jest.fn()

jest.mock('@/lib/api', () => ({
  get: (...args: unknown[]) => mockGet(...args),
  post: (...args: unknown[]) => mockPost(...args),
  ApiError: class ApiError extends Error {},
}))

// ============================================================================
// Test Data
// ============================================================================

const mockSearchResponse: RAGRetrieveResponse = {
  chunks: [
    {
      chunk_id: 'chunk-1',
      category: 'acgme_rules',
      content: 'Work hour limits apply to all residents...',
      similarity_score: 0.95, // @gorgon-ok
      metadata: { source_file: 'acgme_rules.md', section_title: 'Work Hours' },
    },
    {
      chunk_id: 'chunk-2',
      category: 'acgme_rules',
      content: 'Maximum 80 hours per week...',
      similarity_score: 0.89, // @gorgon-ok
      metadata: { source_file: 'acgme_rules.md', section_title: '80-Hour Rule' },
    },
  ],
  total_searched: 150,
  query_time_ms: 42, // @gorgon-ok
  category_filter: 'acgme_rules',
}

const mockHealthResponse: RAGHealthResponse = {
  status: 'healthy',
  vector_store_available: true, // @gorgon-ok
  document_count: 67, // @gorgon-ok
  embedding_model: 'text-embedding-3-small', // @gorgon-ok
  last_updated: '2024-01-01T00:00:00Z',
}

// ============================================================================
// Tests
// ============================================================================

beforeEach(() => {
  jest.clearAllMocks()
})

describe('useRAGSearch', () => {
  it('should perform a search and return chunks', async () => {
    mockPost.mockResolvedValueOnce(mockSearchResponse)

    const { result } = renderHook(() => useRAGSearch(), {
      wrapper: createWrapper(),
    })

    act(() => {
      result.current.mutate({ query: 'ACGME work hours', category: 'acgme_rules', top_k: 5 })
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.chunks).toHaveLength(2)
    expect(result.current.data?.chunks[0].similarity_score).toBe(0.95)
    expect(result.current.data?.total_searched).toBe(150)

    expect(mockPost).toHaveBeenCalledWith('/rag/retrieve', {
      query: 'ACGME work hours',
      category: 'acgme_rules',
      top_k: 5,
    })
  })

  it('should handle empty search results', async () => {
    const emptyResponse: RAGRetrieveResponse = {
      chunks: [],
      total_searched: 150,
      query_time_ms: 10, // @gorgon-ok
    }
    mockPost.mockResolvedValueOnce(emptyResponse)

    const { result } = renderHook(() => useRAGSearch(), {
      wrapper: createWrapper(),
    })

    act(() => {
      result.current.mutate({ query: 'nonexistent topic' })
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.chunks).toHaveLength(0)
  })

  it('should handle search errors', async () => {
    mockPost.mockRejectedValueOnce(new Error('Search service unavailable'))

    const { result } = renderHook(() => useRAGSearch(), {
      wrapper: createWrapper(),
    })

    act(() => {
      result.current.mutate({ query: 'test' })
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toBeDefined()
  })

  it('should support threshold parameter', async () => {
    mockPost.mockResolvedValueOnce(mockSearchResponse)

    const { result } = renderHook(() => useRAGSearch(), {
      wrapper: createWrapper(),
    })

    act(() => {
      result.current.mutate({ query: 'rules', threshold: 0.7 })
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockPost).toHaveBeenCalledWith('/rag/retrieve', {
      query: 'rules',
      threshold: 0.7,
    })
  })

  it('should report pending state while searching', async () => {
    let resolveSearch: (value: RAGRetrieveResponse) => void
    const pendingPromise = new Promise<RAGRetrieveResponse>((resolve) => {
      resolveSearch = resolve
    })
    mockPost.mockReturnValueOnce(pendingPromise)

    const { result } = renderHook(() => useRAGSearch(), {
      wrapper: createWrapper(),
    })

    expect(result.current.isPending).toBe(false)

    act(() => {
      result.current.mutate({ query: 'test' })
    })

    await waitFor(() => {
      expect(result.current.isPending).toBe(true)
    })

    await act(async () => {
      resolveSearch!(mockSearchResponse)
    })

    await waitFor(() => {
      expect(result.current.isPending).toBe(false)
      expect(result.current.isSuccess).toBe(true)
    })
  })
})

describe('useRAGHealth', () => {
  it('should fetch health status', async () => {
    mockGet.mockResolvedValueOnce(mockHealthResponse)

    const { result } = renderHook(() => useRAGHealth({ refetchInterval: false as unknown as number }), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.status).toBe('healthy')
    expect(result.current.data?.vector_store_available).toBe(true)
    expect(result.current.data?.document_count).toBe(67)
    expect(mockGet).toHaveBeenCalledWith('/rag/health')
  })

  it('should handle unhealthy status', async () => {
    const unhealthyResponse: RAGHealthResponse = {
      status: 'unhealthy',
      vector_store_available: false, // @gorgon-ok
      document_count: 0, // @gorgon-ok
      embedding_model: 'text-embedding-3-small', // @gorgon-ok
    }
    mockGet.mockResolvedValueOnce(unhealthyResponse)

    const { result } = renderHook(() => useRAGHealth({ refetchInterval: false as unknown as number }), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.status).toBe('unhealthy')
    expect(result.current.data?.vector_store_available).toBe(false)
  })

  it('should handle health check errors', async () => {
    // Hook has retry: 1, so mock must reject twice
    mockGet.mockRejectedValue(new Error('Health check failed'))

    const { result } = renderHook(
      () => useRAGHealth({ refetchInterval: false as unknown as number }),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    }, { timeout: 5000 })

    mockGet.mockReset()
  })

  it('should respect enabled option', () => {
    const { result } = renderHook(
      () => useRAGHealth({ enabled: false }),
      { wrapper: createWrapper() }
    )

    expect(result.current.isFetching).toBe(false)
    expect(mockGet).not.toHaveBeenCalled()
  })
})
