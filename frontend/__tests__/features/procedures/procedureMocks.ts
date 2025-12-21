/**
 * Mock data for procedure credentialing tests
 * Based on backend procedure and credential schemas
 */

/**
 * Procedure status values
 */
export type ProcedureStatus = 'active' | 'expired' | 'suspended' | 'pending';

/**
 * Competency level values
 */
export type CompetencyLevel = 'trainee' | 'qualified' | 'expert' | 'master';

/**
 * Complexity level values
 */
export type ComplexityLevel = 'basic' | 'standard' | 'advanced' | 'complex';

/**
 * Procedure type
 */
export interface Procedure {
  id: string;
  name: string;
  description: string | null;
  category: string | null;
  specialty: string | null;
  supervision_ratio: number;
  requires_certification: boolean;
  complexity_level: ComplexityLevel;
  min_pgy_level: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * Credential type
 */
export interface Credential {
  id: string;
  person_id: string;
  procedure_id: string;
  status: ProcedureStatus;
  competency_level: CompetencyLevel;
  issued_date: string | null;
  expiration_date: string | null;
  last_verified_date: string | null;
  max_concurrent_residents: number | null;
  max_per_week: number | null;
  max_per_academic_year: number | null;
  notes: string | null;
  is_valid: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * Credential with procedure details
 */
export interface CredentialWithProcedure extends Credential {
  procedure: {
    id: string;
    name: string;
    specialty: string | null;
    category: string | null;
  };
}

/**
 * Person summary for credentials
 */
export interface PersonSummary {
  id: string;
  name: string;
  type: string;
}

/**
 * Credential with person details
 */
export interface CredentialWithPerson extends Credential {
  person: PersonSummary;
}

/**
 * Faculty credential summary
 */
export interface FacultyCredentialSummary {
  person_id: string;
  person_name: string;
  total_credentials: number;
  active_credentials: number;
  expiring_soon: number;
  procedures: Array<{
    id: string;
    name: string;
    specialty: string | null;
    category: string | null;
  }>;
}

/**
 * Mock data factories for procedures
 */
export const procedureMockFactories = {
  procedure: (overrides: Partial<Procedure> = {}): Procedure => ({
    id: 'proc-1',
    name: 'Colonoscopy',
    description: 'Diagnostic and therapeutic colonoscopy procedure',
    category: 'surgical',
    specialty: 'Gastroenterology',
    supervision_ratio: 1,
    requires_certification: true,
    complexity_level: 'standard',
    min_pgy_level: 2,
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    ...overrides,
  }),

  credential: (overrides: Partial<Credential> = {}): Credential => ({
    id: 'cred-1',
    person_id: 'person-1',
    procedure_id: 'proc-1',
    status: 'active',
    competency_level: 'qualified',
    issued_date: '2024-01-01',
    expiration_date: '2025-01-01',
    last_verified_date: '2024-06-01',
    max_concurrent_residents: 2,
    max_per_week: 10,
    max_per_academic_year: 200,
    notes: null,
    is_valid: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    ...overrides,
  }),

  credentialWithProcedure: (overrides: Partial<CredentialWithProcedure> = {}): CredentialWithProcedure => ({
    ...procedureMockFactories.credential(),
    procedure: {
      id: 'proc-1',
      name: 'Colonoscopy',
      specialty: 'Gastroenterology',
      category: 'surgical',
    },
    ...overrides,
  }),

  credentialWithPerson: (overrides: Partial<CredentialWithPerson> = {}): CredentialWithPerson => ({
    ...procedureMockFactories.credential(),
    person: {
      id: 'person-1',
      name: 'Dr. John Smith',
      type: 'faculty',
    },
    ...overrides,
  }),

  facultySummary: (overrides: Partial<FacultyCredentialSummary> = {}): FacultyCredentialSummary => ({
    person_id: 'person-1',
    person_name: 'Dr. John Smith',
    total_credentials: 5,
    active_credentials: 4,
    expiring_soon: 1,
    procedures: [
      { id: 'proc-1', name: 'Colonoscopy', specialty: 'Gastroenterology', category: 'surgical' },
      { id: 'proc-2', name: 'Upper Endoscopy', specialty: 'Gastroenterology', category: 'surgical' },
      { id: 'proc-3', name: 'Joint Injection', specialty: 'Sports Medicine', category: 'office' },
      { id: 'proc-4', name: 'Ultrasound-guided Aspiration', specialty: 'Sports Medicine', category: 'office' },
    ],
    ...overrides,
  }),

  expiredCredential: (overrides: Partial<Credential> = {}): Credential => ({
    ...procedureMockFactories.credential(),
    id: 'cred-expired',
    status: 'expired',
    expiration_date: '2023-01-01',
    is_valid: false,
    ...overrides,
  }),

  suspendedCredential: (overrides: Partial<Credential> = {}): Credential => ({
    ...procedureMockFactories.credential(),
    id: 'cred-suspended',
    status: 'suspended',
    is_valid: false,
    notes: 'Suspended pending recertification review',
    ...overrides,
  }),

  pendingCredential: (overrides: Partial<Credential> = {}): Credential => ({
    ...procedureMockFactories.credential(),
    id: 'cred-pending',
    status: 'pending',
    issued_date: null,
    expiration_date: null,
    is_valid: false,
    notes: 'Awaiting certification completion',
    ...overrides,
  }),

  expiringCredential: (overrides: Partial<Credential> = {}): Credential => {
    const expirationDate = new Date();
    expirationDate.setDate(expirationDate.getDate() + 15);
    return {
      ...procedureMockFactories.credential(),
      id: 'cred-expiring',
      expiration_date: expirationDate.toISOString().split('T')[0],
      ...overrides,
    };
  },
};

/**
 * Mock API responses
 */
export const procedureMockResponses = {
  procedureList: {
    items: [
      procedureMockFactories.procedure(),
      procedureMockFactories.procedure({
        id: 'proc-2',
        name: 'Upper Endoscopy',
        description: 'Diagnostic and therapeutic upper GI endoscopy',
        complexity_level: 'standard',
      }),
      procedureMockFactories.procedure({
        id: 'proc-3',
        name: 'Joint Injection',
        specialty: 'Sports Medicine',
        category: 'office',
        complexity_level: 'basic',
        min_pgy_level: 1,
      }),
      procedureMockFactories.procedure({
        id: 'proc-4',
        name: 'Arthroscopic Surgery',
        specialty: 'Orthopedics',
        category: 'surgical',
        complexity_level: 'advanced',
        min_pgy_level: 3,
      }),
    ],
    total: 4,
  },

  credentialList: {
    items: [
      procedureMockFactories.credential(),
      procedureMockFactories.credential({
        id: 'cred-2',
        procedure_id: 'proc-2',
        competency_level: 'expert',
      }),
      procedureMockFactories.expiredCredential(),
    ],
    total: 3,
  },

  credentialWithProcedureList: {
    items: [
      procedureMockFactories.credentialWithProcedure(),
      procedureMockFactories.credentialWithProcedure({
        id: 'cred-2',
        procedure_id: 'proc-2',
        competency_level: 'expert',
        procedure: {
          id: 'proc-2',
          name: 'Upper Endoscopy',
          specialty: 'Gastroenterology',
          category: 'surgical',
        },
      }),
    ],
    total: 2,
  },

  facultyCredentialsList: [
    procedureMockFactories.facultySummary(),
    procedureMockFactories.facultySummary({
      person_id: 'person-2',
      person_name: 'Dr. Jane Doe',
      total_credentials: 3,
      active_credentials: 3,
      expiring_soon: 0,
      procedures: [
        { id: 'proc-3', name: 'Joint Injection', specialty: 'Sports Medicine', category: 'office' },
        { id: 'proc-4', name: 'Arthroscopic Surgery', specialty: 'Orthopedics', category: 'surgical' },
      ],
    }),
    procedureMockFactories.facultySummary({
      person_id: 'person-3',
      person_name: 'Dr. Mike Wilson',
      total_credentials: 2,
      active_credentials: 1,
      expiring_soon: 1,
      procedures: [
        { id: 'proc-1', name: 'Colonoscopy', specialty: 'Gastroenterology', category: 'surgical' },
      ],
    }),
  ],

  qualifiedFaculty: {
    procedure_id: 'proc-1',
    procedure_name: 'Colonoscopy',
    qualified_faculty: [
      { id: 'person-1', name: 'Dr. John Smith', type: 'faculty' },
      { id: 'person-3', name: 'Dr. Mike Wilson', type: 'faculty' },
    ],
    total: 2,
  },

  emptyProcedureList: {
    items: [],
    total: 0,
  },

  emptyCredentialList: {
    items: [],
    total: 0,
  },
};
