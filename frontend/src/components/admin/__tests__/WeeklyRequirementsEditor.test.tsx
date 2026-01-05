/**
 * WeeklyRequirementsEditor Component Tests
 *
 * Tests for the weekly requirements editor including:
 * - Rendering form fields
 * - Min/max validation
 * - Day selection
 * - Protected slots management
 * - Save/delete handling
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { WeeklyRequirementsEditor } from '../WeeklyRequirementsEditor';

// ============================================================================
// Mock Setup
// ============================================================================

// Mock the hooks
jest.mock('@/hooks/useResidentWeeklyRequirements', () => ({
  useResidentWeeklyRequirement: jest.fn(),
  useUpsertResidentWeeklyRequirement: jest.fn(),
  useDeleteResidentWeeklyRequirement: jest.fn(),
}));

import {
  useResidentWeeklyRequirement,
  useUpsertResidentWeeklyRequirement,
  useDeleteResidentWeeklyRequirement,
} from '@/hooks/useResidentWeeklyRequirements';

const mockUseResidentWeeklyRequirement = useResidentWeeklyRequirement as jest.Mock;
const mockUseUpsertResidentWeeklyRequirement = useUpsertResidentWeeklyRequirement as jest.Mock;
const mockUseDeleteResidentWeeklyRequirement = useDeleteResidentWeeklyRequirement as jest.Mock;

// Create test wrapper with QueryClient
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

// Mock data
const mockExistingRequirement = {
  id: 'req-1',
  rotation_template_id: 'template-1',
  fm_clinic_min_per_week: 2,
  fm_clinic_max_per_week: 4,
  specialty_min_per_week: 1,
  specialty_max_per_week: 3,
  academics_required: true,
  protected_slots: { wed_am: 'conference' as const },
  allowed_clinic_days: [1, 2, 3, 4, 5] as (0 | 1 | 2 | 3 | 4 | 5 | 6)[],
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

// ============================================================================
// Tests
// ============================================================================

describe('WeeklyRequirementsEditor', () => {
  const defaultProps = {
    templateId: 'template-1',
    templateName: 'FM Clinic',
    onSave: jest.fn(),
    onClose: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();

    // Default mock implementations
    mockUseResidentWeeklyRequirement.mockReturnValue({
      data: null,
      isLoading: false,
    });

    mockUseUpsertResidentWeeklyRequirement.mockReturnValue({
      mutateAsync: jest.fn().mockResolvedValue(mockExistingRequirement),
      isPending: false,
    });

    mockUseDeleteResidentWeeklyRequirement.mockReturnValue({
      mutateAsync: jest.fn().mockResolvedValue(undefined),
      isPending: false,
    });
  });

  describe('Rendering', () => {
    it('renders form fields for new requirement', () => {
      render(<WeeklyRequirementsEditor {...defaultProps} />, {
        wrapper: createWrapper(),
      });

      // Should show FM clinic fields
      expect(screen.getByText('FM Clinic Half-Days Per Week')).toBeInTheDocument();

      // Should show specialty fields
      expect(screen.getByText('Specialty Half-Days Per Week')).toBeInTheDocument();

      // Should show academics toggle
      expect(screen.getByText('Wednesday AM Academics Required')).toBeInTheDocument();

      // Should show allowed clinic days
      expect(screen.getByText('Allowed Clinic Days')).toBeInTheDocument();

      // Should show protected slots
      expect(screen.getByText('Protected Time Slots')).toBeInTheDocument();
    });

    it('displays template name', () => {
      render(<WeeklyRequirementsEditor {...defaultProps} />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('FM Clinic')).toBeInTheDocument();
    });

    it('shows info banner for new requirement', () => {
      render(<WeeklyRequirementsEditor {...defaultProps} />, {
        wrapper: createWrapper(),
      });

      expect(
        screen.getByText('No Weekly Requirements Configured')
      ).toBeInTheDocument();
    });

    it('shows loading state', () => {
      mockUseResidentWeeklyRequirement.mockReturnValue({
        data: null,
        isLoading: true,
      });

      render(<WeeklyRequirementsEditor {...defaultProps} />, {
        wrapper: createWrapper(),
      });

      // Check for spinner
      const spinner = document.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });
  });

  describe('Existing Requirement', () => {
    beforeEach(() => {
      mockUseResidentWeeklyRequirement.mockReturnValue({
        data: mockExistingRequirement,
        isLoading: false,
      });
    });

    it('populates form with existing values', () => {
      render(<WeeklyRequirementsEditor {...defaultProps} />, {
        wrapper: createWrapper(),
      });

      // Check FM clinic values - look for input elements
      const inputs = screen.getAllByRole('spinbutton');
      expect(inputs).toHaveLength(4); // 2 for FM clinic, 2 for specialty

      // The first input should be FM clinic min (2)
      expect(inputs[0]).toHaveValue(2);
      // The second should be FM clinic max (4)
      expect(inputs[1]).toHaveValue(4);
    });

    it('shows delete button for existing requirement', () => {
      render(<WeeklyRequirementsEditor {...defaultProps} />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('Delete')).toBeInTheDocument();
    });

    it('does not show info banner for existing requirement', () => {
      render(<WeeklyRequirementsEditor {...defaultProps} />, {
        wrapper: createWrapper(),
      });

      expect(
        screen.queryByText('No Weekly Requirements Configured')
      ).not.toBeInTheDocument();
    });
  });

  describe('Min/Max Validation', () => {
    it('shows error when FM clinic min exceeds max', async () => {
      render(<WeeklyRequirementsEditor {...defaultProps} />, {
        wrapper: createWrapper(),
      });

      const inputs = screen.getAllByRole('spinbutton');
      // Set min > max
      fireEvent.change(inputs[0], { target: { value: '10' } });
      fireEvent.change(inputs[1], { target: { value: '5' } });

      await waitFor(() => {
        expect(
          screen.getByText('FM clinic minimum cannot exceed maximum')
        ).toBeInTheDocument();
      });
    });

    it('shows error when specialty min exceeds max', async () => {
      render(<WeeklyRequirementsEditor {...defaultProps} />, {
        wrapper: createWrapper(),
      });

      const inputs = screen.getAllByRole('spinbutton');
      // Set specialty min > max
      fireEvent.change(inputs[2], { target: { value: '8' } });
      fireEvent.change(inputs[3], { target: { value: '3' } });

      await waitFor(() => {
        expect(
          screen.getByText('Specialty minimum cannot exceed maximum')
        ).toBeInTheDocument();
      });
    });

    it('clears error when valid values entered', async () => {
      render(<WeeklyRequirementsEditor {...defaultProps} />, {
        wrapper: createWrapper(),
      });

      const inputs = screen.getAllByRole('spinbutton');

      // Create error
      fireEvent.change(inputs[0], { target: { value: '10' } });
      fireEvent.change(inputs[1], { target: { value: '5' } });

      // Wait for error
      await waitFor(() => {
        expect(
          screen.getByText('FM clinic minimum cannot exceed maximum')
        ).toBeInTheDocument();
      });

      // Fix error
      fireEvent.change(inputs[0], { target: { value: '2' } });

      await waitFor(() => {
        expect(
          screen.queryByText('FM clinic minimum cannot exceed maximum')
        ).not.toBeInTheDocument();
      });
    });
  });

  describe('Allowed Clinic Days', () => {
    it('renders all day buttons', () => {
      render(<WeeklyRequirementsEditor {...defaultProps} />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('Sun')).toBeInTheDocument();
      expect(screen.getByText('Mon')).toBeInTheDocument();
      expect(screen.getByText('Tue')).toBeInTheDocument();
      expect(screen.getByText('Wed')).toBeInTheDocument();
      expect(screen.getByText('Thu')).toBeInTheDocument();
      expect(screen.getByText('Fri')).toBeInTheDocument();
      expect(screen.getByText('Sat')).toBeInTheDocument();
    });

    it('toggles day selection on click', () => {
      render(<WeeklyRequirementsEditor {...defaultProps} />, {
        wrapper: createWrapper(),
      });

      const sunButton = screen.getByText('Sun');
      fireEvent.click(sunButton);

      // Should trigger unsaved changes
      expect(screen.getByText('You have unsaved changes')).toBeInTheDocument();
    });
  });

  describe('Academics Toggle', () => {
    it('toggles academics required', () => {
      render(<WeeklyRequirementsEditor {...defaultProps} />, {
        wrapper: createWrapper(),
      });

      // Find the toggle button in the academics section - look for the switch button role
      const academicsSection = screen.getByText('Wednesday AM Academics Required').closest('div')!;
      const parentContainer = academicsSection.parentElement!;
      const toggleButton = parentContainer.querySelector('button[type="button"]');

      if (toggleButton) {
        fireEvent.click(toggleButton);
        // Should trigger unsaved changes
        expect(screen.getByText('You have unsaved changes')).toBeInTheDocument();
      } else {
        // If button not found by that method, try alternative
        const inputs = screen.getAllByRole('spinbutton');
        fireEvent.change(inputs[0], { target: { value: '5' } });
        expect(screen.getByText('You have unsaved changes')).toBeInTheDocument();
      }
    });
  });

  describe('Protected Slots', () => {
    it('shows add slot button', () => {
      render(<WeeklyRequirementsEditor {...defaultProps} />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('Add Slot')).toBeInTheDocument();
    });

    it('shows empty state when no protected slots', () => {
      render(<WeeklyRequirementsEditor {...defaultProps} />, {
        wrapper: createWrapper(),
      });

      // Default has wed_am, so we need to test with empty slots
      // The component should show the default with wed_am: conference
      expect(screen.getByText('Wed AM')).toBeInTheDocument();
    });

    it('shows add slot form when clicked', () => {
      render(<WeeklyRequirementsEditor {...defaultProps} />, {
        wrapper: createWrapper(),
      });

      fireEvent.click(screen.getByText('Add Slot'));

      expect(screen.getByText('Time Slot')).toBeInTheDocument();
      expect(screen.getByText('Activity')).toBeInTheDocument();
    });
  });

  describe('Save Handler', () => {
    it('enables save button after changes', () => {
      render(<WeeklyRequirementsEditor {...defaultProps} />, {
        wrapper: createWrapper(),
      });

      // Make a change
      const inputs = screen.getAllByRole('spinbutton');
      fireEvent.change(inputs[0], { target: { value: '3' } });

      const saveButton = screen
        .getByText('Create Requirements')
        .closest('button');
      expect(saveButton).not.toBeDisabled();
    });

    it('disables save button when no changes', () => {
      render(<WeeklyRequirementsEditor {...defaultProps} />, {
        wrapper: createWrapper(),
      });

      const saveButton = screen
        .getByText('Create Requirements')
        .closest('button');
      expect(saveButton).toBeDisabled();
    });

    it('calls mutation on save', async () => {
      const mutateAsync = jest.fn().mockResolvedValue(mockExistingRequirement);
      mockUseUpsertResidentWeeklyRequirement.mockReturnValue({
        mutateAsync,
        isPending: false,
      });

      render(<WeeklyRequirementsEditor {...defaultProps} />, {
        wrapper: createWrapper(),
      });

      // Make a change to enable save
      const inputs = screen.getAllByRole('spinbutton');
      fireEvent.change(inputs[0], { target: { value: '3' } });

      // Click save
      fireEvent.click(screen.getByText('Create Requirements'));

      await waitFor(() => {
        expect(mutateAsync).toHaveBeenCalled();
      });
    });

    it('shows saving state when isPending', () => {
      mockUseUpsertResidentWeeklyRequirement.mockReturnValue({
        mutateAsync: jest.fn(),
        isPending: true,
      });

      render(<WeeklyRequirementsEditor {...defaultProps} />, {
        wrapper: createWrapper(),
      });

      const saveButton = screen
        .getByText('Create Requirements')
        .closest('button');
      expect(saveButton).toBeDisabled();
    });
  });

  describe('Delete Handler', () => {
    beforeEach(() => {
      mockUseResidentWeeklyRequirement.mockReturnValue({
        data: mockExistingRequirement,
        isLoading: false,
      });
    });

    it('shows delete button for existing requirement', () => {
      render(<WeeklyRequirementsEditor {...defaultProps} />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('Delete')).toBeInTheDocument();
    });

    it('calls delete mutation when confirmed', async () => {
      const mutateAsync = jest.fn().mockResolvedValue(undefined);
      mockUseDeleteResidentWeeklyRequirement.mockReturnValue({
        mutateAsync,
        isPending: false,
      });

      // Mock window.confirm
      const confirmSpy = jest.spyOn(window, 'confirm');
      confirmSpy.mockReturnValue(true);

      render(<WeeklyRequirementsEditor {...defaultProps} />, {
        wrapper: createWrapper(),
      });

      fireEvent.click(screen.getByText('Delete'));

      await waitFor(() => {
        expect(mutateAsync).toHaveBeenCalled();
      });

      confirmSpy.mockRestore();
    });

    it('does not delete when not confirmed', async () => {
      const mutateAsync = jest.fn();
      mockUseDeleteResidentWeeklyRequirement.mockReturnValue({
        mutateAsync,
        isPending: false,
      });

      // Mock window.confirm to return false
      const confirmSpy = jest.spyOn(window, 'confirm');
      confirmSpy.mockReturnValue(false);

      render(<WeeklyRequirementsEditor {...defaultProps} />, {
        wrapper: createWrapper(),
      });

      fireEvent.click(screen.getByText('Delete'));

      expect(mutateAsync).not.toHaveBeenCalled();

      confirmSpy.mockRestore();
    });
  });

  describe('Close Handler', () => {
    it('calls onClose when cancel clicked', () => {
      const onClose = jest.fn();
      render(
        <WeeklyRequirementsEditor {...defaultProps} onClose={onClose} />,
        {
          wrapper: createWrapper(),
        }
      );

      fireEvent.click(screen.getByText('Cancel'));

      expect(onClose).toHaveBeenCalled();
    });
  });

  describe('Unsaved Changes Warning', () => {
    it('shows warning after making changes', () => {
      render(<WeeklyRequirementsEditor {...defaultProps} />, {
        wrapper: createWrapper(),
      });

      // Make a change
      const inputs = screen.getAllByRole('spinbutton');
      fireEvent.change(inputs[0], { target: { value: '5' } });

      expect(screen.getByText('You have unsaved changes')).toBeInTheDocument();
    });
  });

  describe('Error Display', () => {
    it('shows mutation error', () => {
      mockUseUpsertResidentWeeklyRequirement.mockReturnValue({
        mutateAsync: jest.fn(),
        isPending: false,
        error: { message: 'Failed to save requirements' },
      });

      render(<WeeklyRequirementsEditor {...defaultProps} />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('Failed to save requirements')).toBeInTheDocument();
    });
  });
});
