/**
 * Tests for SummaryCard Component
 *
 * Tests rendering, loading states, and data display
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { SummaryCard } from '@/features/my-dashboard/SummaryCard';
import { Calendar, Briefcase, ArrowRightLeft } from 'lucide-react';

describe('SummaryCard', () => {
  describe('Basic Rendering', () => {
    it('should render title', () => {
      render(
        <SummaryCard
          title="Next Assignment"
          value="Today at 8 AM"
          icon={Calendar}
        />
      );

      expect(screen.getByText('Next Assignment')).toBeInTheDocument();
    });

    it('should render string value', () => {
      render(
        <SummaryCard
          title="Next Assignment"
          value="Today at 8 AM"
          icon={Calendar}
        />
      );

      expect(screen.getByText('Today at 8 AM')).toBeInTheDocument();
    });

    it('should render numeric value', () => {
      render(
        <SummaryCard
          title="Workload (4 weeks)"
          value={12}
          icon={Briefcase}
        />
      );

      expect(screen.getByText('12')).toBeInTheDocument();
    });

    it('should render zero value', () => {
      render(
        <SummaryCard
          title="Pending Swaps"
          value={0}
          icon={ArrowRightLeft}
        />
      );

      expect(screen.getByText('0')).toBeInTheDocument();
    });

    it('should render icon', () => {
      const { container } = render(
        <SummaryCard
          title="Test Card"
          value="Test Value"
          icon={Calendar}
        />
      );

      const icon = container.querySelector('svg');
      expect(icon).toBeInTheDocument();
    });
  });

  describe('Optional Props', () => {
    it('should render description when provided', () => {
      render(
        <SummaryCard
          title="Workload (4 weeks)"
          value={12}
          icon={Briefcase}
          description="shifts ahead"
        />
      );

      expect(screen.getByText('shifts ahead')).toBeInTheDocument();
    });

    it('should not render description when not provided', () => {
      const { container } = render(
        <SummaryCard
          title="Next Assignment"
          value="Today"
          icon={Calendar}
        />
      );

      const descriptionElement = container.querySelector('.text-xs');
      expect(descriptionElement).not.toBeInTheDocument();
    });

    it('should apply custom icon color', () => {
      const { container } = render(
        <SummaryCard
          title="Test Card"
          value="Test"
          icon={Calendar}
          iconColor="text-red-600"
        />
      );

      const icon = container.querySelector('.text-red-600');
      expect(icon).toBeInTheDocument();
    });

    it('should default to text-blue-600 icon color', () => {
      const { container } = render(
        <SummaryCard
          title="Test Card"
          value="Test"
          icon={Calendar}
        />
      );

      const icon = container.querySelector('.text-blue-600');
      expect(icon).toBeInTheDocument();
    });

    it('should apply custom background color', () => {
      const { container } = render(
        <SummaryCard
          title="Test Card"
          value="Test"
          icon={Calendar}
          bgColor="bg-red-50"
        />
      );

      const bgElement = container.querySelector('.bg-red-50');
      expect(bgElement).toBeInTheDocument();
    });

    it('should default to bg-blue-50 background color', () => {
      const { container } = render(
        <SummaryCard
          title="Test Card"
          value="Test"
          icon={Calendar}
        />
      );

      const bgElement = container.querySelector('.bg-blue-50');
      expect(bgElement).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('should render skeleton when loading', () => {
      const { container } = render(
        <SummaryCard
          title="Next Assignment"
          value="Today"
          icon={Calendar}
          isLoading={true}
        />
      );

      const skeleton = container.querySelector('.animate-pulse');
      expect(skeleton).toBeInTheDocument();
    });

    it('should not display value when loading', () => {
      render(
        <SummaryCard
          title="Next Assignment"
          value="Today at 8 AM"
          icon={Calendar}
          isLoading={true}
        />
      );

      expect(screen.queryByText('Today at 8 AM')).not.toBeInTheDocument();
    });

    it('should not display title text when loading', () => {
      render(
        <SummaryCard
          title="Next Assignment"
          value="Today"
          icon={Calendar}
          isLoading={true}
        />
      );

      expect(screen.queryByText('Next Assignment')).not.toBeInTheDocument();
    });

    it('should show multiple skeleton elements when loading', () => {
      const { container } = render(
        <SummaryCard
          title="Test Card"
          value="Test"
          icon={Calendar}
          isLoading={true}
        />
      );

      const skeletons = container.querySelectorAll('.bg-gray-200, .bg-gray-300');
      expect(skeletons.length).toBeGreaterThan(1);
    });
  });

  describe('Null/Undefined Values', () => {
    it('should display dash for null value', () => {
      render(
        <SummaryCard
          title="Next Assignment"
          value={null as any}
          icon={Calendar}
        />
      );

      expect(screen.getByText('-')).toBeInTheDocument();
    });

    it('should display dash for undefined value', () => {
      render(
        <SummaryCard
          title="Next Assignment"
          value={undefined as any}
          icon={Calendar}
        />
      );

      expect(screen.getByText('-')).toBeInTheDocument();
    });

    it('should not display dash for empty string', () => {
      render(
        <SummaryCard
          title="Next Assignment"
          value=""
          icon={Calendar}
        />
      );

      // Empty string should be rendered as is, not as a dash
      expect(screen.queryByText('-')).not.toBeInTheDocument();
    });

    it('should display zero without converting to dash', () => {
      render(
        <SummaryCard
          title="Pending Swaps"
          value={0}
          icon={ArrowRightLeft}
        />
      );

      expect(screen.getByText('0')).toBeInTheDocument();
      expect(screen.queryByText('-')).not.toBeInTheDocument();
    });
  });

  describe('Styling', () => {
    it('should have hover shadow effect', () => {
      const { container } = render(
        <SummaryCard
          title="Test Card"
          value="Test"
          icon={Calendar}
        />
      );

      const card = container.querySelector('.hover\\:shadow-md');
      expect(card).toBeInTheDocument();
    });

    it('should have white background', () => {
      const { container } = render(
        <SummaryCard
          title="Test Card"
          value="Test"
          icon={Calendar}
        />
      );

      const card = container.querySelector('.bg-white');
      expect(card).toBeInTheDocument();
    });

    it('should have rounded corners', () => {
      const { container } = render(
        <SummaryCard
          title="Test Card"
          value="Test"
          icon={Calendar}
        />
      );

      const card = container.querySelector('.rounded-lg');
      expect(card).toBeInTheDocument();
    });

    it('should have border', () => {
      const { container } = render(
        <SummaryCard
          title="Test Card"
          value="Test"
          icon={Calendar}
        />
      );

      const card = container.querySelector('.border-gray-200');
      expect(card).toBeInTheDocument();
    });
  });

  describe('Text Truncation', () => {
    it('should truncate long titles', () => {
      const { container } = render(
        <SummaryCard
          title="This is a very long title that should be truncated"
          value="Test"
          icon={Calendar}
        />
      );

      const titleElement = container.querySelector('.truncate');
      expect(titleElement).toBeInTheDocument();
      expect(titleElement).toHaveTextContent(
        'This is a very long title that should be truncated'
      );
    });

    it('should truncate long values', () => {
      const { container } = render(
        <SummaryCard
          title="Test"
          value="This is a very long value that should be truncated to fit in the card"
          icon={Calendar}
        />
      );

      const valueElement = container.querySelector('.text-2xl');
      expect(valueElement).toHaveClass('truncate');
    });

    it('should line-clamp description to 2 lines', () => {
      const { container } = render(
        <SummaryCard
          title="Test"
          value="Test"
          icon={Calendar}
          description="This is a very long description that should be clamped to two lines only"
        />
      );

      const descElement = container.querySelector('.line-clamp-2');
      expect(descElement).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have semantic structure', () => {
      const { container } = render(
        <SummaryCard
          title="Next Assignment"
          value="Today at 8 AM"
          icon={Calendar}
          description="upcoming shift"
        />
      );

      // Should have paragraph elements for text content
      const paragraphs = container.querySelectorAll('p');
      expect(paragraphs.length).toBeGreaterThan(0);
    });

    it('should render all text content as readable text', () => {
      render(
        <SummaryCard
          title="Workload (4 weeks)"
          value={12}
          icon={Briefcase}
          description="shifts ahead"
        />
      );

      // All text should be accessible
      expect(screen.getByText('Workload (4 weeks)')).toBeVisible();
      expect(screen.getByText('12')).toBeVisible();
      expect(screen.getByText('shifts ahead')).toBeVisible();
    });
  });

  describe('Different Icon Types', () => {
    it('should render Calendar icon', () => {
      const { container } = render(
        <SummaryCard
          title="Test"
          value="Test"
          icon={Calendar}
        />
      );

      const icon = container.querySelector('svg');
      expect(icon).toBeInTheDocument();
    });

    it('should render Briefcase icon', () => {
      const { container } = render(
        <SummaryCard
          title="Test"
          value="Test"
          icon={Briefcase}
        />
      );

      const icon = container.querySelector('svg');
      expect(icon).toBeInTheDocument();
    });

    it('should render ArrowRightLeft icon', () => {
      const { container } = render(
        <SummaryCard
          title="Test"
          value="Test"
          icon={ArrowRightLeft}
        />
      );

      const icon = container.querySelector('svg');
      expect(icon).toBeInTheDocument();
    });
  });

  describe('Responsive Design', () => {
    it('should have responsive text sizes', () => {
      const { container } = render(
        <SummaryCard
          title="Test"
          value="Test Value"
          icon={Calendar}
        />
      );

      const valueElement = container.querySelector('.text-2xl.md\\:text-3xl');
      expect(valueElement).toBeInTheDocument();
    });

    it('should have responsive padding', () => {
      const { container } = render(
        <SummaryCard
          title="Test"
          value="Test"
          icon={Calendar}
        />
      );

      const card = container.querySelector('.p-4.md\\:p-6');
      expect(card).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle very large numbers', () => {
      render(
        <SummaryCard
          title="Total Assignments"
          value={999999}
          icon={Briefcase}
        />
      );

      expect(screen.getByText('999999')).toBeInTheDocument();
    });

    it('should handle negative numbers', () => {
      render(
        <SummaryCard
          title="Balance"
          value={-5}
          icon={Briefcase}
        />
      );

      expect(screen.getByText('-5')).toBeInTheDocument();
    });

    it('should handle decimal numbers', () => {
      render(
        <SummaryCard
          title="Average"
          value={12.5}
          icon={Briefcase}
        />
      );

      expect(screen.getByText('12.5')).toBeInTheDocument();
    });

    it('should handle special characters in strings', () => {
      render(
        <SummaryCard
          title="Special & Characters"
          value="Value with <html> & symbols"
          icon={Calendar}
        />
      );

      expect(screen.getByText('Special & Characters')).toBeInTheDocument();
      expect(screen.getByText('Value with <html> & symbols')).toBeInTheDocument();
    });
  });
});
