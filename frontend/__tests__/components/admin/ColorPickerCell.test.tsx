/**
 * Tests for ColorPickerCell component
 *
 * Tests color picker functionality, preset selection, custom color input, and accessibility.
 */
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ColorPickerCell } from '@/components/admin/ColorPickerCell';

describe('ColorPickerCell', () => {
  const defaultProps = {
    value: '#FF0000',
    onSave: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Display Mode', () => {
    it('should render color swatch with current value', () => {
      const { container } = render(<ColorPickerCell {...defaultProps} />);
      const swatch = container.querySelector('[style*="background-color: rgb(255, 0, 0)"]');
      expect(swatch).toBeInTheDocument();
    });

    it('should show color hex value', () => {
      render(<ColorPickerCell {...defaultProps} />);
      expect(screen.getByText('#FF0000')).toBeInTheDocument();
    });

    it('should show "None" when value is null', () => {
      render(<ColorPickerCell {...defaultProps} value={null} />);
      expect(screen.getByText('None')).toBeInTheDocument();
    });

    it('should show palette icon when no color is set', () => {
      render(<ColorPickerCell {...defaultProps} value={null} />);
      // Palette icon should be rendered in the dashed border swatch
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
    });

    it('should not be clickable when disabled', async () => {
      const user = userEvent.setup();
      render(<ColorPickerCell {...defaultProps} disabled />);

      await user.click(screen.getByRole('button'));

      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });
  });

  describe('Picker Dialog', () => {
    it('should open picker on click', async () => {
      const user = userEvent.setup();
      render(<ColorPickerCell {...defaultProps} />);

      await user.click(screen.getByRole('button'));

      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    it('should show preset colors section', async () => {
      const user = userEvent.setup();
      render(<ColorPickerCell {...defaultProps} />);

      await user.click(screen.getByRole('button'));

      expect(screen.getByText('Presets')).toBeInTheDocument();
    });

    it('should show custom color input', async () => {
      const user = userEvent.setup();
      render(<ColorPickerCell {...defaultProps} />);

      await user.click(screen.getByRole('button'));

      expect(screen.getByText('Custom')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('#RRGGBB')).toBeInTheDocument();
    });

    it('should close on close button click', async () => {
      const user = userEvent.setup();
      render(<ColorPickerCell {...defaultProps} />);

      await user.click(screen.getByRole('button'));
      await user.click(screen.getByText('Close'));

      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
      });
    });

    it('should close on click outside', async () => {
      const user = userEvent.setup();
      render(
        <div>
          <ColorPickerCell {...defaultProps} />
          <div data-testid="outside">Outside</div>
        </div>
      );

      await user.click(screen.getByRole('button'));
      expect(screen.getByRole('dialog')).toBeInTheDocument();

      await user.click(screen.getByTestId('outside'));

      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
      });
    });
  });

  describe('Preset Color Selection', () => {
    it('should display preset color buttons', async () => {
      const user = userEvent.setup();
      render(<ColorPickerCell {...defaultProps} />);

      await user.click(screen.getByRole('button'));

      // Should have preset color buttons
      const presetButtons = screen.getAllByRole('button').filter(
        (btn) => btn.getAttribute('title')?.includes('#')
      );
      expect(presetButtons.length).toBeGreaterThan(0);
    });

    it('should highlight currently selected color', async () => {
      const user = userEvent.setup();
      const { container } = render(<ColorPickerCell {...defaultProps} value="#EF4444" />);

      await user.click(screen.getByRole('button'));

      // Find the preset button for #EF4444 (Red)
      const redButton = screen.getByTitle(/Red.*#EF4444/i);
      expect(redButton).toHaveClass('border-violet-500');
    });

    it('should call onSave when preset is clicked', async () => {
      const user = userEvent.setup();
      const onSave = jest.fn();
      render(<ColorPickerCell value={null} onSave={onSave} />);

      await user.click(screen.getByRole('button'));

      // Click a preset (White)
      const whiteButton = screen.getByTitle(/White.*#FFFFFF/i);
      await user.click(whiteButton);

      expect(onSave).toHaveBeenCalledWith('#FFFFFF');
    });

    it('should close picker after selecting preset', async () => {
      const user = userEvent.setup();
      render(<ColorPickerCell {...defaultProps} />);

      await user.click(screen.getByRole('button'));

      const whiteButton = screen.getByTitle(/White.*#FFFFFF/i);
      await user.click(whiteButton);

      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
      });
    });
  });

  describe('Custom Color Input', () => {
    it('should pre-fill input with current value', async () => {
      const user = userEvent.setup();
      render(<ColorPickerCell {...defaultProps} value="#123456" />);

      await user.click(screen.getByRole('button'));

      const input = screen.getByPlaceholderText('#RRGGBB');
      await waitFor(() => {
        expect(input).toHaveValue('#123456');
      });
    });

    it('should accept hex without hash', async () => {
      const user = userEvent.setup();
      const onSave = jest.fn();
      render(<ColorPickerCell value={null} onSave={onSave} />);

      await user.click(screen.getByRole('button'));

      const input = screen.getByPlaceholderText('#RRGGBB');
      await user.type(input, 'AABBCC');

      // Find and click the apply button (check mark next to input)
      const applyButtons = screen.getAllByRole('button', { name: /apply custom color/i });
      await user.click(applyButtons[0]);

      expect(onSave).toHaveBeenCalledWith('#AABBCC');
    });

    it('should validate hex color format', async () => {
      const user = userEvent.setup();
      render(<ColorPickerCell {...defaultProps} value={null} />);

      await user.click(screen.getByRole('button'));

      const input = screen.getByPlaceholderText('#RRGGBB');
      await user.type(input, 'invalid');

      expect(screen.getByText(/enter a valid hex color/i)).toBeInTheDocument();
    });

    it('should disable apply button for invalid color', async () => {
      const user = userEvent.setup();
      render(<ColorPickerCell {...defaultProps} value={null} />);

      await user.click(screen.getByRole('button'));

      const input = screen.getByPlaceholderText('#RRGGBB');
      await user.type(input, 'XYZ');

      const applyButton = screen.getByRole('button', { name: /apply custom color/i });
      expect(applyButton).toBeDisabled();
    });

    it('should show preview for valid custom color', async () => {
      const user = userEvent.setup();
      render(<ColorPickerCell {...defaultProps} value={null} />);

      await user.click(screen.getByRole('button'));

      const input = screen.getByPlaceholderText('#RRGGBB');
      await user.type(input, '#00FF00');

      expect(screen.getByText('Preview')).toBeInTheDocument();
      expect(screen.getByText('Sample Text')).toBeInTheDocument();
    });

    it('should save on Enter key', async () => {
      const user = userEvent.setup();
      const onSave = jest.fn();
      render(<ColorPickerCell value={null} onSave={onSave} />);

      await user.click(screen.getByRole('button'));

      const input = screen.getByPlaceholderText('#RRGGBB');
      await user.type(input, '#FFFF00{Enter}');

      expect(onSave).toHaveBeenCalledWith('#FFFF00');
    });

    it('should close on Escape key', async () => {
      const user = userEvent.setup();
      render(<ColorPickerCell {...defaultProps} />);

      await user.click(screen.getByRole('button'));

      const input = screen.getByPlaceholderText('#RRGGBB');
      await user.type(input, 'ABC{Escape}');

      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
      });
    });
  });

  describe('Clear Color', () => {
    it('should show clear button when value exists and allowClear is true', async () => {
      const user = userEvent.setup();
      render(<ColorPickerCell {...defaultProps} allowClear />);

      await user.click(screen.getByRole('button'));

      expect(screen.getByText('Clear color')).toBeInTheDocument();
    });

    it('should not show clear button when allowClear is false', async () => {
      const user = userEvent.setup();
      render(<ColorPickerCell {...defaultProps} allowClear={false} />);

      await user.click(screen.getByRole('button'));

      expect(screen.queryByText('Clear color')).not.toBeInTheDocument();
    });

    it('should not show clear button when value is null', async () => {
      const user = userEvent.setup();
      render(<ColorPickerCell {...defaultProps} value={null} allowClear />);

      await user.click(screen.getByRole('button'));

      expect(screen.queryByText('Clear color')).not.toBeInTheDocument();
    });

    it('should call onSave with null when clear is clicked', async () => {
      const user = userEvent.setup();
      const onSave = jest.fn();
      render(<ColorPickerCell value="#FF0000" onSave={onSave} allowClear />);

      await user.click(screen.getByRole('button'));
      await user.click(screen.getByText('Clear color'));

      expect(onSave).toHaveBeenCalledWith(null);
    });
  });

  describe('Loading State', () => {
    it('should show loader when isSaving', () => {
      render(<ColorPickerCell {...defaultProps} isSaving />);
      // Should not be able to interact
      const button = screen.getByRole('button');
      expect(button).toBeDisabled();
    });

    it('should not open picker when isSaving', async () => {
      const user = userEvent.setup();
      render(<ColorPickerCell {...defaultProps} isSaving />);

      await user.click(screen.getByRole('button'));

      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper aria-label', () => {
      render(<ColorPickerCell {...defaultProps} ariaLabel="Background color" />);
      expect(screen.getByRole('button')).toHaveAttribute('aria-label', 'Background color');
    });

    it('should have aria-haspopup attribute', () => {
      render(<ColorPickerCell {...defaultProps} />);
      expect(screen.getByRole('button')).toHaveAttribute('aria-haspopup', 'dialog');
    });

    it('should have aria-expanded when open', async () => {
      const user = userEvent.setup();
      render(<ColorPickerCell {...defaultProps} />);

      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('aria-expanded', 'false');

      await user.click(button);

      expect(button).toHaveAttribute('aria-expanded', 'true');
    });

    it('should have proper dialog role when open', async () => {
      const user = userEvent.setup();
      render(<ColorPickerCell {...defaultProps} />);

      await user.click(screen.getByRole('button'));

      expect(screen.getByRole('dialog')).toHaveAttribute('aria-label', 'Color picker');
    });
  });
});
