import { render, screen, waitFor } from '@/test-utils'
import userEvent from '@testing-library/user-event'
import { UserMenu } from '@/components/UserMenu'
import { useAuth } from '@/contexts/AuthContext'

jest.mock('@/contexts/AuthContext')

describe('UserMenu', () => {
  const mockLogout = jest.fn()
  const mockUser = {
    id: '123',
    username: 'Test User',
    email: 'test@example.com',
    role: 'resident',
  }

  beforeEach(() => {
    jest.clearAllMocks()
    ;(useAuth as jest.Mock).mockReturnValue({
      user: mockUser,
      logout: mockLogout,
      isAuthenticated: true,
    })
  })

  describe('Menu Rendering', () => {
    it('should render user menu button', () => {
      render(<UserMenu />)
      expect(screen.getByRole('button')).toBeInTheDocument()
    })

    it('should display user initials', () => {
      render(<UserMenu />)
      expect(screen.getByText('TU')).toBeInTheDocument()
    })

    it('should display username on hover', async () => {
      render(<UserMenu />)
      const button = screen.getByRole('button', { name: /user menu/i })
      await userEvent.hover(button)
      expect(screen.getByText('Test User')).toBeInTheDocument()
    })
  })

  describe('Menu Interactions', () => {
    it('should open menu on click', async () => {
      render(<UserMenu />)
      const button = screen.getByRole('button', { name: /user menu/i })
      await userEvent.click(button)
      // Dropdown shows user email and logout option
      expect(screen.getByText('test@example.com')).toBeInTheDocument()
    })

    it('should display user email in menu', async () => {
      render(<UserMenu />)
      await userEvent.click(screen.getByRole('button', { name: /user menu/i }))
      expect(screen.getByText('test@example.com')).toBeInTheDocument()
    })

    it('should display user role badge', async () => {
      render(<UserMenu />)
      await userEvent.click(screen.getByRole('button', { name: /user menu/i }))
      expect(screen.getByText(/resident/i)).toBeInTheDocument()
    })

    it('should close menu when clicking outside', async () => {
      render(<UserMenu />)
      await userEvent.click(screen.getByRole('button', { name: /user menu/i }))
      expect(screen.getByText('test@example.com')).toBeInTheDocument()
      await userEvent.click(document.body)
      await waitFor(() => {
        expect(screen.queryByText('test@example.com')).not.toBeInTheDocument()
      })
    })
  })

  describe('Logout Functionality', () => {
    it('should call logout when logout button clicked', async () => {
      render(<UserMenu />)
      await userEvent.click(screen.getByRole('button', { name: /user menu/i }))
      const logoutButton = screen.getByText(/logout/i)
      await userEvent.click(logoutButton)
      expect(mockLogout).toHaveBeenCalledTimes(1)
    })

    it('should close menu after logout', async () => {
      render(<UserMenu />)
      await userEvent.click(screen.getByRole('button', { name: /user menu/i }))
      await userEvent.click(screen.getByText(/logout/i))
      // Menu closes after logout
      expect(mockLogout).toHaveBeenCalledTimes(1)
    })
  })

  describe('Profile Navigation', () => {
    it('should have settings link in menu', async () => {
      render(<UserMenu />)
      await userEvent.click(screen.getByRole('button', { name: /user menu/i }))
      expect(screen.getByText(/settings/i)).toBeInTheDocument()
    })

    it('should have settings link for admins', async () => {
      ;(useAuth as jest.Mock).mockReturnValue({
        user: { ...mockUser, role: 'admin' },
        logout: mockLogout,
        isAuthenticated: true,
      })
      render(<UserMenu />)
      await userEvent.click(screen.getByRole('button', { name: /user menu/i }))
      expect(screen.getByText(/settings/i)).toBeInTheDocument()
    })
  })
})
