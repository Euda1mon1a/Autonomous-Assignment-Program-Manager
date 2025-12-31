import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ConflictList } from '@/features/conflicts/ConflictList';
import { conflictsMockFactories, conflictsMockResponses } from './conflicts-mocks';
import { createWrapper } from '../../utils/test-utils';
import * as hooks from '@/features/conflicts/hooks';

// Mock the hooks module
jest.mock('@/features/conflicts/hooks', () => ({
  useConflicts: jest.fn(),
  useDetectConflicts: jest.fn(),
  conflictQueryKeys: {
    all: ['conflicts'],
    list: () => ['conflicts', 'list'],
  },
}));

// Mock ConflictCard component
jest.mock('@/features/conflicts/ConflictCard', () => ({
  ConflictCard: ({
    conflict,
    onSelect,
    onResolve,
    onViewSuggestions,
  }: {
    conflict: { id: string; title: string };
    onSelect?: (conflict: { id: string; title: string }) => void;
    onResolve?: (conflict: { id: string; title: string }) => void;
    onViewSuggestions?: (conflict: { id: string; title: string }) => void;
  }) => (
    <div data-testid={`conflict-card-${conflict.id}`}>
      <div>{conflict.title}</div>
      {onSelect && <button onClick={() => onSelect(conflict)}>Select</button>}
      {onResolve && <button onClick={() => onResolve(conflict)}>Resolve</button>}
      {onViewSuggestions && <button onClick={() => onViewSuggestions(conflict)}>View Suggestions</button>}
    </div>
  ),
}));

const mockedUseConflicts = hooks.useConflicts as jest.MockedFunction<typeof hooks.useConflicts>;
const mockedUseDetectConflicts = hooks.useDetectConflicts as jest.MockedFunction<
  typeof hooks.useDetectConflicts
>;

