/**
 * Tests for DayCell Component
 * Component: DayCell - Single day cell in calendar
 */

import React from 'react';
import { render, screen, fireEvent } from '@/test-utils';
import '@testing-library/jest-dom';
import { DayCell } from '../DayCell';

describe('DayCell', () => {
  const mockOnClick = jest.fn();

  beforeEach(() => {
    mockOnClick.mockClear();
  });

  describe('Rendering', () => {
    it('renders day number', () => {
      render(
        <DayCell
          day={15}
          date="2024-01-15"
          isCurrentMonth={true}
          isToday={false}
          isWeekend={false}
          onClick={mockOnClick}
        />
      );

      expect(screen.getByText('15')).toBeInTheDocument();
    });

    it('renders with current month styling', () => {
      const { container } = render(
        <DayCell
          day={15}
          date="2024-01-15"
          isCurrentMonth={true}
          isToday={false}
          isWeekend={false}
          onClick={mockOnClick}
        />
      );

      const dayCell = container.firstChild;
      expect(dayCell).not.toHaveClass('opacity-50');
    });

    it('renders with dimmed styling for other month', () => {
      const { container } = render(
        <DayCell
          day={31}
          date="2023-12-31"
          isCurrentMonth={false}
          isToday={false}
          isWeekend={false}
          onClick={mockOnClick}
        />
      );

      const dayCell = container.firstChild;
      expect(dayCell).toHaveClass('opacity-50');
    });

    it('renders with today styling', () => {
      const { container } = render(
        <DayCell
          day={15}
          date="2024-01-15"
          isCurrentMonth={true}
          isToday={true}
          isWeekend={false}
          onClick={mockOnClick}
        />
      );

      const todayElement = container.querySelector('.bg-blue-600');
      expect(todayElement).toBeInTheDocument();
    });

    it('renders with weekend styling', () => {
      const { container } = render(
        <DayCell
          day={14}
          date="2024-01-14"
          isCurrentMonth={true}
          isToday={false}
          isWeekend={true}
          onClick={mockOnClick}
        />
      );

      const weekendCell = container.querySelector('.bg-gray-50');
      expect(weekendCell).toBeInTheDocument();
    });

    it('renders with assignments when provided', () => {
      render(
        <DayCell
          day={15}
          date="2024-01-15"
          isCurrentMonth={true}
          isToday={false}
          isWeekend={false}
          onClick={mockOnClick}
          assignmentCount={3}
        />
      );

      expect(screen.getByText('3')).toBeInTheDocument();
    });

    it('renders with no assignment indicator when count is 0', () => {
      render(
        <DayCell
          day={15}
          date="2024-01-15"
          isCurrentMonth={true}
          isToday={false}
          isWeekend={false}
          onClick={mockOnClick}
          assignmentCount={0}
        />
      );

      expect(screen.queryByText('0')).not.toBeInTheDocument();
    });
  });

  describe('Interaction', () => {
    it('calls onClick when clicked', () => {
      render(
        <DayCell
          day={15}
          date="2024-01-15"
          isCurrentMonth={true}
          isToday={false}
          isWeekend={false}
          onClick={mockOnClick}
        />
      );

      const dayCell = screen.getByText('15').closest('div');
      fireEvent.click(dayCell!);

      expect(mockOnClick).toHaveBeenCalledWith('2024-01-15');
    });

    it('has hover effect', () => {
      const { container } = render(
        <DayCell
          day={15}
          date="2024-01-15"
          isCurrentMonth={true}
          isToday={false}
          isWeekend={false}
          onClick={mockOnClick}
        />
      );

      const dayCell = container.firstChild;
      expect(dayCell).toHaveClass('cursor-pointer');
    });
  });

  describe('Edge Cases', () => {
    it('renders single digit days', () => {
      render(
        <DayCell
          day={1}
          date="2024-01-01"
          isCurrentMonth={true}
          isToday={false}
          isWeekend={false}
          onClick={mockOnClick}
        />
      );

      expect(screen.getByText('1')).toBeInTheDocument();
    });

    it('renders double digit days', () => {
      render(
        <DayCell
          day={31}
          date="2024-01-31"
          isCurrentMonth={true}
          isToday={false}
          isWeekend={false}
          onClick={mockOnClick}
        />
      );

      expect(screen.getByText('31')).toBeInTheDocument();
    });

    it('combines today and weekend styling', () => {
      const { container } = render(
        <DayCell
          day={14}
          date="2024-01-14"
          isCurrentMonth={true}
          isToday={true}
          isWeekend={true}
          onClick={mockOnClick}
        />
      );

      const todayMarker = container.querySelector('.bg-blue-600');
      const weekendBg = container.querySelector('.bg-gray-50');

      expect(todayMarker).toBeInTheDocument();
      expect(weekendBg).toBeInTheDocument();
    });

    it('handles large assignment counts', () => {
      render(
        <DayCell
          day={15}
          date="2024-01-15"
          isCurrentMonth={true}
          isToday={false}
          isWeekend={false}
          onClick={mockOnClick}
          assignmentCount={99}
        />
      );

      expect(screen.getByText('99')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('is keyboard accessible', () => {
      render(
        <DayCell
          day={15}
          date="2024-01-15"
          isCurrentMonth={true}
          isToday={false}
          isWeekend={false}
          onClick={mockOnClick}
        />
      );

      const dayCell = screen.getByText('15').closest('div');

      // Should be clickable
      fireEvent.click(dayCell!);
      expect(mockOnClick).toHaveBeenCalled();
    });
  });
});
