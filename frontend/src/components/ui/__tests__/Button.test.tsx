import { renderWithProviders } from '@/test-utils';
/**
 * Tests for Button Component
 * Component: 40 - Base button variants
 *
 * Note: Button now requires onClick OR type="submit" to prevent unclickable buttons.
 * Tests use noop for onClick when not testing click behavior.
 * See: Session 086 - button prevention mechanism
 */

import React from 'react';
import { renderWithProviders as render, screen, fireEvent } from '@/test-utils';
import '@testing-library/jest-dom';
import { Button, IconButton } from '../Button';

// Noop handler for tests that don't test click behavior
const noop = () => {};

describe('Button', () => {
  // Test 40.1: Render test
  describe('Rendering', () => {
    it('renders with children', () => {
      render(<Button onClick={noop}>Click me</Button>);

      expect(screen.getByText('Click me')).toBeInTheDocument();
    });

    it('renders as a button element', () => {
      render(<Button onClick={noop}>Click me</Button>);

      const button = screen.getByText('Click me');
      expect(button.tagName).toBe('BUTTON');
    });

    it('forwards ref correctly', () => {
      const ref = React.createRef<HTMLButtonElement>();
      render(<Button ref={ref} onClick={noop}>Click me</Button>);

      expect(ref.current).toBeInstanceOf(HTMLButtonElement);
    });

    it('renders with left icon', () => {
      render(<Button onClick={noop} leftIcon={<span>📝</span>}>Edit</Button>);

      expect(screen.getByText('📝')).toBeInTheDocument();
      expect(screen.getByText('Edit')).toBeInTheDocument();
    });

    it('renders with right icon', () => {
      render(<Button onClick={noop} rightIcon={<span>→</span>}>Next</Button>);

      expect(screen.getByText('→')).toBeInTheDocument();
      expect(screen.getByText('Next')).toBeInTheDocument();
    });

    it('renders loading state', () => {
      render(<Button onClick={noop} isLoading>Save</Button>);

      expect(screen.getByText('Save')).toBeInTheDocument();
    });

    it('renders custom loading text', () => {
      render(<Button onClick={noop} isLoading loadingText="Saving...">Save</Button>);

      expect(screen.getByText('Saving...')).toBeInTheDocument();
    });
  });

  // Test 40.2: Variant and size tests
  describe('Variants and Sizes', () => {
    it('renders primary variant (default)', () => {
      const { container } = render(<Button onClick={noop} variant="primary">Primary</Button>);

      const button = container.querySelector('.bg-blue-600');
      expect(button).toBeInTheDocument();
    });

    it('renders secondary variant', () => {
      const { container } = render(<Button onClick={noop} variant="secondary">Secondary</Button>);

      const button = container.querySelector('.bg-gray-100');
      expect(button).toBeInTheDocument();
    });

    it('renders danger variant', () => {
      const { container } = render(<Button onClick={noop} variant="danger">Delete</Button>);

      const button = container.querySelector('.bg-red-600');
      expect(button).toBeInTheDocument();
    });

    it('renders ghost variant', () => {
      const { container } = render(<Button onClick={noop} variant="ghost">Ghost</Button>);

      const button = container.querySelector('.bg-transparent');
      expect(button).toBeInTheDocument();
    });

    it('renders outline variant', () => {
      const { container } = render(<Button onClick={noop} variant="outline">Outline</Button>);

      const button = container.querySelector('.border.border-gray-300');
      expect(button).toBeInTheDocument();
    });

    it('renders success variant', () => {
      const { container } = render(<Button onClick={noop} variant="success">Success</Button>);

      const button = container.querySelector('.bg-green-600');
      expect(button).toBeInTheDocument();
    });

    it('renders small size', () => {
      const { container } = render(<Button onClick={noop} size="sm">Small</Button>);

      const button = container.querySelector('.px-3.py-1\\.5.text-sm');
      expect(button).toBeInTheDocument();
    });

    it('renders medium size (default)', () => {
      const { container } = render(<Button onClick={noop} size="md">Medium</Button>);

      const button = container.querySelector('.px-4.py-2.text-sm');
      expect(button).toBeInTheDocument();
    });

    it('renders large size', () => {
      const { container } = render(<Button onClick={noop} size="lg">Large</Button>);

      const button = container.querySelector('.px-6.py-3.text-base');
      expect(button).toBeInTheDocument();
    });

    it('renders full width when fullWidth is true', () => {
      const { container } = render(<Button onClick={noop} fullWidth>Full Width</Button>);

      const button = container.querySelector('.w-full');
      expect(button).toBeInTheDocument();
    });
  });

  // Test 40.3: Accessibility and interaction
  describe('Accessibility and Interaction', () => {
    it('handles click events', () => {
      const handleClick = jest.fn();
      render(<Button onClick={handleClick}>Click me</Button>);

      fireEvent.click(screen.getByText('Click me'));
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('is disabled when disabled prop is true', () => {
      render(<Button onClick={noop} disabled>Disabled</Button>);

      const button = screen.getByText('Disabled');
      expect(button).toBeDisabled();
    });

    it('is disabled when isLoading is true', () => {
      render(<Button onClick={noop} isLoading>Loading</Button>);

      const button = screen.getByText('Loading');
      expect(button).toBeDisabled();
    });

    it('does not call onClick when disabled', () => {
      const handleClick = jest.fn();
      render(<Button disabled onClick={handleClick}>Disabled</Button>);

      fireEvent.click(screen.getByText('Disabled'));
      expect(handleClick).not.toHaveBeenCalled();
    });

    it('is keyboard accessible', () => {
      render(<Button onClick={noop}>Focus me</Button>);

      const button = screen.getByText('Focus me');
      button.focus();

      expect(button).toHaveFocus();
    });

    it('applies focus ring styles', () => {
      const { container } = render(<Button onClick={noop}>Click me</Button>);

      const button = container.querySelector('.focus\\:outline-none.focus\\:ring-2');
      expect(button).toBeInTheDocument();
    });

    it('passes through other HTML button props', () => {
      render(<Button type="submit" name="submit-btn" data-testid="custom-button">Submit</Button>);

      const button = screen.getByText('Submit');
      expect(button).toHaveAttribute('type', 'submit');
      expect(button).toHaveAttribute('name', 'submit-btn');
      expect(button).toHaveAttribute('data-testid', 'custom-button');
    });
  });

  // Test 40.4: Edge cases and IconButton
  describe('Edge Cases and IconButton', () => {
    it('applies custom className', () => {
      const { container } = render(<Button onClick={noop} className="custom-class">Click me</Button>);

      const button = container.querySelector('.custom-class');
      expect(button).toBeInTheDocument();
    });

    it('merges custom className with base classes', () => {
      render(<Button onClick={noop} className="custom-class">Click me</Button>);

      const button = screen.getByText('Click me');
      expect(button).toHaveClass('custom-class');
      expect(button).toHaveClass('inline-flex');
    });

    it('hides icons when loading', () => {
      render(<Button onClick={noop} isLoading leftIcon={<span>📝</span>} rightIcon={<span>→</span>}>Save</Button>);

      expect(screen.queryByText('📝')).not.toBeInTheDocument();
      expect(screen.queryByText('→')).not.toBeInTheDocument();
    });

    it('renders IconButton variant', () => {
      render(<IconButton onClick={noop} aria-label="Search">🔍</IconButton>);

      expect(screen.getByText('🔍')).toBeInTheDocument();
    });

    it('IconButton has correct padding for sizes', () => {
      const { container, rerender } = render(<IconButton onClick={noop} aria-label="Search" size="sm">🔍</IconButton>);

      expect(container.querySelector('.p-1\\.5')).toBeInTheDocument();

      rerender(<IconButton onClick={noop} aria-label="Search" size="md">🔍</IconButton>);
      expect(container.querySelector('.p-2')).toBeInTheDocument();

      rerender(<IconButton onClick={noop} aria-label="Search" size="lg">🔍</IconButton>);
      expect(container.querySelector('.p-3')).toBeInTheDocument();
    });

    it('IconButton forwards ref correctly', () => {
      const ref = React.createRef<HTMLButtonElement>();
      render(<IconButton onClick={noop} aria-label="Search" ref={ref}>🔍</IconButton>);

      expect(ref.current).toBeInstanceOf(HTMLButtonElement);
    });

    it('renders with both icons and text', () => {
      render(<Button onClick={noop} leftIcon={<span>📝</span>} rightIcon={<span>→</span>}>Edit and Next</Button>);

      expect(screen.getByText('📝')).toBeInTheDocument();
      expect(screen.getByText('Edit and Next')).toBeInTheDocument();
      expect(screen.getByText('→')).toBeInTheDocument();
    });

    it('applies disabled styles', () => {
      const { container } = render(<Button onClick={noop} disabled>Disabled</Button>);

      const button = container.querySelector('.disabled\\:opacity-50.disabled\\:cursor-not-allowed');
      expect(button).toBeInTheDocument();
    });
  });
});
