/**
 * Free Energy Hook
 *
 * TanStack Query hook for Helmholtz free energy optimization.
 * Analyzes schedule stability using thermodynamic principles.
 */
import { useMutation } from '@tanstack/react-query';
import { ApiError } from '@/lib/api';
import {
  optimizeFreeEnergy,
  type FreeEnergyRequest,
  type FreeEnergyOptimizationResponse,
} from '@/api/exotic-resilience';

export function useFreeEnergy() {
  return useMutation<FreeEnergyOptimizationResponse, ApiError, FreeEnergyRequest>({
    mutationFn: optimizeFreeEnergy,
  });
}

export type { FreeEnergyRequest, FreeEnergyOptimizationResponse };
