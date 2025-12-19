// API Response Types for Residency Scheduler
// Generated from backend models

// ============================================================================
// Utility Types
// ============================================================================

/**
 * Represents a UUID string identifier
 * @example "550e8400-e29b-41d4-a716-446655440000"
 */
export type UUID = string;

/**
 * Represents an ISO 8601 date string (YYYY-MM-DD)
 * @example "2025-12-18"
 */
export type DateString = string;

/**
 * Represents an ISO 8601 datetime string with timezone
 * @example "2025-12-18T10:30:00Z"
 */
export type DateTimeString = string;

/**
 * Represents an email address string
 * @example "user@example.com"
 */
export type Email = string;

// ============================================================================
// Enums
// ============================================================================

/**
 * Types of personnel in the residency program
 */
export enum PersonType {
  /** Medical resident in training */
  RESIDENT = 'resident',
  /** Supervising faculty member */
  FACULTY = 'faculty'
}

/**
 * Time periods for scheduling blocks
 */
export enum TimeOfDay {
  /** Morning shift */
  AM = 'AM',
  /** Afternoon/Evening shift */
  PM = 'PM'
}

/**
 * Assignment roles for personnel in a schedule block
 */
export enum AssignmentRole {
  /** Primary person assigned to the activity */
  PRIMARY = 'primary',
  /** Supervising faculty member */
  SUPERVISING = 'supervising',
  /** Backup person for the activity */
  BACKUP = 'backup'
}

/**
 * Types of absences that can be recorded
 */
export enum AbsenceType {
  /** Scheduled vacation time */
  VACATION = 'vacation',
  /** Military deployment */
  DEPLOYMENT = 'deployment',
  /** Temporary duty assignment */
  TDY = 'tdy',
  /** Medical leave */
  MEDICAL = 'medical',
  /** Family emergency leave */
  FAMILY_EMERGENCY = 'family_emergency',
  /** Conference attendance */
  CONFERENCE = 'conference',
  /** Sick leave */
  SICK = 'sick',
  /** Bereavement leave */
  BEREAVEMENT = 'bereavement',
  /** Emergency leave */
  EMERGENCY_LEAVE = 'emergency_leave',
  /** Convalescent leave */
  CONVALESCENT = 'convalescent',
  /** Maternity or paternity leave */
  MATERNITY_PATERNITY = 'maternity_paternity',
  /** Personal leave */
  PERSONAL = 'personal'
}

/**
 * Severity levels for ACGME violations and scheduling issues
 */
export enum ViolationSeverity {
  /** Critical violation requiring immediate attention */
  CRITICAL = 'CRITICAL',
  /** High priority violation */
  HIGH = 'HIGH',
  /** Medium priority violation */
  MEDIUM = 'MEDIUM',
  /** Low priority violation or warning */
  LOW = 'LOW'
}

/**
 * Available scheduling algorithms
 */
export enum SchedulingAlgorithm {
  /** Greedy algorithm - fast but may not find optimal solution */
  GREEDY = 'greedy',
  /** Google OR-Tools CP-SAT solver - optimal but slower */
  CP_SAT = 'cp_sat',
  /** PuLP linear programming solver */
  PULP = 'pulp',
  /** Hybrid approach combining multiple algorithms */
  HYBRID = 'hybrid'
}

/**
 * Status of a schedule generation run
 */
export enum ScheduleStatus {
  /** Schedule generated successfully with full coverage */
  SUCCESS = 'success',
  /** Schedule generated with partial coverage or minor issues */
  PARTIAL = 'partial',
  /** Schedule generation failed */
  FAILED = 'failed'
}

// ============================================================================
// Person Types
// ============================================================================

/**
 * Represents a person in the residency program (resident or faculty)
 */
export interface Person {
  /** Unique identifier */
  id: UUID;
  /** Full name of the person */
  name: string;
  /** Email address */
  email: Email | null;
  /** Type of person (resident or faculty) */
  type: PersonType;
  /** Post-graduate year level (for residents only) */
  pgy_level: number | null;
  /** Whether the person is credentialed to perform procedures */
  performs_procedures: boolean;
  /** List of medical specialties */
  specialties: string[] | null;
  /** Primary duty assignment */
  primary_duty: string | null;
  /** Timestamp when the record was created */
  created_at: DateTimeString;
  /** Timestamp when the record was last updated */
  updated_at: DateTimeString;
}

