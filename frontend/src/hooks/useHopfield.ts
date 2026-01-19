/**
 * Hopfield Network Hooks
 *
 * TanStack Query hooks for Hopfield network analysis endpoints.
 * Used to analyze schedule stability using attractor dynamics.
 *
 * Endpoints:
 * - POST /resilience/exotic/hopfield/energy
 * - POST /resilience/exotic/hopfield/attractors
 * - POST /resilience/exotic/hopfield/basin-depth
 * - POST /resilience/exotic/hopfield/spurious
 */
import { useMutation } from '@tanstack/react-query';
import { ApiError } from '@/lib/api';
import {
  analyzeHopfieldEnergy,
  findNearbyAttractors,
  measureBasinDepth,
  detectSpuriousAttractors,
  type HopfieldEnergyRequest,
  type HopfieldEnergyResponse,
  type NearbyAttractorsRequest,
  type NearbyAttractorsResponse,
  type BasinDepthRequest,
  type BasinDepthResponse,
  type SpuriousAttractorsRequest,
  type SpuriousAttractorsResponse,
} from '@/api/exotic-resilience';

// ============================================================================
// Hopfield Energy Hook
// ============================================================================

/**
 * Analyzes schedule energy using Hopfield network model.
 *
 * Calculates the energy of the current schedule configuration,
 * where lower energy indicates a more stable and optimal state.
 *
 * @returns Mutation hook for Hopfield energy analysis
 *
 * @example
 * ```ts
 * const energyMutation = useHopfieldEnergy();
 *
 * const handleAnalyze = async () => {
 *   const result = await energyMutation.mutateAsync({
 *     startDate: '2026-01-01',
 *     endDate: '2026-01-31',
 *   });
 *   console.log('Stability:', result.stabilityLevel);
 *   console.log('Energy:', result.metrics.totalEnergy);
 * };
 * ```
 */
export function useHopfieldEnergy() {
  return useMutation<HopfieldEnergyResponse, ApiError, HopfieldEnergyRequest>({
    mutationFn: analyzeHopfieldEnergy,
  });
}

// ============================================================================
// Nearby Attractors Hook
// ============================================================================

/**
 * Finds stable attractors near the current schedule state.
 *
 * Explores the energy landscape to identify nearby local minima
 * that the schedule could transition to with minimal changes.
 *
 * @returns Mutation hook for nearby attractors search
 *
 * @example
 * ```ts
 * const attractorsMutation = useNearbyAttractors();
 *
 * const handleSearch = async () => {
 *   const result = await attractorsMutation.mutateAsync({
 *     startDate: '2026-01-01',
 *     endDate: '2026-01-31',
 *     maxDistance: 10,
 *   });
 *   console.log('Found:', result.attractorsFound, 'attractors');
 * };
 * ```
 */
export function useNearbyAttractors() {
  return useMutation<NearbyAttractorsResponse, ApiError, NearbyAttractorsRequest>({
    mutationFn: findNearbyAttractors,
  });
}

// ============================================================================
// Basin Depth Hook
// ============================================================================

/**
 * Measures the depth of the current basin of attraction.
 *
 * Determines how robust the schedule is against perturbations
 * by analyzing the energy barriers surrounding the current state.
 *
 * @returns Mutation hook for basin depth analysis
 *
 * @example
 * ```ts
 * const basinMutation = useBasinDepth();
 *
 * const handleMeasure = async () => {
 *   const result = await basinMutation.mutateAsync({
 *     startDate: '2026-01-01',
 *     endDate: '2026-01-31',
 *     numPerturbations: 100,
 *   });
 *   console.log('Robust:', result.isRobust);
 *   console.log('Threshold:', result.robustnessThreshold, 'changes');
 * };
 * ```
 */
export function useBasinDepth() {
  return useMutation<BasinDepthResponse, ApiError, BasinDepthRequest>({
    mutationFn: measureBasinDepth,
  });
}

// ============================================================================
// Spurious Attractors Hook
// ============================================================================

/**
 * Detects spurious attractors (scheduling anti-patterns).
 *
 * Identifies local minima that represent suboptimal configurations
 * which could trap optimization or cause scheduling issues.
 *
 * @returns Mutation hook for spurious attractor detection
 *
 * @example
 * ```ts
 * const spuriousMutation = useSpuriousAttractors();
 *
 * const handleDetect = async () => {
 *   const result = await spuriousMutation.mutateAsync({
 *     startDate: '2026-01-01',
 *     endDate: '2026-01-31',
 *     searchRadius: 20,
 *   });
 *   console.log('Anti-patterns found:', result.spuriousAttractorsFound);
 * };
 * ```
 */
export function useSpuriousAttractors() {
  return useMutation<SpuriousAttractorsResponse, ApiError, SpuriousAttractorsRequest>({
    mutationFn: detectSpuriousAttractors,
  });
}

// Re-export types for convenience
export type {
  HopfieldEnergyRequest,
  HopfieldEnergyResponse,
  NearbyAttractorsRequest,
  NearbyAttractorsResponse,
  BasinDepthRequest,
  BasinDepthResponse,
  SpuriousAttractorsRequest,
  SpuriousAttractorsResponse,
  StabilityLevel,
  AttractorType,
  AttractorInfoResponse,
  BasinMetricsResponse,
  SpuriousAttractorInfoResponse,
  EnergyMetricsResponse,
} from '@/api/exotic-resilience';
