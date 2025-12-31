/**
 * Tests for Audit Hooks
 *
 * Tests React Query hooks for audit log data fetching and mutations
 */

import { renderHook, waitFor } from '@/test-utils';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import * as api from '@/lib/api';
import {
  useAuditLogs,
  useAuditLogEntry,
  useAuditStatistics,
  useAuditTimeline,
  useEntityAuditHistory,
  useUserAuditActivity,
  useAuditUsers,
  useExportAuditLogs,
  useMarkAuditReviewed,
  auditQueryKeys,
} from '@/features/audit/hooks';
import {
  mockAuditLogResponse,
  mockStatistics,
  mockUsers,
  mockAuditLogs,
} from './mockData';

// Mock the API
jest.mock('@/lib/api');
const mockGet = api.get as jest.MockedFunction<typeof api.get>;
const mockPost = api.post as jest.MockedFunction<typeof api.post>;

// Create a test wrapper
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
      mutations: {
        retry: false,
      },
    },
    logger: {
      log: () => {},
      warn: () => {},
      error: () => {},
    },
  });

  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
}

describe('Audit Hooks', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // ============================================================================
  // useAuditLogs Tests
  // ============================================================================

  describe('useAuditLogs', () => {
    it('should fetch audit logs successfully', async () => {
      mockGet.mockResolvedValueOnce(mockAuditLogResponse);

      const { result } = renderHook(() => useAuditLogs(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data).toEqual(mockAuditLogResponse);
      expect(mockGet).toHaveBeenCalledWith(expect.stringContaining('/audit/logs'));
    });

    it('should apply pagination parameters', async () => {
      mockGet.mockResolvedValueOnce(mockAuditLogResponse);

      const params = {
        pagination: { page: 2, pageSize: 25 },
      };

      const { result } = renderHook(() => useAuditLogs(params), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith(
        expect.stringContaining('page=2')
      );
      expect(mockGet).toHaveBeenCalledWith(
        expect.stringContaining('page_size=25')
      );
    });

    it('should apply filter parameters', async () => {
      mockGet.mockResolvedValueOnce(mockAuditLogResponse);

      const params = {
        filters: {
          entityTypes: ['assignment' as const],
          actions: ['create' as const],
        },
      };

      const { result } = renderHook(() => useAuditLogs(params), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith(
        expect.stringContaining('entity_types=assignment')
      );
      expect(mockGet).toHaveBeenCalledWith(
        expect.stringContaining('actions=create')
      );
    });

    it('should apply sort parameters', async () => {
      mockGet.mockResolvedValueOnce(mockAuditLogResponse);

      const params = {
        sort: { field: 'user' as const, direction: 'asc' as const },
      };

      const { result } = renderHook(() => useAuditLogs(params), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith(
        expect.stringContaining('sort_by=user')
      );
      expect(mockGet).toHaveBeenCalledWith(
        expect.stringContaining('sort_direction=asc')
      );
    });

    it('should apply date range filters', async () => {
      mockGet.mockResolvedValueOnce(mockAuditLogResponse);

      const params = {
        filters: {
          dateRange: { start: '2025-12-01', end: '2025-12-17' },
        },
      };

      const { result } = renderHook(() => useAuditLogs(params), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith(
        expect.stringContaining('start_date=2025-12-01')
      );
      expect(mockGet).toHaveBeenCalledWith(
        expect.stringContaining('end_date=2025-12-17')
      );
    });

    it('should apply search query', async () => {
      mockGet.mockResolvedValueOnce(mockAuditLogResponse);

      const params = {
        filters: {
          searchQuery: 'test query',
        },
      };

      const { result } = renderHook(() => useAuditLogs(params), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith(
        expect.stringContaining('search=test')
      );
    });

    it('should apply ACGME overrides filter', async () => {
      mockGet.mockResolvedValueOnce(mockAuditLogResponse);

      const params = {
        filters: {
          acgmeOverridesOnly: true,
        },
      };

      const { result } = renderHook(() => useAuditLogs(params), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith(
        expect.stringContaining('acgme_overrides_only=true')
      );
    });

    it('should handle loading state', () => {
      mockGet.mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      const { result } = renderHook(() => useAuditLogs(), {
        wrapper: createWrapper(),
      });

      expect(result.current.isLoading).toBe(true);
      expect(result.current.data).toBeUndefined();
    });

    it('should handle error state', async () => {
      const error = new Error('Failed to fetch');
      mockGet.mockRejectedValueOnce(error);

      const { result } = renderHook(() => useAuditLogs(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error).toBeDefined();
    });
  });

  // ============================================================================
  // useAuditLogEntry Tests
  // ============================================================================

  describe('useAuditLogEntry', () => {
    it('should fetch single audit log entry', async () => {
      const entry = mockAuditLogs[0];
      mockGet.mockResolvedValueOnce(entry);

      const { result } = renderHook(() => useAuditLogEntry('audit-1'), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data).toEqual(entry);
      expect(mockGet).toHaveBeenCalledWith('/audit/logs/audit-1');
    });

    it('should not fetch when id is empty', () => {
      const { result } = renderHook(() => useAuditLogEntry(''), {
        wrapper: createWrapper(),
      });

      expect(result.current.fetchStatus).toBe('idle');
      expect(mockGet).not.toHaveBeenCalled();
    });
  });

  // ============================================================================
  // useAuditStatistics Tests
  // ============================================================================

  describe('useAuditStatistics', () => {
    it('should fetch audit statistics', async () => {
      mockGet.mockResolvedValueOnce(mockStatistics);

      const { result } = renderHook(() => useAuditStatistics(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data).toEqual(mockStatistics);
      expect(mockGet).toHaveBeenCalledWith(
        expect.stringContaining('/audit/statistics')
      );
    });

    it('should apply date range to statistics query', async () => {
      mockGet.mockResolvedValueOnce(mockStatistics);

      const dateRange = { start: '2025-12-01', end: '2025-12-17' };
      const { result } = renderHook(() => useAuditStatistics(dateRange), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith(
        expect.stringContaining('start_date=2025-12-01')
      );
      expect(mockGet).toHaveBeenCalledWith(
        expect.stringContaining('end_date=2025-12-17')
      );
    });
  });

  // ============================================================================
  // useAuditTimeline Tests
  // ============================================================================

  describe('useAuditTimeline', () => {
    it('should fetch and transform timeline events', async () => {
      mockGet.mockResolvedValueOnce(mockAuditLogResponse);

      const { result } = renderHook(() => useAuditTimeline(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data).toBeDefined();
      expect(Array.isArray(result.current.data)).toBe(true);
      if (result.current.data) {
        expect(result.current.data.length).toBeGreaterThan(0);
        expect(result.current.data[0]).toHaveProperty('title');
        expect(result.current.data[0]).toHaveProperty('description');
      }
    });

    it('should apply filters to timeline query', async () => {
      mockGet.mockResolvedValueOnce(mockAuditLogResponse);

      const filters = { entityTypes: ['assignment' as const] };
      const { result } = renderHook(() => useAuditTimeline(filters), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith(
        expect.stringContaining('entity_types=assignment')
      );
    });
  });

  // ============================================================================
  // useEntityAuditHistory Tests
  // ============================================================================

  describe('useEntityAuditHistory', () => {
    it('should fetch entity audit history', async () => {
      mockGet.mockResolvedValueOnce(mockAuditLogResponse);

      const { result } = renderHook(
        () => useEntityAuditHistory('assignment', 'assign-123'),
        {
          wrapper: createWrapper(),
        }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith(
        expect.stringContaining('entity_type=assignment')
      );
      expect(mockGet).toHaveBeenCalledWith(
        expect.stringContaining('entity_id=assign-123')
      );
    });

    it('should not fetch when entityType or entityId is empty', () => {
      const { result } = renderHook(() => useEntityAuditHistory('', ''), {
        wrapper: createWrapper(),
      });

      expect(result.current.fetchStatus).toBe('idle');
      expect(mockGet).not.toHaveBeenCalled();
    });
  });

  // ============================================================================
  // useUserAuditActivity Tests
  // ============================================================================

  describe('useUserAuditActivity', () => {
    it('should fetch user audit activity', async () => {
      mockGet.mockResolvedValueOnce(mockAuditLogResponse);

      const { result } = renderHook(() => useUserAuditActivity('user-1'), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith(
        expect.stringContaining('user_ids=user-1')
      );
    });

    it('should apply date range to user activity query', async () => {
      mockGet.mockResolvedValueOnce(mockAuditLogResponse);

      const dateRange = { start: '2025-12-01', end: '2025-12-17' };
      const { result } = renderHook(
        () => useUserAuditActivity('user-1', dateRange),
        {
          wrapper: createWrapper(),
        }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockGet).toHaveBeenCalledWith(
        expect.stringContaining('start_date=2025-12-01')
      );
      expect(mockGet).toHaveBeenCalledWith(
        expect.stringContaining('end_date=2025-12-17')
      );
    });

    it('should not fetch when userId is empty', () => {
      const { result } = renderHook(() => useUserAuditActivity(''), {
        wrapper: createWrapper(),
      });

      expect(result.current.fetchStatus).toBe('idle');
      expect(mockGet).not.toHaveBeenCalled();
    });
  });

  // ============================================================================
  // useAuditUsers Tests
  // ============================================================================

  describe('useAuditUsers', () => {
    it('should fetch audit users', async () => {
      mockGet.mockResolvedValueOnce(mockUsers);

      const { result } = renderHook(() => useAuditUsers(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data).toEqual(mockUsers);
      expect(mockGet).toHaveBeenCalledWith('/audit/users');
    });
  });

  // ============================================================================
  // useExportAuditLogs Tests
  // ============================================================================

  describe('useExportAuditLogs', () => {
    it('should export audit logs', async () => {
      const blob = new Blob(['test'], { type: 'text/csv' });
      mockPost.mockResolvedValueOnce(blob);

      const { result } = renderHook(() => useExportAuditLogs(), {
        wrapper: createWrapper(),
      });

      const config = {
        format: 'csv' as const,
        includeMetadata: true,
        includeChanges: true,
      };

      result.current.mutate(config);

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockPost).toHaveBeenCalledWith(
        '/audit/export',
        config,
        expect.any(Object)
      );
      expect(result.current.data).toEqual(blob);
    });

    it('should handle export error', async () => {
      const error = new Error('Export failed');
      mockPost.mockRejectedValueOnce(error);

      const { result } = renderHook(() => useExportAuditLogs(), {
        wrapper: createWrapper(),
      });

      const config = {
        format: 'json' as const,
        includeMetadata: false,
      };

      result.current.mutate(config);

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error).toBeDefined();
    });
  });

  // ============================================================================
  // useMarkAuditReviewed Tests
  // ============================================================================

  describe('useMarkAuditReviewed', () => {
    it('should mark audit entries as reviewed', async () => {
      mockPost.mockResolvedValueOnce(undefined);

      const { result } = renderHook(() => useMarkAuditReviewed(), {
        wrapper: createWrapper(),
      });

      const payload = {
        ids: ['audit-1', 'audit-2'],
        reviewedBy: 'user-1',
        notes: 'Reviewed for compliance',
      };

      result.current.mutate(payload);

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(mockPost).toHaveBeenCalledWith('/audit/mark-reviewed', {
        ids: payload.ids,
        reviewed_by: payload.reviewedBy,
        notes: payload.notes,
      });
    });

    it('should handle marking reviewed error', async () => {
      const error = new Error('Failed to mark reviewed');
      mockPost.mockRejectedValueOnce(error);

      const { result } = renderHook(() => useMarkAuditReviewed(), {
        wrapper: createWrapper(),
      });

      const payload = {
        ids: ['audit-1'],
        reviewedBy: 'user-1',
      };

      result.current.mutate(payload);

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error).toBeDefined();
    });
  });

  // ============================================================================
  // Query Keys Tests
  // ============================================================================

  describe('Query Keys', () => {
    it('should generate correct query keys for logs', () => {
      const params = {
        filters: { entityTypes: ['assignment' as const] },
        pagination: { page: 1, pageSize: 10 },
      };

      const key = auditQueryKeys.logs(params);

      expect(key).toEqual(['audit', 'logs', params]);
    });

    it('should generate correct query key for single log', () => {
      const key = auditQueryKeys.log('audit-1');

      expect(key).toEqual(['audit', 'logs', 'audit-1']);
    });

    it('should generate correct query key for statistics', () => {
      const dateRange = { start: '2025-12-01', end: '2025-12-17' };
      const key = auditQueryKeys.statistics(dateRange);

      expect(key).toEqual(['audit', 'statistics', dateRange]);
    });

    it('should generate correct query key for entity history', () => {
      const key = auditQueryKeys.entityHistory('assignment', 'assign-123');

      expect(key).toEqual(['audit', 'entity-history', 'assignment', 'assign-123']);
    });

    it('should generate correct query key for user activity', () => {
      const dateRange = { start: '2025-12-01', end: '2025-12-17' };
      const key = auditQueryKeys.userActivity('user-1', dateRange);

      expect(key).toEqual(['audit', 'user-activity', 'user-1', dateRange]);
    });
  });
});