/**
 * Data required to create a new person record
 */
export interface PersonCreate {
  /** Full name of the person */
  name: string;
  /** Email address (optional) */
  email?: Email;
  /** Type of person (resident or faculty) */
  type: PersonType;
  /** Post-graduate year level (for residents only) */
  pgy_level?: number;
  /** Whether the person is credentialed to perform procedures */
  performs_procedures?: boolean;
  /** List of medical specialties */
  specialties?: string[];
  /** Primary duty assignment */
  primary_duty?: string;
}

/**
 * Data that can be updated for an existing person
 */
export interface PersonUpdate {
  /** Full name of the person */
  name?: string;
  /** Email address */
  email?: Email;
  /** Type of person (resident or faculty) */
  type?: PersonType;
  /** Post-graduate year level (for residents only) */
  pgy_level?: number;
  /** Whether the person is credentialed to perform procedures */
  performs_procedures?: boolean;
  /** List of medical specialties */
  specialties?: string[];
  /** Primary duty assignment */
  primary_duty?: string;
}

// ============================================================================
// Block Types
// ============================================================================

/**
 * Represents a scheduling block (a specific time period on a specific day)
 */
export interface Block {
  /** Unique identifier */
  id: UUID;
  /** Date of the block */
  date: DateString;
  /** Time period (AM or PM) */
  time_of_day: TimeOfDay;
  /** Sequential block number */
  block_number: number;
  /** Whether this block falls on a weekend */
  is_weekend: boolean;
  /** Whether this block falls on a holiday */
  is_holiday: boolean;
  /** Name of the holiday if applicable */
  holiday_name: string | null;
}

/**
 * Data required to create a new scheduling block
 */
export interface BlockCreate {
  /** Date of the block */
  date: DateString;
  /** Time period (AM or PM) */
  time_of_day: TimeOfDay;
  /** Sequential block number */
  block_number: number;
  /** Whether this block falls on a weekend */
  is_weekend?: boolean;
  /** Whether this block falls on a holiday */
  is_holiday?: boolean;
  /** Name of the holiday if applicable */
  holiday_name?: string;
}

/**
 * Data that can be updated for an existing block
 */
export interface BlockUpdate {
  /** Date of the block */
  date?: DateString;
  /** Time period (AM or PM) */
  time_of_day?: TimeOfDay;
  /** Sequential block number */
  block_number?: number;
  /** Whether this block falls on a weekend */
  is_weekend?: boolean;
  /** Whether this block falls on a holiday */
  is_holiday?: boolean;
  /** Name of the holiday if applicable */
  holiday_name?: string;
}

// ============================================================================
// Assignment Types
// ============================================================================

/**
 * Represents an assignment of a person to a specific block
 */
export interface Assignment {
  /** Unique identifier */
  id: UUID;
  /** ID of the block this assignment belongs to */
  block_id: UUID;
  /** ID of the person assigned */
  person_id: UUID;
  /** ID of the rotation template being used (if applicable) */
  rotation_template_id: UUID | null;
  /** Role of the person in this assignment */
  role: AssignmentRole;
  /** Custom activity description overriding the rotation template */
  activity_override: string | null;
  /** Additional notes about this assignment */
  notes: string | null;
  /** ID of the user who created this assignment */
  created_by: UUID | null;
  /** Timestamp when the assignment was created */
  created_at: DateTimeString;
  /** Timestamp when the assignment was last updated */
  updated_at: DateTimeString;
}

/**
 * Data required to create a new assignment
 */
export interface AssignmentCreate {
  /** ID of the block this assignment belongs to */
  block_id: UUID;
  /** ID of the person to assign */
  person_id: UUID;
  /** ID of the rotation template to use (optional) */
  rotation_template_id?: UUID;
  /** Role of the person in this assignment */
  role: AssignmentRole;
  /** Custom activity description overriding the rotation template */
  activity_override?: string;
  /** Additional notes about this assignment */
  notes?: string;
  /** ID of the user creating this assignment */
  created_by?: UUID;
}

