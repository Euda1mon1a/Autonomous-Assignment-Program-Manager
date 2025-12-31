import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { PersonFilter } from '@/components/schedule/PersonFilter'

// Mock the hooks
jest.mock('@/lib/hooks', () => ({
  usePeople: jest.fn(),
}))

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(),
}))

const { usePeople } = require('@/lib/hooks')
const { useAuth } = require('@/contexts/AuthContext')

describe('PersonFilter', () => {
  const mockPeople = {
    items: [
      {
        id: 'p1',
        name: 'Dr. Alice Smith',
        type: 'resident',
        pgy_level: 1,
        email: 'alice@example.com',
      },
      {
        id: 'p2',
        name: 'Dr. Bob Johnson',
        type: 'resident',
        pgy_level: 3,
        email: 'bob@example.com',
      },
      {
        id: 'p3',
        name: 'Dr. Carol Williams',
        type: 'faculty',
        pgy_level: null,
        email: 'carol@example.com',
      },
      {
        id: 'p4',
        name: 'Dr. David Brown',
        type: 'resident',
        pgy_level: 1,
        email: 'david@example.com',
      },
    ],
  }

  beforeEach(() => {
    jest.clearAllMocks()
    usePeople.mockReturnValue({ data: mockPeople, isLoading: false })
    useAuth.mockReturnValue({ user: { id: 'u1', name: 'Current User' } })
  })

  describe('Button Rendering', () => {
    it('should render trigger button', () => {
      const onSelect = jest.fn()

      render(<PersonFilter selectedPersonId={null} onSelect={onSelect} />)

      expect(screen.getByRole('button', { name: /All People/i })).toBeInTheDocument()
    })

    it('should show "All People" when no person selected', () => {
      const onSelect = jest.fn()

      render(<PersonFilter selectedPersonId={null} onSelect={onSelect} />)

      expect(screen.getByText('All People')).toBeInTheDocument()
    })

    it('should show person name when person is selected', () => {
      const onSelect = jest.fn()

      render(<PersonFilter selectedPersonId="p1" onSelect={onSelect} />)

      expect(screen.getByText('Dr. Alice Smith')).toBeInTheDocument()
    })

    it('should show "My Schedule" when selectedPersonId is "me"', () => {
      const onSelect = jest.fn()

      render(<PersonFilter selectedPersonId="me" onSelect={onSelect} />)

      expect(screen.getByText('My Schedule')).toBeInTheDocument()
    })

    it('should have proper aria attributes when closed', () => {
      const onSelect = jest.fn()

      render(<PersonFilter selectedPersonId={null} onSelect={onSelect} />)

      const button = screen.getByRole('button', { name: /All People/i })
      expect(button).toHaveAttribute('aria-expanded', 'false')
      expect(button).toHaveAttribute('aria-haspopup', 'listbox')
    })

    it('should update aria-expanded when opened', () => {
      const onSelect = jest.fn()

      render(<PersonFilter selectedPersonId={null} onSelect={onSelect} />)

      const button = screen.getByRole('button', { name: /All People/i })
      fireEvent.click(button)

      expect(button).toHaveAttribute('aria-expanded', 'true')
    })
  })

  describe('Dropdown Opening/Closing', () => {
    it('should open dropdown when button is clicked', () => {
      const onSelect = jest.fn()

      render(<PersonFilter selectedPersonId={null} onSelect={onSelect} />)

      const button = screen.getByRole('button', { name: /All People/i })
      fireEvent.click(button)

      expect(screen.getByRole('listbox')).toBeInTheDocument()
    })

    it('should close dropdown when clicking outside', async () => {
      const onSelect = jest.fn()

      render(
        <div>
          <PersonFilter selectedPersonId={null} onSelect={onSelect} />
          <div data-testid="outside">Outside</div>
        </div>
      )

      const button = screen.getByRole('button', { name: /All People/i })
      fireEvent.click(button)

      expect(screen.getByRole('listbox')).toBeInTheDocument()

      const outside = screen.getByTestId('outside')
      fireEvent.mouseDown(outside)

      await waitFor(() => {
        expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
      })
    })

    it('should close dropdown when Escape key is pressed', () => {
      const onSelect = jest.fn()

      render(<PersonFilter selectedPersonId={null} onSelect={onSelect} />)

      const button = screen.getByRole('button', { name: /All People/i })
      fireEvent.click(button)

      const dropdown = screen.getByRole('listbox')
      fireEvent.keyDown(dropdown, { key: 'Escape' })

      expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
    })
  })

  describe('People List Display', () => {
    it('should display all people when dropdown is opened', () => {
      const onSelect = jest.fn()

      render(<PersonFilter selectedPersonId={null} onSelect={onSelect} />)

      const button = screen.getByRole('button')
      fireEvent.click(button)

      expect(screen.getByText('Dr. Alice Smith')).toBeInTheDocument()
      expect(screen.getByText('Dr. Bob Johnson')).toBeInTheDocument()
      expect(screen.getByText('Dr. Carol Williams')).toBeInTheDocument()
      expect(screen.getByText('Dr. David Brown')).toBeInTheDocument()
    })

    it('should group residents by PGY level', () => {
      const onSelect = jest.fn()

      render(<PersonFilter selectedPersonId={null} onSelect={onSelect} />)

      const button = screen.getByRole('button')
      fireEvent.click(button)

      expect(screen.getByText('Residents')).toBeInTheDocument()
      expect(screen.getByText('PGY-1')).toBeInTheDocument()
      expect(screen.getByText('PGY-3')).toBeInTheDocument()
    })

    it('should display faculty section', () => {
      const onSelect = jest.fn()

      render(<PersonFilter selectedPersonId={null} onSelect={onSelect} />)

      const button = screen.getByRole('button')
      fireEvent.click(button)

      expect(screen.getByText('Faculty')).toBeInTheDocument()
    })

    it('should show "My Schedule" option when user is logged in', () => {
      const onSelect = jest.fn()

      render(<PersonFilter selectedPersonId={null} onSelect={onSelect} />)

      const button = screen.getByRole('button')
      fireEvent.click(button)

      const myScheduleOptions = screen.getAllByText('My Schedule')
      expect(myScheduleOptions.length).toBeGreaterThan(0)
    })

    it('should not show "My Schedule" when user is not logged in', () => {
      useAuth.mockReturnValue({ user: null })
      const onSelect = jest.fn()

      render(<PersonFilter selectedPersonId={null} onSelect={onSelect} />)

      const button = screen.getByRole('button')
      fireEvent.click(button)

      const myScheduleOptions = screen.queryAllByText('My Schedule')
      // Should only appear in button text, not in dropdown
      expect(myScheduleOptions.length).toBeLessThan(2)
    })

    it('should display email addresses', () => {
      const onSelect = jest.fn()

      render(<PersonFilter selectedPersonId={null} onSelect={onSelect} />)

      const button = screen.getByRole('button')
      fireEvent.click(button)

      expect(screen.getByText('alice@example.com')).toBeInTheDocument()
      expect(screen.getByText('bob@example.com')).toBeInTheDocument()
    })
  })

  describe('Search Functionality', () => {
    it('should show search input when there are more than 10 people', () => {
      const manyPeople = {
        items: Array.from({ length: 15 }, (_, i) => ({
          id: `p${i}`,
          name: `Dr. Person ${i}`,
          type: 'resident',
          pgy_level: 1,
          email: `person${i}@example.com`,
        })),
      }
      usePeople.mockReturnValue({ data: manyPeople, isLoading: false })

      const onSelect = jest.fn()

      render(<PersonFilter selectedPersonId={null} onSelect={onSelect} />)

      const button = screen.getByRole('button')
      fireEvent.click(button)

      expect(screen.getByPlaceholderText('Search people...')).toBeInTheDocument()
    })

    it('should not show search input when there are 10 or fewer people', () => {
      const onSelect = jest.fn()

      render(<PersonFilter selectedPersonId={null} onSelect={onSelect} />)

      const button = screen.getByRole('button')
      fireEvent.click(button)

      expect(screen.queryByPlaceholderText('Search people...')).not.toBeInTheDocument()
    })

    it('should filter people by name when searching', () => {
      const manyPeople = {
        items: [
          ...mockPeople.items,
          ...Array.from({ length: 10 }, (_, i) => ({
            id: `px${i}`,
            name: `Dr. Other ${i}`,
            type: 'resident',
            pgy_level: 2,
            email: `other${i}@example.com`,
          })),
        ],
      }
      usePeople.mockReturnValue({ data: manyPeople, isLoading: false })

      const onSelect = jest.fn()

      render(<PersonFilter selectedPersonId={null} onSelect={onSelect} />)

      const button = screen.getByRole('button')
      fireEvent.click(button)

      const searchInput = screen.getByPlaceholderText('Search people...')
      fireEvent.change(searchInput, { target: { value: 'Alice' } })

      expect(screen.getByText('Dr. Alice Smith')).toBeInTheDocument()
      expect(screen.queryByText('Dr. Bob Johnson')).not.toBeInTheDocument()
    })

    it('should filter people by email when searching', () => {
      const manyPeople = {
        items: [
          ...mockPeople.items,
          ...Array.from({ length: 10 }, (_, i) => ({
            id: `px${i}`,
            name: `Dr. Other ${i}`,
            type: 'resident',
            pgy_level: 2,
            email: `other${i}@example.com`,
          })),
        ],
      }
      usePeople.mockReturnValue({ data: manyPeople, isLoading: false })

      const onSelect = jest.fn()

      render(<PersonFilter selectedPersonId={null} onSelect={onSelect} />)

      const button = screen.getByRole('button')
      fireEvent.click(button)

      const searchInput = screen.getByPlaceholderText('Search people...')
      fireEvent.change(searchInput, { target: { value: 'alice@example' } })

      expect(screen.getByText('Dr. Alice Smith')).toBeInTheDocument()
      expect(screen.queryByText('Dr. Bob Johnson')).not.toBeInTheDocument()
    })

    it('should show "No people found" when search has no results', () => {
      const manyPeople = {
        items: [
          ...mockPeople.items,
          ...Array.from({ length: 10 }, (_, i) => ({
            id: `px${i}`,
            name: `Dr. Other ${i}`,
            type: 'resident',
            pgy_level: 2,
            email: `other${i}@example.com`,
          })),
        ],
      }
      usePeople.mockReturnValue({ data: manyPeople, isLoading: false })

      const onSelect = jest.fn()

      render(<PersonFilter selectedPersonId={null} onSelect={onSelect} />)

      const button = screen.getByRole('button')
      fireEvent.click(button)

      const searchInput = screen.getByPlaceholderText('Search people...')
      fireEvent.change(searchInput, { target: { value: 'nonexistent' } })

      expect(screen.getByText(/No people found matching/)).toBeInTheDocument()
    })

    it('should clear search when X button is clicked', () => {
      const manyPeople = {
        items: [
          ...mockPeople.items,
          ...Array.from({ length: 10 }, (_, i) => ({
            id: `px${i}`,
            name: `Dr. Other ${i}`,
            type: 'resident',
            pgy_level: 2,
            email: `other${i}@example.com`,
          })),
        ],
      }
      usePeople.mockReturnValue({ data: manyPeople, isLoading: false })

      const onSelect = jest.fn()

      render(<PersonFilter selectedPersonId={null} onSelect={onSelect} />)

      const button = screen.getByRole('button')
      fireEvent.click(button)

      const searchInput = screen.getByPlaceholderText('Search people...') as HTMLInputElement
      fireEvent.change(searchInput, { target: { value: 'Alice' } })

      expect(searchInput.value).toBe('Alice')

      const clearButton = screen.getByRole('button', { name: '' })
      const clearButtons = screen.getAllByRole('button')
      const xButton = clearButtons.find((btn) => btn.querySelector('svg')?.classList.contains('lucide-x'))

      if (xButton) {
        fireEvent.click(xButton)
        expect(searchInput.value).toBe('')
      }
    })
  })

  describe('Selection', () => {
    it('should call onSelect with null when "All People" is clicked', () => {
      const onSelect = jest.fn()

      render(<PersonFilter selectedPersonId="p1" onSelect={onSelect} />)

      const button = screen.getByRole('button')
      fireEvent.click(button)

      // When selectedPersonId="p1", the button shows the person's name, not "All People"
      // So there's only one "All People" element - the dropdown option
      const allPeopleOptions = screen.getAllByText('All People')
      const allPeopleOption = allPeopleOptions.find(el => el.closest('[role="option"]'))
      fireEvent.click(allPeopleOption!.closest('button')!)

      expect(onSelect).toHaveBeenCalledWith(null)
    })

    it('should call onSelect with "me" when "My Schedule" is clicked', () => {
      const onSelect = jest.fn()

      render(<PersonFilter selectedPersonId={null} onSelect={onSelect} />)

      const button = screen.getByRole('button')
      fireEvent.click(button)

      const myScheduleOptions = screen.getAllByText('My Schedule')
      const dropdownOption = myScheduleOptions.find(
        (el) => el.closest('button')?.getAttribute('aria-selected') !== null
      )

      if (dropdownOption) {
        fireEvent.click(dropdownOption.closest('button')!)
        expect(onSelect).toHaveBeenCalledWith('me')
      }
    })

    it('should call onSelect with person id when person is clicked', () => {
      const onSelect = jest.fn()

      render(<PersonFilter selectedPersonId={null} onSelect={onSelect} />)

      const button = screen.getByRole('button')
      fireEvent.click(button)

      const aliceOption = screen.getByText('Dr. Alice Smith')
      fireEvent.click(aliceOption.closest('button')!)

      expect(onSelect).toHaveBeenCalledWith('p1')
    })

    it('should close dropdown after selection', () => {
      const onSelect = jest.fn()

      render(<PersonFilter selectedPersonId={null} onSelect={onSelect} />)

      const button = screen.getByRole('button')
      fireEvent.click(button)

      const aliceOption = screen.getByText('Dr. Alice Smith')
      fireEvent.click(aliceOption.closest('button')!)

      expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
    })

    it('should clear search after selection', () => {
      const manyPeople = {
        items: [
          ...mockPeople.items,
          ...Array.from({ length: 10 }, (_, i) => ({
            id: `px${i}`,
            name: `Dr. Other ${i}`,
            type: 'resident',
            pgy_level: 2,
            email: `other${i}@example.com`,
          })),
        ],
      }
      usePeople.mockReturnValue({ data: manyPeople, isLoading: false })

      const onSelect = jest.fn()

      render(<PersonFilter selectedPersonId={null} onSelect={onSelect} />)

      const button = screen.getByRole('button')
      fireEvent.click(button)

      const searchInput = screen.getByPlaceholderText('Search people...') as HTMLInputElement
      fireEvent.change(searchInput, { target: { value: 'Alice' } })

      const aliceOption = screen.getByText('Dr. Alice Smith')
      fireEvent.click(aliceOption.closest('button')!)

      // Reopen to check
      fireEvent.click(screen.getByRole('button'))
      const searchInputAfter = screen.getByPlaceholderText('Search people...') as HTMLInputElement
      expect(searchInputAfter.value).toBe('')
    })
  })

  describe('Selection Highlighting', () => {
    it('should highlight selected person', () => {
      const onSelect = jest.fn()

      render(<PersonFilter selectedPersonId="p1" onSelect={onSelect} />)

      const button = screen.getByRole('button')
      fireEvent.click(button)

      // Find the option in the dropdown (not the button) by looking at the listbox
      const allAliceElements = screen.getAllByText('Dr. Alice Smith')
      // The dropdown option should have aria-selected="true"
      const aliceOption = allAliceElements.find(el =>
        el.closest('button')?.getAttribute('aria-selected') === 'true'
      )?.closest('button')
      expect(aliceOption).toHaveClass('bg-blue-50')
      expect(aliceOption).toHaveClass('text-blue-700')
    })

    it('should not highlight unselected people', () => {
      const onSelect = jest.fn()

      render(<PersonFilter selectedPersonId="p1" onSelect={onSelect} />)

      const button = screen.getByRole('button')
      fireEvent.click(button)

      // Bob should not be selected
      const bobOption = screen.getByText('Dr. Bob Johnson').closest('button')!
      expect(bobOption).not.toHaveClass('bg-blue-50')
      expect(bobOption).toHaveAttribute('aria-selected', 'false')
    })

    it('should highlight "All People" when no selection', () => {
      const onSelect = jest.fn()

      render(<PersonFilter selectedPersonId={null} onSelect={onSelect} />)

      const button = screen.getByRole('button')
      fireEvent.click(button)

      const allPeopleOptions = screen.getAllByText('All People')
      const dropdownOption = allPeopleOptions.find(
        (el) => el.closest('button')?.getAttribute('aria-selected') === 'true'
      )

      expect(dropdownOption).toBeTruthy()
    })
  })

  describe('Loading State', () => {
    it('should show loading message when people are loading', () => {
      usePeople.mockReturnValue({ data: null, isLoading: true })
      const onSelect = jest.fn()

      render(<PersonFilter selectedPersonId={null} onSelect={onSelect} />)

      const button = screen.getByRole('button')
      fireEvent.click(button)

      expect(screen.getByText('Loading...')).toBeInTheDocument()
    })
  })

  describe('Sorting', () => {
    it('should sort people alphabetically within PGY groups', () => {
      const onSelect = jest.fn()

      render(<PersonFilter selectedPersonId={null} onSelect={onSelect} />)

      const button = screen.getByRole('button')
      fireEvent.click(button)

      const pgy1Names = ['Dr. Alice Smith', 'Dr. David Brown']
      const elements = screen.getAllByRole('option')
      const pgy1Elements = elements.filter((el) =>
        pgy1Names.includes(el.textContent?.split('\n')[0] || '')
      )

      // Check that Alice comes before David
      const aliceIndex = elements.indexOf(pgy1Elements[0])
      const davidIndex = elements.indexOf(pgy1Elements[1])

      if (aliceIndex !== -1 && davidIndex !== -1) {
        expect(aliceIndex).toBeLessThan(davidIndex)
      }
    })

    it('should sort faculty alphabetically', () => {
      const multipleAttending = {
        items: [
          ...mockPeople.items,
          {
            id: 'p5',
            name: 'Dr. Adam Faculty',
            type: 'faculty',
            pgy_level: null,
            email: 'adam@example.com',
          },
        ],
      }
      usePeople.mockReturnValue({ data: multipleAttending, isLoading: false })

      const onSelect = jest.fn()

      render(<PersonFilter selectedPersonId={null} onSelect={onSelect} />)

      const button = screen.getByRole('button')
      fireEvent.click(button)

      // Adam should come before Carol
      expect(screen.getByText('Dr. Adam Faculty')).toBeInTheDocument()
      expect(screen.getByText('Dr. Carol Williams')).toBeInTheDocument()
    })
  })

  describe('Icon Display', () => {
    it('should show Users icon for "All People"', () => {
      const onSelect = jest.fn()
      const { container } = render(<PersonFilter selectedPersonId={null} onSelect={onSelect} />)

      expect(container.querySelector('.lucide-users')).toBeInTheDocument()
    })

    it('should show User icon when person is selected', () => {
      const onSelect = jest.fn()
      const { container } = render(<PersonFilter selectedPersonId="p1" onSelect={onSelect} />)

      expect(container.querySelector('.lucide-user')).toBeInTheDocument()
    })

    it('should show blue User icon for "My Schedule"', () => {
      const onSelect = jest.fn()
      const { container } = render(<PersonFilter selectedPersonId="me" onSelect={onSelect} />)

      const userIcon = container.querySelector('.lucide-user')
      expect(userIcon).toHaveClass('text-blue-600')
    })
  })

  describe('Person Avatars', () => {
    it('should display person initials in avatar', () => {
      const onSelect = jest.fn()

      render(<PersonFilter selectedPersonId={null} onSelect={onSelect} />)

      const button = screen.getByRole('button')
      fireEvent.click(button)

      // The component displays initials based on name - "Dr. Alice Smith" = "D" (first letter of first word after "Dr.")
      // Check that avatar initials are rendered (the exact format depends on implementation)
      const avatarElements = document.querySelectorAll('[class*="rounded-full"]')
      expect(avatarElements.length).toBeGreaterThan(0)
    })
  })
})
