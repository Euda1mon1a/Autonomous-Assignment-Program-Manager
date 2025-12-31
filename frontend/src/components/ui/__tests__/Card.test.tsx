import { renderWithProviders } from '@/test-utils';
/**
 * Tests for Card Component
 * Component: 41 - Card container
 */

import React from 'react';
import { renderWithProviders as render, screen } from '@/test-utils';
import '@testing-library/jest-dom';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../Card';

describe('Card', () => {
  // Test 41.1: Render test
  describe('Rendering', () => {
    it('renders with children', () => {
      render(<Card><div>Card content</div></Card>);

      expect(screen.getByText('Card content')).toBeInTheDocument();
    });

    it('renders with default padding', () => {
      const { container } = render(<Card><div>Content</div></Card>);

      expect(container.querySelector('.p-4')).toBeInTheDocument();
    });

    it('renders with default shadow', () => {
      const { container } = render(<Card><div>Content</div></Card>);

      expect(container.querySelector('.shadow-sm')).toBeInTheDocument();
    });

    it('renders with white background', () => {
      const { container } = render(<Card><div>Content</div></Card>);

      expect(container.querySelector('.bg-white')).toBeInTheDocument();
    });

    it('renders with rounded corners', () => {
      const { container } = render(<Card><div>Content</div></Card>);

      expect(container.querySelector('.rounded-lg')).toBeInTheDocument();
    });
  });

  // Test 41.2: Prop variants
  describe('Prop Variants', () => {
    it('renders with no padding', () => {
      const { container } = render(<Card padding="none"><div>Content</div></Card>);

      expect(container.querySelector('.p-4')).not.toBeInTheDocument();
    });

    it('renders with small padding', () => {
      const { container } = render(<Card padding="sm"><div>Content</div></Card>);

      expect(container.querySelector('.p-3')).toBeInTheDocument();
    });

    it('renders with large padding', () => {
      const { container } = render(<Card padding="lg"><div>Content</div></Card>);

      expect(container.querySelector('.p-6')).toBeInTheDocument();
    });

    it('renders with no shadow', () => {
      const { container } = render(<Card shadow="none"><div>Content</div></Card>);

      const card = container.querySelector('.bg-white.rounded-lg');
      expect(card).not.toHaveClass('shadow-sm', 'shadow', 'shadow-md', 'shadow-lg');
    });

    it('renders with large shadow', () => {
      const { container } = render(<Card shadow="lg"><div>Content</div></Card>);

      expect(container.querySelector('.shadow-lg')).toBeInTheDocument();
    });

    it('applies hover effect when hover prop is true', () => {
      const { container } = render(<Card hover><div>Content</div></Card>);

      expect(container.querySelector('.transition-shadow.hover\\:shadow-md')).toBeInTheDocument();
    });

    it('does not apply hover effect by default', () => {
      const { container } = render(<Card><div>Content</div></Card>);

      const card = container.querySelector('.bg-white.rounded-lg');
      expect(card).not.toHaveClass('hover:shadow-md');
    });

    it('applies custom className', () => {
      const { container } = render(<Card className="custom-card"><div>Content</div></Card>);

      expect(container.querySelector('.custom-card')).toBeInTheDocument();
    });
  });

  // Test 41.3: Sub-components
  describe('Sub-components', () => {
    it('renders CardHeader', () => {
      render(
        <Card>
          <CardHeader>
            <div>Header content</div>
          </CardHeader>
        </Card>
      );

      expect(screen.getByText('Header content')).toBeInTheDocument();
    });

    it('renders CardTitle', () => {
      render(
        <Card>
          <CardHeader>
            <CardTitle>Card Title</CardTitle>
          </CardHeader>
        </Card>
      );

      const title = screen.getByText('Card Title');
      expect(title.tagName).toBe('H3');
    });

    it('renders CardDescription', () => {
      render(
        <Card>
          <CardHeader>
            <CardDescription>Card description text</CardDescription>
          </CardHeader>
        </Card>
      );

      expect(screen.getByText('Card description text')).toBeInTheDocument();
    });

    it('renders CardContent', () => {
      render(
        <Card>
          <CardContent>
            <p>Main content</p>
          </CardContent>
        </Card>
      );

      expect(screen.getByText('Main content')).toBeInTheDocument();
    });

    it('renders CardFooter', () => {
      render(
        <Card>
          <CardFooter>
            <button>Action</button>
          </CardFooter>
        </Card>
      );

      expect(screen.getByText('Action')).toBeInTheDocument();
    });

    it('CardHeader has bottom margin', () => {
      const { container } = render(
        <Card>
          <CardHeader><div>Header</div></CardHeader>
        </Card>
      );

      expect(container.querySelector('.mb-4')).toBeInTheDocument();
    });

    it('CardFooter has top margin and border', () => {
      const { container } = render(
        <Card>
          <CardFooter><div>Footer</div></CardFooter>
        </Card>
      );

      expect(container.querySelector('.mt-4.pt-4.border-t')).toBeInTheDocument();
    });

    it('CardTitle has proper text styling', () => {
      const { container } = render(
        <Card>
          <CardTitle>Title</CardTitle>
        </Card>
      );

      expect(container.querySelector('.text-lg.font-semibold.text-gray-900')).toBeInTheDocument();
    });

    it('CardDescription has gray text', () => {
      const { container } = render(
        <Card>
          <CardDescription>Description</CardDescription>
        </Card>
      );

      expect(container.querySelector('.text-sm.text-gray-600')).toBeInTheDocument();
    });
  });

  // Test 41.4: Edge cases and composition
  describe('Edge Cases and Composition', () => {
    it('renders complete card structure', () => {
      render(
        <Card>
          <CardHeader>
            <CardTitle>Title</CardTitle>
            <CardDescription>Description</CardDescription>
          </CardHeader>
          <CardContent>
            <p>Content</p>
          </CardContent>
          <CardFooter>
            <button>Action</button>
          </CardFooter>
        </Card>
      );

      expect(screen.getByText('Title')).toBeInTheDocument();
      expect(screen.getByText('Description')).toBeInTheDocument();
      expect(screen.getByText('Content')).toBeInTheDocument();
      expect(screen.getByText('Action')).toBeInTheDocument();
    });

    it('handles complex content', () => {
      render(
        <Card>
          <CardContent>
            <div>
              <h4>Subtitle</h4>
              <ul>
                <li>Item 1</li>
                <li>Item 2</li>
              </ul>
            </div>
          </CardContent>
        </Card>
      );

      expect(screen.getByText('Subtitle')).toBeInTheDocument();
      expect(screen.getByText('Item 1')).toBeInTheDocument();
      expect(screen.getByText('Item 2')).toBeInTheDocument();
    });

    it('sub-components accept custom className', () => {
      const { container } = render(
        <Card>
          <CardHeader className="custom-header">Header</CardHeader>
          <CardContent className="custom-content">Content</CardContent>
          <CardFooter className="custom-footer">Footer</CardFooter>
        </Card>
      );

      expect(container.querySelector('.custom-header')).toBeInTheDocument();
      expect(container.querySelector('.custom-content')).toBeInTheDocument();
      expect(container.querySelector('.custom-footer')).toBeInTheDocument();
    });

    it('renders without header', () => {
      render(
        <Card>
          <CardContent>Just content</CardContent>
        </Card>
      );

      expect(screen.getByText('Just content')).toBeInTheDocument();
    });

    it('renders without footer', () => {
      render(
        <Card>
          <CardHeader>
            <CardTitle>Title</CardTitle>
          </CardHeader>
          <CardContent>Content</CardContent>
        </Card>
      );

      expect(screen.getByText('Title')).toBeInTheDocument();
      expect(screen.getByText('Content')).toBeInTheDocument();
    });

    it('applies all props together', () => {
      const { container } = render(
        <Card padding="lg" shadow="lg" hover className="custom-card">
          <div>Content</div>
        </Card>
      );

      const card = container.firstChild;
      expect(card).toHaveClass('p-6');
      expect(card).toHaveClass('shadow-lg');
      expect(card).toHaveClass('transition-shadow');
      expect(card).toHaveClass('custom-card');
    });
  });
});
