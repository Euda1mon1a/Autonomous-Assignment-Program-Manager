/**
 * Mock data factories for conflict resolution tests
 * Provides reusable mock data for conflict-related tests
 */

import type {
  Conflict,
  ConflictSeverity,
  ConflictType,
  ConflictStatus,
  ResolutionMethod,
  ResolutionSuggestion,
  ResolutionChange,
  ManualOverride,
  ConflictHistoryEntry,
  ConflictPattern,
  ConflictStatistics,
  ConflictFilters,
  AbsenceConflictDetails,
  SchedulingOverlapDetails,
  ACGMEViolationDetails,
  CapacityExceededDetails,
  BatchResolutionRequest,
  BatchResolutionResult,
} from '@/features/conflicts/types';

/**
 * Mock data factories
 */
export const conflictsMockFactories = {
  conflict: (overrides: Partial<Conflict> = {}): Conflict => ({
    id: 'conflict-1',
    type: 'absence_conflict' as ConflictType,
    severity: 'high' as ConflictSeverity,
    status: 'unresolved' as ConflictStatus,
    title: 'Assignment during absence',
    description: 'Dr. Smith is assigned while on vacation',
    affected_person_ids: ['person-1'],
    affected_assignment_ids: ['assignment-1'],
    affected_block_ids: ['block-1'],
    conflict_date: '2024-02-15',
    conflict_session: 'AM',
    detected_at: '2024-02-10T10:00:00Z',
    detected_by: 'system',
    details: {
      person_name: 'Dr. John Smith',
      person_id: 'person-1',
      absence_type: 'vacation',
      absence_start: '2024-02-14',
      absence_end: '2024-02-18',
      assignment_rotation: 'Inpatient Medicine',
    } as AbsenceConflictDetails,
    ...overrides,
  }),

  schedulingOverlapConflict: (overrides: Partial<Conflict> = {}): Conflict => ({
    id: 'conflict-2',
    type: 'scheduling_overlap',
    severity: 'critical',
    status: 'unresolved',
    title: 'Double-booked time slot',
    description: 'Dr. Doe is assigned to two rotations at the same time',
    affected_person_ids: ['person-2'],
    affected_assignment_ids: ['assignment-2', 'assignment-3'],
    affected_block_ids: ['block-2'],
    conflict_date: '2024-02-20',
    conflict_session: 'PM',
    detected_at: '2024-02-15T14:30:00Z',
    detected_by: 'system',
    details: {
      person_name: 'Dr. Jane Doe',
      person_id: 'person-2',
      first_assignment: {
        id: 'assignment-2',
        rotation_name: 'Clinic',
        location: 'Main Hospital',
      },
      second_assignment: {
        id: 'assignment-3',
        rotation_name: 'ER',
        location: 'Emergency Department',
      },
    } as SchedulingOverlapDetails,
    ...overrides,
  }),

  acgmeViolationConflict: (overrides: Partial<Conflict> = {}): Conflict => ({
    id: 'conflict-3',
    type: 'acgme_violation',
    severity: 'critical',
    status: 'unresolved',
    title: 'ACGME duty hour violation',
    description: 'Dr. Johnson exceeds 80-hour weekly limit',
    affected_person_ids: ['person-3'],
    affected_assignment_ids: ['assignment-4'],
    affected_block_ids: ['block-3'],
    conflict_date: '2024-02-22',
    detected_at: '2024-02-20T16:00:00Z',
    detected_by: 'validation',
    details: {
      person_name: 'Dr. Bob Johnson',
      person_id: 'person-3',
      violation_type: '80-hour weekly limit',
      current_value: 85,
      limit_value: 80,
      unit: 'hours',
      period_start: '2024-02-15',
      period_end: '2024-02-22',
    } as ACGMEViolationDetails,
    ...overrides,
  }),

  capacityExceededConflict: (overrides: Partial<Conflict> = {}): Conflict => ({
    id: 'conflict-4',
    type: 'capacity_exceeded',
    severity: 'medium',
    status: 'unresolved',
    title: 'Rotation capacity exceeded',
    description: 'Inpatient rotation has too many assigned residents',
    affected_person_ids: ['person-4', 'person-5', 'person-6'],
    affected_assignment_ids: ['assignment-5', 'assignment-6', 'assignment-7'],
    affected_block_ids: ['block-4'],
    conflict_date: '2024-02-25',
    detected_at: '2024-02-23T09:00:00Z',
    detected_by: 'system',
    details: {
      rotation_name: 'Inpatient Medicine',
      rotation_id: 'rotation-1',
      current_count: 5,
      max_capacity: 4,
      assigned_people: [
        { id: 'person-4', name: 'Dr. Alice Brown' },
        { id: 'person-5', name: 'Dr. Charlie Davis' },
        { id: 'person-6', name: 'Dr. Eve Wilson' },
      ],
    } as CapacityExceededDetails,
    ...overrides,
  }),

  resolutionChange: (overrides: Partial<ResolutionChange> = {}): ResolutionChange => ({
    type: 'reassign',
    entity_type: 'assignment',
    entity_id: 'assignment-1',
    description: 'Reassign Dr. Smith to different date',
    from_person_id: 'person-1',
    from_person_name: 'Dr. John Smith',
    to_person_id: 'person-2',
    to_person_name: 'Dr. Jane Doe',
    ...overrides,
  }),

  resolutionSuggestion: (overrides: Partial<ResolutionSuggestion> = {}): ResolutionSuggestion => ({
    id: 'suggestion-1',
    conflict_id: 'conflict-1',
    method: 'manual_reassign' as ResolutionMethod,
    title: 'Reassign to available resident',
    description: 'Reassign this rotation to Dr. Doe who is available',
    impact_score: 15,
    confidence: 85,
    changes: [conflictsMockFactories.resolutionChange()],
    side_effects: ['Dr. Doe will have 1 extra shift this month'],
    recommended: true,
    ...overrides,
  }),

  manualOverride: (overrides: Partial<ManualOverride> = {}): ManualOverride => ({
    conflict_id: 'conflict-1',
    override_type: 'temporary',
    reason: 'emergency_coverage',
    justification: 'Required for emergency coverage during unexpected absence',
    expires_at: '2024-03-01T00:00:00Z',
    is_acgme_related: false,
    supervisor_approval_required: true,
    supervisor_approved: false,
    ...overrides,
  }),

  conflictHistoryEntry: (overrides: Partial<ConflictHistoryEntry> = {}): ConflictHistoryEntry => ({
    id: 'history-1',
    conflict_id: 'conflict-1',
    action: 'detected',
    timestamp: '2024-02-10T10:00:00Z',
    user_id: 'system',
    user_name: 'System',
    changes: {},
    notes: 'Conflict automatically detected during validation',
    ...overrides,
  }),

  conflictPattern: (overrides: Partial<ConflictPattern> = {}): ConflictPattern => ({
    id: 'pattern-1',
    type: 'absence_conflict',
    frequency: 5,
    first_occurrence: '2024-01-15T00:00:00Z',
    last_occurrence: '2024-02-10T00:00:00Z',
    affected_people: [
      { id: 'person-1', name: 'Dr. John Smith', occurrence_count: 3 },
      { id: 'person-2', name: 'Dr. Jane Doe', occurrence_count: 2 },
    ],
    root_cause: 'Vacation periods not properly blocked in schedule',
    suggested_prevention: 'Implement automatic blocking of vacation periods during scheduling',
    ...overrides,
  }),

  conflictStatistics: (overrides: Partial<ConflictStatistics> = {}): ConflictStatistics => ({
    total_conflicts: 24,
    by_severity: {
      critical: 3,
      high: 8,
      medium: 10,
      low: 3,
    },
    by_type: {
      scheduling_overlap: 5,
      acgme_violation: 3,
      supervision_missing: 2,
      capacity_exceeded: 4,
      absence_conflict: 6,
      qualification_mismatch: 2,
      consecutive_duty: 1,
      rest_period: 1,
      coverage_gap: 0,
    },
    by_status: {
      unresolved: 12,
      pending_review: 5,
      resolved: 6,
      ignored: 1,
    },
    resolution_rate: 75.5,
    average_resolution_time_hours: 18.5,
    most_affected_people: [
      { id: 'person-1', name: 'Dr. John Smith', conflict_count: 5 },
      { id: 'person-2', name: 'Dr. Jane Doe', conflict_count: 4 },
      { id: 'person-3', name: 'Dr. Bob Johnson', conflict_count: 3 },
    ],
    trending_up: false,
    ...overrides,
  }),

  conflictFilters: (overrides: Partial<ConflictFilters> = {}): ConflictFilters => ({
    types: ['absence_conflict', 'scheduling_overlap'],
    severities: ['critical', 'high'],
    statuses: ['unresolved'],
    date_range: {
      start: '2024-02-01',
      end: '2024-02-28',
    },
    ...overrides,
  }),

  batchResolutionRequest: (
    overrides: Partial<BatchResolutionRequest> = {}
  ): BatchResolutionRequest => ({
    conflict_ids: ['conflict-1', 'conflict-2', 'conflict-3'],
    resolution_method: 'manual_reassign',
    notes: 'Batch resolution for similar conflicts',
    ...overrides,
  }),

  batchResolutionResult: (
    overrides: Partial<BatchResolutionResult> = {}
  ): BatchResolutionResult => ({
    total: 3,
    successful: 2,
    failed: 1,
    results: [
      {
        conflict_id: 'conflict-1',
        success: true,
        message: 'Successfully resolved',
        resolution: conflictsMockFactories.resolutionSuggestion(),
      },
      {
        conflict_id: 'conflict-2',
        success: true,
        message: 'Successfully resolved',
      },
      {
        conflict_id: 'conflict-3',
        success: false,
        message: 'Failed to resolve: No available alternatives',
      },
    ],
    ...overrides,
  }),
};

