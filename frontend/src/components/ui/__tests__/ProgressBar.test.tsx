import { renderWithProviders } from '@/test-utils';
/**
 * Tests for ProgressBar Component
 * Component: 35 - Progress indicator
 */

import React from 'react';
import { renderWithProviders as render, screen } from '@/test-utils';
import '@testing-library/jest-dom';
import { ProgressBar } from '../ProgressBar';

describe('ProgressBar', () => {
  // Test 35.1: Render test
  describe('Rendering', () => {
    it('renders with default props', () => {
      render(<ProgressBar value={50} />);

      const progressbar = screen.getByRole('progressbar');
      expect(progressbar).toBeInTheDocument();
      expect(progressbar).toHaveAttribute('aria-valuenow', '50');
    });

    it('displays percentage label', () => {
      render(<ProgressBar value={75} />);

      expect(screen.getByText('75%')).toBeInTheDocument();
    });

    it('renders with custom label', () => {
      render(<ProgressBar value={60} label="Upload Progress" />);

      expect(screen.getByText('Upload Progress')).toBeInTheDocument();
      expect(screen.getByText('60%')).toBeInTheDocument();
    });

    it('hides label when showLabel is false', () => {
      render(<ProgressBar value={50} showLabel={false} />);

      expect(screen.queryByText('50%')).not.toBeInTheDocument();
    });

    it('shows label text but not percentage when only label provided', () => {
      render(<ProgressBar value={40} label="Processing" showLabel={false} />);

      expect(screen.getByText('Processing')).toBeInTheDocument();
      expect(screen.queryByText('40%')).not.toBeInTheDocument();
    });
  });

  // Test 35.2: Variant and size tests
  describe('Variants and Sizes', () => {
    it('renders default variant (blue)', () => {
      const { container } = render(<ProgressBar value={50} variant="default" />);

      const bar = container.querySelector('.bg-blue-600');
      expect(bar).toBeInTheDocument();
    });

    it('renders success variant (green)', () => {
      const { container } = render(<ProgressBar value={100} variant="success" />);

      const bar = container.querySelector('.bg-green-600');
      expect(bar).toBeInTheDocument();
    });

    it('renders warning variant (yellow)', () => {
      const { container } = render(<ProgressBar value={75} variant="warning" />);

      const bar = container.querySelector('.bg-yellow-600');
      expect(bar).toBeInTheDocument();
    });

    it('renders danger variant (red)', () => {
      const { container } = render(<ProgressBar value={25} variant="danger" />);

      const bar = container.querySelector('.bg-red-600');
      expect(bar).toBeInTheDocument();
    });

    it('renders small size', () => {
      const { container } = render(<ProgressBar value={50} size="sm" />);

      const track = container.querySelector('.h-2');
      expect(track).toBeInTheDocument();
    });

    it('renders medium size (default)', () => {
      const { container } = render(<ProgressBar value={50} size="md" />);

      const track = container.querySelector('.h-4');
      expect(track).toBeInTheDocument();
    });

    it('renders large size', () => {
      const { container } = render(<ProgressBar value={50} size="lg" />);

      const track = container.querySelector('.h-6');
      expect(track).toBeInTheDocument();
    });
  });

  // Test 35.3: Accessibility
  describe('Accessibility', () => {
    it('has proper ARIA attributes', () => {
      render(<ProgressBar value={60} max={100} />);

      const progressbar = screen.getByRole('progressbar');
      expect(progressbar).toHaveAttribute('aria-valuenow', '60');
      expect(progressbar).toHaveAttribute('aria-valuemin', '0');
      expect(progressbar).toHaveAttribute('aria-valuemax', '100');
    });

    it('has aria-label with custom label', () => {
      render(<ProgressBar value={50} label="File Upload" />);

      const progressbar = screen.getByRole('progressbar');
      expect(progressbar).toHaveAttribute('aria-label', 'File Upload');
    });

    it('has default aria-label when no label provided', () => {
      render(<ProgressBar value={75} />);

      const progressbar = screen.getByRole('progressbar');
      expect(progressbar).toHaveAttribute('aria-label', 'Progress: 75%');
    });

    it('respects custom max value in ARIA attributes', () => {
      render(<ProgressBar value={50} max={200} />);

      const progressbar = screen.getByRole('progressbar');
      expect(progressbar).toHaveAttribute('aria-valuemax', '200');
    });
  });

  // Test 35.4: Edge cases and calculations
  describe('Edge Cases and Calculations', () => {
    it('handles 0% progress', () => {
      const { container } = render(<ProgressBar value={0} />);

      expect(screen.getByText('0%')).toBeInTheDocument();

      const bar = container.querySelector('[role="progressbar"]');
      expect(bar).toHaveStyle({ width: '0%' });
    });

    it('handles 100% progress', () => {
      const { container } = render(<ProgressBar value={100} />);

      expect(screen.getByText('100%')).toBeInTheDocument();

      const bar = container.querySelector('[role="progressbar"]');
      expect(bar).toHaveStyle({ width: '100%' });
    });

    it('caps progress at 100% when value exceeds max', () => {
      const { container } = render(<ProgressBar value={150} max={100} />);

      expect(screen.getByText('100%')).toBeInTheDocument();

      const bar = container.querySelector('[role="progressbar"]');
      expect(bar).toHaveStyle({ width: '100%' });
    });

    it('calculates percentage correctly with custom max', () => {
      render(<ProgressBar value={50} max={200} />);

      // 50 out of 200 is 25%
      expect(screen.getByText('25%')).toBeInTheDocument();
    });

    it('handles decimal values', () => {
      render(<ProgressBar value={33.7} max={100} />);

      // Should round to 34%
      expect(screen.getByText('34%')).toBeInTheDocument();
    });

    it('applies animated class when animated prop is true', () => {
      const { container } = render(<ProgressBar value={50} animated />);

      const bar = container.querySelector('.animate-pulse');
      expect(bar).toBeInTheDocument();
    });

    it('does not apply animated class when animated is false', () => {
      const { container } = render(<ProgressBar value={50} animated={false} />);

      const bar = container.querySelector('.animate-pulse');
      expect(bar).not.toBeInTheDocument();
    });

    it('applies custom className', () => {
      const { container } = render(<ProgressBar value={50} className="custom-class" />);

      expect(container.querySelector('.progress-bar.custom-class')).toBeInTheDocument();
    });

    it('applies transition classes for smooth animation', () => {
      const { container } = render(<ProgressBar value={50} />);

      const bar = container.querySelector('.transition-all.duration-500.ease-out');
      expect(bar).toBeInTheDocument();
    });

    it('maintains proper width style', () => {
      const { container } = render(<ProgressBar value={65} />);

      const bar = container.querySelector('[role="progressbar"]');
      expect(bar).toHaveStyle({ width: '65%' });
    });

    it('uses correct text size for each size variant', () => {
      const { container, rerender } = render(<ProgressBar value={50} size="sm" />);

      expect(container.querySelector('.text-xs')).toBeInTheDocument();

      rerender(<ProgressBar value={50} size="md" />);
      expect(container.querySelector('.text-sm')).toBeInTheDocument();

      rerender(<ProgressBar value={50} size="lg" />);
      expect(container.querySelector('.text-base')).toBeInTheDocument();
    });

    it('handles negative values by treating as 0', () => {
      const { container } = render(<ProgressBar value={-10} />);

      expect(screen.getByText('0%')).toBeInTheDocument();
    });

    it('renders track with gray background', () => {
      const { container } = render(<ProgressBar value={50} />);

      const track = container.querySelector('.bg-gray-200.rounded-full');
      expect(track).toBeInTheDocument();
    });
  });
});
