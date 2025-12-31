import { render, screen, fireEvent, waitFor } from '@/test-utils';
import { SwapRequestForm, SwapRequestFormProps, BlockDetails } from '@/components/swap/SwapRequestForm';

// Mock child components
jest.mock('@/components/schedule/ShiftIndicator', () => ({
  ShiftIndicator: ({ shift, size, variant }: any) => (
    <span data-testid="shift-indicator">{shift}</span>
  ),
}));

jest.mock('@/components/schedule/RotationBadge', () => ({
  RotationBadge: ({ rotationType, size }: any) => (
    <span data-testid="rotation-badge">{rotationType}</span>
  ),
}));

describe('SwapRequestForm', () => {
  const mockBlocks: BlockDetails[] = [
    {
      id: 'block-1',
      date: '2025-01-15',
      shift: 'AM',
      rotationType: 'Inpatient',
      personName: 'Dr. Current User',
    },
    {
      id: 'block-2',
      date: '2025-01-20',
      shift: 'PM',
      rotationType: 'Clinic',
      personName: 'Dr. Current User',
    },
  ];

  const mockPersons = [
    { id: 'person-1', name: 'Dr. Alice Smith', role: 'PGY-2' },
    { id: 'person-2', name: 'Dr. Bob Jones', role: 'PGY-3' },
  ];

  const mockGetAvailableBlocks = jest.fn<Promise<BlockDetails[]>, [string]>().mockResolvedValue([
    {
      id: 'target-block-1',
      date: '2025-01-16',
      shift: 'AM',
      rotationType: 'Procedure',
      personName: 'Dr. Alice Smith',
    },
  ]);

  const mockOnSubmit = jest.fn().mockResolvedValue(undefined);
  const mockOnCancel = jest.fn();

  const defaultProps: SwapRequestFormProps = {
    currentUserBlocks: mockBlocks,
    availablePersons: mockPersons,
    getAvailableBlocksForPerson: mockGetAvailableBlocks,
    onSubmit: mockOnSubmit,
    onCancel: mockOnCancel,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    it('renders without crashing', () => {
      render(<SwapRequestForm {...defaultProps} />);

      expect(screen.getByText('Create Swap Request')).toBeInTheDocument();
    });

    it('renders swap type selection buttons', () => {
      render(<SwapRequestForm {...defaultProps} />);

      expect(screen.getByText('One-to-One')).toBeInTheDocument();
      expect(screen.getByText('Absorb')).toBeInTheDocument();
      expect(screen.getByText('Give Away')).toBeInTheDocument();
    });

    it('renders block selection dropdown', () => {
      render(<SwapRequestForm {...defaultProps} />);

      expect(screen.getByLabelText(/Block to Give Up/i)).toBeInTheDocument();
    });

    it('renders reason dropdown', () => {
      render(<SwapRequestForm {...defaultProps} />);

      expect(screen.getByLabelText(/Reason for Swap/i)).toBeInTheDocument();
    });

    it('renders notes textarea', () => {
      render(<SwapRequestForm {...defaultProps} />);

      expect(screen.getByLabelText(/Additional Notes/i)).toBeInTheDocument();
    });

    it('renders submit and cancel buttons', () => {
      render(<SwapRequestForm {...defaultProps} />);

      expect(screen.getByText('Create Swap Request')).toBeInTheDocument();
      expect(screen.getByText('Cancel')).toBeInTheDocument();
    });
  });

  describe('Swap Type Selection', () => {
    it('selects one-to-one swap by default', () => {
      const { container } = render(<SwapRequestForm {...defaultProps} />);

      const oneToOneButton = screen.getByText('One-to-One').closest('button');
      expect(oneToOneButton).toHaveClass('border-blue-600');
      expect(oneToOneButton).toHaveClass('bg-blue-50');
    });

    it('changes to absorb swap when clicked', () => {
      render(<SwapRequestForm {...defaultProps} />);

      const absorbButton = screen.getByText('Absorb').closest('button');
      fireEvent.click(absorbButton!);

      expect(absorbButton).toHaveClass('border-blue-600');
      expect(absorbButton).toHaveClass('bg-blue-50');
    });

    it('changes to give-away swap when clicked', () => {
      render(<SwapRequestForm {...defaultProps} />);

      const giveAwayButton = screen.getByText('Give Away').closest('button');
      fireEvent.click(giveAwayButton!);

      expect(giveAwayButton).toHaveClass('border-blue-600');
      expect(giveAwayButton).toHaveClass('bg-blue-50');
    });

    it('shows target person selection only for one-to-one swaps', () => {
      render(<SwapRequestForm {...defaultProps} />);

      expect(screen.getByLabelText(/Swap With/i)).toBeInTheDocument();

      // Switch to absorb
      const absorbButton = screen.getByText('Absorb').closest('button');
      fireEvent.click(absorbButton!);

      expect(screen.queryByLabelText(/Swap With/i)).not.toBeInTheDocument();
    });
  });

  describe('Block Selection', () => {
    it('displays all current user blocks in dropdown', () => {
      render(<SwapRequestForm {...defaultProps} />);

      const select = screen.getByLabelText(/Block to Give Up/i);
      fireEvent.click(select);

      expect(screen.getByText(/1\/15\/2025.*AM.*Inpatient/)).toBeInTheDocument();
      expect(screen.getByText(/1\/20\/2025.*PM.*Clinic/)).toBeInTheDocument();
    });

    it('shows selected block details', () => {
      render(<SwapRequestForm {...defaultProps} />);

      const select = screen.getByLabelText(/Block to Give Up/i) as HTMLSelectElement;
      fireEvent.change(select, { target: { value: 'block-1' } });

      expect(screen.getByText('1/15/2025')).toBeInTheDocument();
      expect(screen.getByTestId('shift-indicator')).toHaveTextContent('AM');
      expect(screen.getByTestId('rotation-badge')).toHaveTextContent('Inpatient');
    });
  });

  describe('One-to-One Swap Flow', () => {
    it('loads target blocks when target person is selected', async () => {
      render(<SwapRequestForm {...defaultProps} />);

      const personSelect = screen.getByLabelText(/Swap With/i) as HTMLSelectElement;
      fireEvent.change(personSelect, { target: { value: 'person-1' } });

      await waitFor(() => {
        expect(mockGetAvailableBlocks).toHaveBeenCalledWith('person-1');
      });

      expect(screen.getByLabelText(/Their Block/i)).toBeInTheDocument();
    });

    it('displays loading state while fetching target blocks', async () => {
      mockGetAvailableBlocks.mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve([]), 100))
      );

      render(<SwapRequestForm {...defaultProps} />);

      const personSelect = screen.getByLabelText(/Swap With/i) as HTMLSelectElement;
      fireEvent.change(personSelect, { target: { value: 'person-1' } });

      expect(await screen.findByText(/Loading available blocks/i)).toBeInTheDocument();
    });

    it('shows error when target blocks fail to load', async () => {
      mockGetAvailableBlocks.mockRejectedValueOnce(new Error('Network error'));

      render(<SwapRequestForm {...defaultProps} />);

      const personSelect = screen.getByLabelText(/Swap With/i) as HTMLSelectElement;
      fireEvent.change(personSelect, { target: { value: 'person-1' } });

      await waitFor(() => {
        expect(screen.getByText(/Failed to load available blocks/i)).toBeInTheDocument();
      });
    });

    it('shows message when no blocks available for target person', async () => {
      mockGetAvailableBlocks.mockResolvedValueOnce([]);

      render(<SwapRequestForm {...defaultProps} />);

      const personSelect = screen.getByLabelText(/Swap With/i) as HTMLSelectElement;
      fireEvent.change(personSelect, { target: { value: 'person-1' } });

      await waitFor(() => {
        expect(screen.getByText(/No available blocks for this person/i)).toBeInTheDocument();
      });
    });

    it('displays target block details when selected', async () => {
      render(<SwapRequestForm {...defaultProps} />);

      // Select target person
      const personSelect = screen.getByLabelText(/Swap With/i) as HTMLSelectElement;
      fireEvent.change(personSelect, { target: { value: 'person-1' } });

      await waitFor(() => {
        expect(screen.getByLabelText(/Their Block/i)).toBeInTheDocument();
      });

      // Select target block
      const blockSelect = screen.getByLabelText(/Their Block/i) as HTMLSelectElement;
      fireEvent.change(blockSelect, { target: { value: 'target-block-1' } });

      await waitFor(() => {
        expect(screen.getByText('1/16/2025')).toBeInTheDocument();
      });
    });
  });

  describe('Form Validation', () => {
    it('shows error when submitting without selecting block', async () => {
      render(<SwapRequestForm {...defaultProps} />);

      const submitButton = screen.getByText('Create Swap Request');
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/Please select a block to give up/i)).toBeInTheDocument();
      });

      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    it('shows error when submitting without reason', async () => {
      render(<SwapRequestForm {...defaultProps} />);

      // Select block
      const blockSelect = screen.getByLabelText(/Block to Give Up/i) as HTMLSelectElement;
      fireEvent.change(blockSelect, { target: { value: 'block-1' } });

      const submitButton = screen.getByText('Create Swap Request');
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/Please provide a reason for the swap/i)).toBeInTheDocument();
      });

      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    it('shows error for one-to-one without target person', async () => {
      render(<SwapRequestForm {...defaultProps} />);

      // Select block and reason
      const blockSelect = screen.getByLabelText(/Block to Give Up/i) as HTMLSelectElement;
      fireEvent.change(blockSelect, { target: { value: 'block-1' } });

      const reasonSelect = screen.getByLabelText(/Reason for Swap/i) as HTMLSelectElement;
      fireEvent.change(reasonSelect, { target: { value: 'personal' } });

      const submitButton = screen.getByText('Create Swap Request');
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/Please select a target person and block/i)).toBeInTheDocument();
      });
    });
  });

  describe('Form Submission', () => {
    it('submits valid one-to-one swap request', async () => {
      render(<SwapRequestForm {...defaultProps} />);

      // Fill form
      const blockSelect = screen.getByLabelText(/Block to Give Up/i) as HTMLSelectElement;
      fireEvent.change(blockSelect, { target: { value: 'block-1' } });

      const reasonSelect = screen.getByLabelText(/Reason for Swap/i) as HTMLSelectElement;
      fireEvent.change(reasonSelect, { target: { value: 'personal' } });

      const personSelect = screen.getByLabelText(/Swap With/i) as HTMLSelectElement;
      fireEvent.change(personSelect, { target: { value: 'person-1' } });

      await waitFor(() => {
        expect(screen.getByLabelText(/Their Block/i)).toBeInTheDocument();
      });

      const targetBlockSelect = screen.getByLabelText(/Their Block/i) as HTMLSelectElement;
      fireEvent.change(targetBlockSelect, { target: { value: 'target-block-1' } });

      const submitButton = screen.getByText('Create Swap Request');
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith({
          requestorPersonId: '',
          givingUpBlockId: 'block-1',
          swapType: 'one-to-one',
          targetPersonId: 'person-1',
          targetBlockId: 'target-block-1',
          reason: 'personal',
          notes: undefined,
        });
      });
    });

    it('submits absorb swap request', async () => {
      render(<SwapRequestForm {...defaultProps} />);

      // Select absorb type
      const absorbButton = screen.getByText('Absorb').closest('button');
      fireEvent.click(absorbButton!);

      // Fill form
      const blockSelect = screen.getByLabelText(/Block to Give Up/i) as HTMLSelectElement;
      fireEvent.change(blockSelect, { target: { value: 'block-1' } });

      const reasonSelect = screen.getByLabelText(/Reason for Swap/i) as HTMLSelectElement;
      fireEvent.change(reasonSelect, { target: { value: 'medical' } });

      const submitButton = screen.getByText('Create Swap Request');
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith({
          requestorPersonId: '',
          givingUpBlockId: 'block-1',
          swapType: 'absorb',
          targetPersonId: undefined,
          targetBlockId: undefined,
          reason: 'medical',
          notes: undefined,
        });
      });
    });

    it('includes notes when provided', async () => {
      render(<SwapRequestForm {...defaultProps} />);

      // Fill form
      const absorbButton = screen.getByText('Absorb').closest('button');
      fireEvent.click(absorbButton!);

      const blockSelect = screen.getByLabelText(/Block to Give Up/i) as HTMLSelectElement;
      fireEvent.change(blockSelect, { target: { value: 'block-1' } });

      const reasonSelect = screen.getByLabelText(/Reason for Swap/i) as HTMLSelectElement;
      fireEvent.change(reasonSelect, { target: { value: 'personal' } });

      const notesTextarea = screen.getByLabelText(/Additional Notes/i);
      fireEvent.change(notesTextarea, { target: { value: 'Family emergency' } });

      const submitButton = screen.getByText('Create Swap Request');
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith(
          expect.objectContaining({
            notes: 'Family emergency',
          })
        );
      });
    });

    it('shows loading state during submission', async () => {
      mockOnSubmit.mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      );

      render(<SwapRequestForm {...defaultProps} />);

      // Fill minimal valid form
      const absorbButton = screen.getByText('Absorb').closest('button');
      fireEvent.click(absorbButton!);

      const blockSelect = screen.getByLabelText(/Block to Give Up/i) as HTMLSelectElement;
      fireEvent.change(blockSelect, { target: { value: 'block-1' } });

      const reasonSelect = screen.getByLabelText(/Reason for Swap/i) as HTMLSelectElement;
      fireEvent.change(reasonSelect, { target: { value: 'personal' } });

      const submitButton = screen.getByText('Create Swap Request');
      fireEvent.click(submitButton);

      expect(await screen.findByText('Submitting...')).toBeInTheDocument();
    });

    it('shows error message on submission failure', async () => {
      mockOnSubmit.mockRejectedValueOnce(new Error('Server error'));

      render(<SwapRequestForm {...defaultProps} />);

      // Fill minimal valid form
      const absorbButton = screen.getByText('Absorb').closest('button');
      fireEvent.click(absorbButton!);

      const blockSelect = screen.getByLabelText(/Block to Give Up/i) as HTMLSelectElement;
      fireEvent.change(blockSelect, { target: { value: 'block-1' } });

      const reasonSelect = screen.getByLabelText(/Reason for Swap/i) as HTMLSelectElement;
      fireEvent.change(reasonSelect, { target: { value: 'personal' } });

      const submitButton = screen.getByText('Create Swap Request');
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Server error')).toBeInTheDocument();
      });
    });
  });

  describe('Cancel Functionality', () => {
    it('calls onCancel when cancel button clicked', () => {
      render(<SwapRequestForm {...defaultProps} />);

      const cancelButton = screen.getByText('Cancel');
      fireEvent.click(cancelButton);

      expect(mockOnCancel).toHaveBeenCalledTimes(1);
    });

    it('disables cancel button during submission', async () => {
      mockOnSubmit.mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      );

      render(<SwapRequestForm {...defaultProps} />);

      // Submit form
      const absorbButton = screen.getByText('Absorb').closest('button');
      fireEvent.click(absorbButton!);

      const blockSelect = screen.getByLabelText(/Block to Give Up/i) as HTMLSelectElement;
      fireEvent.change(blockSelect, { target: { value: 'block-1' } });

      const reasonSelect = screen.getByLabelText(/Reason for Swap/i) as HTMLSelectElement;
      fireEvent.change(reasonSelect, { target: { value: 'personal' } });

      const submitButton = screen.getByText('Create Swap Request');
      fireEvent.click(submitButton);

      const cancelButton = await screen.findByText('Cancel');
      expect(cancelButton).toBeDisabled();
    });
  });

  describe('Custom Styling', () => {
    it('applies custom className', () => {
      const { container } = render(<SwapRequestForm {...defaultProps} className="custom-form" />);

      expect(container.querySelector('.custom-form')).toBeInTheDocument();
    });
  });
});
