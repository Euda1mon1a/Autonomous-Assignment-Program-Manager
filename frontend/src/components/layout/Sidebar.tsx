'use client';

import React, { useState } from 'react';
import { X, ChevronLeft, ChevronRight } from 'lucide-react';

export interface SidebarProps {
  children: React.ReactNode;
  position?: 'left' | 'right';
  width?: 'sm' | 'md' | 'lg';
  collapsible?: boolean;
  defaultCollapsed?: boolean;
  overlay?: boolean;
  onClose?: () => void;
  className?: string;
}

const widthStyles = {
  sm: 'w-64',
  md: 'w-80',
  lg: 'w-96',
};

/**
 * Sidebar component for side navigation or content panels
 *
 * @example
 * ```tsx
 * <Sidebar position="left" collapsible>
 *   <nav>Navigation items</nav>
 * </Sidebar>
 * ```
 */
export function Sidebar({
  children,
  position = 'left',
  width = 'md',
  collapsible = false,
  defaultCollapsed = false,
  overlay = false,
  onClose,
  className = '',
}: SidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed);

  const toggleCollapse = () => {
    setIsCollapsed(!isCollapsed);
  };

  const positionStyles = position === 'left' ? 'left-0' : 'right-0';

  return (
    <>
      {/* Overlay (for mobile/modal sidebars) */}
      {overlay && !isCollapsed && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        role="navigation"
        aria-label="Sidebar navigation"
        className={`fixed ${positionStyles} top-0 h-full bg-white border-r border-gray-200 transition-all duration-300 z-50 ${
          isCollapsed ? 'w-16' : widthStyles[width]
        } ${className}`}
      >
        {/* Header with collapse button */}
        {collapsible && (
          <div className="flex items-center justify-between p-4 border-b border-gray-200">
            {!isCollapsed && <div className="flex-1" />}
            <button
              onClick={toggleCollapse}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            >
              {position === 'left' ? (
                isCollapsed ? <ChevronRight className="w-5 h-5" /> : <ChevronLeft className="w-5 h-5" />
              ) : (
                isCollapsed ? <ChevronLeft className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />
              )}
            </button>
          </div>
        )}

        {/* Close button (for overlay mode) */}
        {overlay && onClose && !isCollapsed && (
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-2 hover:bg-gray-100 rounded-lg lg:hidden"
          >
            <X className="w-5 h-5" />
          </button>
        )}

        {/* Content */}
        <div className={`overflow-y-auto h-full ${isCollapsed ? 'hidden' : ''}`}>
          {children}
        </div>
      </aside>
    </>
  );
}

/**
 * Sidebar navigation item
 */
export function SidebarItem({
  icon,
  label,
  active = false,
  badge,
  onClick,
  className = '',
}: {
  icon?: React.ReactNode;
  label: string;
  active?: boolean;
  badge?: string | number;
  onClick?: () => void;
  className?: string;
}) {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center gap-3 px-4 py-3 text-sm transition-colors ${
        active
          ? 'bg-blue-50 text-blue-700 font-medium border-l-4 border-blue-700'
          : 'text-gray-700 hover:bg-gray-50 border-l-4 border-transparent'
      } ${className}`}
    >
      {icon && <span className="flex-shrink-0">{icon}</span>}
      <span className="flex-1 text-left">{label}</span>
      {badge !== undefined && (
        <span className="px-2 py-0.5 text-xs font-medium bg-gray-200 text-gray-700 rounded-full">
          {badge}
        </span>
      )}
    </button>
  );
}

/**
 * Sidebar section with header
 */
export function SidebarSection({
  title,
  children,
  className = '',
}: {
  title?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`py-4 ${className}`}>
      {title && (
        <h3 className="px-4 mb-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
          {title}
        </h3>
      )}
      <div className="space-y-1">{children}</div>
    </div>
  );
}
