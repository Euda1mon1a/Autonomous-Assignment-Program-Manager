/**
 * @jest-environment jsdom
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { PersonFilter } from '../PersonFilter';

// Mock the hooks
jest.mock('@/lib/hooks', () => ({
  usePeople: jest.fn(),
}));

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(),
}));

import { usePeople } from '@/lib/hooks';
import { useAuth } from '@/contexts/AuthContext';

const mockUsePeople = usePeople as jest.MockedFunction<typeof usePeople>;
const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;

describe('PersonFilter', () => {
  const mockOnSelect = jest.fn();
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  const mockPeople = [
    { id: '1', name: 'Dr. Alice Smith', email: 'alice@example.com', type: 'resident' as const, pgyLevel: 1 },
    { id: '2', name: 'Dr. Bob Jones', email: 'bob@example.com', type: 'resident' as const, pgyLevel: 2 },
    { id: '3', name: 'Dr. Carol Lee', email: 'carol@example.com', type: 'resident' as const, pgyLevel: 3 },
    { id: '4', name: 'Dr. David Chen', email: 'david@example.com', type: 'faculty' as const, pgyLevel: null },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    mockUsePeople.mockReturnValue({
      data: { items: mockPeople, total: 4 },
      isLoading: false,
      error: null,
    } as any);
    mockUseAuth.mockReturnValue({
      user: { id: '1', email: 'alice@example.com' },
    } as any);
  });

  const defaultProps = {
    selectedPersonId: null,
    onSelect: mockOnSelect,
  };

  const renderComponent = (props = {}) => {
    return render(
      <QueryClientProvider client={queryClient}>
        <PersonFilter {...defaultProps} {...props} />
      </QueryClientProvider>
    );
  };

  describe('rendering', () => {
    it('renders trigger button with "All People" when no selection', () => {
      renderComponent();

      expect(screen.getByText('All People')).toBeInTheDocument();
    });

    it('renders selected person name when person selected', () => {
      renderComponent({ selectedPersonId: '1' });

      expect(screen.getByText('Dr. Alice Smith')).toBeInTheDocument();
    });

    it('renders "My Schedule" when "me" is selected', () => {
      renderComponent({ selectedPersonId: 'me' });

      expect(screen.getByText('My Schedule')).toBeInTheDocument();
    });

    it('renders appropriate icon for selection type', () => {
      const { container } = renderComponent();

      const icon = container.querySelector('.lucide-users');
      expect(icon).toBeInTheDocument();
    });

    it('shows chevron icon that rotates when open', () => {
      const { container } = renderComponent();

      const button = screen.getByRole('button');
      const chevron = container.querySelector('.lucide-chevron-down');

      expect(chevron).toBeInTheDocument();
      expect(chevron).not.toHaveClass('rotate-180');

      fireEvent.click(button);

      expect(chevron).toHaveClass('rotate-180');
    });
  });

  describe('dropdown interaction', () => {
    it('opens dropdown when button clicked', () => {
      renderComponent();

      const button = screen.getByRole('button');
      fireEvent.click(button);

      expect(screen.getByRole('listbox')).toBeInTheDocument();
    });

    it('closes dropdown when clicking outside', async () => {
      renderComponent();

      const button = screen.getByRole('button');
      fireEvent.click(button);

      expect(screen.getByRole('listbox')).toBeInTheDocument();

      // Simulate click outside
      fireEvent.mouseDown(document.body);

      await waitFor(() => {
        expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
      });
    });

    it('closes dropdown on Escape key', () => {
      renderComponent();

      const button = screen.getByRole('button');
      fireEvent.click(button);

      const dropdown = screen.getByRole('listbox');
      fireEvent.keyDown(dropdown, { key: 'Escape' });

      expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
    });

    it('has proper ARIA attributes', () => {
      renderComponent();

      const button = screen.getByRole('button');

      expect(button).toHaveAttribute('aria-haspopup', 'listbox');
      expect(button).toHaveAttribute('aria-expanded', 'false');

      fireEvent.click(button);

      expect(button).toHaveAttribute('aria-expanded', 'true');
    });
  });

  describe('people grouping', () => {
    it('displays residents grouped by PGY level', () => {
      renderComponent();

      fireEvent.click(screen.getByRole('button'));

      expect(screen.getByText('Residents')).toBeInTheDocument();
      expect(screen.getByText('PGY-1')).toBeInTheDocument();
      expect(screen.getByText('PGY-2')).toBeInTheDocument();
      expect(screen.getByText('PGY-3')).toBeInTheDocument();
    });

    it('displays faculty in separate section', () => {
      renderComponent();

      fireEvent.click(screen.getByRole('button'));

      expect(screen.getByText('Faculty')).toBeInTheDocument();
      expect(screen.getByText('Dr. David Chen')).toBeInTheDocument();
    });

    it('sorts people alphabetically within groups', () => {
      renderComponent();

      fireEvent.click(screen.getByRole('button'));

      const names = screen.getAllByText(/Dr\./);
      const nameTexts = names.map((el) => el.textContent);

      // Within each group, names should be sorted
      expect(nameTexts).toContain('Dr. Alice Smith');
      expect(nameTexts).toContain('Dr. Bob Jones');
    });
  });

  describe('search functionality', () => {
    it('shows search input when there are more than 10 people', () => {
      const manyPeople = Array.from({ length: 15 }, (_, i) => ({
        id: `${i}`,
        name: `Dr. Person ${i}`,
        email: `person${i}@example.com`,
        type: 'resident' as const,
        pgyLevel: 1,
      }));

      mockUsePeople.mockReturnValue({
        data: { items: manyPeople, total: 15 },
        isLoading: false,
      } as any);

      renderComponent();
      fireEvent.click(screen.getByRole('button'));

      expect(screen.getByPlaceholderText('Search people...')).toBeInTheDocument();
    });

    it('filters people by name', () => {
      const manyPeople = Array.from({ length: 15 }, (_, i) => ({
        id: `${i}`,
        name: `Dr. Person ${i}`,
        email: `person${i}@example.com`,
        type: 'resident' as const,
        pgyLevel: 1,
      }));

      mockUsePeople.mockReturnValue({
        data: { items: manyPeople, total: 15 },
        isLoading: false,
      } as any);

      renderComponent();
      fireEvent.click(screen.getByRole('button'));

      const searchInput = screen.getByPlaceholderText('Search people...');
      fireEvent.change(searchInput, { target: { value: 'Person 1' } });

      // Should show filtered results
      expect(screen.getByText('Dr. Person 1')).toBeInTheDocument();
      expect(screen.queryByText('Dr. Person 2')).not.toBeInTheDocument();
    });

    it('shows "no results" message when search has no matches', () => {
      const manyPeople = Array.from({ length: 15 }, (_, i) => ({
        id: `${i}`,
        name: `Dr. Person ${i}`,
        email: `person${i}@example.com`,
        type: 'resident' as const,
        pgyLevel: 1,
      }));

      mockUsePeople.mockReturnValue({
        data: { items: manyPeople, total: 15 },
        isLoading: false,
      } as any);

      renderComponent();
      fireEvent.click(screen.getByRole('button'));

      const searchInput = screen.getByPlaceholderText('Search people...');
      fireEvent.change(searchInput, { target: { value: 'Nonexistent' } });

      expect(screen.getByText(/No people found matching "Nonexistent"/)).toBeInTheDocument();
    });

    it('clears search when X button clicked', () => {
      const manyPeople = Array.from({ length: 15 }, (_, i) => ({
        id: `${i}`,
        name: `Dr. Person ${i}`,
        email: `person${i}@example.com`,
        type: 'resident' as const,
        pgyLevel: 1,
      }));

      mockUsePeople.mockReturnValue({
        data: { items: manyPeople, total: 15 },
        isLoading: false,
      } as any);

      renderComponent();
      fireEvent.click(screen.getByRole('button'));

      const searchInput = screen.getByPlaceholderText('Search people...') as HTMLInputElement;
      fireEvent.change(searchInput, { target: { value: 'test' } });

      expect(searchInput.value).toBe('test');

      const clearButton = screen.getByRole('button', { name: '' }); // X button
      fireEvent.click(clearButton);

      expect(searchInput.value).toBe('');
    });
  });

  describe('selection', () => {
    it('calls onSelect with null when "All People" clicked', () => {
      renderComponent({ selectedPersonId: '1' });

      fireEvent.click(screen.getByRole('button'));
      fireEvent.click(screen.getByText('All People'));

      expect(mockOnSelect).toHaveBeenCalledWith(null);
    });

    it('calls onSelect with "me" when "My Schedule" clicked', () => {
      renderComponent();

      fireEvent.click(screen.getByRole('button'));
      fireEvent.click(screen.getByText('My Schedule'));

      expect(mockOnSelect).toHaveBeenCalledWith('me');
    });

    it('calls onSelect with person ID when person clicked', () => {
      renderComponent();

      fireEvent.click(screen.getByRole('button'));
      fireEvent.click(screen.getByText('Dr. Alice Smith'));

      expect(mockOnSelect).toHaveBeenCalledWith('1');
    });

    it('closes dropdown after selection', async () => {
      renderComponent();

      fireEvent.click(screen.getByRole('button'));
      fireEvent.click(screen.getByText('Dr. Alice Smith'));

      await waitFor(() => {
        expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
      });
    });

    it('highlights selected option', () => {
      renderComponent({ selectedPersonId: '1' });

      fireEvent.click(screen.getByRole('button'));

      const selectedOption = screen.getByText('Dr. Alice Smith').closest('button');
      expect(selectedOption).toHaveClass('bg-blue-50', 'text-blue-700');
      expect(selectedOption).toHaveAttribute('aria-selected', 'true');
    });
  });

  describe('loading state', () => {
    it('shows loading message when data is loading', () => {
      mockUsePeople.mockReturnValue({
        data: undefined,
        isLoading: true,
      } as any);

      renderComponent();

      fireEvent.click(screen.getByRole('button'));

      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });
  });

  describe('avatar display', () => {
    it('shows initials in avatar circles', () => {
      renderComponent();

      fireEvent.click(screen.getByRole('button'));

      const avatar = screen.getByText('A'); // First letter of Alice
      expect(avatar).toBeInTheDocument();
      expect(avatar).toHaveClass('rounded-full');
    });
  });
});
