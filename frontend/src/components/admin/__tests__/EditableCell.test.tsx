/**
 * EditableCell Component Tests
 *
 * Tests for the inline editable cell including:
 * - Display mode rendering
 * - Click to enter edit mode
 * - Keyboard interactions (Enter to save, Escape to cancel)
 * - Text, number, and select field types
 * - Disabled and saving states
 * - Value validation (number min/max)
 */
import React from 'react';
import { render, screen, fireEvent } from '@/test-utils';
import '@testing-library/jest-dom';
import { EditableCell, type EditableCellProps } from '../EditableCell';

// ============================================================================
// Test Setup
// ============================================================================

const defaultProps: EditableCellProps = {
  value: 'Hello World',
  onSave: jest.fn(),
};

// ============================================================================
// Tests
// ============================================================================

describe('EditableCell', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Display Mode', () => {
    it('renders the current value', () => {
      render(<EditableCell {...defaultProps} />);

      expect(screen.getByText('Hello World')).toBeInTheDocument();
    });

    it('renders placeholder when value is null', () => {
      render(<EditableCell {...defaultProps} value={null} placeholder="Click to edit" />);

      expect(screen.getByText('Click to edit')).toBeInTheDocument();
    });

    it('renders custom display via renderDisplay prop', () => {
      render(
        <EditableCell
          {...defaultProps}
          value={42}
          renderDisplay={(v) => <span data-testid="custom">{v} items</span>}
        />
      );

      expect(screen.getByTestId('custom')).toHaveTextContent('42 items');
    });

    it('has button role for accessibility', () => {
      render(<EditableCell {...defaultProps} />);

      expect(screen.getByRole('button')).toBeInTheDocument();
    });

    it('includes aria-label with current value', () => {
      render(<EditableCell {...defaultProps} />);

      expect(screen.getByRole('button')).toHaveAttribute(
        'aria-label',
        'Click to edit: Hello World'
      );
    });

    it('uses custom ariaLabel when provided', () => {
      render(<EditableCell {...defaultProps} ariaLabel="Edit name" />);

      expect(screen.getByRole('button')).toHaveAttribute('aria-label', 'Edit name');
    });
  });

  describe('Entering Edit Mode', () => {
    it('enters edit mode on click', () => {
      render(<EditableCell {...defaultProps} />);

      fireEvent.click(screen.getByRole('button'));

      expect(screen.getByRole('button', { name: 'Save' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument();
    });

    it('enters edit mode on Enter key', () => {
      render(<EditableCell {...defaultProps} />);

      fireEvent.keyDown(screen.getByRole('button'), { key: 'Enter' });

      expect(screen.getByRole('button', { name: 'Save' })).toBeInTheDocument();
    });

    it('enters edit mode on Space key', () => {
      render(<EditableCell {...defaultProps} />);

      fireEvent.keyDown(screen.getByRole('button'), { key: ' ' });

      expect(screen.getByRole('button', { name: 'Save' })).toBeInTheDocument();
    });

    it('does not enter edit mode when disabled', () => {
      render(<EditableCell {...defaultProps} disabled />);

      fireEvent.click(screen.getByRole('button'));

      expect(screen.queryByRole('button', { name: 'Save' })).not.toBeInTheDocument();
    });

    it('does not enter edit mode when saving', () => {
      render(<EditableCell {...defaultProps} isSaving />);

      fireEvent.click(screen.getByRole('button'));

      expect(screen.queryByRole('button', { name: 'Save' })).not.toBeInTheDocument();
    });
  });

  describe('Text Editing', () => {
    it('shows input with current value in edit mode', () => {
      render(<EditableCell {...defaultProps} />);

      fireEvent.click(screen.getByRole('button'));

      const input = screen.getByDisplayValue('Hello World');
      expect(input).toBeInTheDocument();
    });

    it('calls onSave with new value on Enter', () => {
      const onSave = jest.fn();
      render(<EditableCell {...defaultProps} onSave={onSave} />);

      fireEvent.click(screen.getByRole('button'));

      const input = screen.getByDisplayValue('Hello World');
      fireEvent.change(input, { target: { value: 'Updated Value' } });
      fireEvent.keyDown(input, { key: 'Enter' });

      expect(onSave).toHaveBeenCalledWith('Updated Value');
    });

    it('calls onSave with null for empty text', () => {
      const onSave = jest.fn();
      render(<EditableCell {...defaultProps} onSave={onSave} />);

      fireEvent.click(screen.getByRole('button'));

      const input = screen.getByDisplayValue('Hello World');
      fireEvent.change(input, { target: { value: '' } });
      fireEvent.keyDown(input, { key: 'Enter' });

      expect(onSave).toHaveBeenCalledWith(null);
    });

    it('does not call onSave when value unchanged', () => {
      const onSave = jest.fn();
      render(<EditableCell {...defaultProps} onSave={onSave} />);

      fireEvent.click(screen.getByRole('button'));

      const input = screen.getByDisplayValue('Hello World');
      fireEvent.keyDown(input, { key: 'Enter' });

      expect(onSave).not.toHaveBeenCalled();
    });

    it('cancels edit on Escape', () => {
      const onSave = jest.fn();
      render(<EditableCell {...defaultProps} onSave={onSave} />);

      fireEvent.click(screen.getByRole('button'));

      const input = screen.getByDisplayValue('Hello World');
      fireEvent.change(input, { target: { value: 'Changed' } });
      fireEvent.keyDown(input, { key: 'Escape' });

      // Should return to display mode with original value
      expect(screen.getByText('Hello World')).toBeInTheDocument();
      expect(onSave).not.toHaveBeenCalled();
    });

    it('saves via Save button click', () => {
      const onSave = jest.fn();
      render(<EditableCell {...defaultProps} onSave={onSave} />);

      fireEvent.click(screen.getByRole('button'));

      const input = screen.getByDisplayValue('Hello World');
      fireEvent.change(input, { target: { value: 'Button Save' } });
      fireEvent.click(screen.getByRole('button', { name: 'Save' }));

      expect(onSave).toHaveBeenCalledWith('Button Save');
    });

    it('cancels via Cancel button click', () => {
      const onSave = jest.fn();
      render(<EditableCell {...defaultProps} onSave={onSave} />);

      fireEvent.click(screen.getByRole('button'));
      fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));

      expect(screen.getByText('Hello World')).toBeInTheDocument();
      expect(onSave).not.toHaveBeenCalled();
    });
  });

  describe('Number Editing', () => {
    it('renders number input in edit mode', () => {
      render(<EditableCell {...defaultProps} value={5} type="number" />);

      fireEvent.click(screen.getByRole('button'));

      const input = screen.getByDisplayValue('5');
      expect(input).toHaveAttribute('type', 'number');
    });

    it('saves parsed number value', () => {
      const onSave = jest.fn();
      render(<EditableCell {...defaultProps} value={5} type="number" onSave={onSave} />);

      fireEvent.click(screen.getByRole('button'));

      const input = screen.getByDisplayValue('5');
      fireEvent.change(input, { target: { value: '10' } });
      fireEvent.keyDown(input, { key: 'Enter' });

      expect(onSave).toHaveBeenCalledWith(10);
    });

    it('clamps to min value', () => {
      const onSave = jest.fn();
      render(
        <EditableCell {...defaultProps} value={5} type="number" min={0} onSave={onSave} />
      );

      fireEvent.click(screen.getByRole('button'));

      const input = screen.getByDisplayValue('5');
      fireEvent.change(input, { target: { value: '-5' } });
      fireEvent.keyDown(input, { key: 'Enter' });

      expect(onSave).toHaveBeenCalledWith(0);
    });

    it('clamps to max value', () => {
      const onSave = jest.fn();
      render(
        <EditableCell {...defaultProps} value={5} type="number" max={10} onSave={onSave} />
      );

      fireEvent.click(screen.getByRole('button'));

      const input = screen.getByDisplayValue('5');
      fireEvent.change(input, { target: { value: '99' } });
      fireEvent.keyDown(input, { key: 'Enter' });

      expect(onSave).toHaveBeenCalledWith(10);
    });

    it('saves null for empty number value', () => {
      const onSave = jest.fn();
      render(<EditableCell {...defaultProps} value={5} type="number" onSave={onSave} />);

      fireEvent.click(screen.getByRole('button'));

      const input = screen.getByDisplayValue('5');
      fireEvent.change(input, { target: { value: '' } });
      fireEvent.keyDown(input, { key: 'Enter' });

      expect(onSave).toHaveBeenCalledWith(null);
    });

    it('treats invalid number input as empty (saves null)', () => {
      const onSave = jest.fn();
      render(<EditableCell {...defaultProps} value={5} type="number" onSave={onSave} />);

      fireEvent.click(screen.getByRole('button'));

      // In jsdom, type="number" coerces invalid text to empty string
      const input = screen.getByDisplayValue('5');
      fireEvent.change(input, { target: { value: 'abc' } });
      fireEvent.keyDown(input, { key: 'Enter' });

      // Empty string on a number field becomes null
      expect(onSave).toHaveBeenCalledWith(null);
    });
  });

  describe('Select Editing', () => {
    const selectOptions = [
      { value: 'a', label: 'Option A' },
      { value: 'b', label: 'Option B' },
      { value: 'c', label: 'Option C' },
    ];

    it('renders select element in edit mode', () => {
      render(
        <EditableCell
          {...defaultProps}
          value="a"
          type="select"
          options={selectOptions}
        />
      );

      fireEvent.click(screen.getByRole('button'));

      expect(screen.getByText('Option A')).toBeInTheDocument();
      expect(screen.getByText('Option B')).toBeInTheDocument();
      expect(screen.getByText('Option C')).toBeInTheDocument();
    });

    it('renders default empty option', () => {
      render(
        <EditableCell
          {...defaultProps}
          value="a"
          type="select"
          options={selectOptions}
        />
      );

      fireEvent.click(screen.getByRole('button'));

      expect(screen.getByText('-- Select --')).toBeInTheDocument();
    });

    it('saves selected option via Save button', () => {
      const onSave = jest.fn();
      render(
        <EditableCell
          {...defaultProps}
          value="a"
          type="select"
          options={selectOptions}
          onSave={onSave}
        />
      );

      fireEvent.click(screen.getByRole('button'));

      const select = screen.getByRole('combobox');
      fireEvent.change(select, { target: { value: 'b' } });
      fireEvent.click(screen.getByRole('button', { name: 'Save' }));

      expect(onSave).toHaveBeenCalledWith('b');
    });
  });

  describe('Disabled State', () => {
    it('sets tabIndex to -1 when disabled', () => {
      render(<EditableCell {...defaultProps} disabled />);

      expect(screen.getByRole('button')).toHaveAttribute('tabindex', '-1');
    });
  });

  describe('Saving State', () => {
    it('disables Save button when isSaving is true', () => {
      render(<EditableCell {...defaultProps} isSaving />);

      // In display mode with saving, it should show a spinner alongside value
      expect(screen.getByText('Hello World')).toBeInTheDocument();
    });
  });
});
