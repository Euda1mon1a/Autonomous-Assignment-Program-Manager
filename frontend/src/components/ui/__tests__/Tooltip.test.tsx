/**
 * Tests for Tooltip Component
 * Component: 39 - Hover tooltips
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Tooltip } from '../Tooltip';

describe('Tooltip', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  // Test 39.1: Render test
  describe('Rendering', () => {
    it('renders children', () => {
      render(
        <Tooltip content="Helpful info">
          <button>Hover me</button>
        </Tooltip>
      );

      expect(screen.getByText('Hover me')).toBeInTheDocument();
    });

    it('does not show tooltip initially', () => {
      render(
        <Tooltip content="Helpful info">
          <button>Hover me</button>
        </Tooltip>
      );

      expect(screen.queryByText('Helpful info')).not.toBeInTheDocument();
    });

    it('shows tooltip on mouse enter after delay', async () => {
      render(
        <Tooltip content="Helpful info" delay={200}>
          <button>Hover me</button>
        </Tooltip>
      );

      fireEvent.mouseEnter(screen.getByText('Hover me'));

      act(() => {
        jest.advanceTimersByTime(200);
      });

      expect(screen.getByText('Helpful info')).toBeInTheDocument();
    });

    it('hides tooltip on mouse leave', async () => {
      render(
        <Tooltip content="Helpful info" delay={0}>
          <button>Hover me</button>
        </Tooltip>
      );

      const button = screen.getByText('Hover me');
      fireEvent.mouseEnter(button);

      act(() => {
        jest.advanceTimersByTime(0);
      });

      expect(screen.getByText('Helpful info')).toBeInTheDocument();

      fireEvent.mouseLeave(button);

      expect(screen.queryByText('Helpful info')).not.toBeInTheDocument();
    });

    it('has proper tooltip role', () => {
      render(
        <Tooltip content="Helpful info" delay={0}>
          <button>Hover me</button>
        </Tooltip>
      );

      fireEvent.mouseEnter(screen.getByText('Hover me'));

      act(() => {
        jest.advanceTimersByTime(0);
      });

      const tooltip = screen.getByRole('tooltip');
      expect(tooltip).toBeInTheDocument();
    });
  });

  // Test 39.2: Position variants
  describe('Position Variants', () => {
    it('renders tooltip at top position (default)', () => {
      const { container } = render(
        <Tooltip content="Helpful info" position="top" delay={0}>
          <button>Hover me</button>
        </Tooltip>
      );

      fireEvent.mouseEnter(screen.getByText('Hover me'));

      act(() => {
        jest.advanceTimersByTime(0);
      });

      const tooltip = container.querySelector('.bottom-full.left-1\\/2');
      expect(tooltip).toBeInTheDocument();
    });

    it('renders tooltip at bottom position', () => {
      const { container } = render(
        <Tooltip content="Helpful info" position="bottom" delay={0}>
          <button>Hover me</button>
        </Tooltip>
      );

      fireEvent.mouseEnter(screen.getByText('Hover me'));

      act(() => {
        jest.advanceTimersByTime(0);
      });

      const tooltip = container.querySelector('.top-full.left-1\\/2');
      expect(tooltip).toBeInTheDocument();
    });

    it('renders tooltip at left position', () => {
      const { container } = render(
        <Tooltip content="Helpful info" position="left" delay={0}>
          <button>Hover me</button>
        </Tooltip>
      );

      fireEvent.mouseEnter(screen.getByText('Hover me'));

      act(() => {
        jest.advanceTimersByTime(0);
      });

      const tooltip = container.querySelector('.right-full.top-1\\/2');
      expect(tooltip).toBeInTheDocument();
    });

    it('renders tooltip at right position', () => {
      const { container } = render(
        <Tooltip content="Helpful info" position="right" delay={0}>
          <button>Hover me</button>
        </Tooltip>
      );

      fireEvent.mouseEnter(screen.getByText('Hover me'));

      act(() => {
        jest.advanceTimersByTime(0);
      });

      const tooltip = container.querySelector('.left-full.top-1\\/2');
      expect(tooltip).toBeInTheDocument();
    });
  });

  // Test 39.3: Accessibility and focus
  describe('Accessibility and Focus', () => {
    it('shows tooltip on focus', () => {
      render(
        <Tooltip content="Helpful info" delay={0}>
          <button>Focus me</button>
        </Tooltip>
      );

      const button = screen.getByText('Focus me');
      fireEvent.focus(button);

      act(() => {
        jest.advanceTimersByTime(0);
      });

      expect(screen.getByText('Helpful info')).toBeInTheDocument();
    });

    it('hides tooltip on blur', () => {
      render(
        <Tooltip content="Helpful info" delay={0}>
          <button>Focus me</button>
        </Tooltip>
      );

      const button = screen.getByText('Focus me');
      fireEvent.focus(button);

      act(() => {
        jest.advanceTimersByTime(0);
      });

      expect(screen.getByText('Helpful info')).toBeInTheDocument();

      fireEvent.blur(button);

      expect(screen.queryByText('Helpful info')).not.toBeInTheDocument();
    });

    it('is keyboard accessible', () => {
      render(
        <Tooltip content="Helpful info" delay={0}>
          <button>Tab to me</button>
        </Tooltip>
      );

      const button = screen.getByText('Tab to me');
      button.focus();
      fireEvent.focus(button);

      act(() => {
        jest.advanceTimersByTime(0);
      });

      expect(screen.getByText('Helpful info')).toBeInTheDocument();
    });
  });

  // Test 39.4: Delay and edge cases
  describe('Delay and Edge Cases', () => {
    it('respects custom delay', () => {
      render(
        <Tooltip content="Helpful info" delay={500}>
          <button>Hover me</button>
        </Tooltip>
      );

      fireEvent.mouseEnter(screen.getByText('Hover me'));

      act(() => {
        jest.advanceTimersByTime(300);
      });

      expect(screen.queryByText('Helpful info')).not.toBeInTheDocument();

      act(() => {
        jest.advanceTimersByTime(200);
      });

      expect(screen.getByText('Helpful info')).toBeInTheDocument();
    });

    it('cancels show timeout on quick mouse leave', () => {
      render(
        <Tooltip content="Helpful info" delay={200}>
          <button>Hover me</button>
        </Tooltip>
      );

      const button = screen.getByText('Hover me');
      fireEvent.mouseEnter(button);

      act(() => {
        jest.advanceTimersByTime(100);
      });

      fireEvent.mouseLeave(button);

      act(() => {
        jest.advanceTimersByTime(200);
      });

      expect(screen.queryByText('Helpful info')).not.toBeInTheDocument();
    });

    it('handles long content', () => {
      const longContent = 'This is a very long tooltip content that should still display correctly';

      render(
        <Tooltip content={longContent} delay={0}>
          <button>Hover me</button>
        </Tooltip>
      );

      fireEvent.mouseEnter(screen.getByText('Hover me'));

      act(() => {
        jest.advanceTimersByTime(0);
      });

      expect(screen.getByText(longContent)).toBeInTheDocument();
    });

    it('handles React node content', () => {
      const content = (
        <div>
          <strong>Title</strong>
          <p>Description</p>
        </div>
      );

      render(
        <Tooltip content={content} delay={0}>
          <button>Hover me</button>
        </Tooltip>
      );

      fireEvent.mouseEnter(screen.getByText('Hover me'));

      act(() => {
        jest.advanceTimersByTime(0);
      });

      expect(screen.getByText('Title')).toBeInTheDocument();
      expect(screen.getByText('Description')).toBeInTheDocument();
    });

    it('applies custom className', () => {
      const { container } = render(
        <Tooltip content="Helpful info" delay={0} className="custom-tooltip">
          <button>Hover me</button>
        </Tooltip>
      );

      expect(container.querySelector('.custom-tooltip')).toBeInTheDocument();
    });

    it('cleans up timeout on unmount', () => {
      const { unmount } = render(
        <Tooltip content="Helpful info" delay={200}>
          <button>Hover me</button>
        </Tooltip>
      );

      fireEvent.mouseEnter(screen.getByText('Hover me'));
      unmount();

      act(() => {
        jest.advanceTimersByTime(200);
      });

      // Should not show tooltip after unmount
      expect(screen.queryByText('Helpful info')).not.toBeInTheDocument();
    });

    it('renders arrow element', () => {
      const { container } = render(
        <Tooltip content="Helpful info" delay={0}>
          <button>Hover me</button>
        </Tooltip>
      );

      fireEvent.mouseEnter(screen.getByText('Hover me'));

      act(() => {
        jest.advanceTimersByTime(0);
      });

      const arrow = container.querySelector('.absolute.w-0.h-0.border-4');
      expect(arrow).toBeInTheDocument();
    });
  });
});
