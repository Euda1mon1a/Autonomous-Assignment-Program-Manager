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
  vectorStoreAvailable: true,
  documentCount: 150,
  embeddingModel: 'all-MiniLM-L6-v2',
  lastUpdated: '2024-01-01T00:00:00Z',
};

const mockRAGSearchResponse = {
  chunks: [
    {
      chunkId: 'chunk-1',
      category: 'acgme_rules' as const,
      content: 'Residents must have at least one day in seven free from all duties',
      similarityScore: 0.92,
      metadata: {
        sourceFile: 'acgme-common-program-requirements.pdf',
        sectionTitle: 'Duty Hours',
        pageNumber: 15,
      },
    },
    {
      chunkId: 'chunk-2',
      category: 'acgme_rules' as const,
      content: 'Work hours must be limited to 80 hours per week averaged over four weeks',
      similarityScore: 0.88,
      metadata: {
        sourceFile: 'acgme-common-program-requirements.pdf',
        sectionTitle: 'Duty Hours',
        pageNumber: 14,
      },
    },
  ],
  totalSearched: 150,
  queryTimeMs: 45,
  categoryFilter: 'acgme_rules' as const,
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
    expect(result.current.data?.vectorStoreAvailable).toBe(true);
    expect(result.current.data?.documentCount).toBe(150);
    expect(mockedApi.get).toHaveBeenCalledWith('/rag/health');
  });

  it('indicates when vector store is unavailable', async () => {
    const unhealthyResponse = {
      ...mockRAGHealth,
      status: 'unhealthy' as const,
      vectorStoreAvailable: false,
      documentCount: 0,
    };
    mockedApi.get.mockResolvedValueOnce(unhealthyResponse);

    const { result } = renderHook(() => useRAGHealth(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.data?.status).toBe('unhealthy');
      expect(result.current.data?.vectorStoreAvailable).toBe(false);
    });
  });

  it('shows embedding model information', async () => {
    mockedApi.get.mockResolvedValueOnce(mockRAGHealth);

    const { result } = renderHook(() => useRAGHealth(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.data?.embeddingModel).toBe('all-MiniLM-L6-v2');
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
        topK: 5,
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
      topK: 5,
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

    expect(result.current.data?.chunks[0].similarityScore).toBeGreaterThan(
      result.current.data!.chunks[1].similarityScore
    );
  });

  it('searches without category filter', async () => {
    mockedApi.post.mockResolvedValueOnce({
      ...mockRAGSearchResponse,
      categoryFilter: undefined,
    });

    const { result } = renderHook(() => useRAGSearch(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        query: 'general query',
        topK: 10,
      });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockedApi.post).toHaveBeenCalledWith('/rag/retrieve', {
      query: 'general query',
      topK: 10,
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
        topK: 1,
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
    expect(firstChunk?.metadata?.sourceFile).toBe(
      'acgme-common-program-requirements.pdf'
    );
    expect(firstChunk?.metadata?.sectionTitle).toBe('Duty Hours');
    expect(firstChunk?.metadata?.pageNumber).toBe(15);
  });

  it('handles search with no results', async () => {
    const emptyResponse = {
      chunks: [],
      totalSearched: 150,
      queryTimeMs: 20,
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
      expect(result.current.data?.queryTimeMs).toBe(45);
    });
  });

  it('searches different document categories', async () => {
    // @enum-ok — keys are RAGCategory enum values, must stay snake_case
    /* eslint-disable @typescript-eslint/naming-convention -- enum value keys */
    const categoryResponses = {
      military_specific: {
        ...mockRAGSearchResponse,
        categoryFilter: 'military_specific' as const,
      },
      resilience_concepts: {
        ...mockRAGSearchResponse,
        categoryFilter: 'resilience_concepts' as const,
      },
      swap_system: {
        ...mockRAGSearchResponse,
        categoryFilter: 'swap_system' as const,
      },
    };
    /* eslint-enable @typescript-eslint/naming-convention */

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
      expect(result.current.data?.categoryFilter).toBe('military_specific');
    });
  });
});
