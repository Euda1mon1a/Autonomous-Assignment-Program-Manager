import { render, screen } from '@testing-library/react'
import { ScheduleCell, ScheduleSeparatorRow } from '@/components/schedule/ScheduleCell'

describe('ScheduleCell', () => {
  describe('Empty Cell State', () => {
    it('should render empty cell with dash when no assignment', () => {
      render(
        <table>
          <tbody>
            <tr>
              <ScheduleCell
                assignment={undefined}
                isWeekend={false}
                isToday={false}
                timeOfDay="AM"
              />
            </tr>
          </tbody>
        </table>
      )

      expect(screen.getByText('-')).toBeInTheDocument()
    })

    it('should apply base cell styling to empty cells', () => {
      const { container } = render(
        <table>
          <tbody>
            <tr>
              <ScheduleCell
                assignment={undefined}
                isWeekend={false}
                isToday={false}
                timeOfDay="AM"
              />
            </tr>
          </tbody>
        </table>
      )

      const cell = container.querySelector('td')
      expect(cell).toHaveClass('border-r')
      expect(cell).toHaveClass('border-gray-200')
    })
  })

  describe('Assignment Display', () => {
    it('should render assignment abbreviation', () => {
      const assignment = {
        abbreviation: 'IM',
        activityType: 'inpatient',
        templateName: 'Inpatient Medicine',
      }

      render(
        <table>
          <tbody>
            <tr>
              <ScheduleCell
                assignment={assignment}
                isWeekend={false}
                isToday={false}
                timeOfDay="AM"
              />
            </tr>
          </tbody>
        </table>
      )

      expect(screen.getByText('IM')).toBeInTheDocument()
    })

    it('should not render dash when assignment is present', () => {
      const assignment = {
        abbreviation: 'CL',
        activityType: 'clinic',
      }

      render(
        <table>
          <tbody>
            <tr>
              <ScheduleCell
                assignment={assignment}
                isWeekend={false}
                isToday={false}
                timeOfDay="AM"
              />
            </tr>
          </tbody>
        </table>
      )

      expect(screen.queryByText('-')).not.toBeInTheDocument()
    })

    it('should render assignment with all properties', () => {
      const assignment = {
        abbreviation: 'PR',
        activityType: 'procedure',
        templateName: 'Procedure Room',
        role: 'backup',
        notes: 'Emergency only',
      }

      render(
        <table>
          <tbody>
            <tr>
              <ScheduleCell
                assignment={assignment}
                isWeekend={false}
                isToday={false}
                timeOfDay="AM"
              />
            </tr>
          </tbody>
        </table>
      )

      expect(screen.getByText('PR')).toBeInTheDocument()
    })
  })

  describe('Color Coding', () => {
    it('should apply blue color for clinic activities', () => {
      const assignment = {
        abbreviation: 'CL',
        activityType: 'clinic',
      }

      const { container } = render(
        <table>
          <tbody>
            <tr>
              <ScheduleCell
                assignment={assignment}
                isWeekend={false}
                isToday={false}
                timeOfDay="AM"
              />
            </tr>
          </tbody>
        </table>
      )

      const badge = container.querySelector('.bg-blue-100')
      expect(badge).toBeInTheDocument()
      expect(badge).toHaveClass('text-blue-800')
    })

    it('should apply purple color for inpatient activities', () => {
      const assignment = {
        abbreviation: 'IM',
        activityType: 'inpatient',
      }

      const { container } = render(
        <table>
          <tbody>
            <tr>
              <ScheduleCell
                assignment={assignment}
                isWeekend={false}
                isToday={false}
                timeOfDay="AM"
              />
            </tr>
          </tbody>
        </table>
      )

      const badge = container.querySelector('.bg-purple-100')
      expect(badge).toBeInTheDocument()
      expect(badge).toHaveClass('text-purple-800')
    })

    it('should apply red color for procedure activities', () => {
      const assignment = {
        abbreviation: 'PR',
        activityType: 'procedure',
      }

      const { container } = render(
        <table>
          <tbody>
            <tr>
              <ScheduleCell
                assignment={assignment}
                isWeekend={false}
                isToday={false}
                timeOfDay="AM"
              />
            </tr>
          </tbody>
        </table>
      )

      const badge = container.querySelector('.bg-red-100')
      expect(badge).toBeInTheDocument()
      expect(badge).toHaveClass('text-red-800')
    })

    it('should apply green color for elective activities', () => {
      const assignment = {
        abbreviation: 'EL',
        activityType: 'elective',
      }

      const { container } = render(
        <table>
          <tbody>
            <tr>
              <ScheduleCell
                assignment={assignment}
                isWeekend={false}
                isToday={false}
                timeOfDay="AM"
              />
            </tr>
          </tbody>
        </table>
      )

      const badge = container.querySelector('.bg-green-100')
      expect(badge).toBeInTheDocument()
      expect(badge).toHaveClass('text-green-800')
    })

    it('should apply orange color for call activities', () => {
      const assignment = {
        abbreviation: 'CA',
        activityType: 'call',
      }

      const { container } = render(
        <table>
          <tbody>
            <tr>
              <ScheduleCell
                assignment={assignment}
                isWeekend={false}
                isToday={false}
                timeOfDay="AM"
              />
            </tr>
          </tbody>
        </table>
      )

      const badge = container.querySelector('.bg-orange-100')
      expect(badge).toBeInTheDocument()
      expect(badge).toHaveClass('text-orange-800')
    })

    it('should apply gray color for conference activities', () => {
      const assignment = {
        abbreviation: 'CO',
        activityType: 'conference',
      }

      const { container } = render(
        <table>
          <tbody>
            <tr>
              <ScheduleCell
                assignment={assignment}
                isWeekend={false}
                isToday={false}
                timeOfDay="AM"
              />
            </tr>
          </tbody>
        </table>
      )

      const badge = container.querySelector('.bg-gray-100')
      expect(badge).toBeInTheDocument()
      expect(badge).toHaveClass('text-gray-800')
    })

    it('should apply amber color for vacation activities', () => {
      const assignment = {
        abbreviation: 'VA',
        activityType: 'vacation',
      }

      const { container } = render(
        <table>
          <tbody>
            <tr>
              <ScheduleCell
                assignment={assignment}
                isWeekend={false}
                isToday={false}
                timeOfDay="AM"
              />
            </tr>
          </tbody>
        </table>
      )

      const badge = container.querySelector('.bg-amber-100')
      expect(badge).toBeInTheDocument()
      expect(badge).toHaveClass('text-amber-800')
    })

    it('should apply default color for unknown activity types', () => {
      const assignment = {
        abbreviation: 'XX',
        activityType: 'unknown-type',
      }

      const { container } = render(
        <table>
          <tbody>
            <tr>
              <ScheduleCell
                assignment={assignment}
                isWeekend={false}
                isToday={false}
                timeOfDay="AM"
              />
            </tr>
          </tbody>
        </table>
      )

      const badge = container.querySelector('.bg-slate-100')
      expect(badge).toBeInTheDocument()
      expect(badge).toHaveClass('text-slate-700')
    })

    it('should handle case-insensitive activity types', () => {
      const assignment = {
        abbreviation: 'CL',
        activityType: 'CLINIC',
      }

      const { container } = render(
        <table>
          <tbody>
            <tr>
              <ScheduleCell
                assignment={assignment}
                isWeekend={false}
                isToday={false}
                timeOfDay="AM"
              />
            </tr>
          </tbody>
        </table>
      )

      const badge = container.querySelector('.bg-blue-100')
      expect(badge).toBeInTheDocument()
    })
  })

  describe('Weekend Styling', () => {
    it('should apply weekend shading when isWeekend is true', () => {
      const { container } = render(
        <table>
          <tbody>
            <tr>
              <ScheduleCell
                assignment={undefined}
                isWeekend={true}
                isToday={false}
                timeOfDay="AM"
              />
            </tr>
          </tbody>
        </table>
      )

      const cell = container.querySelector('td')
      expect(cell).toHaveClass('bg-gray-50/50')
    })

    it('should not apply weekend shading when isWeekend is false', () => {
      const { container } = render(
        <table>
          <tbody>
            <tr>
              <ScheduleCell
                assignment={undefined}
                isWeekend={false}
                isToday={false}
                timeOfDay="AM"
              />
            </tr>
          </tbody>
        </table>
      )

      const cell = container.querySelector('td')
      expect(cell).not.toHaveClass('bg-gray-50/50')
    })
  })

  describe('Today Highlighting', () => {
    it('should apply today highlight when isToday is true', () => {
      const { container } = render(
        <table>
          <tbody>
            <tr>
              <ScheduleCell
                assignment={undefined}
                isWeekend={false}
                isToday={true}
                timeOfDay="AM"
              />
            </tr>
          </tbody>
        </table>
      )

      const cell = container.querySelector('td')
      expect(cell).toHaveClass('bg-blue-50/30')
    })

    it('should not apply today highlight when isToday is false', () => {
      const { container } = render(
        <table>
          <tbody>
            <tr>
              <ScheduleCell
                assignment={undefined}
                isWeekend={false}
                isToday={false}
                timeOfDay="AM"
              />
            </tr>
          </tbody>
        </table>
      )

      const cell = container.querySelector('td')
      expect(cell).not.toHaveClass('bg-blue-50/30')
    })
  })

  describe('Time of Day Styling', () => {
    it('should apply thicker border for PM cells', () => {
      const { container } = render(
        <table>
          <tbody>
            <tr>
              <ScheduleCell
                assignment={undefined}
                isWeekend={false}
                isToday={false}
                timeOfDay="PM"
              />
            </tr>
          </tbody>
        </table>
      )

      const cell = container.querySelector('td')
      expect(cell).toHaveClass('border-r-2')
      expect(cell).toHaveClass('border-r-gray-300')
    })

    it('should not apply thicker border for AM cells', () => {
      const { container } = render(
        <table>
          <tbody>
            <tr>
              <ScheduleCell
                assignment={undefined}
                isWeekend={false}
                isToday={false}
                timeOfDay="AM"
              />
            </tr>
          </tbody>
        </table>
      )

      const cell = container.querySelector('td')
      expect(cell).not.toHaveClass('border-r-2')
    })
  })

  describe('Tooltip Content', () => {
    it('should show template name in tooltip', () => {
      const assignment = {
        abbreviation: 'IM',
        activityType: 'inpatient',
        templateName: 'Inpatient Medicine',
      }

      const { container } = render(
        <table>
          <tbody>
            <tr>
              <ScheduleCell
                assignment={assignment}
                isWeekend={false}
                isToday={false}
                timeOfDay="AM"
              />
            </tr>
          </tbody>
        </table>
      )

      const badge = container.querySelector('[title]')
      expect(badge).toHaveAttribute('title', expect.stringContaining('Inpatient Medicine'))
    })

    it('should show activity type in tooltip', () => {
      const assignment = {
        abbreviation: 'IM',
        activityType: 'inpatient',
        templateName: 'Inpatient Medicine',
      }

      const { container } = render(
        <table>
          <tbody>
            <tr>
              <ScheduleCell
                assignment={assignment}
                isWeekend={false}
                isToday={false}
                timeOfDay="AM"
              />
            </tr>
          </tbody>
        </table>
      )

      const badge = container.querySelector('[title]')
      expect(badge).toHaveAttribute('title', expect.stringContaining('Type: inpatient'))
    })

    it('should show role in tooltip when not primary', () => {
      const assignment = {
        abbreviation: 'IM',
        activityType: 'inpatient',
        templateName: 'Inpatient Medicine',
        role: 'backup',
      }

      const { container } = render(
        <table>
          <tbody>
            <tr>
              <ScheduleCell
                assignment={assignment}
                isWeekend={false}
                isToday={false}
                timeOfDay="AM"
              />
            </tr>
          </tbody>
        </table>
      )

      const badge = container.querySelector('[title]')
      expect(badge).toHaveAttribute('title', expect.stringContaining('Role: backup'))
    })

    it('should not show role in tooltip when role is primary', () => {
      const assignment = {
        abbreviation: 'IM',
        activityType: 'inpatient',
        templateName: 'Inpatient Medicine',
        role: 'primary',
      }

      const { container } = render(
        <table>
          <tbody>
            <tr>
              <ScheduleCell
                assignment={assignment}
                isWeekend={false}
                isToday={false}
                timeOfDay="AM"
              />
            </tr>
          </tbody>
        </table>
      )

      const badge = container.querySelector('[title]')
      expect(badge).not.toHaveAttribute('title', expect.stringContaining('Role:'))
    })

    it('should show notes in tooltip', () => {
      const assignment = {
        abbreviation: 'IM',
        activityType: 'inpatient',
        templateName: 'Inpatient Medicine',
        notes: 'Special assignment',
      }

      const { container } = render(
        <table>
          <tbody>
            <tr>
              <ScheduleCell
                assignment={assignment}
                isWeekend={false}
                isToday={false}
                timeOfDay="AM"
              />
            </tr>
          </tbody>
        </table>
      )

      const badge = container.querySelector('[title]')
      expect(badge).toHaveAttribute('title', expect.stringContaining('Note: Special assignment'))
    })

    it('should use abbreviation as fallback when no template name', () => {
      const assignment = {
        abbreviation: 'IM',
        activityType: 'inpatient',
      }

      const { container } = render(
        <table>
          <tbody>
            <tr>
              <ScheduleCell
                assignment={assignment}
                isWeekend={false}
                isToday={false}
                timeOfDay="AM"
              />
            </tr>
          </tbody>
        </table>
      )

      const badge = container.querySelector('[title]')
      expect(badge).toHaveAttribute('title', expect.stringContaining('IM'))
    })
  })

  describe('Hover Effects', () => {
    it('should apply hover effects to assignment badges', () => {
      const assignment = {
        abbreviation: 'IM',
        activityType: 'inpatient',
      }

      const { container } = render(
        <table>
          <tbody>
            <tr>
              <ScheduleCell
                assignment={assignment}
                isWeekend={false}
                isToday={false}
                timeOfDay="AM"
              />
            </tr>
          </tbody>
        </table>
      )

      const badge = screen.getByText('IM')
      expect(badge).toHaveClass('hover:scale-105')
      expect(badge).toHaveClass('hover:shadow-sm')
      expect(badge).toHaveClass('transition-all')
    })
  })

  describe('Combined States', () => {
    it('should apply both weekend and today highlighting', () => {
      const { container } = render(
        <table>
          <tbody>
            <tr>
              <ScheduleCell
                assignment={undefined}
                isWeekend={true}
                isToday={true}
                timeOfDay="AM"
              />
            </tr>
          </tbody>
        </table>
      )

      const cell = container.querySelector('td')
      expect(cell).toHaveClass('bg-gray-50/50')
      expect(cell).toHaveClass('bg-blue-50/30')
    })

    it('should work with assignment, weekend, and today all true', () => {
      const assignment = {
        abbreviation: 'CL',
        activityType: 'clinic',
      }

      const { container } = render(
        <table>
          <tbody>
            <tr>
              <ScheduleCell
                assignment={assignment}
                isWeekend={true}
                isToday={true}
                timeOfDay="PM"
              />
            </tr>
          </tbody>
        </table>
      )

      const cell = container.querySelector('td')
      expect(cell).toHaveClass('bg-gray-50/50')
      expect(cell).toHaveClass('bg-blue-50/30')
      expect(cell).toHaveClass('border-r-2')
      expect(screen.getByText('CL')).toBeInTheDocument()
    })
  })
})

