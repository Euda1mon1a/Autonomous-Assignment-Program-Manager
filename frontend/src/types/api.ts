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
 * Faculty role types with specific scheduling constraints
 */
export enum FacultyRole {
  /** Program Director: 0 clinic, avoid Tue call */
  PD = 'pd',
  /** Associate Program Director: 2/week, avoid Tue call */
  APD = 'apd',
  /** Officer in Charge: 2/week */
  OIC = 'oic',
  /** Department Chief: 1/week, prefers Wed call */
  DEPT_CHIEF = 'dept_chief',
  /** Sports Medicine: 0 regular clinic, 4 SM clinic/week */
  SPORTS_MED = 'sports_med',
  /** Core Faculty: max 4/week */
  CORE = 'core',
  /** Adjunct Faculty: not auto-scheduled, can be pre-loaded to FMIT */
  ADJUNCT = 'adjunct'
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
  pgyLevel: number | null;
  /** Whether the person is credentialed to perform procedures */
  performsProcedures: boolean;
  /** List of medical specialties */
  specialties: string[] | null;
  /** Primary duty assignment */
  primaryDuty: string | null;
  /** Faculty role (for faculty only) */
  facultyRole: FacultyRole | null;
  /** Timestamp when the record was created */
  createdAt: DateTimeString;
  /** Timestamp when the record was last updated */
  updatedAt: DateTimeString;
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
  pgyLevel?: number;
  /** Whether the person is credentialed to perform procedures */
  performsProcedures?: boolean;
  /** List of medical specialties */
  specialties?: string[];
  /** Primary duty assignment */
  primaryDuty?: string;
  /** Faculty role (for faculty only) */
  facultyRole?: FacultyRole;
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
  pgyLevel?: number;
  /** Whether the person is credentialed to perform procedures */
  performsProcedures?: boolean;
  /** List of medical specialties */
  specialties?: string[];
  /** Primary duty assignment */
  primaryDuty?: string;
  /** Faculty role (for faculty only) */
  facultyRole?: FacultyRole;
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
  timeOfDay: TimeOfDay;
  /** Sequential block number */
  blockNumber: number;
  /** Whether this block falls on a weekend */
  isWeekend: boolean;
  /** Whether this block falls on a holiday */
  isHoliday: boolean;
  /** Name of the holiday if applicable */
  holidayName: string | null;
}

/**
 * Data required to create a new scheduling block
 */
export interface BlockCreate {
  /** Date of the block */
  date: DateString;
  /** Time period (AM or PM) */
  timeOfDay: TimeOfDay;
  /** Sequential block number */
  blockNumber: number;
  /** Whether this block falls on a weekend */
  isWeekend?: boolean;
  /** Whether this block falls on a holiday */
  isHoliday?: boolean;
  /** Name of the holiday if applicable */
  holidayName?: string;
}

/**
 * Data that can be updated for an existing block
 */
export interface BlockUpdate {
  /** Date of the block */
  date?: DateString;
  /** Time period (AM or PM) */
  timeOfDay?: TimeOfDay;
  /** Sequential block number */
  blockNumber?: number;
  /** Whether this block falls on a weekend */
  isWeekend?: boolean;
  /** Whether this block falls on a holiday */
  isHoliday?: boolean;
  /** Name of the holiday if applicable */
  holidayName?: string;
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
  blockId: UUID;
  /** ID of the person assigned */
  personId: UUID;
  /** ID of the rotation template being used (if applicable) */
  rotationTemplateId: UUID | null;
  /** Role of the person in this assignment */
  role: AssignmentRole;
  /** Custom activity description overriding the rotation template */
  activityOverride: string | null;
  /** Additional notes about this assignment */
  notes: string | null;
  /** ID of the user who created this assignment */
  createdBy: UUID | null;
  /** Timestamp when the assignment was created */
  createdAt: DateTimeString;
  /** Timestamp when the assignment was last updated */
  updatedAt: DateTimeString;
}

/**
 * Data required to create a new assignment
 */
export interface AssignmentCreate {
  /** ID of the block this assignment belongs to */
  blockId: UUID;
  /** ID of the person to assign */
  personId: UUID;
  /** ID of the rotation template to use (optional) */
  rotationTemplateId?: UUID;
  /** Role of the person in this assignment */
  role: AssignmentRole;
  /** Custom activity description overriding the rotation template */
  activityOverride?: string;
  /** Additional notes about this assignment */
  notes?: string;
  /** ID of the user creating this assignment */
  createdBy?: UUID;
}

/**
 * Data that can be updated for an existing assignment
 */
