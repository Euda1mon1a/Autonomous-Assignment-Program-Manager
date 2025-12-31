import React from 'react';
import { render, screen } from '@testing-library/react';
import { ScheduleCell, ScheduleSeparatorRow } from '../ScheduleCell';

describe('ScheduleCell', () => {
  const defaultProps = {
    isWeekend: false,
    isToday: false,
    timeOfDay: 'AM' as const,
  };

  describe('rendering', () => {
    it('renders empty cell when no assignment provided', () => {
      const { container } = render(
        <table>
          <tbody>
            <tr>
              <ScheduleCell {...defaultProps} />
            </tr>
          </tbody>
        </table>
      );

      expect(screen.getByText('-')).toBeInTheDocument();
      expect(container.querySelector('td')).toHaveClass('min-w-[50px]');
    });

    it('renders assignment with abbreviation', () => {
      const assignment = {
        abbreviation: 'IM',
        activityType: 'inpatient',
      };

      render(
        <table>
          <tbody>
            <tr>
              <ScheduleCell {...defaultProps} assignment={assignment} />
            </tr>
          </tbody>
        </table>
      );

      expect(screen.getByText('IM')).toBeInTheDocument();
    });

    it('applies weekend styling when isWeekend is true', () => {
      const { container } = render(
        <table>
          <tbody>
            <tr>
              <ScheduleCell {...defaultProps} isWeekend={true} />
            </tr>
          </tbody>
        </table>
      );

      expect(container.querySelector('td')).toHaveClass('bg-gray-50/50');
    });

    it('applies today styling when isToday is true', () => {
      const { container } = render(
        <table>
          <tbody>
            <tr>
              <ScheduleCell {...defaultProps} isToday={true} />
            </tr>
          </tbody>
        </table>
      );

      expect(container.querySelector('td')).toHaveClass('bg-blue-50/30');
    });

    it('applies PM border for PM cells', () => {
      const { container } = render(
        <table>
          <tbody>
            <tr>
              <ScheduleCell {...defaultProps} timeOfDay="PM" />
            </tr>
          </tbody>
        </table>
      );

      expect(container.querySelector('td')).toHaveClass('border-r-2 border-r-gray-300');
    });
  });

  describe('activity type colors', () => {
    it('applies clinic colors', () => {
      const assignment = {
        abbreviation: 'CLNC',
        activityType: 'clinic',
      };

      render(
        <table>
          <tbody>
            <tr>
              <ScheduleCell {...defaultProps} assignment={assignment} />
            </tr>
          </tbody>
        </table>
      );

      const badge = screen.getByText('CLNC').parentElement;
      expect(badge).toHaveClass('bg-blue-100', 'text-blue-800', 'border-blue-300');
    });

    it('applies inpatient colors', () => {
      const assignment = {
        abbreviation: 'INP',
        activityType: 'inpatient',
      };

      render(
        <table>
          <tbody>
            <tr>
              <ScheduleCell {...defaultProps} assignment={assignment} />
            </tr>
          </tbody>
        </table>
      );

      const badge = screen.getByText('INP').parentElement;
      expect(badge).toHaveClass('bg-purple-100', 'text-purple-800', 'border-purple-300');
    });

    it('applies default colors for unknown activity type', () => {
      const assignment = {
        abbreviation: 'UNK',
        activityType: 'unknown',
      };

      render(
        <table>
          <tbody>
            <tr>
              <ScheduleCell {...defaultProps} assignment={assignment} />
            </tr>
          </tbody>
        </table>
      );

      const badge = screen.getByText('UNK').parentElement;
      expect(badge).toHaveClass('bg-slate-100', 'text-slate-700', 'border-slate-300');
    });
  });

  describe('custom colors', () => {
    it('applies custom colors from database', () => {
      const assignment = {
        abbreviation: 'CUSTOM',
        activityType: 'clinic',
        fontColor: 'black',
        backgroundColor: 'white',
      };

      const { container } = render(
        <table>
          <tbody>
            <tr>
              <ScheduleCell {...defaultProps} assignment={assignment} />
            </tr>
          </tbody>
        </table>
      );

      const badge = screen.getByText('CUSTOM').parentElement;
      expect(badge).toHaveStyle({
        color: '#000000',
        backgroundColor: '#ffffff',
      });
    });

    it('falls back to activity colors when custom colors not provided', () => {
      const assignment = {
        abbreviation: 'TEST',
        activityType: 'call',
      };

      render(
        <table>
          <tbody>
            <tr>
              <ScheduleCell {...defaultProps} assignment={assignment} />
            </tr>
          </tbody>
        </table>
      );

      const badge = screen.getByText('TEST').parentElement;
      expect(badge).toHaveClass('bg-orange-100', 'text-orange-800', 'border-orange-300');
    });
  });

  describe('tooltip', () => {
    it('displays template name in tooltip', () => {
      const assignment = {
        abbreviation: 'IM',
        activityType: 'inpatient',
        templateName: 'Inpatient Medicine',
      };

      render(
        <table>
          <tbody>
            <tr>
              <ScheduleCell {...defaultProps} assignment={assignment} />
            </tr>
          </tbody>
        </table>
      );

      const badge = screen.getByText('IM').parentElement;
      expect(badge).toHaveAttribute('title', expect.stringContaining('Inpatient Medicine'));
    });

    it('includes role in tooltip when not primary', () => {
      const assignment = {
        abbreviation: 'IM',
        activityType: 'inpatient',
        role: 'supervisor',
      };

      render(
        <table>
          <tbody>
            <tr>
              <ScheduleCell {...defaultProps} assignment={assignment} />
            </tr>
          </tbody>
        </table>
      );

      const badge = screen.getByText('IM').parentElement;
      expect(badge).toHaveAttribute('title', expect.stringContaining('Role: supervisor'));
    });

    it('includes notes in tooltip', () => {
      const assignment = {
        abbreviation: 'IM',
        activityType: 'inpatient',
        notes: 'Special assignment',
      };

      render(
        <table>
          <tbody>
            <tr>
              <ScheduleCell {...defaultProps} assignment={assignment} />
            </tr>
          </tbody>
        </table>
      );

      const badge = screen.getByText('IM').parentElement;
      expect(badge).toHaveAttribute('title', expect.stringContaining('Note: Special assignment'));
    });
  });

  describe('accessibility', () => {
    it('has hover effects for better interactivity', () => {
      const assignment = {
        abbreviation: 'IM',
        activityType: 'inpatient',
      };

      render(
        <table>
          <tbody>
            <tr>
              <ScheduleCell {...defaultProps} assignment={assignment} />
            </tr>
          </tbody>
        </table>
      );

      const badge = screen.getByText('IM').parentElement;
      expect(badge).toHaveClass('hover:scale-105', 'hover:shadow-sm');
    });
  });
});

