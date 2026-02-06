/**
 * Tests for Hopfield Network Hooks
 *
 * Tests all four Hopfield mutation hooks:
 * - useHopfieldEnergy (POST /resilience/exotic/hopfield/energy)
 * - useNearbyAttractors (POST /resilience/exotic/hopfield/attractors)
 * - useBasinDepth (POST /resilience/exotic/hopfield/basin-depth)
 * - useSpuriousAttractors (POST /resilience/exotic/hopfield/spurious)
 */
import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import {
  useHopfieldEnergy,
  useNearbyAttractors,
  useBasinDepth,
  useSpuriousAttractors,
} from '@/hooks/useHopfield';
import * as api from '@/lib/api';

// Mock the API module
jest.mock('@/lib/api');

const mockedApi = api as jest.Mocked<typeof api>;

// =============================================================================
// Mock Data (camelCase - axios interceptor converts from snake_case)
// =============================================================================

const mockEnergyRequest = {
  startDate: '2026-01-01',
  endDate: '2026-01-31',
};

const mockEnergyResponse = {
  analyzedAt: '2026-02-05T10:00:00Z',
  scheduleId: null,
  periodStart: '2026-01-01',
  periodEnd: '2026-01-31',
  assignmentsAnalyzed: 248,
  metrics: {
    totalEnergy: -0.856,
    normalizedEnergy: -0.712,
    energyDensity: 0.034,
    interactionEnergy: -0.144,
    stabilityScore: 0.88,
    gradientMagnitude: 0.015,
    isLocalMinimum: true,
    distanceToMinimum: 0.02,
  },
  stabilityLevel: 'stable', // @enum-ok
  interpretation: 'Schedule is in a stable configuration with low energy.',
  recommendations: ['Monitor energy drift over next block', 'Basin depth is adequate'],
  source: 'hopfield_network',
};

const mockAttractorsRequest = {
  startDate: '2026-01-01',
  endDate: '2026-01-31',
  maxDistance: 10,
};

const mockAttractorsResponse = {
  analyzedAt: '2026-02-05T10:05:00Z',
  currentStateEnergy: -0.856,
  attractorsFound: 3,
  attractors: [
    {
      attractorId: 'attr-001',
      attractorType: 'global_minimum', // @enum-ok
      energyLevel: -0.92,
      basinDepth: 0.35,
      basinVolume: 12,
      hammingDistance: 4,
      patternDescription: 'Optimal coverage with balanced workload',
      confidence: 0.95,
    },
    {
      attractorId: 'attr-002',
      attractorType: 'local_minimum', // @enum-ok
      energyLevel: -0.81,
      basinDepth: 0.15,
      basinVolume: 6,
      hammingDistance: 7,
      patternDescription: 'Near-optimal with minor coverage gaps',
      confidence: 0.82,
    },
    {
      attractorId: 'attr-003',
      attractorType: 'metastable', // @enum-ok
      energyLevel: -0.65,
      basinDepth: 0.08,
      basinVolume: 3,
      hammingDistance: 9,
      patternDescription: 'Unstable configuration with weekend clustering',
      confidence: 0.71,
    },
  ],
  globalMinimumIdentified: true,
  currentBasinId: 'basin-alpha',
  interpretation: 'Three attractors found within search radius.',
  recommendations: ['Consider transitioning to global minimum attr-001'],
  source: 'hopfield_attractors',
};

const mockBasinRequest = {
  startDate: '2026-01-01',
  endDate: '2026-01-31',
  numPerturbations: 100,
};

const mockBasinResponse = {
  analyzedAt: '2026-02-05T10:10:00Z',
  scheduleId: null,
  attractorId: 'attr-001',
  metrics: {
    minEscapeEnergy: 0.12,
    avgEscapeEnergy: 0.28,
    maxEscapeEnergy: 0.55,
    basinStabilityIndex: 0.87,
    numEscapePaths: 5,
    nearestSaddleDistance: 3,
    basinRadius: 8,
    criticalPerturbationSize: 4,
  },
  stabilityLevel: 'stable', // @enum-ok
  isRobust: true,
  robustnessThreshold: 3,
  interpretation: 'Current basin is deep with high stability index.',
  recommendations: ['Basin depth sufficient for operational use'],
  source: 'hopfield_basin_depth',
};

