/**
 * Tests for Breadcrumbs Component
 * Component: common/Breadcrumbs - Navigation breadcrumb trail
 */

import React from 'react';
import { render, screen, fireEvent } from '@/test-utils';
import '@testing-library/jest-dom';
import { Breadcrumbs } from '../Breadcrumbs';

describe('Breadcrumbs', () => {
  const mockItems = [
    { label: 'Home', href: '/' },
    { label: 'Dashboard', href: '/dashboard' },
    { label: 'Schedule', href: '/schedule' },
  ];

  describe('Rendering', () => {
    it('renders all breadcrumb items', () => {
      render(<Breadcrumbs items={mockItems} />);
      expect(screen.getByText('Home')).toBeInTheDocument();
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
      expect(screen.getByText('Schedule')).toBeInTheDocument();
    });

    it('renders separators between items', () => {
      render(<Breadcrumbs items={mockItems} />);
      const separators = screen.getAllByText('/');
      expect(separators.length).toBe(mockItems.length - 1);
    });

    it('renders first item as link', () => {
      render(<Breadcrumbs items={mockItems} />);
      const homeLink = screen.getByText('Home').closest('a');
      expect(homeLink).toHaveAttribute('href', '/');
    });

    it('renders middle items as links', () => {
      render(<Breadcrumbs items={mockItems} />);
      const dashboardLink = screen.getByText('Dashboard').closest('a');
      expect(dashboardLink).toHaveAttribute('href', '/dashboard');
    });

    it('renders last item without link', () => {
      render(<Breadcrumbs items={mockItems} />);
      const scheduleLink = screen.getByText('Schedule').closest('a');
      expect(scheduleLink).not.toBeInTheDocument();
    });

    it('applies current page styling to last item', () => {
      const { container } = render(<Breadcrumbs items={mockItems} />);
      const lastItem = screen.getByText('Schedule');
      expect(lastItem).toHaveClass('text-gray-900', 'font-medium');
    });
  });

  describe('Single Item', () => {
    it('renders single breadcrumb without separator', () => {
      const singleItem = [{ label: 'Home', href: '/' }];
      render(<Breadcrumbs items={singleItem} />);
      expect(screen.getByText('Home')).toBeInTheDocument();
      expect(screen.queryByText('/')).not.toBeInTheDocument();
    });

    it('renders single item without link', () => {
      const singleItem = [{ label: 'Home', href: '/' }];
      render(<Breadcrumbs items={singleItem} />);
      const homeLink = screen.getByText('Home').closest('a');
      expect(homeLink).not.toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    it('renders nothing when items array is empty', () => {
      const { container } = render(<Breadcrumbs items={[]} />);
      expect(container.firstChild).toBeEmptyDOMElement();
    });
  });

  describe('Icons', () => {
    it('renders home icon for first item', () => {
      render(<Breadcrumbs items={mockItems} showHomeIcon={true} />);
      const { container } = render(<Breadcrumbs items={mockItems} showHomeIcon={true} />);
      expect(container.querySelector('svg')).toBeInTheDocument();
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
      render(<Breadcrumbs items={mockItems} />);
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
        { label: 'Current', href: '/current' },
      ];
      render(<Breadcrumbs items={manyItems} />);
      expect(screen.getByText('Home')).toBeInTheDocument();
      expect(screen.getByText('Current')).toBeInTheDocument();
    });
  });

  describe('Truncation', () => {
    it('truncates long labels', () => {
      const longLabelItems = [
        { label: 'Home', href: '/' },
        {
          label: 'This is a very long breadcrumb label that should be truncated',
          href: '/long',
        },
      ];
      const { container } = render(<Breadcrumbs items={longLabelItems} />);
      const truncatedElement = container.querySelector('.truncate');
      expect(truncatedElement).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles items with special characters', () => {
      const specialItems = [
        { label: 'Home & Away', href: '/' },
        { label: 'C++ Programming', href: '/cpp' },
      ];
      render(<Breadcrumbs items={specialItems} />);
      expect(screen.getByText('Home & Away')).toBeInTheDocument();
      expect(screen.getByText('C++ Programming')).toBeInTheDocument();
    });

    it('handles items with very short labels', () => {
      const shortItems = [
        { label: 'A', href: '/a' },
        { label: 'B', href: '/b' },
      ];
      render(<Breadcrumbs items={shortItems} />);
      expect(screen.getByText('A')).toBeInTheDocument();
      expect(screen.getByText('B')).toBeInTheDocument();
    });
  });
});
