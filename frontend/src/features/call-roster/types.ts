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
  pgyLevel?: number;
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
  rotationName?: string;
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
  blockId: string;
  personId: string;
  rotationTemplateId: string | null;
  role: string;
  activityOverride: string | null;
  notes: string | null;
  createdBy: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface RawAssignmentsResponse {
  items: RawAssignment[];
  total: number;
  page?: number;
  pageSize?: number;
}

/**
 * Raw block from API
 */
export interface RawBlock {
  id: string;
  date: string;
  timeOfDay: 'AM' | 'PM';
  blockNumber: number;
  isWeekend: boolean;
  isHoliday: boolean;
  holidayName: string | null;
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
  pgyLevel: number | null;
  performsProcedures: boolean;
  specialties: string[] | null;
  primaryDuty: string | null;
  facultyRole: string | null;
  createdAt: string;
  updatedAt: string;
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
  activityType: string;
  abbreviation: string | null;
  displayAbbreviation: string | null;
  fontColor: string | null;
  backgroundColor: string | null;
  clinicLocation: string | null;
  maxResidents: number | null;
  requiresSpecialty: string | null;
  requiresProcedureCredential: boolean;
  supervisionRequired: boolean;
  maxSupervisionRatio: number;
  createdAt: string;
}

export interface RawRotationTemplatesResponse {
  items: RawRotationTemplate[];
  total: number;
}

// ============================================================================
// Filter and View Types
// ============================================================================

export interface CallRosterFilters {
  startDate: string;
  endDate: string;
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
  return template?.activityType === 'on_call';
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
