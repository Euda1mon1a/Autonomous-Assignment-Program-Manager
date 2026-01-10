/**
 * @jest-environment jsdom
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { QuickSwapButton, QuickSwapLink } from '../QuickSwapButton';

// Mock the API
jest.mock('@/lib/api', () => ({
  post: jest.fn(),
}));

// Mock Auth Context
jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(() => ({ user: { id: '1', email: 'test@example.com' } })),
}));

import { post } from '@/lib/api';

const mockPost = post as jest.MockedFunction<typeof post>;

describe('QuickSwapButton', () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });

  const defaultProps = {
    assignmentId: 'assignment-123',
    date: '2024-01-15',
    timeOfDay: 'AM' as const,
    activity: 'clinic',
  };

  beforeEach(() => {
    jest.clearAllMocks();
    queryClient.clear();
  });

  const renderComponent = (props = {}) => {
    return render(
      <QueryClientProvider client={queryClient}>
        <QuickSwapButton {...defaultProps} {...props} />
      </QueryClientProvider>
    );
  };

  describe('button rendering', () => {
    it('renders swap button', () => {
      renderComponent();

      expect(screen.getByRole('button', { name: /Request swap/i })).toBeInTheDocument();
    });

    it('renders small size by default', () => {
      const { container } = renderComponent();

      const button = screen.getByRole('button');
      expect(button).toHaveClass('p-1.5', 'text-xs');
    });

    it('renders medium size when specified', () => {
      const { container } = renderComponent({ size: 'md' });

      const button = screen.getByRole('button');
      expect(button).toHaveClass('p-2', 'text-sm');
      expect(screen.getByText('Swap')).toBeInTheDocument();
    });

    it('applies custom className', () => {
      renderComponent({ className: 'custom-class' });

      const button = screen.getByRole('button');
      expect(button).toHaveClass('custom-class');
    });
  });

  describe('modal interaction', () => {
    it('opens modal when button clicked', () => {
      renderComponent();

      const button = screen.getByRole('button');
      fireEvent.click(button);

      expect(screen.getByText('Request Swap')).toBeInTheDocument();
      expect(screen.getByText('Find someone to cover this shift')).toBeInTheDocument();
    });

    it('prevents event propagation when opening', () => {
      const mockHandler = jest.fn();

      const { container } = render(
        <QueryClientProvider client={queryClient}>
          <div onClick={mockHandler}>
            <QuickSwapButton {...defaultProps} />
          </div>
        </QueryClientProvider>
      );

      const button = screen.getByRole('button');
      fireEvent.click(button);

      expect(mockHandler).not.toHaveBeenCalled();
    });

    it('closes modal when X button clicked', () => {
      renderComponent();

      fireEvent.click(screen.getByRole('button'));

      const closeButton = screen.getByLabelText('Close');
      fireEvent.click(closeButton);

      expect(screen.queryByText('Request Swap')).not.toBeInTheDocument();
    });

    it('closes modal when backdrop clicked', () => {
      renderComponent();

      fireEvent.click(screen.getByRole('button'));

      const backdrop = document.querySelector('.fixed.inset-0');
      fireEvent.click(backdrop!);

      expect(screen.queryByText('Request Swap')).not.toBeInTheDocument();
    });

    it('calls onClose callback when modal closes', () => {
      const mockOnClose = jest.fn();
      renderComponent({ onClose: mockOnClose });

      fireEvent.click(screen.getByRole('button'));
      fireEvent.click(screen.getByLabelText('Close'));

      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  describe('assignment details display', () => {
    it('displays formatted date', () => {
      renderComponent();

      fireEvent.click(screen.getByRole('button'));

      expect(screen.getByText(/Mon, Jan 15, 2024/)).toBeInTheDocument();
    });

    it('displays time of day', () => {
      renderComponent({ timeOfDay: 'PM' });

      fireEvent.click(screen.getByRole('button'));

      expect(screen.getByText('PM')).toBeInTheDocument();
    });

    it('displays activity type', () => {
      renderComponent({ activity: 'inpatient' });

      fireEvent.click(screen.getByRole('button'));

      expect(screen.getByText('inpatient')).toBeInTheDocument();
    });
  });

  describe('form interaction', () => {
    it('allows entering reason text', () => {
      renderComponent();

      fireEvent.click(screen.getByRole('button'));

      const textarea = screen.getByPlaceholderText(/e.g., Family commitment/);
      fireEvent.change(textarea, { target: { value: 'Family emergency' } });

      expect(textarea).toHaveValue('Family emergency');
    });

    it('submits form with reason', async () => {
      mockPost.mockResolvedValueOnce({ success: true });

      renderComponent();

      fireEvent.click(screen.getByRole('button'));

      const textarea = screen.getByPlaceholderText(/e.g., Family commitment/);
      fireEvent.change(textarea, { target: { value: 'Family emergency' } });

      const submitButton = screen.getByRole('button', { name: /Submit Request/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockPost).toHaveBeenCalledWith('/swaps/request', {
          assignmentId: 'assignment-123',
          reason: 'Family emergency',
        });
      });
    });

    it('submits without reason if not provided', async () => {
      mockPost.mockResolvedValueOnce({ success: true });

      renderComponent();

      fireEvent.click(screen.getByRole('button'));

      const submitButton = screen.getByRole('button', { name: /Submit Request/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockPost).toHaveBeenCalledWith('/swaps/request', {
          assignmentId: 'assignment-123',
          reason: undefined,
        });
      });
    });
  });

  describe('submission states', () => {
    it('shows loading state while submitting', async () => {
      mockPost.mockImplementation(() => new Promise((resolve) => setTimeout(resolve, 100)));

      renderComponent();

      fireEvent.click(screen.getByRole('button'));

      const submitButton = screen.getByRole('button', { name: /Submit Request/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Submitting...')).toBeInTheDocument();
      });
    });

    it('shows success message after submission', async () => {
      mockPost.mockResolvedValueOnce({ success: true });

      renderComponent();

      fireEvent.click(screen.getByRole('button'));

      const submitButton = screen.getByRole('button', { name: /Submit Request/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Swap request submitted successfully!')).toBeInTheDocument();
      });
    });

    it('shows error message on failure', async () => {
      mockPost.mockRejectedValueOnce(new Error('Failed'));

      renderComponent();

      fireEvent.click(screen.getByRole('button'));

      const submitButton = screen.getByRole('button', { name: /Submit Request/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Failed to submit swap request. Please try again.')).toBeInTheDocument();
      });
    });

    it('disables submit button while loading', async () => {
      mockPost.mockImplementation(() => new Promise((resolve) => setTimeout(resolve, 100)));

      renderComponent();

      fireEvent.click(screen.getByRole('button'));

      const submitButton = screen.getByRole('button', { name: /Submit Request/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(submitButton).toBeDisabled();
      });
    });

    it('disables submit button after success', async () => {
      mockPost.mockResolvedValueOnce({ success: true });

      renderComponent();

      fireEvent.click(screen.getByRole('button'));

      const submitButton = screen.getByRole('button', { name: /Submit Request/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(submitButton).toBeDisabled();
      });
    });
  });

  describe('callbacks', () => {
    it('calls onSuccess after successful submission', async () => {
      mockPost.mockResolvedValueOnce({ success: true });
      const mockOnSuccess = jest.fn();

      renderComponent({ onSuccess: mockOnSuccess });

      fireEvent.click(screen.getByRole('button'));

      const submitButton = screen.getByRole('button', { name: /Submit Request/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockOnSuccess).toHaveBeenCalled();
      });
    });

    it('closes modal after successful submission', async () => {
      mockPost.mockResolvedValueOnce({ success: true });

      renderComponent();

      fireEvent.click(screen.getByRole('button'));

      const submitButton = screen.getByRole('button', { name: /Submit Request/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.queryByText('Request Swap')).not.toBeInTheDocument();
      });
    });

    it('clears reason field after successful submission', async () => {
      mockPost.mockResolvedValueOnce({ success: true });

      renderComponent();

      fireEvent.click(screen.getByRole('button'));

      const textarea = screen.getByPlaceholderText(/e.g., Family commitment/);
      fireEvent.change(textarea, { target: { value: 'Test reason' } });

      const submitButton = screen.getByRole('button', { name: /Submit Request/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.queryByText('Request Swap')).not.toBeInTheDocument();
      });

      // Reopen modal
      fireEvent.click(screen.getByRole('button'));

      const newTextarea = screen.getByPlaceholderText(/e.g., Family commitment/);
      expect(newTextarea).toHaveValue('');
    });
  });

  describe('query invalidation', () => {
    it('invalidates swap requests query after success', async () => {
      mockPost.mockResolvedValueOnce({ success: true });
      const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries');

      renderComponent();

      fireEvent.click(screen.getByRole('button'));

      const submitButton = screen.getByRole('button', { name: /Submit Request/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['swap-requests'] });
      });
    });

    it('invalidates assignments query after success', async () => {
      mockPost.mockResolvedValueOnce({ success: true });
      const invalidateSpy = jest.spyOn(queryClient, 'invalidateQueries');

      renderComponent();

      fireEvent.click(screen.getByRole('button'));

      const submitButton = screen.getByRole('button', { name: /Submit Request/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['assignments'] });
      });
    });
  });
});

describe('QuickSwapLink', () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });

  const defaultProps = {
    assignmentId: 'assignment-123',
    date: '2024-01-15',
    timeOfDay: 'AM' as const,
    activity: 'clinic',
  };

  const renderComponent = (props = {}) => {
    return render(
      <QueryClientProvider client={queryClient}>
        <QuickSwapLink {...defaultProps} {...props} />
      </QueryClientProvider>
    );
  };

  it('renders as a text link', () => {
    renderComponent();

    const link = screen.getByRole('button', { name: /Request Swap/i });
    expect(link).toHaveClass('text-blue-600');
  });

  it('shows swap icon', () => {
    const { container } = renderComponent();

    const icon = container.querySelector('.lucide-arrow-left-right');
    expect(icon).toBeInTheDocument();
  });
});
