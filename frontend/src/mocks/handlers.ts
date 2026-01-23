/**
 * MSW Request Handlers
 *
 * Defines mock API handlers for testing. These handlers intercept
 * HTTP requests during tests and return mock responses.
 */
import { http, HttpResponse } from 'msw'

// Base URL for API requests
const API_BASE_URL = 'http://localhost:8000/api'

// ============================================================================
// Mock Data
// ============================================================================

export const mockPeople = [
  {
    id: 'person-1',
    name: 'Dr. John Smith',
    email: 'john.smith@hospital.org',
    type: 'resident' as const,
    pgyLevel: 2,
    performsProcedures: true,
    specialties: ['Internal Medicine'],
    primaryDuty: null,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  },
  {
    id: 'person-2',
    name: 'Dr. Jane Doe',
    email: 'jane.doe@hospital.org',
    type: 'resident' as const,
    pgyLevel: 1,
    performsProcedures: false,
    specialties: ['Internal Medicine'],
    primaryDuty: null,
    createdAt: '2024-01-02T00:00:00Z',
    updatedAt: '2024-01-02T00:00:00Z',
  },
  {
    id: 'person-3',
    name: 'Dr. Robert Faculty',
    email: 'robert.faculty@hospital.org',
    type: 'faculty' as const,
    pgyLevel: null,
    performsProcedures: true,
    specialties: ['Cardiology', 'Internal Medicine'],
    primaryDuty: 'Attending Physician',
    createdAt: '2024-01-03T00:00:00Z',
    updatedAt: '2024-01-03T00:00:00Z',
  },
]

export const mockAbsences = [
  {
    id: 'absence-1',
    personId: 'person-1',
    startDate: '2024-02-01',
    endDate: '2024-02-07',
    absenceType: 'vacation' as const,
    deploymentOrders: false,
    tdyLocation: null,
    replacementActivity: null,
    notes: 'Annual vacation',
    createdAt: '2024-01-15T00:00:00Z',
  },
  {
    id: 'absence-2',
    personId: 'person-2',
    startDate: '2024-03-01',
    endDate: '2024-03-15',
    absenceType: 'conference' as const,
    deploymentOrders: false,
    tdyLocation: null,
    replacementActivity: null,
    notes: 'Medical conference',
    createdAt: '2024-02-01T00:00:00Z',
  },
]

export const mockAssignments = [
  {
    id: 'assignment-1',
    blockId: 'block-1',
    personId: 'person-1',
    rotationTemplateId: 'template-1',
    role: 'primary' as const,
    activityOverride: null,
    notes: null,
    createdBy: null,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  },
]

export const mockRotationTemplates = [
  {
    id: 'template-1',
    name: 'Inpatient Medicine',
    activityType: 'inpatient',
    abbreviation: 'IM',
    clinicLocation: null,
    maxResidents: 4,
    requiresSpecialty: null,
    requiresProcedureCredential: false,
    supervisionRequired: true,
    maxSupervisionRatio: 4,
    createdAt: '2024-01-01T00:00:00Z',
  },
  {
    id: 'template-2',
    name: 'Outpatient Clinic',
    activityType: 'outpatient',
    abbreviation: 'OC',
    clinicLocation: 'Building A, Room 101',
    maxResidents: 2,
    requiresSpecialty: null,
    requiresProcedureCredential: false,
    supervisionRequired: true,
    maxSupervisionRatio: 2,
    createdAt: '2024-01-01T00:00:00Z',
  },
]

export const mockValidation = {
  valid: true,
  totalViolations: 0,
  violations: [],
  coverageRate: 100,
  statistics: {
    totalBlocks: 100,
    assigned_blocks: 100,
    unassigned_blocks: 0,
  },
}

// ============================================================================
// Request Handlers
// ============================================================================

