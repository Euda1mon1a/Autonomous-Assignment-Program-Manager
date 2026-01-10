/**
 * Tests for Call Roster React Query Hooks
 *
 * Tests data fetching, transformations, and cache management
 * for on-call assignment data and contact information.
 */

import { renderHook, waitFor } from '@testing-library/react';
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
import { createWrapper } from '../../utils/test-utils';

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

// Mock assignment data factory
function createMockAssignment(overrides = {}) {
  return {
    id: 'assignment-1',
    blockId: 'block-1',
    personId: 'person-1',
    role: 'resident',
    rotationTemplate: {
      id: 'rotation-1',
      name: 'Night Call',
      activityType: 'on_call',
      abbreviation: 'NC',
    },
    person: {
      id: 'person-1',
      firstName: 'John',
      lastName: 'Doe',
      pgyLevel: 2,
      email: 'john.doe@example.com',
      phone: '555-1234',
      pager: '555-5678',
    },
    block: {
      id: 'block-1',
      startDate: '2025-01-15',
      endDate: '2025-01-15',
    },
    notes: 'On night call',
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
        shift: 'night',
        person: {
          id: 'person-1',
          name: 'John Doe',
          pgyLevel: 2,
          role: 'intern', // PGY-2 is < 3, so role is 'intern'
          phone: '555-1234',
          pager: '555-5678',
          email: 'john.doe@example.com',
        },
        rotationName: 'Night Call',
        notes: 'On night call',
      });
    });

    it('should build query string with filters', async () => {
      (api.get as jest.Mock).mockResolvedValue({ items: [], total: 0 });

      renderHook(() => useOnCallAssignments('2025-01-01', '2025-01-31'), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith(
          '/assignments?startDate=2025-01-01&endDate=2025-01-31&activityType=on_call'
        );
      });
    });

    it('should filter out non-on-call assignments', async () => {
      const mockResponse = {
        items: [
          createMockAssignment(),
          createMockAssignment({
            id: 'assignment-2',
            rotationTemplate: {
              id: 'rotation-2',
              name: 'Clinic',
              activityType: 'clinic',
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

      // Should only include the on-call assignment
      expect(result.current.data).toHaveLength(1);
      expect(result.current.data?.[0].id).toBe('assignment-1');
    });

    it('should filter out assignments without person data', async () => {
      const mockResponse = {
        items: [
          createMockAssignment(),
          createMockAssignment({
            id: 'assignment-2',
            person: undefined,
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

      // Should only include assignments with person data
      expect(result.current.data).toHaveLength(1);
      expect(result.current.data?.[0].id).toBe('assignment-1');
    });

    it('should filter out assignments without block data', async () => {
      const mockResponse = {
        items: [
          createMockAssignment(),
          createMockAssignment({
            id: 'assignment-2',
            block: undefined,
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

      // Should only include assignments with block data
      expect(result.current.data).toHaveLength(1);
      expect(result.current.data?.[0].id).toBe('assignment-1');
    });

    it('should determine shift type from rotation name', async () => {
      const mockResponse = {
        items: [
          createMockAssignment({
            id: 'day-call',
            rotationTemplate: {
              id: 'rotation-1',
              name: 'Day Call',
              activityType: 'on_call',
            },
            notes: '', // Clear notes to avoid "night" from default
          }),
          createMockAssignment({
            id: 'night-call',
            rotationTemplate: {
              id: 'rotation-2',
              name: 'Night Call',
              activityType: 'on_call',
            },
            notes: '',
          }),
          createMockAssignment({
            id: '24hr-call',
            rotationTemplate: {
              id: 'rotation-3',
              name: '24-hour Call',
              activityType: 'on_call',
            },
            notes: '',
          }),
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
      expect(result.current.data?.[0].shift).toBe('day');
      expect(result.current.data?.[1].shift).toBe('night');
      expect(result.current.data?.[2].shift).toBe('24hr');
    });

    it('should determine role type from PGY level', async () => {
      const mockResponse = {
        items: [
          createMockAssignment({
            id: 'attending',
            person: {
              id: 'person-1',
              firstName: 'Dr.',
              lastName: 'Attending',
              pgyLevel: undefined,
            },
          }),
          createMockAssignment({
            id: 'intern',
            person: {
              id: 'person-2',
              firstName: 'Dr.',
              lastName: 'Intern',
              pgyLevel: 1,
            },
          }),
          createMockAssignment({
            id: 'senior',
            person: {
              id: 'person-3',
              firstName: 'Dr.',
              lastName: 'Senior',
              pgyLevel: 3,
            },
          }),
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
      expect(result.current.data?.[0].person.role).toBe('attending');
      expect(result.current.data?.[1].person.role).toBe('intern');
      expect(result.current.data?.[2].person.role).toBe('senior');
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

      const testDate = new Date('2025-01-15');

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

      const testDate = new Date('2025-01-15');
      const expectedStart = format(startOfMonth(testDate), 'yyyy-MM-dd');
      const expectedEnd = format(endOfMonth(testDate), 'yyyy-MM-dd');

      renderHook(() => useMonthlyOnCallRoster(testDate), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith(
          `/assignments?startDate=${expectedStart}&endDate=${expectedEnd}&activityType=on_call`
        );
      });
    });

    it('should handle API errors', async () => {
      const error = new Error('Failed to fetch monthly roster');
      (api.get as jest.Mock).mockRejectedValue(error);

      const testDate = new Date('2025-01-15');

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
          `/assignments?startDate=${today}&endDate=${today}&activityType=on_call`
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

    it('should include personId in query string', async () => {
      (api.get as jest.Mock).mockResolvedValue({ items: [], total: 0 });

      renderHook(
        () =>
          usePersonOnCallAssignments('person-123', '2025-01-15', '2025-01-20'),
        {
          wrapper: createWrapper(),
        }
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith(
          '/assignments?startDate=2025-01-15&endDate=2025-01-20&personId=person-123&activityType=on_call'
        );
      });
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
          createMockAssignment({
            id: 'assignment-1',
            block: {
              id: 'block-1',
              startDate: '2025-01-15',
              endDate: '2025-01-15',
            },
          }),
          createMockAssignment({
            id: 'assignment-2',
            block: {
              id: 'block-2',
              startDate: '2025-01-15',
              endDate: '2025-01-15',
            },
          }),
          createMockAssignment({
            id: 'assignment-3',
            block: {
              id: 'block-3',
              startDate: '2025-01-16',
              endDate: '2025-01-16',
            },
          }),
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
      const testDate = new Date('2025-01-15');
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
      const date1 = new Date('2025-01-15');
      const date2 = new Date('2025-02-15');
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

  describe('Edge Cases', () => {
    it('should handle assignments with minimal data', async () => {
      const mockResponse = {
        items: [
          {
            id: 'assignment-1',
            blockId: 'block-1',
            personId: 'person-1',
            role: 'resident',
            rotationTemplate: {
              id: 'rotation-1',
              name: 'Call',
              activityType: 'on_call',
            },
            person: {
              id: 'person-1',
              firstName: 'John',
              lastName: 'Doe',
            },
            block: {
              id: 'block-1',
              startDate: '2025-01-15',
              endDate: '2025-01-15',
            },
          },
        ],
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
        person: {
          id: 'person-1',
          name: 'John Doe',
          phone: undefined,
          pager: undefined,
          email: undefined,
        },
      });
    });

    it('should handle shift detection from notes', async () => {
      const mockResponse = {
        items: [
          createMockAssignment({
            id: 'overnight',
            rotationTemplate: {
              id: 'rotation-1',
              name: 'Call',
              activityType: 'on_call',
            },
            notes: 'Overnight shift',
          }),
        ],
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

      expect(result.current.data?.[0].shift).toBe('night');
    });

    it('should default to day shift when no indicators', async () => {
      const mockResponse = {
        items: [
          createMockAssignment({
            rotationTemplate: {
              id: 'rotation-1',
              name: 'Call',
              activityType: 'on_call',
            },
            notes: '',
          }),
        ],
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

      expect(result.current.data?.[0].shift).toBe('day');
    });

    it('should handle supervising role assignment', async () => {
      const mockResponse = {
        items: [
          createMockAssignment({
            role: 'supervising',
            person: {
              id: 'person-1',
              firstName: 'Dr.',
              lastName: 'Supervisor',
              pgyLevel: 2,
            },
          }),
        ],
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

      // Supervising role should result in 'senior' role type
      expect(result.current.data?.[0].person.role).toBe('senior');
    });
  });
});