const mockSpuriousRequest = {
  startDate: '2026-01-01',
  endDate: '2026-01-31',
  searchRadius: 20,
};

const mockSpuriousResponse = {
  analyzedAt: '2026-02-05T10:15:00Z',
  spuriousAttractorsFound: 2,
  spuriousAttractors: [
    {
      attractorId: 'spurious-001',
      energyLevel: -0.42,
      basinSize: 4,
      antiPatternType: 'weekend_clustering', // @enum-ok
      description: 'All weekend shifts assigned to same residents',
      riskLevel: 'high', // @enum-ok
      distanceFromValid: 6,
      probabilityOfCapture: 0.15,
      mitigationStrategy: 'Distribute weekend assignments across PGY levels',
    },
    {
      attractorId: 'spurious-002',
      energyLevel: -0.38,
      basinSize: 2,
      antiPatternType: 'supervision_gap', // @enum-ok
      description: 'Night shifts without adequate faculty coverage',
      riskLevel: 'medium', // @enum-ok
      distanceFromValid: 8,
      probabilityOfCapture: 0.08,
      mitigationStrategy: 'Add supervision constraint for overnight rotations',
    },
  ],
  totalBasinCoverage: 0.72,
  highestRiskAttractor: 'spurious-001',
  isCurrentStateSpurious: false,
  interpretation: 'Two spurious attractors detected in search radius.',
  recommendations: ['Address weekend clustering anti-pattern first'],
  source: 'hopfield_spurious',
};

// =============================================================================
// Wrapper
// =============================================================================

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

// =============================================================================
// Tests
// =============================================================================

