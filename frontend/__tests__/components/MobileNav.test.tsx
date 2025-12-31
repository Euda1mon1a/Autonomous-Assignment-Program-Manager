import { render, screen } from '@/test-utils'
import userEvent from '@testing-library/user-event'
import { MobileNav } from '@/components/MobileNav'
import { useAuth } from '@/hooks/useAuth'

jest.mock('@/hooks/useAuth')

describe('MobileNav', () => {
  const mockUser = {
    id: '123',
    username: 'testuser',
    role: 'resident',
  }

  beforeEach(() => {
    ;(useAuth as jest.Mock).mockReturnValue({
      user: mockUser,
      isAuthenticated: true,
    })
  })

  describe('Menu Toggle', () => {
    it('should render hamburger menu button', () => {
      render(<MobileNav />)
      expect(screen.getByRole('button', { name: /menu/i })).toBeInTheDocument()
    })

    it('should open menu on button click', async () => {
      render(<MobileNav />)
      const button = screen.getByRole('button', { name: /menu/i })
      await userEvent.click(button)
      expect(screen.getByRole('navigation')).toBeInTheDocument()
    })

    it('should close menu when clicking close button', async () => {
      render(<MobileNav />)
      await userEvent.click(screen.getByRole('button', { name: /menu/i }))
      const closeButton = screen.getByRole('button', { name: /close/i })
      await userEvent.click(closeButton)
      expect(screen.queryByRole('navigation')).not.toBeInTheDocument()
    })
  })

  describe('Navigation Links', () => {
    it('should display dashboard link', async () => {
      render(<MobileNav />)
      await userEvent.click(screen.getByRole('button', { name: /menu/i }))
      expect(screen.getByText(/dashboard/i)).toBeInTheDocument()
    })

    it('should display schedule link', async () => {
      render(<MobileNav />)
      await userEvent.click(screen.getByRole('button', { name: /menu/i }))
      expect(screen.getByText(/schedule/i)).toBeInTheDocument()
    })

    it('should close menu when link is clicked', async () => {
      render(<MobileNav />)
      await userEvent.click(screen.getByRole('button', { name: /menu/i }))
      await userEvent.click(screen.getByText(/dashboard/i))
      expect(screen.queryByRole('navigation')).not.toBeInTheDocument()
    })
  })

  describe('Role-Based Navigation', () => {
    it('should show admin links for admin users', async () => {
      ;(useAuth as jest.Mock).mockReturnValue({
        user: { ...mockUser, role: 'admin' },
        isAuthenticated: true,
      })
      render(<MobileNav />)
      await userEvent.click(screen.getByRole('button', { name: /menu/i }))
      expect(screen.getByText(/admin/i)).toBeInTheDocument()
    })

    it('should not show admin links for residents', async () => {
      render(<MobileNav />)
      await userEvent.click(screen.getByRole('button', { name: /menu/i }))
      expect(screen.queryByText(/admin/i)).not.toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('should have proper aria labels', () => {
      render(<MobileNav />)
      const button = screen.getByRole('button', { name: /menu/i })
      expect(button).toHaveAttribute('aria-label')
    })

    it('should support keyboard navigation', async () => {
      render(<MobileNav />)
      const button = screen.getByRole('button', { name: /menu/i })
      button.focus()
      expect(button).toHaveFocus()
    })
  })
})
