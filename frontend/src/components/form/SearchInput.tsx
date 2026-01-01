'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Search, X, Loader2 } from 'lucide-react';

export interface SearchInputProps {
  value: string;
  onChange: (value: string) => void;
  onSearch?: (value: string) => void;
  onFocus?: () => void;
  placeholder?: string;
  loading?: boolean;
  debounceMs?: number;
  showClearButton?: boolean;
  className?: string;
}

/**
 * SearchInput component with debounce and clear functionality
 *
 * @example
 * ```tsx
 * <SearchInput
 *   value={query}
 *   onChange={setQuery}
 *   onSearch={(q) => performSearch(q)}
 *   placeholder="Search residents..."
 *   debounceMs={300}
 *   showClearButton
 * />
 * ```
 */
export function SearchInput({
  value,
  onChange,
  onSearch,
  onFocus,
  placeholder = 'Search...',
  loading = false,
  debounceMs = 300,
  showClearButton = true,
  className = '',
}: SearchInputProps) {
  const [debouncedValue, setDebouncedValue] = useState(value);
  const timeoutRef = useRef<NodeJS.Timeout>();
  const inputId = React.useId();

  // Debounce the search
  useEffect(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    timeoutRef.current = setTimeout(() => {
      setDebouncedValue(value);
      if (onSearch) {
        onSearch(value);
      }
    }, debounceMs);

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [value, debounceMs, onSearch]);

  const handleClear = () => {
    onChange('');
  };

  return (
    <div className={`relative ${className}`}>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" aria-hidden="true" />

        <input
          id={inputId}
          type="search"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onFocus={onFocus}
          placeholder={placeholder}
          className="block w-full pl-10 pr-10 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          aria-label={placeholder}
          aria-busy={loading}
          role="searchbox"
        />

        <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1">
          {loading && (
            <Loader2 className="w-4 h-4 text-gray-400 animate-spin" aria-label="Loading search results" />
          )}

          {showClearButton && value && !loading && (
            <button
              onClick={handleClear}
              className="p-0.5 hover:bg-gray-100 rounded-full transition-colors"
              aria-label="Clear search"
              type="button"
            >
              <X className="w-4 h-4 text-gray-400 hover:text-gray-600" aria-hidden="true" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * SearchInput with suggestions/autocomplete
 */
export interface SearchWithSuggestionsProps extends SearchInputProps {
  suggestions: string[];
  onSuggestionSelect: (suggestion: string) => void;
  maxSuggestions?: number;
}

export function SearchWithSuggestions({
  suggestions,
  onSuggestionSelect,
  maxSuggestions = 5,
  ...searchProps
}: SearchWithSuggestionsProps) {
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const listboxId = React.useId();

  const filteredSuggestions = suggestions
    .filter((s) => s.toLowerCase().includes(searchProps.value.toLowerCase()))
    .slice(0, maxSuggestions);

  // Close on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowSuggestions(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showSuggestions || filteredSuggestions.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex((prev) => Math.min(prev + 1, filteredSuggestions.length - 1));
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex((prev) => Math.max(prev - 1, -1));
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0) {
          onSuggestionSelect(filteredSuggestions[selectedIndex]);
          setShowSuggestions(false);
        }
        break;
      case 'Escape':
        setShowSuggestions(false);
        break;
    }
  };

  return (
    <div ref={dropdownRef} className="relative">
      <div onKeyDown={handleKeyDown}>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" aria-hidden="true" />
          <input
            type="search"
            value={searchProps.value}
            onChange={(e) => {
              searchProps.onChange(e.target.value);
              setShowSuggestions(true);
              setSelectedIndex(-1);
            }}
            onFocus={() => setShowSuggestions(true)}
            placeholder={searchProps.placeholder || 'Search...'}
            className="block w-full pl-10 pr-10 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            aria-label={searchProps.placeholder || 'Search'}
            aria-autocomplete="list"
            aria-controls={listboxId}
            aria-expanded={showSuggestions && filteredSuggestions.length > 0}
            aria-activedescendant={selectedIndex >= 0 ? `suggestion-${selectedIndex}` : undefined}
            role="combobox"
          />
        </div>
      </div>

      {showSuggestions && filteredSuggestions.length > 0 && (
        <ul
          id={listboxId}
          className="absolute z-50 mt-1 w-full bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto"
          role="listbox"
          aria-label="Search suggestions"
        >
          {filteredSuggestions.map((suggestion, index) => (
            <li
              key={index}
              id={`suggestion-${index}`}
              role="option"
              aria-selected={selectedIndex === index}
            >
              <button
                onClick={() => {
                  onSuggestionSelect(suggestion);
                  setShowSuggestions(false);
                }}
                onMouseEnter={() => setSelectedIndex(index)}
                className={`w-full px-4 py-2 text-left text-sm hover:bg-gray-100 ${
                  selectedIndex === index ? 'bg-gray-100' : ''
                }`}
                type="button"
              >
                {suggestion}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
