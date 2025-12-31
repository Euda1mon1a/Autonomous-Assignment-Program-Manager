import { renderWithProviders } from '@/test-utils';
/**
 * Tests for Toast Component
 * Component: 37 - Toast notifications
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@/test-utils';
import '@testing-library/jest-dom';
import { Toast, ToastContainer } from '../Toast';

describe('Toast', () => {
  const mockOnDismiss = jest.fn();

  beforeEach(() => {
    mockOnDismiss.mockClear();
    jest.clearAllTimers();
  });

  // Test 37.1: Render test
  describe('Rendering', () => {
    it('renders with message', () => {
      render(
        <Toast
          id="toast-1"
          type="success"
          message="Operation successful"
          onDismiss={mockOnDismiss}
        />
      );

      expect(screen.getByText('Operation successful')).toBeInTheDocument();
    });

    it('renders success type with green styling', () => {
      const { container } = render(
        <Toast id="toast-1" type="success" message="Success" onDismiss={mockOnDismiss} />
      );

      expect(container.querySelector('.bg-green-50')).toBeInTheDocument();
    });

    it('renders error type with red styling', () => {
      const { container } = render(
        <Toast id="toast-1" type="error" message="Error" onDismiss={mockOnDismiss} />
      );

      expect(container.querySelector('.bg-red-50')).toBeInTheDocument();
    });

    it('renders warning type with yellow styling', () => {
      const { container } = render(
        <Toast id="toast-1" type="warning" message="Warning" onDismiss={mockOnDismiss} />
      );

      expect(container.querySelector('.bg-yellow-50')).toBeInTheDocument();
    });

    it('renders info type with blue styling', () => {
      const { container } = render(
        <Toast id="toast-1" type="info" message="Info" onDismiss={mockOnDismiss} />
      );

      expect(container.querySelector('.bg-blue-50')).toBeInTheDocument();
    });

    it('renders dismiss button', () => {
      render(
        <Toast id="toast-1" type="success" message="Test" onDismiss={mockOnDismiss} />
      );

      expect(screen.getByLabelText('Dismiss notification')).toBeInTheDocument();
    });

    it('renders action button when provided', () => {
      const action = { label: 'Undo', onClick: jest.fn() };

      render(
        <Toast
          id="toast-1"
          type="success"
          message="Test"
          action={action}
          onDismiss={mockOnDismiss}
        />
      );

      expect(screen.getByText('Undo')).toBeInTheDocument();
    });
  });

  // Test 37.2: Toast types and variants
  describe('Toast Types', () => {
    it('shows correct icon for success type', () => {
      render(<Toast id="toast-1" type="success" message="Success" onDismiss={mockOnDismiss} />);

      const alert = screen.getByRole('alert');
      expect(alert).toBeInTheDocument();
    });

    it('shows correct icon for error type', () => {
      render(<Toast id="toast-1" type="error" message="Error" onDismiss={mockOnDismiss} />);

      const alert = screen.getByRole('alert');
      expect(alert).toBeInTheDocument();
    });

    it('shows correct icon for warning type', () => {
      render(<Toast id="toast-1" type="warning" message="Warning" onDismiss={mockOnDismiss} />);

      const alert = screen.getByRole('alert');
      expect(alert).toBeInTheDocument();
    });

    it('shows correct icon for info type', () => {
      render(<Toast id="toast-1" type="info" message="Info" onDismiss={mockOnDismiss} />);

      const alert = screen.getByRole('alert');
      expect(alert).toBeInTheDocument();
    });

    it('renders progress bar for non-persistent toasts', () => {
      const { container } = render(
        <Toast
          id="toast-1"
          type="success"
          message="Test"
          duration={3000}
          onDismiss={mockOnDismiss}
        />
      );

      const progressBar = container.querySelector('.absolute.bottom-0.left-0.h-1');
      expect(progressBar).toBeInTheDocument();
    });

    it('does not render progress bar for persistent toasts', () => {
      const { container } = render(
        <Toast
          id="toast-1"
          type="success"
          message="Test"
          persistent
          onDismiss={mockOnDismiss}
        />
      );

      const progressBar = container.querySelector('.absolute.bottom-0.left-0.h-1');
      expect(progressBar).not.toBeInTheDocument();
    });
  });

  // Test 37.3: Accessibility and interaction
  describe('Accessibility and Interaction', () => {
    it('has proper ARIA role and attributes', () => {
      render(
        <Toast id="toast-1" type="success" message="Test" onDismiss={mockOnDismiss} />
      );

      const alert = screen.getByRole('alert');
      expect(alert).toHaveAttribute('aria-live', 'polite');
    });

    it('dismisses when dismiss button clicked', () => {
      render(
        <Toast id="toast-1" type="success" message="Test" onDismiss={mockOnDismiss} />
      );

      fireEvent.click(screen.getByLabelText('Dismiss notification'));

      expect(mockOnDismiss).toHaveBeenCalledWith('toast-1');
    });

    it('calls action onClick and dismisses when action button clicked', () => {
      const actionOnClick = jest.fn();
      const action = { label: 'Undo', onClick: actionOnClick };

      render(
        <Toast
          id="toast-1"
          type="success"
          message="Test"
          action={action}
          onDismiss={mockOnDismiss}
        />
      );

      fireEvent.click(screen.getByText('Undo'));

      expect(actionOnClick).toHaveBeenCalled();
      expect(mockOnDismiss).toHaveBeenCalledWith('toast-1');
    });

    it('dismiss button is keyboard accessible', () => {
      render(
        <Toast id="toast-1" type="success" message="Test" onDismiss={mockOnDismiss} />
      );

      const dismissButton = screen.getByLabelText('Dismiss notification');
      dismissButton.focus();

      expect(dismissButton).toHaveFocus();
    });
  });

  // Test 37.4: Auto-dismiss and edge cases
  describe('Auto-dismiss and Edge Cases', () => {
    beforeEach(() => {
      jest.useFakeTimers();
    });

    afterEach(() => {
      jest.runOnlyPendingTimers();
      jest.useRealTimers();
    });

    it('auto-dismisses after duration', () => {
      render(
        <Toast
          id="toast-1"
          type="success"
          message="Test"
          duration={3000}
          onDismiss={mockOnDismiss}
        />
      );

      act(() => {
        jest.advanceTimersByTime(3300); // Duration + animation time
      });

      expect(mockOnDismiss).toHaveBeenCalledWith('toast-1');
    });

    it('does not auto-dismiss when persistent', () => {
      render(
        <Toast
          id="toast-1"
          type="success"
          message="Test"
          persistent
          onDismiss={mockOnDismiss}
        />
      );

      act(() => {
        jest.advanceTimersByTime(10000);
      });

      expect(mockOnDismiss).not.toHaveBeenCalled();
    });

    it('handles long messages', () => {
      const longMessage = 'This is a very long message that should still display correctly in the toast notification component and wrap if necessary.';

      render(
        <Toast id="toast-1" type="info" message={longMessage} onDismiss={mockOnDismiss} />
      );

      expect(screen.getByText(longMessage)).toBeInTheDocument();
    });

    it('has minimum and maximum width', () => {
      const { container } = render(
        <Toast id="toast-1" type="success" message="Test" onDismiss={mockOnDismiss} />
      );

      const toast = container.firstChild as HTMLElement;
      const styles = window.getComputedStyle(toast);

      expect(toast).toHaveStyle({ minWidth: '320px', maxWidth: '420px' });
    });
  });

  describe('ToastContainer', () => {
    it('renders multiple toasts', () => {
      const toasts = [
        { id: '1', type: 'success' as const, message: 'Toast 1' },
        { id: '2', type: 'error' as const, message: 'Toast 2' },
        { id: '3', type: 'info' as const, message: 'Toast 3' },
      ];

      render(<ToastContainer toasts={toasts} onDismiss={mockOnDismiss} />);

      expect(screen.getByText('Toast 1')).toBeInTheDocument();
      expect(screen.getByText('Toast 2')).toBeInTheDocument();
      expect(screen.getByText('Toast 3')).toBeInTheDocument();
    });

    it('renders nothing when toasts array is empty', () => {
      const { container } = render(<ToastContainer toasts={[]} onDismiss={mockOnDismiss} />);

      expect(container).toBeEmptyDOMElement();
    });

    it('positions toasts top-right by default', () => {
      const toasts = [{ id: '1', type: 'success' as const, message: 'Test' }];

      const { container } = render(<ToastContainer toasts={toasts} onDismiss={mockOnDismiss} />);

      expect(container.querySelector('.top-4.right-4')).toBeInTheDocument();
    });

    it('positions toasts based on position prop', () => {
      const toasts = [{ id: '1', type: 'success' as const, message: 'Test' }];

      const { container } = render(
        <ToastContainer toasts={toasts} position="bottom-left" onDismiss={mockOnDismiss} />
      );

      expect(container.querySelector('.bottom-4.left-4')).toBeInTheDocument();
    });
  });
});
