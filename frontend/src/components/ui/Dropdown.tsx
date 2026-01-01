'use client';

import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown } from 'lucide-react';

export interface DropdownItem {
  label: string;
  value: string;
  icon?: React.ReactNode;
  disabled?: boolean;
  danger?: boolean;
}

export interface DropdownProps {
  trigger: React.ReactNode;
  items: DropdownItem[];
  onSelect: (value: string) => void;
  align?: 'left' | 'right';
  className?: string;
}

/**
 * Dropdown menu component with keyboard navigation
 *
 * @example
 * ```tsx
 * <Dropdown
 *   trigger={<Button>Actions</Button>}
 *   items={[
 *     { label: 'Edit', value: 'edit' },
 *     { label: 'Delete', value: 'delete', danger: true },
 *   ]}
 *   onSelect={(value) => // console.log(value)}
 * />
 * ```
 */
export function Dropdown({
  trigger,
  items,
  onSelect,
  align = 'left',
  className = '',
}: DropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [focusedIndex, setFocusedIndex] = useState(0);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  // Keyboard navigation
  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (!isOpen) return;

      switch (event.key) {
        case 'Escape':
          setIsOpen(false);
          break;
        case 'ArrowDown':
          event.preventDefault();
          setFocusedIndex((prev) => Math.min(prev + 1, items.length - 1));
          break;
        case 'ArrowUp':
          event.preventDefault();
          setFocusedIndex((prev) => Math.max(prev - 1, 0));
          break;
        case 'Enter':
        case ' ':
          event.preventDefault();
          const item = items[focusedIndex];
          if (!item.disabled) {
            onSelect(item.value);
            setIsOpen(false);
          }
          break;
      }
    }

    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [isOpen, focusedIndex, items, onSelect]);

  const handleSelect = (value: string, disabled?: boolean) => {
    if (disabled) return;
    onSelect(value);
    setIsOpen(false);
  };

  const menuId = React.useId();

  return (
    <div ref={dropdownRef} className={`relative inline-block ${className}`}>
      {/* Trigger */}
      <div
        onClick={() => setIsOpen(!isOpen)}
        aria-haspopup="menu"
        aria-expanded={isOpen}
        aria-controls={isOpen ? menuId : undefined}
      >
        {trigger}
      </div>

      {/* Menu */}
      {isOpen && (
        <div
          ref={menuRef}
          id={menuId}
          className={`absolute z-50 mt-2 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 ${
            align === 'right' ? 'right-0' : 'left-0'
          }`}
          role="menu"
          aria-orientation="vertical"
          aria-activedescendant={`${menuId}-item-${focusedIndex}`}
        >
          <div className="py-1">
            {items.map((item, index) => (
              <button
                key={item.value}
                id={`${menuId}-item-${index}`}
                onClick={() => handleSelect(item.value, item.disabled)}
                onMouseEnter={() => setFocusedIndex(index)}
                className={`
                  w-full text-left px-4 py-2 text-sm flex items-center gap-2
                  ${item.disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                  ${item.danger ? 'text-red-600 hover:bg-red-50' : 'text-gray-700 hover:bg-gray-100'}
                  ${focusedIndex === index ? 'bg-gray-100' : ''}
                `}
                disabled={item.disabled}
                role="menuitem"
                aria-disabled={item.disabled || undefined}
                tabIndex={focusedIndex === index ? 0 : -1}
              >
                {item.icon && <span className="inline-flex" aria-hidden="true">{item.icon}</span>}
                {item.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Simple select dropdown
 */
export interface SelectDropdownProps {
  value: string;
  options: Array<{ label: string; value: string }>;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
}

export function SelectDropdown({
  value,
  options,
  onChange,
  placeholder = 'Select...',
  className = '',
}: SelectDropdownProps) {
  const selectedOption = options.find((opt) => opt.value === value);

  return (
    <Dropdown
      trigger={
        <button
          className={`px-4 py-2 text-sm border border-gray-300 rounded-md bg-white hover:bg-gray-50 flex items-center justify-between gap-2 min-w-[200px] ${className}`}
          aria-label={selectedOption ? `Selected: ${selectedOption.label}` : placeholder}
        >
          <span className={selectedOption ? 'text-gray-900' : 'text-gray-500'}>
            {selectedOption?.label || placeholder}
          </span>
          <ChevronDown className="w-4 h-4 text-gray-400" aria-hidden="true" />
        </button>
      }
      items={options.map((opt) => ({ label: opt.label, value: opt.value }))}
      onSelect={onChange}
    />
  );
}