/**
 * Data that can be updated for an existing assignment
 */
export interface AssignmentUpdate {
  /** ID of the block this assignment belongs to */
  block_id?: UUID;
  /** ID of the person assigned */
  person_id?: UUID;
  /** ID of the rotation template being used */
  rotation_template_id?: UUID;
  /** Role of the person in this assignment */
  role?: AssignmentRole;
  /** Custom activity description overriding the rotation template */
  activity_override?: string;
  /** Additional notes about this assignment */
  notes?: string;
}

// ============================================================================
// Absence Types
// ============================================================================

/**
 * Represents a scheduled absence for a person
 */
export interface Absence {
  /** Unique identifier */
  id: UUID;
  /** ID of the person who will be absent */
  person_id: UUID;
  /** Start date of the absence */
  start_date: DateString;
  /** End date of the absence */
  end_date: DateString;
  /** Type of absence */
  absence_type: AbsenceType;
  /** Whether the absence is due to deployment orders (military) */
  deployment_orders: boolean;
  /** Location of TDY (temporary duty) if applicable */
  tdy_location: string | null;
  /** Replacement activity to be scheduled during absence */
  replacement_activity: string | null;
  /** Additional notes about the absence */
  notes: string | null;
  /** Timestamp when the absence was created */
  created_at: DateTimeString;
}

/**
 * Data required to create a new absence record
 */
export interface AbsenceCreate {
  /** ID of the person who will be absent */
  person_id: UUID;
  /** Start date of the absence */
  start_date: DateString;
  /** End date of the absence */
  end_date: DateString;
  /** Type of absence */
  absence_type: AbsenceType;
  /** Whether the absence is due to deployment orders (military) */
  deployment_orders?: boolean;
  /** Location of TDY (temporary duty) if applicable */
  tdy_location?: string;
  /** Replacement activity to be scheduled during absence */
  replacement_activity?: string;
  /** Additional notes about the absence */
  notes?: string;
}

/**
 * Data that can be updated for an existing absence
 */
export interface AbsenceUpdate {
  /** Start date of the absence */
  start_date?: DateString;
  /** End date of the absence */
  end_date?: DateString;
  /** Type of absence */
  absence_type?: AbsenceType;
  /** Whether the absence is due to deployment orders (military) */
  deployment_orders?: boolean;
  /** Location of TDY (temporary duty) if applicable */
  tdy_location?: string;
  /** Replacement activity to be scheduled during absence */
  replacement_activity?: string;
  /** Additional notes about the absence */
  notes?: string;
}

// ============================================================================
// RotationTemplate Types
// ============================================================================

/**
 * Represents a template for a rotation/activity that can be assigned to residents
 */
export interface RotationTemplate {
  /** Unique identifier */
  id: UUID;
  /** Full name of the rotation */
  name: string;
  /** Type/category of the activity */
  activity_type: string;
  /** Short abbreviation for display in schedules */
  abbreviation: string | null;
  /** Physical location of the clinic/rotation */
  clinic_location: string | null;
  /** Maximum number of residents that can be assigned simultaneously */
  max_residents: number | null;
  /** Required specialty for this rotation (if any) */
  requires_specialty: string | null;
  /** Whether the rotation requires procedure credentials */
  requires_procedure_credential: boolean;
  /** Whether faculty supervision is required */
  supervision_required: boolean;
  /** Maximum ratio of residents to supervisors (e.g., 3 means 3:1) */
  max_supervision_ratio: number;
  /** Timestamp when the template was created */
  created_at: DateTimeString;
}

/**
 * Data required to create a new rotation template
 */
