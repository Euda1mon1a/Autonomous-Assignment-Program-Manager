/**
 * Tests for ErrorAlert Component
 * Component: ErrorAlert - Error message display with retry/dismiss
 */

import React from 'react';
import { render, screen, fireEvent } from '@/test-utils';
import '@testing-library/jest-dom';
import { ErrorAlert } from '../ErrorAlert';

// Mock the getErrorMessage utility
jest.mock('@/lib/errors', () => ({
  getErrorMessage: jest.fn((error: unknown) => {
    if (typeof error === 'string') return error;
    if (error instanceof Error) return error.message;
    return 'An error occurred';
  }),
}));

describe('ErrorAlert', () => {
  // Test: Rendering
  describe('Rendering', () => {
    it('renders with string message', () => {
      render(<ErrorAlert message="Something went wrong" />);

      expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    });

    it('renders with error object', () => {
      const error = new Error('Network error');
      render(<ErrorAlert message={error} />);

      expect(screen.getByText('Network error')).toBeInTheDocument();
    });

    it('has proper role attribute', () => {
      render(<ErrorAlert message="Error" />);

      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    it('renders error icon', () => {
      const { container } = render(<ErrorAlert message="Error" />);

      const icon = container.querySelector('.text-red-600');
      expect(icon).toBeInTheDocument();
    });

    it('renders retry button when onRetry provided', () => {
      const onRetry = jest.fn();
      render(<ErrorAlert message="Error" onRetry={onRetry} />);

      expect(screen.getByLabelText('Retry')).toBeInTheDocument();
    });

    it('does not render retry button when onRetry not provided', () => {
      render(<ErrorAlert message="Error" />);

      expect(screen.queryByLabelText('Retry')).not.toBeInTheDocument();
    });

    it('renders dismiss button when onDismiss provided', () => {
      const onDismiss = jest.fn();
      render(<ErrorAlert message="Error" onDismiss={onDismiss} />);

      expect(screen.getByLabelText('Dismiss error')).toBeInTheDocument();
    });

    it('does not render dismiss button when onDismiss not provided', () => {
      render(<ErrorAlert message="Error" />);

      expect(screen.queryByLabelText('Dismiss error')).not.toBeInTheDocument();
    });
  });

  // Test: Interaction
  describe('Interaction', () => {
    it('calls onRetry when retry button clicked', () => {
      const onRetry = jest.fn();
      render(<ErrorAlert message="Error" onRetry={onRetry} />);

      fireEvent.click(screen.getByLabelText('Retry'));

      expect(onRetry).toHaveBeenCalledTimes(1);
    });

    it('calls onDismiss when dismiss button clicked', () => {
      const onDismiss = jest.fn();
      render(<ErrorAlert message="Error" onDismiss={onDismiss} />);

      fireEvent.click(screen.getByLabelText('Dismiss error'));

      expect(onDismiss).toHaveBeenCalledTimes(1);
    });

    it('retry button is keyboard accessible', () => {
      const onRetry = jest.fn();
      render(<ErrorAlert message="Error" onRetry={onRetry} />);

      const retryButton = screen.getByLabelText('Retry');
      retryButton.focus();

      expect(retryButton).toHaveFocus();
    });

    it('dismiss button is keyboard accessible', () => {
      const onDismiss = jest.fn();
      render(<ErrorAlert message="Error" onDismiss={onDismiss} />);

      const dismissButton = screen.getByLabelText('Dismiss error');
      dismissButton.focus();

      expect(dismissButton).toHaveFocus();
    });
  });

  // Test: Styling
  describe('Styling', () => {
    it('has error background color', () => {
      const { container } = render(<ErrorAlert message="Error" />);

      expect(container.querySelector('.bg-red-50')).toBeInTheDocument();
    });

    it('has error border', () => {
      const { container } = render(<ErrorAlert message="Error" />);

      expect(container.querySelector('.border-red-200')).toBeInTheDocument();
    });

    it('has rounded corners', () => {
      const { container } = render(<ErrorAlert message="Error" />);

      expect(container.querySelector('.rounded-lg')).toBeInTheDocument();
    });

    it('has proper padding', () => {
      const { container } = render(<ErrorAlert message="Error" />);

      expect(container.querySelector('.p-4')).toBeInTheDocument();
    });

    it('message has proper text color', () => {
      const { container } = render(<ErrorAlert message="Error message" />);

      const message = container.querySelector('.text-red-800');
      expect(message).toBeInTheDocument();
    });

    it('buttons have hover states', () => {
      const { container } = render(
        <ErrorAlert
          message="Error"
          onRetry={jest.fn()}
          onDismiss={jest.fn()}
        />
      );

      const buttons = container.querySelectorAll('.hover\\:bg-red-100');
      expect(buttons.length).toBeGreaterThan(0);
    });
  });

  // Test: Edge cases
  describe('Edge Cases', () => {
    it('handles long error messages', () => {
      const longMessage = 'This is a very long error message that should still display correctly in the error alert component without breaking the layout or causing overflow issues in the container.';

      render(<ErrorAlert message={longMessage} />);

      expect(screen.getByText(longMessage)).toBeInTheDocument();
    });

    it('handles both retry and dismiss buttons', () => {
      const onRetry = jest.fn();
      const onDismiss = jest.fn();

      render(
        <ErrorAlert
          message="Error"
          onRetry={onRetry}
          onDismiss={onDismiss}
        />
      );

      expect(screen.getByLabelText('Retry')).toBeInTheDocument();
      expect(screen.getByLabelText('Dismiss error')).toBeInTheDocument();
    });

    it('retry and dismiss buttons have proper gap', () => {
      const { container } = render(
        <ErrorAlert
          message="Error"
          onRetry={jest.fn()}
          onDismiss={jest.fn()}
        />
      );

      expect(container.querySelector('.gap-2')).toBeInTheDocument();
    });

    it('converts unknown error types to string', () => {
      const unknownError = { code: 500 };
      render(<ErrorAlert message={unknownError} />);

      expect(screen.getByText('An error occurred')).toBeInTheDocument();
    });

    it('renders icon with proper ARIA attributes', () => {
      const { container } = render(
        <ErrorAlert
          message="Error"
          onRetry={jest.fn()}
        />
      );

      const icons = container.querySelectorAll('[aria-hidden="true"]');
      expect(icons.length).toBeGreaterThan(0);
    });

    it('uses flexbox layout for proper alignment', () => {
      const { container } = render(<ErrorAlert message="Error" />);

      expect(container.querySelector('.flex.items-start')).toBeInTheDocument();
    });

    it('has proper spacing between icon and message', () => {
      const { container } = render(<ErrorAlert message="Error" />);

      expect(container.querySelector('.gap-3')).toBeInTheDocument();
    });

    it('icon is flex-shrink-0 to prevent squishing', () => {
      const { container } = render(<ErrorAlert message="Error" />);

      expect(container.querySelector('.flex-shrink-0')).toBeInTheDocument();
    });

    it('message area has flex-1 for proper space allocation', () => {
      const { container } = render(<ErrorAlert message="Error" />);

      expect(container.querySelector('.flex-1.min-w-0')).toBeInTheDocument();
    });
  });
});
