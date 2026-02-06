/**
 * Tests for useEnergyLandscape Hook
 *
 * Tests energy landscape analysis mutation including successful requests,
 * optional parameters, error handling, and pending states.
 */
import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import { useEnergyLandscape } from '@/hooks/useEnergyLandscape';

// Mock the API module
jest.mock('@/api/exotic-resilience', () => ({
  analyzeEnergyLandscape: jest.fn(),
}));

import { analyzeEnergyLandscape } from '@/api/exotic-resilience';

const mockedAnalyze = analyzeEnergyLandscape as jest.Mock;

// Test data - camelCase keys (axios interceptor converts from snake_case)
const mockEnergyLandscapeResponse = {
  currentEnergy: -0.742,
  isLocalMinimum: true,
  estimatedBasinSize: 15,
  meanBarrierHeight: 0.234,
  meanGradient: 0.012,
  landscapeRuggedness: 0.456,
  numLocalMinima: 7,
  interpretation:
    'Schedule is in a stable local minimum with moderate landscape ruggedness.',
  recommendations: [
    'Consider perturbation to explore nearby minima',
    'Monitor barrier heights for stability',
  ],
  computedAt: '2026-02-05T14:30:00Z',
  source: 'hopfield_energy_landscape',
};

const mockRequestWithScheduleId = {
  scheduleId: 'schedule-abc-123',
};

const mockEmptyRequest = {};

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

describe('useEnergyLandscape', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('handles successful analysis with correct endpoint and data', async () => {
    mockedAnalyze.mockResolvedValueOnce(mockEnergyLandscapeResponse);

    const { result } = renderHook(() => useEnergyLandscape(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate(mockEmptyRequest);
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockEnergyLandscapeResponse);
    // mutationFn receives (variables, context) - check first arg
    expect(mockedAnalyze.mock.calls[0][0]).toEqual(mockEmptyRequest);
  });

  it('passes optional scheduleId through to the API', async () => {
    mockedAnalyze.mockResolvedValueOnce(mockEnergyLandscapeResponse);

    const { result } = renderHook(() => useEnergyLandscape(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate(mockRequestWithScheduleId);
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockedAnalyze.mock.calls[0][0]).toEqual(mockRequestWithScheduleId);
    expect(result.current.data).toEqual(mockEnergyLandscapeResponse);
  });

  it('works with empty request object', async () => {
    mockedAnalyze.mockResolvedValueOnce(mockEnergyLandscapeResponse);

    const { result } = renderHook(() => useEnergyLandscape(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({});
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockedAnalyze.mock.calls[0][0]).toEqual({});
  });

  it('handles API errors', async () => {
    const error = {
      status: 500,
      message: 'Internal server error during landscape analysis',
    };
    mockedAnalyze.mockRejectedValueOnce(error);

    const { result } = renderHook(() => useEnergyLandscape(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate(mockEmptyRequest);
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeTruthy();
  });

  it('handles pending state during request', async () => {
    let resolvePromise!: (value: typeof mockEnergyLandscapeResponse) => void;
    mockedAnalyze.mockReturnValueOnce(
      new Promise((resolve) => {
        resolvePromise = resolve;
      })
    );

    const { result } = renderHook(() => useEnergyLandscape(), {
      wrapper: createWrapper(),
    });

    act(() => {
      result.current.mutate(mockEmptyRequest);
    });

    // Should be pending while promise is unresolved
    await waitFor(() => {
      expect(result.current.isPending).toBe(true);
    });

    await act(async () => {
      resolvePromise(mockEnergyLandscapeResponse);
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });
  });

  it('returns all fields of EnergyLandscapeResponse', async () => {
    mockedAnalyze.mockResolvedValueOnce(mockEnergyLandscapeResponse);

    const { result } = renderHook(() => useEnergyLandscape(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate(mockEmptyRequest);
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    const data = result.current.data;
    expect(data?.currentEnergy).toBe(-0.742);
    expect(data?.isLocalMinimum).toBe(true);
    expect(data?.estimatedBasinSize).toBe(15);
    expect(data?.meanBarrierHeight).toBe(0.234);
    expect(data?.meanGradient).toBe(0.012);
    expect(data?.landscapeRuggedness).toBe(0.456);
    expect(data?.numLocalMinima).toBe(7);
    expect(data?.interpretation).toBe(
      'Schedule is in a stable local minimum with moderate landscape ruggedness.'
    );
    expect(data?.recommendations).toHaveLength(2);
    expect(data?.computedAt).toBe('2026-02-05T14:30:00Z');
    expect(data?.source).toBe('hopfield_energy_landscape');
  });
});
