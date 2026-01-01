/**
 * Tests for TemplateSearch Component
 *
 * Tests search functionality, filters, and user interactions.
 */

import { render, screen, waitFor } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { TemplateSearch } from '@/features/templates/components/TemplateSearch';
import type { TemplateFilters } from '@/features/templates/types';

describe('TemplateSearch', () => {
  const mockOnFiltersChange = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  afterEach(() => {
    // Ensure real timers are restored after each test
    jest.useRealTimers();
  });

  describe('Search Input', () => {
    it('should render search input', () => {
      render(
        <TemplateSearch
          filters={{}}
          onFiltersChange={mockOnFiltersChange}
        />
      );

      expect(screen.getByPlaceholderText('Search templates...')).toBeInTheDocument();
    });

    it('should display initial search query', () => {
      const filters: TemplateFilters = { searchQuery: 'clinic' };
      render(
        <TemplateSearch
          filters={filters}
          onFiltersChange={mockOnFiltersChange}
        />
      );

      const input = screen.getByPlaceholderText('Search templates...') as HTMLInputElement;
      expect(input.value).toBe('clinic');
    });

    it('should update search query on input', async () => {
      const user = userEvent.setup();
      render(
        <TemplateSearch
          filters={{}}
          onFiltersChange={mockOnFiltersChange}
        />
      );

      const input = screen.getByPlaceholderText('Search templates...');
      await user.type(input, 'test');

      expect(input).toHaveValue('test');
    });

    it('should debounce search query updates', async () => {
      // Enable fake timers BEFORE userEvent.setup, and configure userEvent to advance them
      jest.useFakeTimers();
      const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });

      render(
        <TemplateSearch
          filters={{}}
          onFiltersChange={mockOnFiltersChange}
        />
      );

      const input = screen.getByPlaceholderText('Search templates...');
      await user.type(input, 'test');

      // Should not call immediately
      expect(mockOnFiltersChange).not.toHaveBeenCalled();

      // Fast-forward time for debounce
      await jest.advanceTimersByTimeAsync(300);

      expect(mockOnFiltersChange).toHaveBeenCalledWith(
        expect.objectContaining({ searchQuery: 'test' })
      );

      jest.useRealTimers();
    });

    it('should show clear button when there is input', async () => {
      const user = userEvent.setup();
      render(
        <TemplateSearch
          filters={{}}
          onFiltersChange={mockOnFiltersChange}
        />
      );

      const input = screen.getByPlaceholderText('Search templates...');
      await user.type(input, 'test');

      const clearButton = screen.getByRole('button', { name: '' });
      expect(clearButton).toBeInTheDocument();
    });

    it('should clear search when clear button is clicked', async () => {
      const user = userEvent.setup();
      render(
        <TemplateSearch
          filters={{ searchQuery: 'test' }}
          onFiltersChange={mockOnFiltersChange}
        />
      );

      const clearButtons = screen.getAllByRole('button');
      const clearButton = clearButtons.find(btn => btn.querySelector('svg'));

      if (clearButton) {
        await user.click(clearButton);
      }

      await waitFor(() => {
        expect(mockOnFiltersChange).toHaveBeenCalledWith(
          expect.objectContaining({ searchQuery: undefined })
        );
      });
    });
  });

  describe('Filters Button', () => {
    it('should render filters button when showAdvanced is true', () => {
      render(
        <TemplateSearch
          filters={{}}
          onFiltersChange={mockOnFiltersChange}
          showAdvanced={true}
        />
      );

      expect(screen.getByText('Filters')).toBeInTheDocument();
    });

    it('should not render filters button when showAdvanced is false', () => {
      render(
        <TemplateSearch
          filters={{}}
          onFiltersChange={mockOnFiltersChange}
          showAdvanced={false}
        />
      );

      expect(screen.queryByText('Filters')).not.toBeInTheDocument();
    });

    it('should toggle filter panel when clicked', async () => {
      const user = userEvent.setup();
      render(
        <TemplateSearch
          filters={{}}
          onFiltersChange={mockOnFiltersChange}
        />
      );

      const filtersButton = screen.getByText('Filters');
      await user.click(filtersButton);

      await waitFor(() => {
        expect(screen.getByText('Category')).toBeInTheDocument();
        expect(screen.getByText('Visibility')).toBeInTheDocument();
        expect(screen.getByText('Status')).toBeInTheDocument();
      });
    });

    it('should close filter panel when clicked again', async () => {
      const user = userEvent.setup();
      render(
        <TemplateSearch
          filters={{}}
          onFiltersChange={mockOnFiltersChange}
        />
      );

      const filtersButton = screen.getByText('Filters');
      await user.click(filtersButton);
      await user.click(filtersButton);

      await waitFor(() => {
        expect(screen.queryByText('Category')).not.toBeInTheDocument();
      });
    });

    it('should highlight filters button when filters are active', () => {
      const filters: TemplateFilters = { category: 'clinic' };
      render(
        <TemplateSearch
          filters={filters}
          onFiltersChange={mockOnFiltersChange}
        />
      );

      const filtersButton = screen.getByText('Filters').closest('button');
      expect(filtersButton).toHaveClass('bg-blue-50', 'border-blue-200', 'text-blue-700');
    });

    it('should show active filter count badge', () => {
      const filters: TemplateFilters = {
        category: 'clinic',
        visibility: 'private',
        status: 'active',
      };
      render(
        <TemplateSearch
          filters={filters}
          onFiltersChange={mockOnFiltersChange}
        />
      );

      expect(screen.getByText('3')).toBeInTheDocument();
    });
  });

  describe('Results Count', () => {
    it('should display total results', () => {
      render(
        <TemplateSearch
          filters={{}}
          onFiltersChange={mockOnFiltersChange}
          totalResults={15}
        />
      );

      expect(screen.getByText('15 templates found')).toBeInTheDocument();
    });

    it('should use singular form for 1 result', () => {
      render(
        <TemplateSearch
          filters={{}}
          onFiltersChange={mockOnFiltersChange}
          totalResults={1}
        />
      );

      expect(screen.getByText('1 template found')).toBeInTheDocument();
    });

    it('should show clear filters link when filters are active', () => {
      const filters: TemplateFilters = { category: 'clinic' };
      render(
        <TemplateSearch
          filters={filters}
          onFiltersChange={mockOnFiltersChange}
          totalResults={5}
        />
      );

      expect(screen.getByText('Clear filters')).toBeInTheDocument();
    });

    it('should clear all filters when clear filters is clicked', async () => {
      const user = userEvent.setup();
      const filters: TemplateFilters = { category: 'clinic', searchQuery: 'test' };
      render(
        <TemplateSearch
          filters={filters}
          onFiltersChange={mockOnFiltersChange}
          totalResults={5}
        />
      );

      const clearButton = screen.getByText('Clear filters');
      await user.click(clearButton);

      expect(mockOnFiltersChange).toHaveBeenCalledWith({});
    });
  });

  describe('Advanced Filters', () => {
    // Helper to open filters panel - moved from async beforeEach
    const openFiltersPanel = async (user: ReturnType<typeof userEvent.setup>) => {
      const filtersButton = screen.getByText('Filters');
      await user.click(filtersButton);
      await waitFor(() => {
        expect(screen.getByText('Category')).toBeInTheDocument();
      });
    };

    it('should render category filter', async () => {
      const user = userEvent.setup();
      render(
        <TemplateSearch
          filters={{}}
          onFiltersChange={mockOnFiltersChange}
        />
      );
      await openFiltersPanel(user);

      expect(screen.getByText('Category')).toBeInTheDocument();
      expect(screen.getByText('All categories')).toBeInTheDocument();
    });

    it('should render visibility filter', async () => {
      const user = userEvent.setup();
      render(
        <TemplateSearch
          filters={{}}
          onFiltersChange={mockOnFiltersChange}
        />
      );
      await openFiltersPanel(user);

      expect(screen.getByText('Visibility')).toBeInTheDocument();
      expect(screen.getByText('All visibility')).toBeInTheDocument();
    });

    it('should render status filter', async () => {
      const user = userEvent.setup();
      render(
        <TemplateSearch
          filters={{}}
          onFiltersChange={mockOnFiltersChange}
        />
      );
      await openFiltersPanel(user);

      expect(screen.getByText('Status')).toBeInTheDocument();
      expect(screen.getByText('All statuses')).toBeInTheDocument();
    });

    it('should render sort options', async () => {
      const user = userEvent.setup();
      render(
        <TemplateSearch
          filters={{}}
          onFiltersChange={mockOnFiltersChange}
        />
      );
      await openFiltersPanel(user);

      expect(screen.getByText('Sort by')).toBeInTheDocument();
      const selects = screen.getAllByRole('combobox');
      expect(selects.length).toBeGreaterThan(0);
    });

    it('should update category filter', async () => {
      const user = userEvent.setup();
      render(
        <TemplateSearch
          filters={{}}
          onFiltersChange={mockOnFiltersChange}
        />
      );
      await openFiltersPanel(user);

      // The selects are in order: Category, Visibility, Status, Sort by
      const selects = screen.getAllByRole('combobox');
      await user.selectOptions(selects[0], 'clinic');

      await waitFor(() => {
        expect(mockOnFiltersChange).toHaveBeenCalledWith(
          expect.objectContaining({ category: 'clinic' })
        );
      });
    });

    it('should update visibility filter', async () => {
      const user = userEvent.setup();
      render(
        <TemplateSearch
          filters={{}}
          onFiltersChange={mockOnFiltersChange}
        />
      );
      await openFiltersPanel(user);

      const selects = screen.getAllByRole('combobox');
      await user.selectOptions(selects[1], 'private');

      await waitFor(() => {
        expect(mockOnFiltersChange).toHaveBeenCalledWith(
          expect.objectContaining({ visibility: 'private' })
        );
      });
    });

    it('should update status filter', async () => {
      const user = userEvent.setup();
      render(
        <TemplateSearch
          filters={{}}
          onFiltersChange={mockOnFiltersChange}
        />
      );
      await openFiltersPanel(user);

      const selects = screen.getAllByRole('combobox');
      await user.selectOptions(selects[2], 'active');

      await waitFor(() => {
        expect(mockOnFiltersChange).toHaveBeenCalledWith(
          expect.objectContaining({ status: 'active' })
        );
      });
    });

    it('should update sort by filter', async () => {
      const user = userEvent.setup();
      render(
        <TemplateSearch
          filters={{}}
          onFiltersChange={mockOnFiltersChange}
        />
      );
      await openFiltersPanel(user);

      const selects = screen.getAllByRole('combobox');
      await user.selectOptions(selects[3], 'name');

      await waitFor(() => {
        expect(mockOnFiltersChange).toHaveBeenCalledWith(
          expect.objectContaining({ sortBy: 'name' })
        );
      });
    });

    it('should toggle sort order', async () => {
      const user = userEvent.setup();
      render(
        <TemplateSearch
          filters={{}}
          onFiltersChange={mockOnFiltersChange}
        />
      );
      await openFiltersPanel(user);

      const sortOrderButton = screen.getByTitle(/Descending/);
      await user.click(sortOrderButton);

      await waitFor(() => {
        expect(mockOnFiltersChange).toHaveBeenCalledWith(
          expect.objectContaining({ sortOrder: 'asc' })
        );
      });
    });
  });

  describe('Filter Chips', () => {
    it('should display active filter chips', async () => {
      const user = userEvent.setup();
      const filters: TemplateFilters = {
        category: 'clinic',
        visibility: 'private',
      };

      render(
        <TemplateSearch
          filters={filters}
          onFiltersChange={mockOnFiltersChange}
        />
      );

      const filtersButton = screen.getByText('Filters');
      await user.click(filtersButton);

      await waitFor(() => {
        expect(screen.getByText(/Category: clinic/)).toBeInTheDocument();
        expect(screen.getByText(/Visibility: private/)).toBeInTheDocument();
      });
    });

    it('should remove filter when chip close is clicked', async () => {
      const user = userEvent.setup();
      const filters: TemplateFilters = {
        category: 'clinic',
      };

      render(
        <TemplateSearch
          filters={filters}
          onFiltersChange={mockOnFiltersChange}
        />
      );

      const filtersButton = screen.getByText('Filters');
      await user.click(filtersButton);

      // Wait for chip to appear
      await waitFor(() => {
        expect(screen.getByText(/Category: clinic/)).toBeInTheDocument();
      });

      // Find the chip's parent span and the close button inside it
      const chipText = screen.getByText(/Category: clinic/);
      const chipContainer = chipText.closest('span.inline-flex');
      const closeButton = chipContainer?.querySelector('button');

      if (closeButton) {
        await user.click(closeButton);
      }

      await waitFor(() => {
        expect(mockOnFiltersChange).toHaveBeenCalledWith(
          expect.objectContaining({ category: undefined })
        );
      });
    });

    it('should show search query chip', async () => {
      const user = userEvent.setup();
      const filters: TemplateFilters = {
        searchQuery: 'test query',
      };

      render(
        <TemplateSearch
          filters={filters}
          onFiltersChange={mockOnFiltersChange}
        />
      );

      const filtersButton = screen.getByText('Filters');
      await user.click(filtersButton);

      await waitFor(() => {
        expect(screen.getByText(/Search: "test query"/)).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('should have proper labels', async () => {
      const user = userEvent.setup();
      render(
        <TemplateSearch
          filters={{}}
          onFiltersChange={mockOnFiltersChange}
        />
      );

      const filtersButton = screen.getByText('Filters');
      await user.click(filtersButton);

      // Check that filter labels are visible (component uses labels as text, not htmlFor)
      expect(screen.getByText('Category')).toBeInTheDocument();
      expect(screen.getByText('Visibility')).toBeInTheDocument();
      expect(screen.getByText('Status')).toBeInTheDocument();
      expect(screen.getByText('Sort by')).toBeInTheDocument();
      // And that we have the corresponding comboboxes
      expect(screen.getAllByRole('combobox')).toHaveLength(4);
    });

    it('should be keyboard navigable', async () => {
      const user = userEvent.setup();
      render(
        <TemplateSearch
          filters={{}}
          onFiltersChange={mockOnFiltersChange}
        />
      );

      const searchInput = screen.getByPlaceholderText('Search templates...');
      searchInput.focus();

      await user.keyboard('{Tab}');
      // Focus should be on the Filters button (the button element, not the span inside)
      const filtersButton = screen.getByText('Filters').closest('button');
      expect(filtersButton).toHaveFocus();
    });
  });
});
