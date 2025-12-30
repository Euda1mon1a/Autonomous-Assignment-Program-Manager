'use client';

/**
 * RAG Search Component
 *
 * A semantic search interface for querying documentation using the RAG endpoint.
 * Displays search results with similarity scores and category filtering.
 */
import { useState, useCallback } from 'react';
import { useRAGSearch, useRAGHealth, type RAGCategory, type RAGChunk } from '@/hooks/useRAG';
import { Input } from '@/components/forms/Input';
import { Select } from '@/components/forms/Select';
import { LoadingSpinner } from '@/components/LoadingSpinner';

// ============================================================================
// Constants
// ============================================================================

const CATEGORY_OPTIONS: { value: '' | RAGCategory; label: string }[] = [
  { value: '', label: 'All Categories' },
  { value: 'acgme_rules', label: 'ACGME Rules' },
  { value: 'military_specific', label: 'Military Specific' },
  { value: 'resilience_concepts', label: 'Resilience Concepts' },
  { value: 'scheduling_policy', label: 'Scheduling Policy' },
  { value: 'swap_system', label: 'Swap System' },
  { value: 'user_guide_faq', label: 'User Guide & FAQ' },
];

// ============================================================================
// Sub-components
// ============================================================================

interface ResultCardProps {
  chunk: RAGChunk;
  index: number;
}

/**
 * Displays a single search result with similarity score and content.
 */
function ResultCard({ chunk, index }: ResultCardProps) {
  // Format similarity score as percentage
  const similarityPercent = (chunk.similarity_score * 100).toFixed(1);

  // Determine badge color based on similarity score
  const getBadgeColor = (score: number): string => {
    if (score >= 0.8) return 'bg-green-100 text-green-800';
    if (score >= 0.6) return 'bg-yellow-100 text-yellow-800';
    return 'bg-gray-100 text-gray-800';
  };

  // Format category name for display
  const formatCategory = (category: RAGCategory): string => {
    return category
      .split('_')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors">
      {/* Header with rank and similarity score */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-gray-500">#{index + 1}</span>
          <span
            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getBadgeColor(
              chunk.similarity_score
            )}`}
          >
            {similarityPercent}% match
          </span>
        </div>
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
          {formatCategory(chunk.category)}
        </span>
      </div>

      {/* Content */}
      <p className="text-gray-700 text-sm leading-relaxed whitespace-pre-wrap">
        {chunk.content}
      </p>

      {/* Metadata (if available) */}
      {chunk.metadata && (
        <div className="mt-2 pt-2 border-t border-gray-100 text-xs text-gray-500">
          {chunk.metadata.source_file && (
            <span className="mr-4">Source: {chunk.metadata.source_file}</span>
          )}
          {chunk.metadata.section_title && (
            <span className="mr-4">Section: {chunk.metadata.section_title}</span>
          )}
          {chunk.metadata.page_number && (
            <span>Page: {chunk.metadata.page_number}</span>
          )}
        </div>
      )}
    </div>
  );
}

interface HealthIndicatorProps {
  status: 'healthy' | 'unhealthy' | 'degraded';
  documentCount: number;
}

/**
 * Displays the health status of the RAG system.
 */
function HealthIndicator({ status, documentCount }: HealthIndicatorProps) {
  const getStatusColor = (): string => {
    switch (status) {
      case 'healthy':
        return 'bg-green-500';
      case 'degraded':
        return 'bg-yellow-500';
      case 'unhealthy':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  return (
    <div className="flex items-center gap-2 text-sm text-gray-600">
      <span className={`w-2 h-2 rounded-full ${getStatusColor()}`} />
      <span>
        RAG {status} - {documentCount} documents indexed
      </span>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export interface RAGSearchProps {
  /** Optional CSS class name */
  className?: string;
  /** Default number of results to return */
  defaultTopK?: number;
}

/**
 * RAG Search component for semantic search over documentation.
 *
 * Provides a search interface with:
 * - Text input for search queries
 * - Category filter dropdown
 * - Results display with similarity scores
 * - Health status indicator
 *
 * @example
 * ```tsx
 * function DocumentSearch() {
 *   return (
 *     <div className="p-4">
 *       <h1>Documentation Search</h1>
 *       <RAGSearch defaultTopK={10} />
 *     </div>
 *   );
 * }
 * ```
 */
export function RAGSearch({ className = '', defaultTopK = 5 }: RAGSearchProps) {
  // State
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState<'' | RAGCategory>('');

  // Hooks
  const { data: healthData, isLoading: isHealthLoading } = useRAGHealth();
  const { mutate: search, data: searchData, isPending, error, reset } = useRAGSearch();

  // Handlers
  const handleSearch = useCallback(() => {
    if (!query.trim()) return;

    search({
      query: query.trim(),
      category: category || undefined,
      top_k: defaultTopK,
    });
  }, [query, category, defaultTopK, search]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Enter') {
        handleSearch();
      }
    },
    [handleSearch]
  );

  const handleClear = useCallback(() => {
    setQuery('');
    setCategory('');
    reset();
  }, [reset]);

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Header with health indicator */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Documentation Search</h2>
        {!isHealthLoading && healthData && (
          <HealthIndicator
            status={healthData.status}
            documentCount={healthData.document_count}
          />
        )}
      </div>

      {/* Search controls */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex-1">
          <Input
            label="Search Query"
            placeholder="Enter your question or search terms..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isPending}
          />
        </div>
        <div className="w-full sm:w-48">
          <Select
            label="Category"
            options={CATEGORY_OPTIONS}
            value={category}
            onChange={(e) => setCategory(e.target.value as '' | RAGCategory)}
            disabled={isPending}
          />
        </div>
      </div>

      {/* Action buttons */}
      <div className="flex gap-2">
        <button
          onClick={handleSearch}
          disabled={isPending || !query.trim()}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700
                     disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isPending ? 'Searching...' : 'Search'}
        </button>
        <button
          onClick={handleClear}
          disabled={isPending}
          className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200
                     disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Clear
        </button>
      </div>

      {/* Loading state */}
      {isPending && (
        <div className="py-8">
          <LoadingSpinner text="Searching documentation..." />
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-700 text-sm">
            Error: {error.message || 'Failed to search documentation'}
          </p>
        </div>
      )}

      {/* Results */}
      {searchData && !isPending && (
        <div className="space-y-4">
          {/* Results header */}
          <div className="flex items-center justify-between text-sm text-gray-600">
            <span>
              Found {searchData.chunks.length} result{searchData.chunks.length !== 1 ? 's' : ''}
              {searchData.category_filter && ` in ${searchData.category_filter.replace('_', ' ')}`}
            </span>
            <span>Query time: {searchData.query_time_ms}ms</span>
          </div>

          {/* Results list */}
          {searchData.chunks.length > 0 ? (
            <div className="space-y-3">
              {searchData.chunks.map((chunk, index) => (
                <ResultCard key={chunk.chunk_id} chunk={chunk} index={index} />
              ))}
            </div>
          ) : (
            <div className="py-8 text-center text-gray-500">
              <p>No results found for your query.</p>
              <p className="text-sm mt-1">
                Try different keywords or remove the category filter.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Initial state - no search performed */}
      {!searchData && !isPending && !error && (
        <div className="py-8 text-center text-gray-500 border border-dashed border-gray-300 rounded-lg">
          <p>Enter a search query to find relevant documentation.</p>
          <p className="text-sm mt-1">
            Use natural language questions for best results.
          </p>
        </div>
      )}
    </div>
  );
}

export default RAGSearch;
