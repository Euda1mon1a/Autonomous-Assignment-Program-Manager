/**
 * Tests for Container Component
 * Component: layout/Container - Page container layout
 */

import React from 'react';
import { render, screen } from '@/test-utils';
import '@testing-library/jest-dom';
import { Container } from '../Container';

describe('Container', () => {
  describe('Rendering', () => {
    it('renders children', () => {
      render(
        <Container>
          <div>Test content</div>
        </Container>
      );
      expect(screen.getByText('Test content')).toBeInTheDocument();
    });

    it('renders multiple children', () => {
      render(
        <Container>
          <div>First child</div>
          <div>Second child</div>
        </Container>
      );
      expect(screen.getByText('First child')).toBeInTheDocument();
      expect(screen.getByText('Second child')).toBeInTheDocument();
    });
  });

  describe('Styling', () => {
    it('has default max-width constraint', () => {
      const { container } = render(
        <Container>
          <div>Content</div>
        </Container>
      );
      // Default maxWidth is 'xl' -> max-w-screen-xl
      expect(container.firstChild).toHaveClass('max-w-screen-xl');
    });

    it('has default horizontal padding', () => {
      const { container } = render(
        <Container>
          <div>Content</div>
        </Container>
      );
      expect(container.firstChild).toHaveClass('px-4', 'sm:px-6', 'lg:px-8');
    });

    it('centers content horizontally by default', () => {
      const { container } = render(
        <Container>
          <div>Content</div>
        </Container>
      );
      expect(container.firstChild).toHaveClass('mx-auto');
    });

    it('applies custom className', () => {
      const { container } = render(
        <Container className="custom-class">
          <div>Content</div>
        </Container>
      );
      expect(container.firstChild).toHaveClass('custom-class');
    });
  });

  describe('MaxWidth Variants', () => {
    it('renders sm container', () => {
      const { container } = render(
        <Container maxWidth="sm">
          <div>Content</div>
        </Container>
      );
      expect(container.firstChild).toHaveClass('max-w-screen-sm');
    });

    it('renders md container', () => {
      const { container } = render(
        <Container maxWidth="md">
          <div>Content</div>
        </Container>
      );
      expect(container.firstChild).toHaveClass('max-w-screen-md');
    });

    it('renders lg container', () => {
      const { container } = render(
        <Container maxWidth="lg">
          <div>Content</div>
        </Container>
      );
      expect(container.firstChild).toHaveClass('max-w-screen-lg');
    });

    it('renders full-width container', () => {
      const { container } = render(
        <Container maxWidth="full">
          <div>Content</div>
        </Container>
      );
      expect(container.firstChild).toHaveClass('max-w-full');
    });
  });

  describe('Padding', () => {
    it('renders with padding by default', () => {
      const { container } = render(
        <Container>
          <div>Content</div>
        </Container>
      );
      expect(container.firstChild).toHaveClass('px-4');
    });

    it('renders without padding when disabled', () => {
      const { container } = render(
        <Container padding={false}>
          <div>Content</div>
        </Container>
      );
      expect(container.firstChild).not.toHaveClass('px-4');
    });
  });

  describe('Center', () => {
    it('centers content by default', () => {
      const { container } = render(
        <Container>
          <div>Content</div>
        </Container>
      );
      expect(container.firstChild).toHaveClass('mx-auto');
    });

    it('does not center when disabled', () => {
      const { container } = render(
        <Container center={false}>
          <div>Content</div>
        </Container>
      );
      expect(container.firstChild).not.toHaveClass('mx-auto');
    });
  });

  describe('AsMain', () => {
    it('renders as div by default', () => {
      const { container } = render(
        <Container>
          <div>Content</div>
        </Container>
      );
      expect(container.firstChild?.nodeName).toBe('DIV');
    });

    it('adds main role when asMain is true', () => {
      render(
        <Container asMain>
          <div>Content</div>
        </Container>
      );
      expect(screen.getByRole('main')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles nested containers', () => {
      render(
        <Container>
          <Container maxWidth="sm">
            <div>Nested content</div>
          </Container>
        </Container>
      );
      expect(screen.getByText('Nested content')).toBeInTheDocument();
    });

    it('handles very long content', () => {
      const longContent = 'Lorem ipsum '.repeat(100).trim();
      render(
        <Container>
          <div>{longContent}</div>
        </Container>
      );
      expect(screen.getByText(longContent)).toBeInTheDocument();
    });

    it('handles empty children', () => {
      const { container } = render(<Container>{null}</Container>);
      expect(container.firstChild).toBeInTheDocument();
    });
  });

  describe('Responsive Behavior', () => {
    it('has responsive padding classes', () => {
      const { container } = render(
        <Container>
          <div>Content</div>
        </Container>
      );
      const element = container.firstChild;
      expect(element).toHaveClass('px-4'); // mobile
      expect(element).toHaveClass('sm:px-6'); // tablet
      expect(element).toHaveClass('lg:px-8'); // desktop
    });
  });
});
