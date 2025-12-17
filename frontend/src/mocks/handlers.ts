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
    pgy_level: 2,
    performs_procedures: true,
    specialties: ['Internal Medicine'],
    primary_duty: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'person-2',
    name: 'Dr. Jane Doe',
    email: 'jane.doe@hospital.org',
    type: 'resident' as const,
    pgy_level: 1,
    performs_procedures: false,
    specialties: ['Internal Medicine'],
    primary_duty: null,
    created_at: '2024-01-02T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z',
  },
  {
    id: 'person-3',
    name: 'Dr. Robert Faculty',
    email: 'robert.faculty@hospital.org',
    type: 'faculty' as const,
    pgy_level: null,
    performs_procedures: true,
    specialties: ['Cardiology', 'Internal Medicine'],
    primary_duty: 'Attending Physician',
    created_at: '2024-01-03T00:00:00Z',
    updated_at: '2024-01-03T00:00:00Z',
  },
]

export const mockAbsences = [
  {
    id: 'absence-1',
    person_id: 'person-1',
    start_date: '2024-02-01',
    end_date: '2024-02-07',
    absence_type: 'vacation' as const,
    deployment_orders: false,
    tdy_location: null,
    replacement_activity: null,
    notes: 'Annual vacation',
    created_at: '2024-01-15T00:00:00Z',
  },
  {
    id: 'absence-2',
    person_id: 'person-2',
    start_date: '2024-03-01',
    end_date: '2024-03-15',
    absence_type: 'conference' as const,
    deployment_orders: false,
    tdy_location: null,
    replacement_activity: null,
    notes: 'Medical conference',
    created_at: '2024-02-01T00:00:00Z',
  },
]

export const mockAssignments = [
  {
    id: 'assignment-1',
    block_id: 'block-1',
    person_id: 'person-1',
    rotation_template_id: 'template-1',
    role: 'primary' as const,
    activity_override: null,
    notes: null,
    created_by: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
]

export const mockRotationTemplates = [
  {
    id: 'template-1',
    name: 'Inpatient Medicine',
    activity_type: 'inpatient',
    abbreviation: 'IM',
    clinic_location: null,
    max_residents: 4,
    requires_specialty: null,
    requires_procedure_credential: false,
    supervision_required: true,
    max_supervision_ratio: 4,
    created_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'template-2',
    name: 'Outpatient Clinic',
    activity_type: 'outpatient',
    abbreviation: 'OC',
    clinic_location: 'Building A, Room 101',
    max_residents: 2,
    requires_specialty: null,
    requires_procedure_credential: false,
    supervision_required: true,
    max_supervision_ratio: 2,
    created_at: '2024-01-01T00:00:00Z',
  },
]

export const mockValidation = {
  valid: true,
  total_violations: 0,
  violations: [],
  coverage_rate: 100,
  statistics: {
    total_blocks: 100,
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
    const pgyLevel = url.searchParams.get('pgy_level')

    let filteredPeople = [...mockPeople]

    if (role) {
      filteredPeople = filteredPeople.filter((p) => p.type === role)
    }

    if (pgyLevel) {
      filteredPeople = filteredPeople.filter(
        (p) => p.pgy_level === parseInt(pgyLevel, 10)
      )
    }

    return HttpResponse.json({
      items: filteredPeople,
      total: filteredPeople.length,
    })
  }),

  http.get(`${API_BASE_URL}/people/residents`, ({ request }) => {
    const url = new URL(request.url)
    const pgyLevel = url.searchParams.get('pgy_level')

    let residents = mockPeople.filter((p) => p.type === 'resident')

    if (pgyLevel) {
      residents = residents.filter(
        (p) => p.pgy_level === parseInt(pgyLevel, 10)
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

    if (body.type === 'resident' && !body.pgy_level) {
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
      pgy_level: (body.pgy_level as number) || null,
      performs_procedures: (body.performs_procedures as boolean) || false,
      specialties: (body.specialties as string[]) || null,
      primary_duty: (body.primary_duty as string) || null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
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
      updated_at: new Date().toISOString(),
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
    const personId = url.searchParams.get('person_id')

    let filteredAbsences = [...mockAbsences]

    if (personId) {
      filteredAbsences = filteredAbsences.filter(
        (a) => a.person_id === personId
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
    if (!body.person_id) {
      return HttpResponse.json(
        { detail: 'Person ID is required' },
        { status: 400 }
      )
    }

    if (!body.start_date || !body.end_date) {
      return HttpResponse.json(
        { detail: 'Start and end dates are required' },
        { status: 400 }
      )
    }

    // Check date order
    if (new Date(body.start_date as string) > new Date(body.end_date as string)) {
      return HttpResponse.json(
        { detail: 'End date must be after start date' },
        { status: 400 }
      )
    }

    const newAbsence = {
      id: `absence-${Date.now()}`,
      person_id: body.person_id as string,
      start_date: body.start_date as string,
      end_date: body.end_date as string,
      absence_type: (body.absence_type as string) || 'vacation',
      deployment_orders: (body.deployment_orders as boolean) || false,
      tdy_location: (body.tdy_location as string) || null,
      replacement_activity: (body.replacement_activity as string) || null,
      notes: (body.notes as string) || null,
      created_at: new Date().toISOString(),
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
    const personId = url.searchParams.get('person_id')
    const startDate = url.searchParams.get('start_date')
    const endDate = url.searchParams.get('end_date')

    let filteredAssignments = [...mockAssignments]

    if (personId) {
      filteredAssignments = filteredAssignments.filter(
        (a) => a.person_id === personId
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

    if (!body.block_id || !body.person_id) {
      return HttpResponse.json(
        { detail: 'Block ID and Person ID are required' },
        { status: 400 }
      )
    }

    const newAssignment = {
      id: `assignment-${Date.now()}`,
      block_id: body.block_id as string,
      person_id: body.person_id as string,
      rotation_template_id: (body.rotation_template_id as string) || null,
      role: (body.role as string) || 'primary',
      activity_override: (body.activity_override as string) || null,
      notes: (body.notes as string) || null,
      created_by: (body.created_by as string) || null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
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

    if (!body.name || !body.activity_type) {
      return HttpResponse.json(
        { detail: 'Name and activity type are required' },
        { status: 400 }
      )
    }

    const newTemplate = {
      id: `template-${Date.now()}`,
      name: body.name as string,
      activity_type: body.activity_type as string,
      abbreviation: (body.abbreviation as string) || null,
      clinic_location: (body.clinic_location as string) || null,
      max_residents: (body.max_residents as number) || null,
      requires_specialty: (body.requires_specialty as string) || null,
      requires_procedure_credential: (body.requires_procedure_credential as boolean) || false,
      supervision_required: (body.supervision_required as boolean) || true,
      max_supervision_ratio: (body.max_supervision_ratio as number) || 4,
      created_at: new Date().toISOString(),
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

  // Schedule endpoints
  http.post(`${API_BASE_URL}/schedule/generate`, async ({ request }) => {
    const body = await request.json() as Record<string, unknown>

    if (!body.start_date || !body.end_date) {
      return HttpResponse.json(
        { detail: 'Start and end dates are required' },
        { status: 400 }
      )
    }

    return HttpResponse.json({
      status: 'success',
      message: 'Schedule generated successfully',
      total_blocks_assigned: 100,
      total_blocks: 100,
      validation: mockValidation,
      run_id: `run-${Date.now()}`,
    })
  }),

  http.get(`${API_BASE_URL}/schedule/validate`, ({ request }) => {
    const url = new URL(request.url)
    const startDate = url.searchParams.get('start_date')
    const endDate = url.searchParams.get('end_date')

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
