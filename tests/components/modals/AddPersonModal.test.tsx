import React from 'react';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { AddPersonModal } from '@/components/AddPersonModal';
import { useCreatePerson } from '@/lib/hooks';

// Mock the hooks
jest.mock('@/lib/hooks', () => ({
  useCreatePerson: jest.fn(),
}));

const mockUseCreatePerson = useCreatePerson as jest.MockedFunction<typeof useCreatePerson>;

describe('AddPersonModal', () => {
  const mockOnClose = jest.fn();
  const mockMutateAsync = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseCreatePerson.mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: false,
      isError: false,
      isSuccess: false,
      error: null,
      data: undefined,
      mutate: jest.fn(),
      reset: jest.fn(),
      status: 'idle',
      variables: undefined,
      context: undefined,
      failureCount: 0,
      failureReason: null,
      isPaused: false,
      submittedAt: 0,
    } as any);
  });

  describe('Rendering', () => {
    it('should not render when isOpen is false', () => {
      render(<AddPersonModal isOpen={false} onClose={mockOnClose} />);

      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
      expect(screen.queryByText('Add Person')).not.toBeInTheDocument();
    });

    it('should render modal when isOpen is true', () => {
      render(<AddPersonModal isOpen={true} onClose={mockOnClose} />);

      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText('Add Person')).toBeInTheDocument();
    });

    it('should display all form fields correctly', () => {
      render(<AddPersonModal isOpen={true} onClose={mockOnClose} />);

      // Check for all form fields
      expect(screen.getByLabelText(/name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/type/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/pgy level/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/performs procedures/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/specialties/i)).toBeInTheDocument();
    });

    it('should display action buttons', () => {
      render(<AddPersonModal isOpen={true} onClose={mockOnClose} />);

      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /add person/i })).toBeInTheDocument();
    });

    it('should show PGY level field when type is resident', () => {
      render(<AddPersonModal isOpen={true} onClose={mockOnClose} />);

      expect(screen.getByLabelText(/pgy level/i)).toBeInTheDocument();
    });

    it('should hide PGY level field when type is faculty', async () => {
      const user = userEvent.setup();
      render(<AddPersonModal isOpen={true} onClose={mockOnClose} />);

      const typeSelect = screen.getByLabelText(/type/i);
      await user.selectOptions(typeSelect, 'faculty');

      expect(screen.queryByLabelText(/pgy level/i)).not.toBeInTheDocument();
    });
  });

  describe('Form Validation', () => {
    it('should show error when name is empty', async () => {
      const user = userEvent.setup();
      render(<AddPersonModal isOpen={true} onClose={mockOnClose} />);

      const submitButton = screen.getByRole('button', { name: /add person/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/name is required/i)).toBeInTheDocument();
      });
      expect(mockMutateAsync).not.toHaveBeenCalled();
    });

    it('should show error when name is less than 2 characters', async () => {
      const user = userEvent.setup();
      render(<AddPersonModal isOpen={true} onClose={mockOnClose} />);

      const nameInput = screen.getByLabelText(/name/i);
      await user.type(nameInput, 'A');

      const submitButton = screen.getByRole('button', { name: /add person/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/name must be at least 2 characters/i)).toBeInTheDocument();
      });
      expect(mockMutateAsync).not.toHaveBeenCalled();
    });

    it('should show error for invalid email format', async () => {
      const user = userEvent.setup();
      render(<AddPersonModal isOpen={true} onClose={mockOnClose} />);

      const nameInput = screen.getByLabelText(/name/i);
      await user.type(nameInput, 'John Doe');

      const emailInput = screen.getByLabelText(/email/i);
      await user.type(emailInput, 'invalid-email');

      const submitButton = screen.getByRole('button', { name: /add person/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/invalid email/i)).toBeInTheDocument();
      });
      expect(mockMutateAsync).not.toHaveBeenCalled();
    });

    it('should validate PGY level for residents', async () => {
      const user = userEvent.setup();
      render(<AddPersonModal isOpen={true} onClose={mockOnClose} />);

      const nameInput = screen.getByLabelText(/name/i);
      await user.type(nameInput, 'John Doe');

      // PGY level should default to 1, which is valid
      const submitButton = screen.getByRole('button', { name: /add person/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalled();
      });
    });

    it('should allow valid email format', async () => {
      const user = userEvent.setup();
      mockMutateAsync.mockResolvedValueOnce({} as any);

      render(<AddPersonModal isOpen={true} onClose={mockOnClose} />);

      const nameInput = screen.getByLabelText(/name/i);
      await user.type(nameInput, 'John Doe');

      const emailInput = screen.getByLabelText(/email/i);
      await user.type(emailInput, 'john@example.com');

      const submitButton = screen.getByRole('button', { name: /add person/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith(
          expect.objectContaining({
            name: 'John Doe',
            email: 'john@example.com',
          })
        );
      });
    });

    it('should allow submission without email (optional field)', async () => {
      const user = userEvent.setup();
      mockMutateAsync.mockResolvedValueOnce({} as any);

      render(<AddPersonModal isOpen={true} onClose={mockOnClose} />);

      const nameInput = screen.getByLabelText(/name/i);
      await user.type(nameInput, 'John Doe');

      const submitButton = screen.getByRole('button', { name: /add person/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith(
          expect.not.objectContaining({
            email: expect.anything(),
          })
        );
      });
    });
  });

  describe('Form Submission', () => {
    it('should submit form with valid resident data', async () => {
      const user = userEvent.setup();
      mockMutateAsync.mockResolvedValueOnce({} as any);

      render(<AddPersonModal isOpen={true} onClose={mockOnClose} />);

      await user.type(screen.getByLabelText(/name/i), 'John Doe');
      await user.type(screen.getByLabelText(/email/i), 'john@example.com');
      await user.selectOptions(screen.getByLabelText(/type/i), 'resident');
      await user.selectOptions(screen.getByLabelText(/pgy level/i), '3');
      await user.click(screen.getByLabelText(/performs procedures/i));
      await user.type(screen.getByLabelText(/specialties/i), 'Cardiology, Surgery');

      await user.click(screen.getByRole('button', { name: /add person/i }));

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith({
          name: 'John Doe',
          email: 'john@example.com',
          type: 'resident',
          pgy_level: 3,
          performs_procedures: true,
          specialties: ['Cardiology', 'Surgery'],
        });
      });
    });

    it('should submit form with valid faculty data', async () => {
      const user = userEvent.setup();
      mockMutateAsync.mockResolvedValueOnce({} as any);

      render(<AddPersonModal isOpen={true} onClose={mockOnClose} />);

      await user.type(screen.getByLabelText(/name/i), 'Dr. Smith');
      await user.selectOptions(screen.getByLabelText(/type/i), 'faculty');

      await user.click(screen.getByRole('button', { name: /add person/i }));

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith({
          name: 'Dr. Smith',
          type: 'faculty',
          performs_procedures: false,
        });
      });
    });

    it('should close modal after successful submission', async () => {
      const user = userEvent.setup();
      mockMutateAsync.mockResolvedValueOnce({} as any);

      render(<AddPersonModal isOpen={true} onClose={mockOnClose} />);

      await user.type(screen.getByLabelText(/name/i), 'John Doe');
      await user.click(screen.getByRole('button', { name: /add person/i }));

      await waitFor(() => {
        expect(mockOnClose).toHaveBeenCalled();
      });
    });

    it('should display error message when submission fails', async () => {
      const user = userEvent.setup();
      mockMutateAsync.mockRejectedValueOnce(new Error('Network error'));

      render(<AddPersonModal isOpen={true} onClose={mockOnClose} />);

      await user.type(screen.getByLabelText(/name/i), 'John Doe');
      await user.click(screen.getByRole('button', { name: /add person/i }));

      await waitFor(() => {
        expect(screen.getByText(/failed to create person/i)).toBeInTheDocument();
      });
      expect(mockOnClose).not.toHaveBeenCalled();
    });

    it('should disable submit button while submitting', async () => {
      const user = userEvent.setup();
      mockUseCreatePerson.mockReturnValue({
        mutateAsync: mockMutateAsync,
        isPending: true,
        isError: false,
        isSuccess: false,
        error: null,
        data: undefined,
        mutate: jest.fn(),
        reset: jest.fn(),
        status: 'pending',
        variables: undefined,
        context: undefined,
        failureCount: 0,
        failureReason: null,
        isPaused: false,
        submittedAt: Date.now(),
      } as any);

      render(<AddPersonModal isOpen={true} onClose={mockOnClose} />);

      const submitButton = screen.getByRole('button', { name: /creating/i });
      expect(submitButton).toBeDisabled();
    });

    it('should trim whitespace from name and email', async () => {
      const user = userEvent.setup();
      mockMutateAsync.mockResolvedValueOnce({} as any);

      render(<AddPersonModal isOpen={true} onClose={mockOnClose} />);

      await user.type(screen.getByLabelText(/name/i), '  John Doe  ');
      await user.type(screen.getByLabelText(/email/i), '  john@example.com  ');

      await user.click(screen.getByRole('button', { name: /add person/i }));

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith(
          expect.objectContaining({
            name: 'John Doe',
            email: 'john@example.com',
          })
        );
      });
    });

    it('should parse and filter specialties correctly', async () => {
      const user = userEvent.setup();
      mockMutateAsync.mockResolvedValueOnce({} as any);

      render(<AddPersonModal isOpen={true} onClose={mockOnClose} />);

      await user.type(screen.getByLabelText(/name/i), 'John Doe');
      await user.type(screen.getByLabelText(/specialties/i), 'Cardiology,  Surgery, , Neurology  ');

      await user.click(screen.getByRole('button', { name: /add person/i }));

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith(
          expect.objectContaining({
            specialties: ['Cardiology', 'Surgery', 'Neurology'],
          })
        );
      });
    });
  });

  describe('Cancel and Close', () => {
    it('should close modal when cancel button is clicked', async () => {
      const user = userEvent.setup();
      render(<AddPersonModal isOpen={true} onClose={mockOnClose} />);

      await user.click(screen.getByRole('button', { name: /cancel/i }));

      expect(mockOnClose).toHaveBeenCalled();
    });

    it('should reset form when modal closes', async () => {
      const user = userEvent.setup();
      const { rerender } = render(<AddPersonModal isOpen={true} onClose={mockOnClose} />);

      // Fill out form
      await user.type(screen.getByLabelText(/name/i), 'John Doe');
      await user.type(screen.getByLabelText(/email/i), 'john@example.com');
      await user.click(screen.getByLabelText(/performs procedures/i));

      // Close modal
      await user.click(screen.getByRole('button', { name: /cancel/i }));

      // Reopen modal
      rerender(<AddPersonModal isOpen={false} onClose={mockOnClose} />);
      rerender(<AddPersonModal isOpen={true} onClose={mockOnClose} />);

      // Form should be reset
      expect(screen.getByLabelText(/name/i)).toHaveValue('');
      expect(screen.getByLabelText(/email/i)).toHaveValue('');
      expect(screen.getByLabelText(/performs procedures/i)).not.toBeChecked();
    });

    it('should clear errors when modal closes', async () => {
      const user = userEvent.setup();
      const { rerender } = render(<AddPersonModal isOpen={true} onClose={mockOnClose} />);

      // Trigger validation error
      await user.click(screen.getByRole('button', { name: /add person/i }));
      await waitFor(() => {
        expect(screen.getByText(/name is required/i)).toBeInTheDocument();
      });

      // Close modal
      await user.click(screen.getByRole('button', { name: /cancel/i }));

      // Reopen modal
      rerender(<AddPersonModal isOpen={false} onClose={mockOnClose} />);
      rerender(<AddPersonModal isOpen={true} onClose={mockOnClose} />);

      // Error should be cleared
      expect(screen.queryByText(/name is required/i)).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA attributes on modal', () => {
      render(<AddPersonModal isOpen={true} onClose={mockOnClose} />);

      const modal = screen.getByRole('dialog');
      expect(modal).toHaveAttribute('aria-modal', 'true');
      expect(modal).toHaveAttribute('aria-labelledby');
    });

    it('should mark required fields appropriately', () => {
      render(<AddPersonModal isOpen={true} onClose={mockOnClose} />);

      const nameInput = screen.getByLabelText(/name/i);
      expect(nameInput).toBeRequired();
    });

    it('should associate error messages with inputs', async () => {
      const user = userEvent.setup();
      render(<AddPersonModal isOpen={true} onClose={mockOnClose} />);

      await user.click(screen.getByRole('button', { name: /add person/i }));

      await waitFor(() => {
        const nameInput = screen.getByLabelText(/name/i);
        expect(nameInput).toHaveAttribute('aria-invalid', 'true');
        expect(nameInput).toHaveAttribute('aria-describedby');

        const errorId = nameInput.getAttribute('aria-describedby');
        const errorMessage = document.getElementById(errorId!);
        expect(errorMessage).toHaveTextContent(/name is required/i);
        expect(errorMessage).toHaveAttribute('role', 'alert');
      });
    });

    it('should have accessible labels for all form controls', () => {
      render(<AddPersonModal isOpen={true} onClose={mockOnClose} />);

      expect(screen.getByLabelText(/name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/type/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/pgy level/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/performs procedures/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/specialties/i)).toBeInTheDocument();
    });

    it('should support keyboard navigation', async () => {
      const user = userEvent.setup();
      render(<AddPersonModal isOpen={true} onClose={mockOnClose} />);

      const nameInput = screen.getByLabelText(/name/i);
      const emailInput = screen.getByLabelText(/email/i);

      // Tab through form fields
      nameInput.focus();
      expect(document.activeElement).toBe(nameInput);

      await user.tab();
      expect(document.activeElement).toBe(emailInput);
    });

    it('should handle Enter key to submit form', async () => {
      const user = userEvent.setup();
      mockMutateAsync.mockResolvedValueOnce({} as any);

      render(<AddPersonModal isOpen={true} onClose={mockOnClose} />);

      const nameInput = screen.getByLabelText(/name/i);
      await user.type(nameInput, 'John Doe{Enter}');

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalled();
      });
    });

    it('should display general error with proper styling and role', async () => {
      const user = userEvent.setup();
      mockMutateAsync.mockRejectedValueOnce(new Error('Server error'));

      render(<AddPersonModal isOpen={true} onClose={mockOnClose} />);

      await user.type(screen.getByLabelText(/name/i), 'John Doe');
      await user.click(screen.getByRole('button', { name: /add person/i }));

      await waitFor(() => {
        const errorDiv = screen.getByText(/failed to create person/i).closest('div');
        expect(errorDiv).toHaveClass('bg-red-50', 'border-red-200', 'text-red-700');
      });
    });
  });

  describe('Type-specific behavior', () => {
    it('should include PGY level only for residents', async () => {
      const user = userEvent.setup();
      mockMutateAsync.mockResolvedValueOnce({} as any);

      render(<AddPersonModal isOpen={true} onClose={mockOnClose} />);

      await user.type(screen.getByLabelText(/name/i), 'John Doe');
      await user.selectOptions(screen.getByLabelText(/type/i), 'resident');
      await user.selectOptions(screen.getByLabelText(/pgy level/i), '2');

      await user.click(screen.getByRole('button', { name: /add person/i }));

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith(
          expect.objectContaining({
            type: 'resident',
            pgy_level: 2,
          })
        );
      });
    });

    it('should not include PGY level for faculty', async () => {
      const user = userEvent.setup();
      mockMutateAsync.mockResolvedValueOnce({} as any);

      render(<AddPersonModal isOpen={true} onClose={mockOnClose} />);

      await user.type(screen.getByLabelText(/name/i), 'Dr. Smith');
      await user.selectOptions(screen.getByLabelText(/type/i), 'faculty');

      await user.click(screen.getByRole('button', { name: /add person/i }));

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith(
          expect.not.objectContaining({
            pgy_level: expect.anything(),
          })
        );
      });
    });

    it('should show all PGY level options (1-8)', async () => {
      const user = userEvent.setup();
      render(<AddPersonModal isOpen={true} onClose={mockOnClose} />);

      const pgySelect = screen.getByLabelText(/pgy level/i);
      const options = within(pgySelect).getAllByRole('option');

      expect(options).toHaveLength(8);
      expect(options[0]).toHaveValue('1');
      expect(options[7]).toHaveValue('8');
    });
  });
});
