/**
 * Proxy Coverage Types
 *
 * Type definitions for the Proxy Coverage Dashboard showing
 * "who is covering for whom" across the scheduling system.
 */

// ============================================================================
// Person Reference
// ============================================================================

export interface PersonRef {
  id: string;
  name: string;
  pgyLevel: number | null;
  roleType: 'resident' | 'faculty' | 'fellow' | null;
}

// ============================================================================
// Coverage Relationship Types
// ============================================================================

/**
 * Type of coverage relationship
 */
export type CoverageType =
  | 'remote_surrogate'  // Covering for someone at remote location
  | 'swap_absorb'       // Absorbed shift from another person (one-way swap)
  | 'swap_exchange'     // Swapped shifts with another person
  | 'backup_call'       // Serving as backup call coverage
  | 'absence_coverage'  // Covering for absent colleague
  | 'temporary_proxy';  // General temporary proxy assignment

/**
 * Status of a coverage relationship
 */
export type CoverageStatus =
  | 'active'      // Currently in effect
  | 'scheduled'   // Will become active in the future
  | 'completed'   // Coverage period has ended
  | 'cancelled';  // Was cancelled before completion

// ============================================================================
// Coverage Relationship
// ============================================================================

/**
 * Represents a single coverage relationship between two people
 */
export interface CoverageRelationship {
  /** Unique identifier for this coverage relationship */
  id: string;

  /** The person providing coverage */
  coveringPerson: PersonRef;

  /** The person being covered for */
  coveredPerson: PersonRef;

  /** Type of coverage */
  coverageType: CoverageType;

  /** Current status */
  status: CoverageStatus;

  /** Start date of coverage (ISO string) */
  startDate: string;

  /** End date of coverage (ISO string), null if ongoing */
  endDate: string | null;

  /** Location context (e.g., "Hilo", "Main Clinic") */
  location: string | null;

  /** Additional context about the coverage */
  reason: string | null;

  /** Reference to related swap record if applicable */
  swapId: string | null;
}

// ============================================================================
// Coverage Summary
// ============================================================================

/**
 * Summary statistics for a person's coverage relationships
 */
export interface PersonCoverageSummary {
  person: PersonRef;

  /** Coverage this person is providing for others */
  providing: CoverageRelationship[];

  /** Coverage others are providing for this person */
  receiving: CoverageRelationship[];
}

// ============================================================================
// Coverage Dashboard Response
// ============================================================================

/**
 * Response from the proxy coverage API endpoint
 */
export interface ProxyCoverageResponse {
  /** Date for which coverage is shown */
  date: string;

  /** All active coverage relationships for the date */
  activeCoverage: CoverageRelationship[];

  /** Upcoming scheduled coverage (next 7 days) */
  upcomingCoverage: CoverageRelationship[];

  /** Summary by person */
  byCoverer: PersonCoverageSummary[];

  /** Coverage statistics */
  stats: CoverageStats;

  /** When this data was generated */
  generatedAt: string;
}

/**
 * Aggregated coverage statistics
 */
export interface CoverageStats {
  /** Total active coverage relationships */
  totalActive: number;

  /** Total scheduled for upcoming period */
  totalScheduled: number;

  /** Breakdown by coverage type */
  byType: Record<CoverageType, number>;

  /** People currently providing most coverage */
  topCoverers: Array<{
    person: PersonRef;
    count: number;
  }>;

  /** People currently being covered most */
  mostCovered: Array<{
    person: PersonRef;
    count: number;
  }>;
}

// ============================================================================
// Filter Options
// ============================================================================

export interface ProxyCoverageFilters {
  /** Filter by coverage type */
  coverageType?: CoverageType | 'all';

  /** Filter by status */
  status?: CoverageStatus | 'all';

  /** Filter by person (covering or covered) */
  personId?: string;

  /** Filter by date range */
  startDate?: string;
  endDate?: string;
}
