/**
 * Tests for DailyManifest Component
 *
 * Tests for the main daily manifest page component
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DailyManifest } from '@/features/daily-manifest/DailyManifest';
import { createWrapper } from '../../utils/test-utils';
import { manifestMockResponses } from './mockData';
import * as hooks from '@/features/daily-manifest/hooks';

// Mock the hooks module
jest.mock('@/features/daily-manifest/hooks', () => ({
  useDailyManifest: jest.fn(),
  manifestQueryKeys: {
    all: ['daily-manifest'],
    byDate: (date: string, timeOfDay: string) => ['daily-manifest', date, timeOfDay],
  },
}));

// Mock the LocationCard component
jest.mock('@/features/daily-manifest/LocationCard', () => ({
  LocationCard: ({ location, timeOfDay }: any) => (
    <div data-testid="location-card">
      {location.clinic_location} - {timeOfDay}
    </div>
  ),
}));

const mockedUseDailyManifest = hooks.useDailyManifest as jest.MockedFunction<
  typeof hooks.useDailyManifest
>;

describe('DailyManifest', () => {
  const mockRefetch = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();

    mockedUseDailyManifest.mockReturnValue({
      data: manifestMockResponses.dailyManifest,
      isLoading: false,
      isError: false,
      error: null,
      refetch: mockRefetch,
      isFetching: false,
    } as unknown as ReturnType<typeof hooks.useDailyManifest>);
  });

  // ============================================================================
  // Initial Rendering
  // ============================================================================

  describe('Initial Rendering', () => {
    it('should render page title', async () => {
      render(<DailyManifest />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Daily Manifest')).toBeInTheDocument();
      });
    });

    it('should render page description', async () => {
      render(<DailyManifest />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(
          screen.getByText('Where is everyone NOW - Real-time location and assignment tracking')
        ).toBeInTheDocument();
      });
    });

    it('should render refresh button', async () => {
      render(<DailyManifest />, { wrapper: createWrapper() });

      await waitFor(() => {
        const refreshButton = screen.getByLabelText('Refresh');
        expect(refreshButton).toBeInTheDocument();
      });
    });

    it('should render date picker', async () => {
      render(<DailyManifest />, { wrapper: createWrapper() });

      await waitFor(() => {
        const datePicker = screen.getByDisplayValue(/\d{4}-\d{2}-\d{2}/);
        expect(datePicker).toBeInTheDocument();
      });
    });

    it('should render time of day selector', async () => {
      render(<DailyManifest />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByDisplayValue('Morning (AM)')).toBeInTheDocument();
      });
    });

    it('should render search input', async () => {
      render(<DailyManifest />, { wrapper: createWrapper() });

      await waitFor(() => {
        const searchInput = screen.getByPlaceholderText('Search locations or people...');
        expect(searchInput).toBeInTheDocument();
      });
    });
  });

  // ============================================================================
  // Summary Statistics
  // ============================================================================

  describe('Summary Statistics', () => {
    it('should display total locations', async () => {
      render(<DailyManifest />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Locations')).toBeInTheDocument();
        expect(screen.getByText('2')).toBeInTheDocument();
      });
    });

    it('should display total staff', async () => {
      render(<DailyManifest />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Total Staff')).toBeInTheDocument();
        expect(screen.getByText('4')).toBeInTheDocument();
      });
    });

    it('should display total residents', async () => {
      render(<DailyManifest />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Residents')).toBeInTheDocument();
        expect(screen.getByText('3')).toBeInTheDocument();
      });
    });

    it('should display total faculty', async () => {
      render(<DailyManifest />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Faculty')).toBeInTheDocument();
        expect(screen.getByText('1')).toBeInTheDocument();
      });
    });

    it('should not show statistics when data is not loaded', () => {
      mockedUseDailyManifest.mockReturnValue({
        data: undefined,
        isLoading: true,
        isError: false,
        error: null,
        refetch: mockRefetch,
        isFetching: false,
      } as unknown as ReturnType<typeof hooks.useDailyManifest>);

      render(<DailyManifest />, { wrapper: createWrapper() });

      expect(screen.queryByText('Locations')).not.toBeInTheDocument();
      expect(screen.queryByText('Total Staff')).not.toBeInTheDocument();
    });
  });

  // ============================================================================
  // Loading State
  // ============================================================================

  describe('Loading State', () => {
    it('should show loading spinner when loading', () => {
      mockedUseDailyManifest.mockReturnValue({
        data: undefined,
        isLoading: true,
        isError: false,
        error: null,
        refetch: mockRefetch,
        isFetching: false,
      } as unknown as ReturnType<typeof hooks.useDailyManifest>);

      render(<DailyManifest />, { wrapper: createWrapper() });

      expect(screen.getByText('Loading manifest data...')).toBeInTheDocument();
    });

    it('should show animated spinner icon when loading', () => {
      mockedUseDailyManifest.mockReturnValue({
        data: undefined,
        isLoading: true,
        isError: false,
        error: null,
        refetch: mockRefetch,
        isFetching: false,
      } as unknown as ReturnType<typeof hooks.useDailyManifest>);

      const { container } = render(<DailyManifest />, { wrapper: createWrapper() });

      const spinner = container.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });

    it('should not show locations when loading', () => {
      mockedUseDailyManifest.mockReturnValue({
        data: undefined,
        isLoading: true,
        isError: false,
        error: null,
        refetch: mockRefetch,
        isFetching: false,
      } as unknown as ReturnType<typeof hooks.useDailyManifest>);

      render(<DailyManifest />, { wrapper: createWrapper() });

      expect(screen.queryByTestId('location-card')).not.toBeInTheDocument();
    });
  });

  // ============================================================================
  // Error State
  // ============================================================================

  describe('Error State', () => {
    it('should show error message when error occurs', () => {
      mockedUseDailyManifest.mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: true,
        error: { message: 'Failed to load data', status: 500 } as any,
        refetch: mockRefetch,
        isFetching: false,
      } as unknown as ReturnType<typeof hooks.useDailyManifest>);

      render(<DailyManifest />, { wrapper: createWrapper() });

      expect(screen.getByText('Error Loading Manifest')).toBeInTheDocument();
      expect(screen.getByText('Failed to load data')).toBeInTheDocument();
    });

    it('should show default error message when error has no message', () => {
      mockedUseDailyManifest.mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: true,
        error: null,
        refetch: mockRefetch,
        isFetching: false,
      } as unknown as ReturnType<typeof hooks.useDailyManifest>);

      render(<DailyManifest />, { wrapper: createWrapper() });

      expect(screen.getByText('Failed to load daily manifest data')).toBeInTheDocument();
    });

    it('should show retry button when error occurs', () => {
      mockedUseDailyManifest.mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: true,
        error: { message: 'Failed to load data', status: 500 } as any,
        refetch: mockRefetch,
        isFetching: false,
      } as unknown as ReturnType<typeof hooks.useDailyManifest>);

      render(<DailyManifest />, { wrapper: createWrapper() });

      expect(screen.getByText('Retry')).toBeInTheDocument();
    });

    it('should call refetch when retry button clicked', async () => {
      const user = userEvent.setup();

      mockedUseDailyManifest.mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: true,
        error: { message: 'Failed to load data', status: 500 } as any,
        refetch: mockRefetch,
        isFetching: false,
      } as unknown as ReturnType<typeof hooks.useDailyManifest>);

      render(<DailyManifest />, { wrapper: createWrapper() });

      const retryButton = screen.getByText('Retry');
      await user.click(retryButton);

      expect(mockRefetch).toHaveBeenCalled();
    });

    it('should not show locations when error occurs', () => {
      mockedUseDailyManifest.mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: true,
        error: { message: 'Failed to load data', status: 500 } as any,
        refetch: mockRefetch,
        isFetching: false,
      } as unknown as ReturnType<typeof hooks.useDailyManifest>);

      render(<DailyManifest />, { wrapper: createWrapper() });

      expect(screen.queryByTestId('location-card')).not.toBeInTheDocument();
    });
  });

  // ============================================================================
  // Location Cards Display
  // ============================================================================

  describe('Location Cards Display', () => {
    it('should render location cards when data loaded', async () => {
      render(<DailyManifest />, { wrapper: createWrapper() });

      await waitFor(() => {
        const locationCards = screen.getAllByTestId('location-card');
        expect(locationCards).toHaveLength(2);
      });
    });

    it('should show location count', async () => {
      render(<DailyManifest />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Locations (2)')).toBeInTheDocument();
      });
    });

    it('should show generated timestamp', async () => {
      render(<DailyManifest />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/Last updated:/)).toBeInTheDocument();
      });
    });

    it('should pass location data to LocationCard', async () => {
      render(<DailyManifest />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/Main Clinic/)).toBeInTheDocument();
        expect(screen.getByText(/South Clinic/)).toBeInTheDocument();
      });
    });

    it('should pass timeOfDay to LocationCard', async () => {
      render(<DailyManifest />, { wrapper: createWrapper() });

      await waitFor(() => {
        const locationCards = screen.getAllByTestId('location-card');
        locationCards.forEach((card) => {
          expect(card.textContent).toContain('AM');
        });
      });
    });
  });

  // ============================================================================
  // Empty State
  // ============================================================================

  describe('Empty State', () => {
    it('should show empty state when no locations', async () => {
      mockedUseDailyManifest.mockReturnValue({
        data: manifestMockResponses.emptyManifest,
        isLoading: false,
        isError: false,
        error: null,
        refetch: mockRefetch,
        isFetching: false,
      } as unknown as ReturnType<typeof hooks.useDailyManifest>);

      render(<DailyManifest />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('No locations found')).toBeInTheDocument();
        expect(
          screen.getByText('No assignments scheduled for this date and time')
        ).toBeInTheDocument();
      });
    });

    it('should show different message when search active', async () => {
      const user = userEvent.setup();

      render(<DailyManifest />, { wrapper: createWrapper() });

      const searchInput = screen.getByPlaceholderText('Search locations or people...');
      await user.type(searchInput, 'NonexistentLocation');

      await waitFor(() => {
        expect(screen.getByText('No locations found')).toBeInTheDocument();
        expect(screen.getByText('Try adjusting your search criteria')).toBeInTheDocument();
      });
    });
  });

  // ============================================================================
  // Date Selection
  // ============================================================================

  describe('Date Selection', () => {
    it('should have date input element', async () => {
      render(<DailyManifest />, { wrapper: createWrapper() });

      await waitFor(() => {
        const datePicker = screen.getByDisplayValue(/\d{4}-\d{2}-\d{2}/);
        expect(datePicker).toBeInTheDocument();
        expect(datePicker).toHaveAttribute('type', 'date');
      });
    });

    it('should call hook with current date format', () => {
      render(<DailyManifest />, { wrapper: createWrapper() });

      // Hook should be called with a valid date string
      expect(mockedUseDailyManifest).toHaveBeenCalled();
      const callArgs = mockedUseDailyManifest.mock.calls[0];
      expect(callArgs[0]).toMatch(/\d{4}-\d{2}-\d{2}/);
      expect(callArgs[1]).toBe('AM');
    });
  });

  // ============================================================================
  // Time of Day Selection
  // ============================================================================

  describe('Time of Day Selection', () => {
    it('should have AM, PM, and ALL options', async () => {
      render(<DailyManifest />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Morning (AM)')).toBeInTheDocument();
      });

      const select = screen.getByDisplayValue('Morning (AM)') as HTMLSelectElement;
      const options = Array.from(select.options).map((opt) => opt.text);

      expect(options).toContain('Morning (AM)');
      expect(options).toContain('Afternoon (PM)');
      expect(options).toContain('All Day');
    });

    it('should default to AM', async () => {
      render(<DailyManifest />, { wrapper: createWrapper() });

      await waitFor(() => {
        const select = screen.getByDisplayValue('Morning (AM)');
        expect(select).toBeInTheDocument();
      });
    });

    it('should update timeOfDay when selector changed', async () => {
      const user = userEvent.setup();

      render(<DailyManifest />, { wrapper: createWrapper() });

      const select = screen.getByDisplayValue('Morning (AM)');
      await user.selectOptions(select, 'PM');

      await waitFor(() => {
        expect(mockedUseDailyManifest).toHaveBeenCalledWith(
          expect.any(String),
          'PM'
        );
      });
    });

    it('should fetch new data when timeOfDay changed', async () => {
      const user = userEvent.setup();

      render(<DailyManifest />, { wrapper: createWrapper() });

      const initialCallCount = mockedUseDailyManifest.mock.calls.length;

      const select = screen.getByDisplayValue('Morning (AM)');
      await user.selectOptions(select, 'PM');

      expect(mockedUseDailyManifest.mock.calls.length).toBeGreaterThan(initialCallCount);
    });

    it('should support ALL time period', async () => {
      const user = userEvent.setup();

      render(<DailyManifest />, { wrapper: createWrapper() });

      const select = screen.getByDisplayValue('Morning (AM)');
      await user.selectOptions(select, 'ALL');

      await waitFor(() => {
        expect(mockedUseDailyManifest).toHaveBeenCalledWith(
          expect.any(String),
          'ALL'
        );
      });
    });
  });

  // ============================================================================
  // Search Functionality
  // ============================================================================

  describe('Search Functionality', () => {
    it('should filter locations by location name', async () => {
      const user = userEvent.setup();

      render(<DailyManifest />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getAllByTestId('location-card')).toHaveLength(2);
      });

      const searchInput = screen.getByPlaceholderText('Search locations or people...');
      await user.type(searchInput, 'Main');

      await waitFor(() => {
        const locationCards = screen.getAllByTestId('location-card');
        expect(locationCards).toHaveLength(1);
        expect(screen.getByText(/Main Clinic/)).toBeInTheDocument();
      });
    });

    it('should filter locations by person name', async () => {
      const user = userEvent.setup();

      render(<DailyManifest />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getAllByTestId('location-card')).toHaveLength(2);
      });

      const searchInput = screen.getByPlaceholderText('Search locations or people...');
      await user.type(searchInput, 'John');

      // Main Clinic has Dr. John Smith
      await waitFor(() => {
        const locationCards = screen.getAllByTestId('location-card');
        expect(locationCards).toHaveLength(1);
      });
    });

    it('should be case insensitive', async () => {
      const user = userEvent.setup();

      render(<DailyManifest />, { wrapper: createWrapper() });

      const searchInput = screen.getByPlaceholderText('Search locations or people...');
      await user.type(searchInput, 'MAIN');

      await waitFor(() => {
        expect(screen.getByText(/Main Clinic/)).toBeInTheDocument();
      });
    });

    it('should show all locations when search is cleared', async () => {
      const user = userEvent.setup();

      render(<DailyManifest />, { wrapper: createWrapper() });

      const searchInput = screen.getByPlaceholderText('Search locations or people...');
      await user.type(searchInput, 'Main');

      await waitFor(() => {
        expect(screen.getAllByTestId('location-card')).toHaveLength(1);
      });

      await user.clear(searchInput);

      await waitFor(() => {
        expect(screen.getAllByTestId('location-card')).toHaveLength(2);
      });
    });

    it('should search in both AM and PM assignments', async () => {
      const user = userEvent.setup();

      render(<DailyManifest />, { wrapper: createWrapper() });

      const searchInput = screen.getByPlaceholderText('Search locations or people...');
      // Search for Bob Johnson who is in PM slot
      await user.type(searchInput, 'Bob');

      await waitFor(() => {
        const locationCards = screen.getAllByTestId('location-card');
        expect(locationCards).toHaveLength(1);
      });
    });
  });

  // ============================================================================
  // Refresh Functionality
  // ============================================================================

  describe('Refresh Functionality', () => {
    it('should call refetch when refresh button clicked', async () => {
      const user = userEvent.setup();

      render(<DailyManifest />, { wrapper: createWrapper() });

      const refreshButton = screen.getByLabelText('Refresh');
      await user.click(refreshButton);

      expect(mockRefetch).toHaveBeenCalled();
    });

    it('should disable refresh button when fetching', () => {
      mockedUseDailyManifest.mockReturnValue({
        data: manifestMockResponses.dailyManifest,
        isLoading: false,
        isError: false,
        error: null,
        refetch: mockRefetch,
        isFetching: true,
      } as unknown as ReturnType<typeof hooks.useDailyManifest>);

      render(<DailyManifest />, { wrapper: createWrapper() });

      const refreshButton = screen.getByLabelText('Refresh');
      expect(refreshButton).toBeDisabled();
    });

    it('should show spinning icon when fetching', () => {
      mockedUseDailyManifest.mockReturnValue({
        data: manifestMockResponses.dailyManifest,
        isLoading: false,
        isError: false,
        error: null,
        refetch: mockRefetch,
        isFetching: true,
      } as unknown as ReturnType<typeof hooks.useDailyManifest>);

      const { container } = render(<DailyManifest />, { wrapper: createWrapper() });

      const refreshButton = screen.getByLabelText('Refresh');
      const spinner = refreshButton.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });
  });

  // ============================================================================
  // Integration Tests
  // ============================================================================

  describe('Integration Tests', () => {
    it('should have both date and time controls', async () => {
      render(<DailyManifest />, { wrapper: createWrapper() });

      await waitFor(() => {
        const datePicker = screen.getByDisplayValue(/\d{4}-\d{2}-\d{2}/);
        const timeSelect = screen.getByDisplayValue('Morning (AM)');
        expect(datePicker).toBeInTheDocument();
        expect(timeSelect).toBeInTheDocument();
      });
    });

    it('should show correct location count after filtering', async () => {
      const user = userEvent.setup();

      render(<DailyManifest />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Locations (2)')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText('Search locations or people...');
      await user.type(searchInput, 'Main');

      await waitFor(() => {
        expect(screen.getByText('Locations (1)')).toBeInTheDocument();
      });
    });

    it('should maintain all controls in the same interface', async () => {
      render(<DailyManifest />, { wrapper: createWrapper() });

      await waitFor(() => {
        // All controls should be present
        expect(screen.getByDisplayValue(/\d{4}-\d{2}-\d{2}/)).toBeInTheDocument();
        expect(screen.getByDisplayValue('Morning (AM)')).toBeInTheDocument();
        expect(screen.getByPlaceholderText('Search locations or people...')).toBeInTheDocument();
        expect(screen.getByLabelText('Refresh')).toBeInTheDocument();
      });
    });
  });

  // ============================================================================
  // Accessibility
  // ============================================================================

  describe('Accessibility', () => {
    it('should have proper ARIA label for refresh button', async () => {
      render(<DailyManifest />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByLabelText('Refresh')).toBeInTheDocument();
      });
    });

    it('should have proper form controls', async () => {
      render(<DailyManifest />, { wrapper: createWrapper() });

      await waitFor(() => {
        const datePicker = screen.getByDisplayValue(/\d{4}-\d{2}-\d{2}/);
        expect(datePicker).toHaveAttribute('type', 'date');

        const timeSelect = screen.getByDisplayValue('Morning (AM)');
        expect(timeSelect.tagName).toBe('SELECT');

        const searchInput = screen.getByPlaceholderText('Search locations or people...');
        expect(searchInput).toHaveAttribute('type', 'text');
      });
    });
  });
});
