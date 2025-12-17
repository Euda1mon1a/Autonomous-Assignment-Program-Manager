/**
 * Call Roster Types
 *
 * Type definitions for the Call Roster feature showing
 * who is on call and their contact information.
 */

// ============================================================================
// Person Types
// ============================================================================

export type RoleType = 'attending' | 'senior' | 'intern';

export interface OnCallPerson {
  id: string;
  name: string;
  pgy_level?: number;
  role: RoleType;
  phone?: string;
  pager?: string;
  email?: string;
}

// ============================================================================
// Call Assignment Types
// ============================================================================

export interface CallAssignment {
  id: string;
  date: string;
  shift: 'day' | 'night' | '24hr';
  person: OnCallPerson;
  rotation_name?: string;
  notes?: string;
}

export interface CallRosterEntry {
  date: string;
  assignments: CallAssignment[];
}

// ============================================================================
// API Response Types
// ============================================================================

export interface Assignment {
  id: string;
  block_id: string;
  person_id: string;
  role: string;
  rotation_template?: {
    id: string;
    name: string;
    activity_type: string;
    abbreviation?: string;
  };
  person?: {
    id: string;
    first_name: string;
    last_name: string;
    pgy_level?: number;
    email?: string;
    phone?: string;
    pager?: string;
  };
  block?: {
    id: string;
    start_date: string;
    end_date: string;
  };
  notes?: string;
}

export interface AssignmentsResponse {
  items: Assignment[];
  total: number;
}

// ============================================================================
// Filter and View Types
// ============================================================================

export interface CallRosterFilters {
  start_date: string;
  end_date: string;
  role?: RoleType;
}

export type ViewMode = 'calendar' | 'list';

export interface DateRange {
  start: string;
  end: string;
}

// ============================================================================
// Calendar Types
// ============================================================================

export interface CalendarDay {
  date: Date;
  dateString: string;
  isCurrentMonth: boolean;
  isToday: boolean;
  assignments: CallAssignment[];
}

export interface CalendarWeek {
  days: CalendarDay[];
}

// ============================================================================
// Constants
// ============================================================================

export const ROLE_COLORS: Record<RoleType, string> = {
  attending: 'bg-red-100 text-red-800 border-red-300',
  senior: 'bg-blue-100 text-blue-800 border-blue-300',
  intern: 'bg-green-100 text-green-800 border-green-300',
};

export const ROLE_LABELS: Record<RoleType, string> = {
  attending: 'Attending',
  senior: 'Senior',
  intern: 'Intern',
};

export const SHIFT_LABELS: Record<string, string> = {
  day: 'Day',
  night: 'Night',
  '24hr': '24 Hour',
};

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Determine role type from PGY level and assignment role
 */
export function getRoleType(pgyLevel?: number, assignmentRole?: string): RoleType {
  if (!pgyLevel) {
    return 'attending';
  }
  if (pgyLevel >= 3 || assignmentRole === 'supervising') {
    return 'senior';
  }
  return 'intern';
}

/**
 * Get display name from person object
 */
export function getPersonName(person?: { first_name: string; last_name: string }): string {
  if (!person) return 'Unknown';
  return `${person.first_name} ${person.last_name}`;
}

/**
 * Check if an assignment is an on-call assignment
 */
export function isOnCallAssignment(assignment: Assignment): boolean {
  return assignment.rotation_template?.activity_type === 'on_call';
}

/**
 * Determine shift type from rotation name or notes
 */
export function getShiftType(rotationName?: string, notes?: string): 'day' | 'night' | '24hr' {
  const text = `${rotationName || ''} ${notes || ''}`.toLowerCase();

  if (text.includes('night') || text.includes('overnight')) {
    return 'night';
  }
  if (text.includes('24') || text.includes('24hr') || text.includes('24-hour')) {
    return '24hr';
  }
  return 'day';
}
