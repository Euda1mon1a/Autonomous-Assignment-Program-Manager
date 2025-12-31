import { renderWithProviders } from '@/test-utils';
/**
 * Tests for Badge Component
 * Component: 42 - Status badges
 */

import React from 'react';
import { renderWithProviders as render, screen } from '@/test-utils';
import '@testing-library/jest-dom';
import { Badge, NumericBadge } from '../Badge';

describe('Badge', () => {
  // Test 42.1: Render test
  describe('Rendering', () => {
    it('renders with children', () => {
      render(<Badge>Active</Badge>);

      expect(screen.getByText('Active')).toBeInTheDocument();
    });

    it('renders as a span element', () => {
      const { container } = render(<Badge>Active</Badge>);

      expect(container.querySelector('span')).toBeInTheDocument();
    });

    it('renders with default variant', () => {
      const { container } = render(<Badge>Default</Badge>);

      expect(container.querySelector('.bg-gray-100.text-gray-800')).toBeInTheDocument();
    });

    it('renders with default size (medium)', () => {
      const { container } = render(<Badge>Medium</Badge>);

      expect(container.querySelector('.px-2\\.5.py-1.text-sm')).toBeInTheDocument();
    });

    it('renders with dot indicator when dot prop is true', () => {
      const { container } = render(<Badge dot>With Dot</Badge>);

      expect(container.querySelector('.w-1\\.5.h-1\\.5.rounded-full')).toBeInTheDocument();
    });

    it('does not render dot by default', () => {
      const { container } = render(<Badge>No Dot</Badge>);

      expect(container.querySelector('.w-1\\.5.h-1\\.5.rounded-full')).not.toBeInTheDocument();
    });
  });

  // Test 42.2: Variant tests
  describe('Variants', () => {
    it('renders primary variant', () => {
      const { container } = render(<Badge variant="primary">Primary</Badge>);

      expect(container.querySelector('.bg-blue-100.text-blue-800')).toBeInTheDocument();
    });

    it('renders success variant', () => {
      const { container } = render(<Badge variant="success">Success</Badge>);

      expect(container.querySelector('.bg-green-100.text-green-800')).toBeInTheDocument();
    });

    it('renders warning variant', () => {
      const { container } = render(<Badge variant="warning">Warning</Badge>);

      expect(container.querySelector('.bg-amber-100.text-amber-800')).toBeInTheDocument();
    });

    it('renders danger variant', () => {
      const { container } = render(<Badge variant="danger">Danger</Badge>);

      expect(container.querySelector('.bg-red-100.text-red-800')).toBeInTheDocument();
    });

    it('renders destructive variant', () => {
      const { container } = render(<Badge variant="destructive">Destructive</Badge>);

      expect(container.querySelector('.bg-red-100.text-red-800')).toBeInTheDocument();
    });

    it('renders info variant', () => {
      const { container } = render(<Badge variant="info">Info</Badge>);

      expect(container.querySelector('.bg-cyan-100.text-cyan-800')).toBeInTheDocument();
    });

    it('renders dot with matching color for each variant', () => {
      const { container, rerender } = render(<Badge variant="success" dot>Success</Badge>);

      expect(container.querySelector('.bg-green-600')).toBeInTheDocument();

      rerender(<Badge variant="danger" dot>Danger</Badge>);
      expect(container.querySelector('.bg-red-600')).toBeInTheDocument();

      rerender(<Badge variant="primary" dot>Primary</Badge>);
      expect(container.querySelector('.bg-blue-600')).toBeInTheDocument();
    });
  });

  // Test 42.3: Size and shape variants
  describe('Sizes and Shapes', () => {
    it('renders small size', () => {
      const { container } = render(<Badge size="sm">Small</Badge>);

      expect(container.querySelector('.px-2.py-0\\.5.text-xs')).toBeInTheDocument();
    });

    it('renders large size', () => {
      const { container } = render(<Badge size="lg">Large</Badge>);

      expect(container.querySelector('.px-3.py-1\\.5.text-base')).toBeInTheDocument();
    });

    it('renders with rounded corners by default', () => {
      const { container } = render(<Badge>Badge</Badge>);

      const badge = container.querySelector('span');
      expect(badge).toHaveClass('rounded');
      expect(badge).not.toHaveClass('rounded-full');
    });

    it('renders fully rounded when rounded prop is true', () => {
      const { container } = render(<Badge rounded>Rounded</Badge>);

      expect(container.querySelector('.rounded-full')).toBeInTheDocument();
    });

    it('applies custom className', () => {
      const { container } = render(<Badge className="custom-badge">Custom</Badge>);

      expect(container.querySelector('.custom-badge')).toBeInTheDocument();
    });

    it('renders with all props combined', () => {
      const { container } = render(
        <Badge variant="success" size="lg" rounded dot className="custom">
          Complete
        </Badge>
      );

      const badge = container.querySelector('span');
      expect(badge).toHaveClass('bg-green-100');
      expect(badge).toHaveClass('px-3');
      expect(badge).toHaveClass('rounded-full');
      expect(badge).toHaveClass('custom');
      expect(container.querySelector('.w-1\\.5.h-1\\.5')).toBeInTheDocument();
    });
  });

  // Test 42.4: NumericBadge and edge cases
  describe('NumericBadge', () => {
    it('renders numeric count', () => {
      render(<NumericBadge count={5} />);

      expect(screen.getByText('5')).toBeInTheDocument();
    });

    it('displays max+ when count exceeds max', () => {
      render(<NumericBadge count={150} max={99} />);

      expect(screen.getByText('99+')).toBeInTheDocument();
    });

    it('uses default max of 99', () => {
      render(<NumericBadge count={100} />);

      expect(screen.getByText('99+')).toBeInTheDocument();
    });

    it('renders exact count when below max', () => {
      render(<NumericBadge count={42} max={99} />);

      expect(screen.getByText('42')).toBeInTheDocument();
    });

    it('uses danger variant by default', () => {
      const { container } = render(<NumericBadge count={5} />);

      expect(container.querySelector('.bg-red-100.text-red-800')).toBeInTheDocument();
    });

    it('accepts custom variant', () => {
      const { container } = render(<NumericBadge count={5} variant="primary" />);

      expect(container.querySelector('.bg-blue-100.text-blue-800')).toBeInTheDocument();
    });

    it('is always small and rounded', () => {
      const { container } = render(<NumericBadge count={5} />);

      expect(container.querySelector('.px-2.py-0\\.5.text-xs.rounded-full')).toBeInTheDocument();
    });

    it('accepts custom className', () => {
      const { container } = render(<NumericBadge count={5} className="custom-numeric" />);

      expect(container.querySelector('.custom-numeric')).toBeInTheDocument();
    });

    it('handles zero count', () => {
      render(<NumericBadge count={0} />);

      expect(screen.getByText('0')).toBeInTheDocument();
    });

    it('handles large numbers correctly', () => {
      render(<NumericBadge count={9999} max={999} />);

      expect(screen.getByText('999+')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles long text', () => {
      render(<Badge>This is a very long badge text</Badge>);

      expect(screen.getByText('This is a very long badge text')).toBeInTheDocument();
    });

    it('handles special characters', () => {
      render(<Badge>Status: ✓ Active!</Badge>);

      expect(screen.getByText('Status: ✓ Active!')).toBeInTheDocument();
    });

    it('renders with React nodes as children', () => {
      render(
        <Badge>
          <span>Nested</span> <strong>Content</strong>
        </Badge>
      );

      expect(screen.getByText('Nested')).toBeInTheDocument();
      expect(screen.getByText('Content')).toBeInTheDocument();
    });

    it('has proper inline-flex display', () => {
      const { container } = render(<Badge>Badge</Badge>);

      expect(container.querySelector('.inline-flex.items-center')).toBeInTheDocument();
    });
  });
});
