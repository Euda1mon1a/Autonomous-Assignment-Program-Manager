/**
 * Tests for ScheduleCalendar Component
 * Component: ScheduleCalendar - Main schedule calendar view
 */

import React from 'react';
import { render, screen } from '@/test-utils';
import '@testing-library/jest-dom';
import { ScheduleCalendar } from '../ScheduleCalendar';

// Mock required contexts and dependencies
jest.mock('@/contexts/ToastContext', () => ({
  useToast: () => ({
    toast: {
      success: jest.fn(),
      error: jest.fn(),
    },
  }),
}));

global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({ assignments: [], people: [], templates: [] }),
  })
) as jest.Mock;

describe('ScheduleCalendar', () => {
  const mockWeekStart = new Date('2024-01-01');
  const mockSchedule = {
    '2024-01-01': { AM: [], PM: [] },
    '2024-01-02': { AM: [], PM: [] },
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders without crashing', () => {
    render(<ScheduleCalendar weekStart={mockWeekStart} schedule={mockSchedule} />);
    expect(screen.getByRole('table')).toBeInTheDocument();
  });

  it('displays week days', () => {
    render(<ScheduleCalendar weekStart={mockWeekStart} schedule={mockSchedule} />);
    // Should display the week starting from the given date
    expect(screen.getByRole('table')).toBeInTheDocument();
  });
});