/**
 * Mock API responses
 */
export const conflictsMockResponses = {
  conflicts: {
    items: [
      conflictsMockFactories.conflict(),
      conflictsMockFactories.schedulingOverlapConflict(),
      conflictsMockFactories.acgmeViolationConflict(),
    ],
    total: 3,
  },

  statistics: conflictsMockFactories.conflictStatistics(),

  suggestions: [
    conflictsMockFactories.resolutionSuggestion(),
    conflictsMockFactories.resolutionSuggestion({
      id: 'suggestion-2',
      method: 'cancel_assignment',
      title: 'Cancel assignment',
      description: 'Cancel this assignment and leave slot empty',
      impact_score: 30,
      confidence: 70,
      recommended: false,
    }),
  ],

  history: [
    conflictsMockFactories.conflictHistoryEntry(),
    conflictsMockFactories.conflictHistoryEntry({
      id: 'history-2',
      action: 'updated',
      timestamp: '2024-02-11T11:00:00Z',
      user_id: 'user-1',
      user_name: 'Admin User',
      changes: {
        status: { from: 'unresolved', to: 'pending_review' },
      },
      notes: 'Marked for manual review',
    }),
    conflictsMockFactories.conflictHistoryEntry({
      id: 'history-3',
      action: 'resolved',
      timestamp: '2024-02-12T14:30:00Z',
      user_id: 'user-1',
      user_name: 'Admin User',
      changes: {
        status: { from: 'pending_review', to: 'resolved' },
      },
      notes: 'Reassigned to alternative resident',
    }),
  ],

  patterns: [
    conflictsMockFactories.conflictPattern(),
    conflictsMockFactories.conflictPattern({
      id: 'pattern-2',
      type: 'scheduling_overlap',
      frequency: 3,
      root_cause: 'Manual scheduling without validation',
      suggested_prevention: 'Enable real-time conflict detection during scheduling',
    }),
  ],

  batchResult: conflictsMockFactories.batchResolutionResult(),
};
