import { render, screen, fireEvent } from '@/test-utils'
import {
  AssignmentWarnings,
  WarningBadge,
  generateWarnings,
  type AssignmentWarning,
} from '@/components/schedule/AssignmentWarnings'

describe('AssignmentWarnings', () => {
  describe('Empty State', () => {
    it('should not render when warnings array is empty', () => {
      const { container } = render(<AssignmentWarnings warnings={[]} />)

      expect(container.firstChild).toBeNull()
    })
  })

  describe('Warnings Display', () => {
    it('should render warning count', () => {
      const warnings: AssignmentWarning[] = [
        {
          type: 'hours',
          severity: 'warning',
          message: 'Approaching hour limit',
        },
        {
          type: 'supervision',
          severity: 'critical',
          message: 'No supervisor assigned',
        },
      ]

      render(<AssignmentWarnings warnings={warnings} />)

      expect(screen.getByText('Warnings (2)')).toBeInTheDocument()
    })

    it('should render all warning messages', () => {
      const warnings: AssignmentWarning[] = [
        {
          type: 'hours',
          severity: 'warning',
          message: 'Approaching hour limit',
        },
        {
          type: 'supervision',
          severity: 'critical',
          message: 'No supervisor assigned',
        },
      ]

      render(<AssignmentWarnings warnings={warnings} />)

      expect(screen.getByText('Approaching hour limit')).toBeInTheDocument()
      expect(screen.getByText('No supervisor assigned')).toBeInTheDocument()
    })

    it('should display warning types', () => {
      const warnings: AssignmentWarning[] = [
        {
          type: 'hours',
          severity: 'warning',
          message: 'Test message',
        },
      ]

      render(<AssignmentWarnings warnings={warnings} />)

      expect(screen.getByText('hours')).toBeInTheDocument()
    })
  })

  describe('Severity Styling', () => {
    it('should apply critical styling for critical warnings', () => {
      const warnings: AssignmentWarning[] = [
        {
          type: 'hours',
          severity: 'critical',
          message: 'Critical warning',
        },
      ]

      const { container } = render(<AssignmentWarnings warnings={warnings} />)

      const warningElement = container.querySelector('.bg-red-50')
      expect(warningElement).toHaveClass('bg-red-50')
      expect(warningElement).toHaveClass('border-red-200')
      expect(warningElement).toHaveClass('text-red-800')
    })

    it('should apply warning styling for warning severity', () => {
      const warnings: AssignmentWarning[] = [
        {
          type: 'hours',
          severity: 'warning',
          message: 'Warning message',
        },
      ]

      const { container } = render(<AssignmentWarnings warnings={warnings} />)

      const warningElement = container.querySelector('.bg-amber-50')
      expect(warningElement).toHaveClass('bg-amber-50')
      expect(warningElement).toHaveClass('border-amber-200')
      expect(warningElement).toHaveClass('text-amber-800')
    })

    it('should apply info styling for info severity', () => {
      const warnings: AssignmentWarning[] = [
        {
          type: 'hours',
          severity: 'info',
          message: 'Info message',
        },
      ]

      const { container } = render(<AssignmentWarnings warnings={warnings} />)

      const warningElement = container.querySelector('.bg-blue-50')
      expect(warningElement).toHaveClass('bg-blue-50')
      expect(warningElement).toHaveClass('border-blue-200')
      expect(warningElement).toHaveClass('text-blue-800')
    })
  })

  describe('Warning Sorting', () => {
    it('should sort warnings by severity (critical first)', () => {
      const warnings: AssignmentWarning[] = [
        {
          type: 'hours',
          severity: 'info',
          message: 'Info warning',
        },
        {
          type: 'supervision',
          severity: 'critical',
          message: 'Critical warning',
        },
        {
          type: 'conflict',
          severity: 'warning',
          message: 'Warning message',
        },
      ]

      const { container } = render(<AssignmentWarnings warnings={warnings} />)

      const messages = container.querySelectorAll('.text-sm')
      const messageTexts = Array.from(messages).map((el) => el.textContent)

      const criticalIndex = messageTexts.indexOf('Critical warning')
      const warningIndex = messageTexts.indexOf('Warning message')
      const infoIndex = messageTexts.indexOf('Info warning')

      expect(criticalIndex).toBeLessThan(warningIndex)
      expect(warningIndex).toBeLessThan(infoIndex)
    })
  })

  describe('Critical Acknowledgment', () => {
    it('should show acknowledgment checkbox when there are critical warnings', () => {
      const warnings: AssignmentWarning[] = [
        {
          type: 'supervision',
          severity: 'critical',
          message: 'Critical warning',
        },
      ]

      const onAcknowledge = jest.fn()

      render(
        <AssignmentWarnings
          warnings={warnings}
          onAcknowledgeCritical={onAcknowledge}
        />
      )

      expect(screen.getByRole('checkbox')).toBeInTheDocument()
      expect(screen.getByText(/I understand this override/)).toBeInTheDocument()
    })

    it('should not show acknowledgment checkbox when no critical warnings', () => {
      const warnings: AssignmentWarning[] = [
        {
          type: 'hours',
          severity: 'warning',
          message: 'Warning message',
        },
      ]

      const onAcknowledge = jest.fn()

      render(
        <AssignmentWarnings
          warnings={warnings}
          onAcknowledgeCritical={onAcknowledge}
        />
      )

      expect(screen.queryByRole('checkbox')).not.toBeInTheDocument()
    })

    it('should call onAcknowledgeCritical when checkbox is toggled', () => {
      const warnings: AssignmentWarning[] = [
        {
          type: 'supervision',
          severity: 'critical',
          message: 'Critical warning',
        },
      ]

      const onAcknowledge = jest.fn()

      render(
        <AssignmentWarnings
          warnings={warnings}
          onAcknowledgeCritical={onAcknowledge}
        />
      )

      const checkbox = screen.getByRole('checkbox') as HTMLInputElement
      fireEvent.click(checkbox)

      expect(onAcknowledge).toHaveBeenCalledWith(true)
    })

    it('should reflect criticalAcknowledged state in checkbox', () => {
      const warnings: AssignmentWarning[] = [
        {
          type: 'supervision',
          severity: 'critical',
          message: 'Critical warning',
        },
      ]

      const onAcknowledge = jest.fn()

      render(
        <AssignmentWarnings
          warnings={warnings}
          onAcknowledgeCritical={onAcknowledge}
          criticalAcknowledged={true}
        />
      )

      const checkbox = screen.getByRole('checkbox') as HTMLInputElement
      expect(checkbox.checked).toBe(true)
    })
  })

  describe('Warning Icons', () => {
    it('should display correct icon for hours warning', () => {
      const warnings: AssignmentWarning[] = [
        {
          type: 'hours',
          severity: 'warning',
          message: 'Hour limit warning',
        },
      ]

      const { container } = render(<AssignmentWarnings warnings={warnings} />)

      expect(container.querySelector('.lucide-clock')).toBeInTheDocument()
    })

    it('should display correct icon for supervision warning', () => {
      const warnings: AssignmentWarning[] = [
        {
          type: 'supervision',
          severity: 'warning',
          message: 'Supervision warning',
        },
      ]

      const { container } = render(<AssignmentWarnings warnings={warnings} />)

      expect(container.querySelector('.lucide-users')).toBeInTheDocument()
    })

    it('should display correct icon for conflict warning', () => {
      const warnings: AssignmentWarning[] = [
        {
          type: 'conflict',
          severity: 'warning',
          message: 'Conflict warning',
        },
      ]

      const { container } = render(<AssignmentWarnings warnings={warnings} />)

      expect(container.querySelector('.lucide-calendar')).toBeInTheDocument()
    })

    it('should display correct icon for absence warning', () => {
      const warnings: AssignmentWarning[] = [
        {
          type: 'absence',
          severity: 'warning',
          message: 'Absence warning',
        },
      ]

      const { container } = render(<AssignmentWarnings warnings={warnings} />)

      expect(container.querySelector('.lucide-user-x')).toBeInTheDocument()
    })

    it('should display correct icon for capacity warning', () => {
      const warnings: AssignmentWarning[] = [
        {
          type: 'capacity',
          severity: 'warning',
          message: 'Capacity warning',
        },
      ]

      const { container } = render(<AssignmentWarnings warnings={warnings} />)

      expect(container.querySelector('.lucide-building-2')).toBeInTheDocument()
    })
  })

  describe('Scrolling Behavior', () => {
    it('should apply max height and overflow to warnings list', () => {
      const warnings: AssignmentWarning[] = Array.from({ length: 10 }, (_, i) => ({
        type: 'hours',
        severity: 'warning',
        message: `Warning ${i}`,
      }))

      const { container } = render(<AssignmentWarnings warnings={warnings} />)

      const listContainer = container.querySelector('.max-h-48')
      expect(listContainer).toHaveClass('overflow-y-auto')
    })
  })
})

