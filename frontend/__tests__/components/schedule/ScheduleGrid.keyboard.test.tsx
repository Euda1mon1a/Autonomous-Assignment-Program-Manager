/**
 * ScheduleGrid Keyboard Navigation Tests
 *
 * Tests WAI-ARIA grid pattern keyboard navigation integration:
 * - Arrow keys move focus between cells
 * - Home/End move to first/last column in row
 * - Enter/Space activate focused cell
 * - Roving tabIndex (only focused cell is tabbable)
 * - data-row/data-col attributes for cell identification
 * - aria-selected reflects focused state
 */
import { renderWithProviders, screen, waitFor, mockData } from '@/test-utils'
import { fireEvent } from '@testing-library/react'
import { ScheduleGrid } from '@/components/schedule/ScheduleGrid'
import * as api from '@/lib/api'
import * as hooks from '@/lib/hooks'

// Mock the API and hooks
jest.mock('@/lib/api')
jest.mock('@/lib/hooks')

// Mock framer-motion to avoid animation issues in tests
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
}))

const mockGet = api.get as jest.MockedFunction<typeof api.get>
const mockUsePeople = hooks.usePeople as jest.MockedFunction<typeof hooks.usePeople>
const mockUseRotationTemplates = hooks.useRotationTemplates as jest.MockedFunction<typeof hooks.useRotationTemplates>

