/**
 * Tests for Breadcrumbs Component
 * Component: common/Breadcrumbs - Navigation breadcrumb trail
 */

import React from 'react';
import { render, screen } from '@/test-utils';
import '@testing-library/jest-dom';
import { Breadcrumbs } from '../Breadcrumbs';

// Mock Next.js navigation
jest.mock('next/navigation', () => ({
  usePathname: () => '/schedule',
}));

// Mock Next.js Link
jest.mock('next/link', () => {
  const MockLink = ({ children, href, ...props }: React.AnchorHTMLAttributes<HTMLAnchorElement> & { href: string; children: React.ReactNode }) => {
    return <a href={href} {...props}>{children}</a>;
  };
  MockLink.displayName = 'Link';
  return MockLink;
});

describe('Breadcrumbs', () => {
  const mockItems = [
    { label: 'Home', href: '/' },
    { label: 'Admin', href: '/admin' },
    { label: 'Schedule', href: '/schedule', isCurrentPage: true },
  ];

  describe('Rendering', () => {
    it('renders all breadcrumb items', () => {
      render(<Breadcrumbs items={mockItems} showHome={false} />);
      expect(screen.getByText('Home')).toBeInTheDocument();
      expect(screen.getByText('Admin')).toBeInTheDocument();
      expect(screen.getByText('Schedule')).toBeInTheDocument();
    });

    it('renders ChevronRight separators between items', () => {
      const { container } = render(<Breadcrumbs items={mockItems} showHome={false} />);
      // ChevronRight SVGs are used as separators (aria-hidden)
      const separators = container.querySelectorAll('[aria-hidden="true"]');
      expect(separators.length).toBeGreaterThan(0);
    });

    it('renders non-current items as links', () => {
      render(<Breadcrumbs items={mockItems} showHome={false} />);
      const homeLink = screen.getByText('Home').closest('a');
      expect(homeLink).toHaveAttribute('href', '/');
    });

    it('renders middle items as links', () => {
      render(<Breadcrumbs items={mockItems} showHome={false} />);
      const adminLink = screen.getByText('Admin').closest('a');
      expect(adminLink).toHaveAttribute('href', '/admin');
    });

    it('renders current page item without link', () => {
      render(<Breadcrumbs items={mockItems} showHome={false} />);
      const schedule = screen.getByText('Schedule');
      const scheduleLink = schedule.closest('a');
      expect(scheduleLink).toBeNull();
    });

    it('applies current page styling to current item', () => {
      render(<Breadcrumbs items={mockItems} showHome={false} />);
      const currentItem = screen.getByText('Schedule');
      expect(currentItem).toHaveClass('font-medium');
      expect(currentItem).toHaveClass('text-gray-900');
    });
  });

  describe('Home Icon', () => {
    it('renders home icon when showHome is true (default)', () => {
      const { container } = render(<Breadcrumbs items={mockItems} />);
      expect(container.querySelector('svg')).toBeInTheDocument();
    });

    it('renders home link with Dashboard text', () => {
      render(<Breadcrumbs items={mockItems} />);
      expect(screen.getByLabelText('Home')).toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    it('renders nav when items are empty but showHome is true', () => {
      render(<Breadcrumbs items={[]} />);
      // With showHome=true (default), still renders the home link
      expect(screen.getByRole('navigation')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has nav role', () => {
      render(<Breadcrumbs items={mockItems} />);
      expect(screen.getByRole('navigation')).toBeInTheDocument();
    });

    it('has aria-label for navigation', () => {
      render(<Breadcrumbs items={mockItems} />);
      const nav = screen.getByRole('navigation');
      expect(nav).toHaveAttribute('aria-label', 'Breadcrumb');
    });

    it('has ordered list structure', () => {
      const { container } = render(<Breadcrumbs items={mockItems} />);
      expect(container.querySelector('ol')).toBeInTheDocument();
    });

    it('marks current page with aria-current', () => {
      render(<Breadcrumbs items={mockItems} showHome={false} />);
      const currentPage = screen.getByText('Schedule');
      expect(currentPage).toHaveAttribute('aria-current', 'page');
    });
  });

  describe('Long Paths', () => {
    it('handles many breadcrumb items', () => {
      const manyItems = [
        { label: 'Home', href: '/' },
        { label: 'Level 1', href: '/level1' },
        { label: 'Level 2', href: '/level2' },
        { label: 'Level 3', href: '/level3' },
        { label: 'Current', href: '/current', isCurrentPage: true },
      ];
      render(<Breadcrumbs items={manyItems} showHome={false} />);
      expect(screen.getByText('Home')).toBeInTheDocument();
      expect(screen.getByText('Current')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles items with special characters', () => {
      const specialItems = [
        { label: 'Home & Away', href: '/' },
        { label: 'C++ Programming', href: '/cpp', isCurrentPage: true },
      ];
      render(<Breadcrumbs items={specialItems} showHome={false} />);
      expect(screen.getByText('Home & Away')).toBeInTheDocument();
      expect(screen.getByText('C++ Programming')).toBeInTheDocument();
    });

    it('handles items with very short labels', () => {
      const shortItems = [
        { label: 'A', href: '/a' },
        { label: 'B', href: '/b', isCurrentPage: true },
      ];
      render(<Breadcrumbs items={shortItems} showHome={false} />);
      expect(screen.getByText('A')).toBeInTheDocument();
      expect(screen.getByText('B')).toBeInTheDocument();
    });
  });
});
