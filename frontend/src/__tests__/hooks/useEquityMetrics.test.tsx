/**
 * useEquityMetrics Hook Tests
 *
 * Tests for equity metrics hooks including Gini coefficient calculation,
 * helper functions for color/label, and MCP tool integration.
 */
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import * as api from '@/lib/api';
import {
  useEquityMetrics,
  getGiniColorClass,
  getGiniLabel,
} from '@/hooks/useEquityMetrics';

// Mock the api module
jest.mock('@/lib/api');

const mockedApi = api as jest.Mocked<typeof api>;

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

// Mock equity metrics response
const mockEquitableResponse = {
  giniCoefficient: 0.12,
  is_equitable: true,
  mean_workload: 120,
  std_workload: 10,
  most_overloaded_provider: 'provider-2',
  most_underloaded_provider: 'provider-1',
  max_workload: 130,
  min_workload: 110,
  recommendations: ['Workload is well balanced'],
  interpretation: 'Distribution is equitable (Gini < 0.15)',
};

const mockInequitableResponse = {
  giniCoefficient: 0.35,
  is_equitable: false,
  mean_workload: 120,
  std_workload: 40,
  most_overloaded_provider: 'provider-1',
  most_underloaded_provider: 'provider-3',
  max_workload: 200,
  min_workload: 40,
  recommendations: [
    'Consider redistributing workload',
    'Provider provider-1 has significantly higher workload',
  ],
  interpretation: 'High inequality detected (Gini >= 0.25)',
};

describe('useEquityMetrics', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should calculate equity metrics successfully', async () => {
    mockedApi.post.mockResolvedValueOnce(mockEquitableResponse);

    const providerHours = {
      'provider-1': 110,
      'provider-2': 130,
      'provider-3': 120,
    };

    const { result } = renderHook(() => useEquityMetrics(providerHours), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.giniCoefficient).toBe(0.12);
    expect(result.current.data?.is_equitable).toBe(true);
    expect(result.current.data?.mean_workload).toBe(120);
    expect(mockedApi.post).toHaveBeenCalledWith(
      '/mcp/calculate-equity-metrics',
      expect.objectContaining({
        provider_hours: providerHours,
      })
    );
  });

  it('should include intensity weights when provided', async () => {
    mockedApi.post.mockResolvedValueOnce(mockEquitableResponse);

    const providerHours = {
      'provider-1': 100,
      'provider-2': 100,
    };
    const intensityWeights = {
      'provider-1': 1.5, // Night shift multiplier
      'provider-2': 1.0,
    };

    const { result } = renderHook(
      () => useEquityMetrics(providerHours, intensityWeights),
      {
        wrapper: createWrapper(),
      }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockedApi.post).toHaveBeenCalledWith(
      '/mcp/calculate-equity-metrics',
      expect.objectContaining({
        provider_hours: providerHours,
        intensity_weights: intensityWeights,
      })
    );
  });

  it('should be disabled for empty provider hours', () => {
    const { result } = renderHook(() => useEquityMetrics({}), {
      wrapper: createWrapper(),
    });

    // Query should be disabled, not loading
    expect(result.current.isLoading).toBe(false);
    expect(result.current.isFetching).toBe(false);
    expect(mockedApi.post).not.toHaveBeenCalled();
  });

  it('should be disabled when provider hours is null', () => {
    const { result } = renderHook(() => useEquityMetrics(null), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.isFetching).toBe(false);
  });

  it('should detect high inequality', async () => {
    mockedApi.post.mockResolvedValueOnce(mockInequitableResponse);

    const providerHours = {
      'provider-1': 200,
      'provider-2': 100,
      'provider-3': 40,
    };

    const { result } = renderHook(() => useEquityMetrics(providerHours), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.giniCoefficient).toBe(0.35);
    expect(result.current.data?.is_equitable).toBe(false);
    expect(result.current.data?.recommendations).toContain(
      'Consider redistributing workload'
    );
  });

  it('should identify overloaded and underloaded providers', async () => {
    mockedApi.post.mockResolvedValueOnce(mockInequitableResponse);

    const providerHours = {
      'provider-1': 200,
      'provider-2': 100,
      'provider-3': 40,
    };

    const { result } = renderHook(() => useEquityMetrics(providerHours), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.most_overloaded_provider).toBe('provider-1');
    expect(result.current.data?.most_underloaded_provider).toBe('provider-3');
    expect(result.current.data?.max_workload).toBe(200);
    expect(result.current.data?.min_workload).toBe(40);
  });

  it('should handle API errors gracefully', async () => {
    const apiError = { message: 'MCP tool unavailable', status: 503 };
    mockedApi.post.mockRejectedValueOnce(apiError);

    const providerHours = {
      'provider-1': 100,
      'provider-2': 100,
    };

    const { result } = renderHook(() => useEquityMetrics(providerHours), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toEqual(apiError);
  });

  it('should calculate statistics correctly', async () => {
    mockedApi.post.mockResolvedValueOnce(mockEquitableResponse);

    const providerHours = {
      'provider-1': 110,
      'provider-2': 130,
      'provider-3': 120,
    };

    const { result } = renderHook(() => useEquityMetrics(providerHours), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.mean_workload).toBe(120);
    expect(result.current.data?.std_workload).toBe(10);
  });

  it('should handle single provider case', async () => {
    const singleProviderResponse = {
      giniCoefficient: 0.0,
      is_equitable: true,
      mean_workload: 100,
      std_workload: 0,
      most_overloaded_provider: 'provider-1',
      most_underloaded_provider: 'provider-1',
      max_workload: 100,
      min_workload: 100,
      recommendations: ['Only one provider - no comparison possible'],
      interpretation: 'Single provider scenario',
    };

    mockedApi.post.mockResolvedValueOnce(singleProviderResponse);

    const providerHours = {
      'provider-1': 100,
    };

    const { result } = renderHook(() => useEquityMetrics(providerHours), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.giniCoefficient).toBe(0.0);
    expect(result.current.data?.std_workload).toBe(0);
  });
});

