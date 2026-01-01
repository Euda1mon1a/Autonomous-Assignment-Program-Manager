/**
 * Tests for EmptyState Component
 * Component: EmptyState - Empty state placeholder
 */

import React from 'react';
import { render, screen, fireEvent } from '@/test-utils';
import '@testing-library/jest-dom';
import { EmptyState } from '../EmptyState';
import { Inbox } from 'lucide-react';

describe('EmptyState', () => {
  // Test: Rendering
  describe('Rendering', () => {
    it('renders with title', () => {
      render(<EmptyState title="No items found" />);

      expect(screen.getByText('No items found')).toBeInTheDocument();
    });

    it('renders with description', () => {
      render(
        <EmptyState
          title="No items"
          description="There are no items to display."
        />
      );

      expect(screen.getByText('There are no items to display.')).toBeInTheDocument();
    });

    it('renders without description', () => {
      render(<EmptyState title="No items" />);

      expect(screen.queryByText(/There are/)).not.toBeInTheDocument();
    });

    it('renders with icon', () => {
      const { container } = render(
        <EmptyState
          icon={Inbox}
          title="Empty inbox"
        />
      );

      const iconWrapper = container.querySelector('.bg-gray-100');
      expect(iconWrapper).toBeInTheDocument();
    });

    it('renders without icon', () => {
      const { container } = render(<EmptyState title="No items" />);

      const iconWrapper = container.querySelector('.bg-gray-100');
      expect(iconWrapper).not.toBeInTheDocument();
    });

    it('renders with action button', () => {
      const action = { label: 'Add item', onClick: jest.fn() };
      render(
        <EmptyState
          title="No items"
          action={action}
        />
      );

      expect(screen.getByText('Add item')).toBeInTheDocument();
    });

    it('renders without action button', () => {
      render(<EmptyState title="No items" />);

      expect(screen.queryByRole('button')).not.toBeInTheDocument();
    });

    it('renders children', () => {
      render(
        <EmptyState title="No items">
          <div>Custom content</div>
        </EmptyState>
      );

      expect(screen.getByText('Custom content')).toBeInTheDocument();
    });
  });

  // Test: Interaction
  describe('Interaction', () => {
    it('calls action onClick when button clicked', () => {
      const onClick = jest.fn();
      const action = { label: 'Add item', onClick };

      render(
        <EmptyState
          title="No items"
          action={action}
        />
      );

      fireEvent.click(screen.getByText('Add item'));
      expect(onClick).toHaveBeenCalledTimes(1);
    });

    it('action button is keyboard accessible', () => {
      const action = { label: 'Add item', onClick: jest.fn() };

      render(
        <EmptyState
          title="No items"
          action={action}
        />
      );

      const button = screen.getByText('Add item');
      button.focus();
      expect(button).toHaveFocus();
    });
  });

  // Test: Layout and styling
  describe('Layout and Styling', () => {
    it('centers content', () => {
      const { container } = render(<EmptyState title="No items" />);

      expect(container.querySelector('.flex.flex-col.items-center.justify-center')).toBeInTheDocument();
    });

    it('has proper padding', () => {
      const { container } = render(<EmptyState title="No items" />);

      expect(container.querySelector('.py-12.px-4')).toBeInTheDocument();
    });

    it('has text-center class', () => {
      const { container } = render(<EmptyState title="No items" />);

      expect(container.querySelector('.text-center')).toBeInTheDocument();
    });

    it('renders icon in circular background', () => {
      const { container } = render(
        <EmptyState
          icon={Inbox}
          title="Empty"
        />
      );

      expect(container.querySelector('.rounded-full.bg-gray-100')).toBeInTheDocument();
    });

    it('icon has proper sizing', () => {
      const { container } = render(
        <EmptyState
          icon={Inbox}
          title="Empty"
        />
      );

      const iconWrapper = container.querySelector('.w-16.h-16');
      expect(iconWrapper).toBeInTheDocument();
    });

    it('title has proper styling', () => {
      render(<EmptyState title="No items" />);

      const title = screen.getByText('No items');
      expect(title).toHaveClass('text-lg', 'font-medium', 'text-gray-900');
    });

    it('description has proper styling', () => {
      render(
        <EmptyState
          title="No items"
          description="Add your first item to get started."
        />
      );

      const description = screen.getByText('Add your first item to get started.');
      expect(description).toHaveClass('text-sm', 'text-gray-500');
    });

    it('action button has btn-primary class', () => {
      const action = { label: 'Add item', onClick: jest.fn() };
      render(
        <EmptyState
          title="No items"
          action={action}
        />
      );

      const button = screen.getByText('Add item');
      expect(button).toHaveClass('btn-primary');
    });
  });

  // Test: Edge cases
  describe('Edge Cases', () => {
    it('handles long titles', () => {
      const longTitle = 'This is a very long title that should still display correctly in the empty state component';
      render(<EmptyState title={longTitle} />);

      expect(screen.getByText(longTitle)).toBeInTheDocument();
    });

    it('handles long descriptions', () => {
      const longDescription = 'This is a very long description that provides detailed information about why there are no items and what the user should do next to resolve this empty state.';
      render(
        <EmptyState
          title="No items"
          description={longDescription}
        />
      );

      expect(screen.getByText(longDescription)).toBeInTheDocument();
    });

    it('description has max-width for readability', () => {
      const { container } = render(
        <EmptyState
          title="No items"
          description="Description text"
        />
      );

      expect(container.querySelector('.max-w-sm')).toBeInTheDocument();
    });

    it('renders with all props combined', () => {
      const action = { label: 'Add item', onClick: jest.fn() };

      render(
        <EmptyState
          icon={Inbox}
          title="No items"
          description="Get started by adding your first item."
          action={action}
        >
          <div>Extra content</div>
        </EmptyState>
      );

      expect(screen.getByText('No items')).toBeInTheDocument();
      expect(screen.getByText('Get started by adding your first item.')).toBeInTheDocument();
      expect(screen.getByText('Add item')).toBeInTheDocument();
      expect(screen.getByText('Extra content')).toBeInTheDocument();
    });

    it('renders children below action button', () => {
      const action = { label: 'Add item', onClick: jest.fn() };
      const { container } = render(
        <EmptyState
          title="No items"
          action={action}
        >
          <div>Custom content</div>
        </EmptyState>
      );

      const button = screen.getByText('Add item');
      const customContent = screen.getByText('Custom content');

      // Custom content should be after the button in DOM order
      expect(button.compareDocumentPosition(customContent)).toBe(Node.DOCUMENT_POSITION_FOLLOWING);
    });
  });
});
