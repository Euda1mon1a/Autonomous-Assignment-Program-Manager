/**
 * Tests for Alert Component
 * Component: Alert - Notification messages
 */

import React from 'react';
import { render, screen, fireEvent } from '@/test-utils';
import '@testing-library/jest-dom';
import { Alert } from '../Alert';

describe('Alert', () => {
  // Test: Rendering
  describe('Rendering', () => {
    it('renders with children', () => {
      render(<Alert>Alert message</Alert>);

      expect(screen.getByText('Alert message')).toBeInTheDocument();
    });

    it('renders with title', () => {
      render(
        <Alert title="Important">
          Alert message
        </Alert>
      );

      expect(screen.getByText('Important')).toBeInTheDocument();
      expect(screen.getByText('Alert message')).toBeInTheDocument();
    });

    it('renders without title', () => {
      render(<Alert>Alert message</Alert>);

      expect(screen.queryByRole('heading')).not.toBeInTheDocument();
    });

    it('has proper role attribute', () => {
      render(<Alert>Message</Alert>);

      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    it('renders dismiss button when dismissible', () => {
      const onDismiss = jest.fn();
      render(
        <Alert dismissible onDismiss={onDismiss}>
          Message
        </Alert>
      );

      expect(screen.getByLabelText('Dismiss')).toBeInTheDocument();
    });

    it('does not render dismiss button when not dismissible', () => {
      render(<Alert>Message</Alert>);

      expect(screen.queryByLabelText('Dismiss')).not.toBeInTheDocument();
    });
  });

  // Test: Variants
  describe('Variants', () => {
    it('renders info variant (default)', () => {
      const { container } = render(<Alert variant="info">Info message</Alert>);

      expect(container.querySelector('.bg-blue-50')).toBeInTheDocument();
    });

    it('renders success variant', () => {
      const { container } = render(<Alert variant="success">Success message</Alert>);

      expect(container.querySelector('.bg-green-50')).toBeInTheDocument();
    });

    it('renders warning variant', () => {
      const { container } = render(<Alert variant="warning">Warning message</Alert>);

      expect(container.querySelector('.bg-amber-50')).toBeInTheDocument();
    });

    it('renders error variant', () => {
      const { container } = render(<Alert variant="error">Error message</Alert>);

      expect(container.querySelector('.bg-red-50')).toBeInTheDocument();
    });

    it('renders correct icon for info variant', () => {
      render(<Alert variant="info">Info</Alert>);

      const alert = screen.getByRole('alert');
      expect(alert.querySelector('.text-blue-600')).toBeInTheDocument();
    });

    it('renders correct icon for success variant', () => {
      render(<Alert variant="success">Success</Alert>);

      const alert = screen.getByRole('alert');
      expect(alert.querySelector('.text-green-600')).toBeInTheDocument();
    });

    it('renders correct icon for warning variant', () => {
      render(<Alert variant="warning">Warning</Alert>);

      const alert = screen.getByRole('alert');
      expect(alert.querySelector('.text-amber-600')).toBeInTheDocument();
    });

    it('renders correct icon for error variant', () => {
      render(<Alert variant="error">Error</Alert>);

      const alert = screen.getByRole('alert');
      expect(alert.querySelector('.text-red-600')).toBeInTheDocument();
    });
  });

  // Test: Interaction
  describe('Interaction', () => {
    it('calls onDismiss when dismiss button clicked', () => {
      const onDismiss = jest.fn();
      render(
        <Alert dismissible onDismiss={onDismiss}>
          Message
        </Alert>
      );

      fireEvent.click(screen.getByLabelText('Dismiss'));

      expect(onDismiss).toHaveBeenCalledTimes(1);
    });

    it('dismiss button is keyboard accessible', () => {
      const onDismiss = jest.fn();
      render(
        <Alert dismissible onDismiss={onDismiss}>
          Message
        </Alert>
      );

      const dismissButton = screen.getByLabelText('Dismiss');
      dismissButton.focus();

      expect(dismissButton).toHaveFocus();
    });
  });

  // Test: Edge cases
  describe('Edge Cases', () => {
    it('applies custom className', () => {
      const { container } = render(
        <Alert className="custom-class">Message</Alert>
      );

      expect(container.querySelector('.custom-class')).toBeInTheDocument();
    });

    it('handles long messages', () => {
      const longMessage = 'This is a very long alert message that should still display correctly in the alert component and wrap if necessary without breaking the layout or causing overflow issues.';

      render(<Alert>{longMessage}</Alert>);

      expect(screen.getByText(longMessage)).toBeInTheDocument();
    });

    it('handles long titles', () => {
      const longTitle = 'This is a very long title that should still render correctly';

      render(
        <Alert title={longTitle}>
          Message
        </Alert>
      );

      expect(screen.getByText(longTitle)).toBeInTheDocument();
    });

    it('renders complex children', () => {
      render(
        <Alert>
          <div>
            <strong>Bold text</strong> and <em>italic text</em>
          </div>
        </Alert>
      );

      expect(screen.getByText('Bold text')).toBeInTheDocument();
      expect(screen.getByText('italic text')).toBeInTheDocument();
    });

    it('renders with both title and dismiss button', () => {
      const onDismiss = jest.fn();
      render(
        <Alert title="Title" dismissible onDismiss={onDismiss}>
          Message
        </Alert>
      );

      expect(screen.getByText('Title')).toBeInTheDocument();
      expect(screen.getByLabelText('Dismiss')).toBeInTheDocument();
    });

    it('does not render dismiss button when dismissible but no onDismiss', () => {
      render(
        <Alert dismissible>
          Message
        </Alert>
      );

      expect(screen.queryByLabelText('Dismiss')).not.toBeInTheDocument();
    });
  });
});
