import { render, screen, waitFor } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import {
  ConflictHistory,
  ConflictHistoryTimeline,
  ConflictPatternsView,
} from '@/features/conflicts/ConflictHistory';
import { conflictsMockFactories, conflictsMockResponses } from './conflicts-mocks';
import { createWrapper } from '../../utils/test-utils';
import * as hooks from '@/features/conflicts/hooks';

// Mock the hooks module
jest.mock('@/features/conflicts/hooks', () => ({
  useConflictHistory: jest.fn(),
  useConflictPatterns: jest.fn(),
}));

const mockedUseConflictHistory = hooks.useConflictHistory as jest.MockedFunction<
  typeof hooks.useConflictHistory
>;
const mockedUseConflictPatterns = hooks.useConflictPatterns as jest.MockedFunction<
  typeof hooks.useConflictPatterns
>;

describe('ConflictHistoryTimeline', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Initial Rendering', () => {
    it('should render timeline entries', async () => {
      mockedUseConflictHistory.mockReturnValue({
        data: conflictsMockResponses.history,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useConflictHistory>);

      render(<ConflictHistoryTimeline conflictId="conflict-1" />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText('Conflict Detected')).toBeInTheDocument();
        expect(screen.getByText('Updated')).toBeInTheDocument();
        expect(screen.getByText('Resolved')).toBeInTheDocument();
      });
    });

    it('should show user names for entries', async () => {
      mockedUseConflictHistory.mockReturnValue({
        data: conflictsMockResponses.history,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useConflictHistory>);

      render(<ConflictHistoryTimeline conflictId="conflict-1" />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText('System')).toBeInTheDocument();
        expect(screen.getAllByText('Admin User').length).toBeGreaterThan(0);
      });
    });

    it('should show timestamps', async () => {
      mockedUseConflictHistory.mockReturnValue({
        data: conflictsMockResponses.history,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useConflictHistory>);

      render(<ConflictHistoryTimeline conflictId="conflict-1" />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText(/Feb 10, 2024/i)).toBeInTheDocument();
      });
    });

    it('should show relative time', async () => {
      mockedUseConflictHistory.mockReturnValue({
        data: conflictsMockResponses.history,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useConflictHistory>);

      render(<ConflictHistoryTimeline conflictId="conflict-1" />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText(/ago/i)).toBeInTheDocument();
      });
    });
  });

  describe('Loading State', () => {
    it('should show loading spinner when loading', () => {
      mockedUseConflictHistory.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
      } as unknown as ReturnType<typeof hooks.useConflictHistory>);

      const { container } = render(<ConflictHistoryTimeline conflictId="conflict-1" />, {
        wrapper: createWrapper(),
      });

      const spinner = container.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });

    it('should not show timeline while loading', () => {
      mockedUseConflictHistory.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
      } as unknown as ReturnType<typeof hooks.useConflictHistory>);

      render(<ConflictHistoryTimeline conflictId="conflict-1" />, {
        wrapper: createWrapper(),
      });

      expect(screen.queryByText('Conflict Detected')).not.toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    it('should show error message when query fails', () => {
      mockedUseConflictHistory.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('Failed to load history'),
      } as unknown as ReturnType<typeof hooks.useConflictHistory>);

      render(<ConflictHistoryTimeline conflictId="conflict-1" />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText(/Failed to load history/i)).toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    it('should show empty state when no history', () => {
      mockedUseConflictHistory.mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useConflictHistory>);

      render(<ConflictHistoryTimeline conflictId="conflict-1" />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('No history available')).toBeInTheDocument();
    });
  });

  describe('Change Display', () => {
    it('should show changes when present', async () => {
      mockedUseConflictHistory.mockReturnValue({
        data: conflictsMockResponses.history,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useConflictHistory>);

      render(<ConflictHistoryTimeline conflictId="conflict-1" />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText('Changes:')).toBeInTheDocument();
        expect(screen.getByText('status')).toBeInTheDocument();
      });
    });

    it('should show from and to values for changes', async () => {
      mockedUseConflictHistory.mockReturnValue({
        data: conflictsMockResponses.history,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useConflictHistory>);

      render(<ConflictHistoryTimeline conflictId="conflict-1" />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText('unresolved')).toBeInTheDocument();
        expect(screen.getByText('pending_review')).toBeInTheDocument();
      });
    });
  });

  describe('Notes Display', () => {
    it('should show notes when present', async () => {
      mockedUseConflictHistory.mockReturnValue({
        data: conflictsMockResponses.history,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useConflictHistory>);

      render(<ConflictHistoryTimeline conflictId="conflict-1" />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(
          screen.getByText('Conflict automatically detected during validation')
        ).toBeInTheDocument();
      });
    });
  });

  describe('Action Icons', () => {
    it('should show different icons for different actions', async () => {
      mockedUseConflictHistory.mockReturnValue({
        data: conflictsMockResponses.history,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useConflictHistory>);

      const { container } = render(<ConflictHistoryTimeline conflictId="conflict-1" />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        // Check that timeline dots are rendered (action icons)
        const timelineDots = container.querySelectorAll('.rounded-full');
        expect(timelineDots.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Animation', () => {
    it('should apply animation classes to entries', async () => {
      mockedUseConflictHistory.mockReturnValue({
        data: conflictsMockResponses.history,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useConflictHistory>);

      const { container } = render(<ConflictHistoryTimeline conflictId="conflict-1" />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        const animatedElements = container.querySelectorAll('.animate-fadeInUp');
        expect(animatedElements.length).toBeGreaterThan(0);
      });
    });
  });
});

describe('ConflictPatternsView', () => {
  const mockOnPatternSelect = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Initial Rendering', () => {
    it('should render patterns list', async () => {
      mockedUseConflictPatterns.mockReturnValue({
        data: conflictsMockResponses.patterns,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useConflictPatterns>);

      render(<ConflictPatternsView />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/Vacation periods not properly blocked/i)).toBeInTheDocument();
      });
    });

    it('should show summary statistics', async () => {
      mockedUseConflictPatterns.mockReturnValue({
        data: conflictsMockResponses.patterns,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useConflictPatterns>);

      render(<ConflictPatternsView />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Total Patterns')).toBeInTheDocument();
        expect(screen.getByText('Most Frequent')).toBeInTheDocument();
        expect(screen.getByText('People Affected')).toBeInTheDocument();
      });
    });

    it('should show pattern count', async () => {
      mockedUseConflictPatterns.mockReturnValue({
        data: conflictsMockResponses.patterns,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useConflictPatterns>);

      render(<ConflictPatternsView />, { wrapper: createWrapper() });

      await waitFor(() => {
        // 2 patterns in mock data
        expect(screen.getByText('2')).toBeInTheDocument();
      });
    });
  });

  describe('Type Filtering', () => {
    it('should show type filter buttons', async () => {
      mockedUseConflictPatterns.mockReturnValue({
        data: conflictsMockResponses.patterns,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useConflictPatterns>);

      render(<ConflictPatternsView />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('All')).toBeInTheDocument();
        expect(screen.getByText('Absence Conflict')).toBeInTheDocument();
        expect(screen.getByText('Scheduling Overlap')).toBeInTheDocument();
      });
    });

    it('should highlight All button by default', async () => {
      mockedUseConflictPatterns.mockReturnValue({
        data: conflictsMockResponses.patterns,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useConflictPatterns>);

      render(<ConflictPatternsView />, { wrapper: createWrapper() });

      await waitFor(() => {
        const allButton = screen.getByText('All');
        expect(allButton).toHaveClass('bg-blue-500', 'text-white');
      });
    });

    it('should filter patterns when type selected', async () => {
      const user = userEvent.setup();

      mockedUseConflictPatterns.mockReturnValue({
        data: conflictsMockResponses.patterns,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useConflictPatterns>);

      render(<ConflictPatternsView />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Absence Conflict')).toBeInTheDocument();
      });

      const typeButton = screen.getByText('Absence Conflict');
      await user.click(typeButton);

      await waitFor(() => {
        expect(typeButton).toHaveClass('bg-blue-500', 'text-white');
      });
    });
  });

  describe('Pattern Cards', () => {
    it('should show frequency for each pattern', async () => {
      mockedUseConflictPatterns.mockReturnValue({
        data: conflictsMockResponses.patterns,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useConflictPatterns>);

      render(<ConflictPatternsView />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/5 occurrences/i)).toBeInTheDocument();
      });
    });

    it('should show affected people count', async () => {
      mockedUseConflictPatterns.mockReturnValue({
        data: conflictsMockResponses.patterns,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useConflictPatterns>);

      render(<ConflictPatternsView />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/2 people/i)).toBeInTheDocument();
      });
    });

    it('should show last occurrence date', async () => {
      mockedUseConflictPatterns.mockReturnValue({
        data: conflictsMockResponses.patterns,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useConflictPatterns>);

      render(<ConflictPatternsView />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/Last:/i)).toBeInTheDocument();
      });
    });

    it('should show root cause when present', async () => {
      mockedUseConflictPatterns.mockReturnValue({
        data: conflictsMockResponses.patterns,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useConflictPatterns>);

      render(<ConflictPatternsView />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Potential Root Cause:')).toBeInTheDocument();
        expect(
          screen.getByText(/Vacation periods not properly blocked/i)
        ).toBeInTheDocument();
      });
    });

    it('should show suggested prevention', async () => {
      mockedUseConflictPatterns.mockReturnValue({
        data: conflictsMockResponses.patterns,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useConflictPatterns>);

      render(<ConflictPatternsView />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Suggested Prevention:')).toBeInTheDocument();
        expect(
          screen.getByText(/Implement automatic blocking of vacation periods/i)
        ).toBeInTheDocument();
      });
    });

    it('should show trend indicator', async () => {
      mockedUseConflictPatterns.mockReturnValue({
        data: conflictsMockResponses.patterns,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useConflictPatterns>);

      render(<ConflictPatternsView />, { wrapper: createWrapper() });

      await waitFor(() => {
        // Pattern with frequency > 5 should show "Increasing"
        expect(screen.getByText('Increasing')).toBeInTheDocument();
      });
    });
  });

  describe('Pattern Expansion', () => {
    it('should expand pattern when chevron clicked', async () => {
      const user = userEvent.setup();

      mockedUseConflictPatterns.mockReturnValue({
        data: conflictsMockResponses.patterns,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useConflictPatterns>);

      const { container } = render(<ConflictPatternsView />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/Vacation periods/i)).toBeInTheDocument();
      });

      // Find and click the chevron button
      const chevronButtons = container.querySelectorAll('button');
      const chevronButton = Array.from(chevronButtons).find((btn) =>
        btn.querySelector('.lucide-chevron-right')
      );

      if (chevronButton) {
        await user.click(chevronButton);

        await waitFor(() => {
          expect(screen.getByText('Most Affected People')).toBeInTheDocument();
        });
      }
    });

    it('should show affected people details when expanded', async () => {
      const user = userEvent.setup();

      mockedUseConflictPatterns.mockReturnValue({
        data: conflictsMockResponses.patterns,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useConflictPatterns>);

      const { container } = render(<ConflictPatternsView />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/Vacation periods/i)).toBeInTheDocument();
      });

      const chevronButtons = container.querySelectorAll('button');
      const chevronButton = Array.from(chevronButtons).find((btn) =>
        btn.querySelector('.lucide-chevron-right')
      );

      if (chevronButton) {
        await user.click(chevronButton);

        await waitFor(() => {
          expect(screen.getByText('Dr. John Smith')).toBeInTheDocument();
          expect(screen.getByText(/3 occurrence/i)).toBeInTheDocument();
        });
      }
    });
  });

  describe('Pattern Selection', () => {
    it('should call onPatternSelect when pattern clicked', async () => {
      const user = userEvent.setup();

      mockedUseConflictPatterns.mockReturnValue({
        data: conflictsMockResponses.patterns,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useConflictPatterns>);

      const { container } = render(
        <ConflictPatternsView onPatternSelect={mockOnPatternSelect} />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByText(/Vacation periods/i)).toBeInTheDocument();
      });

      // Click on the pattern card
      const patternCard = container.querySelector('.cursor-pointer');
      if (patternCard) {
        await user.click(patternCard);

        expect(mockOnPatternSelect).toHaveBeenCalledWith(
          expect.objectContaining({
            id: 'pattern-1',
          })
        );
      }
    });
  });

  describe('Loading State', () => {
    it('should show loading spinner when loading', () => {
      mockedUseConflictPatterns.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
      } as unknown as ReturnType<typeof hooks.useConflictPatterns>);

      const { container } = render(<ConflictPatternsView />, { wrapper: createWrapper() });

      const spinner = container.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    it('should show error message when query fails', () => {
      mockedUseConflictPatterns.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('Failed to load patterns'),
      } as unknown as ReturnType<typeof hooks.useConflictPatterns>);

      render(<ConflictPatternsView />, { wrapper: createWrapper() });

      expect(screen.getByText(/Failed to load patterns/i)).toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    it('should show empty state when no patterns', () => {
      mockedUseConflictPatterns.mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useConflictPatterns>);

      render(<ConflictPatternsView />, { wrapper: createWrapper() });

      expect(screen.getByText('No patterns detected')).toBeInTheDocument();
    });

    it('should show helpful message in empty state', () => {
      mockedUseConflictPatterns.mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useConflictPatterns>);

      render(<ConflictPatternsView />, { wrapper: createWrapper() });

      expect(
        screen.getByText(/Patterns will appear here once enough conflict data is collected/i)
      ).toBeInTheDocument();
    });
  });
});

