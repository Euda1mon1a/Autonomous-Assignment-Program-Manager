/**
 * useResidentWeeklyRequirements Hook Tests
 *
 * Tests for resident weekly requirements fetching and management hooks
 * using jest.mock() for API mocking.
 */
import { renderHook, waitFor } from '@/test-utils'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactNode } from 'react'
import * as api from '@/lib/api'
import {
  useResidentWeeklyRequirement,
  useResidentWeeklyRequirementById,
  useCreateResidentWeeklyRequirement,
  useUpdateResidentWeeklyRequirement,
  useDeleteResidentWeeklyRequirement,
  useUpsertResidentWeeklyRequirement,
  weeklyRequirementsQueryKeys,
} from '@/hooks/useResidentWeeklyRequirements'
import type { ResidentWeeklyRequirement } from '@/types/resident-weekly-requirement'

// Mock the api module
jest.mock('@/lib/api')

const mockedApi = api as jest.Mocked<typeof api>

// Mock data
const mockTemplateId = 'template-123'
const mockRequirementId = 'req-456'

const mockRequirement: ResidentWeeklyRequirement = {
  id: mockRequirementId,
  rotationTemplateId: mockTemplateId,
  fmClinicMinPerWeek: 2,
  fmClinicMaxPerWeek: 4,
  specialtyMinPerWeek: 1,
  specialtyMaxPerWeek: 3,
  createdAt: '2024-01-01T00:00:00Z',
  updatedAt: '2024-01-01T00:00:00Z',
}

// Create a fresh QueryClient for each test
function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
        staleTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  })
}

// Wrapper component with QueryClientProvider
function createWrapper() {
  const queryClient = createTestQueryClient()
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    )
  }
}

describe('useResidentWeeklyRequirement', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch weekly requirement by template ID successfully', async () => {
    mockedApi.get.mockResolvedValueOnce(mockRequirement)

    const { result } = renderHook(
      () => useResidentWeeklyRequirement(mockTemplateId),
      { wrapper: createWrapper() }
    )

    expect(result.current.isLoading).toBe(true)

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockRequirement)
    expect(mockedApi.get).toHaveBeenCalledWith(`/resident-weekly-requirements/${mockTemplateId}`)
  })

  it('should return null when requirement not found (404)', async () => {
    const notFoundError = Object.assign(new Error('Not found'), { status: 404 })
    mockedApi.get.mockRejectedValueOnce(notFoundError)

    const { result } = renderHook(
      () => useResidentWeeklyRequirement(mockTemplateId),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toBeNull()
  })

  it('should throw error for non-404 errors', async () => {
    const apiError = Object.assign(new Error('Server error'), { status: 500 })
    mockedApi.get.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useResidentWeeklyRequirement(mockTemplateId),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error?.message).toBe('Server error')
  })

  it('should not fetch when templateId is empty', async () => {
    const { result } = renderHook(
      () => useResidentWeeklyRequirement(''),
      { wrapper: createWrapper() }
    )

    expect(result.current.isLoading).toBe(false)
    expect(result.current.data).toBeUndefined()
    expect(mockedApi.get).not.toHaveBeenCalled()
  })

  it('should handle requirement with all fields populated', async () => {
    mockedApi.get.mockResolvedValueOnce(mockRequirement)

    const { result } = renderHook(
      () => useResidentWeeklyRequirement(mockTemplateId),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    const data = result.current.data
    expect(data?.fmClinicMinPerWeek).toBe(2)
    expect(data?.fmClinicMaxPerWeek).toBe(4)
    expect(data?.specialtyMinPerWeek).toBe(1)
    expect(data?.specialtyMaxPerWeek).toBe(3)
  })
})

describe('useResidentWeeklyRequirementById', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch weekly requirement by ID successfully', async () => {
    mockedApi.get.mockResolvedValueOnce(mockRequirement)

    const { result } = renderHook(
      () => useResidentWeeklyRequirementById(mockRequirementId),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockRequirement)
    expect(mockedApi.get).toHaveBeenCalledWith(`/resident-weekly-requirements/by-id/${mockRequirementId}`)
  })

  it('should not fetch when ID is empty', async () => {
    const { result } = renderHook(
      () => useResidentWeeklyRequirementById(''),
      { wrapper: createWrapper() }
    )

    expect(result.current.isLoading).toBe(false)
    expect(mockedApi.get).not.toHaveBeenCalled()
  })

  it('should handle errors', async () => {
    const apiError = Object.assign(new Error('Not found'), { status: 404 })
    mockedApi.get.mockRejectedValueOnce(apiError)

    const { result } = renderHook(
      () => useResidentWeeklyRequirementById(mockRequirementId),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error?.message).toBe('Not found')
  })
})

