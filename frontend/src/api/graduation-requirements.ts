import { get, post, put, del } from '@/lib/api'

export interface GraduationRequirement {
  id: string
  pgyLevel: number
  rotationTemplateId: string
  minHalves: number
  targetHalves: number | null
  byDate: string | null
  createdAt: string
  updatedAt: string
}

export interface GraduationRequirementCreate {
  pgyLevel: number
  rotationTemplateId: string
  minHalves: number
  targetHalves?: number | null
  byDate?: string | null
}

export interface GraduationRequirementUpdate {
  minHalves?: number
  targetHalves?: number | null
  byDate?: string | null
}

export const graduationRequirementsApi = {
  getByPgy: (pgyLevel: number) =>
    get<GraduationRequirement[]>(`/graduation-requirements/pgy/${pgyLevel}`),

  create: (data: GraduationRequirementCreate) =>
    post<GraduationRequirement>('/graduation-requirements/', data),

  update: (id: string, data: GraduationRequirementUpdate) =>
    put<GraduationRequirement>(`/graduation-requirements/${id}`, data),

  delete: (id: string) =>
    del<{ message: string }>(`/graduation-requirements/${id}`),
}
