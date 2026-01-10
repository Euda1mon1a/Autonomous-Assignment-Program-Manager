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
  | 'acgmeViolation'        // ACGME duty hour violation
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
  affectedPersonIds: string[];
  affectedAssignmentIds: string[];
  affectedBlockIds: string[];

  // Time context
  conflictDate: string;
  conflictSession?: 'AM' | 'PM';

  // Detection metadata
  detectedAt: string;
  detectedBy: 'system' | 'manual' | 'validation';
  rule_id?: string;

  // Resolution info
  resolvedAt?: string;
  resolvedBy?: string;
  resolutionMethod?: ResolutionMethod;
  resolutionNotes?: string;

  // Additional context
  details: ConflictDetails;
}

// ============================================================================
// Conflict Details by Type
// ============================================================================

export interface SchedulingOverlapDetails {
  personName: string;
  personId: string;
  firstAssignment: {
    id: string;
    rotationName: string;
    location?: string;
  };
  secondAssignment: {
    id: string;
    rotationName: string;
    location?: string;
  };
}

export interface ACGMEViolationDetails {
  personName: string;
  personId: string;
  violationType: string;
  currentValue: number;
  limitValue: number;
  unit: string;
  periodStart: string;
  periodEnd: string;
}

export interface SupervisionMissingDetails {
  rotationName: string;
  rotationId: string;
  assignedResidents: Array<{
    id: string;
    name: string;
    pgyLevel?: number;
  }>;
  required_supervisionRatio: number;
}

export interface CapacityExceededDetails {
  rotationName: string;
  rotationId: string;
  currentCount: number;
  maxCapacity: number;
  assignedPeople: Array<{
    id: string;
    name: string;
  }>;
}

export interface AbsenceConflictDetails {
  personName: string;
  personId: string;
  absenceType: string;
  absenceStart: string;
  absenceEnd: string;
  assignmentRotation: string;
}

export interface QualificationMismatchDetails {
  personName: string;
  personId: string;
  rotationName: string;
  requiredQualification: string;
  personQualifications: string[];
}

export interface CoverageGapDetails {
  rotationName: string;
  rotationId: string;
  requiredCoverage: number;
  currentCoverage: number;
  gapType: 'no_coverage' | 'insufficient_coverage';
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
  conflictId: string;
  method: ResolutionMethod;
  title: string;
  description: string;
  impactScore: number; // 0-100, lower is better
  confidence: number;   // 0-100, higher is better

  // What would change
  changes: ResolutionChange[];

  // Side effects
  sideEffects: string[];

  // Whether this is the recommended option
  recommended: boolean;
}

export interface ResolutionChange {
  type: 'reassign' | 'remove' | 'add' | 'swap' | 'modify';
  entityType: 'assignment' | 'person' | 'block';
  entityId: string;
  description: string;

  // For reassignment
  fromPersonId?: string;
  fromPersonName?: string;
  toPersonId?: string;
  toPersonName?: string;

  // For modification
  field?: string;
  old_value?: unknown;
  new_value?: unknown;
}

// ============================================================================
// Manual Override
// ============================================================================

export interface ManualOverride {
  conflictId: string;
  overrideType: 'acknowledge' | 'temporary' | 'permanent';
  reason: string;
  justification: string;
  expiresAt?: string; // For temporary overrides
  approved_by?: string;
  approved_at?: string;

  // Audit fields for ACGME compliance
  isAcgmeRelated: boolean;
  acgme_exception_type?: string;
  supervisorApprovalRequired: boolean;
  supervisorApproved: boolean;
  supervisor_id?: string;
}

// ============================================================================
// Conflict History
// ============================================================================

export interface ConflictHistoryEntry {
  id: string;
  conflictId: string;
  action: 'detected' | 'updated' | 'resolved' | 'reopened' | 'ignored' | 'overridden';
  timestamp: string;
  userId?: string;
  userName?: string;
  changes: Record<string, { from: unknown; to: unknown }>;
  notes?: string;
}

export interface ConflictPattern {
  id: string;
  type: ConflictType;
  frequency: number;
  firstOccurrence: string;
  lastOccurrence: string;
  affectedPeople: Array<{
    id: string;
    name: string;
    occurrenceCount: number;
  }>;
  rootCause?: string;
  suggestedPrevention?: string;
}

// ============================================================================
// Batch Resolution
// ============================================================================

export interface BatchResolutionRequest {
  conflictIds: string[];
  resolutionMethod: ResolutionMethod;
  apply_suggestionId?: string;
  notes?: string;
}

export interface BatchResolutionResult {
  total: number;
  successful: number;
  failed: number;
  results: Array<{
    conflictId: string;
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
  personIds?: string[];
  dateRange?: {
    start: string;
    end: string;
  };
  search?: string;
}

export type ConflictSortField = 'severity' | 'date' | 'type' | 'status' | 'detectedAt';
export type SortDirection = 'asc' | 'desc';

export interface ConflictSortOptions {
  field: ConflictSortField;
  direction: SortDirection;
}

// ============================================================================
// Statistics
// ============================================================================

export interface ConflictStatistics {
  totalConflicts: number;
  bySeverity: Record<ConflictSeverity, number>;
  byType: Record<ConflictType, number>;
  byStatus: Record<ConflictStatus, number>;
  resolutionRate: number;
  averageResolutionTimeHours: number;
  mostAffectedPeople: Array<{
    id: string;
    name: string;
    conflictCount: number;
  }>;
  trendingUp: boolean;
}
