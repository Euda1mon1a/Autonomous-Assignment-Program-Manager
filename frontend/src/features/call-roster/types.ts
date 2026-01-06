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
// Raw API Response Types
// These match what the backend actually returns (IDs only, no nested objects)
// ============================================================================

/**
 * Raw assignment from API - contains only IDs, not nested objects.
 * The hooks perform client-side joins to enrich with person/block/template data.
 */
export interface RawAssignment {
  id: string;
  block_id: string;
  person_id: string;
  rotation_template_id: string | null;
  role: string;
  activity_override: string | null;
  notes: string | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface RawAssignmentsResponse {
  items: RawAssignment[];
  total: number;
  page?: number;
  page_size?: number;
}

/**
 * Raw block from API
 */
export interface RawBlock {
  id: string;
  date: string;
  time_of_day: 'AM' | 'PM';
  block_number: number;
  is_weekend: boolean;
  is_holiday: boolean;
  holiday_name: string | null;
}

export interface RawBlocksResponse {
  items: RawBlock[];
  total: number;
}

/**
 * Raw person from API
 */
export interface RawPerson {
  id: string;
  name: string;
  email: string | null;
  type: 'resident' | 'faculty';
  pgy_level: number | null;
  performs_procedures: boolean;
  specialties: string[] | null;
  primary_duty: string | null;
  faculty_role: string | null;
  created_at: string;
  updated_at: string;
}

export interface RawPeopleResponse {
  items: RawPerson[];
  total: number;
}

/**
 * Raw rotation template from API
 */
export interface RawRotationTemplate {
  id: string;
  name: string;
  activity_type: string;
  abbreviation: string | null;
  display_abbreviation: string | null;
  font_color: string | null;
  background_color: string | null;
  clinic_location: string | null;
  max_residents: number | null;
  requires_specialty: string | null;
  requires_procedure_credential: boolean;
  supervision_required: boolean;
  max_supervision_ratio: number;
  created_at: string;
}

export interface RawRotationTemplatesResponse {
  items: RawRotationTemplate[];
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
 * Get display name from person object.
 * Uses the 'name' field from RawPerson which contains the full name.
 */
export function getPersonName(person?: RawPerson | null): string {
  if (!person) return 'Unknown';
  return person.name;
}

/**
 * Check if an assignment is an on-call assignment by looking up the rotation template
 */
export function isOnCallTemplate(template?: RawRotationTemplate | null): boolean {
  return template?.activity_type === 'on_call';
}

/**
 * Determine shift type from rotation name or notes
 */
export function getShiftType(rotationName?: string | null, notes?: string | null): 'day' | 'night' | '24hr' {
  const text = `${rotationName || ''} ${notes || ''}`.toLowerCase();

  if (text.includes('night') || text.includes('overnight')) {
    return 'night';
  }
  if (text.includes('24') || text.includes('24hr') || text.includes('24-hour')) {
    return '24hr';
  }
  return 'day';
}
