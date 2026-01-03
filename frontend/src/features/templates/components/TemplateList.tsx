'use client';

import { useMemo } from 'react';
import { RefreshCw, FileText, Download } from 'lucide-react';
import type { ScheduleTemplate } from '../types';
import { TemplateCard } from './TemplateCard';

interface TemplateListProps {
  templates: ScheduleTemplate[];
  isLoading?: boolean;
  isError?: boolean;
  error?: Error | null;
  onRetry?: () => void;
  onEdit?: (template: ScheduleTemplate) => void;
  onDelete?: (template: ScheduleTemplate) => void;
  onDuplicate?: (template: ScheduleTemplate) => void;
  onShare?: (template: ScheduleTemplate) => void;
  onPreview?: (template: ScheduleTemplate) => void;
  onApply?: (template: ScheduleTemplate) => void;
  emptyMessage?: string;
  emptyAction?: {
    label: string;
    onClick: () => void;
  };
  variant?: 'grid' | 'list';
}

export function TemplateList({
  templates,
  isLoading = false,
  isError = false,
  error,
  onRetry,
  onEdit,
  onDelete,
  onDuplicate,
  onShare,
  onPreview,
  onApply,
  emptyMessage = 'No templates found',
  emptyAction,
  variant = 'grid',
}: TemplateListProps) {
  // Memoize skeleton array generation
  const skeletons = useMemo(() => Array.from({ length: 6 }, (_, i) => i), []);

  if (isLoading) {
    return (
      <div className={variant === 'grid' ? 'grid gap-4 md:grid-cols-2 lg:grid-cols-3' : 'space-y-3'}>
        {skeletons.map((i) => (
          <TemplateCardSkeleton key={i} variant={variant} />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="card flex flex-col items-center justify-center h-64 text-center">
        <p className="text-gray-600 mb-4">
          {error?.message || 'Failed to load templates'}
        </p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="btn-primary flex items-center gap-2"
            aria-label="Retry loading templates"
          >
            <RefreshCw className="w-4 h-4" aria-hidden="true" />
            Retry
          </button>
        )}
      </div>
    );
  }

  if (templates.length === 0) {
    return (
      <div className="card flex flex-col items-center justify-center h-64 text-center">
        <FileText className="w-12 h-12 text-gray-300 mb-4" aria-hidden="true" />
        <h3 className="text-lg font-medium text-gray-900 mb-1">{emptyMessage}</h3>
        <p className="text-gray-500 mb-4">Get started by creating your first template</p>
        {emptyAction && (
          <button onClick={emptyAction.onClick} className="btn-primary">
            {emptyAction.label}
          </button>
        )}
      </div>
    );
  }

  if (variant === 'list') {
    return (
      <div className="space-y-3">
        {templates.map((template) => (
          <TemplateListItem
            key={template.id}
            template={template}
            onEdit={onEdit}
            onDelete={onDelete}
            onDuplicate={onDuplicate}
            onShare={onShare}
            onPreview={onPreview}
            onApply={onApply}
          />
        ))}
      </div>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {templates.map((template) => (
        <TemplateCard
          key={template.id}
          template={template}
          onEdit={onEdit ? () => onEdit(template) : undefined}
          onDelete={onDelete ? () => onDelete(template) : undefined}
          onDuplicate={onDuplicate ? () => onDuplicate(template) : undefined}
          onShare={onShare ? () => onShare(template) : undefined}
          onPreview={onPreview ? () => onPreview(template) : undefined}
          onApply={onApply ? () => onApply(template) : undefined}
        />
      ))}
    </div>
  );
}

interface TemplateListItemProps {
  template: ScheduleTemplate;
  onEdit?: (template: ScheduleTemplate) => void;
  onDelete?: (template: ScheduleTemplate) => void;
  onDuplicate?: (template: ScheduleTemplate) => void;
  onShare?: (template: ScheduleTemplate) => void;
  onPreview?: (template: ScheduleTemplate) => void;
  onApply?: (template: ScheduleTemplate) => void;
}

function TemplateListItem({
  template,
  onEdit,
  onDelete,
  onDuplicate,

  onPreview,
  onApply,
}: TemplateListItemProps) {
  const activityColors: Record<string, string> = {
    schedule: 'bg-blue-100 text-blue-700',
    assignment: 'bg-green-100 text-green-700',
    rotation: 'bg-purple-100 text-purple-700',
    call: 'bg-orange-100 text-orange-700',
    clinic: 'bg-teal-100 text-teal-700',
    custom: 'bg-gray-100 text-gray-700',
  };

  const colorClass = activityColors[template.category] || 'bg-gray-100 text-gray-700';

  return (
    <div
      className="flex items-center justify-between p-4 bg-white border rounded-lg hover:shadow-md transition-shadow cursor-pointer"
      onClick={() => onPreview?.(template)}
    >
      <div className="flex items-center gap-4 flex-1 min-w-0">
        <span className={`px-2 py-1 rounded text-xs font-medium ${colorClass}`}>
          {template.category}
        </span>
        <div className="flex-1 min-w-0">
          <h3 className="font-medium text-gray-900 truncate">{template.name}</h3>
          {template.description && (
            <p className="text-sm text-gray-500 truncate">{template.description}</p>
          )}
        </div>
        <div className="flex items-center gap-4 text-sm text-gray-500">
          <span>{template.durationWeeks}w</span>
          <span>{template.patterns.length} patterns</span>
        </div>
      </div>

      <div className="flex items-center gap-2 ml-4">
        {onApply && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onApply(template);
            }}
            className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
            aria-label={`Apply template ${template.name}`}
          >
            Apply
          </button>
        )}
        {onEdit && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onEdit(template);
            }}
            className="px-3 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded"
            aria-label={`Edit template ${template.name}`}
          >
            Edit
          </button>
        )}
        {onDuplicate && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDuplicate(template);
            }}
            className="px-3 py-1 text-sm text-gray-600 hover:bg-gray-50 rounded"
            aria-label={`Duplicate template ${template.name}`}
          >
            Duplicate
          </button>
        )}
        {onDelete && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDelete(template);
            }}
            className="px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded"
            aria-label={`Delete template ${template.name}`}
          >
            Delete
          </button>
        )}
      </div>
    </div>
  );
}

