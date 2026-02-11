/**
 * Tests for useWeeklyPattern hook.
 *
 * Tests cover:
 * - Data fetching and transformation
 * - Mutation success/error handling
 * - Query key management
 * - API integration
 */

import { renderHook, waitFor } from '@/test-utils';
import { createWrapper } from '@/test-utils';

import { createEmptyPattern } from '@/types/weekly-pattern';
import {
  useAvailableTemplates,
  useUpdateWeeklyPattern,
  useWeeklyPattern,
  weeklyPatternQueryKeys,
} from '../useWeeklyPattern';

// ============================================================================
// Mocks
// ============================================================================

const mockGet = jest.fn();
const mockPut = jest.fn();

jest.mock('@/lib/api', () => ({
  get: (...args: unknown[]) => mockGet(...args),
  put: (...args: unknown[]) => mockPut(...args),
}));

// ============================================================================
// Test Data
// ============================================================================

const mockBackendPatterns = [
  {
    id: 'pattern-1',
    rotationTemplateId: 'template-1',
    dayOfWeek: 1,
    timeOfDay: 'AM' as const,
    activityType: 'fm_clinic',
    linkedTemplateId: 'linked-1',
    isProtected: false,
    notes: null,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  },
  {
    id: 'pattern-2',
    rotationTemplateId: 'template-1',
    dayOfWeek: 1,
    timeOfDay: 'PM' as const,
    activityType: 'specialty',
    linkedTemplateId: 'linked-2',
    isProtected: true,
    notes: 'Protected slot',
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  },
];

const mockTemplatesResponse = {
  items: [
    {
      id: 'template-1',
      name: 'Clinic',
      activityType: 'clinic',
      abbreviation: 'C',
      displayAbbreviation: 'Clinic',
      fontColor: 'text-blue-800',
      backgroundColor: 'bg-blue-100',
    },
    {
      id: 'template-2',
      name: 'Inpatient',
      activityType: 'inpatient',
      abbreviation: 'IP',
      displayAbbreviation: null,
      fontColor: null,
      backgroundColor: null,
    },
  ],
  total: 2,
};

// ============================================================================
// Tests
// ============================================================================

beforeEach(() => {
  jest.clearAllMocks();
});

describe('useWeeklyPattern', () => {
  it('should fetch and transform patterns correctly', async () => {
    mockGet.mockResolvedValueOnce(mockBackendPatterns);

    const { result } = renderHook(() => useWeeklyPattern('template-1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    const data = result.current.data;
    expect(data).toBeDefined();
    expect(data?.templateId).toBe('template-1');
    expect(data?.pattern.slots).toHaveLength(14);

    // Check Monday AM slot (day=1, time=AM, index=2)
    const mondayAm = data?.pattern.slots[2];
    expect(mondayAm?.dayOfWeek).toBe(1);
    expect(mondayAm?.timeOfDay).toBe('AM');
    expect(mondayAm?.rotationTemplateId).toBe('linked-1');

    expect(mockGet).toHaveBeenCalledWith('/rotation-templates/template-1/patterns');
  });

  it('should not fetch when templateId is empty', async () => {
    const { result } = renderHook(() => useWeeklyPattern(''), {
      wrapper: createWrapper(),
    });

    // Should not be loading because query is disabled
    expect(result.current.isLoading).toBe(false);
    expect(result.current.isFetching).toBe(false);
    expect(mockGet).not.toHaveBeenCalled();
  });

  it('should handle API error', async () => {
    mockGet.mockRejectedValueOnce(new Error('Template not found'));

    const { result } = renderHook(() => useWeeklyPattern('nonexistent'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
  });

  it('should use correct query keys', () => {
    expect(weeklyPatternQueryKeys.all).toEqual(['weekly-patterns']);
    expect(weeklyPatternQueryKeys.pattern('test-id')).toEqual([
      'weekly-patterns',
      'test-id',
    ]);
    expect(weeklyPatternQueryKeys.templates()).toEqual([
      'weekly-patterns',
      'templates',
    ]);
  });
});

describe('useUpdateWeeklyPattern', () => {
  it('should update patterns and return transformed result', async () => {
    const updatedBackendPatterns = [
      {
        id: 'pattern-new-0',
        rotationTemplateId: 'template-1',
        dayOfWeek: 1,
        timeOfDay: 'AM' as const,
        activityType: 'scheduled',
        linkedTemplateId: 'new-template',
        isProtected: false,
        notes: null,
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-01T00:00:00Z',
      },
    ];
    mockPut.mockResolvedValueOnce(updatedBackendPatterns);

    const { result } = renderHook(() => useUpdateWeeklyPattern(), {
      wrapper: createWrapper(),
    });

    const pattern = createEmptyPattern();
    pattern.slots[2].rotationTemplateId = 'new-template';

    result.current.mutate({
      templateId: 'template-1',
      pattern,
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.templateId).toBe('template-1');
    expect(mockPut).toHaveBeenCalledWith(
      '/rotation-templates/template-1/patterns',
      expect.objectContaining({ patterns: expect.any(Array) })
    );
  });

  it('should handle mutation error', async () => {
    mockPut.mockRejectedValueOnce(new Error('Validation error'));

    const { result } = renderHook(() => useUpdateWeeklyPattern(), {
      wrapper: createWrapper(),
    });

    const pattern = createEmptyPattern();

    result.current.mutate({
      templateId: 'template-1',
      pattern,
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
  });
});

describe('useAvailableTemplates', () => {
  it('should fetch and transform templates correctly', async () => {
    mockGet.mockResolvedValueOnce(mockTemplatesResponse);

    const { result } = renderHook(() => useAvailableTemplates(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    const data = result.current.data;
    expect(data).toBeDefined();
    expect(data).toHaveLength(2);

    const firstTemplate = data?.[0];
    expect(firstTemplate?.id).toBe('template-1');
    expect(firstTemplate?.name).toBe('Clinic');
    expect(firstTemplate?.displayAbbreviation).toBe('Clinic');
    expect(firstTemplate?.backgroundColor).toBe('bg-blue-100');

    // Second template should use abbreviation as fallback
    const secondTemplate = data?.[1];
    expect(secondTemplate?.displayAbbreviation).toBe('IP');
  });

  it('should handle API error', async () => {
    mockGet.mockRejectedValueOnce(new Error('Server error'));

    const { result } = renderHook(() => useAvailableTemplates(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
  });
});
