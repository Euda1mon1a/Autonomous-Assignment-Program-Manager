/**
 * PeopleTable Component Tests
 *
 * Tests for the sortable, selectable people table including:
 * - Rendering with people data
 * - Empty state
 * - Row selection (individual and select all)
 * - Sort header interactions
 * - Type badges
 * - Specialty display
 */
import React from 'react';
import { render, screen, fireEvent } from '@/test-utils';
import '@testing-library/jest-dom';
import { PeopleTable, type PeopleTableProps } from '../PeopleTable';
import type { Person } from '@/types/api';

// ============================================================================
// Test Data
// ============================================================================

const mockPeople: Person[] = [
  {
    id: 'p1',
    name: 'Dr. Alice Smith',
    email: 'alice@example.com',
    type: 'resident',
    pgyLevel: 2,
    performsProcedures: false,
    specialties: ['Internal Medicine', 'Cardiology', 'Nephrology'],
    primaryDuty: null,
    facultyRole: null,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  },
  {
    id: 'p2',
    name: 'Dr. Bob Jones',
    email: null,
    type: 'faculty',
    pgyLevel: null,
    performsProcedures: true,
    specialties: ['Surgery'],
    primaryDuty: null,
    facultyRole: null,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  },
  {
    id: 'p3',
    name: 'Dr. Carol White',
    email: 'carol@example.com',
    type: 'resident',
    pgyLevel: 1,
    performsProcedures: false,
    specialties: null,
    primaryDuty: null,
    facultyRole: null,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  },
];

const defaultProps: PeopleTableProps = {
  people: mockPeople,
  selectedIds: [],
  onSelectionChange: jest.fn(),
  sort: { field: 'name', direction: 'asc' },
  onSortChange: jest.fn(),
};

// ============================================================================
// Tests
// ============================================================================