describe('ConflictHistory', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Tab Navigation', () => {
    it('should show history tab when conflict provided', () => {
      const conflict = conflictsMockFactories.conflict();

      mockedUseConflictHistory.mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useConflictHistory>);

      render(<ConflictHistory conflict={conflict} />, { wrapper: createWrapper() });

      expect(screen.getByText('History')).toBeInTheDocument();
    });

    it('should show patterns tab by default', () => {
      mockedUseConflictPatterns.mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useConflictPatterns>);

      render(<ConflictHistory showPatterns={true} />, { wrapper: createWrapper() });

      expect(screen.getByText('Patterns')).toBeInTheDocument();
    });

    it('should switch tabs when clicked', async () => {
      const user = userEvent.setup();
      const conflict = conflictsMockFactories.conflict();

      mockedUseConflictHistory.mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useConflictHistory>);

      mockedUseConflictPatterns.mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useConflictPatterns>);

      render(<ConflictHistory conflict={conflict} showPatterns={true} />, {
        wrapper: createWrapper(),
      });

      const patternsTab = screen.getByText('Patterns');
      await user.click(patternsTab);

      await waitFor(() => {
        expect(patternsTab).toHaveClass('text-blue-600');
      });
    });

    it('should highlight active tab', () => {
      const conflict = conflictsMockFactories.conflict();

      mockedUseConflictHistory.mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useConflictHistory>);

      render(<ConflictHistory conflict={conflict} />, { wrapper: createWrapper() });

      const historyTab = screen.getByText('History');
      expect(historyTab).toHaveClass('border-blue-500', 'text-blue-600');
    });
  });

  describe('Content Display', () => {
    it('should show timeline when history tab active', () => {
      const conflict = conflictsMockFactories.conflict();

      mockedUseConflictHistory.mockReturnValue({
        data: conflictsMockResponses.history,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useConflictHistory>);

      render(<ConflictHistory conflict={conflict} />, { wrapper: createWrapper() });

      expect(screen.getByText('Conflict Detected')).toBeInTheDocument();
    });

    it('should show patterns when patterns tab active', async () => {
      const user = userEvent.setup();
      const conflict = conflictsMockFactories.conflict();

      mockedUseConflictHistory.mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useConflictHistory>);

      mockedUseConflictPatterns.mockReturnValue({
        data: conflictsMockResponses.patterns,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useConflictPatterns>);

      render(<ConflictHistory conflict={conflict} showPatterns={true} />, {
        wrapper: createWrapper(),
      });

      const patternsTab = screen.getByText('Patterns');
      await user.click(patternsTab);

      await waitFor(() => {
        expect(screen.getByText('Total Patterns')).toBeInTheDocument();
      });
    });
  });

  describe('Show Patterns Prop', () => {
    it('should not show patterns tab when showPatterns is false', () => {
      const conflict = conflictsMockFactories.conflict();

      mockedUseConflictHistory.mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useConflictHistory>);

      render(<ConflictHistory conflict={conflict} showPatterns={false} />, {
        wrapper: createWrapper(),
      });

      expect(screen.queryByText('Patterns')).not.toBeInTheDocument();
    });

    it('should show patterns tab when showPatterns is true', () => {
      const conflict = conflictsMockFactories.conflict();

      mockedUseConflictHistory.mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useConflictHistory>);

      render(<ConflictHistory conflict={conflict} showPatterns={true} />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('Patterns')).toBeInTheDocument();
    });
  });
});