describe('useCreateResidentWeeklyRequirement', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should create weekly requirement successfully', async () => {
    const createData = {
      rotationTemplateId: mockTemplateId,
      fmClinicMinPerWeek: 2,
      fmClinicMaxPerWeek: 4,
      specialtyMinPerWeek: 1,
      specialtyMaxPerWeek: 3,
    }

    mockedApi.post.mockResolvedValueOnce(mockRequirement)

    const queryClient = createTestQueryClient()
    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    )

    const { result } = renderHook(() => useCreateResidentWeeklyRequirement(), { wrapper })

    result.current.mutate(createData)

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockRequirement)
    expect(mockedApi.post).toHaveBeenCalledWith('/resident-weekly-requirements', createData)
  })

  it('should invalidate queries and update cache on success', async () => {
    const createData = {
      rotationTemplateId: mockTemplateId,
      fmClinicMinPerWeek: 2,
      fmClinicMaxPerWeek: 4,
      specialtyMinPerWeek: 1,
      specialtyMaxPerWeek: 3,
    }

    mockedApi.post.mockResolvedValueOnce(mockRequirement)

    const queryClient = createTestQueryClient()
    const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries')
    const setDataSpy = jest.spyOn(queryClient, 'setQueryData')

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    )

    const { result } = renderHook(() => useCreateResidentWeeklyRequirement(), { wrapper })

    result.current.mutate(createData)

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: weeklyRequirementsQueryKeys.all,
    })
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: weeklyRequirementsQueryKeys.byTemplate(mockTemplateId),
    })
    expect(setDataSpy).toHaveBeenCalledWith(
      weeklyRequirementsQueryKeys.byTemplate(mockTemplateId),
      mockRequirement
    )
  })

  it('should handle creation errors', async () => {
    const apiError = Object.assign(new Error('Validation failed'), { status: 400 })
    mockedApi.post.mockRejectedValueOnce(apiError)

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={createTestQueryClient()}>
        {children}
      </QueryClientProvider>
    )

    const { result } = renderHook(() => useCreateResidentWeeklyRequirement(), { wrapper })

    result.current.mutate({
      rotationTemplateId: mockTemplateId,
      fmClinicMinPerWeek: 2,
      fmClinicMaxPerWeek: 4,
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error?.message).toBe('Validation failed')
  })
})

describe('useUpdateResidentWeeklyRequirement', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should update weekly requirement successfully', async () => {
    const updateData = {
      fmClinicMinPerWeek: 3,
      fmClinicMaxPerWeek: 5,
    }

    const updatedRequirement = {
      ...mockRequirement,
      ...updateData,
      updatedAt: '2024-01-02T00:00:00Z',
    }

    mockedApi.put.mockResolvedValueOnce(updatedRequirement)

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={createTestQueryClient()}>
        {children}
      </QueryClientProvider>
    )

    const { result } = renderHook(() => useUpdateResidentWeeklyRequirement(), { wrapper })

    result.current.mutate({
      id: mockRequirementId,
      templateId: mockTemplateId,
      data: updateData,
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(updatedRequirement)
    expect(mockedApi.put).toHaveBeenCalledWith(
      `/resident-weekly-requirements/${mockRequirementId}`,
      updateData
    )
  })

  it('should invalidate and update cache on success', async () => {
    const updateData = {
      fmClinicMinPerWeek: 3,
      fmClinicMaxPerWeek: 5,
    }

    const updatedRequirement = { ...mockRequirement, ...updateData }
    mockedApi.put.mockResolvedValueOnce(updatedRequirement)

    const queryClient = createTestQueryClient()
    const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries')
    const setDataSpy = jest.spyOn(queryClient, 'setQueryData')

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    )

    const { result } = renderHook(() => useUpdateResidentWeeklyRequirement(), { wrapper })

    result.current.mutate({
      id: mockRequirementId,
      templateId: mockTemplateId,
      data: updateData,
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: weeklyRequirementsQueryKeys.all,
    })
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: weeklyRequirementsQueryKeys.byTemplate(mockTemplateId),
    })
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: weeklyRequirementsQueryKeys.detail(mockRequirementId),
    })
    expect(setDataSpy).toHaveBeenCalledWith(
      weeklyRequirementsQueryKeys.byTemplate(mockTemplateId),
      updatedRequirement
    )
  })

  it('should handle update errors', async () => {
    const apiError = Object.assign(new Error('Update failed'), { status: 400 })
    mockedApi.put.mockRejectedValueOnce(apiError)

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={createTestQueryClient()}>
        {children}
      </QueryClientProvider>
    )

    const { result } = renderHook(() => useUpdateResidentWeeklyRequirement(), { wrapper })

    result.current.mutate({
      id: mockRequirementId,
      templateId: mockTemplateId,
      data: { fmClinicMinPerWeek: 3 },
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error?.message).toBe('Update failed')
  })
})