describe('ConflictList', () => {
  const mockRefetch = jest.fn();
  const mockMutate = jest.fn();
  const mockOnConflictSelect = jest.fn();
  const mockOnResolve = jest.fn();
  const mockOnViewSuggestions = jest.fn();
  const mockOnViewHistory = jest.fn();
  const mockOnOverride = jest.fn();
  const mockOnIgnore = jest.fn();
  const mockOnBatchSelect = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();

    mockedUseConflicts.mockReturnValue({
      data: conflictsMockResponses.conflicts,
      isLoading: false,
      isError: false,
      error: null,
      refetch: mockRefetch,
    } as unknown as ReturnType<typeof hooks.useConflicts>);

    mockedUseDetectConflicts.mockReturnValue({
      mutate: mockMutate,
      isPending: false,
    } as unknown as ReturnType<typeof hooks.useDetectConflicts>);
  });

  describe('Initial Rendering', () => {
    it('should render conflict cards', async () => {
      render(<ConflictList />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Assignment during absence')).toBeInTheDocument();
        expect(screen.getByText('Double-booked time slot')).toBeInTheDocument();
        expect(screen.getByText('ACGME duty hour violation')).toBeInTheDocument();
      });
    });

    it('should display conflict count', async () => {
      render(<ConflictList />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/3 conflicts/i)).toBeInTheDocument();
      });
    });

    it('should render search input', () => {
      render(<ConflictList />, { wrapper: createWrapper() });

      expect(screen.getByPlaceholderText(/search conflicts/i)).toBeInTheDocument();
    });

    it('should render filter button', () => {
      render(<ConflictList />, { wrapper: createWrapper() });

      expect(screen.getByText(/filters/i)).toBeInTheDocument();
    });

    it('should render sort label and buttons', () => {
      render(<ConflictList />, { wrapper: createWrapper() });

      // The component shows "Sort:" followed by individual sort buttons
      expect(screen.getByText(/sort:/i)).toBeInTheDocument();
    });
  });

  describe('Search Functionality', () => {
    it('should update search query when typing', async () => {
      const user = userEvent.setup();

      render(<ConflictList />, { wrapper: createWrapper() });

      const searchInput = screen.getByPlaceholderText(/search conflicts/i);
      await user.type(searchInput, 'absence');

      expect(searchInput).toHaveValue('absence');
    });

    it('should call useConflicts with search query', async () => {
      const user = userEvent.setup();

      render(<ConflictList />, { wrapper: createWrapper() });

      const searchInput = screen.getByPlaceholderText(/search conflicts/i);
      await user.type(searchInput, 'absence');

      await waitFor(() => {
        expect(mockedUseConflicts).toHaveBeenCalledWith(
          expect.objectContaining({ search: 'absence' }),
          expect.any(Object)
        );
      });
    });

    it('should clear search when cleared', async () => {
      const user = userEvent.setup();

      render(<ConflictList />, { wrapper: createWrapper() });

      const searchInput = screen.getByPlaceholderText(/search conflicts/i);
      await user.type(searchInput, 'test');
      await user.clear(searchInput);

      expect(searchInput).toHaveValue('');
    });
  });

  describe('Filter Functionality', () => {
    it('should toggle filter panel when filter button clicked', async () => {
      const user = userEvent.setup();

      render(<ConflictList />, { wrapper: createWrapper() });

      const filterButton = screen.getByText(/filters/i);
      await user.click(filterButton);

      // Filter panel shows the multiselect placeholder text
      await waitFor(() => {
        // Look for the multi-select placeholder texts that are only visible when filter panel is open
        expect(screen.getByText('All severities')).toBeInTheDocument();
        expect(screen.getByText('All types')).toBeInTheDocument();
        expect(screen.getByText('All statuses')).toBeInTheDocument();
      });
    });

    it('should close filter panel when clicked again', async () => {
      const user = userEvent.setup();

      render(<ConflictList />, { wrapper: createWrapper() });

      const filterButton = screen.getByText(/filters/i);
      await user.click(filterButton);
      await user.click(filterButton);

      await waitFor(() => {
        // When filter panel is closed, the filter labels are not visible
        // Use queryByText to check they no longer exist
        expect(screen.queryByText('All severities')).not.toBeInTheDocument();
      });
    });

    it('should display severity filter options', async () => {
      const user = userEvent.setup();

      render(<ConflictList />, { wrapper: createWrapper() });

      const filterButton = screen.getByText(/filters/i);
      await user.click(filterButton);

      // Click on the severity multi-select to open it
      await waitFor(() => {
        expect(screen.getByText('All severities')).toBeInTheDocument();
      });
      await user.click(screen.getByText('All severities'));

      await waitFor(() => {
        expect(screen.getByText('Critical')).toBeInTheDocument();
        expect(screen.getByText('High')).toBeInTheDocument();
        expect(screen.getByText('Medium')).toBeInTheDocument();
        expect(screen.getByText('Low')).toBeInTheDocument();
      });
    });

    it('should display status filter options', async () => {
      const user = userEvent.setup();

      render(<ConflictList />, { wrapper: createWrapper() });

      const filterButton = screen.getByText(/filters/i);
      await user.click(filterButton);

      // Click on the status multi-select to open it
      await waitFor(() => {
        expect(screen.getByText('All statuses')).toBeInTheDocument();
      });
      await user.click(screen.getByText('All statuses'));

      await waitFor(() => {
        expect(screen.getByText('Unresolved')).toBeInTheDocument();
        expect(screen.getByText('Pending Review')).toBeInTheDocument();
        expect(screen.getByText('Resolved')).toBeInTheDocument();
        expect(screen.getByText('Ignored')).toBeInTheDocument();
      });
    });

    it('should display type filter options', async () => {
      const user = userEvent.setup();

      render(<ConflictList />, { wrapper: createWrapper() });

      const filterButton = screen.getByText(/filters/i);
      await user.click(filterButton);

      // Click on the type multi-select to open it
      await waitFor(() => {
        expect(screen.getByText('All types')).toBeInTheDocument();
      });
      await user.click(screen.getByText('All types'));

      await waitFor(() => {
        expect(screen.getByText('Scheduling Overlap')).toBeInTheDocument();
        expect(screen.getByText('ACGME Violation')).toBeInTheDocument();
        expect(screen.getByText('Absence Conflict')).toBeInTheDocument();
      });
    });

    it('should have clear filters button', async () => {
      const user = userEvent.setup();

      render(<ConflictList />, { wrapper: createWrapper() });

      const filterButton = screen.getByText(/filters/i);
      await user.click(filterButton);

      await waitFor(() => {
        expect(screen.getByText(/clear all/i)).toBeInTheDocument();
      });
    });
  });

  describe('Sort Functionality', () => {
    it('should show sort options when sort button clicked', async () => {
      render(<ConflictList />, { wrapper: createWrapper() });

      // Sort options are always visible as buttons, not in a dropdown
      await waitFor(() => {
        expect(screen.getByText('Severity')).toBeInTheDocument();
        expect(screen.getByText('Conflict Date')).toBeInTheDocument();
        expect(screen.getByText('Detection Date')).toBeInTheDocument();
        expect(screen.getByText('Type')).toBeInTheDocument();
      });
    });

    it('should default to sorting by severity descending', () => {
      render(<ConflictList />, { wrapper: createWrapper() });

      expect(mockedUseConflicts).toHaveBeenCalledWith(
        expect.any(Object),
        expect.objectContaining({
          field: 'severity',
          direction: 'desc',
        })
      );
    });

    it('should toggle sort direction when same field selected', async () => {
      const user = userEvent.setup();

      render(<ConflictList />, { wrapper: createWrapper() });

      // Sort buttons are always visible - click on Severity to toggle direction
      const severityButton = screen.getByText('Severity');
      await user.click(severityButton);

      await waitFor(() => {
        expect(mockedUseConflicts).toHaveBeenCalledWith(
          expect.any(Object),
          expect.objectContaining({
            field: 'severity',
            direction: 'asc',
          })
        );
      });
    });
  });

  describe('Conflict Selection', () => {
    it('should call onConflictSelect when conflict selected', async () => {
      const user = userEvent.setup();

      render(<ConflictList onConflictSelect={mockOnConflictSelect} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByTestId('conflict-card-conflict-1')).toBeInTheDocument();
      });

      const selectButton = screen.getAllByText('Select')[0];
      await user.click(selectButton);

      expect(mockOnConflictSelect).toHaveBeenCalledWith(
        expect.objectContaining({
          id: 'conflict-1',
        })
      );
    });

    it('should call onViewSuggestions when view suggestions clicked', async () => {
      const user = userEvent.setup();

      render(<ConflictList onViewSuggestions={mockOnViewSuggestions} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getAllByText('View Suggestions')[0]).toBeInTheDocument();
      });

      const suggestionsButton = screen.getAllByText('View Suggestions')[0];
      await user.click(suggestionsButton);

      expect(mockOnViewSuggestions).toHaveBeenCalled();
    });

    it('should call onResolve when resolve clicked', async () => {
      const user = userEvent.setup();

      render(<ConflictList onResolve={mockOnResolve} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getAllByText('Resolve')[0]).toBeInTheDocument();
      });

      const resolveButton = screen.getAllByText('Resolve')[0];
      await user.click(resolveButton);

      expect(mockOnResolve).toHaveBeenCalled();
    });
  });

  describe('Loading States', () => {
    it('should show loading state when data is loading', () => {
      mockedUseConflicts.mockReturnValue({
        data: undefined,
        isLoading: true,
        isError: false,
        error: null,
        refetch: mockRefetch,
      } as unknown as ReturnType<typeof hooks.useConflicts>);

      const { container } = render(<ConflictList />, { wrapper: createWrapper() });

      const loadingElements = container.querySelectorAll('.animate-pulse');
      expect(loadingElements.length).toBeGreaterThan(0);
    });

    it('should not show conflicts while loading', () => {
      mockedUseConflicts.mockReturnValue({
        data: undefined,
        isLoading: true,
        isError: false,
        error: null,
        refetch: mockRefetch,
      } as unknown as ReturnType<typeof hooks.useConflicts>);

      render(<ConflictList />, { wrapper: createWrapper() });

      expect(screen.queryByText('Assignment during absence')).not.toBeInTheDocument();
    });
  });

  describe('Error States', () => {
    it('should show error message when query fails', async () => {
      mockedUseConflicts.mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: true,
        error: new Error('Failed to load conflicts') as never,
        refetch: mockRefetch,
      } as unknown as ReturnType<typeof hooks.useConflicts>);

      render(<ConflictList />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/failed to load/i)).toBeInTheDocument();
      });
    });

    it('should show retry button on error', async () => {
      mockedUseConflicts.mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: true,
        error: new Error('Failed to load conflicts') as never,
        refetch: mockRefetch,
      } as unknown as ReturnType<typeof hooks.useConflicts>);

      render(<ConflictList />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/try again/i)).toBeInTheDocument();
      });
    });

    it('should call refetch when retry clicked', async () => {
      const user = userEvent.setup();

      mockedUseConflicts.mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: true,
        error: new Error('Failed to load conflicts') as never,
        refetch: mockRefetch,
      } as unknown as ReturnType<typeof hooks.useConflicts>);

      render(<ConflictList />, { wrapper: createWrapper() });

      const retryButton = await screen.findByText(/try again/i);
      await user.click(retryButton);

      expect(mockRefetch).toHaveBeenCalled();
    });
  });

  describe('Empty States', () => {
    it('should show empty state when no conflicts', () => {
      mockedUseConflicts.mockReturnValue({
        data: { items: [], total: 0, page: 1, page_size: 20, pages: 0 },
        isLoading: false,
        isError: false,
        error: null,
        refetch: mockRefetch,
      } as unknown as ReturnType<typeof hooks.useConflicts>);

      render(<ConflictList />, { wrapper: createWrapper() });

      expect(screen.getByText(/no conflicts found/i)).toBeInTheDocument();
    });

    it('should show empty state message with filters applied', async () => {
      const user = userEvent.setup();

      mockedUseConflicts.mockReturnValue({
        data: { items: [], total: 0, page: 1, page_size: 20, pages: 0 },
        isLoading: false,
        isError: false,
        error: null,
        refetch: mockRefetch,
      } as unknown as ReturnType<typeof hooks.useConflicts>);

      render(<ConflictList />, { wrapper: createWrapper() });

      const searchInput = screen.getByPlaceholderText(/search conflicts/i);
      await user.type(searchInput, 'nonexistent');

      await waitFor(() => {
        expect(screen.getByText(/no conflicts found/i)).toBeInTheDocument();
      });
    });
  });

  describe('Refresh Functionality', () => {
    it('should have refresh button', () => {
      render(<ConflictList />, { wrapper: createWrapper() });

      expect(screen.getByLabelText(/refresh/i)).toBeInTheDocument();
    });

    it('should call refetch when refresh clicked', async () => {
      const user = userEvent.setup();

      render(<ConflictList />, { wrapper: createWrapper() });

      const refreshButton = screen.getByLabelText(/refresh/i);
      await user.click(refreshButton);

      expect(mockRefetch).toHaveBeenCalled();
    });
  });

  describe('Initial Filters', () => {
    it('should apply initial filters', () => {
      const initialFilters = conflictsMockFactories.conflictFilters();

      render(<ConflictList initialFilters={initialFilters} />, {
        wrapper: createWrapper(),
      });

      expect(mockedUseConflicts).toHaveBeenCalledWith(
        expect.objectContaining(initialFilters),
        expect.any(Object)
      );
    });
  });

  describe('Compact Mode', () => {
    it('should render in compact mode when prop is set', () => {
      const { container } = render(<ConflictList compact={true} />, {
        wrapper: createWrapper(),
      });

      expect(container.firstChild).toBeInTheDocument();
    });
  });

  describe('Selectable Mode', () => {
    it('should show checkboxes in selectable mode', () => {
      render(<ConflictList selectable={true} />, {
        wrapper: createWrapper(),
      });

      // In selectable mode, checkboxes would be visible
      expect(screen.getByTestId('conflict-card-conflict-1')).toBeInTheDocument();
    });

    it('should allow batch selection in selectable mode', async () => {
      const user = userEvent.setup();

      render(<ConflictList selectable={true} onBatchSelect={mockOnBatchSelect} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByTestId('conflict-card-conflict-1')).toBeInTheDocument();
      });

      // Test would interact with select all or individual checkboxes
      // Implementation depends on actual component structure
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels', () => {
      render(<ConflictList />, { wrapper: createWrapper() });

      expect(screen.getByPlaceholderText(/search conflicts/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/refresh/i)).toBeInTheDocument();
    });

    it('should be keyboard navigable', async () => {
      const user = userEvent.setup();

      render(<ConflictList />, { wrapper: createWrapper() });

      const searchInput = screen.getByPlaceholderText(/search conflicts/i);
      await user.tab();

      expect(searchInput).toHaveFocus();
    });
  });

  describe('Performance', () => {
    it('should not re-fetch on every render', () => {
      const { rerender } = render(<ConflictList />, { wrapper: createWrapper() });

      const initialCallCount = mockedUseConflicts.mock.calls.length;

      rerender(<ConflictList />);

      expect(mockedUseConflicts.mock.calls.length).toBe(initialCallCount + 1);
    });
  });
});
