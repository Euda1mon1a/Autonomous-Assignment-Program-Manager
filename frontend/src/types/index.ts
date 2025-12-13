// Core types for the Residency Scheduler

export interface Person {
  id: string
  name: string
  type: 'resident' | 'faculty'
  email?: string
  pgy_level?: number
  performs_procedures?: boolean
  specialties?: string[]
  primary_duty?: string
  created_at: string
  updated_at: string
}

export interface Block {
  id: string
  date: string
  time_of_day: 'AM' | 'PM'
  block_number: number
  is_weekend: boolean
  is_holiday: boolean
  holiday_name?: string
}

export interface RotationTemplate {
  id: string
  name: string
  activity_type: string
  abbreviation?: string
  clinic_location?: string
  max_residents?: number
  requires_specialty?: string
  requires_procedure_credential: boolean
  supervision_required: boolean
  max_supervision_ratio: number
  created_at: string
}

export interface Assignment {
  id: string
  block_id: string
  person_id: string
  rotation_template_id?: string
  role: 'primary' | 'supervising' | 'backup'
  activity_override?: string
  notes?: string
  created_by?: string
  created_at: string
  updated_at: string
}

export interface Absence {
  id: string
  person_id: string
  start_date: string
  end_date: string
  absence_type: 'vacation' | 'deployment' | 'tdy' | 'medical' | 'family_emergency' | 'conference'
  deployment_orders: boolean
  tdy_location?: string
  replacement_activity?: string
  notes?: string
  created_at: string
}

export interface Violation {
  type: string
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'
  person_id?: string
  person_name?: string
  block_id?: string
  message: string
  details?: Record<string, unknown>
}

export interface ValidationResult {
  valid: boolean
  total_violations: number
  violations: Violation[]
  coverage_rate: number
  statistics?: Record<string, unknown>
}

export interface ScheduleResponse {
  start_date: string
  end_date: string
  schedule: Record<string, {
    AM: AssignmentDetail[]
    PM: AssignmentDetail[]
  }>
  total_assignments: number
}

export interface AssignmentDetail {
  id: string
  person: {
    id: string
    name: string
    type: string
    pgy_level: number | null
  }
  role: string
  activity: string
  abbreviation: string
}