describe('PeopleTable', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders all people rows', () => {
      render(<PeopleTable {...defaultProps} />);

      expect(screen.getByText('Dr. Alice Smith')).toBeInTheDocument();
      expect(screen.getByText('Dr. Bob Jones')).toBeInTheDocument();
      expect(screen.getByText('Dr. Carol White')).toBeInTheDocument();
    });

    it('renders sort column headers', () => {
      render(<PeopleTable {...defaultProps} />);

      expect(screen.getByText('Name')).toBeInTheDocument();
      expect(screen.getByText('Type')).toBeInTheDocument();
      expect(screen.getByText('PGY Level')).toBeInTheDocument();
      expect(screen.getByText('Email')).toBeInTheDocument();
      expect(screen.getByText('Specialties')).toBeInTheDocument();
    });

    it('renders type badges correctly for residents', () => {
      render(<PeopleTable {...defaultProps} />);

      expect(screen.getAllByText('resident')).toHaveLength(2);
    });

    it('renders type badges correctly for faculty', () => {
      render(<PeopleTable {...defaultProps} />);

      expect(screen.getByText('faculty')).toBeInTheDocument();
    });

    it('renders PGY level for residents', () => {
      render(<PeopleTable {...defaultProps} />);

      expect(screen.getByText('PGY-2')).toBeInTheDocument();
      expect(screen.getByText('PGY-1')).toBeInTheDocument();
    });

    it('renders email when available', () => {
      render(<PeopleTable {...defaultProps} />);

      expect(screen.getByText('alice@example.com')).toBeInTheDocument();
      expect(screen.getByText('carol@example.com')).toBeInTheDocument();
    });

    it('renders dash when email is null', () => {
      render(<PeopleTable {...defaultProps} />);

      // Bob Jones has no email - should show dashes
      const dashes = screen.getAllByText('-');
      expect(dashes.length).toBeGreaterThan(0);
    });

    it('renders specialties with overflow indicator', () => {
      render(<PeopleTable {...defaultProps} />);

      // Alice has 3 specialties, only 2 shown + overflow
      expect(screen.getByText('Internal Medicine')).toBeInTheDocument();
      expect(screen.getByText('Cardiology')).toBeInTheDocument();
      expect(screen.getByText('+1')).toBeInTheDocument();
    });

    it('renders single specialty without overflow', () => {
      render(<PeopleTable {...defaultProps} />);

      expect(screen.getByText('Surgery')).toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    it('renders empty state when no people', () => {
      render(<PeopleTable {...defaultProps} people={[]} />);

      expect(screen.getByText('No people found')).toBeInTheDocument();
      expect(
        screen.getByText('Try adjusting your filters or add new people.')
      ).toBeInTheDocument();
    });

    it('does not render table when no people', () => {
      render(<PeopleTable {...defaultProps} people={[]} />);

      expect(screen.queryByRole('table')).not.toBeInTheDocument();
    });
  });

  describe('Selection', () => {
    it('renders checkboxes for each row', () => {
      render(<PeopleTable {...defaultProps} />);

      // 1 header checkbox + 3 row checkboxes
      const checkboxes = screen.getAllByRole('checkbox');
      expect(checkboxes).toHaveLength(4);
    });

    it('calls onSelectionChange with person id when row checkbox clicked', () => {
      const onSelectionChange = jest.fn();
      render(
        <PeopleTable {...defaultProps} onSelectionChange={onSelectionChange} />
      );

      const checkbox = screen.getByLabelText('Select Dr. Alice Smith');
      fireEvent.click(checkbox);

      expect(onSelectionChange).toHaveBeenCalledWith(['p1']);
    });

    it('removes id from selection when already selected', () => {
      const onSelectionChange = jest.fn();
      render(
        <PeopleTable
          {...defaultProps}
          selectedIds={['p1', 'p2']}
          onSelectionChange={onSelectionChange}
        />
      );

      const checkbox = screen.getByLabelText('Select Dr. Alice Smith');
      fireEvent.click(checkbox);

      expect(onSelectionChange).toHaveBeenCalledWith(['p2']);
    });

    it('selects all when header checkbox clicked', () => {
      const onSelectionChange = jest.fn();
      render(
        <PeopleTable {...defaultProps} onSelectionChange={onSelectionChange} />
      );

      const selectAllCheckbox = screen.getByLabelText('Select all people');
      fireEvent.click(selectAllCheckbox);

      expect(onSelectionChange).toHaveBeenCalledWith(['p1', 'p2', 'p3']);
    });

    it('deselects all when all are selected and header checkbox clicked', () => {
      const onSelectionChange = jest.fn();
      render(
        <PeopleTable
          {...defaultProps}
          selectedIds={['p1', 'p2', 'p3']}
          onSelectionChange={onSelectionChange}
        />
      );

      const deselectAllCheckbox = screen.getByLabelText('Deselect all people');
      fireEvent.click(deselectAllCheckbox);

      expect(onSelectionChange).toHaveBeenCalledWith([]);
    });

    it('selects row when row is clicked', () => {
      const onSelectionChange = jest.fn();
      render(
        <PeopleTable {...defaultProps} onSelectionChange={onSelectionChange} />
      );

      // Click the row text
      fireEvent.click(screen.getByText('Dr. Bob Jones'));

      expect(onSelectionChange).toHaveBeenCalledWith(['p2']);
    });

    it('highlights selected rows', () => {
      render(<PeopleTable {...defaultProps} selectedIds={['p1']} />);

      const checkbox = screen.getByLabelText('Select Dr. Alice Smith');
      expect(checkbox).toBeChecked();
    });
  });

  describe('Sorting', () => {
    it('calls onSortChange when Name header clicked', () => {
      const onSortChange = jest.fn();
      render(
        <PeopleTable {...defaultProps} onSortChange={onSortChange} />
      );

      fireEvent.click(screen.getByText('Name'));

      expect(onSortChange).toHaveBeenCalledWith('name');
    });

    it('calls onSortChange when Type header clicked', () => {
      const onSortChange = jest.fn();
      render(
        <PeopleTable {...defaultProps} onSortChange={onSortChange} />
      );

      fireEvent.click(screen.getByText('Type'));

      expect(onSortChange).toHaveBeenCalledWith('type');
    });

    it('calls onSortChange when PGY Level header clicked', () => {
      const onSortChange = jest.fn();
      render(
        <PeopleTable {...defaultProps} onSortChange={onSortChange} />
      );

      fireEvent.click(screen.getByText('PGY Level'));

      expect(onSortChange).toHaveBeenCalledWith('pgyLevel');
    });

    it('calls onSortChange when Email header clicked', () => {
      const onSortChange = jest.fn();
      render(
        <PeopleTable {...defaultProps} onSortChange={onSortChange} />
      );

      fireEvent.click(screen.getByText('Email'));

      expect(onSortChange).toHaveBeenCalledWith('email');
    });
  });
});