export interface RotationTemplateCreate {
  /** Full name of the rotation */
  name: string;
  /** Type/category of the activity */
  activity_type: string;
  /** Short abbreviation for display in schedules */
  abbreviation?: string;
  /** Physical location of the clinic/rotation */
  clinic_location?: string;
  /** Maximum number of residents that can be assigned simultaneously */
  max_residents?: number;
  /** Required specialty for this rotation (if any) */
  requires_specialty?: string;
  /** Whether the rotation requires procedure credentials */
  requires_procedure_credential?: boolean;
  /** Whether faculty supervision is required */
  supervision_required?: boolean;
  /** Maximum ratio of residents to supervisors (e.g., 3 means 3:1) */
  max_supervision_ratio?: number;
}

/**
 * Data that can be updated for an existing rotation template
 */
export interface RotationTemplateUpdate {
  /** Full name of the rotation */
  name?: string;
  /** Type/category of the activity */
  activity_type?: string;
  /** Short abbreviation for display in schedules */
  abbreviation?: string;
  /** Physical location of the clinic/rotation */
  clinic_location?: string;
  /** Maximum number of residents that can be assigned simultaneously */
  max_residents?: number;
  /** Required specialty for this rotation (if any) */
  requires_specialty?: string;
  /** Whether the rotation requires procedure credentials */
  requires_procedure_credential?: boolean;
  /** Whether faculty supervision is required */
  supervision_required?: boolean;
  /** Maximum ratio of residents to supervisors (e.g., 3 means 3:1) */
  max_supervision_ratio?: number;
}

// ============================================================================
// ScheduleRun Types (Response only)
// ============================================================================

/**
 * Represents a completed schedule generation run
 * Contains metadata about the scheduling algorithm execution
 */
export interface ScheduleRun {
  /** Unique identifier */
  id: UUID;
  /** Start date of the scheduling period */
  start_date: DateString;
  /** End date of the scheduling period */
  end_date: DateString;
  /** Algorithm used for schedule generation */
  algorithm: SchedulingAlgorithm;
  /** Status of the schedule generation */
  status: ScheduleStatus;
  /** Number of blocks successfully assigned */
  total_blocks_assigned: number | null;
  /** Number of ACGME violations detected */
  acgme_violations: number;
  /** Runtime of the algorithm in seconds */
  runtime_seconds: number | null;
  /** Configuration parameters used for this run */
  config_json: ScheduleConfig | null;
  /** Timestamp when the run was created */
  created_at: DateTimeString;
}

// ============================================================================
// ValidationResult Types (Response only)
// ============================================================================

/**
 * Represents a single ACGME or scheduling rule violation
 */
export interface Violation {
  /** Type/category of the violation */
  type: string;
  /** Severity level of the violation */
  severity: ViolationSeverity;
  /** ID of the person involved in the violation (if applicable) */
  person_id: UUID | null;
  /** Name of the person involved in the violation (if applicable) */
  person_name: string | null;
  /** ID of the block where the violation occurred (if applicable) */
  block_id: UUID | null;
  /** Human-readable description of the violation */
  message: string;
  /** Additional structured details about the violation */
  details: ViolationDetails | null;
}

/**
 * Structured details about a violation
 */
export interface ViolationDetails {
  /** Current value that caused the violation */
  current_value?: number | string;
  /** Maximum allowed value */
  max_allowed?: number | string;
  /** Minimum required value */
  min_required?: number | string;
  /** Date range affected by the violation */
  date_range?: {
    start: DateString;
    end: DateString;
  };
  /** Additional context information */
  [key: string]: unknown;
}

/**
 * Result of validating a schedule against ACGME rules
 */
export interface ValidationResult {
  /** Whether the schedule is valid (no critical violations) */
  valid: boolean;
  /** Total number of violations detected */
  total_violations: number;
  /** List of all violations found */
  violations: Violation[];
  /** Percentage of blocks with assignments (0-1) */
  coverage_rate: number;
  /** Additional statistical information about the schedule */
  statistics: ValidationStatistics | null;
}

/**
 * Statistical information about schedule validation
 */
export interface ValidationStatistics {
  /** Total number of blocks in the schedule */
  total_blocks?: number;
  /** Number of blocks with assignments */
  assigned_blocks?: number;
  /** Number of residents in the schedule */
  total_residents?: number;
  /** Average assignments per resident */
  avg_assignments_per_resident?: number;
  /** Violations grouped by severity */
  violations_by_severity?: {
    [K in ViolationSeverity]?: number;
  };
  /** Additional statistics */
  [key: string]: unknown;
}

