import { render, screen } from '@/test-utils'
import userEvent from '@testing-library/user-event'
import { EmptyState } from '@/components/EmptyState'

describe('EmptyState', () => {
  describe('Basic Rendering', () => {
    it('should render title and description', () => {
      render(
        <EmptyState
          title="No data found"
          description="Try adjusting your filters"
        />
      )
      expect(screen.getByText('No data found')).toBeInTheDocument()
      expect(screen.getByText('Try adjusting your filters')).toBeInTheDocument()
    })

    it('should render without description', () => {
      render(<EmptyState title="No results" />)
      expect(screen.getByText('No results')).toBeInTheDocument()
    })

    it('should render default icon', () => {
      const { container } = render(<EmptyState title="Empty" />)
      const icon = container.querySelector('svg')
      expect(icon).toBeInTheDocument()
    })
  })

  describe('Custom Icon', () => {
    it('should render custom icon', () => {
      const CustomIcon = () => <div data-testid="custom-icon">Custom</div>
      render(<EmptyState title="Empty" icon={CustomIcon} />)
      expect(screen.getByTestId('custom-icon')).toBeInTheDocument()
    })
  })

  describe('Action Button', () => {
    it('should render action button when provided', () => {
      const handleClick = jest.fn()
      render(
        <EmptyState
          title="No items"
          action={{ label: "Add Item", onClick: handleClick }}
        />
      )
      expect(screen.getByRole('button', { name: /add item/i })).toBeInTheDocument()
    })

    it('should call onClick when button clicked', async () => {
      const handleClick = jest.fn()
      render(
        <EmptyState
          title="No items"
          action={{ label: "Add Item", onClick: handleClick }}
        />
      )
      await userEvent.click(screen.getByRole('button', { name: /add item/i }))
      expect(handleClick).toHaveBeenCalledTimes(1)
    })

    it('should not render button without action', () => {
      render(<EmptyState title="Empty" />)
      expect(screen.queryByRole('button')).not.toBeInTheDocument()
    })
  })

  describe('Children Support', () => {
    it('should render children when provided', () => {
      render(
        <EmptyState title="Empty">
          <div data-testid="custom-child">Custom content</div>
        </EmptyState>
      )
      expect(screen.getByTestId('custom-child')).toBeInTheDocument()
    })
  })
})
