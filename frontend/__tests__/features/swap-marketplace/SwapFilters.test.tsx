/**
 * Tests for SwapFilters Component
 *
 * Tests filtering functionality, search, and toggle interactions
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SwapFilters } from '@/features/swap-marketplace/SwapFilters';
import { SwapStatus, SwapType } from '@/features/swap-marketplace/types';

describe('SwapFilters', () => {
  const mockOnFiltersChange = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render filters heading', () => {
      render(<SwapFilters filters={{}} onFiltersChange={mockOnFiltersChange} />);

      expect(screen.getByText('Filters')).toBeInTheDocument();
    });

    it('should render search input', () => {
      render(<SwapFilters filters={{}} onFiltersChange={mockOnFiltersChange} />);

      expect(
        screen.getByPlaceholderText('Search by faculty name or reason...')
      ).toBeInTheDocument();
    });

    it('should render My Postings Only button', () => {
      render(<SwapFilters filters={{}} onFiltersChange={mockOnFiltersChange} />);

      expect(screen.getByRole('button', { name: /my postings only/i })).toBeInTheDocument();
    });

    it('should render Compatible Only button', () => {
      render(<SwapFilters filters={{}} onFiltersChange={mockOnFiltersChange} />);

      expect(screen.getByRole('button', { name: /compatible only/i })).toBeInTheDocument();
    });

    it('should show active filter count when filters are applied', () => {
      render(
        <SwapFilters
          filters={{ searchQuery: 'test', showMyPostingsOnly: true }}
          onFiltersChange={mockOnFiltersChange}
        />
      );

      expect(screen.getByText('2')).toBeInTheDocument();
    });

    it('should not show filter count when no filters are active', () => {
      render(<SwapFilters filters={{}} onFiltersChange={mockOnFiltersChange} />);

      expect(screen.queryByText('1')).not.toBeInTheDocument();
    });
  });

  describe('Search Functionality', () => {
    it('should call onFiltersChange when search query is entered', async () => {
      const user = userEvent.setup();

      // Use a state-tracking wrapper to simulate controlled component behavior
      let currentFilters = {};
      const trackingOnChange = jest.fn((newFilters) => {
        currentFilters = newFilters;
        mockOnFiltersChange(newFilters);
      });

      const { rerender } = render(
        <SwapFilters filters={currentFilters} onFiltersChange={trackingOnChange} />
      );

      const searchInput = screen.getByPlaceholderText('Search by faculty name or reason...');

      // Type character by character and rerender to simulate controlled component
      for (const char of 'Dr. Smith') {
        await user.type(searchInput, char);
        rerender(<SwapFilters filters={currentFilters} onFiltersChange={trackingOnChange} />);
      }

      // Verify the callback was called for each character with cumulative text
      expect(mockOnFiltersChange).toHaveBeenCalled();

      // The last call should contain the full search query
      expect(mockOnFiltersChange).toHaveBeenLastCalledWith({
        searchQuery: 'Dr. Smith',
      });
    });

    it('should clear search query when input is emptied', async () => {
      const user = userEvent.setup();

      render(
        <SwapFilters filters={{ searchQuery: 'test' }} onFiltersChange={mockOnFiltersChange} />
      );

      const searchInput = screen.getByPlaceholderText('Search by faculty name or reason...');
      await user.clear(searchInput);

      await waitFor(() => {
        expect(mockOnFiltersChange).toHaveBeenLastCalledWith({
          searchQuery: undefined,
        });
      });
    });

    it('should display existing search query', () => {
      render(
        <SwapFilters filters={{ searchQuery: 'Dr. Smith' }} onFiltersChange={mockOnFiltersChange} />
      );

      const searchInput = screen.getByPlaceholderText(
        'Search by faculty name or reason...'
      ) as HTMLInputElement;
      expect(searchInput.value).toBe('Dr. Smith');
    });
  });

  describe('Quick Toggle Buttons', () => {
    it('should toggle My Postings Only filter', async () => {
      const user = userEvent.setup();

      render(<SwapFilters filters={{}} onFiltersChange={mockOnFiltersChange} />);

      const myPostingsButton = screen.getByRole('button', { name: /my postings only/i });
      await user.click(myPostingsButton);

      expect(mockOnFiltersChange).toHaveBeenCalledWith({
        showMyPostingsOnly: true,
      });
    });

    it('should toggle off My Postings Only filter', async () => {
      const user = userEvent.setup();

      render(
        <SwapFilters
          filters={{ showMyPostingsOnly: true }}
          onFiltersChange={mockOnFiltersChange}
        />
      );

      const myPostingsButton = screen.getByRole('button', { name: /my postings only/i });
      await user.click(myPostingsButton);

      expect(mockOnFiltersChange).toHaveBeenCalledWith({
        showMyPostingsOnly: false,
      });
    });

    it('should toggle Compatible Only filter', async () => {
      const user = userEvent.setup();

      render(<SwapFilters filters={{}} onFiltersChange={mockOnFiltersChange} />);

      const compatibleButton = screen.getByRole('button', { name: /compatible only/i });
      await user.click(compatibleButton);

      expect(mockOnFiltersChange).toHaveBeenCalledWith({
        showCompatibleOnly: true,
      });
    });

    it('should toggle off Compatible Only filter', async () => {
      const user = userEvent.setup();

      render(
        <SwapFilters
          filters={{ showCompatibleOnly: true }}
          onFiltersChange={mockOnFiltersChange}
        />
      );

      const compatibleButton = screen.getByRole('button', { name: /compatible only/i });
      await user.click(compatibleButton);

      expect(mockOnFiltersChange).toHaveBeenCalledWith({
        showCompatibleOnly: false,
      });
    });

    it('should highlight My Postings button when active', () => {
      render(
        <SwapFilters
          filters={{ showMyPostingsOnly: true }}
          onFiltersChange={mockOnFiltersChange}
        />
      );

      const myPostingsButton = screen.getByRole('button', { name: /my postings only/i });
      expect(myPostingsButton).toHaveClass('bg-blue-100');
    });

    it('should highlight Compatible button when active', () => {
      render(
        <SwapFilters
          filters={{ showCompatibleOnly: true }}
          onFiltersChange={mockOnFiltersChange}
        />
      );

      const compatibleButton = screen.getByRole('button', { name: /compatible only/i });
      expect(compatibleButton).toHaveClass('bg-blue-100');
    });
  });

  describe('Expand/Collapse', () => {
    it('should initially hide expanded filters', () => {
      render(<SwapFilters filters={{}} onFiltersChange={mockOnFiltersChange} />);

      expect(screen.queryByText('Date Range')).not.toBeInTheDocument();
      expect(screen.queryByText('Status')).not.toBeInTheDocument();
    });

    it('should show expanded filters when Expand button is clicked', async () => {
      const user = userEvent.setup();

      render(<SwapFilters filters={{}} onFiltersChange={mockOnFiltersChange} />);

      const expandButton = screen.getByRole('button', { name: /expand/i });
      await user.click(expandButton);

      expect(screen.getByText('Date Range')).toBeInTheDocument();
      expect(screen.getByText('Status')).toBeInTheDocument();
      expect(screen.getByText('Swap Type')).toBeInTheDocument();
    });

    it('should hide expanded filters when Collapse button is clicked', async () => {
      const user = userEvent.setup();

      render(<SwapFilters filters={{}} onFiltersChange={mockOnFiltersChange} />);

      // Expand
      const expandButton = screen.getByRole('button', { name: /expand/i });
      await user.click(expandButton);

      // Collapse
      const collapseButton = screen.getByRole('button', { name: /collapse/i });
      await user.click(collapseButton);

      expect(screen.queryByText('Date Range')).not.toBeInTheDocument();
      expect(screen.queryByText('Status')).not.toBeInTheDocument();
    });
  });

  describe('Date Range Filter', () => {
    it('should show quick date range buttons when expanded', async () => {
      const user = userEvent.setup();

      render(<SwapFilters filters={{}} onFiltersChange={mockOnFiltersChange} />);

      const expandButton = screen.getByRole('button', { name: /expand/i });
      await user.click(expandButton);

      expect(screen.getByRole('button', { name: /next 7 days/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /next 30 days/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /this month/i })).toBeInTheDocument();
    });

    it('should apply date range when quick button is clicked', async () => {
      const user = userEvent.setup();

      render(<SwapFilters filters={{}} onFiltersChange={mockOnFiltersChange} />);

      const expandButton = screen.getByRole('button', { name: /expand/i });
      await user.click(expandButton);

      const next7DaysButton = screen.getByRole('button', { name: /next 7 days/i });
      await user.click(next7DaysButton);

      expect(mockOnFiltersChange).toHaveBeenCalledWith(
        expect.objectContaining({
          dateRange: expect.objectContaining({
            start: expect.any(String),
            end: expect.any(String),
          }),
        })
      );
    });

    it('should show Clear button when date range is active', async () => {
      const user = userEvent.setup();

      render(
        <SwapFilters
          filters={{ dateRange: { start: '2025-01-01', end: '2025-01-31' } }}
          onFiltersChange={mockOnFiltersChange}
        />
      );

      const expandButton = screen.getByRole('button', { name: /expand/i });
      await user.click(expandButton);

      expect(screen.getByRole('button', { name: /clear/i })).toBeInTheDocument();
    });

    it('should display selected date range', async () => {
      const user = userEvent.setup();

      render(
        <SwapFilters
          filters={{ dateRange: { start: '2025-01-01', end: '2025-01-31' } }}
          onFiltersChange={mockOnFiltersChange}
        />
      );

      const expandButton = screen.getByRole('button', { name: /expand/i });
      await user.click(expandButton);

      expect(screen.getByText(/selected: 2025-01-01 to 2025-01-31/i)).toBeInTheDocument();
    });

    it('should clear date range when Clear button is clicked', async () => {
      const user = userEvent.setup();

      render(
        <SwapFilters
          filters={{ dateRange: { start: '2025-01-01', end: '2025-01-31' } }}
          onFiltersChange={mockOnFiltersChange}
        />
      );

      const expandButton = screen.getByRole('button', { name: /expand/i });
      await user.click(expandButton);

      const clearButton = screen.getByRole('button', { name: /clear/i });
      await user.click(clearButton);

      expect(mockOnFiltersChange).toHaveBeenCalledWith(
        expect.objectContaining({
          dateRange: undefined,
        })
      );
    });
  });

  describe('Status Filter', () => {
    it('should show all status options when expanded', async () => {
      const user = userEvent.setup();

      render(<SwapFilters filters={{}} onFiltersChange={mockOnFiltersChange} />);

      const expandButton = screen.getByRole('button', { name: /expand/i });
      await user.click(expandButton);

      expect(screen.getByRole('button', { name: 'Pending' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Approved' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Rejected' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Executed' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Cancelled' })).toBeInTheDocument();
    });

    it('should toggle status filter on', async () => {
      const user = userEvent.setup();

      render(<SwapFilters filters={{}} onFiltersChange={mockOnFiltersChange} />);

      const expandButton = screen.getByRole('button', { name: /expand/i });
      await user.click(expandButton);

      const pendingButton = screen.getByRole('button', { name: 'Pending' });
      await user.click(pendingButton);

      expect(mockOnFiltersChange).toHaveBeenCalledWith({
        statuses: [SwapStatus.PENDING],
      });
    });

    it('should allow multiple status selections', async () => {
      const user = userEvent.setup();

      render(
        <SwapFilters filters={{ statuses: [SwapStatus.PENDING] }} onFiltersChange={mockOnFiltersChange} />
      );

      const expandButton = screen.getByRole('button', { name: /expand/i });
      await user.click(expandButton);

      const approvedButton = screen.getByRole('button', { name: 'Approved' });
      await user.click(approvedButton);

      expect(mockOnFiltersChange).toHaveBeenCalledWith({
        statuses: [SwapStatus.PENDING, SwapStatus.APPROVED],
      });
    });

    it('should toggle status filter off', async () => {
      const user = userEvent.setup();

      render(
        <SwapFilters
          filters={{ statuses: [SwapStatus.PENDING, SwapStatus.APPROVED] }}
          onFiltersChange={mockOnFiltersChange}
        />
      );

      const expandButton = screen.getByRole('button', { name: /expand/i });
      await user.click(expandButton);

      const pendingButton = screen.getByRole('button', { name: 'Pending' });
      await user.click(pendingButton);

      expect(mockOnFiltersChange).toHaveBeenCalledWith({
        statuses: [SwapStatus.APPROVED],
      });
    });

    it('should highlight selected status buttons', async () => {
      const user = userEvent.setup();

      render(
        <SwapFilters
          filters={{ statuses: [SwapStatus.PENDING] }}
          onFiltersChange={mockOnFiltersChange}
        />
      );

      const expandButton = screen.getByRole('button', { name: /expand/i });
      await user.click(expandButton);

      const pendingButton = screen.getByRole('button', { name: 'Pending' });
      expect(pendingButton).toHaveClass('bg-blue-100');
    });
  });

  describe('Swap Type Filter', () => {
    it('should show swap type options when expanded', async () => {
      const user = userEvent.setup();

      render(<SwapFilters filters={{}} onFiltersChange={mockOnFiltersChange} />);

      const expandButton = screen.getByRole('button', { name: /expand/i });
      await user.click(expandButton);

      expect(screen.getByRole('button', { name: 'One-to-One Swap' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Absorb Week' })).toBeInTheDocument();
    });

    it('should toggle swap type filter on', async () => {
      const user = userEvent.setup();

      render(<SwapFilters filters={{}} onFiltersChange={mockOnFiltersChange} />);

      const expandButton = screen.getByRole('button', { name: /expand/i });
      await user.click(expandButton);

      const oneToOneButton = screen.getByRole('button', { name: 'One-to-One Swap' });
      await user.click(oneToOneButton);

      expect(mockOnFiltersChange).toHaveBeenCalledWith({
        swapTypes: [SwapType.ONE_TO_ONE],
      });
    });

    it('should toggle swap type filter off', async () => {
      const user = userEvent.setup();

      render(
        <SwapFilters
          filters={{ swapTypes: [SwapType.ONE_TO_ONE] }}
          onFiltersChange={mockOnFiltersChange}
        />
      );

      const expandButton = screen.getByRole('button', { name: /expand/i });
      await user.click(expandButton);

      const oneToOneButton = screen.getByRole('button', { name: 'One-to-One Swap' });
      await user.click(oneToOneButton);

      expect(mockOnFiltersChange).toHaveBeenCalledWith({
        swapTypes: undefined,
      });
    });

    it('should highlight selected swap type buttons', async () => {
      const user = userEvent.setup();

      render(
        <SwapFilters
          filters={{ swapTypes: [SwapType.ABSORB] }}
          onFiltersChange={mockOnFiltersChange}
        />
      );

      const expandButton = screen.getByRole('button', { name: /expand/i });
      await user.click(expandButton);

      const absorbButton = screen.getByRole('button', { name: 'Absorb Week' });
      expect(absorbButton).toHaveClass('bg-blue-100');
    });
  });

  describe('Reset Functionality', () => {
    it('should show Reset button when filters are active', () => {
      render(
        <SwapFilters filters={{ searchQuery: 'test' }} onFiltersChange={mockOnFiltersChange} />
      );

      expect(screen.getByRole('button', { name: /reset/i })).toBeInTheDocument();
    });

    it('should not show Reset button when no filters are active', () => {
      render(<SwapFilters filters={{}} onFiltersChange={mockOnFiltersChange} />);

      expect(screen.queryByRole('button', { name: /reset/i })).not.toBeInTheDocument();
    });

    it('should reset all filters when Reset button is clicked', async () => {
      const user = userEvent.setup();

      render(
        <SwapFilters
          filters={{
            searchQuery: 'test',
            showMyPostingsOnly: true,
            statuses: [SwapStatus.PENDING],
          }}
          onFiltersChange={mockOnFiltersChange}
        />
      );

      const resetButton = screen.getByRole('button', { name: /reset/i });
      await user.click(resetButton);

      expect(mockOnFiltersChange).toHaveBeenCalledWith({});
    });
  });

  describe('Loading State', () => {
    it('should disable inputs when isLoading is true', () => {
      render(<SwapFilters filters={{}} onFiltersChange={mockOnFiltersChange} isLoading={true} />);

      const searchInput = screen.getByPlaceholderText('Search by faculty name or reason...');
      expect(searchInput).toBeDisabled();
    });

    it('should disable toggle buttons when isLoading is true', () => {
      render(<SwapFilters filters={{}} onFiltersChange={mockOnFiltersChange} isLoading={true} />);

      const myPostingsButton = screen.getByRole('button', { name: /my postings only/i });
      const compatibleButton = screen.getByRole('button', { name: /compatible only/i });

      expect(myPostingsButton).toBeDisabled();
      expect(compatibleButton).toBeDisabled();
    });
  });
});
