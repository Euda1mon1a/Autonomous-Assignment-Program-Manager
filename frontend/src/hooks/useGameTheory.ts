/**
 * Game Theory Hooks
 *
 * React Query hooks for Axelrod-style Prisoner's Dilemma simulations.
 * Used to empirically test scheduling and resilience configurations.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { get, post, patch, ApiError } from '@/lib/api';
import type {
  ConfigStrategy,
  StrategyCreate,
  StrategyListResponse,
  Tournament,
  TournamentCreate,
  TournamentResults,
  TournamentListResponse,
  Evolution,
  EvolutionCreate,
  EvolutionResults,
  EvolutionListResponse,
  ValidationRequest,
  ValidationResult,
  ConfigAnalysisRequest,
  ConfigAnalysisResult,
  GameTheorySummary,
} from '@/types/game-theory';

const BASE_URL = '/v1/game-theory';

// ============================================================================
// Strategy Hooks
// ============================================================================

/**
 * Fetches all configuration strategies.
 */
export function useStrategies(activeOnly: boolean = true) {
  return useQuery<StrategyListResponse, ApiError>({
    queryKey: ['game-theory', 'strategies', { activeOnly }],
    queryFn: () => get<StrategyListResponse>(`${BASE_URL}/strategies?active_only=${activeOnly}`),
  });
}

/**
 * Fetches a single strategy by ID.
 */
export function useStrategy(strategyId: string | undefined) {
  return useQuery<ConfigStrategy, ApiError>({
    queryKey: ['game-theory', 'strategies', strategyId],
    queryFn: () => get<ConfigStrategy>(`${BASE_URL}/strategies/${strategyId}`),
    enabled: !!strategyId,
  });
}

/**
 * Creates a new configuration strategy.
 */
export function useCreateStrategy() {
  const queryClient = useQueryClient();

  return useMutation<ConfigStrategy, ApiError, StrategyCreate>({
    mutationFn: (data) => post<ConfigStrategy>(`${BASE_URL}/strategies`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['game-theory', 'strategies'] });
      queryClient.invalidateQueries({ queryKey: ['game-theory', 'summary'] });
    },
  });
}

/**
 * Updates a strategy.
 */
