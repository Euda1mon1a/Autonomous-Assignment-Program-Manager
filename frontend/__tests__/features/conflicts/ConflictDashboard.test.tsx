import { render, screen, waitFor } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { ConflictDashboard } from '@/features/conflicts/ConflictDashboard';
import { conflictsMockFactories, conflictsMockResponses } from './conflicts-mocks';
import { createWrapper } from '../../utils/test-utils';
import * as hooks from '@/features/conflicts/hooks';

// Mock the hooks module
jest.mock('@/features/conflicts/hooks', () => ({
  useConflictStatistics: jest.fn(),
  useConflicts: jest.fn(),
  conflictQueryKeys: {
    all: ['conflicts'],
    list: () => ['conflicts', 'list'],
    statistics: () => ['conflicts', 'statistics'],
  },
}));

// Mock child components
jest.mock('@/features/conflicts/ConflictList', () => ({
  ConflictList: ({ onConflictSelect }: { onConflictSelect: (c: unknown) => void }) => (
    <div data-testid="conflict-list">
      <button onClick={() => onConflictSelect(conflictsMockFactories.conflict())}>
        Select Conflict
      </button>
    </div>
  ),
}));

jest.mock('@/features/conflicts/ConflictResolutionSuggestions', () => ({
  ConflictResolutionSuggestions: ({ onResolved }: { onResolved: () => void }) => (
    <div data-testid="resolution-suggestions">
      Resolution Suggestions
      <button onClick={onResolved}>Resolve</button>
    </div>
  ),
}));

jest.mock('@/features/conflicts/ManualOverrideModal', () => ({
  ManualOverrideModal: ({
    isOpen,
    onClose,
  }: {
    isOpen: boolean;
    onClose: () => void;
  }) => (
    <>
      {isOpen && (
        <div data-testid="override-modal">
          Override Modal
          <button onClick={onClose}>Close Modal</button>
        </div>
      )}
    </>
  ),
}));

jest.mock('@/features/conflicts/ConflictHistory', () => ({
  ConflictHistory: () => <div data-testid="conflict-history">History View</div>,
  ConflictHistoryTimeline: () => <div data-testid="history-timeline">Timeline</div>,
}));

jest.mock('@/features/conflicts/BatchResolution', () => ({
  BatchResolution: ({ onComplete }: { onComplete: () => void }) => (
    <div data-testid="batch-resolution">
      Batch Resolution
      <button onClick={onComplete}>Complete Batch</button>
    </div>
  ),
}));

const mockedUseConflictStatistics = hooks.useConflictStatistics as jest.MockedFunction<
  typeof hooks.useConflictStatistics
>;
const mockedUseConflicts = hooks.useConflicts as jest.MockedFunction<
  typeof hooks.useConflicts
>;

