/**
 * Tests for usePec hooks.
 *
 * Tests cover:
 * - Query key structure
 * - Hook data fetching with mock data
 * - Helper function color mappings
 * - Filter behavior
 */

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import { ReactNode } from 'react';

import {
  usePecDashboard,
  usePecMeetings,
  usePecActionItems,
  usePecDecisions,
  pecQueryKeys,
  getMeetingStatusColor,
  getMeetingTypeLabel,
  getActionPriorityColor,
  getActionStatusColor,
  getCommandDispositionColor,
} from '../usePec';

// ============================================================================
// Test Setup
// ============================================================================

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  });

  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
}

// ============================================================================
// Query Keys Tests
// ============================================================================

describe('pecQueryKeys', () => {
  it('should have correct base key', () => {
    expect(pecQueryKeys.all).toEqual(['pec']);
  });

  it('should generate correct dashboard key', () => {
    expect(pecQueryKeys.dashboard('AY25-26')).toEqual(['pec', 'dashboard', 'AY25-26']);
  });

  it('should generate correct meetings key with filters', () => {
    expect(pecQueryKeys.meetings({ academicYear: 'AY25-26', status: 'completed' })).toEqual([
      'pec',
      'meetings',
      { academicYear: 'AY25-26', status: 'completed' },
    ]);
  });

  it('should generate correct meetings key without filters', () => {
    expect(pecQueryKeys.meetings()).toEqual(['pec', 'meetings', undefined]);
  });

  it('should generate correct actions key', () => {
    expect(pecQueryKeys.actions({ priority: 'high' })).toEqual([
      'pec',
      'actions',
      { priority: 'high' },
    ]);
  });

  it('should generate correct decisions key', () => {
    expect(pecQueryKeys.decisions('mtg-001')).toEqual(['pec', 'decisions', 'mtg-001']);
  });
});

// ============================================================================
// usePecDashboard Tests
// ============================================================================

