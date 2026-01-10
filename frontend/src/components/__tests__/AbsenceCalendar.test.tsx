/**
 * Tests for AbsenceCalendar Component
 * Component: AbsenceCalendar - Calendar view of absences
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@/test-utils';
import '@testing-library/jest-dom';
import { AbsenceCalendar } from '../AbsenceCalendar';
import { mockData } from '@/test-utils';
import { PersonType, AbsenceType } from '@/types/api';
import type { Absence, Person } from '@/types/api';

describe('AbsenceCalendar', () => {
  const mockOnAbsenceClick = jest.fn();

  const mockPeople: Person[] = [
    {
      id: 'person-1',
      name: 'Dr. John Smith',
      email: 'john@hospital.org',
      type: PersonType.RESIDENT,
      pgyLevel: 2,
      performsProcedures: true,
      specialties: ['Internal Medicine'],
      primaryDuty: null,
      facultyRole: null,
      createdAt: '2024-01-01T00:00:00Z',
      updatedAt: '2024-01-01T00:00:00Z',
    },
    {
      id: 'person-2',
      name: 'Dr. Jane Doe',
      email: 'jane@hospital.org',
      type: PersonType.RESIDENT,
      pgyLevel: 3,
      performsProcedures: true,
      specialties: ['Internal Medicine'],
      primaryDuty: null,
      facultyRole: null,
      createdAt: '2024-01-01T00:00:00Z',
      updatedAt: '2024-01-01T00:00:00Z',
    },
  ];

  const mockAbsences: Absence[] = [
    {
      id: 'absence-1',
      personId: 'person-1',
      startDate: '2024-01-15',
      endDate: '2024-01-17',
      absenceType: AbsenceType.VACATION,
      isAwayFromProgram: true,
      deploymentOrders: false,
      tdyLocation: null,
      replacementActivity: null,
      notes: null,
      createdAt: '2024-01-01T00:00:00Z',
    },
    {
      id: 'absence-2',
      personId: 'person-2',
      startDate: '2024-01-20',
      endDate: '2024-01-22',
      absenceType: AbsenceType.CONFERENCE,
      isAwayFromProgram: true,
      deploymentOrders: false,
      tdyLocation: null,
      replacementActivity: null,
      notes: null,
      createdAt: '2024-01-01T00:00:00Z',
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
          personId: 'person-1',
          startDate: '2024-01-15',
          endDate: '2024-01-20', // 6 days
          absenceType: AbsenceType.VACATION,
          isAwayFromProgram: true,
          deploymentOrders: false,
          tdyLocation: null,
          replacementActivity: null,
          notes: null,
          createdAt: '2024-01-01T00:00:00Z',
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
      const manyAbsences: Absence[] = Array.from({ length: 5 }, (_, i) => ({
        id: `absence-${i}`,
        personId: `person-${i}`,
        startDate: '2024-01-15',
        endDate: '2024-01-15',
        absenceType: AbsenceType.VACATION,
        isAwayFromProgram: true,
        deploymentOrders: false,
        tdyLocation: null,
        replacementActivity: null,
        notes: null,
        createdAt: '2024-01-01T00:00:00Z',
      }));

      const manyPeople: Person[] = Array.from({ length: 5 }, (_, i) => ({
        id: `person-${i}`,
        name: `Person ${i}`,
        email: `person${i}@hospital.org`,
        type: PersonType.RESIDENT,
        pgyLevel: 1,
        performsProcedures: false,
        specialties: ['Internal Medicine'],
        primaryDuty: null,
        facultyRole: null,
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-01T00:00:00Z',
      }));

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
          personId: 'non-existent-person',
          startDate: '2024-01-15',
          endDate: '2024-01-15',
          absenceType: AbsenceType.VACATION,
          isAwayFromProgram: true,
          deploymentOrders: false,
          tdyLocation: null,
          replacementActivity: null,
          notes: null,
          createdAt: '2024-01-01T00:00:00Z',
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
