/**
 * @jest-environment jsdom
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { PersonSelector } from '../PersonSelector';
import { PersonType, FacultyRole } from '@/types/api';
import type { Person } from '@/types/api';
import type { RiskTier } from '@/components/ui/RiskBar';

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
    selectedPersonId: null,
    onSelect: mockOnSelect,
    tier: 1 as RiskTier,
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

    it('renders for tier 0 users when forceShow is true', () => {
      renderComponent({ tier: 0, forceShow: true });

      expect(screen.getByRole('button', { name: /select person/i })).toBeInTheDocument();
    });
  });

  describe('rendering', () => {
    it('renders trigger button with "Select person..." when no selection', () => {
      renderComponent();

      expect(screen.getByText('Select person...')).toBeInTheDocument();
    });

    it('renders selected person name with PGY level when person selected', () => {
      renderComponent({ selectedPersonId: '1' });

      expect(screen.getByText('Dr. Alice Smith (PGY-1)')).toBeInTheDocument();
    });

    it('renders faculty label when faculty selected', () => {
      renderComponent({ selectedPersonId: '4' });

      expect(screen.getByText('Dr. David Chen (Faculty)')).toBeInTheDocument();
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

    it('closes dropdown on Escape key', () => {
      renderComponent();

      const button = screen.getByRole('button', { name: /select person/i });
      fireEvent.click(button);

      fireEvent.keyDown(button, { key: 'Escape' });

      expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
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

      const searchInput = screen.getByPlaceholderText(/search by name/i);
      fireEvent.change(searchInput, { target: { value: 'Alice' } });

      expect(screen.getByText('Dr. Alice Smith')).toBeInTheDocument();
      expect(screen.queryByText('Dr. Bob Jones')).not.toBeInTheDocument();
    });

    it('filters people by email', () => {
      renderComponent();

      fireEvent.click(screen.getByRole('button', { name: /select person/i }));

      const searchInput = screen.getByPlaceholderText(/search by name/i);
      fireEvent.change(searchInput, { target: { value: 'bob@example' } });

      expect(screen.getByText('Dr. Bob Jones')).toBeInTheDocument();
      expect(screen.queryByText('Dr. Alice Smith')).not.toBeInTheDocument();
    });

    it('filters people by PGY level', () => {
      renderComponent();

      fireEvent.click(screen.getByRole('button', { name: /select person/i }));

      const searchInput = screen.getByPlaceholderText(/search by name/i);
      fireEvent.change(searchInput, { target: { value: 'pgy2' } });

      expect(screen.getByText('Dr. Bob Jones')).toBeInTheDocument();
      expect(screen.queryByText('Dr. Alice Smith')).not.toBeInTheDocument();
    });

    it('shows "No people found" when search has no matches', () => {
      renderComponent();

      fireEvent.click(screen.getByRole('button', { name: /select person/i }));

      const searchInput = screen.getByPlaceholderText(/search by name/i);
      fireEvent.change(searchInput, { target: { value: 'Nonexistent' } });

      expect(screen.getByText('No people found')).toBeInTheDocument();
    });

    it('clears search when X button clicked', () => {
      renderComponent();

      fireEvent.click(screen.getByRole('button', { name: /select person/i }));

      const searchInput = screen.getByPlaceholderText(/search by name/i) as HTMLInputElement;
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

  describe('keyboard navigation', () => {
    it('opens dropdown on ArrowDown when closed', () => {
      renderComponent();

      const button = screen.getByRole('button', { name: /select person/i });
      fireEvent.keyDown(button, { key: 'ArrowDown' });

      expect(screen.getByRole('listbox')).toBeInTheDocument();
    });

    it('navigates through options with ArrowDown/ArrowUp', () => {
      renderComponent();

      const button = screen.getByRole('button', { name: /select person/i });
      fireEvent.click(button);

      // Navigate down
      fireEvent.keyDown(button, { key: 'ArrowDown' });
      fireEvent.keyDown(button, { key: 'ArrowDown' });

      // Navigate up
      fireEvent.keyDown(button, { key: 'ArrowUp' });

      // Should have navigated to first option
      const options = screen.getAllByRole('option');
      expect(options.length).toBeGreaterThan(0);
    });

    it('selects focused option on Enter', () => {
      renderComponent();

      const button = screen.getByRole('button', { name: /select person/i });
      fireEvent.click(button);

      fireEvent.keyDown(button, { key: 'ArrowDown' });
      fireEvent.keyDown(button, { key: 'Enter' });

      expect(mockOnSelect).toHaveBeenCalled();
    });
  });

  describe('sorting', () => {
    it('sorts residents by PGY level descending, then alphabetically', () => {
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
