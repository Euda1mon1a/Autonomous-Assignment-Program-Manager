import { render, screen, within } from '@/test-utils'
import userEvent from '@testing-library/user-event'
import { AbsenceList } from '@/components/AbsenceList'
import { mockFactories } from '../utils/test-utils'
import type { Absence, Person } from '@/types/api'

describe('AbsenceList', () => {
  const mockPeople: Person[] = [
    mockFactories.person({
      id: 'person-1',
      name: 'Dr. John Smith',
      type: 'resident',
      pgyLevel: 2,
    }),
    mockFactories.person({
      id: 'person-2',
      name: 'Dr. Jane Doe',
      type: 'faculty',
      pgyLevel: null,
    }),
  ]

  const mockAbsences: Absence[] = [
    mockFactories.absence({
      id: 'absence-1',
      personId: 'person-1',
      startDate: '2024-02-05',
      endDate: '2024-02-07',
      absenceType: 'vacation',
      notes: 'Spring break',
    }),
    mockFactories.absence({
      id: 'absence-2',
      personId: 'person-2',
      startDate: '2024-03-10',
      endDate: '2024-03-15',
      absenceType: 'deployment',
      notes: null,
    }),
  ]

  const mockOnEdit = jest.fn()
  const mockOnDelete = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Table Rendering', () => {
    it('should render table with correct headers', () => {
      render(
        <AbsenceList
          absences={mockAbsences}
          people={mockPeople}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      )

      expect(screen.getByText('Person')).toBeInTheDocument()
      expect(screen.getByText('Type')).toBeInTheDocument()
      expect(screen.getByText('Start Date')).toBeInTheDocument()
      expect(screen.getByText('End Date')).toBeInTheDocument()
      expect(screen.getByText('Notes')).toBeInTheDocument()
      expect(screen.getByText('Actions')).toBeInTheDocument()
    })

    it('should render all absences in the list', () => {
      render(
        <AbsenceList
          absences={mockAbsences}
          people={mockPeople}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      )

      expect(screen.getByText('Dr. John Smith')).toBeInTheDocument()
      expect(screen.getByText('Dr. Jane Doe')).toBeInTheDocument()
    })

    it('should render person information with correct formatting', () => {
      render(
        <AbsenceList
          absences={mockAbsences}
          people={mockPeople}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      )

      // Resident should show PGY level
      const johnRow = screen.getByText('Dr. John Smith').closest('tr')
      expect(within(johnRow!).getByText('PGY-2')).toBeInTheDocument()

      // Faculty should show "Faculty"
      const janeRow = screen.getByText('Dr. Jane Doe').closest('tr')
      expect(within(janeRow!).getByText('Faculty')).toBeInTheDocument()
    })

    it('should display absence types with correct formatting', () => {
      render(
        <AbsenceList
          absences={mockAbsences}
          people={mockPeople}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      )

      expect(screen.getByText('vacation')).toBeInTheDocument()
      expect(screen.getByText('deployment')).toBeInTheDocument()
    })

    it('should format dates correctly', () => {
      render(
        <AbsenceList
          absences={mockAbsences}
          people={mockPeople}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      )

      // Check that dates are formatted in expected pattern (date may shift by timezone)
      const datePattern = /\w{3} \d{1,2}, 2024/
      const dateCells = screen.getAllByText(datePattern)
      // Should have 4 dates (2 absences x 2 dates each)
      expect(dateCells.length).toBeGreaterThanOrEqual(4)
    })

    it('should display notes when present', () => {
      render(
        <AbsenceList
          absences={mockAbsences}
          people={mockPeople}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      )

      expect(screen.getByText('Spring break')).toBeInTheDocument()
    })

    it('should display dash for empty notes', () => {
      render(
        <AbsenceList
          absences={mockAbsences}
          people={mockPeople}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      )

      const janeRow = screen.getByText('Dr. Jane Doe').closest('tr')
      const notesCell = within(janeRow!).getAllByText('-')[0]
      expect(notesCell).toBeInTheDocument()
    })
  })

  describe('Absence Type Styling', () => {
    it('should apply correct color classes for vacation', () => {
      render(
        <AbsenceList
          absences={mockAbsences}
          people={mockPeople}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      )

      const vacationBadge = screen.getByText('vacation')
      expect(vacationBadge).toHaveClass('bg-green-100')
      expect(vacationBadge).toHaveClass('text-green-800')
    })

    it('should apply correct color classes for deployment', () => {
      render(
        <AbsenceList
          absences={mockAbsences}
          people={mockPeople}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      )

      const deploymentBadge = screen.getByText('deployment')
      expect(deploymentBadge).toHaveClass('bg-orange-100')
      expect(deploymentBadge).toHaveClass('text-orange-800')
    })

    it('should apply fallback color for unknown absence type', () => {
      const absenceWithUnknownType: Absence[] = [
        mockFactories.absence({
          id: 'absence-1',
          personId: 'person-1',
          absenceType: 'unknown_type' as any,
        }),
      ]

      render(
        <AbsenceList
          absences={absenceWithUnknownType}
          people={mockPeople}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      )

      const badge = screen.getByText('unknown type')
      expect(badge).toHaveClass('bg-purple-100')
      expect(badge).toHaveClass('text-purple-800')
    })

    it('should format absence type with underscores replaced', () => {
      const absenceWithUnderscore: Absence[] = [
        mockFactories.absence({
          id: 'absence-1',
          personId: 'person-1',
          absenceType: 'familyEmergency',
        }),
      ]

      render(
        <AbsenceList
          absences={absenceWithUnderscore}
          people={mockPeople}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      )

      expect(screen.getByText('family emergency')).toBeInTheDocument()
    })
  })

  describe('Sorting', () => {
    it('should sort absences by start date in ascending order', () => {
      const unsortedAbsences: Absence[] = [
        mockFactories.absence({
          id: 'absence-3',
          personId: 'person-1',
          startDate: '2024-06-15',
          endDate: '2024-06-20',
        }),
        mockFactories.absence({
          id: 'absence-1',
          personId: 'person-1',
          startDate: '2024-01-15',
          endDate: '2024-01-20',
        }),
        mockFactories.absence({
          id: 'absence-2',
          personId: 'person-2',
          startDate: '2024-03-15',
          endDate: '2024-03-20',
        }),
      ]

      const { container } = render(
        <AbsenceList
          absences={unsortedAbsences}
          people={mockPeople}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      )

      const rows = container.querySelectorAll('tbody tr')

      // Verify the rows are sorted by checking the month names in order
      // Use getAllByText to handle timezone variations
      const firstRowText = (rows[0] as HTMLElement).textContent || ''
      const secondRowText = (rows[1] as HTMLElement).textContent || ''
      const thirdRowText = (rows[2] as HTMLElement).textContent || ''

      // First row should be January
      expect(firstRowText).toMatch(/Jan.*2024/)
      // Second row should be March
      expect(secondRowText).toMatch(/Mar.*2024/)
      // Third row should be June
      expect(thirdRowText).toMatch(/Jun.*2024/)
    })
  })

  describe('Action Buttons', () => {
    it('should render edit and delete buttons for each absence', () => {
      render(
        <AbsenceList
          absences={mockAbsences}
          people={mockPeople}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      )

      const editButtons = screen.getAllByTitle('Edit absence')
      const deleteButtons = screen.getAllByTitle('Delete absence')

      expect(editButtons).toHaveLength(2)
      expect(deleteButtons).toHaveLength(2)
    })

    it('should call onEdit with correct absence when edit button is clicked', async () => {
      const user = userEvent.setup()

      render(
        <AbsenceList
          absences={mockAbsences}
          people={mockPeople}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      )

      const editButtons = screen.getAllByTitle('Edit absence')
      await user.click(editButtons[0])

      expect(mockOnEdit).toHaveBeenCalledTimes(1)
      expect(mockOnEdit).toHaveBeenCalledWith(
        expect.objectContaining({
          id: 'absence-1',
          personId: 'person-1',
        })
      )
    })

    it('should call onDelete with correct absence when delete button is clicked', async () => {
      const user = userEvent.setup()

      render(
        <AbsenceList
          absences={mockAbsences}
          people={mockPeople}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      )

      const deleteButtons = screen.getAllByTitle('Delete absence')
      await user.click(deleteButtons[1])

      expect(mockOnDelete).toHaveBeenCalledTimes(1)
      expect(mockOnDelete).toHaveBeenCalledWith(
        expect.objectContaining({
          id: 'absence-2',
          personId: 'person-2',
        })
      )
    })

    it('should have appropriate styling for edit button', () => {
      render(
        <AbsenceList
          absences={mockAbsences}
          people={mockPeople}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      )

      const editButton = screen.getAllByTitle('Edit absence')[0]
      expect(editButton).toHaveClass('text-blue-600')
      expect(editButton).toHaveClass('hover:text-blue-800')
    })

    it('should have appropriate styling for delete button', () => {
      render(
        <AbsenceList
          absences={mockAbsences}
          people={mockPeople}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      )

      const deleteButton = screen.getAllByTitle('Delete absence')[0]
      expect(deleteButton).toHaveClass('text-red-600')
      expect(deleteButton).toHaveClass('hover:text-red-800')
    })
  })

  describe('Empty State', () => {
    it('should display empty state message when no absences', () => {
      render(
        <AbsenceList
          absences={[]}
          people={mockPeople}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      )

      expect(screen.getByText(/no absences found/i)).toBeInTheDocument()
      expect(screen.getByText(/click "add absence" to create one/i)).toBeInTheDocument()
    })

    it('should not render table when no absences', () => {
      render(
        <AbsenceList
          absences={[]}
          people={mockPeople}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      )

      expect(screen.queryByRole('table')).not.toBeInTheDocument()
    })

    it('should center empty state message', () => {
      const { container } = render(
        <AbsenceList
          absences={[]}
          people={mockPeople}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      )

      const emptyState = container.querySelector('.text-center')
      expect(emptyState).toBeInTheDocument()
    })
  })

  describe('Person Mapping', () => {
    it('should display "Unknown" for missing person', () => {
      const absenceWithUnknownPerson: Absence[] = [
        mockFactories.absence({
          id: 'absence-1',
          personId: 'unknown-person',
        }),
      ]

      render(
        <AbsenceList
          absences={absenceWithUnknownPerson}
          people={mockPeople}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      )

      expect(screen.getByText('Unknown')).toBeInTheDocument()
    })

    it('should handle empty people array gracefully', () => {
      render(
        <AbsenceList
          absences={mockAbsences}
          people={[]}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      )

      const unknownElements = screen.getAllByText('Unknown')
      expect(unknownElements).toHaveLength(2)
    })
  })

  describe('Row Hover Effect', () => {
    it('should apply hover class to table rows', () => {
      const { container } = render(
        <AbsenceList
          absences={mockAbsences}
          people={mockPeople}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      )

      const rows = container.querySelectorAll('tbody tr')
      rows.forEach((row) => {
        expect(row).toHaveClass('hover:bg-gray-50')
      })
    })
  })

  describe('Table Accessibility', () => {
    it('should have proper table structure', () => {
      render(
        <AbsenceList
          absences={mockAbsences}
          people={mockPeople}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      )

      expect(screen.getByRole('table')).toBeInTheDocument()
    })

    it('should have column headers', () => {
      render(
        <AbsenceList
          absences={mockAbsences}
          people={mockPeople}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      )

      const columnHeaders = screen.getAllByRole('columnheader')
      expect(columnHeaders).toHaveLength(6)
    })

    it('should have table rows', () => {
      render(
        <AbsenceList
          absences={mockAbsences}
          people={mockPeople}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      )

      const rows = screen.getAllByRole('row')
      // Header row + 2 data rows
      expect(rows).toHaveLength(3)
    })
  })

  describe('Notes Truncation', () => {
    it('should apply truncate class to notes cell', () => {
      render(
        <AbsenceList
          absences={mockAbsences}
          people={mockPeople}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      )

      // The notes text is directly inside the td element which has the truncate class
      const notesCell = screen.getByText('Spring break').closest('td')
      expect(notesCell).toHaveClass('truncate')
      expect(notesCell).toHaveClass('max-w-xs')
    })
  })
})
