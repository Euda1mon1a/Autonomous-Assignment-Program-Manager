/**
 * Daily Manifest Feature
 *
 * This module provides a real-time view of daily assignments showing
 * "Where is everyone NOW". It includes:
 *
 * V2 redesign for nursing staff / front desk:
 * - Situational awareness (FMIT, nights, remote)
 * - Attending at-a-glance
 * - Clinic coverage table (Location × AM/PM)
 *
 * @module features/daily-manifest
 */

// ============================================================================
// Components
// ============================================================================

export { DailyManifest } from './DailyManifest';
export { SituationalAwareness } from './SituationalAwareness';
export { ClinicCoverageTable } from './ClinicCoverageTable';
export { LocationCard } from './LocationCard';
export { StaffingSummary } from './StaffingSummary';

// ============================================================================
// Hooks
// ============================================================================

export {
  useDailyManifest,
  useTodayManifest,
  useDailyManifestV2,
  useTodayManifestV2,
  manifestQueryKeys,
} from './hooks';

// ============================================================================
// Types
// ============================================================================

export type {
  // V1 types (kept for backward compatibility)
  PersonAssignment,
  LocationManifest,
  DailyManifestData,
  ManifestFilters,
  // V2 types
  PersonSummary,
  FMITSection,
  NightCallInfo,
  RemoteAssignment,
  AttendingInfo,
  AssignmentSummary,
  HalfDayStaff,
  LocationManifestV2,
  SituationalAwareness as SituationalAwarenessType,
  DailyManifestDataV2,
} from './types';
