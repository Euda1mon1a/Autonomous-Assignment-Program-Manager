'use client';

import { useState } from 'react';
import { X, Save, Eye } from 'lucide-react';
import type {
  ScheduleTemplate,
  ScheduleTemplateCreate,
  ScheduleTemplateUpdate,
  TemplateCategory,
  TemplateVisibility,
  AssignmentPattern,
} from '../types';
import {
  TEMPLATE_CATEGORIES,
  VISIBILITY_OPTIONS,
  DEFAULT_TEMPLATE_VALUES,
  DAY_OF_WEEK_LABELS,
} from '../constants';
import { PatternEditor } from './PatternEditor';
import { usePatternEditor } from '../hooks';

interface TemplateEditorProps {
  template?: ScheduleTemplate | null;
  onSave: (data: ScheduleTemplateCreate | ScheduleTemplateUpdate) => Promise<void>;
  onCancel: () => void;
  onPreview?: (patterns: AssignmentPattern[]) => void;
  isLoading?: boolean;
}

export function TemplateEditor({
  template,
  onSave,
  onCancel,
  onPreview,
  isLoading = false,
}: TemplateEditorProps) {
  const isEditing = !!template;

  // Form state
  const [name, setName] = useState(template?.name || '');
  const [description, setDescription] = useState(template?.description || '');
  const [category, setCategory] = useState<TemplateCategory>(
    template?.category || DEFAULT_TEMPLATE_VALUES.category
  );
  const [visibility, setVisibility] = useState<TemplateVisibility>(
    template?.visibility || DEFAULT_TEMPLATE_VALUES.visibility
  );
  const [durationWeeks, setDurationWeeks] = useState(
    template?.durationWeeks || DEFAULT_TEMPLATE_VALUES.durationWeeks
  );
  const [startDayOfWeek, setStartDayOfWeek] = useState(
    template?.startDayOfWeek ?? DEFAULT_TEMPLATE_VALUES.startDayOfWeek
  );
  const [maxResidentsPerDay, setMaxResidentsPerDay] = useState(
    template?.maxResidentsPerDay?.toString() || ''
  );
  const [requiresSupervision, setRequiresSupervision] = useState(
    template?.requiresSupervision ?? DEFAULT_TEMPLATE_VALUES.requiresSupervision
  );
  const [allowWeekends, setAllowWeekends] = useState(
    template?.allowWeekends ?? DEFAULT_TEMPLATE_VALUES.allowWeekends
  );
  const [allowHolidays, setAllowHolidays] = useState(
    template?.allowHolidays ?? DEFAULT_TEMPLATE_VALUES.allowHolidays
  );
  const [tags, setTags] = useState(template?.tags?.join(', ') || '');

  // Pattern editor
  const patternEditor = usePatternEditor(template?.patterns || []);

  // Validation
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!name.trim()) {
      newErrors.name = 'Name is required';
    }

    if (durationWeeks < 1 || durationWeeks > 52) {
      newErrors.durationWeeks = 'Duration must be between 1 and 52 weeks';
    }

    if (maxResidentsPerDay && (parseInt(maxResidentsPerDay) < 1 || parseInt(maxResidentsPerDay) > 100)) {
      newErrors.maxResidentsPerDay = 'Max residents must be between 1 and 100';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) return;

    const tagsArray = tags
      .split(',')
      .map((t) => t.trim())
      .filter((t) => t.length > 0);

    const data: ScheduleTemplateCreate | ScheduleTemplateUpdate = {
      name: name.trim(),
      description: description.trim() || undefined,
      category,
      visibility,
      durationWeeks,
      startDayOfWeek,
      patterns: patternEditor.patterns,
      maxResidentsPerDay: maxResidentsPerDay ? parseInt(maxResidentsPerDay) : undefined,
      requiresSupervision,
      allowWeekends,
      allowHolidays,
      tags: tagsArray,
    };

    await onSave(data);
  };

  const handlePreview = () => {
    onPreview?.(patternEditor.patterns);
  };

  return (
    <div className="bg-white rounded-lg shadow-lg max-h-[90vh] overflow-hidden flex flex-col" role="dialog" aria-labelledby="template-editor-title" aria-modal="true">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <h2 id="template-editor-title" className="text-lg font-semibold">
          {isEditing ? 'Edit Template' : 'Create Template'}
        </h2>
        <button
          onClick={onCancel}
          className="p-1 hover:bg-gray-100 rounded"
          aria-label="Close"
        >
          <X className="w-5 h-5" aria-hidden="true" />
        </button>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto">
        <div className="p-4 space-y-6">
          {/* Basic Info Section */}
          <section>
            <h3 className="text-sm font-medium text-gray-700 mb-3">Basic Information</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Template Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g., Standard Weekly Clinic Schedule"
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                    errors.name ? 'border-red-500' : ''
                  }`}
                />
                {errors.name && (
                  <p className="mt-1 text-sm text-red-500">{errors.name}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Describe what this template is for..."
                  rows={3}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Category
                  </label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value as TemplateCategory)}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    {TEMPLATE_CATEGORIES.map((cat) => (
                      <option key={cat.id} value={cat.id}>
                        {cat.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Visibility
                  </label>
                  <select
                    value={visibility}
                    onChange={(e) => setVisibility(e.target.value as TemplateVisibility)}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    {VISIBILITY_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tags (comma-separated)
                </label>
                <input
                  type="text"
                  value={tags}
                  onChange={(e) => setTags(e.target.value)}
                  placeholder="e.g., clinic, weekday, primary-care"
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>
          </section>

          {/* Schedule Settings Section */}
          <section>
            <h3 className="text-sm font-medium text-gray-700 mb-3">Schedule Settings</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Duration (weeks) <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  value={durationWeeks}
                  onChange={(e) => setDurationWeeks(parseInt(e.target.value) || 1)}
                  min={1}
                  max={52}
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                    errors.durationWeeks ? 'border-red-500' : ''
                  }`}
                />
                {errors.durationWeeks && (
                  <p className="mt-1 text-sm text-red-500">{errors.durationWeeks}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Start Day
                </label>
                <select
                  value={startDayOfWeek}
                  onChange={(e) => setStartDayOfWeek(parseInt(e.target.value))}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  {DAY_OF_WEEK_LABELS.map((day, index) => (
                    <option key={index} value={index}>
                      {day}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Max Residents/Day
                </label>
                <input
                  type="number"
                  value={maxResidentsPerDay}
                  onChange={(e) => setMaxResidentsPerDay(e.target.value)}
                  placeholder="No limit"
                  min={1}
                  max={100}
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                    errors.maxResidentsPerDay ? 'border-red-500' : ''
                  }`}
                />
                {errors.maxResidentsPerDay && (
                  <p className="mt-1 text-sm text-red-500">{errors.maxResidentsPerDay}</p>
                )}
              </div>
            </div>

            {/* Checkboxes */}
            <div className="mt-4 space-y-2">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={requiresSupervision}
                  onChange={(e) => setRequiresSupervision(e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700">Requires supervision</span>
              </label>

              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={allowWeekends}
                  onChange={(e) => setAllowWeekends(e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700">Allow weekend assignments</span>
              </label>

              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={allowHolidays}
                  onChange={(e) => setAllowHolidays(e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700">Allow holiday assignments</span>
              </label>
            </div>
          </section>

          {/* Patterns Section */}
          <section>
            <PatternEditor
              patterns={patternEditor.patterns}
              onAdd={patternEditor.addPattern}
              onUpdate={patternEditor.updatePattern}
              onRemove={patternEditor.removePattern}
              onDuplicate={patternEditor.duplicatePattern}
              onReorder={patternEditor.reorderPatterns}
            />
          </section>
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-white border-t p-4 flex justify-between items-center">
          <div>
            {patternEditor.patterns.length > 0 && onPreview && (
              <button
                type="button"
                onClick={handlePreview}
                className="flex items-center gap-2 px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
                aria-label="Preview template"
              >
                <Eye className="w-4 h-4" aria-hidden="true" />
                Preview
              </button>
            )}
          </div>
          <div className="flex gap-3">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
              aria-label="Cancel"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              aria-label={isEditing ? 'Save template changes' : 'Create new template'}
            >
              <Save className="w-4 h-4" aria-hidden="true" />
              {isLoading ? 'Saving...' : isEditing ? 'Save Changes' : 'Create Template'}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
