/**
 * Select Component
 *
 * Custom select dropdown with search support
 */

import React, { useState, useRef, useEffect } from 'react';

export interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

export interface SelectProps {
  options: SelectOption[];
  value?: string;
  onChange: (value: string) => void;
  placeholder?: string;
  searchable?: boolean;
  disabled?: boolean;
  error?: string;
  label?: string;
  required?: boolean;
  className?: string;
}

export const Select: React.FC<SelectProps> = ({
  options,
  value,
  onChange,
  placeholder = 'Select an option',
  searchable = false,
  disabled = false,
  error,
  label,
  required = false,
  className = '',
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const containerRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  const selectedOption = options.find(opt => opt.value === value);

  const filteredOptions = searchable && searchQuery
    ? options.filter(opt =>
        opt.label.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : options;

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setSearchQuery('');
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      if (searchable && searchInputRef.current) {
        searchInputRef.current.focus();
      }
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, searchable]);

  const handleSelect = (optionValue: string) => {
    onChange(optionValue);
    setIsOpen(false);
    setSearchQuery('');
  };

  const [activeIndex, setActiveIndex] = useState(-1);

  // Update active index when filtered options change
  useEffect(() => {
    setActiveIndex(-1);
  }, [searchQuery]);

  const scrollToOption = (index: number) => {
    const listbox = document.getElementById('select-listbox');
    const option = document.getElementById(`option-${index}`);
    if (listbox && option) {
      const listboxRect = listbox.getBoundingClientRect();
      const optionRect = option.getBoundingClientRect();
      if (optionRect.bottom > listboxRect.bottom) {
        listbox.scrollTop += optionRect.bottom - listboxRect.bottom;
      } else if (optionRect.top < listboxRect.top) {
        listbox.scrollTop -= listboxRect.top - optionRect.top;
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (disabled) return;

    switch (e.key) {
      case 'Escape':
      case 'Tab':
        setIsOpen(false);
        setSearchQuery('');
        break;
      case 'ArrowDown':
        e.preventDefault();
        if (!isOpen) {
          setIsOpen(true);
        } else {
          setActiveIndex(prev => {
             const next = prev < filteredOptions.length - 1 ? prev + 1 : prev;
             scrollToOption(next);
             return next;
          });
        }
        break;
      case 'ArrowUp':
        e.preventDefault();
        if (!isOpen) {
          setIsOpen(true);
        } else {
          setActiveIndex(prev => {
            const next = prev > 0 ? prev - 1 : 0;
            scrollToOption(next);
            return next;
          });
        }
        break;
      case 'Enter':
        e.preventDefault();
        if (isOpen && activeIndex >= 0 && activeIndex < filteredOptions.length) {
          const option = filteredOptions[activeIndex];
          if (!option.disabled) {
            handleSelect(option.value);
          }
        } else if (!isOpen) {
          setIsOpen(true);
        }
        break;
    }
  };

  return (
    <div className={`select-component ${className}`} ref={containerRef}>
      {/* Label */}
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}

      {/* Select Button */}
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        onKeyDown={handleKeyDown}
        aria-label={label || (selectedOption?.label || placeholder)}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-disabled={disabled}
        className={`
          w-full px-4 py-2 border rounded-lg bg-white text-left transition-colors
          ${error ? 'border-red-500' : 'border-gray-300'}
          ${disabled ? 'bg-gray-100 cursor-not-allowed' : 'hover:border-gray-400'}
          focus:outline-none focus:ring-2 focus:ring-blue-500
        `}
      >
        <div className="flex items-center justify-between">
          <span className={selectedOption ? 'text-gray-900' : 'text-gray-500'}>
            {selectedOption?.label || placeholder}
          </span>
          <span className={`transition-transform ${isOpen ? 'rotate-180' : ''}`} aria-hidden="true">
            ▼
          </span>
        </div>
      </button>

      {/* Error Message */}
      {error && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}

      {/* Dropdown */}
      {isOpen && !disabled && (
        <div
          id="select-listbox"
          className="absolute z-50 mt-1 w-full bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-hidden"
          role="listbox"
          aria-activedescendant={activeIndex >= 0 ? `option-${activeIndex}` : undefined}
        >
          {/* Search Input */}
          {searchable && (
            <div className="p-2 border-b border-gray-200">
              <input
                ref={searchInputRef}
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search..."
                aria-label="Search options"
                aria-controls="select-listbox"
                className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                onKeyDown={handleKeyDown}
              />
            </div>
          )}

          {/* Options List */}
          <div className="overflow-y-auto max-h-52">
            {filteredOptions.length === 0 ? (
              <div className="px-4 py-3 text-sm text-gray-500 text-center" role="status">
                No options found
              </div>
            ) : (
              filteredOptions.map((option, index) => (
                <button
                  key={option.value}
                  id={`option-${index}`}
                  onClick={() => !option.disabled && handleSelect(option.value)}
                  disabled={option.disabled}
                  role="option"
                  aria-selected={option.value === value}
                  aria-disabled={option.disabled}
                  onMouseEnter={() => setActiveIndex(index)}
                  className={`
                    w-full px-4 py-2 text-left text-sm transition-colors
                    ${activeIndex === index ? 'bg-gray-100' : ''}
                    ${option.value === value ? 'bg-blue-50 text-blue-900 font-medium' : 'text-gray-900'}
                    ${option.disabled ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-100'}
                    focus:outline-none
                  `}
                >
                  {option.label}
                  {option.value === value && (
                    <span className="ml-2 text-blue-600" aria-hidden="true">✓</span>
                  )}
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Select;
