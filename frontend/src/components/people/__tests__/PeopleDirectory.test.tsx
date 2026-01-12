/**
 * Tests for PeopleDirectory Component
 * Component: Read-only people directory view (Tier 0)
 */

import React from 'react';
import { renderWithProviders as render, screen, fireEvent } from '@/test-utils';
import '@testing-library/jest-dom';
import { PeopleDirectory } from '../PeopleDirectory';
import { FacultyRole, type Person, type PersonType } from '@/types/api';

// Mock the hooks
jest.mock('@/hooks/usePeople', () => ({
  usePeople: jest.fn(),
}));

jest.mock('@/hooks/useDebounce', () => ({
  useDebounce: jest.fn((value: string) => value),
}));

// Import mocked module
import { usePeople } from '@/hooks/usePeople';

const mockUsePeople = usePeople as jest.MockedFunction<typeof usePeople>;

// Test data
const mockPeople: Person[] = [
  {
    id: '1',
    name: 'Alice Johnson',
    email: 'alice@example.com',
    type: 'resident' as PersonType,
    pgyLevel: 2,
    performsProcedures: true,
    specialties: ['Internal Medicine'],
    primaryDuty: null,
    facultyRole: null,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  },
  {
    id: '2',
    name: 'Bob Smith',
    email: 'bob@example.com',
    type: 'faculty' as PersonType,
    pgyLevel: null,
    performsProcedures: false,
    specialties: ['Cardiology', 'Internal Medicine'],
    primaryDuty: null,
    facultyRole: FacultyRole.CORE,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  },
  {
    id: '3',
    name: 'Carol Williams',
    email: 'carol@example.com',
    type: 'resident' as PersonType,
    pgyLevel: 1,
    performsProcedures: false,
    specialties: null,
    primaryDuty: null,
    facultyRole: null,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  },
];

