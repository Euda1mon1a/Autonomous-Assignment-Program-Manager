/**
 * Daily Manifest Feature
 *
 * This module provides a real-time view of daily assignments showing
 * "Where is everyone NOW". It includes:
 *
 * - Location-based grouping of staff assignments
 * - Time-of-day filtering (AM/PM/All Day)
 * - Staffing summaries and capacity tracking
 * - Real-time updates and search functionality
 *
 * @module features/daily-manifest
 */

// ============================================================================
// Components
// ============================================================================

export { DailyManifest } from './DailyManifest';
export { LocationCard } from './LocationCard';
export { StaffingSummary } from './StaffingSummary';

// ============================================================================
// Hooks
// ============================================================================

export { useDailyManifest, useTodayManifest, manifestQueryKeys } from './hooks';

// ============================================================================
// Types
// ============================================================================

export type {
  PersonAssignment,
  LocationManifest,
  DailyManifestData,
  ManifestFilters,
} from './types';
