/**
 * Tests for SwapRequestForm Component
 *
 * Tests form validation, submission, and mode switching
 */

import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
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

describe('SwapRequestForm', () => {
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

  describe('Loading State', () => {
    it('should show loading spinner when weeks are loading', () => {
      (hooks.useAvailableWeeks as jest.Mock).mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
      });

      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('Loading form data...')).toBeInTheDocument();
    });

    it('should show loading spinner when faculty are loading', () => {
      (hooks.useFacultyMembers as jest.Mock).mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
      });

      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('Loading form data...')).toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    it('should show error when weeks fail to load', () => {
      (hooks.useAvailableWeeks as jest.Mock).mockReturnValue({
        data: undefined,
        isLoading: false,
        error: { message: 'Failed to load available weeks' },
      });

      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('Error Loading Form Data')).toBeInTheDocument();
      expect(screen.getByText('Failed to load available weeks')).toBeInTheDocument();
    });

    it('should show error when faculty fail to load', () => {
      (hooks.useFacultyMembers as jest.Mock).mockReturnValue({
        data: undefined,
        isLoading: false,
        error: { message: 'Failed to load faculty members' },
      });

      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('Error Loading Form Data')).toBeInTheDocument();
      expect(screen.getByText('Failed to load faculty members')).toBeInTheDocument();
    });

    it('should show Go Back button in error state when onCancel is provided', () => {
      (hooks.useAvailableWeeks as jest.Mock).mockReturnValue({
        data: undefined,
        isLoading: false,
        error: { message: 'Failed to load data' },
      });

      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByRole('button', { name: /go back/i })).toBeInTheDocument();
    });
  });

  describe('Form Rendering', () => {
    it('should render form title', () => {
      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('Create Swap Request')).toBeInTheDocument();
    });

    it('should render week selection dropdown', () => {
      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      expect(screen.getAllByRole('combobox')[0]).toBeInTheDocument();
    });

    it('should render swap mode radio buttons', () => {
      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      expect(screen.getAllByRole('radio')[0]).toBeInTheDocument();
      expect(screen.getAllByRole('radio')[1]).toBeInTheDocument();
    });

    it('should render reason textarea', () => {
      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByRole('textbox')).toBeInTheDocument();
    });

    it('should render Create Request button', () => {
      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByRole('button', { name: /create request/i })).toBeInTheDocument();
    });

    it('should render Cancel button when onCancel is provided', () => {
      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
    });

    it('should render Reset button when onCancel is not provided', () => {
      render(<SwapRequestForm onSuccess={mockOnSuccess} />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByRole('button', { name: /reset/i })).toBeInTheDocument();
    });
  });

  describe('Week Selection', () => {
    it('should populate week options from available weeks', () => {
      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      const select = screen.getAllByRole('combobox')[0] as HTMLSelectElement;
      // Should have placeholder + available weeks
      expect(select.options.length).toBe(mockAvailableWeeks.length + 1);
    });

    it('should show conflict indicator for weeks with conflicts', () => {
      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      // Aug 1, 2025 has conflict in mock data - check for option with conflict indicator
      const select = screen.getAllByRole('combobox')[0] as HTMLSelectElement;
      const options = Array.from(select.options);
      const conflictOption = options.find(opt => opt.textContent?.includes('Has Conflict'));
      expect(conflictOption).toBeDefined();
    });

    it('should show message when no weeks are available', () => {
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

    it('should disable submit button when no weeks are available', () => {
      (hooks.useAvailableWeeks as jest.Mock).mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
      });

      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      const submitButton = screen.getByRole('button', { name: /create request/i });
      expect(submitButton).toBeDisabled();
    });
  });

  describe('Swap Mode Selection', () => {
    it('should have auto-find mode selected by default', () => {
      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      const autoRadio = screen.getAllByRole('radio')[0] as HTMLInputElement;
      expect(autoRadio).toBeChecked();
    });

    it('should not show target faculty field in auto mode', () => {
      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      expect(screen.queryByLabelText(/target faculty/i)).not.toBeInTheDocument();
    });

    it('should show target faculty field when specific mode is selected', async () => {
      const user = userEvent.setup();

      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      const specificRadio = screen.getAllByRole('radio')[1];
      await user.click(specificRadio);

      expect(screen.getAllByRole('combobox')[1]).toBeInTheDocument();
    });

    it('should switch between modes correctly', async () => {
      const user = userEvent.setup();

      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      // Switch to specific mode
      const specificRadio = screen.getAllByRole('radio')[1];
      await user.click(specificRadio);
      expect(screen.getAllByRole('combobox')[1]).toBeInTheDocument();

      // Switch back to auto mode
      const autoRadio = screen.getAllByRole('radio')[0];
      await user.click(autoRadio);
      expect(screen.queryByLabelText(/target faculty/i)).not.toBeInTheDocument();
    });
  });

  describe('Target Faculty Selection', () => {
    it('should populate faculty options in specific mode', async () => {
      const user = userEvent.setup();

      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      const specificRadio = screen.getAllByRole('radio')[1];
      await user.click(specificRadio);

      const facultySelect = screen.getAllByRole('combobox')[1] as HTMLSelectElement;
      // Should have placeholder + faculty members
      expect(facultySelect.options.length).toBe(mockFacultyMembers.length + 1);
    });

    it('should display all faculty members as options', async () => {
      const user = userEvent.setup();

      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      const specificRadio = screen.getAllByRole('radio')[1];
      await user.click(specificRadio);

      mockFacultyMembers.forEach((faculty) => {
        expect(screen.getByText(faculty.name)).toBeInTheDocument();
      });
    });
  });

  describe('Reason Text Area', () => {
    it('should allow typing in reason textarea', async () => {
      const user = userEvent.setup();

      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      const textarea = screen.getByRole('textbox');
      await user.type(textarea, 'Medical conference attendance');

      expect(textarea).toHaveValue('Medical conference attendance');
    });

    it('should show character count', () => {
      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('0/500 characters')).toBeInTheDocument();
    });

    it('should update character count when typing', async () => {
      const user = userEvent.setup();

      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      const textarea = screen.getByRole('textbox');
      await user.type(textarea, 'Test reason');

      expect(screen.getByText('11/500 characters')).toBeInTheDocument();
    });

    it('should enforce 500 character limit', () => {
      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      const textarea = screen.getByRole('textbox') as HTMLTextAreaElement;
      expect(textarea).toHaveAttribute('maxLength', '500');
    });
  });

  describe('Form Validation', () => {
    it('should show error when submitting without week selection', async () => {
      const user = userEvent.setup();

      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      const submitButton = screen.getByRole('button', { name: /create request/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/please select a week to offload/i)).toBeInTheDocument();
      });
    });

    it('should show error when specific mode is selected but no faculty is chosen', async () => {
      const user = userEvent.setup();

      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      // Select a week
      const weekSelect = screen.getAllByRole('combobox')[0];
      await user.selectOptions(weekSelect, mockAvailableWeeks[0].date);

      // Switch to specific mode without selecting faculty
      const specificRadio = screen.getAllByRole('radio')[1];
      await user.click(specificRadio);

      // Submit
      const submitButton = screen.getByRole('button', { name: /create request/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/please select a target faculty member/i)).toBeInTheDocument();
      });
    });

    it('should not show faculty error in auto mode', async () => {
      const user = userEvent.setup();

      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      // Select a week
      const weekSelect = screen.getAllByRole('combobox')[0];
      await user.selectOptions(weekSelect, mockAvailableWeeks[0].date);

      // Submit in auto mode
      const submitButton = screen.getByRole('button', { name: /create request/i });
      await user.click(submitButton);

      expect(
        screen.queryByText(/please select a target faculty member/i)
      ).not.toBeInTheDocument();
    });
  });

  describe('Form Submission', () => {
    it('should submit form with correct data in auto mode', async () => {
      const user = userEvent.setup();
      mockMutateAsync.mockResolvedValue(mockCreateSwapResponse);

      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      // Fill form
      const weekSelect = screen.getAllByRole('combobox')[0];
      await user.selectOptions(weekSelect, mockAvailableWeeks[0].date);

      const reasonTextarea = screen.getByRole('textbox');
      await user.type(reasonTextarea, 'Need to attend conference');

      // Submit
      const submitButton = screen.getByRole('button', { name: /create request/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith({
          weekToOffload: mockAvailableWeeks[0].date,
          reason: 'Need to attend conference',
          autoFindCandidates: true,
          preferredTargetFacultyId: undefined,
        });
      });
    });

    it('should submit form with correct data in specific mode', async () => {
      const user = userEvent.setup();
      mockMutateAsync.mockResolvedValue(mockCreateSwapResponse);

      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      // Fill form
      const weekSelect = screen.getAllByRole('combobox')[0];
      await user.selectOptions(weekSelect, mockAvailableWeeks[0].date);

      const specificRadio = screen.getAllByRole('radio')[1];
      await user.click(specificRadio);

      const facultySelect = screen.getAllByRole('combobox')[1];
      await user.selectOptions(facultySelect, mockFacultyMembers[0].id);

      const reasonTextarea = screen.getByRole('textbox');
      await user.type(reasonTextarea, 'Personal matter');

      // Submit
      const submitButton = screen.getByRole('button', { name: /create request/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith({
          weekToOffload: mockAvailableWeeks[0].date,
          reason: 'Personal matter',
          autoFindCandidates: false,
          preferredTargetFacultyId: mockFacultyMembers[0].id,
        });
      });
    });

    it('should call onSuccess after successful submission', async () => {
      const user = userEvent.setup();
      mockMutateAsync.mockResolvedValue(mockCreateSwapResponse);

      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      // Fill and submit form
      const weekSelect = screen.getAllByRole('combobox')[0];
      await user.selectOptions(weekSelect, mockAvailableWeeks[0].date);

      const submitButton = screen.getByRole('button', { name: /create request/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnSuccess).toHaveBeenCalled();
      });
    });

    it('should reset form after successful submission', async () => {
      const user = userEvent.setup();
      mockMutateAsync.mockResolvedValue(mockCreateSwapResponse);

      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      // Fill form
      const weekSelect = screen.getAllByRole('combobox')[0] as HTMLSelectElement;
      await user.selectOptions(weekSelect, mockAvailableWeeks[0].date);

      const reasonTextarea = screen.getByRole('textbox') as HTMLTextAreaElement;
      await user.type(reasonTextarea, 'Test reason');

      // Submit
      const submitButton = screen.getByRole('button', { name: /create request/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(weekSelect.value).toBe('');
        expect(reasonTextarea.value).toBe('');
      });
    });

    it('should show success message after submission', async () => {
      const user = userEvent.setup();
      mockMutateAsync.mockResolvedValue(mockCreateSwapResponse);

      (hooks.useCreateSwapRequest as jest.Mock).mockReturnValue({
        mutateAsync: mockMutateAsync,
        isPending: false,
        isSuccess: true,
        data: mockCreateSwapResponse,
        error: null,
      });

      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText(/swap request created successfully/i)).toBeInTheDocument();
      expect(screen.getByText(/5 candidate\(s\) notified/i)).toBeInTheDocument();
    });

    it('should show loading state during submission', () => {
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

      expect(screen.getByRole('button', { name: /creating\.\.\./i })).toBeInTheDocument();
    });

    it('should disable form fields during submission', () => {
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
      expect(screen.getByRole('textbox')).toBeDisabled();
    });

    it('should show error message on submission failure', async () => {
      const user = userEvent.setup();
      mockMutateAsync.mockRejectedValue(new Error('Network error'));

      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      // Fill and submit form
      const weekSelect = screen.getAllByRole('combobox')[0];
      await user.selectOptions(weekSelect, mockAvailableWeeks[0].date);

      const submitButton = screen.getByRole('button', { name: /create request/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/network error/i)).toBeInTheDocument();
      });
    });
  });

  describe('Cancel/Reset Functionality', () => {
    it('should call onCancel when Cancel button is clicked', async () => {
      const user = userEvent.setup();

      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      expect(mockOnCancel).toHaveBeenCalled();
    });

    it('should reset form when Reset button is clicked', async () => {
      const user = userEvent.setup();

      render(<SwapRequestForm onSuccess={mockOnSuccess} />, {
        wrapper: createWrapper(),
      });

      // Fill form
      const weekSelect = screen.getAllByRole('combobox')[0] as HTMLSelectElement;
      await user.selectOptions(weekSelect, mockAvailableWeeks[0].date);

      const reasonTextarea = screen.getByRole('textbox') as HTMLTextAreaElement;
      await user.type(reasonTextarea, 'Test reason');

      // Reset
      const resetButton = screen.getByRole('button', { name: /reset/i });
      await user.click(resetButton);

      expect(weekSelect.value).toBe('');
      expect(reasonTextarea.value).toBe('');
    });
  });

  describe('Help Section', () => {
    it('should render help section', () => {
      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('How it works:')).toBeInTheDocument();
    });

    it('should show helpful instructions', () => {
      render(<SwapRequestForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />, {
        wrapper: createWrapper(),
      });

      expect(
        screen.getByText(/select a week you are assigned to that you want to swap/i)
      ).toBeInTheDocument();
      expect(
        screen.getByText(/choose to auto-find candidates or request a specific faculty member/i)
      ).toBeInTheDocument();
    });
  });
});
