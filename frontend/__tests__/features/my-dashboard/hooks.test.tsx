/**
 * Tests for My Dashboard React Query Hooks
 *
 * Tests data fetching, mutations, and cache management
 */

import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import * as api from '@/lib/api';
import {
  useMyDashboard,
  useCalendarSyncUrl,
  useCalendarSync,
  useRequestSwap,
  dashboardQueryKeys,
} from '@/features/my-dashboard/hooks';
import {
  mockDashboardApiResponse,
  mockCalendarSyncResponse,
  mockSwapRequestResponse,
} from './mockData';
import React from 'react';

// Mock the API module
jest.mock('@/lib/api');

// Create wrapper with QueryClient
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  const Wrapper = ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children);
  return Wrapper;
}

describe('My Dashboard Hooks', () => {
  beforeEach(() => {
    jest.clearAllMocks();

    // Mock localStorage for user data
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: jest.fn(() => JSON.stringify({ id: 'user-123' })),
        setItem: jest.fn(),
        removeItem: jest.fn(),
        clear: jest.fn(),
      },
      writable: true,
    });
  });

  describe('useMyDashboard', () => {
    it('should fetch dashboard data successfully', async () => {
      (api.get as jest.Mock).mockResolvedValue(mockDashboardApiResponse);

      const { result } = renderHook(() => useMyDashboard(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toBeDefined();
      expect(result.current.data?.user.name).toBe('Dr. John Smith');
      expect(result.current.data?.upcomingSchedule).toHaveLength(2);
      expect(result.current.data?.pendingSwaps).toHaveLength(1);
      expect(result.current.data?.summary.workloadNext4Weeks).toBe(12);
    });

    it('should pass daysAhead parameter to API', async () => {
      (api.get as jest.Mock).mockResolvedValue(mockDashboardApiResponse);

      renderHook(() => useMyDashboard({ daysAhead: 60 }), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith(
          expect.stringContaining('daysAhead=60')
        );
      });
    });

    it('should pass includeSwaps parameter to API', async () => {
      (api.get as jest.Mock).mockResolvedValue(mockDashboardApiResponse);

      renderHook(() => useMyDashboard({ includeSwaps: false }), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith(
          expect.stringContaining('includeSwaps=false')
        );
      });
    });

    it('should pass includeAbsences parameter to API', async () => {
      (api.get as jest.Mock).mockResolvedValue(mockDashboardApiResponse);

      renderHook(() => useMyDashboard({ includeAbsences: false }), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith(
          expect.stringContaining('includeAbsences=false')
        );
      });
    });

    it('should transform assignment data from API format', async () => {
      (api.get as jest.Mock).mockResolvedValue(mockDashboardApiResponse);

      const { result } = renderHook(() => useMyDashboard(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      const firstAssignment = result.current.data?.upcomingSchedule[0];
      expect(firstAssignment?.timeOfDay).toBe('AM');
      expect(firstAssignment?.canTrade).toBe(true);
      expect(firstAssignment?.activity).toBe('Inpatient Medicine');
    });

    it('should transform pending swap data from API format', async () => {
      (api.get as jest.Mock).mockResolvedValue(mockDashboardApiResponse);

      const { result } = renderHook(() => useMyDashboard(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      const firstSwap = result.current.data?.pendingSwaps[0];
      expect(firstSwap?.type).toBe('incoming');
      expect(firstSwap?.otherFacultyName).toBe('Dr. Sarah Williams');
      expect(firstSwap?.canRespond).toBe(true);
    });

    it('should handle empty upcoming schedule', async () => {
      const emptyResponse = {
        ...mockDashboardApiResponse,
        upcomingSchedule: [],
      };
      (api.get as jest.Mock).mockResolvedValue(emptyResponse);

      const { result } = renderHook(() => useMyDashboard(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.upcomingSchedule).toEqual([]);
    });

    it('should handle missing optional fields', async () => {
      const minimalResponse = {
        user: mockDashboardApiResponse.user,
        summary: {
          nextAssignment: null,
          workloadNext4Weeks: 0,
          pendingSwapCount: 0,
          upcomingAbsences: 0,
        },
      };
      (api.get as jest.Mock).mockResolvedValue(minimalResponse);

      const { result } = renderHook(() => useMyDashboard(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.upcomingSchedule).toEqual([]);
      expect(result.current.data?.pendingSwaps).toEqual([]);
      expect(result.current.data?.absences).toEqual([]);
    });

    it('should handle API errors', async () => {
      const error = new Error('Failed to fetch dashboard');
      (api.get as jest.Mock).mockRejectedValue(error);

      const { result } = renderHook(() => useMyDashboard(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toEqual(error);
    });

    it('should use correct query key', () => {
      const params = { daysAhead: 30 };
      const expectedKey = dashboardQueryKeys.dashboard(params);

      expect(expectedKey).toEqual(['my-dashboard', 'data', params]);
    });

    it('should handle assignments without IDs', async () => {
      const responseWithoutIds = {
        ...mockDashboardApiResponse,
        upcomingSchedule: [
          {
            date: '2025-02-15',
            timeOfDay: 'AM',
            activity: 'Test Activity',
            location: 'Ward',
            canTrade: true,
          },
        ],
      };
      (api.get as jest.Mock).mockResolvedValue(responseWithoutIds);

      const { result } = renderHook(() => useMyDashboard(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      const assignment = result.current.data?.upcomingSchedule[0];
      expect(assignment?.id).toContain('2025-02-15');
      expect(assignment?.id).toContain('AM');
    });
  });

  describe('useCalendarSyncUrl', () => {
    it('should fetch calendar sync URL successfully', async () => {
      const mockResponse = { url: 'https://example.com/calendar/sync/token123' };
      (api.get as jest.Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useCalendarSyncUrl(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toBe('https://example.com/calendar/sync/token123');
    });

    it('should call correct API endpoint', async () => {
      const mockResponse = { url: 'https://example.com/calendar/sync/token123' };
      (api.get as jest.Mock).mockResolvedValue(mockResponse);

      renderHook(() => useCalendarSyncUrl(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith('/portal/my/calendar-sync-url');
      });
    });

    it('should handle API errors', async () => {
      const error = new Error('Failed to fetch calendar URL');
      (api.get as jest.Mock).mockRejectedValue(error);

      const { result } = renderHook(() => useCalendarSyncUrl(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toEqual(error);
    });
  });

  describe('useCalendarSync', () => {
    it('should sync calendar successfully', async () => {
      (api.post as jest.Mock).mockResolvedValue(mockCalendarSyncResponse);

      const { result } = renderHook(() => useCalendarSync(), {
        wrapper: createWrapper(),
      });

      let response: any;
      await waitFor(async () => {
        response = await result.current.mutateAsync({
          format: 'ics',
          includeWeeksAhead: 12,
        });
      });

      expect(api.post).toHaveBeenCalledWith('/portal/my/calendar-sync', {
        format: 'ics',
        includeWeeksAhead: 12,
      });

      expect(response).toEqual({
        success: true,
        url: 'https://example.com/calendar/download/token123.ics',
        message: 'Calendar sync successful',
      });
    });

    it('should default to 12 weeks if not specified', async () => {
      (api.post as jest.Mock).mockResolvedValue(mockCalendarSyncResponse);

      const { result } = renderHook(() => useCalendarSync(), {
        wrapper: createWrapper(),
      });

      await waitFor(async () => {
        await result.current.mutateAsync({ format: 'google' });
      });

      expect(api.post).toHaveBeenCalledWith('/portal/my/calendar-sync', {
        format: 'google',
        includeWeeksAhead: 12,
      });
    });

    it('should handle different calendar formats', async () => {
      (api.post as jest.Mock).mockResolvedValue(mockCalendarSyncResponse);

      const { result } = renderHook(() => useCalendarSync(), {
        wrapper: createWrapper(),
      });

      // Test ICS format
      await waitFor(async () => {
        await result.current.mutateAsync({ format: 'ics' });
      });
      expect(api.post).toHaveBeenCalledWith(
        '/portal/my/calendar-sync',
        expect.objectContaining({ format: 'ics' })
      );

      result.current.reset();

      // Test Google format
      await waitFor(async () => {
        await result.current.mutateAsync({ format: 'google' });
      });
      expect(api.post).toHaveBeenCalledWith(
        '/portal/my/calendar-sync',
        expect.objectContaining({ format: 'google' })
      );

      result.current.reset();

      // Test Outlook format
      await waitFor(async () => {
        await result.current.mutateAsync({ format: 'outlook' });
      });
      expect(api.post).toHaveBeenCalledWith(
        '/portal/my/calendar-sync',
        expect.objectContaining({ format: 'outlook' })
      );
    });

    it('should handle API errors', async () => {
      const error = new Error('Failed to sync calendar');
      (api.post as jest.Mock).mockRejectedValue(error);

      const { result } = renderHook(() => useCalendarSync(), {
        wrapper: createWrapper(),
      });

      try {
        await result.current.mutateAsync({ format: 'ics' });
      } catch (e) {
        expect(e).toEqual(error);
      }
    });

    it('should invalidate calendar URL query after successful sync', async () => {
      (api.post as jest.Mock).mockResolvedValue(mockCalendarSyncResponse);

      const queryClient = new QueryClient({
        defaultOptions: {
          queries: { retry: false },
          mutations: { retry: false },
        },
      });

      const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries');

      const wrapper = ({ children }: { children: React.ReactNode }) =>
        React.createElement(QueryClientProvider, { client: queryClient }, children);

      const { result } = renderHook(() => useCalendarSync(), { wrapper });

      await waitFor(async () => {
        await result.current.mutateAsync({ format: 'ics' });
      });

      expect(invalidateSpy).toHaveBeenCalledWith({
        queryKey: dashboardQueryKeys.calendarUrl(),
      });
    });
  });

  describe('useRequestSwap', () => {
    it('should request swap successfully', async () => {
      (api.post as jest.Mock).mockResolvedValue(mockSwapRequestResponse);

      const { result } = renderHook(() => useRequestSwap(), {
        wrapper: createWrapper(),
      });

      let response: any;
      await waitFor(async () => {
        response = await result.current.mutateAsync({
          assignmentId: 'assignment-123',
          reason: 'Medical conference',
        });
      });

      expect(api.post).toHaveBeenCalledWith(
        '/portal/my/assignments/assignment-123/request-swap',
        { reason: 'Medical conference' }
      );

      expect(response).toEqual({
        success: true,
        message: 'Swap request created successfully',
      });
    });

    it('should request swap without reason', async () => {
      (api.post as jest.Mock).mockResolvedValue(mockSwapRequestResponse);

      const { result } = renderHook(() => useRequestSwap(), {
        wrapper: createWrapper(),
      });

      await waitFor(async () => {
        await result.current.mutateAsync({ assignmentId: 'assignment-123' });
      });

      expect(api.post).toHaveBeenCalledWith(
        '/portal/my/assignments/assignment-123/request-swap',
        { reason: undefined }
      );
    });

    it('should handle API errors', async () => {
      const error = new Error('Failed to create swap request');
      (api.post as jest.Mock).mockRejectedValue(error);

      const { result } = renderHook(() => useRequestSwap(), {
        wrapper: createWrapper(),
      });

      try {
        await result.current.mutateAsync({
          assignmentId: 'assignment-123',
          reason: 'Test',
        });
      } catch (e) {
        expect(e).toEqual(error);
      }
    });

    it('should invalidate dashboard queries after successful request', async () => {
      (api.post as jest.Mock).mockResolvedValue(mockSwapRequestResponse);

      const queryClient = new QueryClient({
        defaultOptions: {
          queries: { retry: false },
          mutations: { retry: false },
        },
      });

      const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries');

      const wrapper = ({ children }: { children: React.ReactNode }) =>
        React.createElement(QueryClientProvider, { client: queryClient }, children);

      const { result } = renderHook(() => useRequestSwap(), { wrapper });

      await waitFor(async () => {
        await result.current.mutateAsync({
          assignmentId: 'assignment-123',
          reason: 'Test',
        });
      });

      expect(invalidateSpy).toHaveBeenCalledWith({
        queryKey: dashboardQueryKeys.all,
      });
    });
  });

  describe('Query Keys', () => {
    it('should generate correct query key for all dashboard queries', () => {
      expect(dashboardQueryKeys.all).toEqual(['my-dashboard']);
    });

    it('should generate correct query key for dashboard without params', () => {
      expect(dashboardQueryKeys.dashboard()).toEqual(['my-dashboard', 'data', undefined]);
    });

    it('should generate correct query key for dashboard with params', () => {
      const params = { daysAhead: 60, includeSwaps: true };
      expect(dashboardQueryKeys.dashboard(params)).toEqual([
        'my-dashboard',
        'data',
        params,
      ]);
    });

    it('should generate correct query key for calendar URL', () => {
      expect(dashboardQueryKeys.calendarUrl()).toEqual(['my-dashboard', 'calendar-url']);
    });
  });
});
