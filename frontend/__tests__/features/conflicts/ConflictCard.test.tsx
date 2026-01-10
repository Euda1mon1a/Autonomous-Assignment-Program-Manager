import { render, screen, waitFor } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { ConflictCard } from '@/features/conflicts/ConflictCard';
import { conflictsMockFactories } from './conflicts-mocks';
import { createWrapper } from '../../utils/test-utils';

describe('ConflictCard', () => {
  const mockOnSelect = jest.fn();
  const mockOnResolve = jest.fn();
  const mockOnViewSuggestions = jest.fn();
  const mockOnViewHistory = jest.fn();
  const mockOnOverride = jest.fn();
  const mockOnIgnore = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Initial Rendering', () => {
    it('should render conflict title', () => {
      const conflict = conflictsMockFactories.conflict();

      render(<ConflictCard conflict={conflict} />, { wrapper: createWrapper() });

      expect(screen.getByText('Assignment during absence')).toBeInTheDocument();
    });

    it('should render conflict description', () => {
      const conflict = conflictsMockFactories.conflict();

      render(<ConflictCard conflict={conflict} />, { wrapper: createWrapper() });

      expect(screen.getByText('Dr. Smith is assigned while on vacation')).toBeInTheDocument();
    });

    it('should display severity badge', () => {
      const conflict = conflictsMockFactories.conflict({ severity: 'critical' });

      render(<ConflictCard conflict={conflict} />, { wrapper: createWrapper() });

      expect(screen.getByText('CRITICAL')).toBeInTheDocument();
    });

    it('should display status badge', () => {
      const conflict = conflictsMockFactories.conflict({ status: 'unresolved' });

      render(<ConflictCard conflict={conflict} />, { wrapper: createWrapper() });

      expect(screen.getByText('Unresolved')).toBeInTheDocument();
    });

    it('should display type label', () => {
      const conflict = conflictsMockFactories.conflict({ type: 'absence_conflict' });

      render(<ConflictCard conflict={conflict} />, { wrapper: createWrapper() });

      expect(screen.getByText('Absence Conflict')).toBeInTheDocument();
    });

    it('should display conflict date', () => {
      const conflict = conflictsMockFactories.conflict({ conflictDate: '2024-02-15' });

      render(<ConflictCard conflict={conflict} />, { wrapper: createWrapper() });

      expect(screen.getByText(/Feb 15, 2024/i)).toBeInTheDocument();
    });

    it('should display affected count', () => {
      const conflict = conflictsMockFactories.conflict({
        affectedPersonIds: ['person-1', 'person-2', 'person-3'],
      });

      render(<ConflictCard conflict={conflict} />, { wrapper: createWrapper() });

      expect(screen.getByText('3 affected')).toBeInTheDocument();
    });

    it('should display detection time', () => {
      const conflict = conflictsMockFactories.conflict();

      render(<ConflictCard conflict={conflict} />, { wrapper: createWrapper() });

      expect(screen.getByText(/Detected/i)).toBeInTheDocument();
    });
  });

  describe('Severity Styling', () => {
    it('should apply critical severity styles', () => {
      const conflict = conflictsMockFactories.conflict({ severity: 'critical' });

      const { container } = render(<ConflictCard conflict={conflict} />, {
        wrapper: createWrapper(),
      });

      const card = container.firstChild as HTMLElement;
      expect(card).toHaveClass('bg-red-50', 'border-red-200');
    });

    it('should apply high severity styles', () => {
      const conflict = conflictsMockFactories.conflict({ severity: 'high' });

      const { container } = render(<ConflictCard conflict={conflict} />, {
        wrapper: createWrapper(),
      });

      const card = container.firstChild as HTMLElement;
      expect(card).toHaveClass('bg-orange-50', 'border-orange-200');
    });

    it('should apply medium severity styles', () => {
      const conflict = conflictsMockFactories.conflict({ severity: 'medium' });

      const { container } = render(<ConflictCard conflict={conflict} />, {
        wrapper: createWrapper(),
      });

      const card = container.firstChild as HTMLElement;
      expect(card).toHaveClass('bg-amber-50', 'border-amber-200');
    });

    it('should apply low severity styles', () => {
      const conflict = conflictsMockFactories.conflict({ severity: 'low' });

      const { container } = render(<ConflictCard conflict={conflict} />, {
        wrapper: createWrapper(),
      });

      const card = container.firstChild as HTMLElement;
      expect(card).toHaveClass('bg-blue-50', 'border-blue-200');
    });
  });

  describe('Selection', () => {
    it('should call onSelect when card is clicked', async () => {
      const user = userEvent.setup();
      const conflict = conflictsMockFactories.conflict();

      render(<ConflictCard conflict={conflict} onSelect={mockOnSelect} />, {
        wrapper: createWrapper(),
      });

      const card = screen.getByText('Assignment during absence').closest('div');
      if (card) {
        await user.click(card);
      }

      expect(mockOnSelect).toHaveBeenCalledWith(conflict);
    });

    it('should highlight card when selected', () => {
      const conflict = conflictsMockFactories.conflict();

      const { container } = render(<ConflictCard conflict={conflict} isSelected={true} />, {
        wrapper: createWrapper(),
      });

      const card = container.firstChild as HTMLElement;
      expect(card).toHaveClass('ring-2', 'ring-blue-500');
    });

    it('should not highlight card when not selected', () => {
      const conflict = conflictsMockFactories.conflict();

      const { container } = render(<ConflictCard conflict={conflict} isSelected={false} />, {
        wrapper: createWrapper(),
      });

      const card = container.firstChild as HTMLElement;
      expect(card).not.toHaveClass('ring-2');
    });
  });

  describe('Expansion', () => {
    it('should toggle expansion when expand button clicked', async () => {
      const user = userEvent.setup();
      const conflict = conflictsMockFactories.conflict();

      render(<ConflictCard conflict={conflict} />, { wrapper: createWrapper() });

      // Initially not expanded
      expect(screen.queryByText(/Details/i)).not.toBeInTheDocument();

      // Click expand
      const expandButton = screen.getByLabelText('Expand');
      await user.click(expandButton);

      // Should show details
      await waitFor(() => {
        expect(screen.getByText(/Details/i)).toBeInTheDocument();
      });

      // Click collapse
      const collapseButton = screen.getByLabelText('Collapse');
      await user.click(collapseButton);

      // Should hide details
      await waitFor(() => {
        expect(screen.queryByText(/Details/i)).not.toBeInTheDocument();
      });
    });

    it('should show affected assignments when expanded', async () => {
      const user = userEvent.setup();
      const conflict = conflictsMockFactories.conflict({
        affectedAssignmentIds: ['assignment-1', 'assignment-2'],
      });

      render(<ConflictCard conflict={conflict} />, { wrapper: createWrapper() });

      const expandButton = screen.getByLabelText('Expand');
      await user.click(expandButton);

      await waitFor(() => {
        expect(screen.getByText(/Affected Assignments \(2\)/i)).toBeInTheDocument();
      });
    });

    it('should show conflict details when expanded', async () => {
      const user = userEvent.setup();
      const conflict = conflictsMockFactories.conflict();

      render(<ConflictCard conflict={conflict} />, { wrapper: createWrapper() });

      const expandButton = screen.getByLabelText('Expand');
      await user.click(expandButton);

      await waitFor(() => {
        expect(screen.getByText(/Details/i)).toBeInTheDocument();
      });
    });

    it('should show resolution info for resolved conflicts', async () => {
      const user = userEvent.setup();
      const conflict = conflictsMockFactories.conflict({
        status: 'resolved',
        resolvedAt: '2024-02-15T10:00:00Z',
        resolvedBy: 'Admin User',
        resolutionMethod: 'manual_reassign',
        resolutionNotes: 'Reassigned to different date',
      });

      render(<ConflictCard conflict={conflict} />, { wrapper: createWrapper() });

      const expandButton = screen.getByLabelText('Expand');
      await user.click(expandButton);

      await waitFor(() => {
        expect(screen.getByText(/Resolution/i)).toBeInTheDocument();
        expect(screen.getByText(/Admin User/i)).toBeInTheDocument();
        expect(screen.getByText(/Reassigned to different date/i)).toBeInTheDocument();
      });
    });
  });

  describe('Action Menu', () => {
    it('should show action menu when more button clicked', async () => {
      const user = userEvent.setup();
      const conflict = conflictsMockFactories.conflict({ status: 'unresolved' });

      render(
        <ConflictCard
          conflict={conflict}
          onViewSuggestions={mockOnViewSuggestions}
          onResolve={mockOnResolve}
          onOverride={mockOnOverride}
          onViewHistory={mockOnViewHistory}
          onIgnore={mockOnIgnore}
        />,
        { wrapper: createWrapper() }
      );

      const moreButton = screen.getByLabelText('More actions');
      await user.click(moreButton);

      await waitFor(() => {
        expect(screen.getByText('View Suggestions')).toBeInTheDocument();
        expect(screen.getByText('Resolve')).toBeInTheDocument();
        expect(screen.getByText('Override')).toBeInTheDocument();
        expect(screen.getByText('View History')).toBeInTheDocument();
        expect(screen.getByText('Ignore')).toBeInTheDocument();
      });
    });

    it('should call onViewSuggestions when clicked in menu', async () => {
      const user = userEvent.setup();
      const conflict = conflictsMockFactories.conflict({ status: 'unresolved' });

      render(
        <ConflictCard conflict={conflict} onViewSuggestions={mockOnViewSuggestions} />,
        { wrapper: createWrapper() }
      );

      const moreButton = screen.getByLabelText('More actions');
      await user.click(moreButton);

      const suggestionsButton = await screen.findByText('View Suggestions');
      await user.click(suggestionsButton);

      expect(mockOnViewSuggestions).toHaveBeenCalledWith(conflict);
    });

    it('should call onResolve when clicked in menu', async () => {
      const user = userEvent.setup();
      const conflict = conflictsMockFactories.conflict({ status: 'unresolved' });

      render(<ConflictCard conflict={conflict} onResolve={mockOnResolve} />, {
        wrapper: createWrapper(),
      });

      const moreButton = screen.getByLabelText('More actions');
      await user.click(moreButton);

      const resolveButton = await screen.findByText('Resolve');
      await user.click(resolveButton);

      expect(mockOnResolve).toHaveBeenCalledWith(conflict);
    });

    it('should call onOverride when clicked in menu', async () => {
      const user = userEvent.setup();
      const conflict = conflictsMockFactories.conflict({ status: 'unresolved' });

      render(<ConflictCard conflict={conflict} onOverride={mockOnOverride} />, {
        wrapper: createWrapper(),
      });

      const moreButton = screen.getByLabelText('More actions');
      await user.click(moreButton);

      const overrideButton = await screen.findByText('Override');
      await user.click(overrideButton);

      expect(mockOnOverride).toHaveBeenCalledWith(conflict);
    });

    it('should call onViewHistory when clicked in menu', async () => {
      const user = userEvent.setup();
      const conflict = conflictsMockFactories.conflict();

      render(<ConflictCard conflict={conflict} onViewHistory={mockOnViewHistory} />, {
        wrapper: createWrapper(),
      });

      const moreButton = screen.getByLabelText('More actions');
      await user.click(moreButton);

      const historyButton = await screen.findByText('View History');
      await user.click(historyButton);

      expect(mockOnViewHistory).toHaveBeenCalledWith(conflict);
    });

    it('should call onIgnore when clicked in menu', async () => {
      const user = userEvent.setup();
      const conflict = conflictsMockFactories.conflict({ status: 'unresolved' });

      render(<ConflictCard conflict={conflict} onIgnore={mockOnIgnore} />, {
        wrapper: createWrapper(),
      });

      const moreButton = screen.getByLabelText('More actions');
      await user.click(moreButton);

      const ignoreButton = await screen.findByText('Ignore');
      await user.click(ignoreButton);

      expect(mockOnIgnore).toHaveBeenCalledWith(conflict);
    });
  });

  describe('Quick Actions (Expanded)', () => {
    it('should show quick action buttons when expanded for unresolved conflicts', async () => {
      const user = userEvent.setup();
      const conflict = conflictsMockFactories.conflict({ status: 'unresolved' });

      render(
        <ConflictCard
          conflict={conflict}
          onViewSuggestions={mockOnViewSuggestions}
          onResolve={mockOnResolve}
        />,
        { wrapper: createWrapper() }
      );

      const expandButton = screen.getByLabelText('Expand');
      await user.click(expandButton);

      await waitFor(() => {
        const buttons = screen.getAllByText('View Suggestions');
        expect(buttons.length).toBeGreaterThan(0);
      });
    });

    it('should call onViewSuggestions from quick action button', async () => {
      const user = userEvent.setup();
      const conflict = conflictsMockFactories.conflict({ status: 'unresolved' });

      render(
        <ConflictCard conflict={conflict} onViewSuggestions={mockOnViewSuggestions} />,
        { wrapper: createWrapper() }
      );

      const expandButton = screen.getByLabelText('Expand');
      await user.click(expandButton);

      await waitFor(() => {
        expect(screen.getAllByText('View Suggestions').length).toBeGreaterThan(0);
      });

      const quickActionButton = screen.getAllByText('View Suggestions')[1]; // Get the quick action button (second one)
      await user.click(quickActionButton);

      expect(mockOnViewSuggestions).toHaveBeenCalledWith(conflict);
    });

    it('should call onResolve from quick action button', async () => {
      const user = userEvent.setup();
      const conflict = conflictsMockFactories.conflict({ status: 'unresolved' });

      render(<ConflictCard conflict={conflict} onResolve={mockOnResolve} />, {
        wrapper: createWrapper(),
      });

      const expandButton = screen.getByLabelText('Expand');
      await user.click(expandButton);

      await waitFor(() => {
        expect(screen.getAllByText('Resolve').length).toBeGreaterThan(0);
      });

      const quickActionButton = screen.getAllByText('Resolve')[1]; // Get the quick action button (second one)
      await user.click(quickActionButton);

      expect(mockOnResolve).toHaveBeenCalledWith(conflict);
    });
  });

  describe('Compact Mode', () => {
    it('should render in compact mode', () => {
      const conflict = conflictsMockFactories.conflict();

      render(<ConflictCard conflict={conflict} compact={true} />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('Assignment during absence')).toBeInTheDocument();
    });

    it('should not show expand button in compact mode', () => {
      const conflict = conflictsMockFactories.conflict();

      render(<ConflictCard conflict={conflict} compact={true} />, {
        wrapper: createWrapper(),
      });

      expect(screen.queryByLabelText('Expand')).not.toBeInTheDocument();
    });

    it('should show status badge in compact mode', () => {
      const conflict = conflictsMockFactories.conflict({ status: 'unresolved' });

      render(<ConflictCard conflict={conflict} compact={true} />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('Unresolved')).toBeInTheDocument();
    });

    it('should call onSelect when clicked in compact mode', async () => {
      const user = userEvent.setup();
      const conflict = conflictsMockFactories.conflict();

      render(
        <ConflictCard conflict={conflict} compact={true} onSelect={mockOnSelect} />,
        { wrapper: createWrapper() }
      );

      const card = screen.getByText('Assignment during absence').closest('div');
      if (card) {
        await user.click(card);
      }

      expect(mockOnSelect).toHaveBeenCalledWith(conflict);
    });
  });

  describe('Different Conflict Types', () => {
    it('should render scheduling overlap conflict', () => {
      const conflict = conflictsMockFactories.schedulingOverlapConflict();

      render(<ConflictCard conflict={conflict} />, { wrapper: createWrapper() });

      expect(screen.getByText('Double-booked time slot')).toBeInTheDocument();
      expect(screen.getByText('Scheduling Overlap')).toBeInTheDocument();
    });

    it('should render ACGME violation conflict', () => {
      const conflict = conflictsMockFactories.acgmeViolationConflict();

      render(<ConflictCard conflict={conflict} />, { wrapper: createWrapper() });

      expect(screen.getByText('ACGME duty hour violation')).toBeInTheDocument();
      expect(screen.getByText('ACGME Violation')).toBeInTheDocument();
    });

    it('should render capacity exceeded conflict', () => {
      const conflict = conflictsMockFactories.capacityExceededConflict();

      render(<ConflictCard conflict={conflict} />, { wrapper: createWrapper() });

      expect(screen.getByText('Rotation capacity exceeded')).toBeInTheDocument();
      expect(screen.getByText('Capacity Exceeded')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels', () => {
      const conflict = conflictsMockFactories.conflict();

      render(<ConflictCard conflict={conflict} />, { wrapper: createWrapper() });

      expect(screen.getByLabelText('Expand')).toBeInTheDocument();
      expect(screen.getByLabelText('More actions')).toBeInTheDocument();
    });

    it('should update ARIA label when expanded', async () => {
      const user = userEvent.setup();
      const conflict = conflictsMockFactories.conflict();

      render(<ConflictCard conflict={conflict} />, { wrapper: createWrapper() });

      const expandButton = screen.getByLabelText('Expand');
      await user.click(expandButton);

      await waitFor(() => {
        expect(screen.getByLabelText('Collapse')).toBeInTheDocument();
      });
    });
  });

  describe('Hover Effects', () => {
    it('should apply hover classes', () => {
      const conflict = conflictsMockFactories.conflict();

      const { container } = render(<ConflictCard conflict={conflict} />, {
        wrapper: createWrapper(),
      });

      const card = container.firstChild as HTMLElement;
      expect(card).toHaveClass('hover:shadow-md', 'hover:-translate-y-0.5');
    });
  });
});
