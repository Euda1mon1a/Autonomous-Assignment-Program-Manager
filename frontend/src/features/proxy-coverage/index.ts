/**
 * Proxy Coverage Feature
 *
 * Dashboard showing "who is covering for whom" across the scheduling system.
 * Includes coverage from swaps, remote surrogates, backup call, and absences.
 *
 * @module features/proxy-coverage
 */

// ============================================================================
// Components
// ============================================================================

export { ProxyCoverageDashboard } from './ProxyCoverageDashboard';
export { ProxyCoverageCard } from './ProxyCoverageCard';

// ============================================================================
// Hooks
// ============================================================================

export {
  useProxyCoverage,
  useTodayProxyCoverage,
  useFilteredProxyCoverage,
  proxyCoverageQueryKeys,
} from './hooks';

// ============================================================================
// Types
// ============================================================================

export type {
  PersonRef,
  CoverageType,
  CoverageStatus,
  CoverageRelationship,
  PersonCoverageSummary,
  ProxyCoverageResponse,
  CoverageStats,
  ProxyCoverageFilters,
} from './types';