// ============================================================================
// Helper Function Tests
// ============================================================================

describe('getGiniColorClass', () => {
  it('should return green for equitable distribution (< 0.15)', () => {
    expect(getGiniColorClass(0.0)).toBe('text-green-500');
    expect(getGiniColorClass(0.1)).toBe('text-green-500');
    expect(getGiniColorClass(0.14)).toBe('text-green-500');
  });

  it('should return yellow for moderate inequality (0.15-0.25)', () => {
    expect(getGiniColorClass(0.15)).toBe('text-yellow-500');
    expect(getGiniColorClass(0.2)).toBe('text-yellow-500');
    expect(getGiniColorClass(0.24)).toBe('text-yellow-500');
  });

  it('should return red for high inequality (>= 0.25)', () => {
    expect(getGiniColorClass(0.25)).toBe('text-red-500');
    expect(getGiniColorClass(0.35)).toBe('text-red-500');
    expect(getGiniColorClass(0.5)).toBe('text-red-500');
    expect(getGiniColorClass(1.0)).toBe('text-red-500');
  });

  it('should handle edge cases', () => {
    expect(getGiniColorClass(0.0)).toBe('text-green-500');
    expect(getGiniColorClass(1.0)).toBe('text-red-500');
  });
});

describe('getGiniLabel', () => {
  it('should return "Equitable" for low Gini (< 0.15)', () => {
    expect(getGiniLabel(0.0)).toBe('Equitable');
    expect(getGiniLabel(0.1)).toBe('Equitable');
    expect(getGiniLabel(0.14)).toBe('Equitable');
  });

  it('should return "Moderate Inequality" for mid-range Gini (0.15-0.25)', () => {
    expect(getGiniLabel(0.15)).toBe('Moderate Inequality');
    expect(getGiniLabel(0.2)).toBe('Moderate Inequality');
    expect(getGiniLabel(0.24)).toBe('Moderate Inequality');
  });

  it('should return "High Inequality" for high Gini (>= 0.25)', () => {
    expect(getGiniLabel(0.25)).toBe('High Inequality');
    expect(getGiniLabel(0.35)).toBe('High Inequality');
    expect(getGiniLabel(0.5)).toBe('High Inequality');
    expect(getGiniLabel(1.0)).toBe('High Inequality');
  });

  it('should handle edge cases', () => {
    expect(getGiniLabel(0.0)).toBe('Equitable');
    expect(getGiniLabel(1.0)).toBe('High Inequality');
  });

  it('should use consistent thresholds with color class', () => {
    // These should match the thresholds in getGiniColorClass
    const testValues = [0.0, 0.14, 0.15, 0.24, 0.25, 1.0];

    testValues.forEach((gini) => {
      const color = getGiniColorClass(gini);
      const label = getGiniLabel(gini);

      if (color === 'text-green-500') {
        expect(label).toBe('Equitable');
      } else if (color === 'text-yellow-500') {
        expect(label).toBe('Moderate Inequality');
      } else if (color === 'text-red-500') {
        expect(label).toBe('High Inequality');
      }
    });
  });
});