describe('ConflictDashboard', () => {
  const mockRefetch = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();

    mockedUseConflictStatistics.mockReturnValue({
      data: conflictsMockResponses.statistics,
      isLoading: false,
      isError: false,
      error: null,
      refetch: mockRefetch,
    } as unknown as ReturnType<typeof hooks.useConflictStatistics>);

    mockedUseConflicts.mockReturnValue({
      data: conflictsMockResponses.conflicts,
      isLoading: false,
      isError: false,
      error: null,
      refetch: mockRefetch,
    } as unknown as ReturnType<typeof hooks.useConflicts>);
  });

  describe('Initial Rendering', () => {
    it('should render dashboard title', async () => {
      render(<ConflictDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Conflict Resolution')).toBeInTheDocument();
      });
    });

    it('should render dashboard description', async () => {
      render(<ConflictDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(
          screen.getByText('Detect, review, and resolve scheduling conflicts')
        ).toBeInTheDocument();
      });
    });

    it('should render refresh button', async () => {
      render(<ConflictDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Refresh')).toBeInTheDocument();
      });
    });

    it('should render conflict list', async () => {
      render(<ConflictDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByTestId('conflict-list')).toBeInTheDocument();
      });
    });
  });

  describe('Statistics Cards', () => {
    it('should display unresolved conflicts count', async () => {
      render(<ConflictDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Unresolved Conflicts')).toBeInTheDocument();
        expect(screen.getByText('12')).toBeInTheDocument();
      });
    });

    it('should display critical conflicts count', async () => {
      render(<ConflictDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Critical')).toBeInTheDocument();
        expect(screen.getByText('3')).toBeInTheDocument();
      });
    });

    it('should display resolution rate', async () => {
      render(<ConflictDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Resolution Rate')).toBeInTheDocument();
        expect(screen.getByText('76%')).toBeInTheDocument();
      });
    });

    it('should display trend status', async () => {
      render(<ConflictDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Trend')).toBeInTheDocument();
        expect(screen.getByText('Stable')).toBeInTheDocument();
      });
    });

    it('should show increasing trend when trending up', async () => {
      mockedUseConflictStatistics.mockReturnValue({
        data: conflictsMockFactories.conflictStatistics({ trending_up: true }),
        isLoading: false,
        isError: false,
        error: null,
        refetch: mockRefetch,
      } as unknown as ReturnType<typeof hooks.useConflictStatistics>);

      render(<ConflictDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Increasing')).toBeInTheDocument();
      });
    });

    it('should show loading skeleton when statistics loading', async () => {
      mockedUseConflictStatistics.mockReturnValue({
        data: undefined,
        isLoading: true,
        isError: false,
        error: null,
        refetch: mockRefetch,
      } as unknown as ReturnType<typeof hooks.useConflictStatistics>);

      const { container } = render(<ConflictDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        const skeletons = container.querySelectorAll('.animate-pulse');
        expect(skeletons.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Navigation Tabs', () => {
    it('should render all conflicts tab', async () => {
      render(<ConflictDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('All Conflicts')).toBeInTheDocument();
      });
    });

    it('should render patterns tab', async () => {
      render(<ConflictDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Patterns')).toBeInTheDocument();
      });
    });

    it('should highlight active tab', async () => {
      render(<ConflictDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        const allConflictsTab = screen.getByText('All Conflicts');
        expect(allConflictsTab).toHaveClass('text-blue-600');
      });
    });

    it('should switch to patterns view when tab clicked', async () => {
      const user = userEvent.setup();

      render(<ConflictDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Patterns')).toBeInTheDocument();
      });

      const patternsTab = screen.getByText('Patterns');
      await user.click(patternsTab);

      await waitFor(() => {
        expect(screen.getByTestId('conflict-history')).toBeInTheDocument();
      });
    });
  });

  describe('Conflict Selection', () => {
    it('should show resolution panel when conflict selected', async () => {
      const user = userEvent.setup();

      render(<ConflictDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByTestId('conflict-list')).toBeInTheDocument();
      });

      const selectButton = screen.getByText('Select Conflict');
      await user.click(selectButton);

      await waitFor(() => {
        expect(screen.getByTestId('resolution-suggestions')).toBeInTheDocument();
        // There are two elements with "Resolution Suggestions" text - the panel label and the mock
        expect(screen.getAllByText('Resolution Suggestions').length).toBeGreaterThan(0);
      });
    });

    it('should show close button in resolution panel', async () => {
      const user = userEvent.setup();

      render(<ConflictDashboard />, { wrapper: createWrapper() });

      const selectButton = screen.getByText('Select Conflict');
      await user.click(selectButton);

      await waitFor(() => {
        const closeButton = screen.getByLabelText('Close panel');
        expect(closeButton).toBeInTheDocument();
      });
    });

    it('should close resolution panel when close button clicked', async () => {
      const user = userEvent.setup();

      render(<ConflictDashboard />, { wrapper: createWrapper() });

      const selectButton = screen.getByText('Select Conflict');
      await user.click(selectButton);

      await waitFor(() => {
        expect(screen.getByTestId('resolution-suggestions')).toBeInTheDocument();
      });

      const closeButton = screen.getByLabelText('Close panel');
      await user.click(closeButton);

      await waitFor(() => {
        expect(screen.queryByTestId('resolution-suggestions')).not.toBeInTheDocument();
      });
    });

    it('should switch to history view when history button clicked', async () => {
      const user = userEvent.setup();

      render(<ConflictDashboard />, { wrapper: createWrapper() });

      const selectButton = screen.getByText('Select Conflict');
      await user.click(selectButton);

      await waitFor(() => {
        expect(screen.getByText('History')).toBeInTheDocument();
      });

      const historyButton = screen.getByText('History');
      await user.click(historyButton);

      await waitFor(() => {
        expect(screen.getByTestId('history-timeline')).toBeInTheDocument();
      });
    });

    it('should switch back to suggestions when suggestions button clicked', async () => {
      const user = userEvent.setup();

      render(<ConflictDashboard />, { wrapper: createWrapper() });

      const selectButton = screen.getByText('Select Conflict');
      await user.click(selectButton);

      const historyButton = screen.getByText('History');
      await user.click(historyButton);

      await waitFor(() => {
        expect(screen.getByTestId('history-timeline')).toBeInTheDocument();
      });

      const suggestionsButton = screen.getByText('Suggestions');
      await user.click(suggestionsButton);

      await waitFor(() => {
        expect(screen.getByTestId('resolution-suggestions')).toBeInTheDocument();
      });
    });
  });

  describe('Conflict Resolution', () => {
    it('should refetch conflicts after resolution', async () => {
      const user = userEvent.setup();

      render(<ConflictDashboard />, { wrapper: createWrapper() });

      const selectButton = screen.getByText('Select Conflict');
      await user.click(selectButton);

      await waitFor(() => {
        expect(screen.getByTestId('resolution-suggestions')).toBeInTheDocument();
      });

      const resolveButton = screen.getByText('Resolve');
      await user.click(resolveButton);

      await waitFor(() => {
        expect(mockRefetch).toHaveBeenCalled();
      });
    });

    it('should close panel after resolution', async () => {
      const user = userEvent.setup();

      render(<ConflictDashboard />, { wrapper: createWrapper() });

      const selectButton = screen.getByText('Select Conflict');
      await user.click(selectButton);

      const resolveButton = screen.getByText('Resolve');
      await user.click(resolveButton);

      await waitFor(() => {
        expect(screen.queryByTestId('resolution-suggestions')).not.toBeInTheDocument();
      });
    });
  });

  describe('Refresh Functionality', () => {
    it('should call refetch when refresh button clicked', async () => {
      const user = userEvent.setup();

      render(<ConflictDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Refresh')).toBeInTheDocument();
      });

      const refreshButton = screen.getByText('Refresh');
      await user.click(refreshButton);

      expect(mockRefetch).toHaveBeenCalled();
    });
  });

  describe('Initial Filters', () => {
    it('should pass initial filters to useConflicts hook', () => {
      const initialFilters = conflictsMockFactories.conflictFilters();

      render(<ConflictDashboard initialFilters={initialFilters} />, {
        wrapper: createWrapper(),
      });

      expect(mockedUseConflicts).toHaveBeenCalledWith(initialFilters);
    });
  });

  describe('Loading States', () => {
    it('should show loading state when conflicts are loading', () => {
      mockedUseConflicts.mockReturnValue({
        data: undefined,
        isLoading: true,
        isError: false,
        error: null,
        refetch: mockRefetch,
      } as unknown as ReturnType<typeof hooks.useConflicts>);

      render(<ConflictDashboard />, { wrapper: createWrapper() });

      expect(screen.getByTestId('conflict-list')).toBeInTheDocument();
    });
  });

  describe('Responsive Layout', () => {
    it('should show full width list when no conflict selected', async () => {
      const { container } = render(<ConflictDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        const listPanel = container.querySelector('.w-full');
        expect(listPanel).toBeInTheDocument();
      });
    });

    it('should split view when conflict selected', async () => {
      const user = userEvent.setup();

      render(<ConflictDashboard />, { wrapper: createWrapper() });

      const selectButton = screen.getByText('Select Conflict');
      await user.click(selectButton);

      await waitFor(() => {
        expect(screen.getByTestId('resolution-suggestions')).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels', async () => {
      const user = userEvent.setup();

      render(<ConflictDashboard />, { wrapper: createWrapper() });

      const selectButton = screen.getByText('Select Conflict');
      await user.click(selectButton);

      await waitFor(() => {
        const closeButton = screen.getByLabelText('Close panel');
        expect(closeButton).toBeInTheDocument();
      });
    });
  });

  describe('Animations', () => {
    it('should apply animation classes', async () => {
      const { container } = render(<ConflictDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        const animatedElements = container.querySelectorAll('.animate-fadeIn');
        expect(animatedElements.length).toBeGreaterThan(0);
      });
    });
  });
});
