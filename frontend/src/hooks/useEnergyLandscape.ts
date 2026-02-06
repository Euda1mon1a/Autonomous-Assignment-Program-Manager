/**
 * Energy Landscape Hook
 *
 * TanStack Query hook for energy landscape analysis.
 * Analyzes the optimization landscape around the current schedule.
 */
import { useMutation } from '@tanstack/react-query';
import { ApiError } from '@/lib/api';
import {
  analyzeEnergyLandscape,
  type EnergyLandscapeRequest,
  type EnergyLandscapeResponse,
} from '@/api/exotic-resilience';

export function useEnergyLandscape() {
  return useMutation<EnergyLandscapeResponse, ApiError, EnergyLandscapeRequest>({
    mutationFn: analyzeEnergyLandscape,
  });
}

export type { EnergyLandscapeRequest, EnergyLandscapeResponse };
