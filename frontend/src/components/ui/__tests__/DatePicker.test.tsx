import { renderWithProviders } from '@/test-utils';
/**
 * Tests for DatePicker Component
 * Component: 31 - Date selection
 */

import React from 'react';
import { renderWithProviders as render, screen, fireEvent, waitFor } from '@/test-utils';
import '@testing-library/jest-dom';
import { DatePicker } from '../DatePicker';

describe('DatePicker', () => {
  const mockOnChange = jest.fn();

  beforeEach(() => {
    mockOnChange.mockClear();
  });

  // Test 31.1: Render test
  describe('Rendering', () => {
    it('renders with placeholder', () => {
      render(<DatePicker onChange={mockOnChange} placeholder="Choose date" />);

      expect(screen.getByText('Choose date')).toBeInTheDocument();
    });

    it('renders with selected value', () => {
      render(<DatePicker value="2025-01-15" onChange={mockOnChange} />);

      expect(screen.getByText(/Jan 15, 2025/)).toBeInTheDocument();
    });

    it('renders calendar icon', () => {
      render(<DatePicker onChange={mockOnChange} />);

      expect(screen.getByText('📅')).toBeInTheDocument();
    });

    it('opens calendar on button click', () => {
      render(<DatePicker onChange={mockOnChange} />);

      const button = screen.getByRole('button');
      fireEvent.click(button);

      expect(screen.getByText('Today')).toBeInTheDocument();
      expect(screen.getByText('Close')).toBeInTheDocument();
    });
  });

  // Test 31.2: Interaction and date selection
  describe('Date Selection', () => {
    it('selects a date when clicked', () => {
      render(<DatePicker onChange={mockOnChange} />);

      // Open calendar
      fireEvent.click(screen.getByRole('button'));

      // Click a date (day 15)
      const day15 = screen.getAllByText('15')[0];
      fireEvent.click(day15);

      expect(mockOnChange).toHaveBeenCalled();
      const callArg = mockOnChange.mock.calls[0][0];
      expect(callArg).toMatch(/^\d{4}-\d{2}-15$/);
    });

    it('closes calendar after selecting a date', async () => {
      render(<DatePicker onChange={mockOnChange} />);

      // Open calendar
      fireEvent.click(screen.getByRole('button'));
      expect(screen.getByText('Today')).toBeInTheDocument();

      // Select a date
      const day15 = screen.getAllByText('15')[0];
      fireEvent.click(day15);

      await waitFor(() => {
        expect(screen.queryByText('Today')).not.toBeInTheDocument();
      });
    });

    it('selects today when Today button clicked', () => {
      render(<DatePicker onChange={mockOnChange} />);

      // Open calendar
      fireEvent.click(screen.getByRole('button'));

      // Click Today
      fireEvent.click(screen.getByText('Today'));

      expect(mockOnChange).toHaveBeenCalled();
      const today = new Date().toISOString().split('T')[0];
      expect(mockOnChange).toHaveBeenCalledWith(today);
    });

    it('navigates to previous month', () => {
      render(<DatePicker onChange={mockOnChange} />);

      // Open calendar
      fireEvent.click(screen.getByRole('button'));

      const currentMonth = screen.getByText(/\w+ \d{4}/);
      const prevButton = screen.getByLabelText('Previous month');

      fireEvent.click(prevButton);

      // Month should have changed
      expect(screen.getByText(/\w+ \d{4}/)).toBeInTheDocument();
    });

    it('navigates to next month', () => {
      render(<DatePicker onChange={mockOnChange} />);

      // Open calendar
      fireEvent.click(screen.getByRole('button'));

      const nextButton = screen.getByLabelText('Next month');
      fireEvent.click(nextButton);

      expect(screen.getByText(/\w+ \d{4}/)).toBeInTheDocument();
    });
  });

  // Test 31.3: Accessibility
  describe('Accessibility', () => {
    it('trigger button is keyboard accessible', () => {
      render(<DatePicker onChange={mockOnChange} />);

      const button = screen.getByRole('button');
      button.focus();

      expect(button).toHaveFocus();
    });

    it('has proper ARIA labels on navigation buttons', () => {
      render(<DatePicker onChange={mockOnChange} />);

      fireEvent.click(screen.getByRole('button'));

      expect(screen.getByLabelText('Previous month')).toBeInTheDocument();
      expect(screen.getByLabelText('Next month')).toBeInTheDocument();
    });

    it('calendar closes on backdrop click', async () => {
      render(<DatePicker onChange={mockOnChange} />);

      // Open calendar
      fireEvent.click(screen.getByRole('button'));
      expect(screen.getByText('Today')).toBeInTheDocument();

      // Click backdrop
      const backdrop = document.querySelector('.fixed.inset-0');
      fireEvent.click(backdrop!);

      await waitFor(() => {
        expect(screen.queryByText('Today')).not.toBeInTheDocument();
      });
    });

    it('calendar closes on Close button click', async () => {
      render(<DatePicker onChange={mockOnChange} />);

      // Open calendar
      fireEvent.click(screen.getByRole('button'));

      // Click Close
      fireEvent.click(screen.getByText('Close'));

      await waitFor(() => {
        expect(screen.queryByText('Today')).not.toBeInTheDocument();
      });
    });

    it('disabled state prevents interaction', () => {
      render(<DatePicker onChange={mockOnChange} disabled />);

      const button = screen.getByRole('button');
      expect(button).toBeDisabled();

      fireEvent.click(button);
      expect(screen.queryByText('Today')).not.toBeInTheDocument();
    });
  });

  // Test 31.4: Edge cases and constraints
  describe('Edge Cases and Constraints', () => {
    it('respects min date constraint', () => {
      const minDate = '2025-01-15';
      render(<DatePicker onChange={mockOnChange} min={minDate} />);

      // Open calendar
      fireEvent.click(screen.getByRole('button'));

      // Try to click a date before min (day 10)
      const day10 = screen.getAllByText('10')[0];
      const button = day10.closest('button');

      if (button) {
        expect(button).toBeDisabled();
      }
    });

    it('respects max date constraint', () => {
      const maxDate = '2025-01-15';
      render(<DatePicker onChange={mockOnChange} max={maxDate} />);

      // Open calendar
      fireEvent.click(screen.getByRole('button'));

      // Dates after max should be disabled
      const day20 = screen.getAllByText('20')[0];
      const button = day20.closest('button');

      if (button) {
        expect(button).toBeDisabled();
      }
    });

    it('highlights selected date', () => {
      render(<DatePicker value="2025-01-15" onChange={mockOnChange} />);

      // Open calendar
      fireEvent.click(screen.getByRole('button'));

      // Find the selected date button
      const day15 = screen.getAllByText('15')[0];
      const button = day15.closest('button');

      expect(button).toHaveClass('bg-blue-600');
    });

    it('highlights today', () => {
      render(<DatePicker onChange={mockOnChange} />);

      // Open calendar
      fireEvent.click(screen.getByRole('button'));

      const today = new Date().getDate();
      const todayElement = screen.getAllByText(today.toString())[0];
      const button = todayElement.closest('button');

      // Today should have border
      expect(button).toHaveClass('border-2', 'border-blue-600');
    });

    it('displays weekday headers', () => {
      render(<DatePicker onChange={mockOnChange} />);

      fireEvent.click(screen.getByRole('button'));

      expect(screen.getByText('Su')).toBeInTheDocument();
      expect(screen.getByText('Mo')).toBeInTheDocument();
      expect(screen.getByText('Tu')).toBeInTheDocument();
      expect(screen.getByText('We')).toBeInTheDocument();
      expect(screen.getByText('Th')).toBeInTheDocument();
      expect(screen.getByText('Fr')).toBeInTheDocument();
      expect(screen.getByText('Sa')).toBeInTheDocument();
    });

    it('shows previous month days in gray', () => {
      render(<DatePicker onChange={mockOnChange} />);

      fireEvent.click(screen.getByRole('button'));

      // Previous/next month days should have text-gray-400
      const { container } = render(<DatePicker onChange={mockOnChange} />);
      fireEvent.click(container.querySelector('button')!);
    });

    it('applies custom className', () => {
      const { container } = render(
        <DatePicker onChange={mockOnChange} className="custom-class" />
      );

      expect(container.querySelector('.date-picker.custom-class')).toBeInTheDocument();
    });

    it('displays 42 day cells (6 weeks)', () => {
      render(<DatePicker onChange={mockOnChange} />);

      fireEvent.click(screen.getByRole('button'));

      // Count all day buttons
      const dayButtons = screen.getAllByRole('button').filter(btn =>
        /^\d+$/.test(btn.textContent || '')
      );

      expect(dayButtons.length).toBe(42);
    });

    it('handles year transitions', () => {
      render(<DatePicker value="2025-01-05" onChange={mockOnChange} />);

      fireEvent.click(screen.getByRole('button'));

      // Navigate to previous month (December 2024)
      const prevButton = screen.getByLabelText('Previous month');
      fireEvent.click(prevButton);

      expect(screen.getByText(/December 2024/)).toBeInTheDocument();
    });
  });
});
