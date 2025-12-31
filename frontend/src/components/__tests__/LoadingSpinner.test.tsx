/**
 * Tests for LoadingSpinner Component
 * Component: LoadingSpinner - Loading state indicator
 */

import React from 'react';
import { render, screen } from '@/test-utils';
import '@testing-library/jest-dom';
import { LoadingSpinner } from '../LoadingSpinner';

describe('LoadingSpinner', () => {
  // Test: Rendering
  describe('Rendering', () => {
    it('renders without crashing', () => {
      render(<LoadingSpinner />);

      expect(screen.getByRole('status')).toBeInTheDocument();
    });

    it('has proper ARIA attributes', () => {
      render(<LoadingSpinner />);

      const spinner = screen.getByRole('status');
      expect(spinner).toHaveAttribute('aria-label', 'Loading');
    });

    it('renders with text', () => {
      render(<LoadingSpinner text="Loading data..." />);

      expect(screen.getByText('Loading data...')).toBeInTheDocument();
    });

    it('does not render text when not provided', () => {
      render(<LoadingSpinner />);

      expect(screen.queryByText(/Loading/)).not.toBeInTheDocument();
    });

    it('has spinning animation', () => {
      const { container } = render(<LoadingSpinner />);

      expect(container.querySelector('.animate-spin')).toBeInTheDocument();
    });
  });

  // Test: Sizes
  describe('Sizes', () => {
    it('renders sm size', () => {
      const { container } = render(<LoadingSpinner size="sm" />);

      expect(container.querySelector('.w-4.h-4')).toBeInTheDocument();
    });

    it('renders md size (default)', () => {
      const { container } = render(<LoadingSpinner size="md" />);

      expect(container.querySelector('.w-8.h-8')).toBeInTheDocument();
    });

    it('renders lg size', () => {
      const { container } = render(<LoadingSpinner size="lg" />);

      expect(container.querySelector('.w-12.h-12')).toBeInTheDocument();
    });

    it('uses md size when not specified', () => {
      const { container } = render(<LoadingSpinner />);

      expect(container.querySelector('.w-8.h-8')).toBeInTheDocument();
    });
  });

  // Test: Text sizing
  describe('Text Sizing', () => {
    it('renders text-xs for sm size', () => {
      const { container } = render(<LoadingSpinner size="sm" text="Loading..." />);

      expect(container.querySelector('.text-xs')).toBeInTheDocument();
    });

    it('renders text-sm for md size', () => {
      const { container } = render(<LoadingSpinner size="md" text="Loading..." />);

      expect(container.querySelector('.text-sm')).toBeInTheDocument();
    });

    it('renders text-base for lg size', () => {
      const { container } = render(<LoadingSpinner size="lg" text="Loading..." />);

      expect(container.querySelector('.text-base')).toBeInTheDocument();
    });
  });

  // Test: Edge cases
  describe('Edge Cases', () => {
    it('renders circular border', () => {
      const { container } = render(<LoadingSpinner />);

      expect(container.querySelector('.rounded-full')).toBeInTheDocument();
    });

    it('has proper color scheme', () => {
      const { container } = render(<LoadingSpinner />);

      const spinner = container.querySelector('.border-gray-200.border-t-blue-600');
      expect(spinner).toBeInTheDocument();
    });

    it('centers content with flexbox', () => {
      const { container } = render(<LoadingSpinner />);

      expect(container.querySelector('.flex.flex-col.items-center.justify-center')).toBeInTheDocument();
    });

    it('has gap between spinner and text', () => {
      const { container } = render(<LoadingSpinner text="Loading..." />);

      expect(container.querySelector('.gap-3')).toBeInTheDocument();
    });

    it('handles long text', () => {
      const longText = 'This is a very long loading message that should still display correctly below the spinner';
      render(<LoadingSpinner text={longText} />);

      expect(screen.getByText(longText)).toBeInTheDocument();
    });

    it('is accessible with screen readers', () => {
      render(<LoadingSpinner text="Loading user data" />);

      const spinner = screen.getByRole('status');
      expect(spinner).toBeInTheDocument();
      expect(screen.getByText('Loading user data')).toBeInTheDocument();
    });
  });
});
