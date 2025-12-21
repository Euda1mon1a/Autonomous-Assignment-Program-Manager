import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { DatePicker } from '@/components/forms/DatePicker'
import { createRef } from 'react'

describe('DatePicker', () => {
  const mockOnChange = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Basic Rendering', () => {
    it('should render label', () => {
      render(<DatePicker label="Start Date" />)

      expect(screen.getByText('Start Date')).toBeInTheDocument()
    })

    it('should render date input', () => {
      const { container } = render(<DatePicker label="Start Date" />)

      const input = container.querySelector('input[type="date"]')
      expect(input).toBeInTheDocument()
      expect(input).toHaveAttribute('type', 'date')
    })

    it('should apply custom className', () => {
      const { container } = render(<DatePicker label="Start Date" className="custom-class" />)

      const input = container.querySelector('input[type="date"]')
      expect(input).toHaveClass('custom-class')
    })

    it('should have default styling classes', () => {
      const { container } = render(<DatePicker label="Start Date" />)

      const input = container.querySelector('input[type="date"]')
      expect(input).toHaveClass('w-full')
      expect(input).toHaveClass('px-3')
      expect(input).toHaveClass('py-2')
      expect(input).toHaveClass('border')
      expect(input).toHaveClass('rounded-md')
    })
  })

  describe('Value Handling', () => {
    it('should display provided value', () => {
      const { container } = render(<DatePicker label="Start Date" value="2024-02-15" />)

      const input = container.querySelector('input[type="date"]') as HTMLInputElement
      expect(input.value).toBe('2024-02-15')
    })

    it('should handle empty value', () => {
      const { container } = render(<DatePicker label="Start Date" value="" />)

      const input = container.querySelector('input[type="date"]') as HTMLInputElement
      expect(input.value).toBe('')
    })

    it('should call onChange when value changes', async () => {
      const user = userEvent.setup()
      const { container } = render(<DatePicker label="Start Date" onChange={mockOnChange} />)

      const input = container.querySelector('input[type="date"]')!
      await user.type(input, '2024-02-15')

      expect(mockOnChange).toHaveBeenCalled()
    })

    it('should pass new value to onChange handler', async () => {
      const user = userEvent.setup()
      const { container } = render(<DatePicker label="Start Date" onChange={mockOnChange} />)

      const input = container.querySelector('input[type="date"]')!
      await user.clear(input)
      await user.type(input, '2024-02-15')

      // onChange is called for each character typed
      expect(mockOnChange).toHaveBeenCalled()
      const lastCall = mockOnChange.mock.calls[mockOnChange.mock.calls.length - 1]
      expect(lastCall[0]).toBe('2024-02-15')
    })

    it('should work without onChange handler', async () => {
      const user = userEvent.setup()
      const { container } = render(<DatePicker label="Start Date" />)

      const input = container.querySelector('input[type="date"]')!

      // Should not throw error
      await expect(user.type(input, '2024-02-15')).resolves.not.toThrow()
    })
  })

  describe('Error Handling', () => {
    it('should display error message when error prop is provided', () => {
      render(<DatePicker label="Start Date" error="This field is required" />)

      expect(screen.getByText('This field is required')).toBeInTheDocument()
    })

    it('should apply error styling to input when error exists', () => {
      const { container } = render(<DatePicker label="Start Date" error="Invalid date" />)

      const input = container.querySelector('input[type="date"]')
      expect(input).toHaveClass('border-red-500')
    })

    it('should apply normal styling when no error', () => {
      const { container } = render(<DatePicker label="Start Date" />)

      const input = container.querySelector('input[type="date"]')
      expect(input).toHaveClass('border-gray-300')
      expect(input).not.toHaveClass('border-red-500')
    })

    it('should display error text in red', () => {
      const { container } = render(
        <DatePicker label="Start Date" error="Invalid date" />
      )

      const errorText = container.querySelector('.text-red-600')
      expect(errorText).toBeInTheDocument()
      expect(errorText).toHaveTextContent('Invalid date')
    })

    it('should not display error element when no error', () => {
      const { container } = render(<DatePicker label="Start Date" />)

      const errorText = container.querySelector('.text-red-600')
      expect(errorText).not.toBeInTheDocument()
    })
  })

  describe('Label Styling', () => {
    it('should have correct label styling', () => {
      const { container } = render(<DatePicker label="Start Date" />)

      const label = container.querySelector('label')
      expect(label).toHaveClass('block')
      expect(label).toHaveClass('text-sm')
      expect(label).toHaveClass('font-medium')
      expect(label).toHaveClass('text-gray-700')
    })

    it('should associate label with input', () => {
      render(<DatePicker label="Start Date" />)

      const label = screen.getByText('Start Date')
      const input = screen.getByLabelText('Start Date')

      expect(label.tagName).toBe('LABEL')
      expect(input).toBeInTheDocument()
    })
  })

  describe('Forward Ref', () => {
    it('should forward ref to input element', () => {
      const ref = createRef<HTMLInputElement>()

      render(<DatePicker label="Start Date" ref={ref} />)

      expect(ref.current).toBeInstanceOf(HTMLInputElement)
      expect(ref.current?.type).toBe('date')
    })

    it('should allow calling focus on ref', () => {
      const ref = createRef<HTMLInputElement>()

      render(<DatePicker label="Start Date" ref={ref} />)

      ref.current?.focus()
      expect(ref.current).toHaveFocus()
    })
  })

  describe('Additional Props', () => {
    it('should pass through disabled prop', () => {
      render(<DatePicker label="Start Date" disabled />)

      const input = screen.getByLabelText('Start Date')
      expect(input).toBeDisabled()
    })

    it('should pass through required prop', () => {
      render(<DatePicker label="Start Date" required />)

      const input = screen.getByLabelText('Start Date')
      expect(input).toBeRequired()
    })

    it('should pass through min prop', () => {
      render(<DatePicker label="Start Date" min="2024-01-01" />)

      const input = screen.getByLabelText('Start Date')
      expect(input).toHaveAttribute('min', '2024-01-01')
    })

    it('should pass through max prop', () => {
      render(<DatePicker label="Start Date" max="2024-12-31" />)

      const input = screen.getByLabelText('Start Date')
      expect(input).toHaveAttribute('max', '2024-12-31')
    })

    it('should pass through placeholder prop', () => {
      render(<DatePicker label="Start Date" placeholder="Select a date" />)

      const input = screen.getByLabelText('Start Date')
      expect(input).toHaveAttribute('placeholder', 'Select a date')
    })

    it('should pass through name prop', () => {
      render(<DatePicker label="Start Date" name="start_date" />)

      const input = screen.getByLabelText('Start Date')
      expect(input).toHaveAttribute('name', 'start_date')
    })

    it('should pass through id prop', () => {
      render(<DatePicker label="Start Date" id="custom-id" />)

      const input = screen.getByLabelText('Start Date')
      expect(input).toHaveAttribute('id', 'custom-id')
    })

    it('should pass through aria-label prop', () => {
      render(<DatePicker label="Start Date" aria-label="Custom aria label" />)

      const input = screen.getByLabelText('Custom aria label')
      expect(input).toBeInTheDocument()
    })
  })

  describe('Focus States', () => {
    it('should have focus styles', () => {
      render(<DatePicker label="Start Date" />)

      const input = screen.getByLabelText('Start Date')
      expect(input).toHaveClass('focus:outline-none')
      expect(input).toHaveClass('focus:ring-2')
      expect(input).toHaveClass('focus:ring-blue-500')
      expect(input).toHaveClass('focus:border-blue-500')
    })

    it('should be focusable', () => {
      render(<DatePicker label="Start Date" />)

      const input = screen.getByLabelText('Start Date')
      input.focus()
      expect(input).toHaveFocus()
    })
  })

  describe('Container Structure', () => {
    it('should wrap components in a container with spacing', () => {
      const { container } = render(<DatePicker label="Start Date" />)

      const wrapper = container.querySelector('.space-y-1')
      expect(wrapper).toBeInTheDocument()
    })

    it('should render label before input', () => {
      const { container } = render(<DatePicker label="Start Date" />)

      const wrapper = container.querySelector('.space-y-1')
      const children = Array.from(wrapper?.children || [])

      expect(children[0].tagName).toBe('LABEL')
      expect(children[1].tagName).toBe('INPUT')
    })

    it('should render error after input when present', () => {
      const { container } = render(
        <DatePicker label="Start Date" error="Error message" />
      )

      const wrapper = container.querySelector('.space-y-1')
      const children = Array.from(wrapper?.children || [])

      expect(children.length).toBe(3)
      expect(children[2].tagName).toBe('P')
      expect(children[2].textContent).toBe('Error message')
    })
  })

  describe('Display Name', () => {
    it('should have correct display name', () => {
      expect(DatePicker.displayName).toBe('DatePicker')
    })
  })

  describe('Integration Scenarios', () => {
    it('should work in a form submission scenario', async () => {
      const user = userEvent.setup()
      const onSubmit = jest.fn((e) => e.preventDefault())

      render(
        <form onSubmit={onSubmit}>
          <DatePicker label="Start Date" name="start_date" required />
          <button type="submit">Submit</button>
        </form>
      )

      const input = screen.getByLabelText('Start Date')
      await user.type(input, '2024-02-15')

      const submitButton = screen.getByRole('button', { name: /submit/i })
      await user.click(submitButton)

      expect(onSubmit).toHaveBeenCalled()
    })

    it('should clear value when user clears input', async () => {
      const user = userEvent.setup()

      render(<DatePicker label="Start Date" value="2024-02-15" onChange={mockOnChange} />)

      const input = screen.getByLabelText('Start Date')
      await user.clear(input)

      expect(mockOnChange).toHaveBeenCalledWith('')
    })

    it('should update when controlled value changes', () => {
      const { rerender } = render(
        <DatePicker label="Start Date" value="2024-02-15" onChange={mockOnChange} />
      )

      let input = screen.getByLabelText('Start Date') as HTMLInputElement
      expect(input.value).toBe('2024-02-15')

      rerender(
        <DatePicker label="Start Date" value="2024-03-20" onChange={mockOnChange} />
      )

      input = screen.getByLabelText('Start Date') as HTMLInputElement
      expect(input.value).toBe('2024-03-20')
    })
  })
})
