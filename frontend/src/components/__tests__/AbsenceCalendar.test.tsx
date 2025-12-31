/**
 * Tests for AbsenceCalendar Component
 * Component: AbsenceCalendar - Calendar view of absences
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@/test-utils';
import '@testing-library/jest-dom';
import { AbsenceCalendar } from '../AbsenceCalendar';
import { mockData } from '@/test-utils';
import type { Absence, Person } from '@/types/api';

describe('AbsenceCalendar', () => {
  const mockOnAbsenceClick = jest.fn();

  const mockPeople: Person[] = [
    mockData.person({ id: 'person-1', name: 'Dr. John Smith' }),
    mockData.person({ id: 'person-2', name: 'Dr. Jane Doe' }),
  ];

  const mockAbsences: Absence[] = [
    {
      id: 'absence-1',
      person_id: 'person-1',
      start_date: '2024-01-15',
      end_date: '2024-01-17',
      absence_type: 'vacation',
      deployment_orders: false,
      tdy_location: null,
      replacement_activity: null,
      notes: null,
      created_at: '2024-01-01T00:00:00Z',
    },
    {
      id: 'absence-2',
      person_id: 'person-2',
      start_date: '2024-01-20',
      end_date: '2024-01-22',
      absence_type: 'conference',
      deployment_orders: false,
      tdy_location: null,
      replacement_activity: null,
      notes: null,
      created_at: '2024-01-01T00:00:00Z',
    },
  ];

  beforeEach(() => {
    mockOnAbsenceClick.mockClear();
    jest.useFakeTimers();
    jest.setSystemTime(new Date('2024-01-15'));
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  describe('Rendering', () => {
    it('renders calendar with current month', () => {
      render(
        <AbsenceCalendar
          absences={mockAbsences}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      );

      expect(screen.getByText('January 2024')).toBeInTheDocument();
    });

    it('renders day headers', () => {
      render(
        <AbsenceCalendar
          absences={mockAbsences}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      );

      ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].forEach((day) => {
        expect(screen.getByText(day)).toBeInTheDocument();
      });
    });

    it('renders absences on correct days', () => {
      render(
        <AbsenceCalendar
          absences={mockAbsences}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      );

      // Check for person initials in calendar
      expect(screen.getByText(/JS/)).toBeInTheDocument(); // John Smith
      expect(screen.getByText(/JD/)).toBeInTheDocument(); // Jane Doe
    });

    it('renders absence type labels', () => {
      render(
        <AbsenceCalendar
          absences={mockAbsences}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      );

      expect(screen.getByText(/vacation/i)).toBeInTheDocument();
      expect(screen.getByText(/conference/i)).toBeInTheDocument();
    });

    it('highlights today', () => {
      const { container } = render(
        <AbsenceCalendar
          absences={mockAbsences}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      );

      // Today (15th) should have special styling
      const todayElement = container.querySelector('.bg-blue-600');
      expect(todayElement).toBeInTheDocument();
    });

    it('renders legend with absence types', () => {
      render(
        <AbsenceCalendar
          absences={mockAbsences}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      );

      // Legend should show first 6 absence types
      expect(screen.getByText('vacation')).toBeInTheDocument();
    });
  });

  describe('Navigation', () => {
    it('has previous month button', () => {
      render(
        <AbsenceCalendar
          absences={mockAbsences}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      );

      const prevButton = screen.getByLabelText('Previous month');
      expect(prevButton).toBeInTheDocument();
    });

    it('has next month button', () => {
      render(
        <AbsenceCalendar
          absences={mockAbsences}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      );

      const nextButton = screen.getByLabelText('Next month');
      expect(nextButton).toBeInTheDocument();
    });

    it('navigates to previous month when clicked', () => {
      render(
        <AbsenceCalendar
          absences={mockAbsences}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      );

      const prevButton = screen.getByLabelText('Previous month');
      fireEvent.click(prevButton);

      expect(screen.getByText('December 2023')).toBeInTheDocument();
    });

    it('navigates to next month when clicked', () => {
      render(
        <AbsenceCalendar
          absences={mockAbsences}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      );

      const nextButton = screen.getByLabelText('Next month');
      fireEvent.click(nextButton);

      expect(screen.getByText('February 2024')).toBeInTheDocument();
    });
  });

  describe('Interaction', () => {
    it('calls onAbsenceClick when absence is clicked', () => {
      render(
        <AbsenceCalendar
          absences={mockAbsences}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      );

      const absenceButton = screen.getByText(/vacation/i).closest('button');
      fireEvent.click(absenceButton!);

      expect(mockOnAbsenceClick).toHaveBeenCalledWith(mockAbsences[0]);
    });

    it('shows tooltips on hover', () => {
      render(
        <AbsenceCalendar
          absences={mockAbsences}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      );

      const absenceButton = screen.getByText(/vacation/i).closest('button');
      expect(absenceButton).toHaveAttribute('title');
    });
  });

  describe('Multi-day Absences', () => {
    it('shows absence across multiple days', () => {
      const multiDayAbsence: Absence[] = [
        {
          id: 'absence-3',
          person_id: 'person-1',
          start_date: '2024-01-15',
          end_date: '2024-01-20', // 6 days
          absence_type: 'vacation',
          deployment_orders: false,
          tdy_location: null,
          replacement_activity: null,
          notes: null,
          created_at: '2024-01-01T00:00:00Z',
        },
      ];

      render(
        <AbsenceCalendar
          absences={multiDayAbsence}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      );

      // Should appear on multiple days
      const vacationElements = screen.getAllByText(/vacation/i);
      expect(vacationElements.length).toBeGreaterThan(1);
    });
  });

  describe('Overflow Handling', () => {
    it('shows "+X more" when more than 3 absences on one day', () => {
      const manyAbsences: Absence[] = [
        ...Array.from({ length: 5 }, (_, i) => ({
          id: `absence-${i}`,
          person_id: `person-${i}`,
          start_date: '2024-01-15',
          end_date: '2024-01-15',
          absence_type: 'vacation' as const,
          deployment_orders: false,
          tdy_location: null,
          replacement_activity: null,
          notes: null,
          created_at: '2024-01-01T00:00:00Z',
        })),
      ];

      const manyPeople = Array.from({ length: 5 }, (_, i) =>
        mockData.person({ id: `person-${i}`, name: `Person ${i}` })
      );

      render(
        <AbsenceCalendar
          absences={manyAbsences}
          people={manyPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      );

      expect(screen.getByText('+2 more')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles empty absences array', () => {
      render(
        <AbsenceCalendar
          absences={[]}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      );

      expect(screen.getByText('January 2024')).toBeInTheDocument();
    });

    it('handles empty people array', () => {
      render(
        <AbsenceCalendar
          absences={mockAbsences}
          people={[]}
          onAbsenceClick={mockOnAbsenceClick}
        />
      );

      // Should show ?? for unknown person
      expect(screen.getByText(/\?\?/)).toBeInTheDocument();
    });

    it('handles absence for person not in people list', () => {
      const orphanAbsence: Absence[] = [
        {
          id: 'absence-orphan',
          person_id: 'non-existent-person',
          start_date: '2024-01-15',
          end_date: '2024-01-15',
          absence_type: 'vacation',
          deployment_orders: false,
          tdy_location: null,
          replacement_activity: null,
          notes: null,
          created_at: '2024-01-01T00:00:00Z',
        },
      ];

      render(
        <AbsenceCalendar
          absences={orphanAbsence}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      );

      expect(screen.getByText(/\?\?/)).toBeInTheDocument();
    });

    it('differentiates weekends', () => {
      const { container } = render(
        <AbsenceCalendar
          absences={mockAbsences}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      );

      // Weekends should have gray background
      const weekendCells = container.querySelectorAll('.bg-gray-50');
      expect(weekendCells.length).toBeGreaterThan(0);
    });
  });
});