export const handlers = [
  // People endpoints
  http.get(`${API_BASE_URL}/people`, ({ request }) => {
    const url = new URL(request.url)
    const role = url.searchParams.get('role')
    const pgyLevel = url.searchParams.get('pgyLevel')

    let filteredPeople = [...mockPeople]

    if (role) {
      filteredPeople = filteredPeople.filter((p) => p.type === role)
    }

    if (pgyLevel) {
      filteredPeople = filteredPeople.filter(
        (p) => p.pgyLevel === parseInt(pgyLevel, 10)
      )
    }

    return HttpResponse.json({
      items: filteredPeople,
      total: filteredPeople.length,
    })
  }),

  http.get(`${API_BASE_URL}/people/residents`, ({ request }) => {
    const url = new URL(request.url)
    const pgyLevel = url.searchParams.get('pgyLevel')

    let residents = mockPeople.filter((p) => p.type === 'resident')

    if (pgyLevel) {
      residents = residents.filter(
        (p) => p.pgyLevel === parseInt(pgyLevel, 10)
      )
    }

    return HttpResponse.json({
      items: residents,
      total: residents.length,
    })
  }),

  http.get(`${API_BASE_URL}/people/faculty`, ({ request }) => {
    const url = new URL(request.url)
    const specialty = url.searchParams.get('specialty')

    let faculty = mockPeople.filter((p) => p.type === 'faculty')

    if (specialty) {
      faculty = faculty.filter(
        (p) => p.specialties?.includes(specialty)
      )
    }

    return HttpResponse.json({
      items: faculty,
      total: faculty.length,
    })
  }),

  http.get(`${API_BASE_URL}/people/:id`, ({ params }) => {
    const person = mockPeople.find((p) => p.id === params.id)

    if (!person) {
      return HttpResponse.json(
        { detail: 'Person not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json(person)
  }),

  http.post(`${API_BASE_URL}/people`, async ({ request }) => {
    const body = await request.json() as Record<string, unknown>

    // Validate required fields
    if (!body.name || typeof body.name !== 'string') {
      return HttpResponse.json(
        { detail: 'Name is required' },
        { status: 400 }
      )
    }

    if (body.type === 'resident' && !body.pgyLevel) {
      return HttpResponse.json(
        { detail: 'PGY level is required for residents' },
        { status: 400 }
      )
    }

    const newPerson = {
      id: `person-${Date.now()}`,
      name: body.name as string,
      email: (body.email as string) || null,
      type: (body.type as 'resident' | 'faculty') || 'resident',
      pgyLevel: (body.pgyLevel as number) || null,
      performsProcedures: (body.performsProcedures as boolean) || false,
      specialties: (body.specialties as string[]) || null,
      primaryDuty: (body.primaryDuty as string) || null,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    }

    return HttpResponse.json(newPerson, { status: 201 })
  }),

  http.put(`${API_BASE_URL}/people/:id`, async ({ params, request }) => {
    const person = mockPeople.find((p) => p.id === params.id)

    if (!person) {
      return HttpResponse.json(
        { detail: 'Person not found' },
        { status: 404 }
      )
    }

    const body = await request.json() as Record<string, unknown>
    const updatedPerson = {
      ...person,
      ...body,
      updatedAt: new Date().toISOString(),
    }

    return HttpResponse.json(updatedPerson)
  }),

  http.delete(`${API_BASE_URL}/people/:id`, ({ params }) => {
    const person = mockPeople.find((p) => p.id === params.id)

    if (!person) {
      return HttpResponse.json(
        { detail: 'Person not found' },
        { status: 404 }
      )
    }

    return new HttpResponse(null, { status: 204 })
  }),

  // Absences endpoints
  http.get(`${API_BASE_URL}/absences`, ({ request }) => {
    const url = new URL(request.url)
    const personId = url.searchParams.get('personId')

    let filteredAbsences = [...mockAbsences]

    if (personId) {
      filteredAbsences = filteredAbsences.filter(
        (a) => a.personId === personId
      )
    }

    return HttpResponse.json({
      items: filteredAbsences,
      total: filteredAbsences.length,
    })
  }),

  http.get(`${API_BASE_URL}/absences/:id`, ({ params }) => {
    const absence = mockAbsences.find((a) => a.id === params.id)

    if (!absence) {
      return HttpResponse.json(
        { detail: 'Absence not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json(absence)
  }),

  http.post(`${API_BASE_URL}/absences`, async ({ request }) => {
    const body = await request.json() as Record<string, unknown>

    // Validate required fields
    if (!body.personId) {
      return HttpResponse.json(
        { detail: 'Person ID is required' },
        { status: 400 }
      )
    }

    if (!body.startDate || !body.endDate) {
      return HttpResponse.json(
        { detail: 'Start and end dates are required' },
        { status: 400 }
      )
    }

    // Check date order
    if (new Date(body.startDate as string) > new Date(body.endDate as string)) {
      return HttpResponse.json(
        { detail: 'End date must be after start date' },
        { status: 400 }
      )
    }

    const newAbsence = {
      id: `absence-${Date.now()}`,
      personId: body.personId as string,
      startDate: body.startDate as string,
      endDate: body.endDate as string,
      absenceType: (body.absenceType as string) || 'vacation',
      deploymentOrders: (body.deploymentOrders as boolean) || false,
      tdyLocation: (body.tdyLocation as string) || null,
      replacementActivity: (body.replacementActivity as string) || null,
      notes: (body.notes as string) || null,
      createdAt: new Date().toISOString(),
    }

    return HttpResponse.json(newAbsence, { status: 201 })
  }),

  http.put(`${API_BASE_URL}/absences/:id`, async ({ params, request }) => {
    const absence = mockAbsences.find((a) => a.id === params.id)

    if (!absence) {
      return HttpResponse.json(
        { detail: 'Absence not found' },
        { status: 404 }
      )
    }

    const body = await request.json() as Record<string, unknown>
    const updatedAbsence = {
      ...absence,
      ...body,
    }

    return HttpResponse.json(updatedAbsence)
  }),

  http.delete(`${API_BASE_URL}/absences/:id`, ({ params }) => {
    const absence = mockAbsences.find((a) => a.id === params.id)

    if (!absence) {
      return HttpResponse.json(
        { detail: 'Absence not found' },
        { status: 404 }
      )
    }

    return new HttpResponse(null, { status: 204 })
  }),

  // Assignments endpoints
  http.get(`${API_BASE_URL}/assignments`, ({ request }) => {
    const url = new URL(request.url)
    const personId = url.searchParams.get('personId')
    const startDate = url.searchParams.get('startDate')
    const endDate = url.searchParams.get('endDate')

    let filteredAssignments = [...mockAssignments]

    if (personId) {
      filteredAssignments = filteredAssignments.filter(
        (a) => a.personId === personId
      )
    }

    // Note: In a real implementation, we would filter by date range

    return HttpResponse.json({
      items: filteredAssignments,
      total: filteredAssignments.length,
    })
  }),

  http.post(`${API_BASE_URL}/assignments`, async ({ request }) => {
    const body = await request.json() as Record<string, unknown>

    if (!body.blockId || !body.personId) {
      return HttpResponse.json(
        { detail: 'Block ID and Person ID are required' },
        { status: 400 }
      )
    }

    const newAssignment = {
      id: `assignment-${Date.now()}`,
      blockId: body.blockId as string,
      personId: body.personId as string,
      rotationTemplateId: (body.rotationTemplateId as string) || null,
      role: (body.role as string) || 'primary',
      activityOverride: (body.activityOverride as string) || null,
      notes: (body.notes as string) || null,
      createdBy: (body.createdBy as string) || null,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    }

    return HttpResponse.json(newAssignment, { status: 201 })
  }),

  http.delete(`${API_BASE_URL}/assignments/:id`, ({ params }) => {
    const assignment = mockAssignments.find((a) => a.id === params.id)

    if (!assignment) {
      return HttpResponse.json(
        { detail: 'Assignment not found' },
        { status: 404 }
      )
    }

    return new HttpResponse(null, { status: 204 })
  }),

  // Rotation templates endpoints
  http.get(`${API_BASE_URL}/rotation-templates`, () => {
    return HttpResponse.json({
      items: mockRotationTemplates,
      total: mockRotationTemplates.length,
    })
  }),

  http.get(`${API_BASE_URL}/rotation-templates/:id`, ({ params }) => {
    const template = mockRotationTemplates.find((t) => t.id === params.id)

    if (!template) {
      return HttpResponse.json(
        { detail: 'Rotation template not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json(template)
  }),

  http.post(`${API_BASE_URL}/rotation-templates`, async ({ request }) => {
    const body = await request.json() as Record<string, unknown>

    if (!body.name || !body.activityType) {
      return HttpResponse.json(
        { detail: 'Name and activity type are required' },
        { status: 400 }
      )
    }

    const newTemplate = {
      id: `template-${Date.now()}`,
      name: body.name as string,
      activityType: body.activityType as string,
      abbreviation: (body.abbreviation as string) || null,
      clinicLocation: (body.clinicLocation as string) || null,
      maxResidents: (body.maxResidents as number) || null,
      requiresSpecialty: (body.requiresSpecialty as string) || null,
      requiresProcedureCredential: (body.requiresProcedureCredential as boolean) || false,
      supervisionRequired: (body.supervisionRequired as boolean) || true,
      maxSupervisionRatio: (body.maxSupervisionRatio as number) || 4,
      createdAt: new Date().toISOString(),
    }

    return HttpResponse.json(newTemplate, { status: 201 })
  }),

  http.put(`${API_BASE_URL}/rotation-templates/:id`, async ({ params, request }) => {
    const template = mockRotationTemplates.find((t) => t.id === params.id)

    if (!template) {
      return HttpResponse.json(
        { detail: 'Rotation template not found' },
        { status: 404 }
      )
    }

    const body = await request.json() as Record<string, unknown>
    const updatedTemplate = {
      ...template,
      ...body,
    }

    return HttpResponse.json(updatedTemplate)
  }),

  http.delete(`${API_BASE_URL}/rotation-templates/:id`, ({ params }) => {
    const template = mockRotationTemplates.find((t) => t.id === params.id)

    if (!template) {
      return HttpResponse.json(
        { detail: 'Rotation template not found' },
        { status: 404 }
      )
    }

    return new HttpResponse(null, { status: 204 })
  }),

  // Weekly patterns endpoints
  http.get(`${API_BASE_URL}/rotation-templates/:id/patterns`, ({ params }) => {
    const template = mockRotationTemplates.find((t) => t.id === params.id)

    if (!template) {
      return HttpResponse.json(
        { detail: 'Rotation template not found' },
        { status: 404 }
      )
    }

    // Return mock patterns for the template
    const mockPatterns = [
      {
        id: `pattern-${params.id}-1`,
        rotationTemplateId: params.id,
        dayOfWeek: 1, // Monday
        timeOfDay: 'AM',
        activityType: 'fm_clinic',
        linkedTemplateId: 'template-2',
        isProtected: false,
        notes: null,
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-01T00:00:00Z',
      },
      {
        id: `pattern-${params.id}-2`,
        rotationTemplateId: params.id,
        dayOfWeek: 1, // Monday
        timeOfDay: 'PM',
        activityType: 'fm_clinic',
        linkedTemplateId: 'template-2',
        isProtected: false,
        notes: null,
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-01T00:00:00Z',
      },
    ]

    return HttpResponse.json(mockPatterns)
  }),

  http.put(`${API_BASE_URL}/rotation-templates/:id/patterns`, async ({ params, request }) => {
    const template = mockRotationTemplates.find((t) => t.id === params.id)

    if (!template) {
      return HttpResponse.json(
        { detail: 'Rotation template not found' },
        { status: 404 }
      )
    }

    const body = await request.json() as { patterns: Array<Record<string, unknown>> }
    const now = new Date().toISOString()

    // Return the created patterns
    const createdPatterns = body.patterns.map((p, index) => ({
      id: `pattern-${params.id}-${index}`,
      rotationTemplateId: params.id,
      dayOfWeek: p.dayOfWeek,
      timeOfDay: p.timeOfDay,
      activityType: p.activityType,
      linkedTemplateId: p.linkedTemplateId,
      isProtected: p.isProtected || false,
      notes: p.notes || null,
      createdAt: now,
      updatedAt: now,
    }))

    return HttpResponse.json(createdPatterns)
  }),

  // Rotation preferences endpoints
  http.get(`${API_BASE_URL}/rotation-templates/:id/preferences`, ({ params }) => {
    const template = mockRotationTemplates.find((t) => t.id === params.id)

    if (!template) {
      return HttpResponse.json(
        { detail: 'Rotation template not found' },
        { status: 404 }
      )
    }

    // Return mock preferences
    const mockPreferences = [
      {
        id: `pref-${params.id}-1`,
        rotationTemplateId: params.id,
        preferenceType: 'full_day_grouping',
        weight: 'medium',
        configJson: {},
        isActive: true,
        description: 'Prefer full days when possible',
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-01T00:00:00Z',
      },
    ]

    return HttpResponse.json(mockPreferences)
  }),

  http.put(`${API_BASE_URL}/rotation-templates/:id/preferences`, async ({ params, request }) => {
    const template = mockRotationTemplates.find((t) => t.id === params.id)

    if (!template) {
      return HttpResponse.json(
        { detail: 'Rotation template not found' },
        { status: 404 }
      )
    }

    const body = await request.json() as Array<Record<string, unknown>>
    const now = new Date().toISOString()

    // Return the created preferences
    const createdPreferences = body.map((p, index) => ({
      id: `pref-${params.id}-${index}`,
      rotationTemplateId: params.id,
      preferenceType: p.preferenceType,
      weight: p.weight || 'medium',
      configJson: p.configJson || {},
      isActive: p.isActive !== undefined ? p.isActive : true,
      description: p.description || null,
      createdAt: now,
      updatedAt: now,
    }))

    return HttpResponse.json(createdPreferences)
  }),

  // Schedule endpoints
  http.post(`${API_BASE_URL}/schedule/generate`, async ({ request }) => {
    const body = await request.json() as Record<string, unknown>

    if (!body.startDate || !body.endDate) {
      return HttpResponse.json(
        { detail: 'Start and end dates are required' },
        { status: 400 }
      )
    }

    return HttpResponse.json({
      status: 'success',
      message: 'Schedule generated successfully',
      totalBlocks_assigned: 100,
      totalBlocks: 100,
      validation: mockValidation,
      run_id: `run-${Date.now()}`,
    })
  }),

  http.get(`${API_BASE_URL}/schedule/validate`, ({ request }) => {
    const url = new URL(request.url)
    const startDate = url.searchParams.get('startDate')
    const endDate = url.searchParams.get('endDate')

    if (!startDate || !endDate) {
      return HttpResponse.json(
        { detail: 'Start and end dates are required' },
        { status: 400 }
      )
    }

    return HttpResponse.json(mockValidation)
  }),
]

// ============================================================================
// Error Handlers (for testing error scenarios)
// ============================================================================

export const errorHandlers = {
  // Returns a network error
  networkError: http.get(`${API_BASE_URL}/people`, () => {
    return HttpResponse.error()
  }),

  // Returns a 500 server error
  serverError: http.get(`${API_BASE_URL}/people`, () => {
    return HttpResponse.json(
      { detail: 'Internal server error' },
      { status: 500 }
    )
  }),

  // Returns a 401 unauthorized
  unauthorized: http.get(`${API_BASE_URL}/people`, () => {
    return HttpResponse.json(
      { detail: 'Unauthorized' },
      { status: 401 }
    )
  }),

  // Returns a 403 forbidden
  forbidden: http.get(`${API_BASE_URL}/people`, () => {
    return HttpResponse.json(
      { detail: 'Forbidden' },
      { status: 403 }
    )
  }),

  // Returns a 422 validation error
  validationError: http.post(`${API_BASE_URL}/people`, () => {
    return HttpResponse.json(
      {
        detail: 'Validation error',
        errors: {
          name: ['Name is required'],
          email: ['Invalid email format'],
        },
      },
      { status: 422 }
    )
  }),
}
