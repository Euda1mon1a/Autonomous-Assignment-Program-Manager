'use client';

import React, { forwardRef, ButtonHTMLAttributes } from 'react';
import { ButtonSpinner } from '../LoadingStates';

export type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'ghost' | 'outline' | 'success';
export type ButtonSize = 'sm' | 'md' | 'lg';

/**
 * Base props shared by all button types
 */
interface ButtonBaseProps extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'onClick' | 'type'> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  loadingText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  fullWidth?: boolean;
}

/**
 * Interactive button - requires onClick handler
 * Use for buttons that trigger actions (open modal, navigate, etc.)
 */
interface ActionButtonProps extends ButtonBaseProps {
  onClick: (e: React.MouseEvent<HTMLButtonElement>) => void;
  type?: 'button' | 'reset'; // Not 'submit' - use SubmitButtonProps for that
}

/**
 * Form submit button - uses form's onSubmit, no onClick needed
 * Use inside <form> elements that have an onSubmit handler
 */
interface SubmitButtonProps extends ButtonBaseProps {
  type: 'submit';
  onClick?: (e: React.MouseEvent<HTMLButtonElement>) => void; // Optional for submit
}

/**
 * Button requires either:
 * - onClick handler (for interactive buttons), OR
 * - type="submit" (for form submission)
 *
 * This prevents unclickable buttons that frustrate users.
 * See: Session 086 - "New Template" button bug
 */
export type ButtonProps = ActionButtonProps | SubmitButtonProps;

const variantStyles: Record<ButtonVariant, string> = {
  primary: 'bg-blue-600 hover:bg-blue-700 text-white shadow-sm focus:ring-blue-500',
  secondary: 'bg-gray-100 hover:bg-gray-200 text-gray-900 focus:ring-gray-500',
  danger: 'bg-red-600 hover:bg-red-700 text-white shadow-sm focus:ring-red-500',
  ghost: 'bg-transparent hover:bg-gray-100 text-gray-700 focus:ring-gray-500',
  outline: 'border border-gray-300 bg-white hover:bg-gray-50 text-gray-700 focus:ring-blue-500',
  success: 'bg-green-600 hover:bg-green-700 text-white shadow-sm focus:ring-green-500',
};

const sizeStyles: Record<ButtonSize, string> = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-sm',
  lg: 'px-6 py-3 text-base',
};

/**
 * Versatile button component with multiple variants and states
 *
 * @example
 * ```tsx
 * <Button variant="primary" size="md">
 *   Save Changes
 * </Button>
 *
 * <Button variant="danger" isLoading>
 *   Deleting...
 * </Button>
 *
 * <Button variant="outline" leftIcon={<PlusIcon />}>
 *   Add Item
 * </Button>
 * ```
 */
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      isLoading = false,
      loadingText,
      leftIcon,
      rightIcon,
      fullWidth = false,
      disabled,
      children,
      className = '',
      type,
      onClick,
      ...props
    },
    ref
  ) => {
    const baseStyles = 'inline-flex items-center justify-center gap-2 font-medium rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed';

    const widthStyles = fullWidth ? 'w-full' : '';

    return (
      <button
        ref={ref}
        type={type || 'button'}
        onClick={onClick}
        disabled={disabled || isLoading}
        aria-busy={isLoading || undefined}
        aria-disabled={disabled || isLoading || undefined}
        className={`${baseStyles} ${variantStyles[variant]} ${sizeStyles[size]} ${widthStyles} ${className}`}
        {...props}
      >
        {isLoading ? (
          <>
            <ButtonSpinner variant="white" />
            {loadingText || children}
          </>
        ) : (
          <>
            {leftIcon && <span className="inline-flex">{leftIcon}</span>}
            {children}
            {rightIcon && <span className="inline-flex">{rightIcon}</span>}
          </>
        )}
      </button>
    );
  }
);

Button.displayName = 'Button';

/**
 * Icon-only button variant
 */
export interface IconButtonProps extends Omit<ButtonProps, 'leftIcon' | 'rightIcon' | 'children'> {
  'aria-label': string; // Enforce accessible label
  icon?: React.ReactNode;
  children?: React.ReactNode; // Keep children for flexibility but encourage icon prop
}

export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(
  ({ children, icon, size = 'md', className = '', onClick, type, ...props }, ref) => {
    const iconSizes = {
      sm: 'p-1.5',
      md: 'p-2',
      lg: 'p-3',
    };

    // IconButton requires onClick OR type="submit" just like Button
    const buttonProps = type === 'submit'
      ? { type: 'submit' as const, onClick }
      : { onClick: onClick!, type };

    return (
      <Button
        ref={ref}
        size={size}
        className={`${iconSizes[size]} ${className}`}
        {...buttonProps}
        {...props}
      >
        {icon || children}
      </Button>
    );
  }
);

IconButton.displayName = 'IconButton';
