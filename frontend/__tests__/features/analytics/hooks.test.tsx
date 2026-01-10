/**
 * Tests for analytics hooks
 * Tests data fetching, caching, and mutation behavior
 */
import { renderHook, waitFor, act } from '@/test-utils';
import {
  useCurrentMetrics,
  useFairnessTrend,
  usePgyEquity,
  useVersionComparison,
  useScheduleVersions,
  useMetricAlerts,
  useWhatIfAnalysis,
  useAcknowledgeAlert,
  useDismissAlert,
  useExportAnalytics,
  useRefreshMetrics,
} from '@/features/analytics/hooks';
import { analyticsMockResponses, analyticsMockFactories } from './analytics-mocks';
import { createWrapper } from '../../utils/test-utils';
import * as api from '@/lib/api';

// Mock the api module
jest.mock('@/lib/api', () => ({
  get: jest.fn(),
  post: jest.fn(),
}));

const mockedApi = api as jest.Mocked<typeof api>;

describe('Analytics Query Hooks', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('useCurrentMetrics', () => {
    it('should fetch current metrics', async () => {
      mockedApi.get.mockResolvedValueOnce(analyticsMockResponses.currentMetrics);

      const { result } = renderHook(() => useCurrentMetrics(), {
        wrapper: createWrapper(),
      });

      expect(result.current.isLoading).toBe(true);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(mockedApi.get).toHaveBeenCalledWith('/analytics/metrics/current');
      expect(result.current.data).toEqual(analyticsMockResponses.currentMetrics);
    });

    it('should handle API errors', async () => {
      const apiError = { message: 'Server error', status: 500 };
      mockedApi.get.mockRejectedValueOnce(apiError);

      const { result } = renderHook(() => useCurrentMetrics(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toEqual(apiError);
    });

    it('should cache metrics data', async () => {
      mockedApi.get.mockResolvedValue(analyticsMockResponses.currentMetrics);

      const { result, rerender } = renderHook(() => useCurrentMetrics(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(mockedApi.get).toHaveBeenCalledTimes(1);

      // Rerender should use cached data
      rerender();

      expect(mockedApi.get).toHaveBeenCalledTimes(1); // Still only called once
    });
  });

  describe('useFairnessTrend', () => {
    it('should fetch fairness trend for 3 months', async () => {
      mockedApi.get.mockResolvedValueOnce(analyticsMockResponses.fairnessTrend);

      const { result } = renderHook(() => useFairnessTrend(3), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('/analytics/trends/fairness?period=90d')
      );
      expect(result.current.data).toEqual(analyticsMockResponses.fairnessTrend);
    });

    it('should fetch fairness trend for 6 months', async () => {
      mockedApi.get.mockResolvedValueOnce(analyticsMockResponses.fairnessTrend);

      const { result } = renderHook(() => useFairnessTrend(6), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('/analytics/trends/fairness?period=180d')
      );
    });

    it('should fetch fairness trend for 12 months', async () => {
      mockedApi.get.mockResolvedValueOnce(analyticsMockResponses.fairnessTrend);

      const { result } = renderHook(() => useFairnessTrend(12), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('/analytics/trends/fairness?period=1y')
      );
    });

    it('should handle API errors', async () => {
      const apiError = { message: 'Failed to fetch trend data', status: 500 };
      mockedApi.get.mockRejectedValueOnce(apiError);

      const { result } = renderHook(() => useFairnessTrend(3), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toEqual(apiError);
    });
  });

  describe('usePgyEquity', () => {
    it('should fetch PGY equity data', async () => {
      mockedApi.get.mockResolvedValueOnce(analyticsMockResponses.pgyEquity);

      const { result } = renderHook(() => usePgyEquity(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(mockedApi.get).toHaveBeenCalledWith('/analytics/equity/pgy');
      expect(result.current.data).toEqual(analyticsMockResponses.pgyEquity);
    });

    it('should handle API errors', async () => {
      const apiError = { message: 'Failed to fetch PGY data', status: 500 };
      mockedApi.get.mockRejectedValueOnce(apiError);

      const { result } = renderHook(() => usePgyEquity(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toEqual(apiError);
    });
  });

  describe('useVersionComparison', () => {
    it('should fetch version comparison', async () => {
      mockedApi.get.mockResolvedValueOnce(analyticsMockResponses.versionComparison);

      const { result } = renderHook(() => useVersionComparison('v1', 'v2'), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(mockedApi.get).toHaveBeenCalledWith(
        '/analytics/versions/compare?version_a=v1&version_b=v2'
      );
      expect(result.current.data).toEqual(analyticsMockResponses.versionComparison);
    });

    it('should not fetch when version IDs are empty', async () => {
      const { result } = renderHook(() => useVersionComparison('', ''), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isPending).toBe(true);
      });

      expect(mockedApi.get).not.toHaveBeenCalled();
    });

    it('should handle API errors', async () => {
      const apiError = { message: 'Comparison failed', status: 500 };
      mockedApi.get.mockRejectedValueOnce(apiError);

      const { result } = renderHook(() => useVersionComparison('v1', 'v2'), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toEqual(apiError);
    });
  });

  describe('useScheduleVersions', () => {
    it('should fetch schedule versions', async () => {
      mockedApi.get.mockResolvedValueOnce(analyticsMockResponses.versions);

      const { result } = renderHook(() => useScheduleVersions(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(mockedApi.get).toHaveBeenCalledWith('/analytics/versions');
      expect(result.current.data).toEqual(analyticsMockResponses.versions);
    });

    it('should handle API errors', async () => {
      const apiError = { message: 'Failed to fetch versions', status: 500 };
      mockedApi.get.mockRejectedValueOnce(apiError);

      const { result } = renderHook(() => useScheduleVersions(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toEqual(apiError);
    });
  });

  describe('useMetricAlerts', () => {
    it('should fetch all alerts when acknowledged parameter not provided', async () => {
      mockedApi.get.mockResolvedValueOnce(analyticsMockResponses.alerts);

      const { result } = renderHook(() => useMetricAlerts(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(mockedApi.get).toHaveBeenCalledWith('/analytics/alerts');
      expect(result.current.data).toEqual(analyticsMockResponses.alerts);
    });

    it('should fetch only unacknowledged alerts', async () => {
      const unacknowledgedAlerts = [analyticsMockResponses.alerts[0]];
      mockedApi.get.mockResolvedValueOnce(unacknowledgedAlerts);

      const { result } = renderHook(() => useMetricAlerts(false), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(mockedApi.get).toHaveBeenCalledWith('/analytics/alerts?acknowledged=false');
    });

    it('should handle API errors', async () => {
      const apiError = { message: 'Failed to fetch alerts', status: 500 };
      mockedApi.get.mockRejectedValueOnce(apiError);

      const { result } = renderHook(() => useMetricAlerts(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toEqual(apiError);
    });
  });
});

describe('Analytics Mutation Hooks', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('useWhatIfAnalysis', () => {
    it('should submit what-if analysis request', async () => {
      const mockResult = analyticsMockResponses.whatIfAnalysis;
      mockedApi.post.mockResolvedValueOnce(mockResult);

      const { result } = renderHook(() => useWhatIfAnalysis(), {
        wrapper: createWrapper(),
      });

      const request = analyticsMockFactories.whatIfAnalysisRequest();

      await act(async () => {
        result.current.mutate(request);
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(mockedApi.post).toHaveBeenCalledWith('/analytics/what-if', request);
      expect(result.current.data).toEqual(mockResult);
    });

    it('should handle analysis errors', async () => {
      const apiError = { message: 'Analysis failed', status: 500 };
      mockedApi.post.mockRejectedValueOnce(apiError);

      const { result } = renderHook(() => useWhatIfAnalysis(), {
        wrapper: createWrapper(),
      });

      const request = analyticsMockFactories.whatIfAnalysisRequest();

      await act(async () => {
        result.current.mutate(request);
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toEqual(apiError);
    });
  });

  describe('useAcknowledgeAlert', () => {
    it('should acknowledge an alert', async () => {
      mockedApi.post.mockResolvedValueOnce(undefined);

      const { result } = renderHook(() => useAcknowledgeAlert(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        result.current.mutate({ alertId: 'alert-1' });
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(mockedApi.post).toHaveBeenCalledWith('/analytics/alerts/alert-1/acknowledge', {});
    });

    it('should acknowledge alert with notes', async () => {
      mockedApi.post.mockResolvedValueOnce(undefined);

      const { result } = renderHook(() => useAcknowledgeAlert(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        result.current.mutate({ alertId: 'alert-1', notes: 'Will address this' });
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(mockedApi.post).toHaveBeenCalledWith('/analytics/alerts/alert-1/acknowledge', {
        notes: 'Will address this',
      });
    });

    it('should handle acknowledgement errors', async () => {
      const apiError = { message: 'Acknowledgement failed', status: 500 };
      mockedApi.post.mockRejectedValueOnce(apiError);

      const { result } = renderHook(() => useAcknowledgeAlert(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        result.current.mutate({ alertId: 'alert-1' });
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toEqual(apiError);
    });
  });

  describe('useDismissAlert', () => {
    it('should dismiss an alert', async () => {
      mockedApi.post.mockResolvedValueOnce(undefined);

      const { result } = renderHook(() => useDismissAlert(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        result.current.mutate('alert-1');
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(mockedApi.post).toHaveBeenCalledWith('/analytics/alerts/alert-1/dismiss', {});
    });

    it('should handle dismissal errors', async () => {
      const apiError = { message: 'Dismissal failed', status: 500 };
      mockedApi.post.mockRejectedValueOnce(apiError);

      const { result } = renderHook(() => useDismissAlert(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        result.current.mutate('alert-1');
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toEqual(apiError);
    });
  });

  describe('useExportAnalytics', () => {
    it('should export analytics as PDF', async () => {
      const mockBlob = new Blob(['test data']);
      mockedApi.post.mockResolvedValueOnce(mockBlob);

      const { result } = renderHook(() => useExportAnalytics(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        result.current.mutate({
          format: 'pdf',
          includeCharts: true,
        });
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(mockedApi.post).toHaveBeenCalledWith(
        '/analytics/export',
        {
          format: 'pdf',
          filters: undefined,
          includeCharts: true,
        },
        {
          responseType: 'blob',
        }
      );
      expect(result.current.data).toEqual(mockBlob);
    });

    it('should export analytics as CSV', async () => {
      const mockBlob = new Blob(['csv data']);
      mockedApi.post.mockResolvedValueOnce(mockBlob);

      const { result } = renderHook(() => useExportAnalytics(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        result.current.mutate({
          format: 'csv',
          includeCharts: false,
        });
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(mockedApi.post).toHaveBeenCalledWith(
        '/analytics/export',
        {
          format: 'csv',
          filters: undefined,
          includeCharts: false,
        },
        {
          responseType: 'blob',
        }
      );
    });

    it('should handle export errors', async () => {
      const apiError = { message: 'Export failed', status: 500 };
      mockedApi.post.mockRejectedValueOnce(apiError);

      const { result } = renderHook(() => useExportAnalytics(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        result.current.mutate({ format: 'pdf' });
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toEqual(apiError);
    });
  });

  describe('useRefreshMetrics', () => {
    it('should refresh metrics', async () => {
      const mockRefreshedMetrics = analyticsMockResponses.currentMetrics;
      mockedApi.post.mockResolvedValueOnce(mockRefreshedMetrics);

      const { result } = renderHook(() => useRefreshMetrics(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        result.current.mutate();
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(mockedApi.post).toHaveBeenCalledWith('/analytics/metrics/refresh', {});
      expect(result.current.data).toEqual(mockRefreshedMetrics);
    });

    it('should handle refresh errors', async () => {
      const apiError = { message: 'Refresh failed', status: 500 };
      mockedApi.post.mockRejectedValueOnce(apiError);

      const { result } = renderHook(() => useRefreshMetrics(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        result.current.mutate();
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toEqual(apiError);
    });
  });
});
