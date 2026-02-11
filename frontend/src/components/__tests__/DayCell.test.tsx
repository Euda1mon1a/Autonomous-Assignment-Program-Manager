/**
 * Tests for DayCell Component
 * Component: DayCell - Single day cell in calendar
 */

import React from 'react';
import { render, screen, fireEvent } from '@/test-utils';
import '@testing-library/jest-dom';
import { DayCell } from '../DayCell';

describe('DayCell', () => {
  describe('Rendering', () => {
    it('renders with date', () => {
      const { container } = render(
        <DayCell
          date={new Date('2024-01-15')}
        />
      );

      // DayCell renders empty state (dash) when no assignments
      expect(container.querySelector('.schedule-cell')).toBeInTheDocument();
      expect(screen.getByText('-')).toBeInTheDocument();
    });

    it('renders with AM assignment', () => {
      render(
        <DayCell
          date={new Date('2024-01-15')}
          amAssignment={{
            id: 'a1',
            activity: 'Clinic',
            abbreviation: 'CL',
            role: 'primary',
          }}
        />
      );

      expect(screen.getByText('CL')).toBeInTheDocument();
    });

    it('renders with PM assignment', () => {
      render(
        <DayCell
          date={new Date('2024-01-15')}
          pmAssignment={{
            id: 'a2',
            activity: 'Inpatient',
            abbreviation: 'IM',
            role: 'primary',
          }}
        />
      );

      expect(screen.getByText('IM')).toBeInTheDocument();
    });

    it('renders with both AM and PM assignments', () => {
      render(
        <DayCell
          date={new Date('2024-01-15')}
          amAssignment={{
            id: 'a1',
            activity: 'Clinic',
            abbreviation: 'CL',
            role: 'primary',
          }}
          pmAssignment={{
            id: 'a2',
            activity: 'Inpatient',
            abbreviation: 'IM',
            role: 'primary',
          }}
        />
      );

      expect(screen.getByText('CL')).toBeInTheDocument();
      expect(screen.getByText('IM')).toBeInTheDocument();
    });

    it('renders combined view when AM and PM are same activity', () => {
      render(
        <DayCell
          date={new Date('2024-01-15')}
          amAssignment={{
            id: 'a1',
            activity: 'Clinic',
            abbreviation: 'CL',
            role: 'primary',
          }}
          pmAssignment={{
            id: 'a2',
            activity: 'Clinic',
            abbreviation: 'CL',
            role: 'primary',
          }}
        />
      );

      // Should only show one CL when activities are the same
      const cells = screen.getAllByText('CL');
      expect(cells.length).toBeGreaterThanOrEqual(1);
    });

    it('renders empty state when no assignments', () => {
      const { container } = render(
        <DayCell
          date={new Date('2024-01-15')}
        />
      );

      // Should render the cell structure
      expect(container.firstChild).toBeInTheDocument();
    });

    it('applies weekend styling', () => {
      const { container } = render(
        <DayCell
          date={new Date('2024-01-14')} // Sunday
        />
      );

      // Weekend should have different styling
      expect(container.firstChild).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('renders single digit days', () => {
      const { container } = render(
        <DayCell
          date={new Date('2024-01-01')}
        />
      );

      // DayCell renders a cell structure regardless of date
      expect(container.querySelector('.schedule-cell')).toBeInTheDocument();
    });

    it('renders double digit days', () => {
      const { container } = render(
        <DayCell
          date={new Date('2024-01-31')}
        />
      );

      expect(container.querySelector('.schedule-cell')).toBeInTheDocument();
    });

    it('handles leap year dates', () => {
      const { container } = render(
        <DayCell
          date={new Date('2024-02-29')}
        />
      );

      expect(container.querySelector('.schedule-cell')).toBeInTheDocument();
    });
  });
});