describe('useDeleteResidentWeeklyRequirement', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should delete weekly requirement successfully', async () => {
    mockedApi.del.mockResolvedValueOnce(undefined)

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={createTestQueryClient()}>
        {children}
      </QueryClientProvider>
    )

    const { result } = renderHook(() => useDeleteResidentWeeklyRequirement(), { wrapper })

    result.current.mutate({
      id: mockRequirementId,
      templateId: mockTemplateId,
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.del).toHaveBeenCalledWith(`/resident-weekly-requirements/${mockRequirementId}`)
  })

  it('should invalidate queries and set cache to null on success', async () => {
    mockedApi.del.mockResolvedValueOnce(undefined)

    const queryClient = createTestQueryClient()
    const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries')
    const setDataSpy = jest.spyOn(queryClient, 'setQueryData')

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    )

    const { result } = renderHook(() => useDeleteResidentWeeklyRequirement(), { wrapper })

    result.current.mutate({
      id: mockRequirementId,
      templateId: mockTemplateId,
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: weeklyRequirementsQueryKeys.all,
    })
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: weeklyRequirementsQueryKeys.byTemplate(mockTemplateId),
    })
    expect(setDataSpy).toHaveBeenCalledWith(
      weeklyRequirementsQueryKeys.byTemplate(mockTemplateId),
      null
    )
  })

  it('should handle deletion errors', async () => {
    const apiError = Object.assign(new Error('Delete failed'), { status: 403 })
    mockedApi.del.mockRejectedValueOnce(apiError)

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={createTestQueryClient()}>
        {children}
      </QueryClientProvider>
    )

    const { result } = renderHook(() => useDeleteResidentWeeklyRequirement(), { wrapper })

    result.current.mutate({
      id: mockRequirementId,
      templateId: mockTemplateId,
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error?.message).toBe('Delete failed')
  })
})

describe('useUpsertResidentWeeklyRequirement', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should create new requirement when existingId is undefined', async () => {
    const upsertData = {
      fmClinicMinPerWeek: 2,
      fmClinicMaxPerWeek: 4,
      specialtyMinPerWeek: 1,
      specialtyMaxPerWeek: 3,
    }

    mockedApi.post.mockResolvedValueOnce(mockRequirement)

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={createTestQueryClient()}>
        {children}
      </QueryClientProvider>
    )

    const { result } = renderHook(() => useUpsertResidentWeeklyRequirement(), { wrapper })

    result.current.mutate({
      templateId: mockTemplateId,
      data: upsertData,
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.post).toHaveBeenCalledWith('/resident-weekly-requirements', {
      ...upsertData,
      rotationTemplateId: mockTemplateId,
    })
    expect(mockedApi.put).not.toHaveBeenCalled()
  })

  it('should update existing requirement when existingId is provided', async () => {
    const upsertData = {
      fmClinicMinPerWeek: 3,
      fmClinicMaxPerWeek: 5,
    }

    const updatedRequirement = { ...mockRequirement, ...upsertData }
    mockedApi.put.mockResolvedValueOnce(updatedRequirement)

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={createTestQueryClient()}>
        {children}
      </QueryClientProvider>
    )

    const { result } = renderHook(() => useUpsertResidentWeeklyRequirement(), { wrapper })

    result.current.mutate({
      templateId: mockTemplateId,
      existingId: mockRequirementId,
      data: upsertData,
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.put).toHaveBeenCalledWith(
      `/resident-weekly-requirements/${mockRequirementId}`,
      upsertData
    )
    expect(mockedApi.post).not.toHaveBeenCalled()
  })

  it('should invalidate queries on success', async () => {
    const upsertData = {
      fmClinicMinPerWeek: 2,
      fmClinicMaxPerWeek: 4,
    }

    mockedApi.post.mockResolvedValueOnce(mockRequirement)

    const queryClient = createTestQueryClient()
    const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries')

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    )

    const { result } = renderHook(() => useUpsertResidentWeeklyRequirement(), { wrapper })

    result.current.mutate({
      templateId: mockTemplateId,
      data: upsertData,
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: weeklyRequirementsQueryKeys.all,
    })
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: weeklyRequirementsQueryKeys.byTemplate(mockTemplateId),
    })
  })

  it('should handle upsert errors', async () => {
    const apiError = Object.assign(new Error('Upsert failed'), { status: 400 })
    mockedApi.post.mockRejectedValueOnce(apiError)

    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={createTestQueryClient()}>
        {children}
      </QueryClientProvider>
    )

    const { result } = renderHook(() => useUpsertResidentWeeklyRequirement(), { wrapper })

    result.current.mutate({
      templateId: mockTemplateId,
      data: {
        fmClinicMinPerWeek: 2,
        fmClinicMaxPerWeek: 4,
      },
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error?.message).toBe('Upsert failed')
  })
})