// ============================================================================
// Solver Statistics Types
// ============================================================================

/**
 * Statistics from the scheduling algorithm solver
 */
export interface SolverStatistics {
  /** Total number of blocks in the scheduling period */
  total_blocks: number | null;
  /** Total number of residents being scheduled */
  total_residents: number | null;
  /** Percentage of blocks successfully assigned (0-1) */
  coverage_rate: number | null;
  /** Number of search tree branches explored (CP-SAT specific) */
  branches: number | null;
  /** Number of conflicts encountered during solving (CP-SAT specific) */
  conflicts: number | null;
}

// ============================================================================
// Schedule Configuration Types
// ============================================================================

/**
 * Configuration parameters for schedule generation
 */
export interface ScheduleConfig {
  /** Maximum number of consecutive days a resident can work */
  max_consecutive_days?: number;
  /** Minimum hours of rest between shifts */
  min_rest_hours?: number;
  /** Whether to enforce strict ACGME compliance */
  strict_acgme_compliance?: boolean;
  /** Weight for coverage optimization (0-1) */
  coverage_weight?: number;
  /** Weight for fairness optimization (0-1) */
  fairness_weight?: number;
  /** Additional algorithm-specific parameters */
  [key: string]: unknown;
}

// ============================================================================
// Schedule Request/Response Types
// ============================================================================

/**
 * Request parameters for generating a schedule
 */
export interface ScheduleRequest {
  /** Start date of the scheduling period */
  start_date: DateString;
  /** End date of the scheduling period */
  end_date: DateString;
  /** Filter to include only specific PGY levels */
  pgy_levels?: number[];
  /** Filter to include only specific rotation templates */
  rotation_template_ids?: UUID[];
  /** Scheduling algorithm to use */
  algorithm: SchedulingAlgorithm;
  /** Maximum time allowed for schedule generation (in seconds) */
  timeout_seconds?: number;
  /** Optional configuration parameters */
  config?: ScheduleConfig;
}

/**
 * Response from schedule generation
 */
export interface ScheduleResponse {
  /** Status of the schedule generation */
  status: ScheduleStatus;
  /** Human-readable message about the result */
  message: string;
  /** Number of blocks successfully assigned */
  total_blocks_assigned: number;
  /** Total number of blocks in the period */
  total_blocks: number;
  /** Validation results for the generated schedule */
  validation: ValidationResult;
  /** ID of the schedule run record */
  run_id: UUID | null;
  /** Statistics from the solver */
  solver_stats: SolverStatistics | null;
}

// ============================================================================
// API List Response Types
// ============================================================================

/**
 * Generic paginated response wrapper for list endpoints
 * @template T The type of items in the response
 */
export interface PaginatedResponse<T> {
  /** Array of items for the current page */
  items: T[];
  /** Total number of items across all pages */
  total: number;
  /** Current page number (1-indexed) */
  page: number;
  /** Number of items per page */
  page_size: number;
  /** Total number of pages */
  pages: number;
}

// ============================================================================
// API Error Response Types
// ============================================================================

/**
 * Standard error response from the API
 */
export interface ApiError {
  /** Error message */
  message: string;
  /** HTTP status code */
  status: number;
  /** Detailed error information (if available) */
  detail?: string | Record<string, unknown>;
  /** Error code for programmatic handling */
  error_code?: string;
}

// ============================================================================
// Utility Types for API Operations
// ============================================================================

/**
 * Generic API response wrapper
 * @template T The type of data in the response
 */
export type ApiResponse<T> = {
  success: true;
  data: T;
} | {
  success: false;
  error: ApiError;
};

/**
 * Type guard to check if an API response is successful
 */
export function isSuccessResponse<T>(
  response: ApiResponse<T>
): response is { success: true; data: T } {
  return response.success === true;
}

/**
 * Type guard to check if an API response is an error
 */
export function isErrorResponse<T>(
  response: ApiResponse<T>
): response is { success: false; error: ApiError } {
  return response.success === false;
}
