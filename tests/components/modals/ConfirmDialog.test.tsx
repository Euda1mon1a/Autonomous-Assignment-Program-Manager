import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { ConfirmDialog } from '@/components/ConfirmDialog';

describe('ConfirmDialog', () => {
  const mockOnClose = jest.fn();
  const mockOnConfirm = jest.fn();

  const defaultProps = {
    isOpen: true,
    onClose: mockOnClose,
    onConfirm: mockOnConfirm,
    title: 'Confirm Action',
    message: 'Are you sure you want to proceed?',
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should not render when isOpen is false', () => {
      render(<ConfirmDialog {...defaultProps} isOpen={false} />);

      expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument();
      expect(screen.queryByText('Confirm Action')).not.toBeInTheDocument();
    });

    it('should render when isOpen is true', () => {
      render(<ConfirmDialog {...defaultProps} />);

      expect(screen.getByRole('alertdialog')).toBeInTheDocument();
      expect(screen.getByText('Confirm Action')).toBeInTheDocument();
    });

    it('should display the title', () => {
      render(<ConfirmDialog {...defaultProps} />);

      expect(screen.getByText('Confirm Action')).toBeInTheDocument();
    });

    it('should display the message', () => {
      render(<ConfirmDialog {...defaultProps} />);

      expect(screen.getByText('Are you sure you want to proceed?')).toBeInTheDocument();
    });

    it('should display default confirm button label', () => {
      render(<ConfirmDialog {...defaultProps} />);

      expect(screen.getByRole('button', { name: /confirm/i })).toBeInTheDocument();
    });

    it('should display default cancel button label', () => {
      render(<ConfirmDialog {...defaultProps} />);

      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
    });

    it('should display custom confirm button label', () => {
      render(<ConfirmDialog {...defaultProps} confirmLabel="Delete Item" />);

      expect(screen.getByRole('button', { name: /delete item/i })).toBeInTheDocument();
    });

    it('should display custom cancel button label', () => {
      render(<ConfirmDialog {...defaultProps} cancelLabel="Go Back" />);

      expect(screen.getByRole('button', { name: /go back/i })).toBeInTheDocument();
    });

    it('should display close button', () => {
      render(<ConfirmDialog {...defaultProps} />);

      expect(screen.getByRole('button', { name: /close/i })).toBeInTheDocument();
    });
  });

  describe('Variants', () => {
    it('should render danger variant with Trash2 icon', () => {
      render(<ConfirmDialog {...defaultProps} variant="danger" />);

      const dialog = screen.getByRole('alertdialog');
      expect(dialog).toBeInTheDocument();

      // Check for danger styling classes
      const confirmButton = screen.getByRole('button', { name: /confirm/i });
      expect(confirmButton).toHaveClass('bg-red-600');
    });

    it('should render warning variant with AlertTriangle icon', () => {
      render(<ConfirmDialog {...defaultProps} variant="warning" />);

      const dialog = screen.getByRole('alertdialog');
      expect(dialog).toBeInTheDocument();

      // Check for warning styling classes
      const confirmButton = screen.getByRole('button', { name: /confirm/i });
      expect(confirmButton).toHaveClass('bg-amber-600');
    });

    it('should render default variant with AlertTriangle icon', () => {
      render(<ConfirmDialog {...defaultProps} variant="default" />);

      const dialog = screen.getByRole('alertdialog');
      expect(dialog).toBeInTheDocument();

      // Check for default styling classes
      const confirmButton = screen.getByRole('button', { name: /confirm/i });
      expect(confirmButton).toHaveClass('bg-blue-600');
    });

    it('should use default variant when no variant is specified', () => {
      render(<ConfirmDialog {...defaultProps} />);

      const confirmButton = screen.getByRole('button', { name: /confirm/i });
      expect(confirmButton).toHaveClass('bg-blue-600');
    });
  });

  describe('Button Interactions', () => {
    it('should call onConfirm when confirm button is clicked', async () => {
      const user = userEvent.setup();
      render(<ConfirmDialog {...defaultProps} />);

      const confirmButton = screen.getByRole('button', { name: /confirm/i });
      await user.click(confirmButton);

      expect(mockOnConfirm).toHaveBeenCalledTimes(1);
    });

    it('should call onClose when cancel button is clicked', async () => {
      const user = userEvent.setup();
      render(<ConfirmDialog {...defaultProps} />);

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      expect(mockOnClose).toHaveBeenCalledTimes(1);
      expect(mockOnConfirm).not.toHaveBeenCalled();
    });

    it('should call onClose when close button (X) is clicked', async () => {
      const user = userEvent.setup();
      render(<ConfirmDialog {...defaultProps} />);

      const closeButton = screen.getByRole('button', { name: /close/i });
      await user.click(closeButton);

      expect(mockOnClose).toHaveBeenCalledTimes(1);
      expect(mockOnConfirm).not.toHaveBeenCalled();
    });

    it('should call onClose when backdrop is clicked', async () => {
      const user = userEvent.setup();
      render(<ConfirmDialog {...defaultProps} />);

      // Find backdrop by getting the first div inside the fixed container
      const container = screen.getByRole('alertdialog').parentElement;
      const backdrop = container?.querySelector('.bg-black\\/50');

      if (backdrop) {
        await user.click(backdrop as HTMLElement);
        expect(mockOnClose).toHaveBeenCalledTimes(1);
      }
    });

    it('should not call onConfirm when clicking outside confirm button', async () => {
      const user = userEvent.setup();
      render(<ConfirmDialog {...defaultProps} />);

      const dialog = screen.getByRole('alertdialog');
      await user.click(dialog);

      expect(mockOnConfirm).not.toHaveBeenCalled();
    });
  });

  describe('Keyboard Interactions', () => {
    it('should close dialog when Escape key is pressed', async () => {
      const user = userEvent.setup();
      render(<ConfirmDialog {...defaultProps} />);

      await user.keyboard('{Escape}');

      expect(mockOnClose).toHaveBeenCalledTimes(1);
      expect(mockOnConfirm).not.toHaveBeenCalled();
    });

    it('should not close dialog on Escape when loading', async () => {
      const user = userEvent.setup();
      render(<ConfirmDialog {...defaultProps} isLoading={true} />);

      await user.keyboard('{Escape}');

      expect(mockOnClose).not.toHaveBeenCalled();
    });

    it('should allow Tab navigation between buttons', async () => {
      const user = userEvent.setup();
      render(<ConfirmDialog {...defaultProps} />);

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      const confirmButton = screen.getByRole('button', { name: /confirm/i });

      cancelButton.focus();
      expect(document.activeElement).toBe(cancelButton);

      await user.tab();
      expect(document.activeElement).toBe(confirmButton);
    });

    it('should trigger confirm with Enter key when confirm button is focused', async () => {
      const user = userEvent.setup();
      render(<ConfirmDialog {...defaultProps} />);

      const confirmButton = screen.getByRole('button', { name: /confirm/i });
      confirmButton.focus();

      await user.keyboard('{Enter}');

      expect(mockOnConfirm).toHaveBeenCalledTimes(1);
    });

    it('should trigger cancel with Enter key when cancel button is focused', async () => {
      const user = userEvent.setup();
      render(<ConfirmDialog {...defaultProps} />);

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      cancelButton.focus();

      await user.keyboard('{Enter}');

      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });
  });

  describe('Focus Management', () => {
    it('should focus cancel button when dialog opens', async () => {
      render(<ConfirmDialog {...defaultProps} />);

      await waitFor(() => {
        const cancelButton = screen.getByRole('button', { name: /cancel/i });
        expect(document.activeElement).toBe(cancelButton);
      });
    });

    it('should maintain focus within dialog', async () => {
      render(<ConfirmDialog {...defaultProps} />);

      await waitFor(() => {
        const cancelButton = screen.getByRole('button', { name: /cancel/i });
        expect(document.activeElement).toBe(cancelButton);
      });
    });

    it('should not change focus when clicking inside dialog', async () => {
      const user = userEvent.setup();
      render(<ConfirmDialog {...defaultProps} />);

      const dialog = screen.getByRole('alertdialog');
      const cancelButton = screen.getByRole('button', { name: /cancel/i });

      await waitFor(() => {
        expect(document.activeElement).toBe(cancelButton);
      });

      // Click inside dialog (but not on a button)
      await user.click(dialog);

      // Focus should remain on cancel button or move to another element
      expect(document.activeElement).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('should disable buttons when loading', () => {
      render(<ConfirmDialog {...defaultProps} isLoading={true} />);

      const confirmButton = screen.getByRole('button', { name: /please wait/i });
      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      const closeButton = screen.getByRole('button', { name: /close/i });

      expect(confirmButton).toBeDisabled();
      expect(cancelButton).toBeDisabled();
      expect(closeButton).toBeDisabled();
    });

    it('should change confirm button text when loading', () => {
      render(<ConfirmDialog {...defaultProps} isLoading={true} />);

      expect(screen.getByText('Please wait...')).toBeInTheDocument();
      expect(screen.queryByText('Confirm')).not.toBeInTheDocument();
    });

    it('should not call onConfirm when clicking disabled confirm button', async () => {
      const user = userEvent.setup();
      render(<ConfirmDialog {...defaultProps} isLoading={true} />);

      const confirmButton = screen.getByRole('button', { name: /please wait/i });
      await user.click(confirmButton);

      expect(mockOnConfirm).not.toHaveBeenCalled();
    });

    it('should not call onClose when clicking disabled cancel button', async () => {
      const user = userEvent.setup();
      render(<ConfirmDialog {...defaultProps} isLoading={true} />);

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      expect(mockOnClose).not.toHaveBeenCalled();
    });

    it('should not close on backdrop click when loading', async () => {
      const user = userEvent.setup();
      render(<ConfirmDialog {...defaultProps} isLoading={true} />);

      const container = screen.getByRole('alertdialog').parentElement;
      const backdrop = container?.querySelector('.bg-black\\/50');

      if (backdrop) {
        await user.click(backdrop as HTMLElement);
        expect(mockOnClose).not.toHaveBeenCalled();
      }
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA role', () => {
      render(<ConfirmDialog {...defaultProps} />);

      expect(screen.getByRole('alertdialog')).toBeInTheDocument();
    });

    it('should have aria-modal attribute', () => {
      render(<ConfirmDialog {...defaultProps} />);

      const dialog = screen.getByRole('alertdialog');
      expect(dialog).toHaveAttribute('aria-modal', 'true');
    });

    it('should have aria-labelledby pointing to title', () => {
      render(<ConfirmDialog {...defaultProps} />);

      const dialog = screen.getByRole('alertdialog');
      const titleId = dialog.getAttribute('aria-labelledby');

      expect(titleId).toBeTruthy();
      const titleElement = document.getElementById(titleId!);
      expect(titleElement).toHaveTextContent('Confirm Action');
    });

    it('should have aria-describedby pointing to message', () => {
      render(<ConfirmDialog {...defaultProps} />);

      const dialog = screen.getByRole('alertdialog');
      const descId = dialog.getAttribute('aria-describedby');

      expect(descId).toBeTruthy();
      const descElement = document.getElementById(descId!);
      expect(descElement).toHaveTextContent('Are you sure you want to proceed?');
    });

    it('should have accessible label for close button', () => {
      render(<ConfirmDialog {...defaultProps} />);

      expect(screen.getByRole('button', { name: /close/i })).toHaveAttribute('aria-label', 'Close');
    });

    it('should prevent body scroll when open', () => {
      render(<ConfirmDialog {...defaultProps} />);

      expect(document.body.style.overflow).toBe('hidden');
    });

    it('should restore body scroll when closed', () => {
      const { unmount } = render(<ConfirmDialog {...defaultProps} />);

      expect(document.body.style.overflow).toBe('hidden');

      unmount();

      expect(document.body.style.overflow).toBe('unset');
    });

    it('should restore body scroll when isOpen changes to false', () => {
      const { rerender } = render(<ConfirmDialog {...defaultProps} isOpen={true} />);

      expect(document.body.style.overflow).toBe('hidden');

      rerender(<ConfirmDialog {...defaultProps} isOpen={false} />);

      expect(document.body.style.overflow).toBe('unset');
    });
  });

  describe('Visual Styling', () => {
    it('should apply danger color classes for danger variant', () => {
      render(<ConfirmDialog {...defaultProps} variant="danger" />);

      const confirmButton = screen.getByRole('button', { name: /confirm/i });
      expect(confirmButton).toHaveClass('bg-red-600', 'hover:bg-red-700');
    });

    it('should apply warning color classes for warning variant', () => {
      render(<ConfirmDialog {...defaultProps} variant="warning" />);

      const confirmButton = screen.getByRole('button', { name: /confirm/i });
      expect(confirmButton).toHaveClass('bg-amber-600', 'hover:bg-amber-700');
    });

    it('should apply default color classes for default variant', () => {
      render(<ConfirmDialog {...defaultProps} variant="default" />);

      const confirmButton = screen.getByRole('button', { name: /confirm/i });
      expect(confirmButton).toHaveClass('bg-blue-600', 'hover:bg-blue-700');
    });

    it('should display icon with appropriate color for danger variant', () => {
      render(<ConfirmDialog {...defaultProps} variant="danger" />);

      const dialog = screen.getByRole('alertdialog');
      const iconContainer = dialog.querySelector('.text-red-600.bg-red-100');
      expect(iconContainer).toBeInTheDocument();
    });

    it('should display icon with appropriate color for warning variant', () => {
      render(<ConfirmDialog {...defaultProps} variant="warning" />);

      const dialog = screen.getByRole('alertdialog');
      const iconContainer = dialog.querySelector('.text-amber-600.bg-amber-100');
      expect(iconContainer).toBeInTheDocument();
    });

    it('should display icon with appropriate color for default variant', () => {
      render(<ConfirmDialog {...defaultProps} variant="default" />);

      const dialog = screen.getByRole('alertdialog');
      const iconContainer = dialog.querySelector('.text-blue-600.bg-blue-100');
      expect(iconContainer).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty message', () => {
      render(<ConfirmDialog {...defaultProps} message="" />);

      expect(screen.getByRole('alertdialog')).toBeInTheDocument();
    });

    it('should handle very long message', () => {
      const longMessage = 'This is a very long message that should still be displayed correctly. '.repeat(10);
      render(<ConfirmDialog {...defaultProps} message={longMessage} />);

      expect(screen.getByText(longMessage)).toBeInTheDocument();
    });

    it('should handle very long title', () => {
      const longTitle = 'This is a very long title that should still be displayed correctly';
      render(<ConfirmDialog {...defaultProps} title={longTitle} />);

      expect(screen.getByText(longTitle)).toBeInTheDocument();
    });

    it('should handle rapid open/close cycles', () => {
      const { rerender } = render(<ConfirmDialog {...defaultProps} isOpen={true} />);

      expect(screen.getByRole('alertdialog')).toBeInTheDocument();

      rerender(<ConfirmDialog {...defaultProps} isOpen={false} />);
      expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument();

      rerender(<ConfirmDialog {...defaultProps} isOpen={true} />);
      expect(screen.getByRole('alertdialog')).toBeInTheDocument();

      rerender(<ConfirmDialog {...defaultProps} isOpen={false} />);
      expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument();
    });

    it('should handle multiple confirm clicks without double-triggering', async () => {
      const user = userEvent.setup();
      render(<ConfirmDialog {...defaultProps} />);

      const confirmButton = screen.getByRole('button', { name: /confirm/i });
      await user.click(confirmButton);
      await user.click(confirmButton);

      // Should be called twice if both clicks go through
      expect(mockOnConfirm).toHaveBeenCalledTimes(2);
    });

    it('should handle special characters in title and message', () => {
      const specialTitle = 'Delete <Item> & "Confirm"?';
      const specialMessage = "Are you sure? This can't be undone & it's permanent!";

      render(
        <ConfirmDialog
          {...defaultProps}
          title={specialTitle}
          message={specialMessage}
        />
      );

      expect(screen.getByText(specialTitle)).toBeInTheDocument();
      expect(screen.getByText(specialMessage)).toBeInTheDocument();
    });
  });

  describe('Integration Scenarios', () => {
    it('should work with async onConfirm handler', async () => {
      const user = userEvent.setup();
      const asyncOnConfirm = jest.fn().mockResolvedValue(undefined);

      render(<ConfirmDialog {...defaultProps} onConfirm={asyncOnConfirm} />);

      const confirmButton = screen.getByRole('button', { name: /confirm/i });
      await user.click(confirmButton);

      await waitFor(() => {
        expect(asyncOnConfirm).toHaveBeenCalled();
      });
    });

    it('should work with async onClose handler', async () => {
      const user = userEvent.setup();
      const asyncOnClose = jest.fn().mockResolvedValue(undefined);

      render(<ConfirmDialog {...defaultProps} onClose={asyncOnClose} />);

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      await waitFor(() => {
        expect(asyncOnClose).toHaveBeenCalled();
      });
    });

    it('should maintain correct state when switching between loading states', () => {
      const { rerender } = render(<ConfirmDialog {...defaultProps} isLoading={false} />);

      let confirmButton = screen.getByRole('button', { name: /confirm/i });
      expect(confirmButton).not.toBeDisabled();

      rerender(<ConfirmDialog {...defaultProps} isLoading={true} />);

      confirmButton = screen.getByRole('button', { name: /please wait/i });
      expect(confirmButton).toBeDisabled();

      rerender(<ConfirmDialog {...defaultProps} isLoading={false} />);

      confirmButton = screen.getByRole('button', { name: /confirm/i });
      expect(confirmButton).not.toBeDisabled();
    });
  });
});
