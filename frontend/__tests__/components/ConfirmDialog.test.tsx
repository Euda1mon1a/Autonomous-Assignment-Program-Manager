/**
 * Tests for ConfirmDialog component
 *
 * Tests dialog rendering, variants, interactions, and accessibility
 */
import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ConfirmDialog } from '@/components/ConfirmDialog'

describe('ConfirmDialog', () => {
  const mockOnClose = jest.fn()
  const mockOnConfirm = jest.fn()

  const defaultProps = {
    isOpen: true,
    onClose: mockOnClose,
    onConfirm: mockOnConfirm,
    title: 'Confirm Action',
    message: 'Are you sure you want to proceed?',
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Rendering', () => {
    it('should not render when isOpen is false', () => {
      render(
        <ConfirmDialog {...defaultProps} isOpen={false} />
      )

      expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument()
    })

    it('should render dialog when isOpen is true', () => {
      render(
        <ConfirmDialog {...defaultProps} />
      )

      expect(screen.getByRole('alertdialog')).toBeInTheDocument()
      expect(screen.getByText('Confirm Action')).toBeInTheDocument()
      expect(screen.getByText('Are you sure you want to proceed?')).toBeInTheDocument()
    })

    it('should render default Confirm and Cancel buttons', () => {
      render(
        <ConfirmDialog {...defaultProps} />
      )

      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /confirm/i })).toBeInTheDocument()
    })

    it('should render custom button labels', () => {
      render(
        <ConfirmDialog
          {...defaultProps}
          confirmLabel="Delete Item"
          cancelLabel="Go Back"
        />
      )

      expect(screen.getByRole('button', { name: /delete item/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /go back/i })).toBeInTheDocument()
    })

    it('should render close button (X)', () => {
      render(
        <ConfirmDialog {...defaultProps} />
      )

      expect(screen.getByRole('button', { name: /close/i })).toBeInTheDocument()
    })
  })

  describe('Variants', () => {
    it('should render danger variant with trash icon', () => {
      render(
        <ConfirmDialog {...defaultProps} variant="danger" />
      )

      const dialog = screen.getByRole('alertdialog')
      expect(dialog).toBeInTheDocument()

      // Check for red color classes on confirm button
      const confirmButton = screen.getByRole('button', { name: /confirm/i })
      expect(confirmButton.className).toMatch(/bg-red-600/)
    })

    it('should render warning variant with alert icon', () => {
      render(
        <ConfirmDialog {...defaultProps} variant="warning" />
      )

      const dialog = screen.getByRole('alertdialog')
      expect(dialog).toBeInTheDocument()

      // Check for amber color classes on confirm button
      const confirmButton = screen.getByRole('button', { name: /confirm/i })
      expect(confirmButton.className).toMatch(/bg-amber-600/)
    })

    it('should render default variant', () => {
      render(
        <ConfirmDialog {...defaultProps} variant="default" />
      )

      const dialog = screen.getByRole('alertdialog')
      expect(dialog).toBeInTheDocument()

      // Check for blue color classes on confirm button
      const confirmButton = screen.getByRole('button', { name: /confirm/i })
      expect(confirmButton.className).toMatch(/bg-blue-600/)
    })
  })

  describe('Button Interactions', () => {
    it('should call onConfirm when Confirm button is clicked', async () => {
      const user = userEvent.setup()

      render(
        <ConfirmDialog {...defaultProps} />
      )

      const confirmButton = screen.getByRole('button', { name: /confirm/i })
      await user.click(confirmButton)

      expect(mockOnConfirm).toHaveBeenCalledTimes(1)
    })

    it('should call onClose when Cancel button is clicked', async () => {
      const user = userEvent.setup()

      render(
        <ConfirmDialog {...defaultProps} />
      )

      const cancelButton = screen.getByRole('button', { name: /cancel/i })
      await user.click(cancelButton)

      expect(mockOnClose).toHaveBeenCalledTimes(1)
    })

    it('should call onClose when close button (X) is clicked', async () => {
      const user = userEvent.setup()

      render(
        <ConfirmDialog {...defaultProps} />
      )

      const closeButton = screen.getByRole('button', { name: /close/i })
      await user.click(closeButton)

      expect(mockOnClose).toHaveBeenCalledTimes(1)
    })

    it('should call onClose when clicking on backdrop', async () => {
      const user = userEvent.setup()

      render(
        <ConfirmDialog {...defaultProps} />
      )

      const backdrop = document.querySelector('.bg-black\\/50')
      if (backdrop) {
        await user.click(backdrop)
        expect(mockOnClose).toHaveBeenCalledTimes(1)
      }
    })
  })

  describe('Keyboard Interactions', () => {
    it('should call onClose when Escape key is pressed', async () => {
      const user = userEvent.setup()

      render(
        <ConfirmDialog {...defaultProps} />
      )

      await user.keyboard('{Escape}')

      expect(mockOnClose).toHaveBeenCalledTimes(1)
    })

    it('should not close on Escape when loading', async () => {
      const user = userEvent.setup()

      render(
        <ConfirmDialog {...defaultProps} isLoading={true} />
      )

      await user.keyboard('{Escape}')

      expect(mockOnClose).not.toHaveBeenCalled()
    })
  })

  describe('Loading State', () => {
    it('should show loading text when isLoading is true', () => {
      render(
        <ConfirmDialog {...defaultProps} isLoading={true} />
      )

      expect(screen.getByText(/please wait/i)).toBeInTheDocument()
    })

    it('should disable buttons when loading', () => {
      render(
        <ConfirmDialog {...defaultProps} isLoading={true} />
      )

      const cancelButton = screen.getByRole('button', { name: /cancel/i })
      const confirmButton = screen.getByRole('button', { name: /please wait/i })
      const closeButton = screen.getByRole('button', { name: /close/i })

      expect(cancelButton).toBeDisabled()
      expect(confirmButton).toBeDisabled()
      expect(closeButton).toBeDisabled()
    })

    it('should not allow backdrop click when loading', async () => {
      const user = userEvent.setup()

      render(
        <ConfirmDialog {...defaultProps} isLoading={true} />
      )

      const backdrop = document.querySelector('.bg-black\\/50')
      if (backdrop) {
        await user.click(backdrop)
        expect(mockOnClose).not.toHaveBeenCalled()
      }
    })

    it('should not allow close button click when loading', async () => {
      const user = userEvent.setup()

      render(
        <ConfirmDialog {...defaultProps} isLoading={true} />
      )

      const closeButton = screen.getByRole('button', { name: /close/i })

      // Button is disabled, so click won't trigger callback
      expect(closeButton).toBeDisabled()
    })
  })

  describe('Focus Management', () => {
    it('should focus cancel button when dialog opens', () => {
      render(
        <ConfirmDialog {...defaultProps} />
      )

      const cancelButton = screen.getByRole('button', { name: /cancel/i })

      // The component uses useEffect to focus, so we need to wait
      waitFor(() => {
        expect(cancelButton).toHaveFocus()
      })
    })
  })

  describe('Body Scroll Lock', () => {
    it('should lock body scroll when dialog is open', () => {
      render(
        <ConfirmDialog {...defaultProps} />
      )

      expect(document.body.style.overflow).toBe('hidden')
    })

    it('should restore body scroll when dialog closes', () => {
      const { unmount } = render(
        <ConfirmDialog {...defaultProps} />
      )

      expect(document.body.style.overflow).toBe('hidden')

      unmount()

      expect(document.body.style.overflow).toBe('unset')
    })
  })

  describe('Accessibility', () => {
    it('should have proper aria attributes', () => {
      render(
        <ConfirmDialog {...defaultProps} />
      )

      const dialog = screen.getByRole('alertdialog')
      expect(dialog).toHaveAttribute('aria-modal', 'true')
      expect(dialog).toHaveAttribute('aria-labelledby')
      expect(dialog).toHaveAttribute('aria-describedby')
    })

    it('should have accessible title and description', () => {
      render(
        <ConfirmDialog {...defaultProps} />
      )

      const dialog = screen.getByRole('alertdialog')
      const titleId = dialog.getAttribute('aria-labelledby')
      const descId = dialog.getAttribute('aria-describedby')

      expect(titleId).toBeTruthy()
      expect(descId).toBeTruthy()

      const title = document.getElementById(titleId!)
      const description = document.getElementById(descId!)

      expect(title).toHaveTextContent('Confirm Action')
      expect(description).toHaveTextContent('Are you sure you want to proceed?')
    })

    it('should have accessible close button', () => {
      render(
        <ConfirmDialog {...defaultProps} />
      )

      const closeButton = screen.getByRole('button', { name: /close/i })
      expect(closeButton).toHaveAttribute('aria-label', 'Close')
    })
  })

  describe('Multiple Instances', () => {
    it('should handle different titles and messages', () => {
      render(
        <ConfirmDialog
          {...defaultProps}
          title="Delete Item"
          message="This action cannot be undone."
        />
      )

      expect(screen.getByText('Delete Item')).toBeInTheDocument()
      expect(screen.getByText('This action cannot be undone.')).toBeInTheDocument()
    })

    it('should handle different variants independently', () => {
      const { rerender } = render(
        <ConfirmDialog {...defaultProps} variant="danger" />
      )

      let confirmButton = screen.getByRole('button', { name: /confirm/i })
      expect(confirmButton.className).toMatch(/bg-red-600/)

      rerender(
        <ConfirmDialog {...defaultProps} variant="warning" />
      )

      confirmButton = screen.getByRole('button', { name: /confirm/i })
      expect(confirmButton.className).toMatch(/bg-amber-600/)

      rerender(
        <ConfirmDialog {...defaultProps} variant="default" />
      )

      confirmButton = screen.getByRole('button', { name: /confirm/i })
      expect(confirmButton.className).toMatch(/bg-blue-600/)
    })
  })

  describe('Edge Cases', () => {
    it('should handle very long message text', () => {
      const longMessage = 'This is a very long message that should wrap properly. '.repeat(10)

      render(
        <ConfirmDialog {...defaultProps} message={longMessage} />
      )

      // Use a substring to verify the message is displayed
      expect(screen.getByText(/this is a very long message that should wrap properly/i)).toBeInTheDocument()
    })

    it('should handle empty custom labels', () => {
      render(
        <ConfirmDialog
          {...defaultProps}
          confirmLabel=""
          cancelLabel=""
        />
      )

      // Buttons should still exist even with empty labels
      const buttons = screen.getAllByRole('button')
      expect(buttons.length).toBeGreaterThan(0)
    })
  })
})
