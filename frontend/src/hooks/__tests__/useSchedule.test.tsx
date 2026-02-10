/**
 * Tests for useSchedule hooks.
 *
 * Tests cover:
 * - Query key structure
 * - useSchedule: schedule fetching by date range
 * - useValidateSchedule: schedule validation
 * - useRotationTemplates: rotation template listing
 * - useRotationTemplate: single template fetch
 * - useAssignments: filtered assignment queries
 * - useGenerateSchedule: schedule generation mutation
 * - useCreateAssignment: assignment creation mutation
 * - useUpdateAssignment: assignment update mutation
 * - useDeleteAssignment: assignment deletion mutation
 * - useCreateTemplate: template creation mutation
 * - useUpdateTemplate: template update mutation
 * - useDeleteTemplate: template deletion mutation
 * - Error handling
 */

import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';

import {
  useSchedule,
  useValidateSchedule,
  useRotationTemplates,
  useRotationTemplate,
  useAssignments,
  useGenerateSchedule,
  useCreateAssignment,
  useUpdateAssignment,
  useDeleteAssignment,
  useCreateTemplate,
  useUpdateTemplate,
  useDeleteTemplate,
  scheduleQueryKeys,
} from '../useSchedule';

// ============================================================================
// Mocks
// ============================================================================

jest.mock('@/lib/api', () => ({
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  del: jest.fn(),
}));

import { get, post, put, del } from '@/lib/api';

const mockGet = get as jest.Mock;
const mockPost = post as jest.Mock;
const mockPut = put as jest.Mock;
const mockDel = del as jest.Mock;

// ============================================================================
// Test Setup
// ============================================================================

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  });

  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
}

// ============================================================================
// Test Data
// ============================================================================

const mockAssignment = {
  id: 'assign-1',
  blockId: 'block-1',
  personId: 'person-1',
  rotationTemplateId: 'rt-1',
  role: 'primary',
  activityOverride: null,
  notes: null,
  createdBy: null,
  createdAt: '2025-01-01T00:00:00Z',
  updatedAt: '2025-01-01T00:00:00Z',
};

const mockAssignmentListResponse = {
  items: [mockAssignment],
  total: 1,
};

const mockRotationTemplate = {
  id: 'rt-1',
  name: 'Family Medicine Clinic',
  activityType: 'clinic',
  abbreviation: 'FMC',
  displayAbbreviation: 'FMC',
  fontColor: null,
  backgroundColor: null,
  clinicLocation: 'Building A',
  maxResidents: 4,
  requiresSpecialty: null,
  requiresProcedureCredential: false,
  supervisionRequired: true,
  maxSupervisionRatio: 4,
  createdAt: '2025-01-01T00:00:00Z',
};

const mockValidationResult = {
  valid: true,
  totalViolations: 0,
  violations: [],
  coverageRate: 0.95,
  statistics: null,
};

const mockGenerateResponse = {
  status: 'success',
  message: 'Schedule generated successfully',
  totalBlocks_assigned: 100,
  totalBlocks: 105,
  validation: mockValidationResult,
  run_id: 'run-1',
  solverStats: {
    totalResidents: 18,
    coverageRate: 0.95,
  },
};

// ============================================================================
// Query Keys Tests
// ============================================================================

describe('scheduleQueryKeys', () => {
  it('should generate correct schedule key', () => {
    expect(scheduleQueryKeys.schedule('2025-01-01', '2025-01-31')).toEqual([
      'schedule', '2025-01-01', '2025-01-31',
    ]);
  });

  it('should generate correct rotationTemplates key', () => {
    expect(scheduleQueryKeys.rotationTemplates()).toEqual([
      'rotation-templates', undefined,
    ]);
    expect(scheduleQueryKeys.rotationTemplates('clinic')).toEqual([
      'rotation-templates', 'clinic',
    ]);
  });

  it('should generate correct rotationTemplate key', () => {
    expect(scheduleQueryKeys.rotationTemplate('rt-1')).toEqual([
      'rotation-templates', 'rt-1',
    ]);
  });

  it('should generate correct validation key', () => {
    expect(scheduleQueryKeys.validation('2025-01-01', '2025-01-31')).toEqual([
      'validation', '2025-01-01', '2025-01-31',
    ]);
  });

  it('should generate correct assignments key with filters', () => {
    const filters = { personId: 'person-1', startDate: '2025-01-01' };
    expect(scheduleQueryKeys.assignments(filters)).toEqual([
      'assignments', filters,
    ]);
  });
});

