/**
 * Mock data for resilience hub tests
 * Based on backend resilience API schemas
 */

export const resilienceMockFactories = {
  healthCheck: (overrides = {}) => ({
    timestamp: '2024-12-19T10:00:00Z',
    overallStatus: 'green',
    utilization: {
      utilizationRate: 0.75,
      level: 'optimal',
      bufferRemaining: 0.25,
      waitTimeMultiplier: 1.2,
      safeCapacity: 100,
      currentDemand: 75,
      theoreticalCapacity: 120,
    },
    defenseLevel: 'PREVENTION',
    redundancyStatus: [
      {
        service: 'Inpatient Coverage',
        status: 'N+2',
        available: 8,
        minimumRequired: 6,
        buffer: 2,
      },
      {
        service: 'Outpatient Clinic',
        status: 'N+1',
        available: 5,
        minimumRequired: 4,
        buffer: 1,
      },
    ],
    loadSheddingLevel: 'NORMAL',
    activeFallbacks: 0,
    crisisMode: false,
    n1Pass: true,
    n2Pass: true,
    phaseTransitionRisk: 0.1,
    immediateActions: [],
    watchItems: ['Monitor utilization trends'],
    ...overrides,
  }),

  healthCheckWarning: (overrides = {}) => ({
    timestamp: '2024-12-19T10:00:00Z',
    overallStatus: 'yellow',
    utilization: {
      utilizationRate: 0.85,
      level: 'high',
      bufferRemaining: 0.15,
      waitTimeMultiplier: 1.8,
      safeCapacity: 100,
      currentDemand: 85,
      theoreticalCapacity: 120,
    },
    defenseLevel: 'CONTROL',
    redundancyStatus: [
      {
        service: 'Inpatient Coverage',
        status: 'N+1',
        available: 7,
        minimumRequired: 6,
        buffer: 1,
      },
    ],
    loadSheddingLevel: 'NORMAL',
    activeFallbacks: 0,
    crisisMode: false,
    n1Pass: true,
    n2Pass: false,
    phaseTransitionRisk: 0.35,
    immediateActions: ['Consider activating backup pool'],
    watchItems: ['Declining N-2 compliance', 'Rising utilization'],
    ...overrides,
  }),

  healthCheckCritical: (overrides = {}) => ({
    timestamp: '2024-12-19T10:00:00Z',
    overallStatus: 'red',
    utilization: {
      utilizationRate: 0.92,
      level: 'critical',
      bufferRemaining: 0.08,
      waitTimeMultiplier: 3.5,
      safeCapacity: 100,
      currentDemand: 92,
      theoreticalCapacity: 120,
    },
    defenseLevel: 'CONTAINMENT',
    redundancyStatus: [
      {
        service: 'Inpatient Coverage',
        status: 'N+0',
        available: 6,
        minimumRequired: 6,
        buffer: 0,
      },
    ],
    loadSheddingLevel: 'RED',
    activeFallbacks: 1,
    crisisMode: true,
    n1Pass: false,
    n2Pass: false,
    phaseTransitionRisk: 0.75,
    immediateActions: [
      'Activate fallback schedule',
      'Reduce non-essential services',
      'Notify leadership',
    ],
    watchItems: [
      'System at capacity',
      'No redundancy available',
      'Phase transition imminent',
    ],
    ...overrides,
  }),

  contingencyReport: (overrides = {}) => ({
    analyzedAt: '2024-12-19T10:00:00Z',
    periodStart: '2024-12-20',
    periodEnd: '2025-01-20',
    n1Pass: true,
    n2Pass: true,
    phaseTransitionRisk: 0.15,
    n1Vulnerabilities: [
      {
        facultyId: 'faculty-1',
        affectedBlocks: 5,
        severity: 'medium',
      },
      {
        facultyId: 'faculty-2',
        affectedBlocks: 3,
        severity: 'low',
      },
    ],
    n2FatalPairs: [
      {
        faculty1Id: 'faculty-1',
        faculty2Id: 'faculty-3',
      },
    ],
    mostCriticalFaculty: [
      {
        facultyId: 'faculty-1',
        facultyName: 'Dr. Smith',
        centralityScore: 0.85,
        servicesCovered: ['Inpatient', 'Procedures', 'Emergency'],
        uniqueCoverageSlots: 12,
        replacementDifficulty: 'high',
        riskLevel: 'critical',
      },
      {
        facultyId: 'faculty-2',
        facultyName: 'Dr. Johnson',
        centralityScore: 0.72,
        servicesCovered: ['Outpatient', 'Clinic'],
        uniqueCoverageSlots: 8,
        replacementDifficulty: 'medium',
        riskLevel: 'high',
      },
    ],
    recommendedActions: [
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
        isActive: false,
        isPrecomputed: true,
        assignmentsCount: 145,
        coverageRate: 0.98,
        servicesReduced: [],
        assumptions: ['All other faculty available', 'Normal operational tempo'],
        activationCount: 3,
      },
      {
        scenario: 'DOUBLE_FACULTY_LOSS',
        description: 'Coverage for simultaneous loss of two faculty members',
        isActive: false,
        isPrecomputed: true,
        assignmentsCount: 132,
        coverageRate: 0.92,
        servicesReduced: ['Research time', 'Administrative duties'],
        assumptions: ['Remaining faculty willing to work extra', 'Overtime approved'],
        activationCount: 1,
      },
      {
        scenario: 'PANDEMIC_ESSENTIAL',
        description: 'Essential services only during pandemic conditions',
        isActive: false,
        isPrecomputed: true,
        assignmentsCount: 95,
        coverageRate: 0.75,
        servicesReduced: ['Outpatient clinic', 'Elective procedures', 'Education'],
        assumptions: ['50% faculty available', 'Patient volume reduced'],
        activationCount: 0,
      },
    ],
    activeCount: 0,
    ...overrides,
  }),

  loadSheddingStatus: (overrides = {}) => ({
    level: 'NORMAL',
    activitiesSuspended: [],
    activitiesProtected: [
      'Patient safety coverage',
      'Emergency response',
      'Critical procedures',
    ],
    capacityAvailable: 100,
    capacityDemand: 75,
    ...overrides,
  }),

  eventHistory: (overrides = {}) => ({
    items: [
      {
        id: 'event-1',
        timestamp: '2024-12-18T14:30:00Z',
        eventType: 'HEALTH_CHECK',
        severity: 'info',
        reason: 'Scheduled health check',
        triggeredBy: 'system',
      },
      {
        id: 'event-2',
        timestamp: '2024-12-17T09:15:00Z',
        eventType: 'LOAD_SHEDDING_ACTIVATED',
        severity: 'warning',
        reason: 'Utilization exceeded threshold',
        triggeredBy: 'user:admin-1',
      },
    ],
    total: 2,
    page: 1,
    pageSize: 50,
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
