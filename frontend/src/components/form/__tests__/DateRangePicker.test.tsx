/**
 * Tests for DateRangePicker Component
 * Component: form/DateRangePicker - Date range selection
 */

import React from 'react';
import { render, screen, fireEvent } from '@/test-utils';
import '@testing-library/jest-dom';
import { DateRangePicker, DateRange } from '../DateRangePicker';

describe('DateRangePicker', () => {
  const mockOnChange = jest.fn();
  const emptyRange: DateRange = { start: null, end: null };

  beforeEach(() => {
    mockOnChange.mockClear();
  });

  describe('Rendering', () => {
    it('renders start date input', () => {
      render(<DateRangePicker value={emptyRange} onChange={mockOnChange} />);
      const inputs = screen.getAllByRole('textbox');
      expect(inputs.length).toBeGreaterThan(0);
    });

    it('renders end date input', () => {
      render(<DateRangePicker value={emptyRange} onChange={mockOnChange} />);
      // DateRangePicker should have two date inputs
      const dateInputs = screen.getAllByRole('textbox');
      expect(dateInputs.length).toBe(2);
    });

    it('displays selected start date', () => {
      const valueWithStart: DateRange = { start: new Date('2024-01-01'), end: null };
      render(<DateRangePicker value={valueWithStart} onChange={mockOnChange} />);
      const startInput = screen.getAllByRole('textbox')[0] as HTMLInputElement;
      expect(startInput.value).toBe('2024-01-01');
    });

    it('displays selected end date', () => {
      const valueWithEnd: DateRange = { start: null, end: new Date('2024-01-31') };
      render(<DateRangePicker value={valueWithEnd} onChange={mockOnChange} />);
      const endInput = screen.getAllByRole('textbox')[1] as HTMLInputElement;
      expect(endInput.value).toBe('2024-01-31');
    });
  });

  describe('Interaction', () => {
    it('calls onChange when start date changes', () => {
      render(<DateRangePicker value={emptyRange} onChange={mockOnChange} />);

      const startInput = screen.getAllByRole('textbox')[0];
      fireEvent.change(startInput, { target: { value: '2024-01-01' } });

      expect(mockOnChange).toHaveBeenCalled();
    });

    it('calls onChange when end date changes', () => {
      const valueWithStart: DateRange = { start: new Date('2024-01-01'), end: null };
      render(<DateRangePicker value={valueWithStart} onChange={mockOnChange} />);

      const endInput = screen.getAllByRole('textbox')[1];
      fireEvent.change(endInput, { target: { value: '2024-01-31' } });

      expect(mockOnChange).toHaveBeenCalled();
    });

    it('clears start date', () => {
      const valueWithStart: DateRange = { start: new Date('2024-01-01'), end: null };
      render(<DateRangePicker value={valueWithStart} onChange={mockOnChange} />);

      const startInput = screen.getAllByRole('textbox')[0];
      fireEvent.change(startInput, { target: { value: '' } });

      expect(mockOnChange).toHaveBeenCalledWith(expect.objectContaining({ start: null }));
    });

    it('clears end date', () => {
      const fullRange: DateRange = { start: new Date('2024-01-01'), end: new Date('2024-01-31') };
      render(<DateRangePicker value={fullRange} onChange={mockOnChange} />);

      const endInput = screen.getAllByRole('textbox')[1];
      fireEvent.change(endInput, { target: { value: '' } });

      expect(mockOnChange).toHaveBeenCalledWith(expect.objectContaining({ end: null }));
    });
  });

  describe('Edge Cases', () => {
    it('handles same start and end date', () => {
      const sameDate: DateRange = { start: new Date('2024-01-15'), end: new Date('2024-01-15') };
      render(<DateRangePicker value={sameDate} onChange={mockOnChange} />);

      const startInput = screen.getAllByRole('textbox')[0] as HTMLInputElement;
      const endInput = screen.getAllByRole('textbox')[1] as HTMLInputElement;

      expect(startInput.value).toBe('2024-01-15');
      expect(endInput.value).toBe('2024-01-15');
    });

    it('handles very far future dates', () => {
      const futureRange: DateRange = { start: new Date('2024-01-01'), end: new Date('2099-12-31') };
      render(<DateRangePicker value={futureRange} onChange={mockOnChange} />);

      const endInput = screen.getAllByRole('textbox')[1] as HTMLInputElement;
      expect(endInput.value).toBe('2099-12-31');
    });

    it('handles leap year dates', () => {
      const leapRange: DateRange = { start: new Date('2024-02-29'), end: new Date('2024-03-01') };
      render(<DateRangePicker value={leapRange} onChange={mockOnChange} />);

      const startInput = screen.getAllByRole('textbox')[0] as HTMLInputElement;
      expect(startInput.value).toBe('2024-02-29');
    });
  });

  describe('Label', () => {
    it('renders custom label when provided', () => {
      render(<DateRangePicker value={emptyRange} onChange={mockOnChange} label="Select Date Range" />);
      expect(screen.getByText('Select Date Range')).toBeInTheDocument();
    });
  });
});
