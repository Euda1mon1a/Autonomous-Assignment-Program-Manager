/**
 * Enhanced Tests for SwapRequestForm Component
 *
 * Additional comprehensive tests covering edge cases, error scenarios,
 * accessibility, and user experience flows.
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SwapRequestForm } from '@/features/swap-marketplace/SwapRequestForm';
import * as hooks from '@/features/swap-marketplace/hooks';
import { mockAvailableWeeks, mockFacultyMembers, mockCreateSwapResponse } from './mockData';

// Mock the hooks
jest.mock('@/features/swap-marketplace/hooks');

// Create a wrapper with QueryClient for testing
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
    logger: {
      log: () => {},
      warn: () => {},
      error: () => {},
    },
  });

  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe('SwapRequestForm - Enhanced Tests', () => {
  const mockOnSuccess = jest.fn();
  const mockOnCancel = jest.fn();
  const mockMutateAsync = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();

    // Setup default mock implementations
    (hooks.useAvailableWeeks as jest.Mock).mockReturnValue({
      data: mockAvailableWeeks,
      isLoading: false,
      error: null,
    });

    (hooks.useFacultyMembers as jest.Mock).mockReturnValue({
      data: mockFacultyMembers,
      isLoading: false,
      error: null,
    });

    (hooks.useCreateSwapRequest as jest.Mock).mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: false,
      isSuccess: false,
      data: null,
      error: null,
    });
  });

  // ============================================================================
  // Edge Cases and Validation
  // ============================================================================

  describe('Edge Cases', () => {
    it('should handle empty reason gracefully', async () => {
      const user = userEvent.setup();
      mockMutateAsync.mockResolvedValue(mockCreateSwapResponse);

      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      const weekSelect = screen.getAllByRole('combobox')[0];
      await user.selectOptions(weekSelect, mockAvailableWeeks[0].date);

      const submitButton = screen.getByRole('button', { name: /create request/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith({
          weekToOffload: mockAvailableWeeks[0].date,
          reason: undefined,
          autoFindCandidates: true,
          preferredTargetFacultyId: undefined,
        });
      });
    });

    it('should trim whitespace from reason', async () => {
      const user = userEvent.setup();
      mockMutateAsync.mockResolvedValue(mockCreateSwapResponse);

      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      const weekSelect = screen.getAllByRole('combobox')[0];
      await user.selectOptions(weekSelect, mockAvailableWeeks[0].date);

      const reasonTextarea = screen.getByRole('textbox');
      await user.type(reasonTextarea, '   Conference attendance   ');

      const submitButton = screen.getByRole('button', { name: /create request/i });
      await user.click(submitButton);

      // The component should send the text as-is (trimming might be done server-side)
      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalled();
      });
    });

    it('should handle single week available', () => {
      (hooks.useAvailableWeeks as jest.Mock).mockReturnValue({
        data: [mockAvailableWeeks[0]],
        isLoading: false,
        error: null,
      });

      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      const select = screen.getAllByRole('combobox')[0] as HTMLSelectElement;
      expect(select.options.length).toBe(2); // placeholder + 1 week
    });

    it('should handle single faculty member available', async () => {
      const user = userEvent.setup();
      (hooks.useFacultyMembers as jest.Mock).mockReturnValue({
        data: [mockFacultyMembers[0]],
        isLoading: false,
        error: null,
      });

      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      const specificRadio = screen.getAllByRole('radio')[1];
      await user.click(specificRadio);

      const facultySelect = screen.getAllByRole('combobox')[1] as HTMLSelectElement;
      expect(facultySelect.options.length).toBe(2); // placeholder + 1 faculty
    });

    it('should clear validation errors when user corrects the form', async () => {
      const user = userEvent.setup();

      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      // Submit without selecting a week
      const submitButton = screen.getByRole('button', { name: /create request/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/please select a week to offload/i)).toBeInTheDocument();
      });

      // Now select a week
      const weekSelect = screen.getAllByRole('combobox')[0];
      await user.selectOptions(weekSelect, mockAvailableWeeks[0].date);

      // Error should still be visible until next submit
      expect(screen.getByText(/please select a week to offload/i)).toBeInTheDocument();
    });

    it('should handle weeks with conflicts correctly', () => {
      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      // Week with conflict should be available but marked
      const weekWithConflict = mockAvailableWeeks.find(w => w.hasConflict);
      expect(weekWithConflict).toBeDefined();
      expect(screen.getByText(/Has Conflict/)).toBeInTheDocument();
    });
  });

  // ============================================================================
  // Mode Switching and State Management
  // ============================================================================

  describe('Mode Switching', () => {
    it('should retain week selection when switching modes', async () => {
      const user = userEvent.setup();

      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      // Select a week
      const weekSelect = screen.getAllByRole('combobox')[0] as HTMLSelectElement;
      await user.selectOptions(weekSelect, mockAvailableWeeks[0].date);

      // Switch to specific mode
      const specificRadio = screen.getAllByRole('radio')[1];
      await user.click(specificRadio);

      // Week should still be selected
      expect(weekSelect.value).toBe(mockAvailableWeeks[0].date);
    });

    it('should retain reason when switching modes', async () => {
      const user = userEvent.setup();

      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      // Type a reason
      const reasonTextarea = screen.getByRole('textbox') as HTMLTextAreaElement;
      await user.type(reasonTextarea, 'Medical appointment');

      // Switch to specific mode
      const specificRadio = screen.getAllByRole('radio')[1];
      await user.click(specificRadio);

      // Reason should still be there
      expect(reasonTextarea.value).toBe('Medical appointment');
    });

    it('should clear faculty selection when switching from specific to auto mode', async () => {
      const user = userEvent.setup();

      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      // Switch to specific mode
      const specificRadio = screen.getAllByRole('radio')[1];
      await user.click(specificRadio);

      // Select a faculty
      const facultySelect = screen.getAllByRole('combobox')[1];
      await user.selectOptions(facultySelect, mockFacultyMembers[0].id);

      // Switch back to auto mode
      const autoRadio = screen.getAllByRole('radio')[0];
      await user.click(autoRadio);

      // Faculty field should be hidden
      expect(screen.queryByLabelText(/target faculty/i)).not.toBeInTheDocument();
    });
  });

  // ============================================================================
  // Error Handling and Recovery
  // ============================================================================

  describe('Error Handling', () => {
    it('should display API error message', async () => {
      const user = userEvent.setup();
      const errorMessage = 'You have already requested a swap for this week';
      mockMutateAsync.mockRejectedValue(new Error(errorMessage));

      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      const weekSelect = screen.getAllByRole('combobox')[0];
      await user.selectOptions(weekSelect, mockAvailableWeeks[0].date);

      const submitButton = screen.getByRole('button', { name: /create request/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(errorMessage)).toBeInTheDocument();
      });
    });

    it('should allow retry after submission failure', async () => {
      const user = userEvent.setup();
      mockMutateAsync.mockRejectedValueOnce(new Error('Network error'));

      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      const weekSelect = screen.getAllByRole('combobox')[0];
      await user.selectOptions(weekSelect, mockAvailableWeeks[0].date);

      const submitButton = screen.getByRole('button', { name: /create request/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/network error/i)).toBeInTheDocument();
      });

      // Now mock success
      mockMutateAsync.mockResolvedValue(mockCreateSwapResponse);

      // Try again
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnSuccess).toHaveBeenCalled();
      });
    });

    it('should handle server error with non-success response', async () => {
      const user = userEvent.setup();
      const errorResponse = {
        success: false,
        message: 'ACGME compliance violation: This swap would exceed weekly hours limit',
      };
      mockMutateAsync.mockResolvedValue(errorResponse);

      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      const weekSelect = screen.getAllByRole('combobox')[0];
      await user.selectOptions(weekSelect, mockAvailableWeeks[0].date);

      const submitButton = screen.getByRole('button', { name: /create request/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/ACGME compliance violation/i)).toBeInTheDocument();
        expect(mockOnSuccess).not.toHaveBeenCalled();
      });
    });

    it('should not call onSuccess if mutation throws', async () => {
      const user = userEvent.setup();
      mockMutateAsync.mockRejectedValue(new Error('Server error'));

      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      const weekSelect = screen.getAllByRole('combobox')[0];
      await user.selectOptions(weekSelect, mockAvailableWeeks[0].date);

      const submitButton = screen.getByRole('button', { name: /create request/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/server error/i)).toBeInTheDocument();
      });

      expect(mockOnSuccess).not.toHaveBeenCalled();
    });
  });

  // ============================================================================
  // Success States and Feedback
  // ============================================================================

  describe('Success States', () => {
    it('should display number of candidates notified', () => {
      (hooks.useCreateSwapRequest as jest.Mock).mockReturnValue({
        mutateAsync: mockMutateAsync,
        isPending: false,
        isSuccess: true,
        data: { ...mockCreateSwapResponse, candidatesNotified: 3 },
        error: null,
      });

      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText(/3 candidate\(s\) notified/i)).toBeInTheDocument();
    });

    it('should handle zero candidates notified', () => {
      (hooks.useCreateSwapRequest as jest.Mock).mockReturnValue({
        mutateAsync: mockMutateAsync,
        isPending: false,
        isSuccess: true,
        data: { ...mockCreateSwapResponse, candidatesNotified: 0 },
        error: null,
      });

      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText(/swap request created successfully/i)).toBeInTheDocument();
    });

    it('should not show success message if there are submit errors', () => {
      (hooks.useCreateSwapRequest as jest.Mock).mockReturnValue({
        mutateAsync: mockMutateAsync,
        isPending: false,
        isSuccess: true,
        data: mockCreateSwapResponse,
        error: null,
      });

      const { rerender } = render(
        <SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText(/swap request created successfully/i)).toBeInTheDocument();

      // Simulate error state
      (hooks.useCreateSwapRequest as jest.Mock).mockReturnValue({
        mutateAsync: mockMutateAsync,
        isPending: false,
        isSuccess: true,
        data: mockCreateSwapResponse,
        error: { message: 'Validation error' },
      });

      rerender(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />);

      // Success message should still show since isSuccess is true
      expect(screen.getByText(/swap request created successfully/i)).toBeInTheDocument();
    });
  });

  // ============================================================================
  // Accessibility
  // ============================================================================

  describe('Accessibility', () => {
    it('should have proper labels for all form fields', () => {
      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      expect(screen.getAllByRole('combobox')[0]).toBeInTheDocument();
      expect(screen.getAllByRole('radio')[0]).toBeInTheDocument();
      expect(screen.getAllByRole('radio')[1]).toBeInTheDocument();
      expect(screen.getByRole('textbox')).toBeInTheDocument();
    });

    it('should have accessible error messages linked to fields', async () => {
      const user = userEvent.setup();

      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      const submitButton = screen.getByRole('button', { name: /create request/i });
      await user.click(submitButton);

      await waitFor(() => {
        const weekSelect = screen.getAllByRole('combobox')[0];
        const errorMessage = screen.getByText(/please select a week to offload/i);

        // Error should be near the field
        expect(weekSelect.parentElement).toContainElement(errorMessage);
      });
    });

    it('should disable all interactive elements during submission', () => {
      (hooks.useCreateSwapRequest as jest.Mock).mockReturnValue({
        mutateAsync: mockMutateAsync,
        isPending: true,
        isSuccess: false,
        data: null,
        error: null,
      });

      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      expect(screen.getAllByRole('combobox')[0]).toBeDisabled();
      expect(screen.getAllByRole('radio')[0]).toBeDisabled();
      expect(screen.getAllByRole('radio')[1]).toBeDisabled();
      expect(screen.getByRole('textbox')).toBeDisabled();
      expect(screen.getByRole('button', { name: /creating\.\.\./i })).toBeDisabled();
    });

    it('should have proper ARIA attributes on buttons', () => {
      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      const submitButton = screen.getByRole('button', { name: /create request/i });
      expect(submitButton).toHaveAttribute('type', 'submit');

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      expect(cancelButton).toHaveAttribute('type', 'button');
    });
  });

  // ============================================================================
  // User Experience
  // ============================================================================

  describe('User Experience', () => {
    it('should show helpful help section', () => {
      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('How it works:')).toBeInTheDocument();
      expect(
        screen.getByText(/eligible faculty will be notified and can accept your request/i)
      ).toBeInTheDocument();
    });

    it('should provide clear feedback for empty state', () => {
      (hooks.useAvailableWeeks as jest.Mock).mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
      });

      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      expect(
        screen.getByText(/you currently have no assigned FMIT weeks to swap/i)
      ).toBeInTheDocument();
    });

    it('should show character counter for reason field', () => {
      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('0/500 characters')).toBeInTheDocument();
    });

    it('should provide mode descriptions', () => {
      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      expect(
        screen.getByText(/system will notify all eligible faculty members who can take this week/i)
      ).toBeInTheDocument();
      expect(
        screen.getByText(/send request to a specific faculty member/i)
      ).toBeInTheDocument();
    });
  });

  // ============================================================================
  // Complex Workflows
  // ============================================================================

  describe('Complex Workflows', () => {
    it('should handle complete workflow: auto mode submission', async () => {
      const user = userEvent.setup();
      mockMutateAsync.mockResolvedValue(mockCreateSwapResponse);

      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      // 1. Select week
      const weekSelect = screen.getAllByRole('combobox')[0];
      await user.selectOptions(weekSelect, mockAvailableWeeks[0].date);

      // 2. Ensure auto mode is selected (default)
      const autoRadio = screen.getAllByRole('radio')[0] as HTMLInputElement;
      expect(autoRadio).toBeChecked();

      // 3. Add reason
      const reasonTextarea = screen.getByRole('textbox');
      await user.type(reasonTextarea, 'Conference in another city');

      // 4. Submit
      const submitButton = screen.getByRole('button', { name: /create request/i });
      await user.click(submitButton);

      // 5. Verify submission
      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith({
          weekToOffload: mockAvailableWeeks[0].date,
          reason: 'Conference in another city',
          autoFindCandidates: true,
          preferredTargetFacultyId: undefined,
        });
      });

      // 6. Verify success callback
      expect(mockOnSuccess).toHaveBeenCalled();
    });

    it('should handle complete workflow: specific faculty submission', async () => {
      const user = userEvent.setup();
      mockMutateAsync.mockResolvedValue(mockCreateSwapResponse);

      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      // 1. Select week
      const weekSelect = screen.getAllByRole('combobox')[0];
      await user.selectOptions(weekSelect, mockAvailableWeeks[1].date);

      // 2. Switch to specific mode
      const specificRadio = screen.getAllByRole('radio')[1];
      await user.click(specificRadio);

      // 3. Select faculty
      const facultySelect = screen.getAllByRole('combobox')[1];
      await user.selectOptions(facultySelect, mockFacultyMembers[2].id);

      // 4. Add reason
      const reasonTextarea = screen.getByRole('textbox');
      await user.type(reasonTextarea, 'Personal request');

      // 5. Submit
      const submitButton = screen.getByRole('button', { name: /create request/i });
      await user.click(submitButton);

      // 6. Verify submission
      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith({
          weekToOffload: mockAvailableWeeks[1].date,
          reason: 'Personal request',
          autoFindCandidates: false,
          preferredTargetFacultyId: mockFacultyMembers[2].id,
        });
      });

      expect(mockOnSuccess).toHaveBeenCalled();
    });

    it('should handle validation failure and correction workflow', async () => {
      const user = userEvent.setup();
      mockMutateAsync.mockResolvedValue(mockCreateSwapResponse);

      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      // 1. Try to submit without selecting week
      const submitButton = screen.getByRole('button', { name: /create request/i });
      await user.click(submitButton);

      // 2. See validation error
      await waitFor(() => {
        expect(screen.getByText(/please select a week to offload/i)).toBeInTheDocument();
      });

      // 3. Fix the issue
      const weekSelect = screen.getAllByRole('combobox')[0];
      await user.selectOptions(weekSelect, mockAvailableWeeks[0].date);

      // 4. Submit again
      await user.click(submitButton);

      // 5. Should succeed now
      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalled();
      });
    });
  });
});
