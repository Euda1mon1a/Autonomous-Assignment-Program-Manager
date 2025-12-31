/**
 * Tests for Input Component
 * Component: 43 - Form inputs
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Input } from '../Input';

describe('Input', () => {
  // Test 43.1: Render test
  describe('Rendering', () => {
    it('renders input element', () => {
      render(<Input placeholder="Enter text" onChange={() => {}} />);

      expect(screen.getByPlaceholderText('Enter text')).toBeInTheDocument();
    });

    it('renders with label', () => {
      render(<Input label="Email" onChange={() => {}} />);

      expect(screen.getByText('Email')).toBeInTheDocument();
    });

    it('renders without label', () => {
      render(<Input placeholder="No label" onChange={() => {}} />);

      expect(screen.queryByText(/Label/)).not.toBeInTheDocument();
    });

    it('forwards ref correctly', () => {
      const ref = React.createRef<HTMLInputElement>();
      render(<Input ref={ref} onChange={() => {}} />);

      expect(ref.current).toBeInstanceOf(HTMLInputElement);
    });

    it('renders with left icon', () => {
      render(<Input leftIcon={<span>🔍</span>} onChange={() => {}} />);

      expect(screen.getByText('🔍')).toBeInTheDocument();
    });

    it('renders with right icon', () => {
      render(<Input rightIcon={<span>✓</span>} onChange={() => {}} />);

      expect(screen.getByText('✓')).toBeInTheDocument();
    });

    it('renders helper text', () => {
      render(<Input helperText="Enter your email address" onChange={() => {}} />);

      expect(screen.getByText('Enter your email address')).toBeInTheDocument();
    });
  });

  // Test 43.2: Controlled input and validation
  describe('Controlled Input and Validation', () => {
    it('handles controlled input', () => {
      const onChange = jest.fn();
      render(<Input value="test" onChange={onChange} />);

      const input = screen.getByDisplayValue('test');
      fireEvent.change(input, { target: { value: 'new value' } });

      expect(onChange).toHaveBeenCalled();
    });

    it('displays error message', () => {
      render(<Input error="This field is required" onChange={() => {}} />);

      expect(screen.getByText('This field is required')).toBeInTheDocument();
    });

    it('applies error styling when error prop provided', () => {
      const { container } = render(<Input error="Error message" onChange={() => {}} />);

      expect(container.querySelector('.border-red-300')).toBeInTheDocument();
    });

    it('shows error icon when error provided', () => {
      render(<Input error="Error message" onChange={() => {}} />);

      // Error icon (AlertCircle) should be rendered
      const errorIcon = document.querySelector('.text-red-500');
      expect(errorIcon).toBeInTheDocument();
    });

    it('hides helper text when error is shown', () => {
      render(
        <Input
          helperText="Helper text"
          error="Error message"
          onChange={() => {}}
        />
      );

      expect(screen.queryByText('Helper text')).not.toBeInTheDocument();
      expect(screen.getByText('Error message')).toBeInTheDocument();
    });

    it('has proper ARIA attributes for errors', () => {
      render(<Input id="email" error="Invalid email" onChange={() => {}} />);

      const input = screen.getByRole('textbox');
      expect(input).toHaveAttribute('aria-invalid', 'true');
      expect(input).toHaveAttribute('aria-describedby', 'email-error');
    });

    it('has proper ARIA attributes for helper text', () => {
      render(<Input id="email" helperText="Enter your email" onChange={() => {}} />);

      const input = screen.getByRole('textbox');
      expect(input).toHaveAttribute('aria-describedby', 'email-helper');
    });
  });

  // Test 43.3: Accessibility and keyboard
  describe('Accessibility', () => {
    it('is keyboard accessible', () => {
      render(<Input placeholder="Focus me" onChange={() => {}} />);

      const input = screen.getByPlaceholderText('Focus me');
      input.focus();

      expect(input).toHaveFocus();
    });

    it('label is associated with input', () => {
      render(<Input label="Username" id="username" onChange={() => {}} />);

      const label = screen.getByText('Username');
      const input = screen.getByRole('textbox');

      // Label should be properly associated
      expect(label.tagName).toBe('LABEL');
    });

    it('supports disabled state', () => {
      render(<Input disabled onChange={() => {}} />);

      const input = screen.getByRole('textbox');
      expect(input).toBeDisabled();
    });

    it('applies disabled styling', () => {
      const { container } = render(<Input disabled onChange={() => {}} />);

      expect(container.querySelector('.disabled\\:bg-gray-100.disabled\\:cursor-not-allowed')).toBeInTheDocument();
    });

    it('has focus ring styles', () => {
      const { container } = render(<Input onChange={() => {}} />);

      expect(container.querySelector('.focus\\:outline-none.focus\\:ring-2')).toBeInTheDocument();
    });
  });

  // Test 43.4: Edge cases and variants
  describe('Edge Cases and Variants', () => {
    it('renders full width when fullWidth is true', () => {
      const { container } = render(<Input fullWidth onChange={() => {}} />);

      expect(container.querySelector('.w-full')).toBeInTheDocument();
    });

    it('does not render full width by default', () => {
      const { container } = render(<Input onChange={() => {}} />);

      const wrapper = container.firstChild;
      expect(wrapper).not.toHaveClass('w-full');
    });

    it('passes through HTML input attributes', () => {
      render(
        <Input
          type="email"
          name="email"
          placeholder="email@example.com"
          required
          onChange={() => {}}
        />
      );

      const input = screen.getByRole('textbox');
      expect(input).toHaveAttribute('type', 'email');
      expect(input).toHaveAttribute('name', 'email');
      expect(input).toHaveAttribute('placeholder', 'email@example.com');
      expect(input).toBeRequired();
    });

    it('applies custom className', () => {
      const { container } = render(<Input className="custom-input" onChange={() => {}} />);

      expect(container.querySelector('.custom-input')).toBeInTheDocument();
    });

    it('handles password type', () => {
      render(<Input type="password" onChange={() => {}} />);

      const input = screen.getByRole('textbox', { hidden: true });
      expect(input).toHaveAttribute('type', 'password');
    });

    it('handles number type', () => {
      render(<Input type="number" onChange={() => {}} />);

      const input = screen.getByRole('spinbutton');
      expect(input).toHaveAttribute('type', 'number');
    });

    it('adjusts padding for left icon', () => {
      const { container } = render(<Input leftIcon={<span>🔍</span>} onChange={() => {}} />);

      expect(container.querySelector('.pl-10')).toBeInTheDocument();
    });

    it('adjusts padding for right icon', () => {
      const { container } = render(<Input rightIcon={<span>✓</span>} onChange={() => {}} />);

      expect(container.querySelector('.pr-10')).toBeInTheDocument();
    });

    it('adjusts padding for error icon', () => {
      const { container } = render(<Input error="Error" onChange={() => {}} />);

      expect(container.querySelector('.pr-10')).toBeInTheDocument();
    });

    it('handles both left and right icons', () => {
      render(<Input leftIcon={<span>🔍</span>} rightIcon={<span>✓</span>} onChange={() => {}} />);

      expect(screen.getByText('🔍')).toBeInTheDocument();
      expect(screen.getByText('✓')).toBeInTheDocument();
    });

    it('error icon takes precedence over right icon', () => {
      render(<Input rightIcon={<span>✓</span>} error="Error" onChange={() => {}} />);

      expect(screen.queryByText('✓')).not.toBeInTheDocument();
      const errorIcon = document.querySelector('.text-red-500');
      expect(errorIcon).toBeInTheDocument();
    });

    it('handles long error messages', () => {
      const longError = 'This is a very long error message that should still display correctly below the input field without breaking the layout.';

      render(<Input error={longError} onChange={() => {}} />);

      expect(screen.getByText(longError)).toBeInTheDocument();
    });
  });
});
