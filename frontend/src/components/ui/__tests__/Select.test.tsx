/**
 * Tests for Select Component
 * Component: 33 - Custom dropdown
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Select, SelectOption } from '../Select';

describe('Select', () => {
  const mockOptions: SelectOption[] = [
    { value: 'option1', label: 'Option 1' },
    { value: 'option2', label: 'Option 2' },
    { value: 'option3', label: 'Option 3' },
    { value: 'disabled', label: 'Disabled Option', disabled: true },
  ];

  const mockOnChange = jest.fn();

  beforeEach(() => {
    mockOnChange.mockClear();
  });

  // Test 33.1: Render test
  describe('Rendering', () => {
    it('renders with placeholder', () => {
      render(<Select options={mockOptions} onChange={mockOnChange} placeholder="Choose option" />);

      expect(screen.getByText('Choose option')).toBeInTheDocument();
    });

    it('renders with selected value', () => {
      render(<Select options={mockOptions} value="option1" onChange={mockOnChange} />);

      expect(screen.getByText('Option 1')).toBeInTheDocument();
    });

    it('renders with label', () => {
      render(<Select options={mockOptions} onChange={mockOnChange} label="Select Option" />);

      expect(screen.getByText('Select Option')).toBeInTheDocument();
    });

    it('shows required indicator when required', () => {
      render(<Select options={mockOptions} onChange={mockOnChange} label="Field" required />);

      expect(screen.getByText('*')).toBeInTheDocument();
    });

    it('displays error message', () => {
      render(<Select options={mockOptions} onChange={mockOnChange} error="This field is required" />);

      expect(screen.getByText('This field is required')).toBeInTheDocument();
    });
  });

  // Test 33.2: Interaction and selection
  describe('Selection Behavior', () => {
    it('opens dropdown on button click', () => {
      render(<Select options={mockOptions} onChange={mockOnChange} />);

      const button = screen.getByRole('button');
      fireEvent.click(button);

      expect(screen.getByText('Option 1')).toBeInTheDocument();
      expect(screen.getByText('Option 2')).toBeInTheDocument();
      expect(screen.getByText('Option 3')).toBeInTheDocument();
    });

    it('selects an option when clicked', () => {
      render(<Select options={mockOptions} onChange={mockOnChange} />);

      // Open dropdown
      fireEvent.click(screen.getByRole('button'));

      // Click an option
      const option2 = screen.getByText('Option 2');
      fireEvent.click(option2);

      expect(mockOnChange).toHaveBeenCalledWith('option2');
    });

    it('closes dropdown after selection', async () => {
      render(<Select options={mockOptions} onChange={mockOnChange} />);

      // Open dropdown
      fireEvent.click(screen.getByRole('button'));

      // Select an option
      fireEvent.click(screen.getByText('Option 2'));

      await waitFor(() => {
        // Options should not be visible anymore
        const allOption1 = screen.queryAllByText('Option 1');
        expect(allOption1.length).toBe(0);
      });
    });

    it('prevents selection of disabled options', () => {
      render(<Select options={mockOptions} onChange={mockOnChange} />);

      // Open dropdown
      fireEvent.click(screen.getByRole('button'));

      // Try to click disabled option
      const disabledOption = screen.getByText('Disabled Option').closest('button');
      expect(disabledOption).toBeDisabled();

      fireEvent.click(disabledOption!);

      expect(mockOnChange).not.toHaveBeenCalled();
    });

    it('shows checkmark on selected option', () => {
      render(<Select options={mockOptions} value="option2" onChange={mockOnChange} />);

      // Open dropdown
      fireEvent.click(screen.getByRole('button'));

      // Find the checkmark
      expect(screen.getByText('✓')).toBeInTheDocument();
    });

    it('rotates arrow icon when open', () => {
      const { container } = render(<Select options={mockOptions} onChange={mockOnChange} />);

      const button = screen.getByRole('button');
      const arrow = container.querySelector('.rotate-180');

      expect(arrow).not.toBeInTheDocument();

      fireEvent.click(button);

      const rotatedArrow = container.querySelector('.rotate-180');
      expect(rotatedArrow).toBeInTheDocument();
    });
  });

  // Test 33.3: Accessibility and keyboard navigation
  describe('Accessibility', () => {
    it('trigger button is keyboard accessible', () => {
      render(<Select options={mockOptions} onChange={mockOnChange} />);

      const button = screen.getByRole('button');
      button.focus();

      expect(button).toHaveFocus();
    });

    it('closes dropdown on Escape key', async () => {
      render(<Select options={mockOptions} onChange={mockOnChange} />);

      // Open dropdown
      const button = screen.getByRole('button');
      fireEvent.click(button);

      expect(screen.getByText('Option 1')).toBeInTheDocument();

      // Press Escape
      fireEvent.keyDown(button, { key: 'Escape' });

      await waitFor(() => {
        const allOption1 = screen.queryAllByText('Option 1');
        expect(allOption1.length).toBe(0);
      });
    });

    it('closes dropdown when clicking outside', async () => {
      render(
        <div>
          <div data-testid="outside">Outside</div>
          <Select options={mockOptions} onChange={mockOnChange} />
        </div>
      );

      // Open dropdown
      fireEvent.click(screen.getByRole('button'));

      // Click outside
      fireEvent.mouseDown(screen.getByTestId('outside'));

      await waitFor(() => {
        const allOption1 = screen.queryAllByText('Option 1');
        expect(allOption1.length).toBe(0);
      });
    });

    it('disabled state prevents interaction', () => {
      render(<Select options={mockOptions} onChange={mockOnChange} disabled />);

      const button = screen.getByRole('button');
      expect(button).toBeDisabled();

      fireEvent.click(button);

      expect(screen.queryByText('Option 1')).not.toBeInTheDocument();
    });

    it('applies error styling when error prop provided', () => {
      const { container } = render(
        <Select options={mockOptions} onChange={mockOnChange} error="Error message" />
      );

      const button = container.querySelector('.border-red-500');
      expect(button).toBeInTheDocument();
    });
  });

  // Test 33.4: Searchable functionality and edge cases
  describe('Searchable Functionality', () => {
    it('renders search input when searchable', () => {
      render(<Select options={mockOptions} onChange={mockOnChange} searchable />);

      fireEvent.click(screen.getByRole('button'));

      expect(screen.getByPlaceholderText('Search...')).toBeInTheDocument();
    });

    it('filters options based on search query', () => {
      render(<Select options={mockOptions} onChange={mockOnChange} searchable />);

      fireEvent.click(screen.getByRole('button'));

      const searchInput = screen.getByPlaceholderText('Search...');
      fireEvent.change(searchInput, { target: { value: 'Option 2' } });

      expect(screen.getByText('Option 2')).toBeInTheDocument();
      expect(screen.queryByText('Option 1')).not.toBeInTheDocument();
    });

    it('shows "No options found" when search has no results', () => {
      render(<Select options={mockOptions} onChange={mockOnChange} searchable />);

      fireEvent.click(screen.getByRole('button'));

      const searchInput = screen.getByPlaceholderText('Search...');
      fireEvent.change(searchInput, { target: { value: 'nonexistent' } });

      expect(screen.getByText('No options found')).toBeInTheDocument();
    });

    it('focuses search input when opening searchable select', () => {
      render(<Select options={mockOptions} onChange={mockOnChange} searchable />);

      fireEvent.click(screen.getByRole('button'));

      const searchInput = screen.getByPlaceholderText('Search...');
      expect(searchInput).toHaveFocus();
    });

    it('clears search query when closing dropdown', async () => {
      render(<Select options={mockOptions} onChange={mockOnChange} searchable />);

      // Open and search
      fireEvent.click(screen.getByRole('button'));
      const searchInput = screen.getByPlaceholderText('Search...');
      fireEvent.change(searchInput, { target: { value: 'Option 2' } });

      // Select an option
      fireEvent.click(screen.getByText('Option 2'));

      // Reopen
      fireEvent.click(screen.getByRole('button'));

      // Search input should be empty
      const newSearchInput = screen.getByPlaceholderText('Search...');
      expect(newSearchInput).toHaveValue('');
    });
  });

  describe('Edge Cases', () => {
    it('handles empty options array', () => {
      render(<Select options={[]} onChange={mockOnChange} />);

      fireEvent.click(screen.getByRole('button'));

      expect(screen.getByText('No options found')).toBeInTheDocument();
    });

    it('applies custom className', () => {
      const { container } = render(
        <Select options={mockOptions} onChange={mockOnChange} className="custom-class" />
      );

      expect(container.querySelector('.select-component.custom-class')).toBeInTheDocument();
    });

    it('displays all options in dropdown', () => {
      render(<Select options={mockOptions} onChange={mockOnChange} />);

      fireEvent.click(screen.getByRole('button'));

      mockOptions.forEach(option => {
        expect(screen.getByText(option.label)).toBeInTheDocument();
      });
    });

    it('handles long option lists with scrolling', () => {
      const manyOptions: SelectOption[] = Array.from({ length: 50 }, (_, i) => ({
        value: `option${i}`,
        label: `Option ${i}`,
      }));

      const { container } = render(<Select options={manyOptions} onChange={mockOnChange} />);

      fireEvent.click(screen.getByRole('button'));

      const dropdown = container.querySelector('.overflow-y-auto.max-h-52');
      expect(dropdown).toBeInTheDocument();
    });
  });
});