describe('WarningBadge', () => {
  describe('Empty State', () => {
    it('should not render when warnings array is empty', () => {
      const { container } = render(<WarningBadge warnings={[]} />)

      expect(container.firstChild).toBeNull()
    })
  })

  describe('Badge Rendering', () => {
    it('should render badge with warning count', () => {
      const warnings: AssignmentWarning[] = [
        {
          type: 'hours',
          severity: 'warning',
          message: 'Warning 1',
        },
        {
          type: 'supervision',
          severity: 'warning',
          message: 'Warning 2',
        },
      ]

      render(<WarningBadge warnings={warnings} />)

      expect(screen.getByText('2')).toBeInTheDocument()
    })

    it('should apply critical styling when there are critical warnings', () => {
      const warnings: AssignmentWarning[] = [
        {
          type: 'supervision',
          severity: 'critical',
          message: 'Critical warning',
        },
      ]

      const { container } = render(<WarningBadge warnings={warnings} />)

      const badge = container.querySelector('.bg-red-100')
      expect(badge).toHaveClass('text-red-700')
    })

    it('should apply warning styling when there are only warning-level warnings', () => {
      const warnings: AssignmentWarning[] = [
        {
          type: 'hours',
          severity: 'warning',
          message: 'Warning message',
        },
      ]

      const { container } = render(<WarningBadge warnings={warnings} />)

      const badge = container.querySelector('.bg-amber-100')
      expect(badge).toHaveClass('text-amber-700')
    })

    it('should apply info styling when there are only info warnings', () => {
      const warnings: AssignmentWarning[] = [
        {
          type: 'hours',
          severity: 'info',
          message: 'Info message',
        },
      ]

      const { container } = render(<WarningBadge warnings={warnings} />)

      const badge = container.querySelector('.bg-blue-100')
      expect(badge).toHaveClass('text-blue-700')
    })

    it('should prioritize critical over warning', () => {
      const warnings: AssignmentWarning[] = [
        {
          type: 'hours',
          severity: 'warning',
          message: 'Warning',
        },
        {
          type: 'supervision',
          severity: 'critical',
          message: 'Critical',
        },
      ]

      const { container } = render(<WarningBadge warnings={warnings} />)

      const badge = container.querySelector('.bg-red-100')
      expect(badge).toBeInTheDocument()
    })
  })

  describe('Compact Mode', () => {
    it('should render compact version when compact is true', () => {
      const warnings: AssignmentWarning[] = [
        {
          type: 'hours',
          severity: 'warning',
          message: 'Warning message',
        },
      ]

      const { container } = render(<WarningBadge warnings={warnings} compact={true} />)

      const compactBadge = container.querySelector('.w-5.h-5')
      expect(compactBadge).toBeInTheDocument()
      expect(screen.queryByText('1')).not.toBeInTheDocument()
    })

    it('should render full version when compact is false', () => {
      const warnings: AssignmentWarning[] = [
        {
          type: 'hours',
          severity: 'warning',
          message: 'Warning message',
        },
      ]

      render(<WarningBadge warnings={warnings} compact={false} />)

      expect(screen.getByText('1')).toBeInTheDocument()
    })
  })
})

