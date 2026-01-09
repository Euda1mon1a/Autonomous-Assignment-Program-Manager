/**
 * Faculty Call Administration Types
 *
 * Types for the faculty call admin interface including call assignments,
 * bulk operations, filtering, and PCAT (Post-Call Availability Tracking) status.
 */

// ============================================================================
// Core Call Assignment Types
// ============================================================================

/**
 * Types of faculty call assignments
 */
export type CallType =
  | 'sunday'
  | 'weekday'
  | 'holiday'
  | 'backup';

/**
 * Post-call availability status
 */
export type PostCallStatus =
  | 'available'
  | 'post_call'
  | 'pcat_applied'
  | 'override';

/**
 * Days of the week
 */
export type DayOfWeek =
  | 'Sunday'
  | 'Monday'
  | 'Tuesday'
  | 'Wednesday'
  | 'Thursday'
  | 'Friday'
  | 'Saturday';

/**
 * Represents a faculty call assignment
 */
export interface CallAssignment {
  /** Unique identifier */
  id: string;
  /** Date of the call assignment */
  date: string;
  /** Day of the week */
  dayOfWeek: DayOfWeek;
  /** ID of the assigned person */
  personId: string;
  /** Name of the assigned person */
  personName: string;
  /** Type of call */
  callType: CallType;
  /** Post-call status */
  postCallStatus: PostCallStatus;
  /** Additional notes */
  notes: string | null;
  /** When this assignment was created */
  createdAt: string;
  /** When this assignment was last updated */
  updatedAt: string;
}

/**
 * Response from call assignments list endpoint
 */
export interface CallAssignmentListResponse {
  items: CallAssignment[];
  total: number;
}

// ============================================================================
// Filter & Sort Types
// ============================================================================

export type CallSortField = 'date' | 'person_name' | 'call_type';
export type SortDirection = 'asc' | 'desc';

export interface CallFilters {
  startDate: string;
  endDate: string;
  personId: string;
  callType: CallType | '';
  search: string;
}

export interface CallSort {
  field: CallSortField;
  direction: SortDirection;
}

// ============================================================================
// Bulk Action Types
// ============================================================================

export type CallBulkActionType =
  | 'delete'
  | 'reassign'
  | 'apply_pcat'
  | 'clear_pcat';

export interface CallBulkActionConfig {
  type: CallBulkActionType;
  label: string;
  description: string;
  isDangerous: boolean;
  requiresConfirmation: boolean;
}

export const CALL_BULK_ACTIONS: CallBulkActionConfig[] = [
  {
    type: 'reassign',
    label: 'Reassign',
    description: 'Reassign selected call assignments to a different person',
    isDangerous: false,
    requiresConfirmation: true,
  },
  {
    type: 'apply_pcat',
    label: 'Apply PCAT Rules',
    description: 'Apply post-call availability tracking rules',
    isDangerous: false,
    requiresConfirmation: true,
  },
  {
    type: 'clear_pcat',
    label: 'Clear PCAT Status',
    description: 'Clear post-call status for selected assignments',
    isDangerous: false,
    requiresConfirmation: true,
  },
  {
    type: 'delete',
    label: 'Delete',
    description: 'Permanently delete selected call assignments',
    isDangerous: true,
    requiresConfirmation: true,
  },
];

// ============================================================================
// API Request Types
// ============================================================================

export interface BulkCallDeleteRequest {
  assignmentIds: string[];
}

export interface BulkCallReassignRequest {
  assignmentIds: string[];
  newPersonId: string;
}

export interface BulkCallPCATRequest {
  assignmentIds: string[];
  apply: boolean;
}

// ============================================================================
// State Types
// ============================================================================

export interface FacultyCallAdminState {
  selectedIds: string[];
  filters: CallFilters;
  sort: CallSort;
  isLoading: boolean;
}

// ============================================================================
// Display Configuration Types
// ============================================================================

export interface CallTypeConfig {
  type: CallType;
  label: string;
  color: string;
  bgColor: string;
}

export const CALL_TYPE_CONFIGS: CallTypeConfig[] = [
  { type: 'sunday', label: 'Sunday Call', color: 'text-blue-400', bgColor: 'bg-blue-500/20' },
  { type: 'weekday', label: 'Weekday Call', color: 'text-emerald-400', bgColor: 'bg-emerald-500/20' },
  { type: 'holiday', label: 'Holiday Call', color: 'text-amber-400', bgColor: 'bg-amber-500/20' },
  { type: 'backup', label: 'Backup Call', color: 'text-purple-400', bgColor: 'bg-purple-500/20' },
];

export function getCallTypeConfig(type: CallType): CallTypeConfig {
  return CALL_TYPE_CONFIGS.find((c) => c.type === type) || CALL_TYPE_CONFIGS[0];
}

export interface PostCallStatusConfig {
  status: PostCallStatus;
  label: string;
  color: string;
  bgColor: string;
}

export const POST_CALL_STATUS_CONFIGS: PostCallStatusConfig[] = [
  { status: 'available', label: 'Available', color: 'text-emerald-400', bgColor: 'bg-emerald-500/20' },
  { status: 'post_call', label: 'Post-Call', color: 'text-amber-400', bgColor: 'bg-amber-500/20' },
  { status: 'pcat_applied', label: 'PCAT Applied', color: 'text-blue-400', bgColor: 'bg-blue-500/20' },
  { status: 'override', label: 'Override', color: 'text-red-400', bgColor: 'bg-red-500/20' },
];

export function getPostCallStatusConfig(status: PostCallStatus): PostCallStatusConfig {
  return POST_CALL_STATUS_CONFIGS.find((c) => c.status === status) || POST_CALL_STATUS_CONFIGS[0];
}
