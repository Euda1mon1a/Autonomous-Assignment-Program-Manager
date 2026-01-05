/**
 * Call Assignment Types
 *
 * TypeScript interfaces for call assignment management including
 * CRUD operations, bulk updates, PCAT generation, and equity analysis.
 */

// ============================================================================
// Core Types
// ============================================================================

export type CallType = 'overnight' | 'weekend' | 'backup';

export interface PersonBrief {
  id: string;
  name: string;
  faculty_role: string | null;
}

export interface CallAssignment {
  id: string;
  call_date: string;
  person_id: string;
  call_type: CallType;
  is_weekend: boolean;
  is_holiday: boolean;
  person: PersonBrief | null;
}

export interface CallAssignmentListResponse {
  items: CallAssignment[];
  total: number;
  skip: number;
  limit: number;
}

// ============================================================================
// CRUD Request/Response Types
// ============================================================================

export interface CallAssignmentCreate {
  call_date: string;
  person_id: string;
  call_type?: CallType;
  is_weekend?: boolean;
  is_holiday?: boolean;
}

export interface CallAssignmentUpdate {
  call_date?: string;
  person_id?: string;
  call_type?: CallType;
  is_weekend?: boolean;
  is_holiday?: boolean;
}

export interface BulkCallAssignmentCreate {
  assignments: CallAssignmentCreate[];
  replace_existing?: boolean;
}

export interface BulkCallAssignmentResponse {
  created: number;
  errors: string[];
}

// ============================================================================
// Bulk Update Types
// ============================================================================

export interface BulkCallAssignmentUpdateInput {
  person_id?: string;
}

export interface BulkCallAssignmentUpdateRequest {
  assignment_ids: string[];
  updates: BulkCallAssignmentUpdateInput;
}

export interface BulkCallAssignmentUpdateResponse {
  updated: number;
  errors: string[];
  assignments: CallAssignment[];
}

// ============================================================================
// PCAT Generation Types
// ============================================================================

export interface PCATGenerationRequest {
  assignment_ids: string[];
}

export interface PCATAssignmentResult {
  call_assignment_id: string;
  call_date: string;
  person_id: string;
  person_name: string | null;
  pcat_created: boolean;
  do_created: boolean;
  pcat_assignment_id: string | null;
  do_assignment_id: string | null;
  error: string | null;
}

export interface PCATGenerationResponse {
  processed: number;
  pcat_created: number;
  do_created: number;
  errors: string[];
  results: PCATAssignmentResult[];
}

// ============================================================================
// Report Types
// ============================================================================

export interface CallCoverageReport {
  start_date: string;
  end_date: string;
  total_expected_nights: number;
  covered_nights: number;
  coverage_percentage: number;
  gaps: string[];
}

export interface CallStats {
  min: number;
  max: number;
  mean: number;
  stdev: number;
}

export interface FacultyCallDistribution {
  person_id: string;
  name: string;
  sunday_calls: number;
  weekday_calls: number;
  total_calls: number;
}

export interface CallEquityReport {
  start_date: string;
  end_date: string;
  faculty_count: number;
  total_overnight_calls: number;
  sunday_call_stats: CallStats;
  weekday_call_stats: CallStats;
  distribution: FacultyCallDistribution[];
}

// ============================================================================
// Equity Preview Types
// ============================================================================

export interface SimulatedChange {
  assignment_id?: string;
  call_date?: string;
  old_person_id?: string;
  new_person_id: string;
  call_type?: CallType;
}

export interface EquityPreviewRequest {
  start_date: string;
  end_date: string;
  simulated_changes?: SimulatedChange[];
}

export interface FacultyEquityDetail {
  person_id: string;
  name: string;
  current_sunday_calls: number;
  current_weekday_calls: number;
  current_total_calls: number;
  projected_sunday_calls: number;
  projected_weekday_calls: number;
  projected_total_calls: number;
  delta: number;
}

export interface EquityPreviewResponse {
  start_date: string;
  end_date: string;
  current_equity: CallEquityReport;
  projected_equity: CallEquityReport;
  faculty_details: FacultyEquityDetail[];
  improvement_score: number;
}

// ============================================================================
// Filter Types
// ============================================================================

export interface CallAssignmentFilters {
  start_date?: string;
  end_date?: string;
  person_id?: string;
  call_type?: CallType;
  skip?: number;
  limit?: number;
}
