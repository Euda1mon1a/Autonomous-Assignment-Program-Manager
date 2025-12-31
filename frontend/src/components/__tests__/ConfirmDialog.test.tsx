/**
 * Tests for ConfirmDialog Component
 * Component: ConfirmDialog - Confirmation dialogs
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@/test-utils';
import '@testing-library/jest-dom';
import { ConfirmDialog } from '../ConfirmDialog';

describe('ConfirmDialog', () => {
  const defaultProps = {
    isOpen: true,
    onClose: jest.fn(),
    onConfirm: jest.fn(),
    title: 'Confirm Action',
    message: 'Are you sure you want to proceed?',
  };

  beforeEach(() => {
    jest.clearAllMocks();
    document.body.style.overflow = 'unset';
  });

  // Test: Rendering
  describe('Rendering', () => {
    it('renders when isOpen is true', () => {
      render(<ConfirmDialog {...defaultProps} />);

      expect(screen.getByText('Confirm Action')).toBeInTheDocument();
      expect(screen.getByText('Are you sure you want to proceed?')).toBeInTheDocument();
    });

    it('does not render when isOpen is false', () => {
      render(<ConfirmDialog {...defaultProps} isOpen={false} />);

      expect(screen.queryByText('Confirm Action')).not.toBeInTheDocument();
    });

    it('has proper dialog role', () => {
      render(<ConfirmDialog {...defaultProps} />);

      const dialog = screen.getByRole('alertdialog');
      expect(dialog).toHaveAttribute('aria-modal', 'true');
    });

    it('renders close button', () => {
      render(<ConfirmDialog {...defaultProps} />);

      expect(screen.getByLabelText('Close')).toBeInTheDocument();
    });

    it('renders cancel button with default label', () => {
      render(<ConfirmDialog {...defaultProps} />);

      expect(screen.getByText('Cancel')).toBeInTheDocument();
    });

    it('renders confirm button with default label', () => {
      render(<ConfirmDialog {...defaultProps} />);

      expect(screen.getByText('Confirm')).toBeInTheDocument();
    });

    it('renders custom cancel label', () => {
      render(<ConfirmDialog {...defaultProps} cancelLabel="No" />);

      expect(screen.getByText('No')).toBeInTheDocument();
    });

    it('renders custom confirm label', () => {
      render(<ConfirmDialog {...defaultProps} confirmLabel="Yes" />);

      expect(screen.getByText('Yes')).toBeInTheDocument();
    });

    it('renders backdrop', () => {
      const { container } = render(<ConfirmDialog {...defaultProps} />);

      expect(container.querySelector('.bg-black\\/50')).toBeInTheDocument();
    });
  });

  // Test: Variants
  describe('Variants', () => {
    it('renders danger variant with red styling', () => {
      const { container } = render(<ConfirmDialog {...defaultProps} variant="danger" />);

      expect(container.querySelector('.bg-red-600')).toBeInTheDocument();
    });

    it('renders warning variant with amber styling', () => {
      const { container } = render(<ConfirmDialog {...defaultProps} variant="warning" />);

      expect(container.querySelector('.bg-amber-600')).toBeInTheDocument();
    });

    it('renders default variant with blue styling', () => {
      const { container } = render(<ConfirmDialog {...defaultProps} variant="default" />);

      expect(container.querySelector('.bg-blue-600')).toBeInTheDocument();
    });

    it('shows trash icon for danger variant', () => {
      render(<ConfirmDialog {...defaultProps} variant="danger" />);

      const dialog = screen.getByRole('alertdialog');
      expect(dialog).toBeInTheDocument();
    });

    it('shows warning icon for warning variant', () => {
      render(<ConfirmDialog {...defaultProps} variant="warning" />);

      const dialog = screen.getByRole('alertdialog');
      expect(dialog).toBeInTheDocument();
    });
  });

  // Test: Interaction
  describe('Interaction', () => {
    it('calls onClose when close button clicked', () => {
      render(<ConfirmDialog {...defaultProps} />);

      fireEvent.click(screen.getByLabelText('Close'));

      expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
    });

    it('calls onClose when cancel button clicked', () => {
      render(<ConfirmDialog {...defaultProps} />);

      fireEvent.click(screen.getByText('Cancel'));

      expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
    });

    it('calls onConfirm when confirm button clicked', () => {
      render(<ConfirmDialog {...defaultProps} />);

      fireEvent.click(screen.getByText('Confirm'));

      expect(defaultProps.onConfirm).toHaveBeenCalledTimes(1);
    });

    it('calls onClose when backdrop clicked', () => {
      const { container } = render(<ConfirmDialog {...defaultProps} />);

      const backdrop = container.querySelector('.bg-black\\/50');
      fireEvent.click(backdrop!);

      expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
    });

    it('calls onClose when Escape key pressed', () => {
      render(<ConfirmDialog {...defaultProps} />);

      fireEvent.keyDown(document, { key: 'Escape' });

      expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
    });

    it('does not call onClose when clicking inside dialog', () => {
      render(<ConfirmDialog {...defaultProps} />);

      fireEvent.click(screen.getByText('Confirm Action'));

      expect(defaultProps.onClose).not.toHaveBeenCalled();
    });
  });

  // Test: Loading state
  describe('Loading State', () => {
    it('disables buttons when isLoading is true', () => {
      render(<ConfirmDialog {...defaultProps} isLoading={true} />);

      expect(screen.getByText('Cancel')).toBeDisabled();
      expect(screen.getByText('Please wait...')).toBeDisabled();
      expect(screen.getByLabelText('Close')).toBeDisabled();
    });

    it('shows loading text on confirm button', () => {
      render(<ConfirmDialog {...defaultProps} isLoading={true} />);

      expect(screen.getByText('Please wait...')).toBeInTheDocument();
    });

    it('does not close on Escape when loading', () => {
      render(<ConfirmDialog {...defaultProps} isLoading={true} />);

      fireEvent.keyDown(document, { key: 'Escape' });

      expect(defaultProps.onClose).not.toHaveBeenCalled();
    });

    it('does not close on backdrop click when loading', () => {
      const { container } = render(<ConfirmDialog {...defaultProps} isLoading={true} />);

      const backdrop = container.querySelector('.bg-black\\/50');
      fireEvent.click(backdrop!);

      expect(defaultProps.onClose).not.toHaveBeenCalled();
    });
  });

  // Test: Accessibility and focus management
  describe('Accessibility and Focus Management', () => {
    it('has proper ARIA attributes', () => {
      render(<ConfirmDialog {...defaultProps} />);

      const dialog = screen.getByRole('alertdialog');
      expect(dialog).toHaveAttribute('aria-labelledby');
      expect(dialog).toHaveAttribute('aria-describedby');
    });

    it('focuses cancel button when opened', async () => {
      render(<ConfirmDialog {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Cancel')).toHaveFocus();
      });
    });

    it('prevents body scroll when open', () => {
      render(<ConfirmDialog {...defaultProps} />);

      expect(document.body.style.overflow).toBe('hidden');
    });

    it('restores body scroll when closed', () => {
      const { rerender } = render(<ConfirmDialog {...defaultProps} />);

      expect(document.body.style.overflow).toBe('hidden');

      rerender(<ConfirmDialog {...defaultProps} isOpen={false} />);

      expect(document.body.style.overflow).toBe('unset');
    });

    it('title is properly associated with dialog', () => {
      render(<ConfirmDialog {...defaultProps} />);

      const dialog = screen.getByRole('alertdialog');
      const labelledBy = dialog.getAttribute('aria-labelledby');
      const title = document.getElementById(labelledBy!);

      expect(title).toHaveTextContent('Confirm Action');
    });

    it('message is properly associated with dialog', () => {
      render(<ConfirmDialog {...defaultProps} />);

      const dialog = screen.getByRole('alertdialog');
      const describedBy = dialog.getAttribute('aria-describedby');
      const message = document.getElementById(describedBy!);

      expect(message).toHaveTextContent('Are you sure you want to proceed?');
    });
  });

  // Test: Edge cases
  describe('Edge Cases', () => {
    it('handles long titles', () => {
      const longTitle = 'This is a very long title that should still display correctly in the confirmation dialog';

      render(<ConfirmDialog {...defaultProps} title={longTitle} />);

      expect(screen.getByText(longTitle)).toBeInTheDocument();
    });

    it('handles long messages', () => {
      const longMessage = 'This is a very long message that provides detailed information about the action being confirmed and what will happen if the user proceeds with this operation.';

      render(<ConfirmDialog {...defaultProps} message={longMessage} />);

      expect(screen.getByText(longMessage)).toBeInTheDocument();
    });

    it('cleans up event listeners on unmount', () => {
      const { unmount } = render(<ConfirmDialog {...defaultProps} />);

      unmount();

      fireEvent.keyDown(document, { key: 'Escape' });

      expect(defaultProps.onClose).not.toHaveBeenCalled();
    });

    it('has proper styling hierarchy', () => {
      render(<ConfirmDialog {...defaultProps} />);

      const title = screen.getByText('Confirm Action');
      expect(title.tagName).toBe('H2');
    });

    it('buttons have proper layout', () => {
      const { container } = render(<ConfirmDialog {...defaultProps} />);

      expect(container.querySelector('.flex.gap-3')).toBeInTheDocument();
    });

    it('cancel button is flex-1 for equal width', () => {
      render(<ConfirmDialog {...defaultProps} />);

      const cancelButton = screen.getByText('Cancel');
      expect(cancelButton).toHaveClass('flex-1');
    });

    it('confirm button is flex-1 for equal width', () => {
      render(<ConfirmDialog {...defaultProps} />);

      const confirmButton = screen.getByText('Confirm');
      expect(confirmButton).toHaveClass('flex-1');
    });

    it('has z-index for proper stacking', () => {
      const { container } = render(<ConfirmDialog {...defaultProps} />);

      expect(container.querySelector('.z-50')).toBeInTheDocument();
    });
  });
});