export interface AssignmentUpdate {
  /** ID of the block this assignment belongs to */
  blockId?: UUID;
  /** ID of the person assigned */
  personId?: UUID;
  /** ID of the rotation template being used */
  rotationTemplateId?: UUID;
  /** Role of the person in this assignment */
  role?: AssignmentRole;
  /** Custom activity description overriding the rotation template */
  activityOverride?: string;
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
  personId: UUID;
  /** Start date of the absence */
  startDate: DateString;
  /** End date of the absence */
  endDate: DateString;
  /** Type of absence */
  absenceType: AbsenceType;
  /** Whether this absence counts toward away-from-program limit (28 days/year for residents) */
  isAwayFromProgram: boolean;
  /** Whether the absence is due to deployment orders (military) */
  deploymentOrders: boolean;
  /** Location of TDY (temporary duty) if applicable */
  tdyLocation: string | null;
  /** Replacement activity to be scheduled during absence */
  replacementActivity: string | null;
  /** Additional notes about the absence */
  notes: string | null;
  /** Timestamp when the absence was created */
  createdAt: DateTimeString;
}

/**
 * Data required to create a new absence record
 */
export interface AbsenceCreate {
  /** ID of the person who will be absent */
  personId: UUID;
  /** Start date of the absence */
  startDate: DateString;
  /** End date of the absence */
  endDate: DateString;
  /** Type of absence */
  absenceType: AbsenceType;
  /** Whether this counts toward away-from-program limit (default: true for residents, false for faculty) */
  isAwayFromProgram?: boolean;
  /** Whether the absence is due to deployment orders (military) */
  deploymentOrders?: boolean;
  /** Location of TDY (temporary duty) if applicable */
  tdyLocation?: string;
  /** Replacement activity to be scheduled during absence */
  replacementActivity?: string;
  /** Additional notes about the absence */
  notes?: string;
}

/**
 * Data that can be updated for an existing absence
 */
export interface AbsenceUpdate {
  /** Start date of the absence */
  startDate?: DateString;
  /** End date of the absence */
  endDate?: DateString;
  /** Type of absence */
  absenceType?: AbsenceType;
  /** Whether this counts toward away-from-program limit */
  isAwayFromProgram?: boolean;
  /** Whether the absence is due to deployment orders (military) */
  deploymentOrders?: boolean;
  /** Location of TDY (temporary duty) if applicable */
  tdyLocation?: string;
  /** Replacement activity to be scheduled during absence */
  replacementActivity?: string;
  /** Additional notes about the absence */
  notes?: string;
}

// ============================================================================
// Away-From-Program Tracking Types
// ============================================================================

/**
 * Threshold status for away-from-program tracking
 */
export type ThresholdStatus = 'ok' | 'warning' | 'critical' | 'exceeded';

/**
 * Detail of an absence contributing to away-from-program count
 */
export interface AwayAbsenceDetail {
  id: string;
  startDate: string;
  endDate: string;
  absenceType: string;
  /** Days counted toward away-from-program */
  days: number;
}

/**
 * Summary of a resident's away-from-program status
 *
 * Residents who exceed 28 days away from program per academic year
 * must extend their training.
 */
export interface AwayFromProgramSummary {
  personId: string;
  /** Academic year (e.g., '2025-2026') */
  academicYear: string;
  /** Total days away from program this year */
  daysUsed: number;
  /** Days remaining before limit (min 0) */
  daysRemaining: number;
  /** Current status: ok, warning (21+), critical (28), exceeded */
  thresholdStatus: ThresholdStatus;
  /** Maximum allowed days per year */
  maxDays: number;
  /** Warning threshold (75%) */
  warningDays: number;
  /** Absences contributing to count */
  absences: AwayAbsenceDetail[];
}

/**
 * Response for threshold check (before creating new absence)
 */
export interface AwayFromProgramCheck {
  /** Current days used */
  currentDays: number;
  /** Days if new absence is added */
  projectedDays: number;
  thresholdStatus: ThresholdStatus;
  daysRemaining: number;
  maxDays: number;
  warningDays: number;
}

/**
 * Away-from-program status for all residents (compliance dashboard)
 */
export interface AllResidentsAwayStatus {
  academicYear: string;
  residents: AwayFromProgramSummary[];
  summary: {
    totalResidents: number;
    byStatus: Record<ThresholdStatus, number>;
  };
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
  activityType: string;
  /** Short abbreviation for display in schedules */
  abbreviation: string | null;
  /** User-facing abbreviation code for schedule grid (preferred over abbreviation) */
  displayAbbreviation: string | null;
  /** Tailwind color class for text */
  fontColor: string | null;
  /** Tailwind color class for background */
  backgroundColor: string | null;
  /** Physical location of the clinic/rotation */
  clinicLocation: string | null;
  /** Maximum number of residents that can be assigned simultaneously */
  maxResidents: number | null;
  /** Required specialty for this rotation (if any) */
  requiresSpecialty: string | null;
  /** Whether the rotation requires procedure credentials */
  requiresProcedureCredential: boolean;
  /** Whether faculty supervision is required */
  supervisionRequired: boolean;
  /** Maximum ratio of residents to supervisors (e.g., 3 means 3:1) */
  maxSupervisionRatio: number;
  /** Timestamp when the template was created */
  createdAt: DateTimeString;
}

/**
 * Data required to create a new rotation template
 */
