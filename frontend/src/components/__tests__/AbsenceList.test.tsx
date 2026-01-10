/**
 * Tests for AbsenceList Component
 * Component: AbsenceList - Table view of absences
 */

import React from 'react';
import { render, screen, fireEvent } from '@/test-utils';
import '@testing-library/jest-dom';
import { AbsenceList } from '../AbsenceList';
import { mockData } from '@/test-utils';
import { AbsenceType, PersonType, type Absence, type Person } from '@/types/api';

describe('AbsenceList', () => {
  const mockOnEdit = jest.fn();
  const mockOnDelete = jest.fn();

  const mockPeople: Person[] = [
    {
      id: 'person-1',
      name: 'Dr. John Smith',
      email: 'john.smith@example.com',
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
      email: 'jane.doe@example.com',
      type: PersonType.FACULTY,
      pgyLevel: null,
      performsProcedures: true,
      specialties: ['Cardiology'],
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
      deploymentOrders: false,
      tdyLocation: null,
      replacementActivity: null,
      notes: 'Winter break',
      isAwayFromProgram: true,
      createdAt: '2024-01-01T00:00:00Z',
    },
    {
      id: 'absence-2',
      personId: 'person-2',
      startDate: '2024-01-20',
      endDate: '2024-01-22',
      absenceType: AbsenceType.CONFERENCE,
      deploymentOrders: false,
      tdyLocation: null,
      replacementActivity: null,
      notes: null,
      isAwayFromProgram: true,
      createdAt: '2024-01-01T00:00:00Z',
    },
  ];

  beforeEach(() => {
    mockOnEdit.mockClear();
    mockOnDelete.mockClear();
  });

  describe('Rendering', () => {
    it('renders table headers', () => {
      render(
        <AbsenceList
          absences={mockAbsences}
          people={mockPeople}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      expect(screen.getByText('Person')).toBeInTheDocument();
      expect(screen.getByText('Type')).toBeInTheDocument();
      expect(screen.getByText('Start Date')).toBeInTheDocument();
      expect(screen.getByText('End Date')).toBeInTheDocument();
      expect(screen.getByText('Notes')).toBeInTheDocument();
      expect(screen.getByText('Actions')).toBeInTheDocument();
    });

    it('renders absence rows', () => {
      render(
        <AbsenceList
          absences={mockAbsences}
          people={mockPeople}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      expect(screen.getByText('Dr. John Smith')).toBeInTheDocument();
      expect(screen.getByText('Dr. Jane Doe')).toBeInTheDocument();
    });

    it('displays person type correctly', () => {
      render(
        <AbsenceList
          absences={mockAbsences}
          people={mockPeople}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      expect(screen.getByText('PGY-2')).toBeInTheDocument();
      expect(screen.getByText('Faculty')).toBeInTheDocument();
    });

    it('displays absence type with correct formatting', () => {
      render(
        <AbsenceList
          absences={mockAbsences}
          people={mockPeople}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      expect(screen.getByText('vacation')).toBeInTheDocument();
      expect(screen.getByText('conference')).toBeInTheDocument();
    });

    it('formats dates correctly', () => {
      render(
        <AbsenceList
          absences={mockAbsences}
          people={mockPeople}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      expect(screen.getByText('Jan 15, 2024')).toBeInTheDocument();
      expect(screen.getByText('Jan 17, 2024')).toBeInTheDocument();
      expect(screen.getByText('Jan 20, 2024')).toBeInTheDocument();
      expect(screen.getByText('Jan 22, 2024')).toBeInTheDocument();
    });

    it('displays notes when present', () => {
      render(
        <AbsenceList
          absences={mockAbsences}
          people={mockPeople}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      expect(screen.getByText('Winter break')).toBeInTheDocument();
    });

    it('displays dash when notes are absent', () => {
      render(
        <AbsenceList
          absences={mockAbsences}
          people={mockPeople}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      const dashElements = screen.getAllByText('-');
      expect(dashElements.length).toBeGreaterThan(0);
    });

    it('renders edit button for each absence', () => {
      render(
        <AbsenceList
          absences={mockAbsences}
          people={mockPeople}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      const editButtons = screen.getAllByLabelText('Edit absence');
      expect(editButtons).toHaveLength(mockAbsences.length);
    });

    it('renders delete button for each absence', () => {
      render(
        <AbsenceList
          absences={mockAbsences}
          people={mockPeople}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      const deleteButtons = screen.getAllByLabelText('Delete absence');
      expect(deleteButtons).toHaveLength(mockAbsences.length);
    });
  });

  describe('Sorting', () => {
    it('sorts absences by start date (earliest first)', () => {
      const unsortedAbsences: Absence[] = [
        {
          id: 'absence-3',
          personId: 'person-1',
          startDate: '2024-02-01',
          endDate: '2024-02-01',
          absenceType: AbsenceType.VACATION,
          deploymentOrders: false,
          tdyLocation: null,
          replacementActivity: null,
          notes: null,
          isAwayFromProgram: true,
          createdAt: '2024-01-01T00:00:00Z',
        },
        {
          id: 'absence-1',
          personId: 'person-1',
          startDate: '2024-01-15',
          endDate: '2024-01-15',
          absenceType: AbsenceType.VACATION,
          deploymentOrders: false,
          tdyLocation: null,
          replacementActivity: null,
          notes: null,
          isAwayFromProgram: true,
          createdAt: '2024-01-01T00:00:00Z',
        },
      ];

      const { container } = render(
        <AbsenceList
          absences={unsortedAbsences}
          people={mockPeople}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      const rows = container.querySelectorAll('tbody tr');
      const firstRowDate = rows[0].querySelector('td:nth-child(3)')?.textContent;

      expect(firstRowDate).toBe('Jan 15, 2024');
    });
  });

  describe('Interaction', () => {
    it('calls onEdit when edit button clicked', () => {
      render(
        <AbsenceList
          absences={mockAbsences}
          people={mockPeople}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      const editButtons = screen.getAllByLabelText('Edit absence');
      fireEvent.click(editButtons[0]);

      expect(mockOnEdit).toHaveBeenCalledWith(mockAbsences[0]);
      expect(mockOnEdit).toHaveBeenCalledTimes(1);
    });

    it('calls onDelete when delete button clicked', () => {
      render(
        <AbsenceList
          absences={mockAbsences}
          people={mockPeople}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      const deleteButtons = screen.getAllByLabelText('Delete absence');
      fireEvent.click(deleteButtons[0]);

      expect(mockOnDelete).toHaveBeenCalledWith(mockAbsences[0]);
      expect(mockOnDelete).toHaveBeenCalledTimes(1);
    });

    it('highlights row on hover', () => {
      const { container } = render(
        <AbsenceList
          absences={mockAbsences}
          people={mockPeople}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      const row = container.querySelector('tbody tr');
      expect(row).toHaveClass('hover:bg-gray-50');
    });
  });

  describe('Empty State', () => {
    it('renders empty state when no absences', () => {
      render(
        <AbsenceList
          absences={[]}
          people={mockPeople}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      expect(screen.getByText('No absences found. Click "Add Absence" to create one.')).toBeInTheDocument();
    });

    it('does not render table when empty', () => {
      const { container } = render(
        <AbsenceList
          absences={[]}
          people={mockPeople}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      const table = container.querySelector('table');
      expect(table).not.toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles absence for unknown person', () => {
      const orphanAbsence: Absence[] = [
        {
          id: 'absence-orphan',
          personId: 'non-existent',
          startDate: '2024-01-15',
          endDate: '2024-01-15',
          absenceType: AbsenceType.VACATION,
          deploymentOrders: false,
          tdyLocation: null,
          replacementActivity: null,
          notes: null,
          isAwayFromProgram: true,
          createdAt: '2024-01-01T00:00:00Z',
        },
      ];

      render(
        <AbsenceList
          absences={orphanAbsence}
          people={mockPeople}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      expect(screen.getByText('Unknown')).toBeInTheDocument();
    });

    it('handles all absence types with correct colors', () => {
      const allTypesAbsences: Absence[] = [
        { ...mockAbsences[0], id: '1', absenceType: AbsenceType.VACATION },
        { ...mockAbsences[0], id: '2', absenceType: AbsenceType.SICK },
        { ...mockAbsences[0], id: '3', absenceType: AbsenceType.DEPLOYMENT },
        { ...mockAbsences[0], id: '4', absenceType: AbsenceType.CONFERENCE },
      ];

      render(
        <AbsenceList
          absences={allTypesAbsences}
          people={mockPeople}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      expect(screen.getByText('vacation')).toBeInTheDocument();
      expect(screen.getByText('sick')).toBeInTheDocument();
      expect(screen.getByText('deployment')).toBeInTheDocument();
      expect(screen.getByText('conference')).toBeInTheDocument();
    });

    it('truncates long notes', () => {
      const longNoteAbsence: Absence[] = [
        {
          ...mockAbsences[0],
          notes: 'This is a very long note that should be truncated in the table view to prevent layout issues',
        },
      ];

      const { container } = render(
        <AbsenceList
          absences={longNoteAbsence}
          people={mockPeople}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      const notesCell = container.querySelector('.max-w-xs.truncate');
      expect(notesCell).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has accessible button labels', () => {
      render(
        <AbsenceList
          absences={mockAbsences}
          people={mockPeople}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      const editButtons = screen.getAllByLabelText('Edit absence');
      const deleteButtons = screen.getAllByLabelText('Delete absence');

      expect(editButtons.length).toBe(2);
      expect(deleteButtons.length).toBe(2);
    });

    it('has proper table structure', () => {
      const { container } = render(
        <AbsenceList
          absences={mockAbsences}
          people={mockPeople}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      const table = container.querySelector('table');
      const thead = container.querySelector('thead');
      const tbody = container.querySelector('tbody');

      expect(table).toBeInTheDocument();
      expect(thead).toBeInTheDocument();
      expect(tbody).toBeInTheDocument();
    });
  });
});
