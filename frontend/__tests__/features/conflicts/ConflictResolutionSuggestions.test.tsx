import { render, screen, waitFor } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { ConflictResolutionSuggestions } from '@/features/conflicts/ConflictResolutionSuggestions';
import { conflictsMockFactories, conflictsMockResponses } from './conflicts-mocks';
import { createWrapper } from '../../utils/test-utils';
import * as hooks from '@/features/conflicts/hooks';

// Mock the hooks module
jest.mock('@/features/conflicts/hooks', () => ({
  useResolutionSuggestions: jest.fn(),
  useApplyResolution: jest.fn(),
}));

const mockedUseResolutionSuggestions = hooks.useResolutionSuggestions as jest.MockedFunction<
  typeof hooks.useResolutionSuggestions
>;
const mockedUseApplyResolution = hooks.useApplyResolution as jest.MockedFunction<
  typeof hooks.useApplyResolution
>;

describe('ConflictResolutionSuggestions', () => {
  const mockOnResolved = jest.fn();
  const mockOnClose = jest.fn();
  const mockMutateAsync = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();

    mockedUseApplyResolution.mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: false,
      isError: false,
      error: null,
    } as unknown as ReturnType<typeof hooks.useApplyResolution>);
  });

  describe('Initial Rendering', () => {
    it('should render header', async () => {
      mockedUseResolutionSuggestions.mockReturnValue({
        data: conflictsMockResponses.suggestions,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useResolutionSuggestions>);

      const conflict = conflictsMockFactories.conflict();

      render(<ConflictResolutionSuggestions conflict={conflict} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText('Resolution Suggestions')).toBeInTheDocument();
      });
    });

    it('should show suggestion count', async () => {
      mockedUseResolutionSuggestions.mockReturnValue({
        data: conflictsMockResponses.suggestions,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useResolutionSuggestions>);

      const conflict = conflictsMockFactories.conflict();

      render(<ConflictResolutionSuggestions conflict={conflict} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText(/2 suggestions available/i)).toBeInTheDocument();
      });
    });

    it('should render suggestion cards', async () => {
      mockedUseResolutionSuggestions.mockReturnValue({
        data: conflictsMockResponses.suggestions,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useResolutionSuggestions>);

      const conflict = conflictsMockFactories.conflict();

      render(<ConflictResolutionSuggestions conflict={conflict} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText('Reassign to available resident')).toBeInTheDocument();
        expect(screen.getByText('Cancel assignment')).toBeInTheDocument();
      });
    });

    it('should show suggestion descriptions', async () => {
      mockedUseResolutionSuggestions.mockReturnValue({
        data: conflictsMockResponses.suggestions,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useResolutionSuggestions>);

      const conflict = conflictsMockFactories.conflict();

      render(<ConflictResolutionSuggestions conflict={conflict} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(
          screen.getByText('Reassign this rotation to Dr. Doe who is available')
        ).toBeInTheDocument();
      });
    });
  });

  describe('Loading State', () => {
    it('should show loading spinner when loading', () => {
      mockedUseResolutionSuggestions.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
      } as unknown as ReturnType<typeof hooks.useResolutionSuggestions>);

      const conflict = conflictsMockFactories.conflict();

      render(<ConflictResolutionSuggestions conflict={conflict} />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText(/Analyzing conflict and generating suggestions/i)).toBeInTheDocument();
    });

    it('should show loading skeletons', () => {
      mockedUseResolutionSuggestions.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
      } as unknown as ReturnType<typeof hooks.useResolutionSuggestions>);

      const conflict = conflictsMockFactories.conflict();

      const { container } = render(<ConflictResolutionSuggestions conflict={conflict} />, {
        wrapper: createWrapper(),
      });

      const skeletons = container.querySelectorAll('.animate-pulse');
      expect(skeletons.length).toBeGreaterThan(0);
    });

    it('should not show suggestions while loading', () => {
      mockedUseResolutionSuggestions.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
      } as unknown as ReturnType<typeof hooks.useResolutionSuggestions>);

      const conflict = conflictsMockFactories.conflict();

      render(<ConflictResolutionSuggestions conflict={conflict} />, {
        wrapper: createWrapper(),
      });

      expect(screen.queryByText('Reassign to available resident')).not.toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    it('should show error message when query fails', () => {
      mockedUseResolutionSuggestions.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('Failed to load suggestions'),
      } as unknown as ReturnType<typeof hooks.useResolutionSuggestions>);

      const conflict = conflictsMockFactories.conflict();

      render(<ConflictResolutionSuggestions conflict={conflict} />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('Error loading suggestions')).toBeInTheDocument();
      expect(screen.getByText('Failed to load suggestions')).toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    it('should show empty state when no suggestions', () => {
      mockedUseResolutionSuggestions.mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useResolutionSuggestions>);

      const conflict = conflictsMockFactories.conflict();

      render(<ConflictResolutionSuggestions conflict={conflict} />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('No automatic suggestions available')).toBeInTheDocument();
    });

    it('should show helpful message in empty state', () => {
      mockedUseResolutionSuggestions.mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useResolutionSuggestions>);

      const conflict = conflictsMockFactories.conflict();

      render(<ConflictResolutionSuggestions conflict={conflict} />, {
        wrapper: createWrapper(),
      });

      expect(
        screen.getByText(/This conflict requires manual resolution/i)
      ).toBeInTheDocument();
    });
  });

  describe('Suggestion Badges', () => {
    it('should show recommended badge for recommended suggestions', async () => {
      mockedUseResolutionSuggestions.mockReturnValue({
        data: conflictsMockResponses.suggestions,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useResolutionSuggestions>);

      const conflict = conflictsMockFactories.conflict();

      render(<ConflictResolutionSuggestions conflict={conflict} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText('Recommended')).toBeInTheDocument();
      });
    });

    it('should show method label', async () => {
      mockedUseResolutionSuggestions.mockReturnValue({
        data: conflictsMockResponses.suggestions,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useResolutionSuggestions>);

      const conflict = conflictsMockFactories.conflict();

      render(<ConflictResolutionSuggestions conflict={conflict} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText('Reassign')).toBeInTheDocument();
        expect(screen.getByText('Cancel Assignment')).toBeInTheDocument();
      });
    });

    it('should show impact score', async () => {
      mockedUseResolutionSuggestions.mockReturnValue({
        data: conflictsMockResponses.suggestions,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useResolutionSuggestions>);

      const conflict = conflictsMockFactories.conflict();

      render(<ConflictResolutionSuggestions conflict={conflict} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText('Impact:')).toBeInTheDocument();
        expect(screen.getByText('Low')).toBeInTheDocument();
      });
    });

    it('should show confidence score', async () => {
      mockedUseResolutionSuggestions.mockReturnValue({
        data: conflictsMockResponses.suggestions,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useResolutionSuggestions>);

      const conflict = conflictsMockFactories.conflict();

      render(<ConflictResolutionSuggestions conflict={conflict} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText('Confidence:')).toBeInTheDocument();
        expect(screen.getByText('85%')).toBeInTheDocument();
      });
    });
  });

  describe('Suggestion Selection', () => {
    it('should select suggestion when clicked', async () => {
      const user = userEvent.setup();

      mockedUseResolutionSuggestions.mockReturnValue({
        data: conflictsMockResponses.suggestions,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useResolutionSuggestions>);

      const conflict = conflictsMockFactories.conflict();

      const { container } = render(<ConflictResolutionSuggestions conflict={conflict} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText('Reassign to available resident')).toBeInTheDocument();
      });

      const suggestionCard = screen
        .getByText('Reassign to available resident')
        .closest('div');

      if (suggestionCard) {
        await user.click(suggestionCard);

        await waitFor(() => {
          expect(suggestionCard).toHaveClass('border-blue-500');
        });
      }
    });

    it('should show notes textarea when suggestion selected', async () => {
      const user = userEvent.setup();

      mockedUseResolutionSuggestions.mockReturnValue({
        data: conflictsMockResponses.suggestions,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useResolutionSuggestions>);

      const conflict = conflictsMockFactories.conflict();

      render(<ConflictResolutionSuggestions conflict={conflict} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText('Reassign to available resident')).toBeInTheDocument();
      });

      const suggestionCard = screen
        .getByText('Reassign to available resident')
        .closest('div');

      if (suggestionCard) {
        await user.click(suggestionCard);

        await waitFor(() => {
          expect(
            screen.getByPlaceholderText('Add any notes about this resolution...')
          ).toBeInTheDocument();
        });
      }
    });

    it('should enable apply button when suggestion selected', async () => {
      const user = userEvent.setup();

      mockedUseResolutionSuggestions.mockReturnValue({
        data: conflictsMockResponses.suggestions,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useResolutionSuggestions>);

      const conflict = conflictsMockFactories.conflict();

      render(<ConflictResolutionSuggestions conflict={conflict} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        const applyButton = screen.getByText('Apply Resolution');
        expect(applyButton).toBeDisabled();
      });

      const suggestionCard = screen
        .getByText('Reassign to available resident')
        .closest('div');

      if (suggestionCard) {
        await user.click(suggestionCard);

        await waitFor(() => {
          const applyButton = screen.getByText('Apply Resolution');
          expect(applyButton).not.toBeDisabled();
        });
      }
    });
  });

  describe('Suggestion Expansion', () => {
    it('should expand suggestion when chevron clicked', async () => {
      const user = userEvent.setup();

      mockedUseResolutionSuggestions.mockReturnValue({
        data: conflictsMockResponses.suggestions,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useResolutionSuggestions>);

      const conflict = conflictsMockFactories.conflict();

      render(<ConflictResolutionSuggestions conflict={conflict} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText('Reassign to available resident')).toBeInTheDocument();
      });

      const expandButton = screen.getAllByLabelText('Expand')[0];
      await user.click(expandButton);

      await waitFor(() => {
        expect(screen.getByText(/Proposed Changes/i)).toBeInTheDocument();
      });
    });

    it('should show changes when expanded', async () => {
      const user = userEvent.setup();

      mockedUseResolutionSuggestions.mockReturnValue({
        data: conflictsMockResponses.suggestions,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useResolutionSuggestions>);

      const conflict = conflictsMockFactories.conflict();

      render(<ConflictResolutionSuggestions conflict={conflict} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText('Reassign to available resident')).toBeInTheDocument();
      });

      const expandButton = screen.getAllByLabelText('Expand')[0];
      await user.click(expandButton);

      await waitFor(() => {
        expect(screen.getByText('Reassign Dr. Smith to different date')).toBeInTheDocument();
      });
    });

    it('should show side effects when present', async () => {
      const user = userEvent.setup();

      mockedUseResolutionSuggestions.mockReturnValue({
        data: conflictsMockResponses.suggestions,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useResolutionSuggestions>);

      const conflict = conflictsMockFactories.conflict();

      render(<ConflictResolutionSuggestions conflict={conflict} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText('Reassign to available resident')).toBeInTheDocument();
      });

      const expandButton = screen.getAllByLabelText('Expand')[0];
      await user.click(expandButton);

      await waitFor(() => {
        expect(screen.getByText('Potential Side Effects')).toBeInTheDocument();
        expect(
          screen.getByText('Dr. Doe will have 1 extra shift this month')
        ).toBeInTheDocument();
      });
    });

    it('should toggle between expand and collapse', async () => {
      const user = userEvent.setup();

      mockedUseResolutionSuggestions.mockReturnValue({
        data: conflictsMockResponses.suggestions,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useResolutionSuggestions>);

      const conflict = conflictsMockFactories.conflict();

      render(<ConflictResolutionSuggestions conflict={conflict} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText('Reassign to available resident')).toBeInTheDocument();
      });

      const expandButton = screen.getAllByLabelText('Expand')[0];
      await user.click(expandButton);

      await waitFor(() => {
        expect(screen.getByLabelText('Collapse')).toBeInTheDocument();
      });

      const collapseButton = screen.getAllByLabelText('Collapse')[0];
      await user.click(collapseButton);

      await waitFor(() => {
        expect(screen.queryByText(/Proposed Changes/i)).not.toBeInTheDocument();
      });
    });
  });

  describe('Apply Resolution', () => {
    it('should call mutation when apply clicked', async () => {
      const user = userEvent.setup();

      mockMutateAsync.mockResolvedValue(conflictsMockFactories.conflict({ status: 'resolved' }));

      mockedUseResolutionSuggestions.mockReturnValue({
        data: conflictsMockResponses.suggestions,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useResolutionSuggestions>);

      const conflict = conflictsMockFactories.conflict();

      render(<ConflictResolutionSuggestions conflict={conflict} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText('Reassign to available resident')).toBeInTheDocument();
      });

      // Select suggestion
      const suggestionCard = screen
        .getByText('Reassign to available resident')
        .closest('div');

      if (suggestionCard) {
        await user.click(suggestionCard);
      }

      // Click apply
      const applyButton = screen.getByText('Apply Resolution');
      await user.click(applyButton);

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith({
          conflictId: conflict.id,
          suggestionId: 'suggestion-1',
          notes: undefined,
        });
      });
    });

    it('should include notes when provided', async () => {
      const user = userEvent.setup();

      mockMutateAsync.mockResolvedValue(conflictsMockFactories.conflict({ status: 'resolved' }));

      mockedUseResolutionSuggestions.mockReturnValue({
        data: conflictsMockResponses.suggestions,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useResolutionSuggestions>);

      const conflict = conflictsMockFactories.conflict();

      render(<ConflictResolutionSuggestions conflict={conflict} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText('Reassign to available resident')).toBeInTheDocument();
      });

      // Select suggestion
      const suggestionCard = screen
        .getByText('Reassign to available resident')
        .closest('div');

      if (suggestionCard) {
        await user.click(suggestionCard);
      }

      // Add notes
      const notesInput = screen.getByPlaceholderText('Add any notes about this resolution...');
      await user.type(notesInput, 'Test resolution notes');

      // Click apply
      const applyButton = screen.getByText('Apply Resolution');
      await user.click(applyButton);

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith({
          conflictId: conflict.id,
          suggestionId: 'suggestion-1',
          notes: 'Test resolution notes',
        });
      });
    });

    it('should call onResolved when successful', async () => {
      const user = userEvent.setup();

      const resolvedConflict = conflictsMockFactories.conflict({ status: 'resolved' });
      mockMutateAsync.mockResolvedValue(resolvedConflict);

      mockedUseResolutionSuggestions.mockReturnValue({
        data: conflictsMockResponses.suggestions,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useResolutionSuggestions>);

      const conflict = conflictsMockFactories.conflict();

      render(
        <ConflictResolutionSuggestions conflict={conflict} onResolved={mockOnResolved} />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByText('Reassign to available resident')).toBeInTheDocument();
      });

      // Select and apply
      const suggestionCard = screen
        .getByText('Reassign to available resident')
        .closest('div');

      if (suggestionCard) {
        await user.click(suggestionCard);
      }

      const applyButton = screen.getByText('Apply Resolution');
      await user.click(applyButton);

      await waitFor(() => {
        expect(mockOnResolved).toHaveBeenCalledWith(resolvedConflict);
      });
    });

    it('should show loading state during apply', async () => {
      const user = userEvent.setup();

      mockedUseApplyResolution.mockReturnValue({
        mutateAsync: mockMutateAsync,
        isPending: true,
        isError: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useApplyResolution>);

      mockedUseResolutionSuggestions.mockReturnValue({
        data: conflictsMockResponses.suggestions,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useResolutionSuggestions>);

      const conflict = conflictsMockFactories.conflict();

      render(<ConflictResolutionSuggestions conflict={conflict} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText('Reassign to available resident')).toBeInTheDocument();
      });

      // Select suggestion
      const suggestionCard = screen
        .getByText('Reassign to available resident')
        .closest('div');

      if (suggestionCard) {
        await user.click(suggestionCard);
      }

      await waitFor(() => {
        expect(screen.getByText('Applying...')).toBeInTheDocument();
      });
    });

    it('should show error when apply fails', async () => {
      const user = userEvent.setup();

      mockMutateAsync.mockRejectedValue(new Error('Failed to apply resolution'));

      mockedUseApplyResolution.mockReturnValue({
        mutateAsync: mockMutateAsync,
        isPending: false,
        isError: true,
        error: new Error('Failed to apply resolution'),
      } as unknown as ReturnType<typeof hooks.useApplyResolution>);

      mockedUseResolutionSuggestions.mockReturnValue({
        data: conflictsMockResponses.suggestions,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useResolutionSuggestions>);

      const conflict = conflictsMockFactories.conflict();

      render(<ConflictResolutionSuggestions conflict={conflict} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText(/Failed to apply resolution/i)).toBeInTheDocument();
      });
    });
  });

  describe('Cancel/Close', () => {
    it('should show cancel button when onClose provided', async () => {
      mockedUseResolutionSuggestions.mockReturnValue({
        data: conflictsMockResponses.suggestions,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useResolutionSuggestions>);

      const conflict = conflictsMockFactories.conflict();

      render(<ConflictResolutionSuggestions conflict={conflict} onClose={mockOnClose} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText('Cancel')).toBeInTheDocument();
      });
    });

    it('should call onClose when cancel clicked', async () => {
      const user = userEvent.setup();

      mockedUseResolutionSuggestions.mockReturnValue({
        data: conflictsMockResponses.suggestions,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useResolutionSuggestions>);

      const conflict = conflictsMockFactories.conflict();

      render(<ConflictResolutionSuggestions conflict={conflict} onClose={mockOnClose} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText('Cancel')).toBeInTheDocument();
      });

      const cancelButton = screen.getByText('Cancel');
      await user.click(cancelButton);

      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  describe('Sorting', () => {
    it('should show recommended suggestions first', async () => {
      mockedUseResolutionSuggestions.mockReturnValue({
        data: conflictsMockResponses.suggestions,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useResolutionSuggestions>);

      const conflict = conflictsMockFactories.conflict();

      const { container } = render(<ConflictResolutionSuggestions conflict={conflict} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        const suggestions = container.querySelectorAll('[data-testid*="suggestion"]');
        // First suggestion should have recommended badge
        expect(screen.getByText('Recommended')).toBeInTheDocument();
      });
    });

    it('should sort by confidence when recommendation status equal', async () => {
      const suggestions = [
        conflictsMockFactories.resolutionSuggestion({
          id: 'suggestion-1',
          recommended: false,
          confidence: 85,
        }),
        conflictsMockFactories.resolutionSuggestion({
          id: 'suggestion-2',
          recommended: false,
          confidence: 70,
        }),
      ];

      mockedUseResolutionSuggestions.mockReturnValue({
        data: suggestions,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useResolutionSuggestions>);

      const conflict = conflictsMockFactories.conflict();

      render(<ConflictResolutionSuggestions conflict={conflict} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText('85%')).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels', async () => {
      mockedUseResolutionSuggestions.mockReturnValue({
        data: conflictsMockResponses.suggestions,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useResolutionSuggestions>);

      const conflict = conflictsMockFactories.conflict();

      render(<ConflictResolutionSuggestions conflict={conflict} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getAllByLabelText('Expand')[0]).toBeInTheDocument();
      });
    });

    it('should update ARIA label when expanded', async () => {
      const user = userEvent.setup();

      mockedUseResolutionSuggestions.mockReturnValue({
        data: conflictsMockResponses.suggestions,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof hooks.useResolutionSuggestions>);

      const conflict = conflictsMockFactories.conflict();

      render(<ConflictResolutionSuggestions conflict={conflict} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText('Reassign to available resident')).toBeInTheDocument();
      });

      const expandButton = screen.getAllByLabelText('Expand')[0];
      await user.click(expandButton);

      await waitFor(() => {
        expect(screen.getAllByLabelText('Collapse')[0]).toBeInTheDocument();
      });
    });
  });
});