describe('ScheduleSeparatorRow', () => {
  it('renders separator with label', () => {
    render(
      <table>
        <tbody>
          <ScheduleSeparatorRow label="PGY-1" columnCount={7} />
        </tbody>
      </table>
    );

    expect(screen.getByText('PGY-1')).toBeInTheDocument();
  });

  it('renders empty separator without label', () => {
    const { container } = render(
      <table>
        <tbody>
          <ScheduleSeparatorRow columnCount={7} />
        </tbody>
      </table>
    );

    const cell = container.querySelector('td');
    expect(cell).toBeInTheDocument();
    expect(cell).toHaveClass('bg-gray-100/50');
  });

  it('applies correct column span', () => {
    const { container } = render(
      <table>
        <tbody>
          <ScheduleSeparatorRow label="Faculty" columnCount={7} />
        </tbody>
      </table>
    );

    const cell = container.querySelector('td');
    expect(cell).toHaveAttribute('colSpan', '15'); // 1 + (7 * 2) = 15
  });

  it('has proper styling classes', () => {
    const { container } = render(
      <table>
        <tbody>
          <ScheduleSeparatorRow label="PGY-2" columnCount={5} />
        </tbody>
      </table>
    );

    const row = container.querySelector('tr');
    expect(row).toHaveClass('bg-gray-100/50', 'border-y', 'border-gray-300');

    const cell = container.querySelector('td');
    expect(cell).toHaveClass('py-1', 'px-4', 'text-xs', 'font-medium', 'text-gray-500');
  });
});
