// API Response Types for Residency Scheduler
// Generated from backend models

// ============================================================================
// Person Types
// ============================================================================

export interface Person {
  id: string;
  name: string;
  email: string | null;
  type: 'resident' | 'faculty';
  pgy_level: number | null;
  performs_procedures: boolean;
  specialties: string[] | null;
  primary_duty: string | null;
  created_at: string;
  updated_at: string;
}

export interface PersonCreate {
  name: string;
  email?: string;
  type: 'resident' | 'faculty';
  pgy_level?: number;
  performs_procedures?: boolean;
  specialties?: string[];
  primary_duty?: string;
}

export interface PersonUpdate {
  name?: string;
  email?: string;
  type?: 'resident' | 'faculty';
  pgy_level?: number;
  performs_procedures?: boolean;
  specialties?: string[];
  primary_duty?: string;
}

// ============================================================================
// Block Types
// ============================================================================

export interface Block {
  id: string;
  date: string;
  time_of_day: 'AM' | 'PM';
  block_number: number;
  is_weekend: boolean;
  is_holiday: boolean;
  holiday_name: string | null;
}

export interface BlockCreate {
  date: string;
  time_of_day: 'AM' | 'PM';
  block_number: number;
  is_weekend?: boolean;
  is_holiday?: boolean;
  holiday_name?: string;
}

export interface BlockUpdate {
  date?: string;
  time_of_day?: 'AM' | 'PM';
  block_number?: number;
  is_weekend?: boolean;
  is_holiday?: boolean;
  holiday_name?: string;
}

// ============================================================================
// Assignment Types
// ============================================================================

export interface Assignment {
  id: string;
  block_id: string;
  person_id: string;
  rotation_template_id: string | null;
  role: 'primary' | 'supervising' | 'backup';
  activity_override: string | null;
  notes: string | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface AssignmentCreate {
  block_id: string;
  person_id: string;
  rotation_template_id?: string;
  role: 'primary' | 'supervising' | 'backup';
  activity_override?: string;
  notes?: string;
  created_by?: string;
}

export interface AssignmentUpdate {
  block_id?: string;
  person_id?: string;
  rotation_template_id?: string;
  role?: 'primary' | 'supervising' | 'backup';
  activity_override?: string;
  notes?: string;
}

// ============================================================================
// Absence Types
// ============================================================================

export interface Absence {
  id: string;
  person_id: string;
  start_date: string;
  end_date: string;
  absence_type: 'vacation' | 'deployment' | 'tdy' | 'medical' | 'family_emergency' | 'conference';
  deployment_orders: boolean;
  tdy_location: string | null;
  replacement_activity: string | null;
  notes: string | null;
  created_at: string;
}

export interface AbsenceCreate {
  person_id: string;
  start_date: string;
  end_date: string;
  absence_type: 'vacation' | 'deployment' | 'tdy' | 'medical' | 'family_emergency' | 'conference';
  deployment_orders?: boolean;
  tdy_location?: string;
  replacement_activity?: string;
  notes?: string;
}

export interface AbsenceUpdate {
  start_date?: string;
  end_date?: string;
  absence_type?: 'vacation' | 'deployment' | 'tdy' | 'medical' | 'family_emergency' | 'conference';
  deployment_orders?: boolean;
  tdy_location?: string;
  replacement_activity?: string;
  notes?: string;
}

// ============================================================================
// RotationTemplate Types
// ============================================================================

export interface RotationTemplate {
  id: string;
  name: string;
  activity_type: string;
  abbreviation: string | null;
  clinic_location: string | null;
  max_residents: number | null;
  requires_specialty: string | null;
  requires_procedure_credential: boolean;
  supervision_required: boolean;
  max_supervision_ratio: number;
  created_at: string;
}

export interface RotationTemplateCreate {
  name: string;
  activity_type: string;
  abbreviation?: string;
  clinic_location?: string;
  max_residents?: number;
  requires_specialty?: string;
  requires_procedure_credential?: boolean;
  supervision_required?: boolean;
  max_supervision_ratio?: number;
}

export interface RotationTemplateUpdate {
  name?: string;
  activity_type?: string;
  abbreviation?: string;
  clinic_location?: string;
  max_residents?: number;
  requires_specialty?: string;
  requires_procedure_credential?: boolean;
  supervision_required?: boolean;
  max_supervision_ratio?: number;
}

// ============================================================================
// ScheduleRun Types (Response only)
// ============================================================================

export type SchedulingAlgorithm = 'greedy' | 'cp_sat' | 'pulp' | 'hybrid';

export interface ScheduleRun {
  id: string;
  start_date: string;
  end_date: string;
  algorithm: SchedulingAlgorithm;
  status: 'success' | 'partial' | 'failed';
  total_blocks_assigned: number | null;
  acgme_violations: number;
  runtime_seconds: number | null;
  config_json: Record<string, unknown> | null;
  created_at: string;
}

// ============================================================================
// ValidationResult Types (Response only)
// ============================================================================

export interface Violation {
  type: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  person_id: string | null;
  person_name: string | null;
  block_id: string | null;
  message: string;
  details: Record<string, unknown> | null;
}

export interface ValidationResult {
  valid: boolean;
  total_violations: number;
  violations: Violation[];
  coverage_rate: number;
  statistics: Record<string, unknown> | null;
}

// ============================================================================
// Solver Statistics Types
// ============================================================================

export interface SolverStatistics {
  total_blocks: number | null;
  total_residents: number | null;
  coverage_rate: number | null;
  branches: number | null;  // CP-SAT specific
  conflicts: number | null; // CP-SAT specific
}

// ============================================================================
// Schedule Request/Response Types
// ============================================================================

export interface ScheduleRequest {
  start_date: string;
  end_date: string;
  pgy_levels?: number[];
  rotation_template_ids?: string[];
  algorithm: SchedulingAlgorithm;
  timeout_seconds?: number;
}

export interface ScheduleResponse {
  status: 'success' | 'partial' | 'failed';
  message: string;
  total_blocks_assigned: number;
  total_blocks: number;
  validation: ValidationResult;
  run_id: string | null;
  solver_stats: SolverStatistics | null;
}

// ============================================================================
// API List Response Types
// ============================================================================

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}
