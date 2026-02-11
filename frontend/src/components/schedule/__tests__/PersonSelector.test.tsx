/**
 * @jest-environment jsdom
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { PersonSelector } from '../PersonSelector';
import { PersonType, FacultyRole } from '@/types/api';
import type { Person } from '@/types/api';

describe('PersonSelector', () => {
  const mockOnSelect = jest.fn();

  const mockPeople: Person[] = [
    {
      id: '1',
      name: 'Dr. Alice Smith',
      email: 'alice@example.com',
      type: PersonType.RESIDENT,
      pgyLevel: 1,
      performsProcedures: false,
      specialties: null,
      primaryDuty: null,
      facultyRole: null,
      createdAt: '2025-01-01T00:00:00Z',
      updatedAt: '2025-01-01T00:00:00Z',
    },
    {
      id: '2',
      name: 'Dr. Bob Jones',
      email: 'bob@example.com',
      type: PersonType.RESIDENT,
      pgyLevel: 2,
      performsProcedures: false,
      specialties: null,
      primaryDuty: null,
      facultyRole: null,
      createdAt: '2025-01-01T00:00:00Z',
      updatedAt: '2025-01-01T00:00:00Z',
    },
    {
      id: '3',
      name: 'Dr. Carol Lee',
      email: 'carol@example.com',
      type: PersonType.RESIDENT,
      pgyLevel: 3,
      performsProcedures: true,
      specialties: null,
      primaryDuty: null,
      facultyRole: null,
      createdAt: '2025-01-01T00:00:00Z',
      updatedAt: '2025-01-01T00:00:00Z',
    },
    {
      id: '4',
      name: 'Dr. David Chen',
      email: 'david@example.com',
      type: PersonType.FACULTY,
      pgyLevel: null,
      performsProcedures: true,
      specialties: ['sports medicine'],
      primaryDuty: null,
      facultyRole: FacultyRole.CORE,
      createdAt: '2025-01-01T00:00:00Z',
      updatedAt: '2025-01-01T00:00:00Z',
    },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
  });

  const defaultProps = {
    people: mockPeople,
    selectedPersonId: null as string | null,
    onSelect: mockOnSelect,
    tier: 1,
  };

  const renderComponent = (props = {}) => {
    return render(<PersonSelector {...defaultProps} {...props} />);
  };

  describe('tier-based visibility', () => {
    it('does not render for tier 0 users', () => {
      const { container } = renderComponent({ tier: 0 });

      expect(container.firstChild).toBeNull();
    });

    it('renders for tier 1 users', () => {
      renderComponent({ tier: 1 });

      expect(screen.getByRole('button', { name: /select person/i })).toBeInTheDocument();
    });

    it('renders for tier 2 users', () => {
      renderComponent({ tier: 2 });

      expect(screen.getByRole('button', { name: /select person/i })).toBeInTheDocument();
    });
  });

  describe('rendering', () => {
    it('renders trigger button with "Select Person" when no selection', () => {
      renderComponent();

      expect(screen.getByText('Select Person')).toBeInTheDocument();
    });

    it('renders selected person name when person selected', () => {
      renderComponent({ selectedPersonId: '1' });

      expect(screen.getByText('Dr. Alice Smith')).toBeInTheDocument();
    });

    it('shows loading state when isLoading is true', () => {
      renderComponent({ isLoading: true });

      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });
  });

  describe('dropdown interaction', () => {
    it('opens dropdown when button clicked', () => {
      renderComponent();

      const button = screen.getByRole('button', { name: /select person/i });
      fireEvent.click(button);

      expect(screen.getByRole('listbox')).toBeInTheDocument();
    });

    it('closes dropdown when clicking outside', async () => {
      renderComponent();

      const button = screen.getByRole('button', { name: /select person/i });
      fireEvent.click(button);

      expect(screen.getByRole('listbox')).toBeInTheDocument();

      fireEvent.mouseDown(document.body);

      await waitFor(() => {
        expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
      });
    });

    it('has proper ARIA attributes', () => {
      renderComponent();

      const button = screen.getByRole('button', { name: /select person/i });

      expect(button).toHaveAttribute('aria-haspopup', 'listbox');
      expect(button).toHaveAttribute('aria-expanded', 'false');

      fireEvent.click(button);

      expect(button).toHaveAttribute('aria-expanded', 'true');
    });
  });

  describe('search functionality', () => {
    it('filters people by name', () => {
      renderComponent();

      fireEvent.click(screen.getByRole('button', { name: /select person/i }));

      const searchInput = screen.getByPlaceholderText('Search people...');
      fireEvent.change(searchInput, { target: { value: 'Alice' } });

      expect(screen.getByText('Dr. Alice Smith')).toBeInTheDocument();
      expect(screen.queryByText('Dr. Bob Jones')).not.toBeInTheDocument();
    });

    it('filters people by email', () => {
      renderComponent();

      fireEvent.click(screen.getByRole('button', { name: /select person/i }));

      const searchInput = screen.getByPlaceholderText('Search people...');
      fireEvent.change(searchInput, { target: { value: 'bob@example' } });

      expect(screen.getByText('Dr. Bob Jones')).toBeInTheDocument();
      expect(screen.queryByText('Dr. Alice Smith')).not.toBeInTheDocument();
    });

    it('shows "No results found" when search has no matches', () => {
      renderComponent();

      fireEvent.click(screen.getByRole('button', { name: /select person/i }));

      const searchInput = screen.getByPlaceholderText('Search people...');
      fireEvent.change(searchInput, { target: { value: 'Nonexistent' } });

      expect(screen.getByText('No results found')).toBeInTheDocument();
    });

    it('clears search when X button clicked', () => {
      renderComponent();

      fireEvent.click(screen.getByRole('button', { name: /select person/i }));

      const searchInput = screen.getByPlaceholderText('Search people...') as HTMLInputElement;
      fireEvent.change(searchInput, { target: { value: 'test' } });

      expect(searchInput.value).toBe('test');

      const clearButton = screen.getByLabelText('Clear search');
      fireEvent.click(clearButton);

      expect(searchInput.value).toBe('');
    });
  });

  describe('selection', () => {
    it('calls onSelect with person ID when person clicked', () => {
      renderComponent();

      fireEvent.click(screen.getByRole('button', { name: /select person/i }));
      fireEvent.click(screen.getByText('Dr. Alice Smith'));

      expect(mockOnSelect).toHaveBeenCalledWith('1');
    });

    it('closes dropdown after selection', async () => {
      renderComponent();

      fireEvent.click(screen.getByRole('button', { name: /select person/i }));
      fireEvent.click(screen.getByText('Dr. Alice Smith'));

      await waitFor(() => {
        expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
      });
    });

    it('highlights selected option', () => {
      renderComponent({ selectedPersonId: '1' });

      fireEvent.click(screen.getByRole('button', { name: /select person/i }));

      const selectedOption = screen.getByRole('option', { selected: true });
      expect(selectedOption).toHaveTextContent('Dr. Alice Smith');
    });
  });

  describe('grouping', () => {
    it('groups residents by PGY level', () => {
      renderComponent();

      fireEvent.click(screen.getByRole('button', { name: /select person/i }));

      // PGY level headers should appear
      expect(screen.getByText('PGY-1')).toBeInTheDocument();
      expect(screen.getByText('PGY-2')).toBeInTheDocument();
      expect(screen.getByText('PGY-3')).toBeInTheDocument();
    });

    it('shows Faculty section', () => {
      renderComponent();

      fireEvent.click(screen.getByRole('button', { name: /select person/i }));

      expect(screen.getByText('Faculty')).toBeInTheDocument();
    });

    it('sorts residents by PGY level descending', () => {
      renderComponent();

      fireEvent.click(screen.getByRole('button', { name: /select person/i }));

      const options = screen.getAllByRole('option');
      const nameOrder = options.map((opt) => opt.textContent);

      // PGY-3 should come before PGY-2 and PGY-1
      const pgy3Index = nameOrder.findIndex((n) => n?.includes('Carol'));
      const pgy2Index = nameOrder.findIndex((n) => n?.includes('Bob'));
      const pgy1Index = nameOrder.findIndex((n) => n?.includes('Alice'));

      expect(pgy3Index).toBeLessThan(pgy2Index);
      expect(pgy2Index).toBeLessThan(pgy1Index);
    });

    it('puts residents before faculty', () => {
      renderComponent();

      fireEvent.click(screen.getByRole('button', { name: /select person/i }));

      const options = screen.getAllByRole('option');
      const nameOrder = options.map((opt) => opt.textContent);

      // Faculty should be last
      const facultyIndex = nameOrder.findIndex((n) => n?.includes('David'));
      const residentIndex = nameOrder.findIndex((n) => n?.includes('Alice'));

      expect(residentIndex).toBeLessThan(facultyIndex);
    });
  });
});
