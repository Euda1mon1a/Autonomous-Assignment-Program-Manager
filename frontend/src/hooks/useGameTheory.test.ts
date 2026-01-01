/**
 * Tests for Game Theory Hooks
 *
 * Tests Prisoner's Dilemma simulations, tournament management,
 * and strategy validation for configuration testing.
 */
import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import {
  useStrategies,
  useStrategy,
  useCreateStrategy,
  useTournaments,
  useTournament,
  useCreateTournament,
  useEvolutions,
  useValidateStrategy,
  useAnalyzeConfig,
  useGameTheorySummary,
} from './useGameTheory';
import * as api from '@/lib/api';

// Mock the API module
jest.mock('@/lib/api');

const mockedApi = api as jest.Mocked<typeof api>;

// Test data
const mockStrategy = {
  id: 'strategy-123',
  name: 'Tit for Tat',
  description: 'Cooperate first, then mimic opponent',
  config: { type: 'tit_for_tat' },
  is_active: true,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

const mockTournament = {
  id: 'tournament-123',
  name: 'Configuration Test',
  description: 'Testing scheduler configs',
  strategies: ['strategy-1', 'strategy-2'],
  rounds: 100,
  status: 'completed' as const,
  winner: 'strategy-1',
  started_at: '2024-01-01T00:00:00Z',
  completed_at: '2024-01-01T00:05:00Z',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:05:00Z',
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

describe('useStrategies', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('fetches strategies list successfully', async () => {
    const mockResponse = {
      strategies: [mockStrategy],
      total: 1,
    };
    mockedApi.get.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(() => useStrategies(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(mockResponse);
    expect(mockedApi.get).toHaveBeenCalledWith(
      '/v1/game-theory/strategies?active_only=true'
    );
  });

  it('fetches all strategies including inactive', async () => {
    const mockResponse = {
      strategies: [mockStrategy],
      total: 1,
    };
    mockedApi.get.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(() => useStrategies(false), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(mockedApi.get).toHaveBeenCalledWith(
      '/v1/game-theory/strategies?active_only=false'
    );
  });
});

describe('useStrategy', () => {
  it('fetches single strategy successfully', async () => {
    mockedApi.get.mockResolvedValueOnce(mockStrategy);

    const { result } = renderHook(() => useStrategy('strategy-123'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(mockStrategy);
    expect(mockedApi.get).toHaveBeenCalledWith(
      '/v1/game-theory/strategies/strategy-123'
    );
  });

  it('does not fetch when id is undefined', async () => {
    const { result } = renderHook(() => useStrategy(undefined), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(mockedApi.get).not.toHaveBeenCalled();
  });
});

describe('useCreateStrategy', () => {
  it('creates strategy successfully', async () => {
    mockedApi.post.mockResolvedValueOnce(mockStrategy);

    const { result } = renderHook(() => useCreateStrategy(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        name: 'New Strategy',
        description: 'Test strategy',
        config: { type: 'custom' },
      });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockStrategy);
  });
});

describe('useTournaments', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('fetches tournaments list successfully', async () => {
    const mockResponse = {
      tournaments: [mockTournament],
      total: 1,
    };
    mockedApi.get.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(() => useTournaments(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(mockResponse);
    expect(mockedApi.get).toHaveBeenCalledWith(
      '/v1/game-theory/tournaments?limit=50'
    );
  });

  it('applies custom limit', async () => {
    const mockResponse = {
      tournaments: [mockTournament],
      total: 1,
    };
    mockedApi.get.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(() => useTournaments(100), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(mockedApi.get).toHaveBeenCalledWith(
      '/v1/game-theory/tournaments?limit=100'
    );
  });
});

describe('useTournament', () => {
  it('fetches single tournament successfully', async () => {
    mockedApi.get.mockResolvedValueOnce(mockTournament);

    const { result } = renderHook(() => useTournament('tournament-123'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(mockTournament);
  });

  it('polls while tournament is running', async () => {
    const runningTournament = {
      ...mockTournament,
      status: 'running' as const,
    };
    mockedApi.get.mockResolvedValue(runningTournament);

    renderHook(() => useTournament('tournament-123'), {
      wrapper: createWrapper(),
    });

    // Should refetch automatically (tested via refetchInterval)
    await waitFor(() => {
      expect(mockedApi.get).toHaveBeenCalled();
    });
  });
});

describe('useCreateTournament', () => {
  it('creates tournament successfully', async () => {
    mockedApi.post.mockResolvedValueOnce(mockTournament);

    const { result } = renderHook(() => useCreateTournament(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        name: 'Test Tournament',
        description: 'Testing configs',
        strategy_ids: ['strategy-1', 'strategy-2'],
        rounds: 100,
      });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockTournament);
  });
});

describe('useEvolutions', () => {
  it('fetches evolutions list successfully', async () => {
    const mockEvolution = {
      id: 'evolution-123',
      name: 'Evolution Test',
      generations: 50,
      population_size: 100,
      status: 'completed' as const,
      winner: 'strategy-1',
      created_at: '2024-01-01T00:00:00Z',
    };

    const mockResponse = {
      evolutions: [mockEvolution],
      total: 1,
    };
    mockedApi.get.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(() => useEvolutions(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(mockResponse);
  });
});

describe('useValidateStrategy', () => {
  it('validates strategy against tit for tat', async () => {
    const mockValidationResult = {
      strategy_id: 'strategy-123',
      is_valid: true,
      score: 85,
      cooperations: 90,
      defections: 10,
      message: 'Strategy performed well',
    };
    mockedApi.post.mockResolvedValueOnce(mockValidationResult);

    const { result } = renderHook(() => useValidateStrategy(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        strategy_id: 'strategy-123',
        rounds: 100,
      });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockValidationResult);
  });
});

describe('useAnalyzeConfig', () => {
  it('analyzes configuration using game theory', async () => {
    const mockAnalysisResult = {
      config_id: 'config-123',
      stability_score: 0.92,
      nash_equilibrium: true,
      pareto_optimal: true,
      recommendations: ['Increase timeout', 'Adjust priority weights'],
    };
    mockedApi.post.mockResolvedValueOnce(mockAnalysisResult);

    const { result } = renderHook(() => useAnalyzeConfig(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        config: { constraints: [], preferences: [] },
        rounds: 1000,
      });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockAnalysisResult);
  });
});

describe('useGameTheorySummary', () => {
  it('fetches game theory summary successfully', async () => {
    const mockSummary = {
      total_strategies: 10,
      total_tournaments: 25,
      total_evolutions: 5,
      active_simulations: 2,
      recent_winners: ['Tit for Tat', 'Generous Tit for Tat'],
    };
    mockedApi.get.mockResolvedValueOnce(mockSummary);

    const { result } = renderHook(() => useGameTheorySummary(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(mockSummary);
    expect(mockedApi.get).toHaveBeenCalledWith('/v1/game-theory/summary');
  });
});