describe('ScheduleSeparatorRow', () => {
  describe('Basic Rendering', () => {
    it('should render separator row with label', () => {
      render(
        <table>
          <tbody>
            <ScheduleSeparatorRow label="PGY-1" columnCount={7} />
          </tbody>
        </table>
      )

      expect(screen.getByText('PGY-1')).toBeInTheDocument()
    })

    it('should render without label', () => {
      const { container } = render(
        <table>
          <tbody>
            <ScheduleSeparatorRow columnCount={7} />
          </tbody>
        </table>
      )

      const cell = container.querySelector('td')
      expect(cell).toBeInTheDocument()
      expect(cell?.textContent).toBe('')
    })

    it('should apply proper styling', () => {
      const { container } = render(
        <table>
          <tbody>
            <ScheduleSeparatorRow label="PGY-2" columnCount={7} />
          </tbody>
        </table>
      )

      const row = container.querySelector('tr')
      expect(row).toHaveClass('bg-gray-100/50')
      expect(row).toHaveClass('border-y')
      expect(row).toHaveClass('border-gray-300')
    })

    it('should apply text styling', () => {
      const { container } = render(
        <table>
          <tbody>
            <ScheduleSeparatorRow label="Faculty" columnCount={7} />
          </tbody>
        </table>
      )

      const cell = container.querySelector('td')
      expect(cell).toHaveClass('uppercase')
      expect(cell).toHaveClass('text-gray-500')
      expect(cell).toHaveClass('font-medium')
    })
  })

  describe('Column Spanning', () => {
    it('should calculate correct colspan for 7 columns', () => {
      const { container } = render(
        <table>
          <tbody>
            <ScheduleSeparatorRow label="PGY-1" columnCount={7} />
          </tbody>
        </table>
      )

      const cell = container.querySelector('td')
      // Formula: 1 + columnCount * 2 = 1 + 7 * 2 = 15
      expect(cell).toHaveAttribute('colSpan', '15')
    })

    it('should calculate correct colspan for 14 columns', () => {
      const { container } = render(
        <table>
          <tbody>
            <ScheduleSeparatorRow label="PGY-2" columnCount={14} />
          </tbody>
        </table>
      )

      const cell = container.querySelector('td')
      // Formula: 1 + columnCount * 2 = 1 + 14 * 2 = 29
      expect(cell).toHaveAttribute('colSpan', '29')
    })

    it('should handle single column', () => {
      const { container } = render(
        <table>
          <tbody>
            <ScheduleSeparatorRow label="Single" columnCount={1} />
          </tbody>
        </table>
      )

      const cell = container.querySelector('td')
      // Formula: 1 + columnCount * 2 = 1 + 1 * 2 = 3
      expect(cell).toHaveAttribute('colSpan', '3')
    })
  })
})
