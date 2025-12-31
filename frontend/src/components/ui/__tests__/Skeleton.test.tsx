import { renderWithProviders } from '@/test-utils';
import React from 'react';
import { renderWithProviders as render, screen } from '@/test-utils';
import { Skeleton, SkeletonText, SkeletonCard, SkeletonTable } from '../Skeleton';

describe('Skeleton', () => {
  it('renders with default props', () => {
    render(<Skeleton />);
    const skeleton = screen.getByRole('status');
    expect(skeleton).toBeInTheDocument();
    expect(skeleton).toHaveClass('animate-pulse');
  });

  it('renders multiple skeletons with count prop', () => {
    render(<Skeleton count={3} />);
    const skeletons = screen.getAllByRole('status');
    expect(skeletons).toHaveLength(3);
  });

  it('renders with custom width and height', () => {
    render(<Skeleton width="200px" height="50px" />);
    const skeleton = screen.getByRole('status');
    expect(skeleton).toHaveStyle({ width: '200px', height: '50px' });
  });

  it('renders with numeric width and height', () => {
    render(<Skeleton width={200} height={50} />);
    const skeleton = screen.getByRole('status');
    expect(skeleton).toHaveStyle({ width: '200px', height: '50px' });
  });

  it('renders without animation when animate is false', () => {
    render(<Skeleton animate={false} />);
    const skeleton = screen.getByRole('status');
    expect(skeleton).not.toHaveClass('animate-pulse');
  });

  describe('variants', () => {
    it('renders text variant with correct classes', () => {
      render(<Skeleton variant="text" />);
      const skeleton = screen.getByRole('status');
      expect(skeleton).toHaveClass('rounded');
    });

    it('renders circular variant with correct classes', () => {
      render(<Skeleton variant="circular" />);
      const skeleton = screen.getByRole('status');
      expect(skeleton).toHaveClass('rounded-full');
    });

    it('renders rectangular variant with correct classes', () => {
      render(<Skeleton variant="rectangular" />);
      const skeleton = screen.getByRole('status');
      expect(skeleton).toHaveClass('rounded-none');
    });

    it('renders rounded variant with correct classes', () => {
      render(<Skeleton variant="rounded" />);
      const skeleton = screen.getByRole('status');
      expect(skeleton).toHaveClass('rounded-lg');
    });
  });

  describe('SkeletonText', () => {
    it('renders multiple text lines', () => {
      render(<SkeletonText lines={3} />);
      const skeletons = screen.getAllByRole('status');
      expect(skeletons).toHaveLength(3);
    });

    it('renders last line with 70% width', () => {
      const { container } = render(<SkeletonText lines={2} />);
      const skeletons = container.querySelectorAll('[role="status"]');
      // Last skeleton should have 70% width
      expect(skeletons[1]).toHaveStyle({ width: '70%' });
    });
  });

  describe('SkeletonCard', () => {
    it('renders card skeleton structure', () => {
      render(<SkeletonCard />);
      const skeletons = screen.getAllByRole('status');
      // Should have circular avatar + text lines
      expect(skeletons.length).toBeGreaterThan(1);
    });
  });

  describe('SkeletonTable', () => {
    it('renders table skeleton with default rows and columns', () => {
      render(<SkeletonTable />);
      const skeletons = screen.getAllByRole('status');
      // Default: 5 rows * 4 columns + 4 header columns = 24 skeletons
      expect(skeletons).toHaveLength(24);
    });

    it('renders table skeleton with custom rows and columns', () => {
      render(<SkeletonTable rows={3} columns={2} />);
      const skeletons = screen.getAllByRole('status');
      // 3 rows * 2 columns + 2 header columns = 8 skeletons
      expect(skeletons).toHaveLength(8);
    });
  });

  it('applies custom className', () => {
    render(<Skeleton className="custom-class" />);
    const skeleton = screen.getByRole('status');
    expect(skeleton).toHaveClass('custom-class');
  });

  it('has correct aria-label', () => {
    render(<Skeleton />);
    const skeleton = screen.getByRole('status');
    expect(skeleton).toHaveAttribute('aria-label', 'Loading...');
  });
});