// ============================================================================
// useSchedule Tests
// ============================================================================

describe('useSchedule', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch schedule for date range', async () => {
    mockGet.mockResolvedValueOnce(mockAssignmentListResponse);

    const startDate = new Date('2025-01-01');
    const endDate = new Date('2025-01-31');

    const { result } = renderHook(
      () => useSchedule(startDate, endDate),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    const url = mockGet.mock.calls[0][0] as string;
    expect(url).toContain('/assignments?');
    expect(url).toContain('start_date=2025-01-01');
    expect(url).toContain('end_date=2025-01-31');
    expect(url).toContain('page_size=5000');

    expect(result.current.data?.items).toHaveLength(1);
    expect(result.current.data?.total).toBe(1);
  });

  it('should handle API error', async () => {
    mockGet.mockRejectedValueOnce({ message: 'Server error', status: 500 });

    const { result } = renderHook(
      () => useSchedule(new Date('2025-01-01'), new Date('2025-01-31')),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
  });
});

// ============================================================================
// useValidateSchedule Tests
// ============================================================================

describe('useValidateSchedule', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch validation results', async () => {
    mockGet.mockResolvedValueOnce(mockValidationResult);

    const { result } = renderHook(
      () => useValidateSchedule('2025-01-01', '2025-01-31'),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    const url = mockGet.mock.calls[0][0] as string;
    expect(url).toContain('/schedule/validate?');
    expect(url).toContain('start_date=2025-01-01');
    expect(url).toContain('end_date=2025-01-31');

    expect(result.current.data?.valid).toBe(true);
    expect(result.current.data?.totalViolations).toBe(0);
  });
});

// ============================================================================
// useRotationTemplates Tests
// ============================================================================

describe('useRotationTemplates', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch all rotation templates', async () => {
    const mockResponse = { items: [mockRotationTemplate], total: 1 };
    mockGet.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(() => useRotationTemplates(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith('/rotation-templates');
    expect(result.current.data?.items).toHaveLength(1);
    expect(result.current.data?.items[0].name).toBe('Family Medicine Clinic');
  });
});

// ============================================================================
// useRotationTemplate Tests
// ============================================================================

describe('useRotationTemplate', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch a single rotation template', async () => {
    mockGet.mockResolvedValueOnce(mockRotationTemplate);

    const { result } = renderHook(() => useRotationTemplate('rt-1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith('/rotation-templates/rt-1');
    expect(result.current.data?.id).toBe('rt-1');
    expect(result.current.data?.name).toBe('Family Medicine Clinic');
  });

  it('should not fetch when id is empty', () => {
    const { result } = renderHook(() => useRotationTemplate(''), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.isFetching).toBe(false);
    expect(mockGet).not.toHaveBeenCalled();
  });
});

// ============================================================================
// useAssignments Tests
// ============================================================================

describe('useAssignments', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch assignments without filters', async () => {
    mockGet.mockResolvedValueOnce(mockAssignmentListResponse);

    const { result } = renderHook(() => useAssignments(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith('/assignments');
    expect(result.current.data?.items).toHaveLength(1);
  });

  it('should pass filters as query params', async () => {
    mockGet.mockResolvedValueOnce(mockAssignmentListResponse);

    const { result } = renderHook(
      () =>
        useAssignments({
          startDate: '2025-01-01',
          endDate: '2025-01-31',
          personId: 'person-1',
          role: 'primary',
          pageSize: 50,
        }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    const url = mockGet.mock.calls[0][0] as string;
    expect(url).toContain('start_date=2025-01-01');
    expect(url).toContain('end_date=2025-01-31');
    expect(url).toContain('person_id=person-1');
    expect(url).toContain('role=primary');
    expect(url).toContain('page_size=50');
  });
});

// ============================================================================
// useGenerateSchedule Tests
// ============================================================================

describe('useGenerateSchedule', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should generate a schedule', async () => {
    mockPost.mockResolvedValueOnce(mockGenerateResponse);

    const { result } = renderHook(() => useGenerateSchedule(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        startDate: '2025-01-01',
        endDate: '2025-06-30',
        algorithm: 'hybrid',
        timeout_seconds: 300,
      });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockPost).toHaveBeenCalledWith('/schedule/generate', {
      startDate: '2025-01-01',
      endDate: '2025-06-30',
      algorithm: 'hybrid',
      timeout_seconds: 300,
    });

    expect(result.current.data?.status).toBe('success');
    expect(result.current.data?.totalBlocks_assigned).toBe(100);
  });

  it('should handle generation error', async () => {
    mockPost.mockRejectedValueOnce({
      message: 'Generation already in progress',
      status: 409,
    });

    const { result } = renderHook(() => useGenerateSchedule(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        startDate: '2025-01-01',
        endDate: '2025-06-30',
      });
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
  });
});

