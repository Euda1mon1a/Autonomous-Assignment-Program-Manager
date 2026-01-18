import React from "react";

interface IconProps {
  className?: string;
}

export const BrainIcon: React.FC<IconProps> = ({ className = "w-5 h-5" }) => (
  <svg
    className={className}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M9.5 2A5.5 5.5 0 0 0 4 7.5c0 1.25.42 2.4 1.13 3.32C4.43 11.64 4 12.77 4 14c0 3.31 2.69 6 6 6h.5c1.38 0 2.5-1.12 2.5-2.5V14h3a3 3 0 0 0 0-6h-3V5.5C13 3.57 11.43 2 9.5 2z" />
    <path d="M14.5 2A5.5 5.5 0 0 1 20 7.5c0 1.25-.42 2.4-1.13 3.32.7.82 1.13 1.95 1.13 3.18 0 3.31-2.69 6-6 6h-.5c-1.38 0-2.5-1.12-2.5-2.5V14h-3a3 3 0 0 1 0-6h3V5.5C11 3.57 12.57 2 14.5 2z" />
  </svg>
);

export const MoonIcon: React.FC<IconProps> = ({ className = "w-4 h-4" }) => (
  <svg
    className={className}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
  </svg>
);

export const AlertIcon: React.FC<IconProps> = ({ className = "w-4 h-4" }) => (
  <svg
    className={className}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <circle cx="12" cy="12" r="10" />
    <line x1="12" y1="8" x2="12" y2="12" />
    <line x1="12" y1="16" x2="12.01" y2="16" />
  </svg>
);

export const PulseIcon: React.FC<IconProps> = ({ className = "w-4 h-4" }) => (
  <svg
    className={className}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
  </svg>
);