describe('useHopfieldEnergy', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('handles successful energy analysis with correct endpoint', async () => {
    mockedApi.post.mockResolvedValueOnce(mockEnergyResponse);

    const { result } = renderHook(() => useHopfieldEnergy(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate(mockEnergyRequest);
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockEnergyResponse);
    expect(mockedApi.post).toHaveBeenCalledWith(
      '/resilience/exotic/hopfield/energy',
      mockEnergyRequest
    );
  });

  it('handles API errors', async () => {
    const error = {
      status: 500,
      message: 'Internal server error during energy analysis',
    };
    mockedApi.post.mockRejectedValueOnce(error);

    const { result } = renderHook(() => useHopfieldEnergy(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate(mockEnergyRequest);
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeTruthy();
  });

  it('returns nested metrics object with all fields', async () => {
    mockedApi.post.mockResolvedValueOnce(mockEnergyResponse);

    const { result } = renderHook(() => useHopfieldEnergy(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate(mockEnergyRequest);
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    const data = result.current.data;
    expect(data?.metrics.totalEnergy).toBe(-0.856);
    expect(data?.metrics.normalizedEnergy).toBe(-0.712);
    expect(data?.metrics.stabilityScore).toBe(0.88);
    expect(data?.metrics.isLocalMinimum).toBe(true);
    expect(data?.metrics.distanceToMinimum).toBe(0.02);
    expect(data?.assignmentsAnalyzed).toBe(248);
    expect(data?.stabilityLevel).toBe('stable');
    expect(data?.recommendations).toHaveLength(2);
  });
});

describe('useNearbyAttractors', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('handles successful attractors search with correct endpoint', async () => {
    mockedApi.post.mockResolvedValueOnce(mockAttractorsResponse);

    const { result } = renderHook(() => useNearbyAttractors(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate(mockAttractorsRequest);
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockAttractorsResponse);
    expect(mockedApi.post).toHaveBeenCalledWith(
      '/resilience/exotic/hopfield/attractors',
      mockAttractorsRequest
    );
  });

  it('handles API errors', async () => {
    const error = {
      status: 500,
      message: 'Internal server error during attractor search',
    };
    mockedApi.post.mockRejectedValueOnce(error);

    const { result } = renderHook(() => useNearbyAttractors(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate(mockAttractorsRequest);
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeTruthy();
  });

  it('returns attractors array with correct structure', async () => {
    mockedApi.post.mockResolvedValueOnce(mockAttractorsResponse);

    const { result } = renderHook(() => useNearbyAttractors(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate(mockAttractorsRequest);
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    const data = result.current.data;
    expect(data?.attractorsFound).toBe(3);
    expect(data?.attractors).toHaveLength(3);
    expect(data?.attractors[0].attractorId).toBe('attr-001');
    expect(data?.attractors[0].attractorType).toBe('global_minimum');
    expect(data?.attractors[0].confidence).toBe(0.95);
    expect(data?.globalMinimumIdentified).toBe(true);
    expect(data?.currentBasinId).toBe('basin-alpha');
  });
});

describe('useBasinDepth', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('handles successful basin measurement with correct endpoint', async () => {
    mockedApi.post.mockResolvedValueOnce(mockBasinResponse);

    const { result } = renderHook(() => useBasinDepth(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate(mockBasinRequest);
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockBasinResponse);
    expect(mockedApi.post).toHaveBeenCalledWith(
      '/resilience/exotic/hopfield/basin-depth',
      mockBasinRequest
    );
  });

  it('handles API errors', async () => {
    const error = {
      status: 500,
      message: 'Internal server error during basin depth measurement',
    };
    mockedApi.post.mockRejectedValueOnce(error);

    const { result } = renderHook(() => useBasinDepth(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate(mockBasinRequest);
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeTruthy();
  });

  it('returns nested metrics and robustness fields', async () => {
    mockedApi.post.mockResolvedValueOnce(mockBasinResponse);

    const { result } = renderHook(() => useBasinDepth(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate(mockBasinRequest);
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    const data = result.current.data;
    expect(data?.metrics.minEscapeEnergy).toBe(0.12);
    expect(data?.metrics.avgEscapeEnergy).toBe(0.28);
    expect(data?.metrics.basinStabilityIndex).toBe(0.87);
    expect(data?.metrics.criticalPerturbationSize).toBe(4);
    expect(data?.isRobust).toBe(true);
    expect(data?.robustnessThreshold).toBe(3);
    expect(data?.stabilityLevel).toBe('stable');
    expect(data?.attractorId).toBe('attr-001');
  });
});

describe('useSpuriousAttractors', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('handles successful spurious detection with correct endpoint', async () => {
    mockedApi.post.mockResolvedValueOnce(mockSpuriousResponse);

    const { result } = renderHook(() => useSpuriousAttractors(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate(mockSpuriousRequest);
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockSpuriousResponse);
    expect(mockedApi.post).toHaveBeenCalledWith(
      '/resilience/exotic/hopfield/spurious',
      mockSpuriousRequest
    );
  });

  it('handles API errors', async () => {
    const error = {
      status: 500,
      message: 'Internal server error during spurious attractor detection',
    };
    mockedApi.post.mockRejectedValueOnce(error);

    const { result } = renderHook(() => useSpuriousAttractors(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate(mockSpuriousRequest);
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeTruthy();
  });

  it('returns spuriousAttractors array with risk assessment', async () => {
    mockedApi.post.mockResolvedValueOnce(mockSpuriousResponse);

    const { result } = renderHook(() => useSpuriousAttractors(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate(mockSpuriousRequest);
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    const data = result.current.data;
    expect(data?.spuriousAttractorsFound).toBe(2);
    expect(data?.spuriousAttractors).toHaveLength(2);
    expect(data?.spuriousAttractors[0].attractorId).toBe('spurious-001');
    expect(data?.spuriousAttractors[0].riskLevel).toBe('high');
    expect(data?.spuriousAttractors[0].probabilityOfCapture).toBe(0.15);
    expect(data?.spuriousAttractors[1].antiPatternType).toBe('supervision_gap');
    expect(data?.highestRiskAttractor).toBe('spurious-001');
    expect(data?.isCurrentStateSpurious).toBe(false);
    expect(data?.totalBasinCoverage).toBe(0.72);
  });
});
