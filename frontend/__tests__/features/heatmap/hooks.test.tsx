/**
 * Tests for heatmap hooks
 * Tests data fetching, caching, mutations, and query invalidation
 */

import { renderHook, waitFor, act } from '@/test-utils';
import {
  useHeatmapData,
  useCoverageHeatmap,
  useWorkloadHeatmap,
  useRotationCoverageComparison,
  useAvailableRotations,
  useExportHeatmap,
  useDownloadHeatmap,
  usePrefetchHeatmap,
  useInvalidateHeatmaps,
  heatmapQueryKeys,
} from '@/features/heatmap/hooks';
import { heatmapMockFactories, heatmapMockResponses } from './heatmap-mocks';
import { createWrapper } from '../../utils/test-utils';
import * as api from '@/lib/api';

// Mock the api module
jest.mock('@/lib/api', () => ({
  get: jest.fn(),
  post: jest.fn(),
}));

const mockedApi = api as jest.Mocked<typeof api>;

describe('Heatmap Query Hooks', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('useHeatmapData', () => {
    it('should fetch heatmap data with filters', async () => {
      const filters = heatmapMockFactories.filters();
      mockedApi.get.mockResolvedValueOnce(heatmapMockResponses.heatmapData);

      const { result } = renderHook(() => useHeatmapData(filters), {
        wrapper: createWrapper(),
      });

      expect(result.current.isLoading).toBe(true);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('/visualization/heatmap')
      );
      expect(result.current.data).toEqual(heatmapMockResponses.heatmapData);
    });

    it('should build correct query string with all filters', async () => {
      const filters = heatmapMockFactories.filters({
        startDate: '2024-01-01',
        endDate: '2024-01-31',
        personIds: ['person-1', 'person-2'],
        rotationIds: ['rotation-1'],
        includeFmit: false,
        groupBy: 'person',
      });

      mockedApi.get.mockResolvedValueOnce(heatmapMockResponses.heatmapData);

      const { result } = renderHook(() => useHeatmapData(filters), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      const callArg = mockedApi.get.mock.calls[0][0];

      expect(callArg).toContain('startDate=2024-01-01');
      expect(callArg).toContain('endDate=2024-01-31');
      // Commas get URL-encoded as %2C
      expect(callArg).toContain('personIds=');
      expect(callArg).toContain('person-1');
      expect(callArg).toContain('person-2');
      expect(callArg).toContain('rotationIds=rotation-1');
      expect(callArg).toContain('includeFmit=false');
      expect(callArg).toContain('groupBy=week');
    });

    it('should handle empty filters', async () => {
      const emptyFilters = {};
      mockedApi.get.mockResolvedValueOnce(heatmapMockResponses.heatmapData);

      const { result } = renderHook(() => useHeatmapData(emptyFilters), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(mockedApi.get).toHaveBeenCalledWith('/visualization/heatmap');
    });

    it('should handle API errors', async () => {
      const filters = heatmapMockFactories.filters();
      const apiError = { message: 'Server error', status: 500 };
      mockedApi.get.mockRejectedValueOnce(apiError);

      const { result } = renderHook(() => useHeatmapData(filters), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toEqual(apiError);
    });

    it('should cache heatmap data', async () => {
      const filters = heatmapMockFactories.filters();
      mockedApi.get.mockResolvedValue(heatmapMockResponses.heatmapData);

      const { result, rerender } = renderHook(() => useHeatmapData(filters), {
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

  describe('useCoverageHeatmap', () => {
    it('should fetch coverage heatmap data', async () => {
      const dateRange = heatmapMockFactories.dateRange();
      mockedApi.get.mockResolvedValueOnce(heatmapMockResponses.coverageHeatmap);

      const { result } = renderHook(() => useCoverageHeatmap(dateRange), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('/visualization/heatmap/coverage')
      );
      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('startDate=2024-01-01')
      );
      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('endDate=2024-01-31')
      );
      expect(result.current.data).toEqual(heatmapMockResponses.coverageHeatmap);
    });

    it('should handle API errors', async () => {
      const dateRange = heatmapMockFactories.dateRange();
      const apiError = { message: 'Failed to fetch coverage data', status: 500 };
      mockedApi.get.mockRejectedValueOnce(apiError);

      const { result } = renderHook(() => useCoverageHeatmap(dateRange), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toEqual(apiError);
    });

    it('should use correct query key', async () => {
      const dateRange = heatmapMockFactories.dateRange();
      mockedApi.get.mockResolvedValueOnce(heatmapMockResponses.coverageHeatmap);

      const { result } = renderHook(() => useCoverageHeatmap(dateRange), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      const expectedKey = heatmapQueryKeys.coverage(dateRange);
      expect(expectedKey).toEqual(['heatmap', 'coverage', dateRange]);
    });
  });

  describe('useWorkloadHeatmap', () => {
    it('should fetch workload heatmap data', async () => {
      const personIds = ['person-1', 'person-2'];
      const dateRange = heatmapMockFactories.dateRange();
      mockedApi.get.mockResolvedValueOnce(heatmapMockResponses.workloadHeatmap);

      const { result } = renderHook(() => useWorkloadHeatmap(personIds, dateRange), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('/visualization/heatmap/workload')
      );
      // Commas get URL-encoded as %2C
      const callArg = mockedApi.get.mock.calls[0][0];
      expect(callArg).toContain('personIds=');
      expect(callArg).toContain('person-1');
      expect(callArg).toContain('person-2');
      expect(result.current.data).toEqual(heatmapMockResponses.workloadHeatmap);
    });

    it('should not fetch when person IDs array is empty', async () => {
      const personIds: string[] = [];
      const dateRange = heatmapMockFactories.dateRange();

      const { result } = renderHook(() => useWorkloadHeatmap(personIds, dateRange), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isPending).toBe(true);
      });

      expect(mockedApi.get).not.toHaveBeenCalled();
    });

    it('should handle API errors', async () => {
      const personIds = ['person-1'];
      const dateRange = heatmapMockFactories.dateRange();
      const apiError = { message: 'Failed to fetch workload data', status: 500 };
      mockedApi.get.mockRejectedValueOnce(apiError);

      const { result } = renderHook(() => useWorkloadHeatmap(personIds, dateRange), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toEqual(apiError);
    });

    it('should use correct query key', async () => {
      const personIds = ['person-1'];
      const dateRange = heatmapMockFactories.dateRange();
      mockedApi.get.mockResolvedValueOnce(heatmapMockResponses.workloadHeatmap);

      const { result } = renderHook(() => useWorkloadHeatmap(personIds, dateRange), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      const expectedKey = heatmapQueryKeys.workload(personIds, dateRange);
      expect(expectedKey).toEqual(['heatmap', 'workload', personIds, dateRange]);
    });
  });

  describe('useRotationCoverageComparison', () => {
    it('should fetch rotation coverage comparison', async () => {
      const dateRange = heatmapMockFactories.dateRange();
      const rotationIds = ['rotation-1', 'rotation-2'];
      mockedApi.get.mockResolvedValueOnce(heatmapMockResponses.heatmapData);

      const { result } = renderHook(
        () => useRotationCoverageComparison(dateRange, rotationIds),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('/visualization/heatmap/rotation-comparison')
      );
      // Commas get URL-encoded as %2C
      const callArg = mockedApi.get.mock.calls[0][0];
      expect(callArg).toContain('rotationIds=');
      expect(callArg).toContain('rotation-1');
      expect(callArg).toContain('rotation-2');
    });

    it('should fetch without rotation IDs filter', async () => {
      const dateRange = heatmapMockFactories.dateRange();
      mockedApi.get.mockResolvedValueOnce(heatmapMockResponses.heatmapData);

      const { result } = renderHook(() => useRotationCoverageComparison(dateRange), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('/visualization/heatmap/rotation-comparison')
      );
      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.not.stringContaining('rotationIds')
      );
    });

    it('should handle API errors', async () => {
      const dateRange = heatmapMockFactories.dateRange();
      const apiError = { message: 'Comparison failed', status: 500 };
      mockedApi.get.mockRejectedValueOnce(apiError);

      const { result } = renderHook(() => useRotationCoverageComparison(dateRange), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toEqual(apiError);
    });
  });

  describe('useAvailableRotations', () => {
    it('should fetch available rotations', async () => {
      mockedApi.get.mockResolvedValueOnce(heatmapMockResponses.availableRotations);

      const { result } = renderHook(() => useAvailableRotations(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(mockedApi.get).toHaveBeenCalledWith('/visualization/rotations');
      expect(result.current.data).toEqual(heatmapMockResponses.availableRotations);
    });

    it('should handle API errors', async () => {
      const apiError = { message: 'Failed to fetch rotations', status: 500 };
      mockedApi.get.mockRejectedValueOnce(apiError);

      const { result } = renderHook(() => useAvailableRotations(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toEqual(apiError);
    });

    it('should cache rotations with longer stale time', async () => {
      mockedApi.get.mockResolvedValue(heatmapMockResponses.availableRotations);

      const { result, rerender } = renderHook(() => useAvailableRotations(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(mockedApi.get).toHaveBeenCalledTimes(1);

      // Rerender should use cached data
      rerender();

      expect(mockedApi.get).toHaveBeenCalledTimes(1);
    });
  });
});

describe('Heatmap Mutation Hooks', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('useExportHeatmap', () => {
    it('should export heatmap as PNG', async () => {
      const mockBlob = new Blob(['test data']);
      mockedApi.post.mockResolvedValueOnce(mockBlob);

      const { result } = renderHook(() => useExportHeatmap(), {
        wrapper: createWrapper(),
      });

      const exportConfig = heatmapMockFactories.exportConfig({
        format: 'png',
      });

      await act(async () => {
        result.current.mutate(exportConfig);
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(mockedApi.post).toHaveBeenCalledWith(
        '/visualization/heatmap/export',
        exportConfig,
        {
          responseType: 'blob',
        }
      );
      expect(result.current.data).toEqual(mockBlob);
    });

    it('should export heatmap as SVG', async () => {
      const mockBlob = new Blob(['svg data']);
      mockedApi.post.mockResolvedValueOnce(mockBlob);

      const { result } = renderHook(() => useExportHeatmap(), {
        wrapper: createWrapper(),
      });

      const exportConfig = heatmapMockFactories.exportConfig({
        format: 'svg',
      });

      await act(async () => {
        result.current.mutate(exportConfig);
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(mockedApi.post).toHaveBeenCalledWith(
        '/visualization/heatmap/export',
        exportConfig,
        {
          responseType: 'blob',
        }
      );
    });

    it('should handle export errors', async () => {
      const apiError = { message: 'Export failed', status: 500 };
      mockedApi.post.mockRejectedValueOnce(apiError);

      const { result } = renderHook(() => useExportHeatmap(), {
        wrapper: createWrapper(),
      });

      const exportConfig = heatmapMockFactories.exportConfig();

      await act(async () => {
        result.current.mutate(exportConfig);
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toEqual(apiError);
    });

    it('should export with custom dimensions', async () => {
      const mockBlob = new Blob(['test data']);
      mockedApi.post.mockResolvedValueOnce(mockBlob);

      const { result } = renderHook(() => useExportHeatmap(), {
        wrapper: createWrapper(),
      });

      const exportConfig = heatmapMockFactories.exportConfig({
        width: 1600,
        height: 1000,
      });

      await act(async () => {
        result.current.mutate(exportConfig);
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(mockedApi.post).toHaveBeenCalledWith(
        '/visualization/heatmap/export',
        expect.objectContaining({
          width: 1600,
          height: 1000,
        }),
        expect.any(Object)
      );
    });
  });

  describe('useDownloadHeatmap', () => {
    // Mock DOM methods for download
    let createElementSpy: jest.SpyInstance;
    let createObjectURLSpy: jest.Mock;
    let revokeObjectURLSpy: jest.Mock;
    let appendChildSpy: jest.SpyInstance;
    let removeChildSpy: jest.SpyInstance;
    let mockLink: any;

    beforeEach(() => {
      mockLink = {
        href: '',
        download: '',
        click: jest.fn(),
      };

      // Only mock createElement for 'a' elements, pass through for others
      const originalCreateElement = document.createElement.bind(document);
      createElementSpy = jest.spyOn(document, 'createElement').mockImplementation((tagName: string) => {
        if (tagName === 'a') {
          return mockLink;
        }
        return originalCreateElement(tagName);
      });

      // Mock URL methods
      createObjectURLSpy = jest.fn().mockReturnValue('blob:url');
      revokeObjectURLSpy = jest.fn();
      (global as any).URL = {
        createObjectURL: createObjectURLSpy,
        revokeObjectURL: revokeObjectURLSpy,
      };

      appendChildSpy = jest.spyOn(document.body, 'appendChild').mockImplementation((node) => node as any);
      removeChildSpy = jest.spyOn(document.body, 'removeChild').mockImplementation((node) => node as any);
    });

    afterEach(() => {
      createElementSpy.mockRestore();
      appendChildSpy.mockRestore();
      removeChildSpy.mockRestore();
      delete (global as any).URL;
    });

    it('should download heatmap with custom filename', async () => {
      const mockBlob = new Blob(['test data']);
      mockedApi.post.mockResolvedValueOnce(mockBlob);

      const { result } = renderHook(() => useDownloadHeatmap(), {
        wrapper: createWrapper(),
      });

      const exportConfig = heatmapMockFactories.exportConfig({
        format: 'png',
      });

      await act(async () => {
        await result.current.download(exportConfig, 'custom-heatmap.png');
      });

      await waitFor(() => {
        expect(createObjectURLSpy).toHaveBeenCalledWith(mockBlob);
      });

      expect(appendChildSpy).toHaveBeenCalled();
      expect(removeChildSpy).toHaveBeenCalled();
      expect(revokeObjectURLSpy).toHaveBeenCalledWith('blob:url');
    });

    it('should download with auto-generated filename', async () => {
      const mockBlob = new Blob(['test data']);
      mockedApi.post.mockResolvedValueOnce(mockBlob);

      const { result } = renderHook(() => useDownloadHeatmap(), {
        wrapper: createWrapper(),
      });

      const exportConfig = heatmapMockFactories.exportConfig({
        format: 'svg',
      });

      await act(async () => {
        await result.current.download(exportConfig);
      });

      await waitFor(() => {
        expect(createObjectURLSpy).toHaveBeenCalledWith(mockBlob);
      });

      // Should create element with auto-generated filename
      expect(createElementSpy).toHaveBeenCalledWith('a');
    });

    it('should handle download errors', async () => {
      const apiError = { message: 'Download failed', status: 500 };
      mockedApi.post.mockRejectedValueOnce(apiError);

      const { result } = renderHook(() => useDownloadHeatmap(), {
        wrapper: createWrapper(),
      });

      const exportConfig = heatmapMockFactories.exportConfig();

      await expect(async () => {
        await result.current.download(exportConfig);
      }).rejects.toEqual(apiError);
    });
  });
});

describe('Heatmap Utility Hooks', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('usePrefetchHeatmap', () => {
    it('should prefetch heatmap data', async () => {
      const filters = heatmapMockFactories.filters();
      mockedApi.get.mockResolvedValueOnce(heatmapMockResponses.heatmapData);

      const { result } = renderHook(() => usePrefetchHeatmap(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        result.current(filters);
      });

      // Give time for prefetch to execute
      await waitFor(() => {
        expect(mockedApi.get).toHaveBeenCalledWith(
          expect.stringContaining('/visualization/heatmap')
        );
      });
    });

    it('should prefetch with correct filters', async () => {
      const filters = heatmapMockFactories.filters({
        startDate: '2024-01-01',
        personIds: ['person-1'],
      });
      mockedApi.get.mockResolvedValueOnce(heatmapMockResponses.heatmapData);

      const { result } = renderHook(() => usePrefetchHeatmap(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        result.current(filters);
      });

      await waitFor(() => {
        expect(mockedApi.get).toHaveBeenCalledWith(
          expect.stringContaining('startDate=2024-01-01')
        );
      });
    });
  });

  describe('useInvalidateHeatmaps', () => {
    it('should return invalidate function', () => {
      const { result } = renderHook(() => useInvalidateHeatmaps(), {
        wrapper: createWrapper(),
      });

      expect(typeof result.current).toBe('function');
    });

    it('should call invalidate without errors', async () => {
      const { result } = renderHook(() => useInvalidateHeatmaps(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        result.current();
      });

      // Should not throw error
      expect(result.current).toBeDefined();
    });
  });
});

describe('Query Keys', () => {
  it('should generate correct coverage query key', () => {
    const dateRange = heatmapMockFactories.dateRange();
    const key = heatmapQueryKeys.coverage(dateRange);

    expect(key).toEqual(['heatmap', 'coverage', dateRange]);
  });

  it('should generate correct workload query key', () => {
    const personIds = ['person-1', 'person-2'];
    const dateRange = heatmapMockFactories.dateRange();
    const key = heatmapQueryKeys.workload(personIds, dateRange);

    expect(key).toEqual(['heatmap', 'workload', personIds, dateRange]);
  });

  it('should generate correct custom query key', () => {
    const filters = heatmapMockFactories.filters();
    const key = heatmapQueryKeys.custom(filters);

    expect(key).toEqual(['heatmap', 'custom', filters]);
  });

  it('should generate correct rotations query key', () => {
    const key = heatmapQueryKeys.rotations();

    expect(key).toEqual(['heatmap', 'rotations']);
  });

  it('should generate base query key', () => {
    const key = heatmapQueryKeys.all;

    expect(key).toEqual(['heatmap']);
  });
});
