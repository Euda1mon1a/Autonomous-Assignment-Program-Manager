/**
 * Tests for Spinner Component
 * Component: Spinner - Loading indicators
 */

import React from 'react';
import { render, screen } from '@/test-utils';
import '@testing-library/jest-dom';
import { Spinner } from '../Spinner';

describe('Spinner', () => {
  // Test: Rendering
  describe('Rendering', () => {
    it('renders without crashing', () => {
      const { container } = render(<Spinner />);

      expect(container.querySelector('.spinner')).toBeInTheDocument();
    });

    it('has proper role and aria-label', () => {
      render(<Spinner />);

      const spinner = screen.getByRole('status');
      expect(spinner).toHaveAttribute('aria-label', 'Loading');
    });

    it('renders with custom label', () => {
      render(<Spinner label="Loading data..." />);

      expect(screen.getByText('Loading data...')).toBeInTheDocument();
      expect(screen.getByRole('status')).toHaveAttribute('aria-label', 'Loading data...');
    });

    it('does not render label text when not provided', () => {
      render(<Spinner />);

      const container = screen.getByRole('status').parentElement;
      expect(container?.querySelector('span')).not.toBeInTheDocument();
    });

    it('has spinning animation', () => {
      const { container } = render(<Spinner />);

      const spinnerElement = container.querySelector('.animate-spin');
      expect(spinnerElement).toBeInTheDocument();
    });
  });

  // Test: Sizes
  describe('Sizes', () => {
    it('renders xs size', () => {
      const { container } = render(<Spinner size="xs" />);

      expect(container.querySelector('.w-4.h-4')).toBeInTheDocument();
    });

    it('renders sm size', () => {
      const { container } = render(<Spinner size="sm" />);

      expect(container.querySelector('.w-6.h-6')).toBeInTheDocument();
    });

    it('renders md size (default)', () => {
      const { container } = render(<Spinner size="md" />);

      expect(container.querySelector('.w-8.h-8')).toBeInTheDocument();
    });

    it('renders lg size', () => {
      const { container } = render(<Spinner size="lg" />);

      expect(container.querySelector('.w-12.h-12')).toBeInTheDocument();
    });

    it('renders xl size', () => {
      const { container } = render(<Spinner size="xl" />);

      expect(container.querySelector('.w-16.h-16')).toBeInTheDocument();
    });
  });

  // Test: Variants
  describe('Variants', () => {
    it('renders default variant', () => {
      const { container } = render(<Spinner variant="default" />);

      expect(container.querySelector('.border-gray-300.border-t-gray-600')).toBeInTheDocument();
    });

    it('renders primary variant', () => {
      const { container } = render(<Spinner variant="primary" />);

      expect(container.querySelector('.border-blue-200.border-t-blue-600')).toBeInTheDocument();
    });

    it('renders white variant', () => {
      const { container } = render(<Spinner variant="white" />);

      expect(container.querySelector('.border-white')).toBeInTheDocument();
    });

    it('uses default variant when not specified', () => {
      const { container } = render(<Spinner />);

      expect(container.querySelector('.border-gray-300.border-t-gray-600')).toBeInTheDocument();
    });
  });

  // Test: Edge cases
  describe('Edge Cases', () => {
    it('applies custom className', () => {
      const { container } = render(<Spinner className="custom-class" />);

      expect(container.querySelector('.custom-class')).toBeInTheDocument();
    });

    it('combines size and variant', () => {
      const { container } = render(<Spinner size="lg" variant="primary" />);

      expect(container.querySelector('.w-12.h-12')).toBeInTheDocument();
      expect(container.querySelector('.border-blue-200.border-t-blue-600')).toBeInTheDocument();
    });

    it('renders label with custom size', () => {
      render(<Spinner size="xs" label="Loading..." />);

      const label = screen.getByText('Loading...');
      expect(label).toHaveClass('text-sm');
    });

    it('has proper structure with label', () => {
      const { container } = render(<Spinner label="Please wait" />);

      const wrapper = container.querySelector('.inline-flex.flex-col.items-center.gap-2');
      expect(wrapper).toBeInTheDocument();
    });

    it('is accessible with screen readers', () => {
      render(<Spinner label="Loading content" />);

      const spinner = screen.getByRole('status');
      expect(spinner).toHaveAccessibleName('Loading content');
    });

    it('renders circular border', () => {
      const { container } = render(<Spinner />);

      const spinnerElement = container.querySelector('.rounded-full.border-2');
      expect(spinnerElement).toBeInTheDocument();
    });
  });
});