describe('usePecDashboard', () => {
  it('should fetch dashboard data with mock data', async () => {
    const { result } = renderHook(() => usePecDashboard('AY25-26'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    const data = result.current.data;
    expect(data).toBeDefined();
    expect(data?.academicYear).toBe('AY25-26');
    expect(data?.totalResidents).toBe(18);
    expect(data?.metrics).toBeDefined();
    expect(data?.metrics.meetingsThisYear).toBe(3);
  });

  it('should not fetch when academicYear is empty', async () => {
    const { result } = renderHook(() => usePecDashboard(''), {
      wrapper: createWrapper(),
    });

    // Query should be disabled
    expect(result.current.isLoading).toBe(false);
    expect(result.current.isFetching).toBe(false);
  });
});

// ============================================================================
// usePecMeetings Tests
// ============================================================================

describe('usePecMeetings', () => {
  it('should fetch all meetings with mock data', async () => {
    const { result } = renderHook(() => usePecMeetings(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    const data = result.current.data;
    expect(data).toBeDefined();
    expect(data?.length).toBeGreaterThan(0);
    expect(data?.[0]).toHaveProperty('id');
    expect(data?.[0]).toHaveProperty('meetingDate');
    expect(data?.[0]).toHaveProperty('meetingType');
  });

  it('should filter meetings by status', async () => {
    const { result } = renderHook(() => usePecMeetings({ status: 'completed' }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    const data = result.current.data;
    expect(data).toBeDefined();
    data?.forEach((meeting) => {
      expect(meeting.status).toBe('completed');
    });
  });

  it('should filter meetings by academic year', async () => {
    const { result } = renderHook(() => usePecMeetings({ academicYear: 'AY25-26' }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    const data = result.current.data;
    expect(data).toBeDefined();
    data?.forEach((meeting) => {
      expect(meeting.academicYear).toBe('AY25-26');
    });
  });
});

// ============================================================================
// usePecActionItems Tests
// ============================================================================

describe('usePecActionItems', () => {
  it('should fetch action items with mock data', async () => {
    const { result } = renderHook(() => usePecActionItems(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    const data = result.current.data;
    expect(data).toBeDefined();
    expect(data?.length).toBeGreaterThan(0);
    expect(data?.[0]).toHaveProperty('id');
    expect(data?.[0]).toHaveProperty('description');
    expect(data?.[0]).toHaveProperty('priority');
    expect(data?.[0]).toHaveProperty('status');
  });

  it('should filter actions by priority', async () => {
    const { result } = renderHook(() => usePecActionItems({ priority: 'critical' }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    const data = result.current.data;
    expect(data).toBeDefined();
    data?.forEach((action) => {
      expect(action.priority).toBe('critical');
    });
  });

  it('should filter overdue actions', async () => {
    const { result } = renderHook(() => usePecActionItems({ overdue: true }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    const data = result.current.data;
    expect(data).toBeDefined();
    data?.forEach((action) => {
      expect(action.isOverdue).toBe(true);
    });
  });
});

// ============================================================================
// usePecDecisions Tests
// ============================================================================

describe('usePecDecisions', () => {
  it('should fetch decisions for a meeting', async () => {
    const { result } = renderHook(() => usePecDecisions('mtg-002'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    const data = result.current.data;
    expect(data).toBeDefined();
    expect(data?.length).toBeGreaterThan(0);
    expect(data?.[0]).toHaveProperty('id');
    expect(data?.[0]).toHaveProperty('decisionType');
    expect(data?.[0]).toHaveProperty('summary');
  });

  it('should not fetch when meetingId is empty', async () => {
    const { result } = renderHook(() => usePecDecisions(''), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.isFetching).toBe(false);
  });
});

// ============================================================================
// Helper Function Tests
// ============================================================================

describe('getMeetingStatusColor', () => {
  it('should return correct color for scheduled', () => {
    expect(getMeetingStatusColor('scheduled')).toContain('blue');
  });

  it('should return correct color for in_progress', () => {
    expect(getMeetingStatusColor('in_progress')).toContain('amber');
  });

  it('should return correct color for completed', () => {
    expect(getMeetingStatusColor('completed')).toContain('green');
  });

  it('should return correct color for cancelled', () => {
    expect(getMeetingStatusColor('cancelled')).toContain('slate');
  });

  it('should return default color for unknown status', () => {
    expect(getMeetingStatusColor('unknown')).toContain('slate');
  });
});

describe('getMeetingTypeLabel', () => {
  it('should return correct label for quarterly', () => {
    expect(getMeetingTypeLabel('quarterly')).toBe('Quarterly');
  });

  it('should return correct label for annual', () => {
    expect(getMeetingTypeLabel('annual')).toBe('Annual');
  });

  it('should return correct label for special', () => {
    expect(getMeetingTypeLabel('special')).toBe('Special');
  });

  it('should return correct label for sentinel', () => {
    expect(getMeetingTypeLabel('sentinel')).toBe('Sentinel Event');
  });

  it('should return type as-is for unknown types', () => {
    expect(getMeetingTypeLabel('custom')).toBe('custom');
  });
});

describe('getActionPriorityColor', () => {
  it('should return correct color for critical', () => {
    expect(getActionPriorityColor('critical')).toContain('red');
  });

  it('should return correct color for high', () => {
    expect(getActionPriorityColor('high')).toContain('orange');
  });

  it('should return correct color for medium', () => {
    expect(getActionPriorityColor('medium')).toContain('amber');
  });

  it('should return correct color for low', () => {
    expect(getActionPriorityColor('low')).toContain('slate');
  });
});

describe('getActionStatusColor', () => {
  it('should return correct color for open', () => {
    expect(getActionStatusColor('open')).toContain('blue');
  });

  it('should return correct color for in_progress', () => {
    expect(getActionStatusColor('in_progress')).toContain('amber');
  });

  it('should return correct color for completed', () => {
    expect(getActionStatusColor('completed')).toContain('green');
  });

  it('should return correct color for deferred', () => {
    expect(getActionStatusColor('deferred')).toContain('purple');
  });

  it('should return correct color for cancelled', () => {
    expect(getActionStatusColor('cancelled')).toContain('slate');
  });
});

describe('getCommandDispositionColor', () => {
  it('should return correct color for Approved', () => {
    expect(getCommandDispositionColor('Approved')).toContain('green');
  });

  it('should return correct color for Pending', () => {
    expect(getCommandDispositionColor('Pending')).toContain('amber');
  });

  it('should return correct color for Disapproved', () => {
    expect(getCommandDispositionColor('Disapproved')).toContain('red');
  });

  it('should return correct color for Modified', () => {
    expect(getCommandDispositionColor('Modified')).toContain('purple');
  });

  it('should return default color for undefined', () => {
    expect(getCommandDispositionColor(undefined)).toContain('slate');
  });
});
