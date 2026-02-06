/**
 * Tests for Free Energy Optimization Hook
 *
 * Tests Helmholtz free energy optimization mutation hook
 * that analyzes schedule stability using thermodynamic principles.
 */
import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import { useFreeEnergy } from '../useFreeEnergy';
import type {
  FreeEnergyRequest,
  FreeEnergyOptimizationResponse,
} from '@/api/exotic-resilience';

// Mock the optimizeFreeEnergy function
const mockOptimizeFreeEnergy = jest.fn();

jest.mock('@/api/exotic-resilience', () => ({
  optimizeFreeEnergy: (...args: unknown[]) => mockOptimizeFreeEnergy(...args),
}));

// Test data
const mockFreeEnergyResponse: FreeEnergyOptimizationResponse = {
  freeEnergy: -12.45,
  internalEnergy: 8.3,
  entropyTerm: 20.75,
  temperature: 1.0,
  constraintViolations: 2,
  configurationEntropy: 3.14,
  interpretation: 'Schedule is thermodynamically stable with low free energy.',
  recommendations: [
    'Consider reducing constraint violations to lower internal energy.',
    'Current entropy level indicates good schedule flexibility.',
  ],
  computedAt: '2026-02-05T12:00:00Z',
  source: 'cp-sat-solver',
};

const mockFullRequest: FreeEnergyRequest = {
  scheduleId: 'schedule-abc-123',
  targetTemperature: 0.5,
  maxIterations: 500,
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

describe('useFreeEnergy', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('handles successful free energy optimization', async () => {
    mockOptimizeFreeEnergy.mockResolvedValueOnce(mockFreeEnergyResponse);

    const { result } = renderHook(() => useFreeEnergy(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({});
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockFreeEnergyResponse);
    expect(mockOptimizeFreeEnergy).toHaveBeenCalledTimes(1);
    expect(mockOptimizeFreeEnergy.mock.calls[0][0]).toEqual({});
  });

  it('passes all optional parameters correctly', async () => {
    mockOptimizeFreeEnergy.mockResolvedValueOnce(mockFreeEnergyResponse);

    const { result } = renderHook(() => useFreeEnergy(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate(mockFullRequest);
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockOptimizeFreeEnergy).toHaveBeenCalledTimes(1);
    expect(mockOptimizeFreeEnergy.mock.calls[0][0]).toEqual(mockFullRequest);
    expect(result.current.data).toEqual(mockFreeEnergyResponse);
  });

  it('works with minimal (empty) request', async () => {
    mockOptimizeFreeEnergy.mockResolvedValueOnce(mockFreeEnergyResponse);

    const { result } = renderHook(() => useFreeEnergy(), {
      wrapper: createWrapper(),
    });

    const emptyRequest = {};

    await act(async () => {
      result.current.mutate(emptyRequest);
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockOptimizeFreeEnergy).toHaveBeenCalledTimes(1);
    expect(mockOptimizeFreeEnergy.mock.calls[0][0]).toEqual(emptyRequest);
  });

  it('passes custom targetTemperature correctly', async () => {
    const customTempResponse = {
      ...mockFreeEnergyResponse,
      temperature: 2.5,
      freeEnergy: -8.1,
      entropyTerm: 16.4,
    };

    mockOptimizeFreeEnergy.mockResolvedValueOnce(customTempResponse);

    const { result } = renderHook(() => useFreeEnergy(), {
      wrapper: createWrapper(),
    });

    const tempRequest = { targetTemperature: 2.5 };

    await act(async () => {
      result.current.mutate(tempRequest);
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockOptimizeFreeEnergy.mock.calls[0][0]).toEqual(tempRequest);
    expect(result.current.data?.temperature).toBe(2.5);
  });

  it('handles API errors', async () => {
    const error = {
      status: 500,
      message: 'Internal server error during free energy optimization',
    };
    mockOptimizeFreeEnergy.mockRejectedValueOnce(error);

    const { result } = renderHook(() => useFreeEnergy(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({});
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeTruthy();
  });

  it('handles pending state during request', async () => {
    let resolvePromise: (value: FreeEnergyOptimizationResponse) => void;
    mockOptimizeFreeEnergy.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolvePromise = resolve;
        })
    );

    const { result } = renderHook(() => useFreeEnergy(), {
      wrapper: createWrapper(),
    });

    act(() => {
      result.current.mutate({});
    });

    // Should be pending while promise is unresolved
    await waitFor(() => {
      expect(result.current.isPending).toBe(true);
    });

    // Resolve the promise
    await act(async () => {
      resolvePromise!(mockFreeEnergyResponse);
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });
  });

  it('returns correct key response fields', async () => {
    mockOptimizeFreeEnergy.mockResolvedValueOnce(mockFreeEnergyResponse);

    const { result } = renderHook(() => useFreeEnergy(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate(mockFullRequest);
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    const data = result.current.data;
    expect(data?.freeEnergy).toBe(-12.45);
    expect(data?.internalEnergy).toBe(8.3);
    expect(data?.entropyTerm).toBe(20.75);
    expect(data?.temperature).toBe(1.0);
    expect(data?.constraintViolations).toBe(2);
    expect(data?.configurationEntropy).toBe(3.14);
    expect(data?.interpretation).toBeDefined();
    expect(data?.recommendations).toHaveLength(2);
    expect(data?.computedAt).toBe('2026-02-05T12:00:00Z');
    expect(data?.source).toBe('cp-sat-solver');
  });
});
