'use client';

import React, { useState, useRef, useEffect } from 'react';
import { X, ChevronDown, Check } from 'lucide-react';
import { Badge } from '../ui/Badge';

export interface MultiSelectOption {
  label: string;
  value: string;
  disabled?: boolean;
}

export interface MultiSelectProps {
  options: MultiSelectOption[];
  value: string[];
  onChange: (value: string[]) => void;
  label?: string;
  placeholder?: string;
  maxDisplay?: number;
  searchable?: boolean;
  className?: string;
}

/**
 * MultiSelect component for selecting multiple options
 *
 * @example
 * ```tsx
 * <MultiSelect
 *   options={[
 *     { label: 'Option 1', value: '1' },
 *     { label: 'Option 2', value: '2' },
 *   ]}
 *   value={['1']}
 *   onChange={(values) => setSelected(values)}
 *   label="Select Options"
 *   searchable
 * />
 * ```
 */
export function MultiSelect({
  options,
  value,
  onChange,
  label,
  placeholder = 'Select options...',
  maxDisplay = 3,
  searchable = false,
  className = '',
}: MultiSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const dropdownRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const listboxId = React.useId();
  const labelId = React.useId();

  // Close on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setSearchQuery('');
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  const filteredOptions = searchable
    ? options.filter((opt) =>
        opt.label.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : options;

  const selectedOptions = options.filter((opt) => value.includes(opt.value));

  const toggleOption = (optionValue: string) => {
    if (value.includes(optionValue)) {
      onChange(value.filter((v) => v !== optionValue));
    } else {
      onChange([...value, optionValue]);
    }
  };

  const removeOption = (optionValue: string) => {
    onChange(value.filter((v) => v !== optionValue));
  };

  const clearAll = () => {
    onChange([]);
  };

  return (
    <div ref={dropdownRef} className={`relative ${className}`}>
      {label && (
        <label id={labelId} className="block text-sm font-medium text-gray-700 mb-1">
          {label}
        </label>
      )}

      {/* Trigger Button */}
      <button
        ref={buttonRef}
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full min-h-[42px] px-3 py-2 text-left border border-gray-300 rounded-md bg-white hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-labelledby={label ? labelId : undefined}
        aria-label={!label ? placeholder : undefined}
        role="combobox"
        aria-controls={listboxId}
      >
        <div className="flex items-center justify-between gap-2">
          <div className="flex-1 flex flex-wrap gap-1">
            {selectedOptions.length === 0 ? (
              <span className="text-gray-500">{placeholder}</span>
            ) : selectedOptions.length <= maxDisplay ? (
              selectedOptions.map((opt) => (
                <Badge
                  key={opt.value}
                  variant="primary"
                  size="sm"
                  className="cursor-pointer"
                >
                  {opt.label}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      removeOption(opt.value);
                    }}
                    aria-label={`Remove ${opt.label}`}
                    type="button"
                  >
                    <X
                      className="w-3 h-3 ml-1 hover:text-blue-900"
                      aria-hidden="true"
                    />
                  </button>
                </Badge>
              ))
            ) : (
              <>
                <Badge variant="primary" size="sm">
                  {selectedOptions[0].label}
                </Badge>
                <Badge variant="default" size="sm">
                  +{selectedOptions.length - 1} more
                </Badge>
              </>
            )}
          </div>

          <div className="flex items-center gap-1">
            {value.length > 0 && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  clearAll();
                }}
                className="p-1 hover:bg-gray-100 rounded"
                aria-label="Clear all selections"
                type="button"
              >
                <X className="w-4 h-4 text-gray-400" aria-hidden="true" />
              </button>
            )}
            <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} aria-hidden="true" />
          </div>
        </div>
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div
          id={listboxId}
          className="absolute z-50 mt-1 w-full bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto"
          role="listbox"
          aria-label={label || 'Select options'}
          aria-multiselectable="true"
        >
          {searchable && (
            <div className="p-2 border-b border-gray-200">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search..."
                className="w-full px-3 py-1.5 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                onClick={(e) => e.stopPropagation()}
                aria-label="Search options"
              />
            </div>
          )}

          <div className="py-1">
            {filteredOptions.length === 0 ? (
              <div className="px-3 py-2 text-sm text-gray-500" role="status">
                No options found
              </div>
            ) : (
              filteredOptions.map((option) => {
                const isSelected = value.includes(option.value);

                return (
                  <div
                    key={option.value}
                    role="option"
                    aria-selected={isSelected}
                    aria-disabled={option.disabled}
                  >
                    <button
                      onClick={() => !option.disabled && toggleOption(option.value)}
                      disabled={option.disabled}
                      className={`w-full px-3 py-2 text-left text-sm flex items-center justify-between hover:bg-gray-100 ${
                        option.disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'
                      } ${isSelected ? 'bg-blue-50 text-blue-900' : 'text-gray-900'}`}
                      type="button"
                      tabIndex={0}
                    >
                      <span>{option.label}</span>
                      {isSelected && <Check className="w-4 h-4 text-blue-600" aria-hidden="true" />}
                    </button>
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}
