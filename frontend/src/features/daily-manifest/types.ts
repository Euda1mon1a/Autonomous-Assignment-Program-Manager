/**
 * Daily Manifest Types
 *
 * Type definitions for the Daily Manifest feature showing
 * real-time location and assignment information.
 */

// ============================================================================
// Person Assignment
// ============================================================================

export interface PersonAssignment {
  person: {
    id: string;
    name: string;
    pgyLevel?: number;
    roleType?: 'resident' | 'faculty' | 'fellow';
  };
  role: string;
  activity: string;
  assignmentId?: string;
  rotationName?: string;
}

// ============================================================================
// Location Manifest
// ============================================================================

export interface LocationManifest {
  clinicLocation: string;
  timeSlots: {
    AM?: PersonAssignment[];
    PM?: PersonAssignment[];
  };
  staffingSummary: {
    total: number;
    residents: number;
    faculty: number;
    fellows?: number;
  };
  capacity?: {
    current: number;
    maximum: number;
  };
}

// ============================================================================
// Daily Manifest Data
// ============================================================================

export interface DailyManifestData {
  date: string;
  time_of_day: 'AM' | 'PM' | 'ALL' | null;
  locations: LocationManifest[];
  generatedAt: string;
  // Summary is computed client-side from locations, not returned by backend
  summary?: {
    total_locations: number;
    total_staff: number;
    total_residents: number;
    total_faculty: number;
  };
}

// ============================================================================
// Filter Options
// ============================================================================

export interface ManifestFilters {
  location?: string;
  roleType?: 'resident' | 'faculty' | 'fellow' | 'all';
  search?: string;
}

// ============================================================================
// Schedule Date Range
// ============================================================================

/**
 * Represents the date range where schedule data is available
 */
export interface ScheduleDateRange {
  /** Earliest date with schedule data (ISO format) */
  start_date: string | null;
  /** Latest date with schedule data (ISO format) */
  end_date: string | null;
  /** Whether any schedule data exists */
  has_data: boolean;
}

// ============================================================================
// V2 Types - Redesigned for Nursing/Front Desk
// ============================================================================

/**
 * Person summary for display
 */
export interface PersonSummary {
  id: string;
  name: string;
  pgyLevel: number | null;
}

/**
 * FMIT (Family Medicine Inpatient Team) - NOT in clinic
 */
export interface FMITSection {
  attending: PersonSummary | null;
  residents: PersonSummary[];
}

/**
 * Night call information
 */
export interface NightCallInfo {
  person: PersonSummary;
  callType: string;
}

/**
 * Remote location assignment (Hilo, Okinawa, Kapiolani)
 */
export interface RemoteAssignment {
  person: PersonSummary;
  location: string;
  surrogate: PersonSummary | null;
}

/**
 * Attending physician info at-a-glance
 */
export interface AttendingInfo {
  am: PersonSummary | null;
  pm: PersonSummary | null;
}

/**
 * Assignment summary for manifest
 */
export interface AssignmentSummary {
  person: PersonSummary;
  role: string;
  activity: string;
}

/**
 * Staff for a single half-day
 */
export interface HalfDayStaff {
  assignments: AssignmentSummary[];
  count: number;
}

/**
 * Location manifest with AM/PM columns
 */
export interface LocationManifestV2 {
  location: string;
  am: HalfDayStaff;
  pm: HalfDayStaff;
}

/**
 * Absence information for situational awareness
 */
export interface AbsenceInfo {
  person: PersonSummary;
  absenceType: string;  // vacation, sick, deployment, etc.
}

/**
 * Situational awareness - who is NOT in clinic
 */
export interface SituationalAwareness {
  fmitTeam: FMITSection;
  nightRotation: NightCallInfo[];
  remoteAssignments: RemoteAssignment[];
  absences: AbsenceInfo[];  // NEW: People with absences
}

/**
 * Assignment info for a half-day (without person info)
 */
export interface AssignmentInfoV2 {
  activity: string;      // Activity type (e.g., clinical, leave)
  abbreviation: string;  // Short code (e.g., CL, PR)
  role: string;          // Role (primary, supervising, backup)
}

/**
 * Person-centric clinic coverage (DayView style)
 */
export interface PersonClinicCoverage {
  person: PersonSummary;
  am: AssignmentInfoV2 | null;
  pm: AssignmentInfoV2 | null;
}

/**
 * V2 Daily Manifest Response
 */
export interface DailyManifestDataV2 {
  date: string;
  situationalAwareness: SituationalAwareness;
  attending: AttendingInfo;
  clinicCoverage: PersonClinicCoverage[];  // Changed from LocationManifestV2[]
  generatedAt: string;
}