describe('generateWarnings', () => {
  describe('Hours Warning', () => {
    it('should generate warning when exceeding max hours', () => {
      const context = {
        personId: 'p1',
        personName: 'Dr. Smith',
        date: '2024-01-15',
        session: 'AM' as const,
        weeklyHours: 78,
        maxWeeklyHours: 80,
      }

      const warnings = generateWarnings(context)

      expect(warnings).toHaveLength(1)
      expect(warnings[0].type).toBe('hours')
      expect(warnings[0].severity).toBe('warning')
      expect(warnings[0].message).toContain('82 hours')
    })

    it('should generate critical warning when significantly over hours', () => {
      const context = {
        personId: 'p1',
        personName: 'Dr. Smith',
        date: '2024-01-15',
        session: 'AM' as const,
        weeklyHours: 85, // 85 + 4 = 89, which is 9 hours over 80 = critical
        maxWeeklyHours: 80,
      }

      const warnings = generateWarnings(context)

      expect(warnings).toHaveLength(1)
      expect(warnings[0].severity).toBe('critical')
    })

    it('should not generate warning when under max hours', () => {
      const context = {
        personId: 'p1',
        date: '2024-01-15',
        session: 'AM' as const,
        weeklyHours: 70,
        maxWeeklyHours: 80,
      }

      const warnings = generateWarnings(context)

      const hoursWarnings = warnings.filter((w) => w.type === 'hours')
      expect(hoursWarnings).toHaveLength(0)
    })
  })

  describe('Supervision Warning', () => {
    it('should generate critical warning when supervision required but missing', () => {
      const context = {
        personId: 'p1',
        date: '2024-01-15',
        session: 'AM' as const,
        requiresSupervision: true,
        hasSupervisor: false,
      }

      const warnings = generateWarnings(context)

      expect(warnings).toHaveLength(1)
      expect(warnings[0].type).toBe('supervision')
      expect(warnings[0].severity).toBe('critical')
    })

    it('should not generate warning when supervisor is present', () => {
      const context = {
        personId: 'p1',
        date: '2024-01-15',
        session: 'AM' as const,
        requiresSupervision: true,
        hasSupervisor: true,
      }

      const warnings = generateWarnings(context)

      const supervisionWarnings = warnings.filter((w) => w.type === 'supervision')
      expect(supervisionWarnings).toHaveLength(0)
    })
  })

  describe('Conflict Warning', () => {
    it('should generate critical warning when assignment conflicts', () => {
      const context = {
        personId: 'p1',
        personName: 'Dr. Smith',
        date: '2024-01-15',
        session: 'AM' as const,
        existingAssignments: [
          {
            date: '2024-01-15',
            session: 'AM' as const,
            rotationName: 'Clinic',
          },
        ],
      }

      const warnings = generateWarnings(context)

      expect(warnings).toHaveLength(1)
      expect(warnings[0].type).toBe('conflict')
      expect(warnings[0].severity).toBe('critical')
      expect(warnings[0].message).toContain('already assigned')
    })

    it('should not generate warning for different time slots', () => {
      const context = {
        personId: 'p1',
        date: '2024-01-15',
        session: 'AM' as const,
        existingAssignments: [
          {
            date: '2024-01-15',
            session: 'PM' as const,
            rotationName: 'Clinic',
          },
        ],
      }

      const warnings = generateWarnings(context)

      const conflictWarnings = warnings.filter((w) => w.type === 'conflict')
      expect(conflictWarnings).toHaveLength(0)
    })
  })

  describe('Absence Warning', () => {
    it('should generate critical warning when person is absent', () => {
      const context = {
        personId: 'p1',
        personName: 'Dr. Smith',
        date: '2024-01-15',
        session: 'AM' as const,
        absences: [
          {
            startDate: '2024-01-10',
            endDate: '2024-01-20',
            type: 'vacation',
          },
        ],
      }

      const warnings = generateWarnings(context)

      expect(warnings).toHaveLength(1)
      expect(warnings[0].type).toBe('absence')
      expect(warnings[0].severity).toBe('critical')
      expect(warnings[0].message).toContain('vacation absence')
    })

    it('should not generate warning when date is outside absence period', () => {
      const context = {
        personId: 'p1',
        date: '2024-01-25',
        session: 'AM' as const,
        absences: [
          {
            startDate: '2024-01-10',
            endDate: '2024-01-20',
            type: 'vacation',
          },
        ],
      }

      const warnings = generateWarnings(context)

      const absenceWarnings = warnings.filter((w) => w.type === 'absence')
      expect(absenceWarnings).toHaveLength(0)
    })
  })

  describe('Capacity Warning', () => {
    it('should generate warning when rotation is at capacity', () => {
      const context = {
        personId: 'p1',
        date: '2024-01-15',
        session: 'AM' as const,
        rotationCapacity: 5,
        currentRotationCount: 5,
      }

      const warnings = generateWarnings(context)

      expect(warnings).toHaveLength(1)
      expect(warnings[0].type).toBe('capacity')
      expect(warnings[0].severity).toBe('warning')
      expect(warnings[0].message).toContain('at capacity')
    })

    it('should not generate warning when rotation is under capacity', () => {
      const context = {
        personId: 'p1',
        date: '2024-01-15',
        session: 'AM' as const,
        rotationCapacity: 5,
        currentRotationCount: 3,
      }

      const warnings = generateWarnings(context)

      const capacityWarnings = warnings.filter((w) => w.type === 'capacity')
      expect(capacityWarnings).toHaveLength(0)
    })
  })

  describe('Multiple Warnings', () => {
    it('should generate multiple warnings when multiple conditions are met', () => {
      const context = {
        personId: 'p1',
        personName: 'Dr. Smith',
        date: '2024-01-15',
        session: 'AM' as const,
        weeklyHours: 78,
        maxWeeklyHours: 80,
        requiresSupervision: true,
        hasSupervisor: false,
        rotationCapacity: 5,
        currentRotationCount: 5,
      }

      const warnings = generateWarnings(context)

      expect(warnings.length).toBeGreaterThan(1)
      expect(warnings.some((w) => w.type === 'hours')).toBe(true)
      expect(warnings.some((w) => w.type === 'supervision')).toBe(true)
      expect(warnings.some((w) => w.type === 'capacity')).toBe(true)
    })
  })
})
