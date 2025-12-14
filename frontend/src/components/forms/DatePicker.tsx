import { forwardRef, InputHTMLAttributes } from 'react';

interface DatePickerProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type' | 'onChange' | 'value'> {
  label: string;
  error?: string;
  value?: string;
  onChange?: (value: string) => void;
}

export const DatePicker = forwardRef<HTMLInputElement, DatePickerProps>(
  ({ label, error, value, onChange, className = '', ...props }, ref) => {
    return (
      <div className="space-y-1">
        <label className="block text-sm font-medium text-gray-700">
          {label}
        </label>
        <input
          ref={ref}
          type="date"
          value={value}
          onChange={(e) => onChange?.(e.target.value)}
          className={`
            w-full px-3 py-2 border rounded-md shadow-sm
            focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
            ${error ? 'border-red-500' : 'border-gray-300'}
            ${className}
          `}
          {...props}
        />
        {error && (
          <p className="text-sm text-red-600">{error}</p>
        )}
      </div>
    );
  }
);

DatePicker.displayName = 'DatePicker';
