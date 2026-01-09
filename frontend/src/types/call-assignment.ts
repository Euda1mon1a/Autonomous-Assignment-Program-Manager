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
  facultyRole: string | null;
}

export interface CallAssignment {
  id: string;
  date: string;
  personId: string;
  callType: CallType;
  isWeekend: boolean;
  isHoliday: boolean;
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
  callDate: string;  // Backend expects call_date for create
  personId: string;
  callType?: string;  // Backend accepts: sunday, weekday, holiday, backup
  isWeekend?: boolean;
  isHoliday?: boolean;
}

export interface CallAssignmentUpdate {
  callDate?: string;  // Backend expects call_date for update
  personId?: string;
  callType?: string;
  isWeekend?: boolean;
  isHoliday?: boolean;
}

export interface BulkCallAssignmentCreate {
  assignments: CallAssignmentCreate[];
  replaceExisting?: boolean;
}

export interface BulkCallAssignmentResponse {
  created: number;
  errors: string[];
}

// ============================================================================
// Bulk Update Types
// ============================================================================

export interface BulkCallAssignmentUpdateInput {
  personId?: string;
}

export interface BulkCallAssignmentUpdateRequest {
  assignmentIds: string[];
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
  assignmentIds: string[];
}

export interface PCATAssignmentResult {
  callAssignmentId: string;
  callDate: string;
  personId: string;
  personName: string | null;
  pcatCreated: boolean;
  doCreated: boolean;
  pcatAssignmentId: string | null;
  doAssignmentId: string | null;
  error: string | null;
}

export interface PCATGenerationResponse {
  processed: number;
  pcatCreated: number;
  doCreated: number;
  errors: string[];
  results: PCATAssignmentResult[];
}

// ============================================================================
// Report Types
// ============================================================================

export interface CallCoverageReport {
  startDate: string;
  endDate: string;
  totalExpectedNights: number;
  coveredNights: number;
  coveragePercentage: number;
  gaps: string[];
}

export interface CallStats {
  min: number;
  max: number;
  mean: number;
  stdev: number;
}

export interface FacultyCallDistribution {
  personId: string;
  name: string;
  sundayCalls: number;
  weekdayCalls: number;
  totalCalls: number;
}

export interface CallEquityReport {
  startDate: string;
  endDate: string;
  facultyCount: number;
  totalOvernightCalls: number;
  sundayCallStats: CallStats;
  weekdayCallStats: CallStats;
  distribution: FacultyCallDistribution[];
}

// ============================================================================
// Equity Preview Types
// ============================================================================

export interface SimulatedChange {
  assignmentId?: string;
  callDate?: string;
  oldPersonId?: string;
  newPersonId: string;
  callType?: CallType;
}

export interface EquityPreviewRequest {
  startDate: string;
  endDate: string;
  simulatedChanges?: SimulatedChange[];
}

export interface FacultyEquityDetail {
  personId: string;
  name: string;
  currentSundayCalls: number;
  currentWeekdayCalls: number;
  currentTotalCalls: number;
  projectedSundayCalls: number;
  projectedWeekdayCalls: number;
  projectedTotalCalls: number;
  delta: number;
}

export interface EquityPreviewResponse {
  startDate: string;
  endDate: string;
  currentEquity: CallEquityReport;
  projectedEquity: CallEquityReport;
  facultyDetails: FacultyEquityDetail[];
  improvementScore: number;
}

// ============================================================================
// Filter Types
// ============================================================================

export interface CallAssignmentFilters {
  startDate?: string;
  endDate?: string;
  personId?: string;
  callType?: CallType;
  skip?: number;
  limit?: number;
}
