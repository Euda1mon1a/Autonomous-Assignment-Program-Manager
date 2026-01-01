/**
 * Switch Component
 *
 * Toggle switch for boolean values
 */

import React from 'react';

export interface SwitchProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
  description?: string;
  disabled?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const Switch: React.FC<SwitchProps> = ({
  checked,
  onChange,
  label,
  description,
  disabled = false,
  size = 'md',
  className = '',
}) => {
  const sizeConfig = {
    sm: {
      switch: 'w-9 h-5',
      thumb: 'w-4 h-4',
      translate: 'translate-x-4',
    },
    md: {
      switch: 'w-11 h-6',
      thumb: 'w-5 h-5',
      translate: 'translate-x-5',
    },
    lg: {
      switch: 'w-14 h-7',
      thumb: 'w-6 h-6',
      translate: 'translate-x-7',
    },
  };

  const config = sizeConfig[size];

  const handleClick = () => {
    if (!disabled) {
      onChange(!checked);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === ' ' || e.key === 'Enter') {
      e.preventDefault();
      handleClick();
    }
  };

  return (
    <div className={`switch-component ${className}`}>
      <div className="flex items-center gap-3">
        {/* Switch */}
        <button
          type="button"
          role="switch"
          aria-checked={checked}
          aria-label={label || (checked ? 'Switch on' : 'Switch off')}
          aria-disabled={disabled}
          onClick={handleClick}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          className={`
            relative inline-flex items-center rounded-full transition-colors
            ${config.switch}
            ${checked ? 'bg-blue-600' : 'bg-gray-200'}
            ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
          `}
        >
          <span
            className={`
              inline-block rounded-full bg-white shadow-sm transition-transform
              ${config.thumb}
              ${checked ? config.translate : 'translate-x-0.5'}
            `}
            aria-hidden="true"
          />
        </button>

        {/* Label & Description */}
        {(label || description) && (
          <div className="flex-1">
            {label && (
              <div
                className={`text-sm font-medium ${
                  disabled ? 'text-gray-400' : 'text-gray-900'
                }`}
              >
                {label}
              </div>
            )}
            {description && (
              <div className="text-xs text-gray-500 mt-0.5">{description}</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Switch;
