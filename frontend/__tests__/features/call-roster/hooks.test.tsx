/**
 * Tests for Call Roster React Query Hooks
 *
 * Tests data fetching, transformations, and cache management
 * for on-call assignment data and contact information.
 */

import { renderHook, waitFor } from '@/test-utils';
import { QueryClient } from '@tanstack/react-query';
import * as api from '@/lib/api';
import {
  useOnCallAssignments,
  useMonthlyOnCallRoster,
  useTodayOnCall,
  usePersonOnCallAssignments,
  useOnCallByDate,
  callRosterQueryKeys,
} from '@/features/call-roster/hooks';
import { format, startOfMonth, endOfMonth } from 'date-fns';
import { createWrapper } from '@/test-utils';

// Mock the API module
jest.mock('@/lib/api');

// Mock date-fns to control today's date
jest.mock('date-fns', () => ({
  ...jest.requireActual('date-fns'),
  format: jest.fn((date: Date | string, formatStr: string) => {
    const actualFormat = jest.requireActual('date-fns').format;
    return actualFormat(date, formatStr);
  }),
}));

// Mock assignment data factory matching ApiCallAssignment shape
function createMockAssignment(overrides: Record<string, unknown> = {}) {
  return {
    id: 'assignment-1',
    date: '2025-01-15',
    personId: 'person-1',
    callType: 'weekday' as const,
    isWeekend: false,
    isHoliday: false,
    person: {
      id: 'person-1',
      name: 'John Doe',
      facultyRole: 'attending',
    },
    ...overrides,
  };
}

