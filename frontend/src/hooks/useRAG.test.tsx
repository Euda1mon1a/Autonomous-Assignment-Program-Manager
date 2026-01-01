/**
 * Tests for RAG (Retrieval-Augmented Generation) Hooks
 *
 * Tests semantic search over documentation with vector-based
 * similarity search for knowledge retrieval.
 */
import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import { useRAGHealth, useRAGSearch } from './useRAG';
import * as api from '@/lib/api';

// Mock the API module
jest.mock('@/lib/api');

const mockedApi = api as jest.Mocked<typeof api>;

// Test data
const mockRAGHealth = {
  status: 'healthy' as const,
  vector_store_available: true,
  document_count: 150,
  embedding_model: 'all-MiniLM-L6-v2',
  last_updated: '2024-01-01T00:00:00Z',
};

const mockRAGSearchResponse = {
  chunks: [
    {
      chunk_id: 'chunk-1',
      category: 'acgme_rules' as const,
      content: 'Residents must have at least one day in seven free from all duties',
      similarity_score: 0.92,
      metadata: {
        source_file: 'acgme-common-program-requirements.pdf',
        section_title: 'Duty Hours',
        page_number: 15,
      },
    },
    {
      chunk_id: 'chunk-2',
      category: 'acgme_rules' as const,
      content: 'Work hours must be limited to 80 hours per week averaged over four weeks',
      similarity_score: 0.88,
      metadata: {
        source_file: 'acgme-common-program-requirements.pdf',
        section_title: 'Duty Hours',
        page_number: 14,
      },
    },
  ],
  total_searched: 150,
  query_time_ms: 45,
  category_filter: 'acgme_rules' as const,
};

// Create wrapper with QueryClient
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

