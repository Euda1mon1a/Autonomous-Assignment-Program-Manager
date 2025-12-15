/**
 * Conflict Resolution Types
 *
 * Type definitions for the conflict resolution UI feature,
 * including conflict detection, resolution suggestions, and history tracking.
 */

// ============================================================================
// Conflict Severity and Types
// ============================================================================

export type ConflictSeverity = 'critical' | 'high' | 'medium' | 'low';

export type ConflictType =
  | 'scheduling_overlap'     // Double-booked time slot
  | 'acgme_violation'        // ACGME duty hour violation
  | 'supervision_missing'    // Required supervision not present
  | 'capacity_exceeded'      // Rotation capacity exceeded
  | 'absence_conflict'       // Assignment during absence
  | 'qualification_mismatch' // Person lacks required qualification
  | 'consecutive_duty'       // Too many consecutive duty days
  | 'rest_period'            // Insufficient rest between shifts
  | 'coverage_gap';          // No coverage for required slot

export type ConflictStatus = 'unresolved' | 'pending_review' | 'resolved' | 'ignored';

export type ResolutionMethod =
  | 'auto_resolved'       // System automatically resolved
  | 'manual_reassign'     // User manually reassigned
  | 'manual_override'     // User overrode with acknowledgment
  | 'swap'                // Swapped assignments between people
  | 'cancel_assignment'   // Removed the conflicting assignment
  | 'add_coverage'        // Added additional coverage
  | 'ignored';            // User chose to ignore

// ============================================================================
// Core Conflict Interface
// ============================================================================

export interface Conflict {
  id: string;
  type: ConflictType;
  severity: ConflictSeverity;
  status: ConflictStatus;
  title: string;
  description: string;

  // Affected entities
  affected_person_ids: string[];
  affected_assignment_ids: string[];
  affected_block_ids: string[];

  // Time context
  conflict_date: string;
  conflict_session?: 'AM' | 'PM';

  // Detection metadata
  detected_at: string;
  detected_by: 'system' | 'manual' | 'validation';
  rule_id?: string;

  // Resolution info
  resolved_at?: string;
  resolved_by?: string;
  resolution_method?: ResolutionMethod;
  resolution_notes?: string;

  // Additional context
  details: ConflictDetails;
}

// ============================================================================
// Conflict Details by Type
// ============================================================================

export interface SchedulingOverlapDetails {
  person_name: string;
  person_id: string;
  first_assignment: {
    id: string;
    rotation_name: string;
    location?: string;
  };
  second_assignment: {
    id: string;
    rotation_name: string;
    location?: string;
  };
}

export interface ACGMEViolationDetails {
  person_name: string;
  person_id: string;
  violation_type: string;
  current_value: number;
  limit_value: number;
  unit: string;
  period_start: string;
  period_end: string;
}

export interface SupervisionMissingDetails {
  rotation_name: string;
  rotation_id: string;
  assigned_residents: Array<{
    id: string;
    name: string;
    pgy_level?: number;
  }>;
  required_supervision_ratio: number;
}

export interface CapacityExceededDetails {
  rotation_name: string;
  rotation_id: string;
  current_count: number;
  max_capacity: number;
  assigned_people: Array<{
    id: string;
    name: string;
  }>;
}

export interface AbsenceConflictDetails {
  person_name: string;
  person_id: string;
  absence_type: string;
  absence_start: string;
  absence_end: string;
  assignment_rotation: string;
}

export interface QualificationMismatchDetails {
  person_name: string;
  person_id: string;
  rotation_name: string;
  required_qualification: string;
  person_qualifications: string[];
}

export interface CoverageGapDetails {
  rotation_name: string;
  rotation_id: string;
  required_coverage: number;
  current_coverage: number;
  gap_type: 'no_coverage' | 'insufficient_coverage';
}

export type ConflictDetails =
  | SchedulingOverlapDetails
  | ACGMEViolationDetails
  | SupervisionMissingDetails
  | CapacityExceededDetails
  | AbsenceConflictDetails
  | QualificationMismatchDetails
  | CoverageGapDetails
  | Record<string, unknown>;

// ============================================================================
// Resolution Suggestions
// ============================================================================

export interface ResolutionSuggestion {
  id: string;
  conflict_id: string;
  method: ResolutionMethod;
  title: string;
  description: string;
  impact_score: number; // 0-100, lower is better
  confidence: number;   // 0-100, higher is better

  // What would change
  changes: ResolutionChange[];

  // Side effects
  side_effects: string[];

  // Whether this is the recommended option
  recommended: boolean;
}

export interface ResolutionChange {
  type: 'reassign' | 'remove' | 'add' | 'swap' | 'modify';
  entity_type: 'assignment' | 'person' | 'block';
  entity_id: string;
  description: string;

  // For reassignment
  from_person_id?: string;
  from_person_name?: string;
  to_person_id?: string;
  to_person_name?: string;

  // For modification
  field?: string;
  old_value?: unknown;
  new_value?: unknown;
}

// ============================================================================
// Manual Override
// ============================================================================

export interface ManualOverride {
  conflict_id: string;
  override_type: 'acknowledge' | 'temporary' | 'permanent';
  reason: string;
  justification: string;
  expires_at?: string; // For temporary overrides
  approved_by?: string;
  approved_at?: string;

  // Audit fields for ACGME compliance
  is_acgme_related: boolean;
  acgme_exception_type?: string;
  supervisor_approval_required: boolean;
  supervisor_approved: boolean;
  supervisor_id?: string;
}

// ============================================================================
// Conflict History
// ============================================================================

export interface ConflictHistoryEntry {
  id: string;
  conflict_id: string;
  action: 'detected' | 'updated' | 'resolved' | 'reopened' | 'ignored' | 'overridden';
  timestamp: string;
  user_id?: string;
  user_name?: string;
  changes: Record<string, { from: unknown; to: unknown }>;
  notes?: string;
}

export interface ConflictPattern {
  id: string;
  type: ConflictType;
  frequency: number;
  first_occurrence: string;
  last_occurrence: string;
  affected_people: Array<{
    id: string;
    name: string;
    occurrence_count: number;
  }>;
  root_cause?: string;
  suggested_prevention?: string;
}

// ============================================================================
// Batch Resolution
// ============================================================================

export interface BatchResolutionRequest {
  conflict_ids: string[];
  resolution_method: ResolutionMethod;
  apply_suggestion_id?: string;
  notes?: string;
}

export interface BatchResolutionResult {
  total: number;
  successful: number;
  failed: number;
  results: Array<{
    conflict_id: string;
    success: boolean;
    message: string;
    resolution?: ResolutionSuggestion;
  }>;
}

// ============================================================================
// Filter and Sort Options
// ============================================================================

export interface ConflictFilters {
  types?: ConflictType[];
  severities?: ConflictSeverity[];
  statuses?: ConflictStatus[];
  person_ids?: string[];
  date_range?: {
    start: string;
    end: string;
  };
  search?: string;
}

export type ConflictSortField = 'severity' | 'date' | 'type' | 'status' | 'detected_at';
export type SortDirection = 'asc' | 'desc';

export interface ConflictSortOptions {
  field: ConflictSortField;
  direction: SortDirection;
}

// ============================================================================
// Statistics
// ============================================================================

export interface ConflictStatistics {
  total_conflicts: number;
  by_severity: Record<ConflictSeverity, number>;
  by_type: Record<ConflictType, number>;
  by_status: Record<ConflictStatus, number>;
  resolution_rate: number;
  average_resolution_time_hours: number;
  most_affected_people: Array<{
    id: string;
    name: string;
    conflict_count: number;
  }>;
  trending_up: boolean;
}
