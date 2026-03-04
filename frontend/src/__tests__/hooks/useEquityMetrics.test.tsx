/**
 * useEquityMetrics Hook Tests
 *
 * Tests for equity metrics calculation including Gini coefficient
 * and helper functions for color coding and labels.
 */
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import * as api from '@/lib/api';
import {
  useEquityMetrics,
  getGiniColorClass,
  getGiniLabel,
  type EquityMetricsResponse,
} from '@/hooks/useEquityMetrics';

// Mock the api module
jest.mock('@/lib/api');

const mockedApi = api as jest.Mocked<typeof api>;

// Mock data
const mockEquitableResponse: EquityMetricsResponse = {
  giniCoefficient: 0.12,
  isEquitable: true,
  meanWorkload: 160,
  stdWorkload: 15,
  mostOverloadedProvider: 'provider-2',
  mostUnderloadedProvider: 'provider-3',
  maxWorkload: 175,
  minWorkload: 145,
  recommendations: [],
  interpretation: 'Workload is equitably distributed',
};

const mockModerateResponse: EquityMetricsResponse = {
  giniCoefficient: 0.18,
  isEquitable: false,
  meanWorkload: 160,
  stdWorkload: 25,
  mostOverloadedProvider: 'provider-1',
  mostUnderloadedProvider: 'provider-4',
  maxWorkload: 200,
  minWorkload: 120,
  recommendations: [
    'Consider redistributing 15 hours from provider-1 to provider-4',
  ],
  interpretation: 'Moderate inequality detected',
};

const mockHighInequalityResponse: EquityMetricsResponse = {
  giniCoefficient: 0.35,
  isEquitable: false,
  meanWorkload: 160,
  stdWorkload: 50,
  mostOverloadedProvider: 'provider-1',
  mostUnderloadedProvider: 'provider-5',
  maxWorkload: 240,
  minWorkload: 80,
  recommendations: [
    'Immediate rebalancing required',
    'Redistribute 60 hours from provider-1',
  ],
  interpretation: 'High inequality - immediate action required',
};

/* eslint-disable @typescript-eslint/naming-convention -- ID keys */
const mockProviderHours: Record<string, number> = {
  'provider-1': 175,
  'provider-2': 165,
  'provider-3': 155,
  'provider-4': 160,
};
/* eslint-enable @typescript-eslint/naming-convention */

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
  });
}

// Wrapper component with QueryClientProvider
function createWrapper() {
  const queryClient = createTestQueryClient();
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
}

describe('useEquityMetrics', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should calculate equity metrics successfully', async () => {
    mockedApi.post.mockResolvedValueOnce(mockEquitableResponse);

    const { result } = renderHook(
      () => useEquityMetrics(mockProviderHours),
      { wrapper: createWrapper() }
    );

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockEquitableResponse);
    expect(mockedApi.post).toHaveBeenCalledWith(
      '/mcp/calculate-equity-metrics',
      {
        providerHours: mockProviderHours,
        intensityWeights: null,
      }
    );
  });

  it('should include intensity weights if provided', async () => {
    mockedApi.post.mockResolvedValueOnce(mockEquitableResponse);

    /* eslint-disable @typescript-eslint/naming-convention -- ID keys */
    const intensityWeights = {
      'provider-1': 1.5,
      'provider-2': 1.0,
    };
    /* eslint-enable @typescript-eslint/naming-convention */

    const { result } = renderHook(
      () => useEquityMetrics(mockProviderHours, intensityWeights),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockedApi.post).toHaveBeenCalledWith(
      '/mcp/calculate-equity-metrics',
      {
        providerHours: mockProviderHours,
        intensityWeights: intensityWeights,
      }
    );
  });

  it('should handle equitable distribution', async () => {
    mockedApi.post.mockResolvedValueOnce(mockEquitableResponse);

    const { result } = renderHook(
      () => useEquityMetrics(mockProviderHours),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.giniCoefficient).toBeLessThan(0.15);
    expect(result.current.data?.isEquitable).toBe(true);
  });

  it('should handle moderate inequality', async () => {
    mockedApi.post.mockResolvedValueOnce(mockModerateResponse);

    const { result } = renderHook(
      () => useEquityMetrics(mockProviderHours),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.giniCoefficient).toBeGreaterThanOrEqual(0.15);
    expect(result.current.data?.giniCoefficient).toBeLessThan(0.25);
    expect(result.current.data?.isEquitable).toBe(false);
  });

  it('should handle high inequality', async () => {
    mockedApi.post.mockResolvedValueOnce(mockHighInequalityResponse);

    const { result } = renderHook(
      () => useEquityMetrics(mockProviderHours),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.giniCoefficient).toBeGreaterThanOrEqual(0.25);
    expect(result.current.data?.recommendations).toHaveLength(2);
  });

  it('should not fetch if provider hours is null', () => {
    const { result } = renderHook(() => useEquityMetrics(null), {
      wrapper: createWrapper(),
    });

    expect(result.current.isFetching).toBe(false);
    expect(mockedApi.post).not.toHaveBeenCalled();
  });

  it('should not fetch if provider hours is empty', () => {
    const { result } = renderHook(() => useEquityMetrics({}), {
      wrapper: createWrapper(),
    });

    expect(result.current.isFetching).toBe(false);
    expect(mockedApi.post).not.toHaveBeenCalled();
  });

  it('should return default values for empty input', async () => {
    const { result } = renderHook(() => useEquityMetrics(null), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.data).toBeUndefined();
    });
  });

  it('should handle API errors', async () => {
    const apiError = { message: 'MCP tool unavailable', status: 503 };
    mockedApi.post.mockRejectedValueOnce(apiError);

    const { result } = renderHook(
      () => useEquityMetrics(mockProviderHours),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toEqual(apiError);
  });

  it('should show workload statistics', async () => {
    mockedApi.post.mockResolvedValueOnce(mockEquitableResponse);

    const { result } = renderHook(
      () => useEquityMetrics(mockProviderHours),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.meanWorkload).toBe(160);
    expect(result.current.data?.stdWorkload).toBe(15);
    expect(result.current.data?.maxWorkload).toBe(175);
    expect(result.current.data?.minWorkload).toBe(145);
  });

  it('should identify overloaded and underloaded providers', async () => {
    mockedApi.post.mockResolvedValueOnce(mockModerateResponse);

    const { result } = renderHook(
      () => useEquityMetrics(mockProviderHours),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.mostOverloadedProvider).toBe('provider-1');
    expect(result.current.data?.mostUnderloadedProvider).toBe('provider-4');
  });

  it('should provide recommendations for rebalancing', async () => {
    mockedApi.post.mockResolvedValueOnce(mockModerateResponse);

    const { result } = renderHook(
      () => useEquityMetrics(mockProviderHours),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.recommendations.length).toBeGreaterThan(0);
  });

  it('should provide human-readable interpretation', async () => {
    mockedApi.post.mockResolvedValueOnce(mockEquitableResponse);

    const { result } = renderHook(
      () => useEquityMetrics(mockProviderHours),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.interpretation).toBeTruthy();
    expect(typeof result.current.data?.interpretation).toBe('string');
  });
});

