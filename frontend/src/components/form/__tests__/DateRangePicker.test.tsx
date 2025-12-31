/**
 * Tests for DateRangePicker Component
 * Component: form/DateRangePicker - Date range selection
 */

import React from 'react';
import { render, screen, fireEvent } from '@/test-utils';
import '@testing-library/jest-dom';
import { DateRangePicker } from '../DateRangePicker';

describe('DateRangePicker', () => {
  const mockOnChange = jest.fn();

  beforeEach(() => {
    mockOnChange.mockClear();
  });

  describe('Rendering', () => {
    it('renders start date input', () => {
      render(<DateRangePicker startDate="" endDate="" onChange={mockOnChange} />);
      expect(screen.getByLabelText(/start date/i)).toBeInTheDocument();
    });

    it('renders end date input', () => {
      render(<DateRangePicker startDate="" endDate="" onChange={mockOnChange} />);
      expect(screen.getByLabelText(/end date/i)).toBeInTheDocument();
    });

    it('displays selected start date', () => {
      render(<DateRangePicker startDate="2024-01-01" endDate="" onChange={mockOnChange} />);
      const startInput = screen.getByLabelText(/start date/i) as HTMLInputElement;
      expect(startInput.value).toBe('2024-01-01');
    });

    it('displays selected end date', () => {
      render(<DateRangePicker startDate="" endDate="2024-01-31" onChange={mockOnChange} />);
      const endInput = screen.getByLabelText(/end date/i) as HTMLInputElement;
      expect(endInput.value).toBe('2024-01-31');
    });
  });

  describe('Interaction', () => {
    it('calls onChange when start date changes', () => {
      render(<DateRangePicker startDate="" endDate="" onChange={mockOnChange} />);

      const startInput = screen.getByLabelText(/start date/i);
      fireEvent.change(startInput, { target: { value: '2024-01-01' } });

      expect(mockOnChange).toHaveBeenCalledWith({
        startDate: '2024-01-01',
        endDate: '',
      });
    });

    it('calls onChange when end date changes', () => {
      render(<DateRangePicker startDate="2024-01-01" endDate="" onChange={mockOnChange} />);

      const endInput = screen.getByLabelText(/end date/i);
      fireEvent.change(endInput, { target: { value: '2024-01-31' } });

      expect(mockOnChange).toHaveBeenCalledWith({
        startDate: '2024-01-01',
        endDate: '2024-01-31',
      });
    });

    it('clears start date', () => {
      render(<DateRangePicker startDate="2024-01-01" endDate="" onChange={mockOnChange} />);

      const startInput = screen.getByLabelText(/start date/i);
      fireEvent.change(startInput, { target: { value: '' } });

      expect(mockOnChange).toHaveBeenCalledWith({
        startDate: '',
        endDate: '',
      });
    });

    it('clears end date', () => {
      render(<DateRangePicker startDate="2024-01-01" endDate="2024-01-31" onChange={mockOnChange} />);

      const endInput = screen.getByLabelText(/end date/i);
      fireEvent.change(endInput, { target: { value: '' } });

      expect(mockOnChange).toHaveBeenCalledWith({
        startDate: '2024-01-01',
        endDate: '',
      });
    });
  });

  describe('Validation', () => {
    it('shows error when end date is before start date', () => {
      render(
        <DateRangePicker
          startDate="2024-01-31"
          endDate="2024-01-01"
          onChange={mockOnChange}
          error="End date must be after start date"
        />
      );
      expect(screen.getByText(/end date must be after start date/i)).toBeInTheDocument();
    });

    it('validates date range on change', () => {
      const { rerender } = render(<DateRangePicker startDate="2024-01-01" endDate="" onChange={mockOnChange} />);

      const endInput = screen.getByLabelText(/end date/i);
      fireEvent.change(endInput, { target: { value: '2023-12-31' } });

      // Validation should occur
      rerender(
        <DateRangePicker
          startDate="2024-01-01"
          endDate="2023-12-31"
          onChange={mockOnChange}
          error="End date must be after start date"
        />
      );

      expect(screen.getByText(/end date must be after start date/i)).toBeInTheDocument();
    });
  });

  describe('Disabled State', () => {
    it('disables both inputs when disabled', () => {
      render(<DateRangePicker startDate="" endDate="" onChange={mockOnChange} disabled={true} />);

      const startInput = screen.getByLabelText(/start date/i);
      const endInput = screen.getByLabelText(/end date/i);

      expect(startInput).toBeDisabled();
      expect(endInput).toBeDisabled();
    });

    it('does not call onChange when disabled', () => {
      render(<DateRangePicker startDate="" endDate="" onChange={mockOnChange} disabled={true} />);

      const startInput = screen.getByLabelText(/start date/i);
      fireEvent.change(startInput, { target: { value: '2024-01-01' } });

      expect(mockOnChange).not.toHaveBeenCalled();
    });
  });

  describe('Accessibility', () => {
    it('has proper labels', () => {
      render(<DateRangePicker startDate="" endDate="" onChange={mockOnChange} />);
      expect(screen.getByLabelText(/start date/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/end date/i)).toBeInTheDocument();
    });

    it('associates error with inputs', () => {
      render(
        <DateRangePicker
          startDate="2024-01-31"
          endDate="2024-01-01"
          onChange={mockOnChange}
          error="Invalid range"
        />
      );

      const endInput = screen.getByLabelText(/end date/i);
      expect(endInput).toHaveAccessibleDescription();
    });
  });

  describe('Edge Cases', () => {
    it('handles same start and end date', () => {
      render(<DateRangePicker startDate="2024-01-15" endDate="2024-01-15" onChange={mockOnChange} />);

      const startInput = screen.getByLabelText(/start date/i) as HTMLInputElement;
      const endInput = screen.getByLabelText(/end date/i) as HTMLInputElement;

      expect(startInput.value).toBe('2024-01-15');
      expect(endInput.value).toBe('2024-01-15');
    });

    it('handles very far future dates', () => {
      render(<DateRangePicker startDate="2024-01-01" endDate="2099-12-31" onChange={mockOnChange} />);

      const endInput = screen.getByLabelText(/end date/i) as HTMLInputElement;
      expect(endInput.value).toBe('2099-12-31');
    });

    it('handles leap year dates', () => {
      render(<DateRangePicker startDate="2024-02-29" endDate="2024-03-01" onChange={mockOnChange} />);

      const startInput = screen.getByLabelText(/start date/i) as HTMLInputElement;
      expect(startInput.value).toBe('2024-02-29');
    });
  });

  describe('Custom Labels', () => {
    it('renders custom start label', () => {
      render(
        <DateRangePicker startDate="" endDate="" onChange={mockOnChange} startLabel="From" endLabel="To" />
      );
      expect(screen.getByLabelText(/from/i)).toBeInTheDocument();
    });

    it('renders custom end label', () => {
      render(
        <DateRangePicker startDate="" endDate="" onChange={mockOnChange} startLabel="From" endLabel="To" />
      );
      expect(screen.getByLabelText(/to/i)).toBeInTheDocument();
    });
  });
});
