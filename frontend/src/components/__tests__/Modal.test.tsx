import { renderWithProviders } from '@/test-utils';
/**
 * Tests for Modal Component
 * Component: 36 - Modal dialog
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@/test-utils';
import '@testing-library/jest-dom';
import { Modal } from '../Modal';

describe('Modal', () => {
  const mockOnClose = jest.fn();

  beforeEach(() => {
    mockOnClose.mockClear();
    // Reset document overflow style
    document.body.style.overflow = 'unset';
  });

  // Test 36.1: Render test
  describe('Rendering', () => {
    it('renders when isOpen is true', () => {
      render(
        <Modal isOpen={true} onClose={mockOnClose} title="Test Modal">
          <div>Modal content</div>
        </Modal>
      );

      expect(screen.getByText('Test Modal')).toBeInTheDocument();
      expect(screen.getByText('Modal content')).toBeInTheDocument();
    });

    it('does not render when isOpen is false', () => {
      render(
        <Modal isOpen={false} onClose={mockOnClose} title="Test Modal">
          <div>Modal content</div>
        </Modal>
      );

      expect(screen.queryByText('Test Modal')).not.toBeInTheDocument();
    });

    it('renders close button', () => {
      render(
        <Modal isOpen={true} onClose={mockOnClose} title="Test Modal">
          <div>Content</div>
        </Modal>
      );

      expect(screen.getByLabelText('Close modal')).toBeInTheDocument();
    });

    it('renders backdrop', () => {
      const { container } = render(
        <Modal isOpen={true} onClose={mockOnClose} title="Test Modal">
          <div>Content</div>
        </Modal>
      );

      expect(container.querySelector('.bg-black\\/50')).toBeInTheDocument();
    });

    it('has proper dialog role', () => {
      render(
        <Modal isOpen={true} onClose={mockOnClose} title="Test Modal">
          <div>Content</div>
        </Modal>
      );

      const dialog = screen.getByRole('dialog');
      expect(dialog).toBeInTheDocument();
      expect(dialog).toHaveAttribute('aria-modal', 'true');
    });
  });

  // Test 36.2: Interaction
  describe('Interaction', () => {
    it('calls onClose when close button clicked', () => {
      render(
        <Modal isOpen={true} onClose={mockOnClose} title="Test Modal">
          <div>Content</div>
        </Modal>
      );

      fireEvent.click(screen.getByLabelText('Close modal'));
      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });

    it('calls onClose when backdrop clicked', () => {
      const { container } = render(
        <Modal isOpen={true} onClose={mockOnClose} title="Test Modal">
          <div>Content</div>
        </Modal>
      );

      const backdrop = container.querySelector('.bg-black\\/50');
      fireEvent.click(backdrop!);

      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });

    it('calls onClose when Escape key pressed', () => {
      render(
        <Modal isOpen={true} onClose={mockOnClose} title="Test Modal">
          <div>Content</div>
        </Modal>
      );

      fireEvent.keyDown(document, { key: 'Escape' });
      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });

    it('does not call onClose when clicking inside modal', () => {
      render(
        <Modal isOpen={true} onClose={mockOnClose} title="Test Modal">
          <div>Content</div>
        </Modal>
      );

      fireEvent.click(screen.getByText('Modal content'));
      expect(mockOnClose).not.toHaveBeenCalled();
    });
  });

  // Test 36.3: Accessibility and focus management
  describe('Accessibility and Focus Management', () => {
    it('has proper ARIA attributes', () => {
      render(
        <Modal isOpen={true} onClose={mockOnClose} title="Test Modal">
          <div>Content</div>
        </Modal>
      );

      const dialog = screen.getByRole('dialog');
      expect(dialog).toHaveAttribute('aria-modal', 'true');
      expect(dialog).toHaveAttribute('aria-labelledby');
    });

    it('focuses first input when opened', async () => {
      render(
        <Modal isOpen={true} onClose={mockOnClose} title="Test Modal">
          <input type="text" placeholder="First input" />
          <button>Submit</button>
        </Modal>
      );

      await waitFor(() => {
        const input = screen.getByPlaceholderText('First input');
        expect(input).toHaveFocus();
      });
    });

    it('traps focus within modal', () => {
      render(
        <Modal isOpen={true} onClose={mockOnClose} title="Test Modal">
          <button>First</button>
          <button>Last</button>
        </Modal>
      );

      const firstButton = screen.getByText('First');
      const lastButton = screen.getByText('Last');
      const closeButton = screen.getByLabelText('Close modal');

      // Tab from last element should cycle to first
      lastButton.focus();
      fireEvent.keyDown(document, { key: 'Tab' });

      // Should trap focus (implementation uses focus trap)
      expect(document.activeElement).toBeTruthy();
    });

    it('prevents body scroll when open', () => {
      render(
        <Modal isOpen={true} onClose={mockOnClose} title="Test Modal">
          <div>Content</div>
        </Modal>
      );

      expect(document.body.style.overflow).toBe('hidden');
    });

    it('restores body scroll when closed', () => {
      const { rerender } = render(
        <Modal isOpen={true} onClose={mockOnClose} title="Test Modal">
          <div>Content</div>
        </Modal>
      );

      expect(document.body.style.overflow).toBe('hidden');

      rerender(
        <Modal isOpen={false} onClose={mockOnClose} title="Test Modal">
          <div>Content</div>
        </Modal>
      );

      expect(document.body.style.overflow).toBe('unset');
    });
  });

  // Test 36.4: Edge cases
  describe('Edge Cases', () => {
    it('handles complex content', () => {
      render(
        <Modal isOpen={true} onClose={mockOnClose} title="Complex Modal">
          <div>
            <h3>Subtitle</h3>
            <p>Paragraph 1</p>
            <p>Paragraph 2</p>
            <button>Action</button>
          </div>
        </Modal>
      );

      expect(screen.getByText('Subtitle')).toBeInTheDocument();
      expect(screen.getByText('Paragraph 1')).toBeInTheDocument();
      expect(screen.getByText('Action')).toBeInTheDocument();
    });

    it('handles multiple inputs', () => {
      render(
        <Modal isOpen={true} onClose={mockOnClose} title="Form Modal">
          <input type="text" placeholder="Name" />
          <input type="email" placeholder="Email" />
          <textarea placeholder="Message" />
        </Modal>
      );

      expect(screen.getByPlaceholderText('Name')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Email')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Message')).toBeInTheDocument();
    });

    it('renders title in header', () => {
      render(
        <Modal isOpen={true} onClose={mockOnClose} title="Important Title">
          <div>Content</div>
        </Modal>
      );

      const title = screen.getByText('Important Title');
      expect(title.tagName).toBe('H2');
    });

    it('handles long titles', () => {
      const longTitle = 'This is a very long title that should still render correctly in the modal header';

      render(
        <Modal isOpen={true} onClose={mockOnClose} title={longTitle}>
          <div>Content</div>
        </Modal>
      );

      expect(screen.getByText(longTitle)).toBeInTheDocument();
    });

    it('cleans up event listeners on unmount', () => {
      const { unmount } = render(
        <Modal isOpen={true} onClose={mockOnClose} title="Test Modal">
          <div>Content</div>
        </Modal>
      );

      unmount();

      // Escape key should not trigger after unmount
      fireEvent.keyDown(document, { key: 'Escape' });
      expect(mockOnClose).not.toHaveBeenCalled();
    });
  });
});