export interface RotationTemplateCreate {
  /** Full name of the rotation */
  name: string;
  /** Type/category of the activity */
  activityType: string;
  /** Short abbreviation for display in schedules */
  abbreviation?: string;
  /** User-facing abbreviation code for schedule grid (preferred over abbreviation) */
  displayAbbreviation?: string;
  /** Tailwind color class for text */
  fontColor?: string;
  /** Tailwind color class for background */
  backgroundColor?: string;
  /** Physical location of the clinic/rotation */
  clinicLocation?: string;
  /** Maximum number of residents that can be assigned simultaneously */
  maxResidents?: number;
  /** Required specialty for this rotation (if any) */
  requiresSpecialty?: string;
  /** Whether the rotation requires procedure credentials */
  requiresProcedureCredential?: boolean;
  /** Whether faculty supervision is required */
  supervisionRequired?: boolean;
  /** Maximum ratio of residents to supervisors (e.g., 3 means 3:1) */
  maxSupervisionRatio?: number;
}

/**
 * Data that can be updated for an existing rotation template
 */
export interface RotationTemplateUpdate {
  /** Full name of the rotation */
  name?: string;
  /** Type/category of the activity */
  activityType?: string;
  /** Short abbreviation for display in schedules */
  abbreviation?: string;
  /** User-facing abbreviation code for schedule grid (preferred over abbreviation) */
  displayAbbreviation?: string;
  /** Tailwind color class for text */
  fontColor?: string;
  /** Tailwind color class for background */
  backgroundColor?: string;
  /** Physical location of the clinic/rotation */
  clinicLocation?: string;
  /** Maximum number of residents that can be assigned simultaneously */
  maxResidents?: number;
  /** Required specialty for this rotation (if any) */
  requiresSpecialty?: string;
  /** Whether the rotation requires procedure credentials */
  requiresProcedureCredential?: boolean;
  /** Whether faculty supervision is required */
  supervisionRequired?: boolean;
  /** Maximum ratio of residents to supervisors (e.g., 3 means 3:1) */
  maxSupervisionRatio?: number;
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
  startDate: DateString;
  /** End date of the scheduling period */
  endDate: DateString;
  /** Algorithm used for schedule generation */
  algorithm: SchedulingAlgorithm;
  /** Status of the schedule generation */
  status: ScheduleStatus;
  /** Number of blocks successfully assigned */
  totalBlocksAssigned: number | null;
  /** Number of ACGME violations detected */
  acgmeViolations: number;
  /** Runtime of the algorithm in seconds */
  runtimeSeconds: number | null;
  /** Configuration parameters used for this run */
  configJson: ScheduleConfig | null;
  /** Timestamp when the run was created */
  createdAt: DateTimeString;
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
  personId: UUID | null;
  /** Name of the person involved in the violation (if applicable) */
  personName: string | null;
  /** ID of the block where the violation occurred (if applicable) */
  blockId: UUID | null;
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
  currentValue?: number | string;
  /** Maximum allowed value */
  maxAllowed?: number | string;
  /** Minimum required value */
  minRequired?: number | string;
  /** Date range affected by the violation */
  dateRange?: {
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
  totalViolations: number;
  /** List of all violations found */
  violations: Violation[];
  /** Percentage of blocks with assignments (0-1) */
  coverageRate: number;
  /** Additional statistical information about the schedule */
  statistics: ValidationStatistics | null;
}

/**
 * Statistical information about schedule validation
 */
export interface ValidationStatistics {
  /** Total number of blocks in the schedule */
  totalBlocks?: number;
  /** Number of blocks with assignments */
  assignedBlocks?: number;
  /** Number of residents in the schedule */
  totalResidents?: number;
  /** Average assignments per resident */
  avgAssignmentsPerResident?: number;
  /** Violations grouped by severity */
  violationsBySeverity?: {
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
  totalBlocks: number | null;
  /** Total number of residents being scheduled */
  totalResidents: number | null;
  /** Percentage of blocks successfully assigned (0-1) */
  coverageRate: number | null;
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
  maxConsecutiveDays?: number;
  /** Minimum hours of rest between shifts */
  minRestHours?: number;
  /** Whether to enforce strict ACGME compliance */
  strictAcgmeCompliance?: boolean;
  /** Weight for coverage optimization (0-1) */
  coverageWeight?: number;
  /** Weight for fairness optimization (0-1) */
  fairnessWeight?: number;
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
  startDate: DateString;
  /** End date of the scheduling period */
  endDate: DateString;
  /** Filter to include only specific PGY levels */
  pgyLevels?: number[];
  /** Filter to include only specific rotation templates */
  rotationTemplateIds?: UUID[];
  /** Scheduling algorithm to use */
  algorithm: SchedulingAlgorithm;
  /** Maximum time allowed for schedule generation (in seconds) */
  timeoutSeconds?: number;
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
  totalBlocksAssigned: number;
  /** Total number of blocks in the period */
  totalBlocks: number;
  /** Validation results for the generated schedule */
  validation: ValidationResult;
  /** ID of the schedule run record */
  runId: UUID | null;
  /** Statistics from the solver */
  solverStats: SolverStatistics | null;
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
  pageSize: number;
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
  errorCode?: string;
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
