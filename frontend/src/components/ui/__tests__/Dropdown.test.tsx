import { renderWithProviders } from '@/test-utils';
/**
 * Tests for Dropdown Component
 * Component: 38 - Dropdown menu
 */

import React from 'react';
import { renderWithProviders as render, screen, fireEvent, waitFor } from '@/test-utils';
import '@testing-library/jest-dom';
import { Dropdown, DropdownItem } from '../Dropdown';

describe('Dropdown', () => {
  const mockItems: DropdownItem[] = [
    { label: 'Edit', value: 'edit' },
    { label: 'Duplicate', value: 'duplicate' },
    { label: 'Archive', value: 'archive' },
    { label: 'Delete', value: 'delete', danger: true },
    { label: 'Disabled', value: 'disabled', disabled: true },
  ];

  const mockOnSelect = jest.fn();

  beforeEach(() => {
    mockOnSelect.mockClear();
  });

  // Test 38.1: Render test
  describe('Rendering', () => {
    it('renders with trigger', () => {
      render(
        <Dropdown
          trigger={<button>Actions</button>}
          items={mockItems}
          onSelect={mockOnSelect}
        />
      );

      expect(screen.getByText('Actions')).toBeInTheDocument();
    });

    it('does not show menu initially', () => {
      render(
        <Dropdown
          trigger={<button>Actions</button>}
          items={mockItems}
          onSelect={mockOnSelect}
        />
      );

      expect(screen.queryByText('Edit')).not.toBeInTheDocument();
    });

    it('shows menu when trigger clicked', () => {
      render(
        <Dropdown
          trigger={<button>Actions</button>}
          items={mockItems}
          onSelect={mockOnSelect}
        />
      );

      fireEvent.click(screen.getByText('Actions'));

      expect(screen.getByText('Edit')).toBeInTheDocument();
      expect(screen.getByText('Duplicate')).toBeInTheDocument();
      expect(screen.getByText('Archive')).toBeInTheDocument();
    });

    it('renders menu items with proper role', () => {
      render(
        <Dropdown
          trigger={<button>Actions</button>}
          items={mockItems}
          onSelect={mockOnSelect}
        />
      );

      fireEvent.click(screen.getByText('Actions'));

      const menu = screen.getByRole('menu');
      expect(menu).toBeInTheDocument();

      const menuItems = screen.getAllByRole('menuitem');
      expect(menuItems).toHaveLength(mockItems.length);
    });
  });

  // Test 38.2: Item variants and selection
  describe('Item Variants and Selection', () => {
    it('calls onSelect when item clicked', () => {
      render(
        <Dropdown
          trigger={<button>Actions</button>}
          items={mockItems}
          onSelect={mockOnSelect}
        />
      );

      fireEvent.click(screen.getByText('Actions'));
      fireEvent.click(screen.getByText('Edit'));

      expect(mockOnSelect).toHaveBeenCalledWith('edit');
    });

    it('closes menu after selection', async () => {
      render(
        <Dropdown
          trigger={<button>Actions</button>}
          items={mockItems}
          onSelect={mockOnSelect}
        />
      );

      fireEvent.click(screen.getByText('Actions'));
      fireEvent.click(screen.getByText('Edit'));

      await waitFor(() => {
        expect(screen.queryByText('Edit')).not.toBeInTheDocument();
      });
    });

    it('applies danger styling to danger items', () => {
      render(
        <Dropdown
          trigger={<button>Actions</button>}
          items={mockItems}
          onSelect={mockOnSelect}
        />
      );

      fireEvent.click(screen.getByText('Actions'));

      const deleteButton = screen.getByText('Delete').closest('button');
      expect(deleteButton).toHaveClass('text-red-600');
    });

    it('disables disabled items', () => {
      render(
        <Dropdown
          trigger={<button>Actions</button>}
          items={mockItems}
          onSelect={mockOnSelect}
        />
      );

      fireEvent.click(screen.getByText('Actions'));

      const disabledButton = screen.getByText('Disabled').closest('button');
      expect(disabledButton).toBeDisabled();
    });

    it('does not call onSelect for disabled items', () => {
      render(
        <Dropdown
          trigger={<button>Actions</button>}
          items={mockItems}
          onSelect={mockOnSelect}
        />
      );

      fireEvent.click(screen.getByText('Actions'));
      fireEvent.click(screen.getByText('Disabled'));

      expect(mockOnSelect).not.toHaveBeenCalled();
    });

    it('renders items with icons', () => {
      const itemsWithIcons: DropdownItem[] = [
        { label: 'Edit', value: 'edit', icon: <span>✏️</span> },
        { label: 'Delete', value: 'delete', icon: <span>🗑️</span> },
      ];

      render(
        <Dropdown
          trigger={<button>Actions</button>}
          items={itemsWithIcons}
          onSelect={mockOnSelect}
        />
      );

      fireEvent.click(screen.getByText('Actions'));

      expect(screen.getByText('✏️')).toBeInTheDocument();
      expect(screen.getByText('🗑️')).toBeInTheDocument();
    });
  });

  // Test 38.3: Accessibility and keyboard navigation
  describe('Accessibility and Keyboard Navigation', () => {
    it('closes menu on Escape key', async () => {
      render(
        <Dropdown
          trigger={<button>Actions</button>}
          items={mockItems}
          onSelect={mockOnSelect}
        />
      );

      fireEvent.click(screen.getByText('Actions'));
      expect(screen.getByText('Edit')).toBeInTheDocument();

      fireEvent.keyDown(document, { key: 'Escape' });

      await waitFor(() => {
        expect(screen.queryByText('Edit')).not.toBeInTheDocument();
      });
    });

    it('navigates with Arrow Down key', () => {
      render(
        <Dropdown
          trigger={<button>Actions</button>}
          items={mockItems}
          onSelect={mockOnSelect}
        />
      );

      fireEvent.click(screen.getByText('Actions'));

      fireEvent.keyDown(document, { key: 'ArrowDown' });

      // First item should be highlighted
      const firstItem = screen.getByText('Edit').closest('button');
      expect(firstItem).toHaveClass('bg-gray-100');
    });

    it('navigates with Arrow Up key', () => {
      render(
        <Dropdown
          trigger={<button>Actions</button>}
          items={mockItems}
          onSelect={mockOnSelect}
        />
      );

      fireEvent.click(screen.getByText('Actions'));

      fireEvent.keyDown(document, { key: 'ArrowUp' });

      // Focus should not go below 0
      expect(mockOnSelect).not.toHaveBeenCalled();
    });

    it('selects item with Enter key', () => {
      render(
        <Dropdown
          trigger={<button>Actions</button>}
          items={mockItems}
          onSelect={mockOnSelect}
        />
      );

      fireEvent.click(screen.getByText('Actions'));
      fireEvent.keyDown(document, { key: 'Enter' });

      expect(mockOnSelect).toHaveBeenCalledWith('edit');
    });

    it('selects item with Space key', () => {
      render(
        <Dropdown
          trigger={<button>Actions</button>}
          items={mockItems}
          onSelect={mockOnSelect}
        />
      );

      fireEvent.click(screen.getByText('Actions'));
      fireEvent.keyDown(document, { key: ' ' });

      expect(mockOnSelect).toHaveBeenCalledWith('edit');
    });

    it('closes on outside click', async () => {
      render(
        <div>
          <div data-testid="outside">Outside</div>
          <Dropdown
            trigger={<button>Actions</button>}
            items={mockItems}
            onSelect={mockOnSelect}
          />
        </div>
      );

      fireEvent.click(screen.getByText('Actions'));
      expect(screen.getByText('Edit')).toBeInTheDocument();

      fireEvent.mouseDown(screen.getByTestId('outside'));

      await waitFor(() => {
        expect(screen.queryByText('Edit')).not.toBeInTheDocument();
      });
    });
  });

  // Test 38.4: Alignment and edge cases
  describe('Alignment and Edge Cases', () => {
    it('aligns menu to left by default', () => {
      const { container } = render(
        <Dropdown
          trigger={<button>Actions</button>}
          items={mockItems}
          onSelect={mockOnSelect}
        />
      );

      fireEvent.click(screen.getByText('Actions'));

      const menu = container.querySelector('.left-0');
      expect(menu).toBeInTheDocument();
    });

    it('aligns menu to right when specified', () => {
      const { container } = render(
        <Dropdown
          trigger={<button>Actions</button>}
          items={mockItems}
          onSelect={mockOnSelect}
          align="right"
        />
      );

      fireEvent.click(screen.getByText('Actions'));

      const menu = container.querySelector('.right-0');
      expect(menu).toBeInTheDocument();
    });

    it('handles empty items array', () => {
      render(
        <Dropdown
          trigger={<button>Actions</button>}
          items={[]}
          onSelect={mockOnSelect}
        />
      );

      fireEvent.click(screen.getByText('Actions'));

      const menu = screen.queryByRole('menu');
      expect(menu).toBeInTheDocument();
    });

    it('applies custom className', () => {
      const { container } = render(
        <Dropdown
          trigger={<button>Actions</button>}
          items={mockItems}
          onSelect={mockOnSelect}
          className="custom-dropdown"
        />
      );

      expect(container.querySelector('.custom-dropdown')).toBeInTheDocument();
    });

    it('updates focused item on mouse enter', () => {
      render(
        <Dropdown
          trigger={<button>Actions</button>}
          items={mockItems}
          onSelect={mockOnSelect}
        />
      );

      fireEvent.click(screen.getByText('Actions'));

      const duplicateButton = screen.getByText('Duplicate').closest('button');
      fireEvent.mouseEnter(duplicateButton!);

      expect(duplicateButton).toHaveClass('bg-gray-100');
    });
  });
});
