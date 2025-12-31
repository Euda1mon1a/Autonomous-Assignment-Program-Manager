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
      render(<EmptyState title="Empty" icon={<CustomIcon />} />)
      expect(screen.getByTestId('custom-icon')).toBeInTheDocument()
    })
  })

  describe('Action Button', () => {
    it('should render action button when provided', () => {
      const handleClick = jest.fn()
      render(
        <EmptyState
          title="No items"
          actionLabel="Add Item"
          onAction={handleClick}
        />
      )
      expect(screen.getByRole('button', { name: /add item/i })).toBeInTheDocument()
    })

    it('should call onAction when button clicked', async () => {
      const handleClick = jest.fn()
      render(
        <EmptyState
          title="No items"
          actionLabel="Add Item"
          onAction={handleClick}
        />
      )
      await userEvent.click(screen.getByRole('button', { name: /add item/i }))
      expect(handleClick).toHaveBeenCalledTimes(1)
    })

    it('should not render button without action handler', () => {
      render(<EmptyState title="Empty" actionLabel="Click" />)
      expect(screen.queryByRole('button')).not.toBeInTheDocument()
    })
  })

  describe('Styling Variants', () => {
    it('should apply custom className', () => {
      const { container } = render(
        <EmptyState title="Empty" className="custom-class" />
      )
      expect(container.firstChild).toHaveClass('custom-class')
    })

    it('should render compact variant', () => {
      const { container } = render(<EmptyState title="Empty" variant="compact" />)
      expect(container.firstChild).toHaveClass('compact')
    })
  })
})