function TemplateCardSkeleton({ variant }: { variant: 'grid' | 'list' }) {
  if (variant === 'list') {
    return (
      <div className="flex items-center gap-4 p-4 bg-white border rounded-lg animate-pulse">
        <div className="w-20 h-6 bg-gray-200 rounded"></div>
        <div className="flex-1 space-y-2">
          <div className="w-1/3 h-4 bg-gray-200 rounded"></div>
          <div className="w-2/3 h-3 bg-gray-200 rounded"></div>
        </div>
        <div className="flex gap-2">
          <div className="w-16 h-8 bg-gray-200 rounded"></div>
          <div className="w-16 h-8 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="card animate-pulse">
      <div className="flex justify-between mb-3">
        <div className="space-y-2">
          <div className="w-32 h-4 bg-gray-200 rounded"></div>
          <div className="w-20 h-5 bg-gray-200 rounded"></div>
        </div>
        <div className="w-6 h-6 bg-gray-200 rounded"></div>
      </div>
      <div className="w-full h-3 bg-gray-200 rounded mb-3"></div>
      <div className="w-3/4 h-3 bg-gray-200 rounded mb-3"></div>
      <div className="flex gap-1 mb-3">
        {Array.from({ length: 7 }).map((_, i) => (
          <div key={i} className="flex-1 h-6 bg-gray-200 rounded"></div>
        ))}
      </div>
      <div className="flex gap-1">
        <div className="w-12 h-5 bg-gray-200 rounded"></div>
        <div className="w-12 h-5 bg-gray-200 rounded"></div>
      </div>
    </div>
  );
}

interface PredefinedTemplateCardProps {
  template: {
    templateKey: string;
    name: string;
    description?: string;
    category: string;
    patterns: unknown[];
    durationWeeks: number;
    tags: string[];
  };
  onImport: (templateKey: string) => void;
  isImporting?: boolean;
}

export function PredefinedTemplateCard({
  template,
  onImport,
  isImporting = false,
}: PredefinedTemplateCardProps) {
  const categoryColors: Record<string, { bg: string; text: string }> = {
    schedule: { bg: 'bg-blue-50', text: 'text-blue-700' },
    assignment: { bg: 'bg-green-50', text: 'text-green-700' },
    rotation: { bg: 'bg-purple-50', text: 'text-purple-700' },
    call: { bg: 'bg-orange-50', text: 'text-orange-700' },
    clinic: { bg: 'bg-teal-50', text: 'text-teal-700' },
    custom: { bg: 'bg-gray-50', text: 'text-gray-700' },
  };

  const colors = categoryColors[template.category] || categoryColors.custom;

  return (
    <div className={`p-4 border rounded-lg ${colors.bg}`}>
      <div className="flex items-start justify-between mb-2">
        <div>
          <h3 className={`font-medium ${colors.text}`}>{template.name}</h3>
          <span className="text-xs text-gray-500 capitalize">{template.category}</span>
        </div>
        <span className="px-2 py-0.5 bg-white border rounded text-xs text-gray-600">
          System
        </span>
      </div>

      {template.description && (
        <p className="text-sm text-gray-600 mb-3">{template.description}</p>
      )}

      <div className="flex items-center justify-between text-sm text-gray-500 mb-3">
        <span>{template.durationWeeks} week{template.durationWeeks !== 1 ? 's' : ''}</span>
        <span>{template.patterns.length} patterns</span>
      </div>

      {template.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {template.tags.slice(0, 3).map((tag) => (
            <span
              key={tag}
              className="px-1.5 py-0.5 bg-white text-gray-600 rounded text-xs"
            >
              #{tag}
            </span>
          ))}
        </div>
      )}

      <button
        onClick={() => onImport(template.templateKey)}
        disabled={isImporting}
        className={`w-full flex items-center justify-center gap-2 px-3 py-2 rounded ${colors.text} bg-white hover:bg-gray-50 border disabled:opacity-50`}
        aria-label={`Import ${template.name} to library`}
      >
        <Download className="w-4 h-4" aria-hidden="true" />
        {isImporting ? 'Importing...' : 'Import to Library'}
      </button>
    </div>
  );
}
