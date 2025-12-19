/**
 * Mock data for resilience hub tests
 * Based on backend resilience API schemas
 */

export const resilienceMockFactories = {
  healthCheck: (overrides = {}) => ({
    timestamp: '2024-12-19T10:00:00Z',
    overall_status: 'green',
    utilization: {
      utilization_rate: 0.75,
      level: 'optimal',
      buffer_remaining: 0.25,
      wait_time_multiplier: 1.2,
      safe_capacity: 100,
      current_demand: 75,
      theoretical_capacity: 120,
    },
    defense_level: 'PREVENTION',
    redundancy_status: [
      {
        service: 'Inpatient Coverage',
        status: 'N+2',
        available: 8,
        minimum_required: 6,
        buffer: 2,
      },
      {
        service: 'Outpatient Clinic',
        status: 'N+1',
        available: 5,
        minimum_required: 4,
        buffer: 1,
      },
    ],
    load_shedding_level: 'NORMAL',
    active_fallbacks: 0,
    crisis_mode: false,
    n1_pass: true,
    n2_pass: true,
    phase_transition_risk: 0.1,
    immediate_actions: [],
    watch_items: ['Monitor utilization trends'],
    ...overrides,
  }),

  healthCheckWarning: (overrides = {}) => ({
    timestamp: '2024-12-19T10:00:00Z',
    overall_status: 'yellow',
    utilization: {
      utilization_rate: 0.85,
      level: 'high',
      buffer_remaining: 0.15,
      wait_time_multiplier: 1.8,
      safe_capacity: 100,
      current_demand: 85,
      theoretical_capacity: 120,
    },
    defense_level: 'CONTROL',
    redundancy_status: [
      {
        service: 'Inpatient Coverage',
        status: 'N+1',
        available: 7,
        minimum_required: 6,
        buffer: 1,
      },
    ],
    load_shedding_level: 'NORMAL',
    active_fallbacks: 0,
    crisis_mode: false,
    n1_pass: true,
    n2_pass: false,
    phase_transition_risk: 0.35,
    immediate_actions: ['Consider activating backup pool'],
    watch_items: ['Declining N-2 compliance', 'Rising utilization'],
    ...overrides,
  }),

  healthCheckCritical: (overrides = {}) => ({
    timestamp: '2024-12-19T10:00:00Z',
    overall_status: 'red',
    utilization: {
      utilization_rate: 0.92,
      level: 'critical',
      buffer_remaining: 0.08,
      wait_time_multiplier: 3.5,
      safe_capacity: 100,
      current_demand: 92,
      theoretical_capacity: 120,
    },
    defense_level: 'CONTAINMENT',
    redundancy_status: [
      {
        service: 'Inpatient Coverage',
        status: 'N+0',
        available: 6,
        minimum_required: 6,
        buffer: 0,
      },
    ],
    load_shedding_level: 'RED',
    active_fallbacks: 1,
    crisis_mode: true,
    n1_pass: false,
    n2_pass: false,
    phase_transition_risk: 0.75,
    immediate_actions: [
      'Activate fallback schedule',
      'Reduce non-essential services',
      'Notify leadership',
    ],
    watch_items: [
      'System at capacity',
      'No redundancy available',
      'Phase transition imminent',
    ],
    ...overrides,
  }),

  contingencyReport: (overrides = {}) => ({
    analyzed_at: '2024-12-19T10:00:00Z',
    period_start: '2024-12-20',
    period_end: '2025-01-20',
    n1_pass: true,
    n2_pass: true,
    phase_transition_risk: 0.15,
    n1_vulnerabilities: [
      {
        faculty_id: 'faculty-1',
        affected_blocks: 5,
        severity: 'medium',
      },
      {
        faculty_id: 'faculty-2',
        affected_blocks: 3,
        severity: 'low',
      },
    ],
    n2_fatal_pairs: [
      {
        faculty1_id: 'faculty-1',
        faculty2_id: 'faculty-3',
      },
    ],
    most_critical_faculty: [
      {
        faculty_id: 'faculty-1',
        faculty_name: 'Dr. Smith',
        centrality_score: 0.85,
        services_covered: ['Inpatient', 'Procedures', 'Emergency'],
        unique_coverage_slots: 12,
        replacement_difficulty: 'high',
        risk_level: 'critical',
      },
      {
        faculty_id: 'faculty-2',
        faculty_name: 'Dr. Johnson',
        centrality_score: 0.72,
        services_covered: ['Outpatient', 'Clinic'],
        unique_coverage_slots: 8,
        replacement_difficulty: 'medium',
        risk_level: 'high',
      },
    ],
    recommended_actions: [
      'Cross-train faculty on critical services',
      'Build backup pool for high-risk slots',
    ],
    ...overrides,
  }),

  fallbackList: (overrides = {}) => ({
    fallbacks: [
      {
        scenario: 'SINGLE_FACULTY_LOSS',
        description: 'Coverage for loss of any single faculty member',
        is_active: false,
        is_precomputed: true,
        assignments_count: 145,
        coverage_rate: 0.98,
        services_reduced: [],
        assumptions: ['All other faculty available', 'Normal operational tempo'],
        activation_count: 3,
      },
      {
        scenario: 'DOUBLE_FACULTY_LOSS',
        description: 'Coverage for simultaneous loss of two faculty members',
        is_active: false,
        is_precomputed: true,
        assignments_count: 132,
        coverage_rate: 0.92,
        services_reduced: ['Research time', 'Administrative duties'],
        assumptions: ['Remaining faculty willing to work extra', 'Overtime approved'],
        activation_count: 1,
      },
      {
        scenario: 'PANDEMIC_ESSENTIAL',
        description: 'Essential services only during pandemic conditions',
        is_active: false,
        is_precomputed: true,
        assignments_count: 95,
        coverage_rate: 0.75,
        services_reduced: ['Outpatient clinic', 'Elective procedures', 'Education'],
        assumptions: ['50% faculty available', 'Patient volume reduced'],
        activation_count: 0,
      },
    ],
    active_count: 0,
    ...overrides,
  }),

  loadSheddingStatus: (overrides = {}) => ({
    level: 'NORMAL',
    activities_suspended: [],
    activities_protected: [
      'Patient safety coverage',
      'Emergency response',
      'Critical procedures',
    ],
    capacity_available: 100,
    capacity_demand: 75,
    ...overrides,
  }),

  eventHistory: (overrides = {}) => ({
    items: [
      {
        id: 'event-1',
        timestamp: '2024-12-18T14:30:00Z',
        event_type: 'HEALTH_CHECK',
        severity: 'info',
        reason: 'Scheduled health check',
        triggered_by: 'system',
      },
      {
        id: 'event-2',
        timestamp: '2024-12-17T09:15:00Z',
        event_type: 'LOAD_SHEDDING_ACTIVATED',
        severity: 'warning',
        reason: 'Utilization exceeded threshold',
        triggered_by: 'user:admin-1',
      },
    ],
    total: 2,
    page: 1,
    page_size: 50,
    ...overrides,
  }),
};

export const resilienceMockResponses = {
  healthCheckGreen: resilienceMockFactories.healthCheck(),
  healthCheckYellow: resilienceMockFactories.healthCheckWarning(),
  healthCheckRed: resilienceMockFactories.healthCheckCritical(),
  contingencyAnalysis: resilienceMockFactories.contingencyReport(),
  fallbacks: resilienceMockFactories.fallbackList(),
  loadShedding: resilienceMockFactories.loadSheddingStatus(),
  eventHistory: resilienceMockFactories.eventHistory(),
};