export function useUpdateStrategy(strategyId: string) {
  const queryClient = useQueryClient();

  return useMutation<ConfigStrategy, ApiError, Partial<ConfigStrategy>>({
    mutationFn: (data) => patch<ConfigStrategy>(`${BASE_URL}/strategies/${strategyId}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['game-theory', 'strategies'] });
      queryClient.invalidateQueries({ queryKey: ['game-theory', 'strategies', strategyId] });
    },
  });
}

/**
 * Creates default strategies (Admin only).
 */
export function useCreateDefaultStrategies() {
  const queryClient = useQueryClient();

  return useMutation<{ created: number; strategies: string[] }, ApiError, void>({
    mutationFn: () => post<{ created: number; strategies: string[] }>(`${BASE_URL}/strategies/defaults`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['game-theory', 'strategies'] });
      queryClient.invalidateQueries({ queryKey: ['game-theory', 'summary'] });
    },
  });
}

// ============================================================================
// Tournament Hooks
// ============================================================================

/**
 * Fetches all tournaments.
 */
export function useTournaments(limit: number = 50) {
  return useQuery<TournamentListResponse, ApiError>({
    queryKey: ['game-theory', 'tournaments', { limit }],
    queryFn: () => get<TournamentListResponse>(`${BASE_URL}/tournaments?limit=${limit}`),
  });
}

/**
 * Fetches a single tournament by ID.
 */
export function useTournament(tournamentId: string | undefined) {
  return useQuery<Tournament, ApiError>({
    queryKey: ['game-theory', 'tournaments', tournamentId],
    queryFn: () => get<Tournament>(`${BASE_URL}/tournaments/${tournamentId}`),
    enabled: !!tournamentId,
    refetchInterval: (query) => {
      // Refetch while running
      const data = query.state.data;
      if (data?.status === 'running' || data?.status === 'pending') {
        return 2000; // Poll every 2 seconds
      }
      return false;
    },
  });
}

/**
 * Fetches tournament results.
 */
export function useTournamentResults(tournamentId: string | undefined) {
  return useQuery<TournamentResults, ApiError>({
    queryKey: ['game-theory', 'tournaments', tournamentId, 'results'],
    queryFn: () => get<TournamentResults>(`${BASE_URL}/tournaments/${tournamentId}/results`),
    enabled: !!tournamentId,
  });
}

/**
 * Creates and starts a new tournament.
 */
export function useCreateTournament() {
  const queryClient = useQueryClient();

  return useMutation<Tournament, ApiError, TournamentCreate>({
    mutationFn: (data) => post<Tournament>(`${BASE_URL}/tournaments`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['game-theory', 'tournaments'] });
      queryClient.invalidateQueries({ queryKey: ['game-theory', 'summary'] });
    },
  });
}

/**
 * Runs a tournament synchronously (for testing).
 */
export function useRunTournamentSync(tournamentId: string) {
  const queryClient = useQueryClient();

  return useMutation<{ tournament_id: string; status: string; winner: string }, ApiError, void>({
    mutationFn: () => post<{ tournament_id: string; status: string; winner: string }>(`${BASE_URL}/tournaments/${tournamentId}/run`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['game-theory', 'tournaments'] });
      queryClient.invalidateQueries({ queryKey: ['game-theory', 'tournaments', tournamentId] });
    },
  });
}

// ============================================================================
// Evolution Hooks
// ============================================================================

/**
 * Fetches all evolution simulations.
 */
export function useEvolutions(limit: number = 50) {
  return useQuery<EvolutionListResponse, ApiError>({
    queryKey: ['game-theory', 'evolutions', { limit }],
    queryFn: () => get<EvolutionListResponse>(`${BASE_URL}/evolution?limit=${limit}`),
  });
}

/**
 * Fetches a single evolution by ID.
 */
export function useEvolution(evolutionId: string | undefined) {
  return useQuery<Evolution, ApiError>({
    queryKey: ['game-theory', 'evolutions', evolutionId],
    queryFn: () => get<Evolution>(`${BASE_URL}/evolution/${evolutionId}`),
    enabled: !!evolutionId,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data?.status === 'running' || data?.status === 'pending') {
        return 3000; // Poll every 3 seconds
      }
      return false;
    },
  });
}

/**
 * Fetches evolution results.
 */
export function useEvolutionResults(evolutionId: string | undefined) {
  return useQuery<EvolutionResults, ApiError>({
    queryKey: ['game-theory', 'evolutions', evolutionId, 'results'],
    queryFn: () => get<EvolutionResults>(`${BASE_URL}/evolution/${evolutionId}/results`),
    enabled: !!evolutionId,
  });
}

/**
 * Creates and starts a new evolution simulation.
 */
export function useCreateEvolution() {
  const queryClient = useQueryClient();

  return useMutation<Evolution, ApiError, EvolutionCreate>({
    mutationFn: (data) => post<Evolution>(`${BASE_URL}/evolution`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['game-theory', 'evolutions'] });
      queryClient.invalidateQueries({ queryKey: ['game-theory', 'summary'] });
    },
  });
}

// ============================================================================
// Validation Hooks
// ============================================================================

/**
 * Validates a strategy against Tit for Tat.
 */
export function useValidateStrategy() {
  const queryClient = useQueryClient();

  return useMutation<ValidationResult, ApiError, ValidationRequest>({
    mutationFn: (data) => post<ValidationResult>(`${BASE_URL}/validate`, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['game-theory', 'strategies', data.strategy_id] });
    },
  });
}

// ============================================================================
// Analysis Hooks
// ============================================================================

/**
 * Analyzes a configuration using game theory.
 */
export function useAnalyzeConfig() {
  return useMutation<ConfigAnalysisResult, ApiError, ConfigAnalysisRequest>({
    mutationFn: (data) => post<ConfigAnalysisResult>(`${BASE_URL}/analyze`, data),
  });
}

// ============================================================================
// Summary Hook
// ============================================================================

/**
 * Fetches game theory summary for dashboard.
 */
export function useGameTheorySummary() {
  return useQuery<GameTheorySummary, ApiError>({
    queryKey: ['game-theory', 'summary'],
    queryFn: () => get<GameTheorySummary>(`${BASE_URL}/summary`),
    staleTime: 30000, // 30 seconds
  });
}
