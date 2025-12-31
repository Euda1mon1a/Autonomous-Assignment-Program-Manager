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
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders without crashing', () => {
    render(<ScheduleCalendar startDate="2024-01-01" endDate="2024-01-28" />);
    expect(screen.getByRole('table')).toBeInTheDocument();
  });

  it('displays loading state initially', () => {
    render(<ScheduleCalendar startDate="2024-01-01" endDate="2024-01-28" />);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });
});
