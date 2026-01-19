/**
 * Thermodynamics Hooks
 *
 * TanStack Query hooks for exotic thermodynamics analysis endpoints.
 * Used to evaluate schedule quality using free energy and energy landscape metrics.
 *
 * Endpoints:
 * - POST /resilience/exotic/thermodynamics/free-energy
 * - POST /resilience/exotic/thermodynamics/energy-landscape
 */
import { useMutation } from '@tanstack/react-query';
import { post, ApiError } from '@/lib/api';

const BASE_URL = '/resilience/exotic/thermodynamics';

// ============================================================================
// Type Definitions (using camelCase per project convention)
// ============================================================================

/**
 * Request parameters for free energy calculation.
 */
export interface FreeEnergyRequest {
  scheduleId?: string;
  temperature?: number;
  maxIterations?: number;
}

/**
 * Free energy analysis response from backend.
 * Represents the thermodynamic properties of a schedule configuration.
 */
export interface FreeEnergyResponse {
  freeEnergy: number;
  internalEnergy: number;
  entropyTerm: number;
  temperature: number;
  constraintViolations: number;
  configurationEntropy: number;
  interpretation: string;
  recommendations: string[];
  computedAt: string; // ISO date string
  source: string;
}

/**
 * Request parameters for energy landscape analysis.
 */
export interface EnergyLandscapeRequest {
  scheduleId?: string;
  sampleSize?: number;
}

/**
 * Energy landscape analysis response from backend.
 * Describes the topography of the optimization landscape around the schedule.
 */
export interface EnergyLandscapeResponse {
  currentEnergy: number;
  isLocalMinimum: boolean;
  estimatedBasinSize: number;
  meanBarrierHeight: number;
  meanGradient: number;
  landscapeRuggedness: number;
  numLocalMinima: number;
  interpretation: string;
  recommendations: string[];
  computedAt: string; // ISO date string
  source: string;
}

// ============================================================================
// Free Energy Hook
// ============================================================================

/**
 * Calculates free energy for a schedule configuration.
 *
 * Free energy combines internal energy (constraint violations) and entropy
 * to provide a comprehensive quality metric. Lower values indicate better
 * schedule quality and stability.
 *
 * @returns Mutation hook for free energy calculation
 *
 * @example
 * ```ts
 * const freeEnergyMutation = useFreeEnergy();
 *
 * const handleCalculate = async () => {
 *   const result = await freeEnergyMutation.mutateAsync({
 *     scheduleId: 'schedule-123',
 *     temperature: 300,
 *     maxIterations: 1000,
 *   });
 *   console.log('Free energy:', result.freeEnergy);
 *   console.log('Recommendations:', result.recommendations);
 * };
 * ```
 */
export function useFreeEnergy() {
  return useMutation<FreeEnergyResponse, ApiError, FreeEnergyRequest>({
    mutationFn: (data) =>
      post<FreeEnergyResponse>(`${BASE_URL}/free-energy`, data),
  });
}

// ============================================================================
// Energy Landscape Hook
// ============================================================================

/**
 * Analyzes the energy landscape around a schedule configuration.
 *
 * The energy landscape describes the topography of possible schedule states.
 * A smooth landscape with a single minimum is preferred; ruggededness
 * indicates many local minima that could trap optimization algorithms.
 *
 * @returns Mutation hook for energy landscape analysis
 *
 * @example
 * ```ts
 * const landscapeMutation = useEnergyLandscape();
 *
 * const handleAnalyze = async () => {
 *   const result = await landscapeMutation.mutateAsync({
 *     scheduleId: 'schedule-456',
 *     sampleSize: 500,
 *   });
 *   console.log('Ruggededness:', result.landscapeRuggedness);
 *   console.log('Is local minimum:', result.isLocalMinimum);
 * };
 * ```
 */
export function useEnergyLandscape() {
  return useMutation<EnergyLandscapeResponse, ApiError, EnergyLandscapeRequest>({
    mutationFn: (data) =>
      post<EnergyLandscapeResponse>(`${BASE_URL}/energy-landscape`, data),
  });
}

// Types are already exported at definition above
