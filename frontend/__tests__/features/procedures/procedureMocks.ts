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
  supervisionRatio: number;
  requiresCertification: boolean;
  complexityLevel: ComplexityLevel;
  minPgyLevel: number;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

/**
 * Credential type
 */
export interface Credential {
  id: string;
  personId: string;
  procedureId: string;
  status: ProcedureStatus;
  competencyLevel: CompetencyLevel;
  issuedDate: string | null;
  expirationDate: string | null;
  lastVerifiedDate: string | null;
  maxConcurrentResidents: number | null;
  maxPerWeek: number | null;
  maxPerAcademicYear: number | null;
  notes: string | null;
  isValid: boolean;
  createdAt: string;
  updatedAt: string;
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
  personId: string;
  personName: string;
  totalCredentials: number;
  activeCredentials: number;
  expiringSoon: number;
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
    supervisionRatio: 1,
    requiresCertification: true,
    complexityLevel: 'standard',
    minPgyLevel: 2,
    isActive: true,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
    ...overrides,
  }),

  credential: (overrides: Partial<Credential> = {}): Credential => ({
    id: 'cred-1',
    personId: 'person-1',
    procedureId: 'proc-1',
    status: 'active',
    competencyLevel: 'qualified',
    issuedDate: '2024-01-01',
    expirationDate: '2025-01-01',
    lastVerifiedDate: '2024-06-01',
    maxConcurrentResidents: 2,
    maxPerWeek: 10,
    maxPerAcademicYear: 200,
    notes: null,
    isValid: true,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
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
    personId: 'person-1',
    personName: 'Dr. John Smith',
    totalCredentials: 5,
    activeCredentials: 4,
    expiringSoon: 1,
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
    expirationDate: '2023-01-01',
    isValid: false,
    ...overrides,
  }),

  suspendedCredential: (overrides: Partial<Credential> = {}): Credential => ({
    ...procedureMockFactories.credential(),
    id: 'cred-suspended',
    status: 'suspended',
    isValid: false,
    notes: 'Suspended pending recertification review',
    ...overrides,
  }),

  pendingCredential: (overrides: Partial<Credential> = {}): Credential => ({
    ...procedureMockFactories.credential(),
    id: 'cred-pending',
    status: 'pending',
    issuedDate: null,
    expirationDate: null,
    isValid: false,
    notes: 'Awaiting certification completion',
    ...overrides,
  }),

  expiringCredential: (overrides: Partial<Credential> = {}): Credential => {
    const expirationDate = new Date();
    expirationDate.setDate(expirationDate.getDate() + 15);
    return {
      ...procedureMockFactories.credential(),
      id: 'cred-expiring',
      expirationDate: expirationDate.toISOString().split('T')[0],
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
        complexityLevel: 'standard',
      }),
      procedureMockFactories.procedure({
        id: 'proc-3',
        name: 'Joint Injection',
        specialty: 'Sports Medicine',
        category: 'office',
        complexityLevel: 'basic',
        minPgyLevel: 1,
      }),
      procedureMockFactories.procedure({
        id: 'proc-4',
        name: 'Arthroscopic Surgery',
        specialty: 'Orthopedics',
        category: 'surgical',
        complexityLevel: 'advanced',
        minPgyLevel: 3,
      }),
    ],
    total: 4,
  },

  credentialList: {
    items: [
      procedureMockFactories.credential(),
      procedureMockFactories.credential({
        id: 'cred-2',
        procedureId: 'proc-2',
        competencyLevel: 'expert',
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
        procedureId: 'proc-2',
        competencyLevel: 'expert',
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
      personId: 'person-2',
      personName: 'Dr. Jane Doe',
      totalCredentials: 3,
      activeCredentials: 3,
      expiringSoon: 0,
      procedures: [
        { id: 'proc-3', name: 'Joint Injection', specialty: 'Sports Medicine', category: 'office' },
        { id: 'proc-4', name: 'Arthroscopic Surgery', specialty: 'Orthopedics', category: 'surgical' },
      ],
    }),
    procedureMockFactories.facultySummary({
      personId: 'person-3',
      personName: 'Dr. Mike Wilson',
      totalCredentials: 2,
      activeCredentials: 1,
      expiringSoon: 1,
      procedures: [
        { id: 'proc-1', name: 'Colonoscopy', specialty: 'Gastroenterology', category: 'surgical' },
      ],
    }),
  ],

  qualifiedFaculty: {
    procedureId: 'proc-1',
    procedureName: 'Colonoscopy',
    qualifiedFaculty: [
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
