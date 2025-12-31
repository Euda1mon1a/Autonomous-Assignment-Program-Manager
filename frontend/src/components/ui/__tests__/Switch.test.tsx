import { renderWithProviders } from '@/test-utils';
/**
 * Tests for Switch Component
 * Component: 34 - Toggle switch
 */

import React from 'react';
import { renderWithProviders as render, screen, fireEvent } from '@/test-utils';
import '@testing-library/jest-dom';
import { Switch } from '../Switch';

describe('Switch', () => {
  const mockOnChange = jest.fn();

  beforeEach(() => {
    mockOnChange.mockClear();
  });

  // Test 34.1: Render test
  describe('Rendering', () => {
    it('renders unchecked switch', () => {
      render(<Switch checked={false} onChange={mockOnChange} />);

      const switchElement = screen.getByRole('switch');
      expect(switchElement).toHaveAttribute('aria-checked', 'false');
    });

    it('renders checked switch', () => {
      render(<Switch checked={true} onChange={mockOnChange} />);

      const switchElement = screen.getByRole('switch');
      expect(switchElement).toHaveAttribute('aria-checked', 'true');
    });

    it('renders with label', () => {
      render(<Switch checked={false} onChange={mockOnChange} label="Enable feature" />);

      expect(screen.getByText('Enable feature')).toBeInTheDocument();
    });

    it('renders with description', () => {
      render(
        <Switch checked={false} onChange={mockOnChange} description="This enables the feature" />
      );

      expect(screen.getByText('This enables the feature')).toBeInTheDocument();
    });

    it('renders with both label and description', () => {
      render(
        <Switch
          checked={false}
          onChange={mockOnChange}
          label="Feature Name"
          description="Feature description"
        />
      );

      expect(screen.getByText('Feature Name')).toBeInTheDocument();
      expect(screen.getByText('Feature description')).toBeInTheDocument();
    });
  });

  // Test 34.2: Size variants
  describe('Size Variants', () => {
    it('renders small size', () => {
      const { container } = render(<Switch checked={false} onChange={mockOnChange} size="sm" />);

      const switchElement = container.querySelector('.w-9.h-5');
      expect(switchElement).toBeInTheDocument();
    });

    it('renders medium size (default)', () => {
      const { container } = render(<Switch checked={false} onChange={mockOnChange} size="md" />);

      const switchElement = container.querySelector('.w-11.h-6');
      expect(switchElement).toBeInTheDocument();
    });

    it('renders large size', () => {
      const { container } = render(<Switch checked={false} onChange={mockOnChange} size="lg" />);

      const switchElement = container.querySelector('.w-14.h-7');
      expect(switchElement).toBeInTheDocument();
    });

    it('uses medium size when no size specified', () => {
      const { container } = render(<Switch checked={false} onChange={mockOnChange} />);

      const switchElement = container.querySelector('.w-11.h-6');
      expect(switchElement).toBeInTheDocument();
    });
  });

  // Test 34.3: Accessibility and interaction
  describe('Accessibility and Interaction', () => {
    it('toggles on click', () => {
      render(<Switch checked={false} onChange={mockOnChange} />);

      const switchElement = screen.getByRole('switch');
      fireEvent.click(switchElement);

      expect(mockOnChange).toHaveBeenCalledWith(true);
    });

    it('toggles off when clicked while checked', () => {
      render(<Switch checked={true} onChange={mockOnChange} />);

      const switchElement = screen.getByRole('switch');
      fireEvent.click(switchElement);

      expect(mockOnChange).toHaveBeenCalledWith(false);
    });

    it('toggles on Space key', () => {
      render(<Switch checked={false} onChange={mockOnChange} />);

      const switchElement = screen.getByRole('switch');
      fireEvent.keyDown(switchElement, { key: ' ' });

      expect(mockOnChange).toHaveBeenCalledWith(true);
    });

    it('toggles on Enter key', () => {
      render(<Switch checked={false} onChange={mockOnChange} />);

      const switchElement = screen.getByRole('switch');
      fireEvent.keyDown(switchElement, { key: 'Enter' });

      expect(mockOnChange).toHaveBeenCalledWith(true);
    });

    it('prevents default on Space key to prevent scrolling', () => {
      render(<Switch checked={false} onChange={mockOnChange} />);

      const switchElement = screen.getByRole('switch');
      const event = new KeyboardEvent('keydown', { key: ' ' });
      const preventDefaultSpy = jest.spyOn(event, 'preventDefault');

      fireEvent.keyDown(switchElement, event);

      expect(preventDefaultSpy).toHaveBeenCalled();
    });

    it('has proper ARIA role and checked state', () => {
      const { rerender } = render(<Switch checked={false} onChange={mockOnChange} />);

      let switchElement = screen.getByRole('switch');
      expect(switchElement).toHaveAttribute('aria-checked', 'false');

      rerender(<Switch checked={true} onChange={mockOnChange} />);

      switchElement = screen.getByRole('switch');
      expect(switchElement).toHaveAttribute('aria-checked', 'true');
    });

    it('is keyboard focusable', () => {
      render(<Switch checked={false} onChange={mockOnChange} />);

      const switchElement = screen.getByRole('switch');
      switchElement.focus();

      expect(switchElement).toHaveFocus();
    });
  });

  // Test 34.4: Disabled state and edge cases
  describe('Disabled State and Edge Cases', () => {
    it('does not toggle when disabled', () => {
      render(<Switch checked={false} onChange={mockOnChange} disabled />);

      const switchElement = screen.getByRole('switch');
      expect(switchElement).toBeDisabled();

      fireEvent.click(switchElement);

      expect(mockOnChange).not.toHaveBeenCalled();
    });

    it('applies disabled styling', () => {
      const { container } = render(<Switch checked={false} onChange={mockOnChange} disabled />);

      const switchElement = container.querySelector('.opacity-50.cursor-not-allowed');
      expect(switchElement).toBeInTheDocument();
    });

    it('disables label text color when disabled', () => {
      render(<Switch checked={false} onChange={mockOnChange} label="Feature" disabled />);

      const label = screen.getByText('Feature').closest('div');
      expect(label).toHaveClass('text-gray-400');
    });

    it('applies checked background color', () => {
      const { container } = render(<Switch checked={true} onChange={mockOnChange} />);

      const switchElement = container.querySelector('.bg-blue-600');
      expect(switchElement).toBeInTheDocument();
    });

    it('applies unchecked background color', () => {
      const { container } = render(<Switch checked={false} onChange={mockOnChange} />);

      const switchElement = container.querySelector('.bg-gray-200');
      expect(switchElement).toBeInTheDocument();
    });

    it('translates thumb when checked', () => {
      const { container } = render(<Switch checked={true} onChange={mockOnChange} size="md" />);

      const thumb = container.querySelector('.translate-x-5');
      expect(thumb).toBeInTheDocument();
    });

    it('does not translate thumb when unchecked', () => {
      const { container } = render(<Switch checked={false} onChange={mockOnChange} size="md" />);

      const thumb = container.querySelector('.translate-x-0\\.5');
      expect(thumb).toBeInTheDocument();
    });

    it('applies custom className', () => {
      const { container } = render(
        <Switch checked={false} onChange={mockOnChange} className="custom-class" />
      );

      expect(container.querySelector('.switch-component.custom-class')).toBeInTheDocument();
    });

    it('handles rapid toggling', () => {
      render(<Switch checked={false} onChange={mockOnChange} />);

      const switchElement = screen.getByRole('switch');

      fireEvent.click(switchElement);
      fireEvent.click(switchElement);
      fireEvent.click(switchElement);

      expect(mockOnChange).toHaveBeenCalledTimes(3);
      expect(mockOnChange).toHaveBeenNthCalledWith(1, true);
      expect(mockOnChange).toHaveBeenNthCalledWith(2, false);
      expect(mockOnChange).toHaveBeenNthCalledWith(3, true);
    });

    it('maintains focus ring styles', () => {
      const { container } = render(<Switch checked={false} onChange={mockOnChange} />);

      const switchElement = container.querySelector('.focus\\:ring-2.focus\\:ring-blue-500');
      expect(switchElement).toBeInTheDocument();
    });
  });
});