describe('ScheduleGrid Keyboard Navigation', () => {
  // Two people: PGY-1 and PGY-2, creating 2 rows
  // Two days: Jan 1-2, each with AM/PM = 4 columns total
  const mockPeople = mockData.paginatedResponse([
    mockData.person({
      id: 'person-1',
      name: 'Dr. Alice Smith',
      type: 'resident',
      pgyLevel: 1,
      email: 'alice@test.com',
      role: 'RESIDENT',
    }),
    mockData.person({
      id: 'person-2',
      name: 'Dr. Bob Jones',
      type: 'resident',
      pgyLevel: 2,
      email: 'bob@test.com',
      role: 'RESIDENT',
    }),
  ])

  const mockTemplates = mockData.paginatedResponse([
    mockData.rotationTemplate({
      id: 'template-1',
      name: 'Inpatient Medicine',
      abbreviation: 'IM',
      activityType: 'inpatient',
    }),
  ])

  const mockBlocks = mockData.paginatedResponse([
    mockData.block({ id: 'block-1', date: '2025-01-01', timeOfDay: 'AM' }),
    mockData.block({ id: 'block-2', date: '2025-01-01', timeOfDay: 'PM' }),
    mockData.block({ id: 'block-3', date: '2025-01-02', timeOfDay: 'AM' }),
    mockData.block({ id: 'block-4', date: '2025-01-02', timeOfDay: 'PM' }),
  ])

  const mockAssignments = mockData.paginatedResponse([
    mockData.assignment({
      id: 'assignment-1',
      personId: 'person-1',
      blockId: 'block-1',
      rotationTemplateId: 'template-1',
      role: 'primary',
    }),
  ])

  const startDate = new Date('2025-01-01')
  const endDate = new Date('2025-01-02')

  beforeEach(() => {
    mockUsePeople.mockReturnValue({
      data: mockPeople,
      isLoading: false,
      error: null,
    } as any)

    mockUseRotationTemplates.mockReturnValue({
      data: mockTemplates,
      isLoading: false,
      error: null,
    } as any)

    mockGet.mockImplementation((url: string) => {
      if (url.includes('/blocks')) {
        return Promise.resolve(mockBlocks)
      }
      if (url.includes('/assignments')) {
        return Promise.resolve(mockAssignments)
      }
      return Promise.resolve({ items: [], total: 0, page: 1, per_page: 100 })
    })
  })

  afterEach(() => {
    jest.clearAllMocks()
  })

  async function renderAndWaitForGrid() {
    renderWithProviders(<ScheduleGrid startDate={startDate} endDate={endDate} />)
    await waitFor(() => {
      expect(screen.getByRole('grid')).toBeInTheDocument()
    })
    return screen.getByRole('grid')
  }

  function getGridCells(): HTMLElement[] {
    return screen.getAllByRole('gridcell')
  }

  function getCellAt(row: number, col: number): HTMLElement | null {
    return document.querySelector(`[data-row="${row}"][data-col="${col}"]`)
  }

  describe('ARIA grid role and attributes', () => {
    it('renders the table with role="grid"', async () => {
      const grid = await renderAndWaitForGrid()
      expect(grid.tagName).toBe('TABLE')
      expect(grid).toHaveAttribute('role', 'grid')
    })

    it('renders cells with role="gridcell"', async () => {
      await renderAndWaitForGrid()
      const cells = getGridCells()
      expect(cells.length).toBeGreaterThan(0)
      cells.forEach((cell) => {
        expect(cell).toHaveAttribute('role', 'gridcell')
      })
    })

    it('renders cells with data-row and data-col attributes', async () => {
      await renderAndWaitForGrid()

      // First person (row 0), first day AM (col 0)
      const cell00 = getCellAt(0, 0)
      expect(cell00).toBeInTheDocument()
      expect(cell00).toHaveAttribute('data-row', '0')
      expect(cell00).toHaveAttribute('data-col', '0')

      // First person (row 0), first day PM (col 1)
      const cell01 = getCellAt(0, 1)
      expect(cell01).toBeInTheDocument()
      expect(cell01).toHaveAttribute('data-col', '1')

      // Second person (row 1), second day PM (col 3)
      const cell13 = getCellAt(1, 3)
      expect(cell13).toBeInTheDocument()
      expect(cell13).toHaveAttribute('data-row', '1')
      expect(cell13).toHaveAttribute('data-col', '3')
    })

    it('has correct grid dimensions (2 people x 4 columns)', async () => {
      await renderAndWaitForGrid()

      // 2 people (rows) x 2 days x 2 time slots (AM/PM) = 8 grid cells with data attributes
      // Verify last cell exists
      const lastCell = getCellAt(1, 3)
      expect(lastCell).toBeInTheDocument()

      // Verify out-of-bounds cells don't exist
      const outOfBoundsRow = getCellAt(2, 0)
      expect(outOfBoundsRow).not.toBeInTheDocument()

      const outOfBoundsCol = getCellAt(0, 4)
      expect(outOfBoundsCol).not.toBeInTheDocument()
    })
  })

  describe('roving tabIndex', () => {
    it('first cell (0,0) has tabIndex=0 initially', async () => {
      await renderAndWaitForGrid()

      const firstCell = getCellAt(0, 0)
      expect(firstCell).toHaveAttribute('tabindex', '0')
    })

    it('non-first cells have tabIndex=-1 initially', async () => {
      await renderAndWaitForGrid()

      const cell01 = getCellAt(0, 1)
      expect(cell01).toHaveAttribute('tabindex', '-1')

      const cell10 = getCellAt(1, 0)
      expect(cell10).toHaveAttribute('tabindex', '-1')

      const cell13 = getCellAt(1, 3)
      expect(cell13).toHaveAttribute('tabindex', '-1')
    })

    it('updates tabIndex when a cell receives focus', async () => {
      await renderAndWaitForGrid()

      const cell12 = getCellAt(1, 2)!
      fireEvent.focus(cell12)

      await waitFor(() => {
        // Focused cell should have tabIndex=0
        expect(cell12).toHaveAttribute('tabindex', '0')
      })

      // Previously focused first cell should now have tabIndex=-1
      const cell00 = getCellAt(0, 0)
      expect(cell00).toHaveAttribute('tabindex', '-1')
    })
  })

  describe('arrow key navigation', () => {
    it('ArrowRight moves focus to the next column', async () => {
      const grid = await renderAndWaitForGrid()

      // Focus the first cell
      const cell00 = getCellAt(0, 0)!
      fireEvent.focus(cell00)

      // Press ArrowRight on the grid
      fireEvent.keyDown(grid, { key: 'ArrowRight' })

      await waitFor(() => {
        const cell01 = getCellAt(0, 1)
        expect(cell01).toHaveAttribute('tabindex', '0')
        expect(cell01).toHaveAttribute('aria-selected', 'true')
      })
    })

    it('ArrowLeft moves focus to the previous column', async () => {
      const grid = await renderAndWaitForGrid()

      // Focus a cell that's not in the first column
      const cell02 = getCellAt(0, 2)!
      fireEvent.focus(cell02)

      fireEvent.keyDown(grid, { key: 'ArrowLeft' })

      await waitFor(() => {
        const cell01 = getCellAt(0, 1)
        expect(cell01).toHaveAttribute('tabindex', '0')
        expect(cell01).toHaveAttribute('aria-selected', 'true')
      })
    })

    it('ArrowDown moves focus to the next row', async () => {
      const grid = await renderAndWaitForGrid()

      // Focus first cell
      const cell00 = getCellAt(0, 0)!
      fireEvent.focus(cell00)

      fireEvent.keyDown(grid, { key: 'ArrowDown' })

      await waitFor(() => {
        const cell10 = getCellAt(1, 0)
        expect(cell10).toHaveAttribute('tabindex', '0')
        expect(cell10).toHaveAttribute('aria-selected', 'true')
      })
    })

    it('ArrowUp moves focus to the previous row', async () => {
      const grid = await renderAndWaitForGrid()

      // Focus a cell in the second row
      const cell10 = getCellAt(1, 0)!
      fireEvent.focus(cell10)

      fireEvent.keyDown(grid, { key: 'ArrowUp' })

      await waitFor(() => {
        const cell00 = getCellAt(0, 0)
        expect(cell00).toHaveAttribute('tabindex', '0')
        expect(cell00).toHaveAttribute('aria-selected', 'true')
      })
    })

    it('does not move past the last column (boundary)', async () => {
      const grid = await renderAndWaitForGrid()

      // Focus the last column in the first row
      const cell03 = getCellAt(0, 3)!
      fireEvent.focus(cell03)

      fireEvent.keyDown(grid, { key: 'ArrowRight' })

      await waitFor(() => {
        // Should stay on the same cell
        expect(cell03).toHaveAttribute('tabindex', '0')
        expect(cell03).toHaveAttribute('aria-selected', 'true')
      })
    })

    it('does not move past the first column (boundary)', async () => {
      const grid = await renderAndWaitForGrid()

      const cell00 = getCellAt(0, 0)!
      fireEvent.focus(cell00)

      fireEvent.keyDown(grid, { key: 'ArrowLeft' })

      await waitFor(() => {
        expect(cell00).toHaveAttribute('tabindex', '0')
        expect(cell00).toHaveAttribute('aria-selected', 'true')
      })
    })

    it('does not move past the last row (boundary)', async () => {
      const grid = await renderAndWaitForGrid()

      const cell10 = getCellAt(1, 0)!
      fireEvent.focus(cell10)

      fireEvent.keyDown(grid, { key: 'ArrowDown' })

      await waitFor(() => {
        expect(cell10).toHaveAttribute('tabindex', '0')
        expect(cell10).toHaveAttribute('aria-selected', 'true')
      })
    })

    it('does not move past the first row (boundary)', async () => {
      const grid = await renderAndWaitForGrid()

      const cell00 = getCellAt(0, 0)!
      fireEvent.focus(cell00)

      fireEvent.keyDown(grid, { key: 'ArrowUp' })

      await waitFor(() => {
        expect(cell00).toHaveAttribute('tabindex', '0')
        expect(cell00).toHaveAttribute('aria-selected', 'true')
      })
    })

    it('navigates across multiple cells sequentially', async () => {
      const grid = await renderAndWaitForGrid()

      // Start at (0,0)
      const cell00 = getCellAt(0, 0)!
      fireEvent.focus(cell00)

      // Move right twice: (0,0) -> (0,1) -> (0,2)
      fireEvent.keyDown(grid, { key: 'ArrowRight' })
      fireEvent.keyDown(grid, { key: 'ArrowRight' })

      await waitFor(() => {
        const cell02 = getCellAt(0, 2)
        expect(cell02).toHaveAttribute('tabindex', '0')
      })

      // Move down: (0,2) -> (1,2)
      fireEvent.keyDown(grid, { key: 'ArrowDown' })

      await waitFor(() => {
        const cell12 = getCellAt(1, 2)
        expect(cell12).toHaveAttribute('tabindex', '0')
      })

      // Move left: (1,2) -> (1,1)
      fireEvent.keyDown(grid, { key: 'ArrowLeft' })

      await waitFor(() => {
        const cell11 = getCellAt(1, 1)
        expect(cell11).toHaveAttribute('tabindex', '0')
      })
    })
  })

  describe('Home and End keys', () => {
    it('Home key moves focus to first column in the current row', async () => {
      const grid = await renderAndWaitForGrid()

      // Focus a cell in the middle
      const cell13 = getCellAt(1, 3)!
      fireEvent.focus(cell13)

      fireEvent.keyDown(grid, { key: 'Home' })

      await waitFor(() => {
        const cell10 = getCellAt(1, 0)
        expect(cell10).toHaveAttribute('tabindex', '0')
        expect(cell10).toHaveAttribute('aria-selected', 'true')
      })
    })

    it('End key moves focus to last column in the current row', async () => {
      const grid = await renderAndWaitForGrid()

      const cell10 = getCellAt(1, 0)!
      fireEvent.focus(cell10)

      fireEvent.keyDown(grid, { key: 'End' })

      await waitFor(() => {
        const cell13 = getCellAt(1, 3)
        expect(cell13).toHaveAttribute('tabindex', '0')
        expect(cell13).toHaveAttribute('aria-selected', 'true')
      })
    })
  })

  describe('Enter and Space activation', () => {
    it('Enter key on a focused cell triggers activation (no crash)', async () => {
      const grid = await renderAndWaitForGrid()

      const cell00 = getCellAt(0, 0)!
      fireEvent.focus(cell00)

      // Should not throw
      expect(() => {
        fireEvent.keyDown(grid, { key: 'Enter' })
      }).not.toThrow()

      // Cell should still be focused
      await waitFor(() => {
        expect(cell00).toHaveAttribute('aria-selected', 'true')
      })
    })

    it('Space key on a focused cell triggers activation (no crash)', async () => {
      const grid = await renderAndWaitForGrid()

      const cell11 = getCellAt(1, 1)!
      fireEvent.focus(cell11)

      expect(() => {
        fireEvent.keyDown(grid, { key: ' ' })
      }).not.toThrow()

      await waitFor(() => {
        expect(cell11).toHaveAttribute('aria-selected', 'true')
      })
    })
  })

  describe('cell click interaction', () => {
    it('clicking a cell focuses it and updates aria-selected', async () => {
      await renderAndWaitForGrid()

      const cell12 = getCellAt(1, 2)!
      fireEvent.click(cell12)

      await waitFor(() => {
        expect(cell12).toHaveAttribute('aria-selected', 'true')
        expect(cell12).toHaveAttribute('tabindex', '0')
      })

      // Other cells should not be selected
      const cell00 = getCellAt(0, 0)
      expect(cell00).toHaveAttribute('aria-selected', 'false')
      expect(cell00).toHaveAttribute('tabindex', '-1')
    })
  })

  describe('aria-selected state', () => {
    it('only the focused cell has aria-selected=true', async () => {
      const grid = await renderAndWaitForGrid()

      const cell00 = getCellAt(0, 0)!
      fireEvent.focus(cell00)

      await waitFor(() => {
        expect(cell00).toHaveAttribute('aria-selected', 'true')
      })

      // All other cells should be aria-selected=false
      const cell01 = getCellAt(0, 1)
      expect(cell01).toHaveAttribute('aria-selected', 'false')

      const cell10 = getCellAt(1, 0)
      expect(cell10).toHaveAttribute('aria-selected', 'false')

      const cell13 = getCellAt(1, 3)
      expect(cell13).toHaveAttribute('aria-selected', 'false')
    })

    it('aria-selected moves with keyboard navigation', async () => {
      const grid = await renderAndWaitForGrid()

      const cell00 = getCellAt(0, 0)!
      fireEvent.focus(cell00)

      fireEvent.keyDown(grid, { key: 'ArrowRight' })

      await waitFor(() => {
        const cell01 = getCellAt(0, 1)
        expect(cell01).toHaveAttribute('aria-selected', 'true')
        expect(cell00).toHaveAttribute('aria-selected', 'false')
      })
    })
  })

  describe('unrecognized keys', () => {
    it('ignores non-navigation keys without changing focus', async () => {
      const grid = await renderAndWaitForGrid()

      const cell00 = getCellAt(0, 0)!
      fireEvent.focus(cell00)

      fireEvent.keyDown(grid, { key: 'a' })
      fireEvent.keyDown(grid, { key: 'Escape' })
      fireEvent.keyDown(grid, { key: 'Tab' })

      // Focus should remain on cell00
      await waitFor(() => {
        expect(cell00).toHaveAttribute('tabindex', '0')
        expect(cell00).toHaveAttribute('aria-selected', 'true')
      })
    })
  })

  describe('grid with person filter', () => {
    it('renders correct number of rows when person filter is applied', async () => {
      // Only show person-1 (1 row, 4 columns)
      const personFilter = new Set(['person-1'])

      renderWithProviders(
        <ScheduleGrid startDate={startDate} endDate={endDate} personFilter={personFilter} />
      )

      await waitFor(() => {
        expect(screen.getByRole('grid')).toBeInTheDocument()
      })

      // Only person-1 row should exist (row 0)
      const cell00 = getCellAt(0, 0)
      expect(cell00).toBeInTheDocument()

      // Row 1 should not exist (person-2 is filtered out)
      const cell10 = getCellAt(1, 0)
      expect(cell10).not.toBeInTheDocument()
    })

    it('ArrowDown does not move past last row in filtered grid', async () => {
      const personFilter = new Set(['person-1'])

      renderWithProviders(
        <ScheduleGrid startDate={startDate} endDate={endDate} personFilter={personFilter} />
      )

      await waitFor(() => {
        expect(screen.getByRole('grid')).toBeInTheDocument()
      })

      const grid = screen.getByRole('grid')
      const cell00 = getCellAt(0, 0)!
      fireEvent.focus(cell00)

      await waitFor(() => {
        expect(cell00).toHaveAttribute('aria-selected', 'true')
      })

      // ArrowDown should not move (only 1 row)
      fireEvent.keyDown(grid, { key: 'ArrowDown' })

      // Cell (0,0) should still be focused
      await waitFor(() => {
        expect(cell00).toHaveAttribute('aria-selected', 'true')
        expect(cell00).toHaveAttribute('tabindex', '0')
      })
    })
  })

  describe('grid accessibility label', () => {
    it('grid has descriptive aria-label', async () => {
      const grid = await renderAndWaitForGrid()
      expect(grid).toHaveAttribute('aria-label', 'Schedule grid showing assignments by person and date')
    })
  })
})
