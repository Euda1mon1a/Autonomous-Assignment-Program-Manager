/**
 * RAG (Retrieval-Augmented Generation) Hooks
 *
 * Hooks for semantic search over documentation using the RAG endpoint.
 * Provides vector-based similarity search for knowledge retrieval.
 */
import { useQuery, useMutation } from '@tanstack/react-query'
import { get, post, ApiError } from '@/lib/api'

// ============================================================================
// Types
// ============================================================================

/**
 * Categories of documents available for RAG search
 */
export type RAGCategory =
  | 'acgme_rules'
  | 'military_specific'
  | 'resilience_concepts'
  | 'scheduling_policy'
  | 'swap_system'
  | 'user_guide_faq'

/**
 * A single chunk of text retrieved from the RAG system
 */
export interface RAGChunk {
  /** Unique identifier for the chunk */
  chunk_id: string
  /** The document category this chunk belongs to */
  category: RAGCategory
  /** The actual text content of the chunk */
  content: string
  /** Cosine similarity score (0-1, higher is more relevant) */
  similarity_score: number
  /** Additional metadata about the chunk */
  metadata?: {
    source_file?: string
    section_title?: string
    page_number?: number
  }
}

/**
 * Request payload for RAG retrieval
 */
export interface RAGRetrieveRequest {
  /** The search query text */
  query: string
  /** Optional category filter */
  category?: RAGCategory
  /** Maximum number of results to return (default: 5) */
  top_k?: number
  /** Minimum similarity threshold (0-1, default: 0.5) */
  threshold?: number
}

/**
 * Response from RAG retrieval endpoint
 */
export interface RAGRetrieveResponse {
  /** Retrieved document chunks */
  chunks: RAGChunk[]
  /** Total chunks searched */
  total_searched: number
  /** Time taken in milliseconds */
  query_time_ms: number
  /** The category filter used (if any) */
  category_filter?: RAGCategory
}

/**
 * RAG system health status
 */
export interface RAGHealthResponse {
  /** Overall health status */
  status: 'healthy' | 'unhealthy' | 'degraded'
  /** Whether the vector store is available */
  vector_store_available: boolean
  /** Number of documents indexed */
  document_count: number
  /** Embedding model status */
  embedding_model: string
  /** Last index update timestamp */
  last_updated?: string
}

// ============================================================================
// Query Keys
// ============================================================================

export const ragQueryKeys = {
  all: ['rag'] as const,
  health: () => [...ragQueryKeys.all, 'health'] as const,
  search: (query: string, category?: RAGCategory) =>
    [...ragQueryKeys.all, 'search', query, category] as const,
}

// ============================================================================
// Query Hooks
// ============================================================================

/**
 * Check RAG system health status.
 *
 * This hook fetches the health status of the RAG system including
 * vector store availability and document count.
 *
 * @param options - Query options
 * @returns Query result with RAG health status
 *
 * @example
 * ```tsx
 * function RAGStatus() {
 *   const { data, isLoading } = useRAGHealth();
 *
 *   if (isLoading) return <Spinner />;
 *
 *   return (
 *     <div>
 *       <Badge color={data?.status === 'healthy' ? 'green' : 'red'}>
 *         {data?.status}
 *       </Badge>
 *       <p>Documents: {data?.document_count}</p>
 *     </div>
 *   );
 * }
 * ```
 */
export function useRAGHealth(options?: { enabled?: boolean; refetchInterval?: number }) {
  return useQuery({
    queryKey: ragQueryKeys.health(),
    queryFn: async (): Promise<RAGHealthResponse> => {
      const response = await get<RAGHealthResponse>('/rag/health')
      return response
    },
    staleTime: 30_000, // 30 seconds
    refetchInterval: options?.refetchInterval ?? 60_000, // 1 minute default
    retry: 1,
    enabled: options?.enabled ?? true,
  })
}

// ============================================================================
// Mutation Hooks
// ============================================================================

/**
 * Perform semantic search over RAG documents.
 *
 * This mutation hook sends a search query to the RAG system and returns
 * semantically relevant document chunks with similarity scores.
 *
 * @returns Mutation object for RAG search
 *
 * @example
 * ```tsx
 * function SearchComponent() {
 *   const { mutate, data, isPending } = useRAGSearch();
 *   const [query, setQuery] = useState('');
 *
 *   const handleSearch = () => {
 *     mutate(
 *       { query, category: 'acgme_rules', top_k: 5 },
 *       {
 *         onSuccess: (result) => {
 *           console.log(`Found ${result.chunks.length} results`);
 *         },
 *       }
 *     );
 *   };
 *
 *   return (
 *     <div>
 *       <input value={query} onChange={(e) => setQuery(e.target.value)} />
 *       <button onClick={handleSearch} disabled={isPending}>
 *         {isPending ? 'Searching...' : 'Search'}
 *       </button>
 *       {data?.chunks.map((chunk) => (
 *         <ResultCard key={chunk.chunk_id} chunk={chunk} />
 *       ))}
 *     </div>
 *   );
 * }
 * ```
 *
 * @see useRAGHealth - For checking RAG system status
 */
export function useRAGSearch() {
  return useMutation<RAGRetrieveResponse, ApiError, RAGRetrieveRequest>({
    mutationFn: (request) => post<RAGRetrieveResponse>('/rag/retrieve', request),
  })
}
