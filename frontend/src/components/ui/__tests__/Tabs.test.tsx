/**
 * Tests for Tabs Component
 * Component: 47 - Tab navigation
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Tabs, Tab } from '../Tabs';

describe('Tabs', () => {
  const mockTabs: Tab[] = [
    { id: 'tab1', label: 'Tab 1', content: <div>Content 1</div> },
    { id: 'tab2', label: 'Tab 2', content: <div>Content 2</div> },
    { id: 'tab3', label: 'Tab 3', content: <div>Content 3</div> },
  ];

  // Test 47.1: Render test
  describe('Rendering', () => {
    it('renders all tab labels', () => {
      render(<Tabs tabs={mockTabs} />);

      expect(screen.getByText('Tab 1')).toBeInTheDocument();
      expect(screen.getByText('Tab 2')).toBeInTheDocument();
      expect(screen.getByText('Tab 3')).toBeInTheDocument();
    });

    it('renders first tab content by default', () => {
      render(<Tabs tabs={mockTabs} />);

      expect(screen.getByText('Content 1')).toBeInTheDocument();
      expect(screen.queryByText('Content 2')).not.toBeInTheDocument();
    });

    it('renders defaultTab when specified', () => {
      render(<Tabs tabs={mockTabs} defaultTab="tab2" />);

      expect(screen.getByText('Content 2')).toBeInTheDocument();
      expect(screen.queryByText('Content 1')).not.toBeInTheDocument();
    });

    it('renders tabs with role tablist', () => {
      render(<Tabs tabs={mockTabs} />);

      expect(screen.getByRole('tablist')).toBeInTheDocument();
    });

    it('renders tab buttons with role tab', () => {
      render(<Tabs tabs={mockTabs} />);

      const tabs = screen.getAllByRole('tab');
      expect(tabs).toHaveLength(3);
    });

    it('renders tabpanel with correct role', () => {
      render(<Tabs tabs={mockTabs} />);

      expect(screen.getByRole('tabpanel')).toBeInTheDocument();
    });
  });

  // Test 47.2: Tab switching and interaction
  describe('Tab Switching', () => {
    it('switches tab content on click', () => {
      render(<Tabs tabs={mockTabs} />);

      expect(screen.getByText('Content 1')).toBeInTheDocument();

      fireEvent.click(screen.getByText('Tab 2'));

      expect(screen.getByText('Content 2')).toBeInTheDocument();
      expect(screen.queryByText('Content 1')).not.toBeInTheDocument();
    });

    it('calls onChange callback when tab changes', () => {
      const onChange = jest.fn();
      render(<Tabs tabs={mockTabs} onChange={onChange} />);

      fireEvent.click(screen.getByText('Tab 2'));

      expect(onChange).toHaveBeenCalledWith('tab2');
    });

    it('applies aria-selected to active tab', () => {
      render(<Tabs tabs={mockTabs} defaultTab="tab2" />);

      const tab1 = screen.getByText('Tab 1');
      const tab2 = screen.getByText('Tab 2');

      expect(tab1).toHaveAttribute('aria-selected', 'false');
      expect(tab2).toHaveAttribute('aria-selected', 'true');
    });

    it('associates tab with tabpanel via aria-controls', () => {
      render(<Tabs tabs={mockTabs} />);

      const tab1 = screen.getByText('Tab 1');
      expect(tab1).toHaveAttribute('aria-controls', 'panel-tab1');
    });

    it('renders tabs with icons', () => {
      const tabsWithIcons: Tab[] = [
        { id: 'tab1', label: 'Home', icon: <span>🏠</span>, content: <div>Home</div> },
        { id: 'tab2', label: 'Profile', icon: <span>👤</span>, content: <div>Profile</div> },
      ];

      render(<Tabs tabs={tabsWithIcons} />);

      expect(screen.getByText('🏠')).toBeInTheDocument();
      expect(screen.getByText('👤')).toBeInTheDocument();
    });
  });

  // Test 47.3: Accessibility and disabled state
  describe('Accessibility and Disabled State', () => {
    it('disables tabs when disabled prop is true', () => {
      const tabsWithDisabled: Tab[] = [
        { id: 'tab1', label: 'Tab 1', content: <div>Content 1</div> },
        { id: 'tab2', label: 'Tab 2', content: <div>Content 2</div>, disabled: true },
      ];

      render(<Tabs tabs={tabsWithDisabled} />);

      const tab2 = screen.getByText('Tab 2');
      expect(tab2).toBeDisabled();
    });

    it('does not switch to disabled tab', () => {
      const tabsWithDisabled: Tab[] = [
        { id: 'tab1', label: 'Tab 1', content: <div>Content 1</div> },
        { id: 'tab2', label: 'Tab 2', content: <div>Content 2</div>, disabled: true },
      ];

      render(<Tabs tabs={tabsWithDisabled} />);

      fireEvent.click(screen.getByText('Tab 2'));

      expect(screen.getByText('Content 1')).toBeInTheDocument();
      expect(screen.queryByText('Content 2')).not.toBeInTheDocument();
    });

    it('is keyboard accessible', () => {
      render(<Tabs tabs={mockTabs} />);

      const tab1 = screen.getByText('Tab 1');
      tab1.focus();

      expect(tab1).toHaveFocus();
    });

    it('has focus ring styles', () => {
      const { container } = render(<Tabs tabs={mockTabs} />);

      expect(container.querySelector('.focus\\:outline-none.focus\\:ring-2')).toBeInTheDocument();
    });

    it('applies disabled styling to disabled tabs', () => {
      const tabsWithDisabled: Tab[] = [
        { id: 'tab1', label: 'Tab 1', content: <div>Content 1</div> },
        { id: 'tab2', label: 'Tab 2', content: <div>Content 2</div>, disabled: true },
      ];

      const { container } = render(<Tabs tabs={tabsWithDisabled} />);

      const disabledTab = screen.getByText('Tab 2');
      expect(disabledTab).toHaveClass('disabled:opacity-50', 'disabled:cursor-not-allowed');
    });
  });

  // Test 47.4: Variants and edge cases
  describe('Variants and Edge Cases', () => {
    it('renders default variant with underline style', () => {
      const { container } = render(<Tabs tabs={mockTabs} variant="default" />);

      expect(container.querySelector('.border-b.border-gray-200')).toBeInTheDocument();
    });

    it('renders pills variant', () => {
      const { container } = render(<Tabs tabs={mockTabs} variant="pills" />);

      expect(container.querySelector('.bg-gray-100.rounded-lg')).toBeInTheDocument();
    });

    it('applies active styles for default variant', () => {
      render(<Tabs tabs={mockTabs} variant="default" />);

      const activeTab = screen.getByText('Tab 1');
      expect(activeTab).toHaveClass('border-blue-600', 'text-blue-600');
    });

    it('applies active styles for pills variant', () => {
      render(<Tabs tabs={mockTabs} variant="pills" />);

      const activeTab = screen.getByText('Tab 1');
      expect(activeTab).toHaveClass('bg-white', 'text-gray-900', 'shadow-sm');
    });

    it('applies custom className', () => {
      const { container } = render(<Tabs tabs={mockTabs} className="custom-tabs" />);

      expect(container.querySelector('.custom-tabs')).toBeInTheDocument();
    });

    it('handles empty tabs array', () => {
      render(<Tabs tabs={[]} />);

      expect(screen.queryByRole('tab')).not.toBeInTheDocument();
    });

    it('handles single tab', () => {
      const singleTab: Tab[] = [
        { id: 'only', label: 'Only Tab', content: <div>Only Content</div> },
      ];

      render(<Tabs tabs={singleTab} />);

      expect(screen.getByText('Only Tab')).toBeInTheDocument();
      expect(screen.getByText('Only Content')).toBeInTheDocument();
    });

    it('handles complex content', () => {
      const complexTabs: Tab[] = [
        {
          id: 'tab1',
          label: 'Complex',
          content: (
            <div>
              <h3>Title</h3>
              <p>Paragraph</p>
              <button>Action</button>
            </div>
          ),
        },
      ];

      render(<Tabs tabs={complexTabs} />);

      expect(screen.getByText('Title')).toBeInTheDocument();
      expect(screen.getByText('Paragraph')).toBeInTheDocument();
      expect(screen.getByText('Action')).toBeInTheDocument();
    });

    it('maintains state across re-renders', () => {
      const { rerender } = render(<Tabs tabs={mockTabs} />);

      fireEvent.click(screen.getByText('Tab 2'));
      expect(screen.getByText('Content 2')).toBeInTheDocument();

      rerender(<Tabs tabs={mockTabs} />);

      expect(screen.getByText('Content 2')).toBeInTheDocument();
    });
  });
});