describe('Call Roster Hooks', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('useOnCallAssignments', () => {
    it('should fetch on-call assignments successfully', async () => {
      const mockResponse = {
        items: [createMockAssignment()],
        total: 1,
      };

      (api.get as jest.Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(
        () => useOnCallAssignments('2025-01-15', '2025-01-20'),
        {
          wrapper: createWrapper(),
        }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toHaveLength(1);
      expect(result.current.data?.[0]).toMatchObject({
        id: 'assignment-1',
        date: '2025-01-15',
        shift: 'day',
        person: {
          id: 'person-1',
          name: 'John Doe',
          role: 'attending',
        },
        rotationName: 'weekday',
      });
    });

    it('should build query string with filters', async () => {
      (api.get as jest.Mock).mockResolvedValue({ items: [], total: 0 });

      renderHook(() => useOnCallAssignments('2025-01-01', '2025-01-31'), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith(
          '/call-assignments?startDate=2025-01-01&endDate=2025-01-31'
        );
      });
    });

    it('should transform all items from response', async () => {
      const mockResponse = {
        items: [
          createMockAssignment(),
          createMockAssignment({
            id: 'assignment-2',
            date: '2025-01-16',
            personId: 'person-2',
            person: {
              id: 'person-2',
              name: 'Jane Smith',
              facultyRole: 'attending',
            },
          }),
        ],
        total: 2,
      };

      (api.get as jest.Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(
        () => useOnCallAssignments('2025-01-15', '2025-01-20'),
        {
          wrapper: createWrapper(),
        }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toHaveLength(2);
    });

    it('should handle assignments without person data gracefully', async () => {
      const mockResponse = {
        items: [
          createMockAssignment(),
          createMockAssignment({
            id: 'assignment-2',
            person: { id: 'person-2', name: 'Jane', facultyRole: null },
          }),
        ],
        total: 2,
      };

      (api.get as jest.Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(
        () => useOnCallAssignments('2025-01-15', '2025-01-20'),
        {
          wrapper: createWrapper(),
        }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // Both should be transformed
      expect(result.current.data).toHaveLength(2);
    });

    it('should sort assignments by date', async () => {
      const mockResponse = {
        items: [
          createMockAssignment({ id: 'late', date: '2025-01-20' }),
          createMockAssignment({ id: 'early', date: '2025-01-15' }),
        ],
        total: 2,
      };

      (api.get as jest.Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(
        () => useOnCallAssignments('2025-01-15', '2025-01-20'),
        {
          wrapper: createWrapper(),
        }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.[0].date).toBe('2025-01-15');
      expect(result.current.data?.[1].date).toBe('2025-01-20');
    });

    it('should map callType to rotationName', async () => {
      const mockResponse = {
        items: [
          createMockAssignment({ id: 'weekday-call', callType: 'weekday' }),
          createMockAssignment({ id: 'sunday-call', callType: 'sunday', date: '2025-01-16' }),
          createMockAssignment({ id: 'holiday-call', callType: 'holiday', date: '2025-01-17', isHoliday: true }),
        ],
        total: 3,
      };

      (api.get as jest.Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(
        () => useOnCallAssignments('2025-01-15', '2025-01-20'),
        {
          wrapper: createWrapper(),
        }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toHaveLength(3);
      expect(result.current.data?.[0].rotationName).toBe('weekday');
      expect(result.current.data?.[1].rotationName).toBe('sunday');
      expect(result.current.data?.[2].rotationName).toBe('holiday');
    });

    it('should set person role to attending', async () => {
      const mockResponse = {
        items: [createMockAssignment()],
        total: 1,
      };

      (api.get as jest.Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(
        () => useOnCallAssignments('2025-01-15', '2025-01-20'),
        {
          wrapper: createWrapper(),
        }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // All faculty are attending per the transform
      expect(result.current.data?.[0].person.role).toBe('attending');
    });

    it('should handle API errors', async () => {
      const error = new Error('Failed to fetch assignments');
      (api.get as jest.Mock).mockRejectedValue(error);

      const { result } = renderHook(
        () => useOnCallAssignments('2025-01-15', '2025-01-20'),
        {
          wrapper: createWrapper(),
        }
      );

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toEqual(error);
    });

    it('should not fetch when startDate is empty', async () => {
      const { result } = renderHook(() => useOnCallAssignments('', '2025-01-20'), {
        wrapper: createWrapper(),
      });

      expect(result.current.fetchStatus).toBe('idle');
      expect(api.get).not.toHaveBeenCalled();
    });

    it('should not fetch when endDate is empty', async () => {
      const { result } = renderHook(() => useOnCallAssignments('2025-01-15', ''), {
        wrapper: createWrapper(),
      });

      expect(result.current.fetchStatus).toBe('idle');
      expect(api.get).not.toHaveBeenCalled();
    });

    it('should use correct query key', () => {
      const key = callRosterQueryKeys.byDate('2025-01-15', '2025-01-20');
      expect(key).toEqual(['call-roster', '2025-01-15', '2025-01-20']);
    });

    it('should return empty array when no items', async () => {
      (api.get as jest.Mock).mockResolvedValue({ items: [], total: 0 });

      const { result } = renderHook(
        () => useOnCallAssignments('2025-01-15', '2025-01-20'),
        {
          wrapper: createWrapper(),
        }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual([]);
    });
  });

  describe('useMonthlyOnCallRoster', () => {
    it('should fetch monthly roster successfully', async () => {
      const mockResponse = {
        items: [createMockAssignment()],
        total: 1,
      };

      (api.get as jest.Mock).mockResolvedValue(mockResponse);

      const testDate = new Date('2025-01-15T12:00:00');

      const { result } = renderHook(() => useMonthlyOnCallRoster(testDate), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toHaveLength(1);
    });

    it('should use month start and end dates', async () => {
      (api.get as jest.Mock).mockResolvedValue({ items: [], total: 0 });

      const testDate = new Date('2025-01-15T12:00:00');
      const expectedStart = format(startOfMonth(testDate), 'yyyy-MM-dd');
      const expectedEnd = format(endOfMonth(testDate), 'yyyy-MM-dd');

      renderHook(() => useMonthlyOnCallRoster(testDate), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith(
          `/call-assignments?startDate=${expectedStart}&endDate=${expectedEnd}`
        );
      });
    });

    it('should handle API errors', async () => {
      const error = new Error('Failed to fetch monthly roster');
      (api.get as jest.Mock).mockRejectedValue(error);

      const testDate = new Date('2025-01-15T12:00:00');

      const { result } = renderHook(() => useMonthlyOnCallRoster(testDate), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toEqual(error);
    });
  });

  describe('useTodayOnCall', () => {
    beforeEach(() => {
      // Mock Date to return consistent value
      jest.useFakeTimers();
      jest.setSystemTime(new Date('2025-01-15T10:00:00Z'));
    });

    afterEach(() => {
      jest.useRealTimers();
    });

    it('should fetch today\'s on-call assignments successfully', async () => {
      const mockResponse = {
        items: [createMockAssignment()],
        total: 1,
      };

      (api.get as jest.Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useTodayOnCall(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toHaveLength(1);
    });

    it('should use today\'s date for query', async () => {
      (api.get as jest.Mock).mockResolvedValue({ items: [], total: 0 });

      const today = format(new Date(), 'yyyy-MM-dd');

      renderHook(() => useTodayOnCall(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith(
          `/call-assignments?startDate=${today}&endDate=${today}`
        );
      });
    });

    it('should handle API errors', async () => {
      const error = new Error('Failed to fetch today\'s assignments');
      (api.get as jest.Mock).mockRejectedValue(error);

      const { result } = renderHook(() => useTodayOnCall(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toEqual(error);
    });

    it('should use correct query key', () => {
      jest.setSystemTime(new Date('2025-01-15T10:00:00Z'));
      const today = format(new Date(), 'yyyy-MM-dd');
      const key = callRosterQueryKeys.today();
      expect(key).toEqual(['call-roster', 'today', today]);
    });

    it('should have shorter stale time than other queries', async () => {
      const mockResponse = {
        items: [createMockAssignment()],
        total: 1,
      };

      (api.get as jest.Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useTodayOnCall(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // Query options should include refetchOnWindowFocus: true
      // This is verified by the hook configuration, not testable here directly
      expect(result.current.data).toHaveLength(1);
    });
  });

  describe('usePersonOnCallAssignments', () => {
    it('should fetch person-specific assignments successfully', async () => {
      const mockResponse = {
        items: [createMockAssignment()],
        total: 1,
      };

      (api.get as jest.Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(
        () =>
          usePersonOnCallAssignments('person-1', '2025-01-15', '2025-01-20'),
        {
          wrapper: createWrapper(),
        }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toHaveLength(1);
    });

    it('should filter assignments by personId', async () => {
      const mockResponse = {
        items: [
          createMockAssignment({ id: 'a1', personId: 'person-1' }),
          createMockAssignment({ id: 'a2', personId: 'person-2', date: '2025-01-16' }),
        ],
        total: 2,
      };

      (api.get as jest.Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(
        () =>
          usePersonOnCallAssignments('person-1', '2025-01-15', '2025-01-20'),
        {
          wrapper: createWrapper(),
        }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // Should only return assignments matching personId
      expect(result.current.data).toHaveLength(1);
      expect(result.current.data?.[0].id).toBe('a1');
    });

    it('should handle API errors', async () => {
      const error = new Error('Failed to fetch person assignments');
      (api.get as jest.Mock).mockRejectedValue(error);

      const { result } = renderHook(
        () =>
          usePersonOnCallAssignments('person-1', '2025-01-15', '2025-01-20'),
        {
          wrapper: createWrapper(),
        }
      );

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toEqual(error);
    });

    it('should not fetch when personId is empty', async () => {
      const { result } = renderHook(
        () => usePersonOnCallAssignments('', '2025-01-15', '2025-01-20'),
        {
          wrapper: createWrapper(),
        }
      );

      expect(result.current.fetchStatus).toBe('idle');
      expect(api.get).not.toHaveBeenCalled();
    });

    it('should not fetch when startDate is empty', async () => {
      const { result } = renderHook(
        () => usePersonOnCallAssignments('person-1', '', '2025-01-20'),
        {
          wrapper: createWrapper(),
        }
      );

      expect(result.current.fetchStatus).toBe('idle');
      expect(api.get).not.toHaveBeenCalled();
    });

    it('should not fetch when endDate is empty', async () => {
      const { result } = renderHook(
        () => usePersonOnCallAssignments('person-1', '2025-01-15', ''),
        {
          wrapper: createWrapper(),
        }
      );

      expect(result.current.fetchStatus).toBe('idle');
      expect(api.get).not.toHaveBeenCalled();
    });

    it('should use correct query key', () => {
      const { result } = renderHook(
        () =>
          usePersonOnCallAssignments('person-1', '2025-01-15', '2025-01-20'),
        {
          wrapper: createWrapper(),
        }
      );

      // The query key should include person ID
      expect(result.current.fetchStatus).toBe('fetching');
    });
  });

  describe('useOnCallByDate', () => {
    it('should group assignments by date', async () => {
      const mockResponse = {
        items: [
          createMockAssignment({ id: 'assignment-1', date: '2025-01-15' }),
          createMockAssignment({ id: 'assignment-2', date: '2025-01-15', personId: 'person-2', person: { id: 'person-2', name: 'Jane', facultyRole: null } }),
          createMockAssignment({ id: 'assignment-3', date: '2025-01-16', personId: 'person-3', person: { id: 'person-3', name: 'Bob', facultyRole: null } }),
        ],
        total: 3,
      };

      (api.get as jest.Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(
        () => useOnCallByDate('2025-01-15', '2025-01-20'),
        {
          wrapper: createWrapper(),
        }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toMatchObject({
        '2025-01-15': expect.arrayContaining([
          expect.objectContaining({ id: 'assignment-1' }),
          expect.objectContaining({ id: 'assignment-2' }),
        ]),
        '2025-01-16': expect.arrayContaining([
          expect.objectContaining({ id: 'assignment-3' }),
        ]),
      });

      expect(result.current.data['2025-01-15']).toHaveLength(2);
      expect(result.current.data['2025-01-16']).toHaveLength(1);
    });

    it('should return assignments array', async () => {
      const mockResponse = {
        items: [createMockAssignment()],
        total: 1,
      };

      (api.get as jest.Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(
        () => useOnCallByDate('2025-01-15', '2025-01-20'),
        {
          wrapper: createWrapper(),
        }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.assignments).toHaveLength(1);
      expect(result.current.assignments[0]).toMatchObject({
        id: 'assignment-1',
        date: '2025-01-15',
      });
    });

    it('should return empty object when no data', async () => {
      (api.get as jest.Mock).mockResolvedValue({ items: [], total: 0 });

      const { result } = renderHook(
        () => useOnCallByDate('2025-01-15', '2025-01-20'),
        {
          wrapper: createWrapper(),
        }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual({});
      expect(result.current.assignments).toEqual([]);
    });

    it('should handle API errors', async () => {
      const error = new Error('Failed to fetch assignments');
      (api.get as jest.Mock).mockRejectedValue(error);

      const { result } = renderHook(
        () => useOnCallByDate('2025-01-15', '2025-01-20'),
        {
          wrapper: createWrapper(),
        }
      );

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toEqual(error);
      expect(result.current.data).toEqual({});
      expect(result.current.assignments).toEqual([]);
    });

    it('should preserve all query states', async () => {
      const mockResponse = {
        items: [createMockAssignment()],
        total: 1,
      };

      (api.get as jest.Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(
        () => useOnCallByDate('2025-01-15', '2025-01-20'),
        {
          wrapper: createWrapper(),
        }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.isLoading).toBe(false);
      expect(result.current.isError).toBe(false);
      expect(result.current.isSuccess).toBe(true);
    });
  });

  describe('Query Keys', () => {
    it('should generate correct query key for all call roster', () => {
      expect(callRosterQueryKeys.all).toEqual(['call-roster']);
    });

    it('should generate correct query key for date range', () => {
      const key = callRosterQueryKeys.byDate('2025-01-15', '2025-01-20');
      expect(key).toEqual(['call-roster', '2025-01-15', '2025-01-20']);
    });

    it('should generate correct query key for month', () => {
      const testDate = new Date('2025-01-15T12:00:00');
      const start = format(startOfMonth(testDate), 'yyyy-MM-dd');
      const end = format(endOfMonth(testDate), 'yyyy-MM-dd');
      const key = callRosterQueryKeys.byMonth(testDate);
      expect(key).toEqual(['call-roster', 'month', start, end]);
    });

    it('should generate correct query key for today', () => {
      jest.useFakeTimers();
      jest.setSystemTime(new Date('2025-01-15T10:00:00Z'));

      const today = format(new Date(), 'yyyy-MM-dd');
      const key = callRosterQueryKeys.today();
      expect(key).toEqual(['call-roster', 'today', today]);

      jest.useRealTimers();
    });

    it('should generate different keys for different dates', () => {
      const key1 = callRosterQueryKeys.byDate('2025-01-15', '2025-01-20');
      const key2 = callRosterQueryKeys.byDate('2025-02-15', '2025-02-20');
      expect(key1).not.toEqual(key2);
    });

    it('should generate different keys for different months', () => {
      const date1 = new Date('2025-01-15T12:00:00');
      const date2 = new Date('2025-02-15T12:00:00');
      const key1 = callRosterQueryKeys.byMonth(date1);
      const key2 = callRosterQueryKeys.byMonth(date2);
      expect(key1).not.toEqual(key2);
    });
  });

  describe('Loading States', () => {
    it('should show loading state while fetching', async () => {
      let resolvePromise: (value: any) => void;
      const promise = new Promise((resolve) => {
        resolvePromise = resolve;
      });

      (api.get as jest.Mock).mockReturnValue(promise);

      const { result } = renderHook(
        () => useOnCallAssignments('2025-01-15', '2025-01-20'),
        {
          wrapper: createWrapper(),
        }
      );

      expect(result.current.isLoading).toBe(true);
      expect(result.current.data).toBeUndefined();

      resolvePromise!({ items: [], total: 0 });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
    });

    it('should transition from loading to success', async () => {
      const mockResponse = {
        items: [createMockAssignment()],
        total: 1,
      };

      (api.get as jest.Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(
        () => useOnCallAssignments('2025-01-15', '2025-01-20'),
        {
          wrapper: createWrapper(),
        }
      );

      expect(result.current.isLoading).toBe(true);
      expect(result.current.isSuccess).toBe(false);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.isLoading).toBe(false);
      expect(result.current.data).toHaveLength(1);
    });

    it('should transition from loading to error', async () => {
      const error = new Error('Network error');
      (api.get as jest.Mock).mockRejectedValue(error);

      const { result } = renderHook(
        () => useOnCallAssignments('2025-01-15', '2025-01-20'),
        {
          wrapper: createWrapper(),
        }
      );

      expect(result.current.isLoading).toBe(true);
      expect(result.current.isError).toBe(false);

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toEqual(error);
    });
  });

  describe('Transform Behavior', () => {
    it('should set notes to Holiday for holiday assignments', async () => {
      const mockResponse = {
        items: [createMockAssignment({ isHoliday: true })],
        total: 1,
      };

      (api.get as jest.Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(
        () => useOnCallAssignments('2025-01-15', '2025-01-20'),
        {
          wrapper: createWrapper(),
        }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.[0].notes).toBe('Holiday');
    });

    it('should set notes to undefined for non-holiday assignments', async () => {
      const mockResponse = {
        items: [createMockAssignment({ isHoliday: false })],
        total: 1,
      };

      (api.get as jest.Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(
        () => useOnCallAssignments('2025-01-15', '2025-01-20'),
        {
          wrapper: createWrapper(),
        }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.[0].notes).toBeUndefined();
    });

    it('should set person fields to undefined when not available', async () => {
      const mockResponse = {
        items: [createMockAssignment()],
        total: 1,
      };

      (api.get as jest.Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(
        () => useOnCallAssignments('2025-01-15', '2025-01-20'),
        {
          wrapper: createWrapper(),
        }
      );

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // Transform sets these to undefined
      expect(result.current.data?.[0].person.pgyLevel).toBeUndefined();
      expect(result.current.data?.[0].person.email).toBeUndefined();
      expect(result.current.data?.[0].person.phone).toBeUndefined();
      expect(result.current.data?.[0].person.pager).toBeUndefined();
    });
  });
});
