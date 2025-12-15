'use client';

import {
  Calendar,
  ClipboardList,
  RefreshCw,
  Phone,
  Building2,
  Puzzle,
  LucideIcon,
} from 'lucide-react';
import type { TemplateCategory } from '../types';
import { TEMPLATE_CATEGORIES, CATEGORY_COLORS } from '../constants';

// Icon mapping
const CATEGORY_ICONS: Record<string, LucideIcon> = {
  Calendar,
  ClipboardList,
  RefreshCw,
  Phone,
  Building2,
  Puzzle,
};

interface TemplateCategoriesProps {
  selectedCategory?: TemplateCategory;
  onCategorySelect: (category: TemplateCategory | undefined) => void;
  categoryCounts?: Record<TemplateCategory, number>;
  variant?: 'pills' | 'cards' | 'list';
}

export function TemplateCategories({
  selectedCategory,
  onCategorySelect,
  categoryCounts = {} as Record<TemplateCategory, number>,
  variant = 'pills',
}: TemplateCategoriesProps) {
  if (variant === 'cards') {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {TEMPLATE_CATEGORIES.map((category) => {
          const Icon = CATEGORY_ICONS[category.icon] || Puzzle;
          const colors = CATEGORY_COLORS[category.id];
          const isSelected = selectedCategory === category.id;
          const count = categoryCounts[category.id] || 0;

          return (
            <button
              key={category.id}
              onClick={() =>
                onCategorySelect(isSelected ? undefined : category.id)
              }
              className={`p-4 rounded-lg border-2 transition-all text-left ${
                isSelected
                  ? `${colors.bg} ${colors.border} ${colors.text}`
                  : 'bg-white border-gray-200 hover:border-gray-300'
              }`}
            >
              <Icon
                className={`w-6 h-6 mb-2 ${
                  isSelected ? colors.text : 'text-gray-500'
                }`}
              />
              <div className="font-medium text-sm">{category.name}</div>
              <div
                className={`text-xs mt-1 ${
                  isSelected ? colors.text : 'text-gray-500'
                }`}
              >
                {count} template{count !== 1 ? 's' : ''}
              </div>
            </button>
          );
        })}
      </div>
    );
  }

  if (variant === 'list') {
    return (
      <div className="space-y-1">
        <button
          onClick={() => onCategorySelect(undefined)}
          className={`w-full px-3 py-2 rounded-lg text-left flex items-center justify-between ${
            !selectedCategory
              ? 'bg-blue-50 text-blue-700'
              : 'hover:bg-gray-50 text-gray-700'
          }`}
        >
          <span className="font-medium">All Templates</span>
          <span className="text-sm text-gray-500">
            {Object.values(categoryCounts).reduce((a, b) => a + b, 0)}
          </span>
        </button>

        {TEMPLATE_CATEGORIES.map((category) => {
          const Icon = CATEGORY_ICONS[category.icon] || Puzzle;
          const colors = CATEGORY_COLORS[category.id];
          const isSelected = selectedCategory === category.id;
          const count = categoryCounts[category.id] || 0;

          return (
            <button
              key={category.id}
              onClick={() =>
                onCategorySelect(isSelected ? undefined : category.id)
              }
              className={`w-full px-3 py-2 rounded-lg text-left flex items-center justify-between ${
                isSelected
                  ? `${colors.bg} ${colors.text}`
                  : 'hover:bg-gray-50 text-gray-700'
              }`}
            >
              <span className="flex items-center gap-2">
                <Icon className="w-4 h-4" />
                <span>{category.name}</span>
              </span>
              <span
                className={`text-sm ${
                  isSelected ? colors.text : 'text-gray-500'
                }`}
              >
                {count}
              </span>
            </button>
          );
        })}
      </div>
    );
  }

  // Pills variant (default)
  return (
    <div className="flex flex-wrap gap-2">
      <button
        onClick={() => onCategorySelect(undefined)}
        className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
          !selectedCategory
            ? 'bg-blue-600 text-white'
            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
        }`}
      >
        All
      </button>

      {TEMPLATE_CATEGORIES.map((category) => {
        const colors = CATEGORY_COLORS[category.id];
        const isSelected = selectedCategory === category.id;
        const count = categoryCounts[category.id] || 0;

        return (
          <button
            key={category.id}
            onClick={() =>
              onCategorySelect(isSelected ? undefined : category.id)
            }
            className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors flex items-center gap-1 ${
              isSelected
                ? `${colors.bg} ${colors.text} ring-2 ring-offset-1 ${colors.border.replace('border', 'ring')}`
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {category.name.split(' ')[0]}
            {count > 0 && (
              <span
                className={`text-xs ${
                  isSelected ? 'opacity-75' : 'text-gray-500'
                }`}
              >
                ({count})
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}

interface CategoryBadgeProps {
  category: TemplateCategory;
  size?: 'sm' | 'md' | 'lg';
}

export function CategoryBadge({ category, size = 'md' }: CategoryBadgeProps) {
  const categoryInfo = TEMPLATE_CATEGORIES.find((c) => c.id === category);
  const colors = CATEGORY_COLORS[category];
  const Icon = CATEGORY_ICONS[categoryInfo?.icon || 'Puzzle'] || Puzzle;

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-sm',
    lg: 'px-3 py-1.5 text-base',
  };

  const iconSizes = {
    sm: 'w-3 h-3',
    md: 'w-4 h-4',
    lg: 'w-5 h-5',
  };

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full ${colors.bg} ${colors.text} ${sizeClasses[size]}`}
    >
      <Icon className={iconSizes[size]} />
      <span>{categoryInfo?.name || category}</span>
    </span>
  );
}
