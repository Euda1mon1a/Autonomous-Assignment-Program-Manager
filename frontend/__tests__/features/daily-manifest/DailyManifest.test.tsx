/**
 * Tests for DailyManifest Component (V2)
 *
 * Tests for the main daily manifest page component using useDailyManifestV2
 */

import { render, screen, waitFor } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { DailyManifest } from '@/features/daily-manifest/DailyManifest';
import { createWrapper } from '@/test-utils';
import { manifestV2MockResponses } from './mockData';
import * as hooks from '@/features/daily-manifest/hooks';

// Mock the hooks module - must include useDailyManifestV2
jest.mock('@/features/daily-manifest/hooks', () => ({
  useDailyManifest: jest.fn(),
  useDailyManifestV2: jest.fn(),
  manifestQueryKeys: {
    all: ['daily-manifest'],
    byDate: (date: string, timeOfDay: string) => ['daily-manifest', date, timeOfDay],
    byDateV2: (date: string) => ['daily-manifest', 'v2', date],
  },
}));

// Mock the SituationalAwareness component
jest.mock('@/features/daily-manifest/SituationalAwareness', () => ({
  SituationalAwareness: ({ data, attending }: any) => (
    <div data-testid="situational-awareness">
      Situational Awareness
    </div>
  ),
}));

// Mock the ClinicCoverageTable component
jest.mock('@/features/daily-manifest/ClinicCoverageTable', () => ({
  ClinicCoverageTable: ({ locations, searchQuery }: any) => (
    <div data-testid="clinic-coverage-table">
      {locations.map((p: any) => (
        <div key={p.person.id} data-testid="person-row">
          {p.person.name}
        </div>
      ))}
    </div>
  ),
}));

const mockedUseDailyManifestV2 = hooks.useDailyManifestV2 as jest.MockedFunction<
  typeof hooks.useDailyManifestV2
>;

