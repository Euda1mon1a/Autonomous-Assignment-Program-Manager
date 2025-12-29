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
    pgy_level?: number;
    role_type?: 'resident' | 'faculty' | 'fellow';
  };
  role: string;
  activity: string;
  assignment_id?: string;
  rotation_name?: string;
}

// ============================================================================
// Location Manifest
// ============================================================================

export interface LocationManifest {
  clinic_location: string;
  time_slots: {
    AM?: PersonAssignment[];
    PM?: PersonAssignment[];
  };
  staffing_summary: {
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
  generated_at: string;
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
  role_type?: 'resident' | 'faculty' | 'fellow' | 'all';
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