describe('getGiniColorClass', () => {
  it('should return green for equitable distribution', () => {
    expect(getGiniColorClass(0.10)).toBe('text-green-500');
    expect(getGiniColorClass(0.14)).toBe('text-green-500');
  });

  it('should return yellow for moderate inequality', () => {
    expect(getGiniColorClass(0.15)).toBe('text-yellow-500');
    expect(getGiniColorClass(0.20)).toBe('text-yellow-500');
    expect(getGiniColorClass(0.24)).toBe('text-yellow-500');
  });

  it('should return red for high inequality', () => {
    expect(getGiniColorClass(0.25)).toBe('text-red-500');
    expect(getGiniColorClass(0.35)).toBe('text-red-500');
    expect(getGiniColorClass(0.50)).toBe('text-red-500');
  });

  it('should handle boundary values', () => {
    expect(getGiniColorClass(0.0)).toBe('text-green-500');
    expect(getGiniColorClass(0.149)).toBe('text-green-500');
    expect(getGiniColorClass(0.150)).toBe('text-yellow-500');
    expect(getGiniColorClass(0.249)).toBe('text-yellow-500');
    expect(getGiniColorClass(0.250)).toBe('text-red-500');
    expect(getGiniColorClass(1.0)).toBe('text-red-500');
  });
});

describe('getGiniLabel', () => {
  it('should return "Equitable" for low Gini', () => {
    expect(getGiniLabel(0.10)).toBe('Equitable');
    expect(getGiniLabel(0.14)).toBe('Equitable');
  });

  it('should return "Moderate Inequality" for medium Gini', () => {
    expect(getGiniLabel(0.15)).toBe('Moderate Inequality');
    expect(getGiniLabel(0.20)).toBe('Moderate Inequality');
    expect(getGiniLabel(0.24)).toBe('Moderate Inequality');
  });

  it('should return "High Inequality" for high Gini', () => {
    expect(getGiniLabel(0.25)).toBe('High Inequality');
    expect(getGiniLabel(0.35)).toBe('High Inequality');
    expect(getGiniLabel(0.50)).toBe('High Inequality');
  });

  it('should handle boundary values', () => {
    expect(getGiniLabel(0.0)).toBe('Equitable');
    expect(getGiniLabel(0.149)).toBe('Equitable');
    expect(getGiniLabel(0.150)).toBe('Moderate Inequality');
    expect(getGiniLabel(0.249)).toBe('Moderate Inequality');
    expect(getGiniLabel(0.250)).toBe('High Inequality');
    expect(getGiniLabel(1.0)).toBe('High Inequality');
  });
});
