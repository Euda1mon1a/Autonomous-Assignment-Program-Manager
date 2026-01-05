/**
 * Tests for EditableCell component
 *
 * Tests click-to-edit functionality, keyboard navigation, and save/cancel behavior.
 */
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { EditableCell } from '@/components/admin/EditableCell';

describe('EditableCell', () => {
  const defaultProps = {
    value: 'Test Value',
    onSave: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Display Mode', () => {
    it('should render the current value', () => {
      render(<EditableCell {...defaultProps} />);
      expect(screen.getByText('Test Value')).toBeInTheDocument();
    });

    it('should render placeholder when value is null', () => {
      render(<EditableCell {...defaultProps} value={null} placeholder="Click to edit" />);
      expect(screen.getByText('Click to edit')).toBeInTheDocument();
    });

    it('should render custom display using renderDisplay', () => {
      render(
        <EditableCell
          {...defaultProps}
          renderDisplay={(val) => <span data-testid="custom">{val} (custom)</span>}
        />
      );
      expect(screen.getByTestId('custom')).toHaveTextContent('Test Value (custom)');
    });

    it('should be focusable with keyboard', () => {
      render(<EditableCell {...defaultProps} />);
      const cell = screen.getByRole('button');
      cell.focus();
      expect(cell).toHaveFocus();
    });

    it('should not be clickable when disabled', () => {
      render(<EditableCell {...defaultProps} disabled />);
      const cell = screen.getByRole('button');
      expect(cell).toHaveAttribute('tabIndex', '-1');
    });

    it('should apply custom className', () => {
      const { container } = render(<EditableCell {...defaultProps} className="custom-class" />);
      expect(container.querySelector('.custom-class')).toBeInTheDocument();
    });
  });

  describe('Edit Mode - Text Input', () => {
    it('should enter edit mode on click', async () => {
      const user = userEvent.setup();
      render(<EditableCell {...defaultProps} />);

      await user.click(screen.getByRole('button'));

      expect(screen.getByRole('textbox')).toBeInTheDocument();
    });

    it('should enter edit mode on Enter key', async () => {
      const user = userEvent.setup();
      render(<EditableCell {...defaultProps} />);

      const cell = screen.getByRole('button');
      cell.focus();
      await user.keyboard('{Enter}');

      expect(screen.getByRole('textbox')).toBeInTheDocument();
    });

    it('should pre-fill input with current value', async () => {
      const user = userEvent.setup();
      render(<EditableCell {...defaultProps} />);

      await user.click(screen.getByRole('button'));

      const input = screen.getByRole('textbox');
      expect(input).toHaveValue('Test Value');
    });

    it('should focus and select input on edit', async () => {
      const user = userEvent.setup();
      render(<EditableCell {...defaultProps} />);

      await user.click(screen.getByRole('button'));

      const input = screen.getByRole('textbox');
      await waitFor(() => {
        expect(input).toHaveFocus();
      });
    });

    it('should show save and cancel buttons', async () => {
      const user = userEvent.setup();
      render(<EditableCell {...defaultProps} />);

      await user.click(screen.getByRole('button'));

      expect(screen.getByRole('button', { name: /save/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
    });
  });

  describe('Edit Mode - Number Input', () => {
    it('should render number input for type="number"', async () => {
      const user = userEvent.setup();
      render(<EditableCell {...defaultProps} value={42} type="number" />);

      await user.click(screen.getByRole('button'));

      const input = screen.getByRole('spinbutton');
      expect(input).toHaveValue(42);
    });

    it('should respect min and max constraints', async () => {
      const user = userEvent.setup();
      const onSave = jest.fn();
      render(<EditableCell value={5} type="number" min={1} max={10} onSave={onSave} />);

      await user.click(screen.getByRole('button'));
      const input = screen.getByRole('spinbutton');

      // Clear and type value above max
      await user.clear(input);
      await user.type(input, '100');
      await user.click(screen.getByRole('button', { name: /save/i }));

      // Should clamp to max
      expect(onSave).toHaveBeenCalledWith(10);
    });

    it('should save null for empty number input', async () => {
      const user = userEvent.setup();
      const onSave = jest.fn();
      render(<EditableCell value={5} type="number" onSave={onSave} />);

      await user.click(screen.getByRole('button'));
      const input = screen.getByRole('spinbutton');

      await user.clear(input);
      await user.click(screen.getByRole('button', { name: /save/i }));

      expect(onSave).toHaveBeenCalledWith(null);
    });
  });

  describe('Edit Mode - Select Input', () => {
    const selectOptions = [
      { value: 'opt1', label: 'Option 1' },
      { value: 'opt2', label: 'Option 2' },
      { value: 'opt3', label: 'Option 3' },
    ];

    it('should render select for type="select"', async () => {
      const user = userEvent.setup();
      render(
        <EditableCell {...defaultProps} value="opt1" type="select" options={selectOptions} />
      );

      await user.click(screen.getByRole('button'));

      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });

    it('should show all options', async () => {
      const user = userEvent.setup();
      render(
        <EditableCell {...defaultProps} value="opt1" type="select" options={selectOptions} />
      );

      await user.click(screen.getByRole('button'));

      const select = screen.getByRole('combobox');
      expect(select).toContainHTML('Option 1');
      expect(select).toContainHTML('Option 2');
      expect(select).toContainHTML('Option 3');
    });

    it('should save selected value', async () => {
      const user = userEvent.setup();
      const onSave = jest.fn();
      render(
        <EditableCell value="opt1" type="select" options={selectOptions} onSave={onSave} />
      );

      await user.click(screen.getByRole('button'));
      await user.selectOptions(screen.getByRole('combobox'), 'opt2');
      await user.click(screen.getByRole('button', { name: /save/i }));

      expect(onSave).toHaveBeenCalledWith('opt2');
    });
  });

  describe('Save Behavior', () => {
    it('should call onSave when save button is clicked', async () => {
      const user = userEvent.setup();
      const onSave = jest.fn();
      render(<EditableCell value="old" onSave={onSave} />);

      await user.click(screen.getByRole('button'));
      await user.clear(screen.getByRole('textbox'));
      await user.type(screen.getByRole('textbox'), 'new value');
      await user.click(screen.getByRole('button', { name: /save/i }));

      expect(onSave).toHaveBeenCalledWith('new value');
    });

    it('should call onSave when Enter is pressed', async () => {
      const user = userEvent.setup();
      const onSave = jest.fn();
      render(<EditableCell value="old" onSave={onSave} />);

      await user.click(screen.getByRole('button'));
      await user.clear(screen.getByRole('textbox'));
      await user.type(screen.getByRole('textbox'), 'new value{Enter}');

      expect(onSave).toHaveBeenCalledWith('new value');
    });

    it('should not call onSave if value unchanged', async () => {
      const user = userEvent.setup();
      const onSave = jest.fn();
      render(<EditableCell value="same" onSave={onSave} />);

      await user.click(screen.getByRole('button'));
      await user.click(screen.getByRole('button', { name: /save/i }));

      expect(onSave).not.toHaveBeenCalled();
    });

    it('should trim whitespace from text values', async () => {
      const user = userEvent.setup();
      const onSave = jest.fn();
      render(<EditableCell value="old" onSave={onSave} />);

      await user.click(screen.getByRole('button'));
      await user.clear(screen.getByRole('textbox'));
      await user.type(screen.getByRole('textbox'), '  trimmed  ');
      await user.click(screen.getByRole('button', { name: /save/i }));

      expect(onSave).toHaveBeenCalledWith('trimmed');
    });

    it('should save null for empty text input', async () => {
      const user = userEvent.setup();
      const onSave = jest.fn();
      render(<EditableCell value="old" onSave={onSave} />);

      await user.click(screen.getByRole('button'));
      await user.clear(screen.getByRole('textbox'));
      await user.click(screen.getByRole('button', { name: /save/i }));

      expect(onSave).toHaveBeenCalledWith(null);
    });
  });

  describe('Cancel Behavior', () => {
    it('should cancel on Escape key', async () => {
      const user = userEvent.setup();
      const onSave = jest.fn();
      render(<EditableCell value="original" onSave={onSave} />);

      await user.click(screen.getByRole('button'));
      await user.clear(screen.getByRole('textbox'));
      await user.type(screen.getByRole('textbox'), 'changed');
      await user.keyboard('{Escape}');

      expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
      expect(screen.getByText('original')).toBeInTheDocument();
      expect(onSave).not.toHaveBeenCalled();
    });

    it('should cancel on cancel button click', async () => {
      const user = userEvent.setup();
      const onSave = jest.fn();
      render(<EditableCell value="original" onSave={onSave} />);

      await user.click(screen.getByRole('button'));
      await user.clear(screen.getByRole('textbox'));
      await user.type(screen.getByRole('textbox'), 'changed');
      await user.click(screen.getByRole('button', { name: /cancel/i }));

      expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
      expect(onSave).not.toHaveBeenCalled();
    });
  });

  describe('Loading State', () => {
    it('should show loading spinner in display mode when isSaving', () => {
      render(<EditableCell {...defaultProps} isSaving />);
      // Loader2 renders as an SVG, check for the container styling
      expect(screen.getByText('Test Value')).toBeInTheDocument();
    });

    it('should disable save button when isSaving', async () => {
      const user = userEvent.setup();
      render(<EditableCell {...defaultProps} isSaving />);

      // Can't enter edit mode when saving
      await user.click(screen.getByRole('button'));
      expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper aria-label in display mode', () => {
      render(<EditableCell {...defaultProps} ariaLabel="Edit template name" />);
      expect(screen.getByRole('button')).toHaveAttribute(
        'aria-label',
        'Edit template name'
      );
    });

    it('should have proper aria-label in edit mode', async () => {
      const user = userEvent.setup();
      render(<EditableCell {...defaultProps} ariaLabel="Edit template name" />);

      await user.click(screen.getByRole('button'));

      expect(screen.getByRole('textbox')).toHaveAttribute(
        'aria-label',
        'Edit template name'
      );
    });
  });
});