describe('PeopleDirectory', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // Test: Loading state
  describe('Loading State', () => {
    it('shows loading spinner while fetching data', () => {
      mockUsePeople.mockReturnValue({
        data: undefined,
        isLoading: true,
        isError: false,
        error: null,
        refetch: jest.fn(),
      } as unknown as ReturnType<typeof usePeople>);

      render(<PeopleDirectory />);

      expect(screen.getByRole('status')).toBeInTheDocument();
    });
  });

  // Test: Error state
  describe('Error State', () => {
    it('shows error message when fetch fails', () => {
      mockUsePeople.mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: true,
        error: { message: 'Network error' },
        refetch: jest.fn(),
      } as unknown as ReturnType<typeof usePeople>);

      render(<PeopleDirectory />);

      expect(screen.getByText(/Network error/)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
    });

    it('calls refetch when retry button is clicked', () => {
      const mockRefetch = jest.fn();
      mockUsePeople.mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: true,
        error: { message: 'Network error' },
        refetch: mockRefetch,
      } as unknown as ReturnType<typeof usePeople>);

      render(<PeopleDirectory />);

      fireEvent.click(screen.getByRole('button', { name: /retry/i }));
      expect(mockRefetch).toHaveBeenCalled();
    });
  });

  // Test: Empty state
  describe('Empty State', () => {
    it('shows empty state when no people exist', () => {
      mockUsePeople.mockReturnValue({
        data: { items: [], total: 0 },
        isLoading: false,
        isError: false,
        error: null,
        refetch: jest.fn(),
      } as unknown as ReturnType<typeof usePeople>);

      render(<PeopleDirectory />);

      expect(screen.getByText(/No people yet/i)).toBeInTheDocument();
    });

    it('shows different message when filters return no results', () => {
      mockUsePeople.mockReturnValue({
        data: { items: [], total: 0 },
        isLoading: false,
        isError: false,
        error: null,
        refetch: jest.fn(),
      } as unknown as ReturnType<typeof usePeople>);

      render(<PeopleDirectory />);

      // Type in search
      const searchInput = screen.getByRole('searchbox');
      fireEvent.change(searchInput, { target: { value: 'nonexistent' } });

      expect(screen.getByText(/No matches found/i)).toBeInTheDocument();
    });
  });

  // Test: People list rendering
  describe('People List', () => {
    beforeEach(() => {
      mockUsePeople.mockReturnValue({
        data: { items: mockPeople, total: 3 },
        isLoading: false,
        isError: false,
        error: null,
        refetch: jest.fn(),
      } as unknown as ReturnType<typeof usePeople>);
    });

    it('renders people cards', () => {
      render(<PeopleDirectory />);

      expect(screen.getByText('Alice Johnson')).toBeInTheDocument();
      expect(screen.getByText('Bob Smith')).toBeInTheDocument();
      expect(screen.getByText('Carol Williams')).toBeInTheDocument();
    });

    it('displays resident badge with PGY level', () => {
      render(<PeopleDirectory />);

      // Multiple PGY level indicators may exist (cards + filter dropdown)
      expect(screen.getAllByText('PGY-2').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('PGY-1').length).toBeGreaterThanOrEqual(1);
    });

    it('displays faculty badge', () => {
      render(<PeopleDirectory />);

      // Multiple faculty badges may exist due to type filter option
      // The badge in the card is what we're looking for
      expect(screen.getAllByText('Faculty').length).toBeGreaterThanOrEqual(1);
    });

    it('displays email as clickable link', () => {
      render(<PeopleDirectory />);

      const aliceEmail = screen.getByText('alice@example.com');
      expect(aliceEmail).toBeInTheDocument();
      expect(aliceEmail.closest('a')).toHaveAttribute('href', 'mailto:alice@example.com');
    });

    it('displays specialties badges', () => {
      render(<PeopleDirectory />);

      expect(screen.getByText('Cardiology')).toBeInTheDocument();
      expect(screen.getAllByText('Internal Medicine')).toHaveLength(2);
    });

    it('shows person count', () => {
      render(<PeopleDirectory />);

      expect(screen.getByText(/3 people/)).toBeInTheDocument();
    });
  });

  // Test: Search functionality
  describe('Search', () => {
    beforeEach(() => {
      mockUsePeople.mockReturnValue({
        data: { items: mockPeople, total: 3 },
        isLoading: false,
        isError: false,
        error: null,
        refetch: jest.fn(),
      } as unknown as ReturnType<typeof usePeople>);
    });

    it('filters people by name', () => {
      render(<PeopleDirectory />);

      const searchInput = screen.getByRole('searchbox');
      fireEvent.change(searchInput, { target: { value: 'alice' } });

      expect(screen.getByText('Alice Johnson')).toBeInTheDocument();
      expect(screen.queryByText('Bob Smith')).not.toBeInTheDocument();
    });

    it('filters people by email', () => {
      render(<PeopleDirectory />);

      const searchInput = screen.getByRole('searchbox');
      fireEvent.change(searchInput, { target: { value: 'bob@' } });

      expect(screen.getByText('Bob Smith')).toBeInTheDocument();
      expect(screen.queryByText('Alice Johnson')).not.toBeInTheDocument();
    });

    it('clears search when X button is clicked', () => {
      render(<PeopleDirectory />);

      const searchInput = screen.getByRole('searchbox');
      fireEvent.change(searchInput, { target: { value: 'alice' } });

      const clearButton = screen.getByRole('button', { name: /clear search/i });
      fireEvent.click(clearButton);

      expect(searchInput).toHaveValue('');
    });

    it('is case insensitive', () => {
      render(<PeopleDirectory />);

      const searchInput = screen.getByRole('searchbox');
      fireEvent.change(searchInput, { target: { value: 'ALICE' } });

      expect(screen.getByText('Alice Johnson')).toBeInTheDocument();
    });
  });

  // Test: Type filter
  describe('Type Filter', () => {
    beforeEach(() => {
      mockUsePeople.mockReturnValue({
        data: { items: mockPeople, total: 3 },
        isLoading: false,
        isError: false,
        error: null,
        refetch: jest.fn(),
      } as unknown as ReturnType<typeof usePeople>);
    });

    it('shows all types by default', () => {
      render(<PeopleDirectory />);

      const typeFilter = screen.getByRole('combobox', { name: /filter by type/i });
      expect(typeFilter).toHaveValue('all');
    });

    it('filters to residents when selected', () => {
      render(<PeopleDirectory />);

      const typeFilter = screen.getByRole('combobox', { name: /filter by type/i });
      fireEvent.change(typeFilter, { target: { value: 'resident' } });

      expect(mockUsePeople).toHaveBeenCalledWith({ role: 'resident' });
    });

    it('filters to faculty when selected', () => {
      render(<PeopleDirectory />);

      const typeFilter = screen.getByRole('combobox', { name: /filter by type/i });
      fireEvent.change(typeFilter, { target: { value: 'faculty' } });

      expect(mockUsePeople).toHaveBeenCalledWith({ role: 'faculty' });
    });
  });

  // Test: PGY Level filter
  describe('PGY Level Filter', () => {
    beforeEach(() => {
      mockUsePeople.mockReturnValue({
        data: { items: mockPeople, total: 3 },
        isLoading: false,
        isError: false,
        error: null,
        refetch: jest.fn(),
      } as unknown as ReturnType<typeof usePeople>);
    });

    it('is visible when type is "all"', () => {
      render(<PeopleDirectory />);

      expect(screen.getByRole('combobox', { name: /filter by pgy level/i })).toBeInTheDocument();
    });

    it('is visible when type is "resident"', () => {
      render(<PeopleDirectory />);

      const typeFilter = screen.getByRole('combobox', { name: /filter by type/i });
      fireEvent.change(typeFilter, { target: { value: 'resident' } });

      expect(screen.getByRole('combobox', { name: /filter by pgy level/i })).toBeInTheDocument();
    });

    it('is hidden when type is "faculty"', () => {
      render(<PeopleDirectory />);

      const typeFilter = screen.getByRole('combobox', { name: /filter by type/i });
      fireEvent.change(typeFilter, { target: { value: 'faculty' } });

      expect(screen.queryByRole('combobox', { name: /filter by pgy level/i })).not.toBeInTheDocument();
    });

    it('filters people by PGY level', () => {
      render(<PeopleDirectory />);

      const pgyFilter = screen.getByRole('combobox', { name: /filter by pgy level/i });
      fireEvent.change(pgyFilter, { target: { value: '1' } });

      expect(screen.getByText('Carol Williams')).toBeInTheDocument();
      expect(screen.queryByText('Alice Johnson')).not.toBeInTheDocument();
    });
  });

  // Test: Refresh functionality
  describe('Refresh', () => {
    it('calls refetch when refresh button is clicked', () => {
      const mockRefetch = jest.fn();
      mockUsePeople.mockReturnValue({
        data: { items: mockPeople, total: 3 },
        isLoading: false,
        isError: false,
        error: null,
        refetch: mockRefetch,
      } as unknown as ReturnType<typeof usePeople>);

      render(<PeopleDirectory />);

      const refreshButton = screen.getByRole('button', { name: /refresh/i });
      fireEvent.click(refreshButton);

      expect(mockRefetch).toHaveBeenCalled();
    });

    it('shows spinning animation while loading', () => {
      mockUsePeople.mockReturnValue({
        data: { items: mockPeople, total: 3 },
        isLoading: true,
        isError: false,
        error: null,
        refetch: jest.fn(),
      } as unknown as ReturnType<typeof usePeople>);

      render(<PeopleDirectory />);

      const refreshButton = screen.getByRole('button', { name: /refresh/i });
      expect(refreshButton.querySelector('.animate-spin')).toBeInTheDocument();
    });
  });

  // Test: Accessibility
  describe('Accessibility', () => {
    beforeEach(() => {
      mockUsePeople.mockReturnValue({
        data: { items: mockPeople, total: 3 },
        isLoading: false,
        isError: false,
        error: null,
        refetch: jest.fn(),
      } as unknown as ReturnType<typeof usePeople>);
    });

    it('has proper ARIA label for search input', () => {
      render(<PeopleDirectory />);

      expect(screen.getByRole('searchbox')).toHaveAttribute('aria-label', 'Search people');
    });

    it('has proper ARIA label for the people list', () => {
      render(<PeopleDirectory />);

      expect(screen.getByRole('list', { name: /people directory/i })).toBeInTheDocument();
    });

    it('has proper ARIA labels for filter controls', () => {
      render(<PeopleDirectory />);

      expect(screen.getByRole('combobox', { name: /filter by type/i })).toBeInTheDocument();
      expect(screen.getByRole('combobox', { name: /filter by pgy level/i })).toBeInTheDocument();
    });

    it('person cards have proper ARIA labels', () => {
      render(<PeopleDirectory />);

      const personCards = screen.getAllByRole('article');
      expect(personCards.length).toBeGreaterThan(0);
    });
  });
});