// ============================================================================
// useCreateAssignment Tests
// ============================================================================

describe('useCreateAssignment', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should create an assignment', async () => {
    mockPost.mockResolvedValueOnce(mockAssignment);

    const { result } = renderHook(() => useCreateAssignment(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        blockId: 'block-1',
        personId: 'person-1',
        role: 'primary',
      });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockPost).toHaveBeenCalledWith('/assignments', {
      blockId: 'block-1',
      personId: 'person-1',
      role: 'primary',
    });
    expect(result.current.data?.id).toBe('assign-1');
  });
});

// ============================================================================
// useUpdateAssignment Tests
// ============================================================================

describe('useUpdateAssignment', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should update an assignment', async () => {
    const updated = { ...mockAssignment, personId: 'person-2' };
    mockPut.mockResolvedValueOnce(updated);

    const { result } = renderHook(() => useUpdateAssignment(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        id: 'assign-1',
        data: { personId: 'person-2' },
      });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockPut).toHaveBeenCalledWith('/assignments/assign-1', {
      personId: 'person-2',
    });
    expect(result.current.data?.personId).toBe('person-2');
  });
});

// ============================================================================
// useDeleteAssignment Tests
// ============================================================================

describe('useDeleteAssignment', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should delete an assignment', async () => {
    mockDel.mockResolvedValueOnce(undefined);

    const { result } = renderHook(() => useDeleteAssignment(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate('assign-1');
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockDel).toHaveBeenCalledWith('/assignments/assign-1');
  });
});

// ============================================================================
// useCreateTemplate Tests
// ============================================================================

describe('useCreateTemplate', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should create a rotation template', async () => {
    mockPost.mockResolvedValueOnce(mockRotationTemplate);

    const { result } = renderHook(() => useCreateTemplate(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        name: 'Family Medicine Clinic',
        activityType: 'clinic',
      });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockPost).toHaveBeenCalledWith('/rotation-templates', {
      name: 'Family Medicine Clinic',
      activityType: 'clinic',
    });
    expect(result.current.data?.id).toBe('rt-1');
  });
});

// ============================================================================
// useUpdateTemplate Tests
// ============================================================================

describe('useUpdateTemplate', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should update a rotation template', async () => {
    const updated = { ...mockRotationTemplate, name: 'Updated Clinic' };
    mockPut.mockResolvedValueOnce(updated);

    const { result } = renderHook(() => useUpdateTemplate(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        id: 'rt-1',
        data: { name: 'Updated Clinic' },
      });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockPut).toHaveBeenCalledWith('/rotation-templates/rt-1', {
      name: 'Updated Clinic',
    });
    expect(result.current.data?.name).toBe('Updated Clinic');
  });
});

// ============================================================================
// useDeleteTemplate Tests
// ============================================================================

describe('useDeleteTemplate', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should delete a rotation template', async () => {
    mockDel.mockResolvedValueOnce(undefined);

    const { result } = renderHook(() => useDeleteTemplate(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate('rt-1');
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockDel).toHaveBeenCalledWith('/rotation-templates/rt-1');
  });

  it('should handle deletion error for in-use template', async () => {
    mockDel.mockRejectedValueOnce({
      message: 'Cannot delete: template in use',
      status: 409,
    });

    const { result } = renderHook(() => useDeleteTemplate(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate('rt-1');
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
  });
});