describe('useRAGHealth', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('fetches RAG health status successfully', async () => {
    mockedApi.get.mockResolvedValueOnce(mockRAGHealth);

    const { result } = renderHook(() => useRAGHealth(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(mockRAGHealth);
    expect(result.current.data?.vector_store_available).toBe(true);
    expect(result.current.data?.document_count).toBe(150);
    expect(mockedApi.get).toHaveBeenCalledWith('/rag/health');
  });

  it('indicates when vector store is unavailable', async () => {
    const unhealthyResponse = {
      ...mockRAGHealth,
      status: 'unhealthy' as const,
      vector_store_available: false,
      document_count: 0,
    };
    mockedApi.get.mockResolvedValueOnce(unhealthyResponse);

    const { result } = renderHook(() => useRAGHealth(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.data?.status).toBe('unhealthy');
      expect(result.current.data?.vector_store_available).toBe(false);
    });
  });

  it('shows embedding model information', async () => {
    mockedApi.get.mockResolvedValueOnce(mockRAGHealth);

    const { result } = renderHook(() => useRAGHealth(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.data?.embedding_model).toBe('all-MiniLM-L6-v2');
    });
  });

  it('respects enabled option', async () => {
    const { result } = renderHook(
      () => useRAGHealth({ enabled: false }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(mockedApi.get).not.toHaveBeenCalled();
  });

  it('uses custom refetch interval', async () => {
    mockedApi.get.mockResolvedValue(mockRAGHealth);

    renderHook(() => useRAGHealth({ refetchInterval: 5000 }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(mockedApi.get).toHaveBeenCalled();
    });
  });

  it('handles health check errors', async () => {
    const error = { status: 503, message: 'RAG service unavailable' };
    mockedApi.get.mockRejectedValueOnce(error);

    const { result } = renderHook(() => useRAGHealth(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
  });
});

describe('useRAGSearch', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('performs search successfully', async () => {
    mockedApi.post.mockResolvedValueOnce(mockRAGSearchResponse);

    const { result } = renderHook(() => useRAGSearch(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        query: '80 hour work week',
        category: 'acgme_rules',
        top_k: 5,
      });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockRAGSearchResponse);
    expect(result.current.data?.chunks).toHaveLength(2);
    expect(mockedApi.post).toHaveBeenCalledWith('/rag/retrieve', {
      query: '80 hour work week',
      category: 'acgme_rules',
      top_k: 5,
    });
  });

  it('returns results sorted by similarity score', async () => {
    mockedApi.post.mockResolvedValueOnce(mockRAGSearchResponse);

    const { result } = renderHook(() => useRAGSearch(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        query: 'duty hours',
      });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.chunks[0].similarity_score).toBeGreaterThan(
      result.current.data!.chunks[1].similarity_score
    );
  });

  it('searches without category filter', async () => {
    mockedApi.post.mockResolvedValueOnce({
      ...mockRAGSearchResponse,
      category_filter: undefined,
    });

    const { result } = renderHook(() => useRAGSearch(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        query: 'general query',
        top_k: 10,
      });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockedApi.post).toHaveBeenCalledWith('/rag/retrieve', {
      query: 'general query',
      top_k: 10,
    });
  });

  it('applies minimum similarity threshold', async () => {
    mockedApi.post.mockResolvedValueOnce(mockRAGSearchResponse);

    const { result } = renderHook(() => useRAGSearch(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        query: 'specific query',
        threshold: 0.7,
      });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockedApi.post).toHaveBeenCalledWith('/rag/retrieve', {
      query: 'specific query',
      threshold: 0.7,
    });
  });

  it('limits number of results with top_k', async () => {
    const limitedResponse = {
      ...mockRAGSearchResponse,
      chunks: [mockRAGSearchResponse.chunks[0]],
    };
    mockedApi.post.mockResolvedValueOnce(limitedResponse);

    const { result } = renderHook(() => useRAGSearch(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        query: 'test query',
        top_k: 1,
      });
    });

    await waitFor(() => {
      expect(result.current.data?.chunks).toHaveLength(1);
    });
  });

  it('includes metadata in search results', async () => {
    mockedApi.post.mockResolvedValueOnce(mockRAGSearchResponse);

    const { result } = renderHook(() => useRAGSearch(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        query: 'ACGME requirements',
        category: 'acgme_rules',
      });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    const firstChunk = result.current.data?.chunks[0];
    expect(firstChunk?.metadata?.source_file).toBe(
      'acgme-common-program-requirements.pdf'
    );
    expect(firstChunk?.metadata?.section_title).toBe('Duty Hours');
    expect(firstChunk?.metadata?.page_number).toBe(15);
  });

  it('handles search with no results', async () => {
    const emptyResponse = {
      chunks: [],
      total_searched: 150,
      query_time_ms: 20,
    };
    mockedApi.post.mockResolvedValueOnce(emptyResponse);

    const { result } = renderHook(() => useRAGSearch(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        query: 'nonexistent topic',
      });
    });

    await waitFor(() => {
      expect(result.current.data?.chunks).toHaveLength(0);
    });
  });

  it('handles search errors', async () => {
    const error = { status: 500, message: 'Search failed' };
    mockedApi.post.mockRejectedValueOnce(error);

    const { result } = renderHook(() => useRAGSearch(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        query: 'test query',
      });
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeTruthy();
  });

  it('reports query execution time', async () => {
    mockedApi.post.mockResolvedValueOnce(mockRAGSearchResponse);

    const { result } = renderHook(() => useRAGSearch(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        query: 'test query',
      });
    });

    await waitFor(() => {
      expect(result.current.data?.query_time_ms).toBe(45);
    });
  });

  it('searches different document categories', async () => {
    const categoryResponses = {
      military_specific: {
        ...mockRAGSearchResponse,
        category_filter: 'military_specific' as const,
      },
      resilience_concepts: {
        ...mockRAGSearchResponse,
        category_filter: 'resilience_concepts' as const,
      },
      swap_system: {
        ...mockRAGSearchResponse,
        category_filter: 'swap_system' as const,
      },
    };

    mockedApi.post.mockResolvedValueOnce(categoryResponses.military_specific);

    const { result } = renderHook(() => useRAGSearch(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        query: 'TDY deployment',
        category: 'military_specific',
      });
    });

    await waitFor(() => {
      expect(result.current.data?.category_filter).toBe('military_specific');
    });
  });
});