describe('DailyManifest', () => {
  const mockRefetch = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();

    mockedUseDailyManifestV2.mockReturnValue({
      data: manifestV2MockResponses.dailyManifestV2,
      isLoading: false,
      isError: false,
      error: null,
      refetch: mockRefetch,
      isFetching: false,
    } as unknown as ReturnType<typeof hooks.useDailyManifestV2>);
  });

  // ============================================================================
  // Initial Rendering
  // ============================================================================

  describe('Initial Rendering', () => {
    it('should render page title', async () => {
      render(<DailyManifest />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('FM Clinic Manifest')).toBeInTheDocument();
      });
    });

    it('should render page description', async () => {
      render(<DailyManifest />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(
          screen.getByText(/in clinic today/i)
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

    it('should render search input', async () => {
      render(<DailyManifest />, { wrapper: createWrapper() });

      await waitFor(() => {
        const searchInput = screen.getByPlaceholderText('Search locations or people...');
        expect(searchInput).toBeInTheDocument();
      });
    });
  });

  // ============================================================================
  // Loading State
  // ============================================================================

  describe('Loading State', () => {
    it('should show loading spinner when loading', () => {
      mockedUseDailyManifestV2.mockReturnValue({
        data: undefined,
        isLoading: true,
        isError: false,
        error: null,
        refetch: mockRefetch,
        isFetching: false,
      } as unknown as ReturnType<typeof hooks.useDailyManifestV2>);

      render(<DailyManifest />, { wrapper: createWrapper() });

      expect(screen.getByText('Loading manifest data...')).toBeInTheDocument();
    });

    it('should show animated spinner icon when loading', () => {
      mockedUseDailyManifestV2.mockReturnValue({
        data: undefined,
        isLoading: true,
        isError: false,
        error: null,
        refetch: mockRefetch,
        isFetching: false,
      } as unknown as ReturnType<typeof hooks.useDailyManifestV2>);

      const { container } = render(<DailyManifest />, { wrapper: createWrapper() });

      const spinner = container.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });

    it('should not show content when loading', () => {
      mockedUseDailyManifestV2.mockReturnValue({
        data: undefined,
        isLoading: true,
        isError: false,
        error: null,
        refetch: mockRefetch,
        isFetching: false,
      } as unknown as ReturnType<typeof hooks.useDailyManifestV2>);

      render(<DailyManifest />, { wrapper: createWrapper() });

      expect(screen.queryByTestId('situational-awareness')).not.toBeInTheDocument();
      expect(screen.queryByTestId('clinic-coverage-table')).not.toBeInTheDocument();
    });
  });

  // ============================================================================
  // Error State
  // ============================================================================

  describe('Error State', () => {
    it('should show error message when error occurs', () => {
      mockedUseDailyManifestV2.mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: true,
        error: { message: 'Failed to load data', status: 500 } as any,
        refetch: mockRefetch,
        isFetching: false,
      } as unknown as ReturnType<typeof hooks.useDailyManifestV2>);

      render(<DailyManifest />, { wrapper: createWrapper() });

      expect(screen.getByText('Unable to Load Manifest')).toBeInTheDocument();
      expect(screen.getByText('Failed to load data')).toBeInTheDocument();
    });

    it('should show default error message when error has no message', () => {
      mockedUseDailyManifestV2.mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: true,
        error: null,
        refetch: mockRefetch,
        isFetching: false,
      } as unknown as ReturnType<typeof hooks.useDailyManifestV2>);

      render(<DailyManifest />, { wrapper: createWrapper() });

      expect(screen.getByText('Unable to Load Manifest')).toBeInTheDocument();
      expect(screen.getByText('An unexpected error occurred. Please try again.')).toBeInTheDocument();
    });

    it('should show retry button when error occurs', () => {
      mockedUseDailyManifestV2.mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: true,
        error: { message: 'Failed to load data', status: 500 } as any,
        refetch: mockRefetch,
        isFetching: false,
      } as unknown as ReturnType<typeof hooks.useDailyManifestV2>);

      render(<DailyManifest />, { wrapper: createWrapper() });

      expect(screen.getByText('Retry')).toBeInTheDocument();
    });

    it('should call refetch when retry button clicked', async () => {
      const user = userEvent.setup();

      mockedUseDailyManifestV2.mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: true,
        error: { message: 'Failed to load data', status: 500 } as any,
        refetch: mockRefetch,
        isFetching: false,
      } as unknown as ReturnType<typeof hooks.useDailyManifestV2>);

      render(<DailyManifest />, { wrapper: createWrapper() });

      const retryButton = screen.getByText('Retry');
      await user.click(retryButton);

      expect(mockRefetch).toHaveBeenCalled();
    });

    it('should not show content when error occurs', () => {
      mockedUseDailyManifestV2.mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: true,
        error: { message: 'Failed to load data', status: 500 } as any,
        refetch: mockRefetch,
        isFetching: false,
      } as unknown as ReturnType<typeof hooks.useDailyManifestV2>);

      render(<DailyManifest />, { wrapper: createWrapper() });

      expect(screen.queryByTestId('situational-awareness')).not.toBeInTheDocument();
      expect(screen.queryByTestId('clinic-coverage-table')).not.toBeInTheDocument();
    });
  });

  // ============================================================================
  // Main Content Display
  // ============================================================================

  describe('Main Content Display', () => {
    it('should render situational awareness section', async () => {
      render(<DailyManifest />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByTestId('situational-awareness')).toBeInTheDocument();
      });
    });

    it('should render clinic coverage table', async () => {
      render(<DailyManifest />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByTestId('clinic-coverage-table')).toBeInTheDocument();
      });
    });

    it('should show staff count', async () => {
      render(<DailyManifest />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('(2 staff)')).toBeInTheDocument();
      });
    });

    it('should show generated timestamp', async () => {
      render(<DailyManifest />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/Updated:/)).toBeInTheDocument();
      });
    });
  });

  // ============================================================================
  // Empty State
  // ============================================================================

  describe('Empty State', () => {
    it('should show empty state when no clinic coverage', async () => {
      mockedUseDailyManifestV2.mockReturnValue({
        data: manifestV2MockResponses.emptyManifestV2,
        isLoading: false,
        isError: false,
        error: null,
        refetch: mockRefetch,
        isFetching: false,
      } as unknown as ReturnType<typeof hooks.useDailyManifestV2>);

      render(<DailyManifest />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/No Schedule Data for/)).toBeInTheDocument();
        expect(
          screen.getByText(/There are no staff assignments scheduled for this/)
        ).toBeInTheDocument();
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

      expect(mockedUseDailyManifestV2).toHaveBeenCalled();
      const callArgs = mockedUseDailyManifestV2.mock.calls[0];
      expect(callArgs[0]).toMatch(/\d{4}-\d{2}-\d{2}/);
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
      mockedUseDailyManifestV2.mockReturnValue({
        data: manifestV2MockResponses.dailyManifestV2,
        isLoading: false,
        isError: false,
        error: null,
        refetch: mockRefetch,
        isFetching: true,
      } as unknown as ReturnType<typeof hooks.useDailyManifestV2>);

      render(<DailyManifest />, { wrapper: createWrapper() });

      const refreshButton = screen.getByLabelText('Refresh');
      expect(refreshButton).toBeDisabled();
    });

    it('should show spinning icon when fetching', () => {
      mockedUseDailyManifestV2.mockReturnValue({
        data: manifestV2MockResponses.dailyManifestV2,
        isLoading: false,
        isError: false,
        error: null,
        refetch: mockRefetch,
        isFetching: true,
      } as unknown as ReturnType<typeof hooks.useDailyManifestV2>);

      const { container } = render(<DailyManifest />, { wrapper: createWrapper() });

      const refreshButton = screen.getByLabelText('Refresh');
      const spinner = refreshButton.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
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

        const searchInput = screen.getByPlaceholderText('Search locations or people...');
        expect(searchInput).toHaveAttribute('type', 'text');
      });
    });
  });
});
