'use client';

import { useState } from 'react';
import { Plus, Trash2, Copy, GripVertical, ChevronDown, ChevronUp } from 'lucide-react';
import type { AssignmentPattern } from '../types';
import {
  DAY_OF_WEEK_LABELS,
  ACTIVITY_TYPE_OPTIONS,
  ROLE_OPTIONS,
  TIME_OF_DAY_OPTIONS,
} from '../constants';

interface PatternEditorProps {
  patterns: AssignmentPattern[];
  onAdd: (pattern: Omit<AssignmentPattern, 'id'>) => void;
  onUpdate: (id: string, updates: Partial<AssignmentPattern>) => void;
  onRemove: (id: string) => void;
  onDuplicate: (id: string) => void;
  onReorder?: (startIndex: number, endIndex: number) => void;
  readOnly?: boolean;
}

export function PatternEditor({
  patterns,
  onAdd,
  onUpdate,
  onRemove,
  onDuplicate,
  readOnly = false,
}: PatternEditorProps) {
  const [expandedPatterns, setExpandedPatterns] = useState<Set<string>>(new Set());
  const [showAddForm, setShowAddForm] = useState(false);

  const toggleExpanded = (id: string) => {
    setExpandedPatterns((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const handleAddPattern = (pattern: Omit<AssignmentPattern, 'id'>) => {
    onAdd(pattern);
    setShowAddForm(false);
  };

  // Group patterns by day
  const patternsByDay = patterns.reduce((acc, pattern) => {
    const day = pattern.dayOfWeek;
    if (!acc[day]) acc[day] = [];
    acc[day].push(pattern);
    return acc;
  }, {} as Record<number, AssignmentPattern[]>);

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h3 className="font-medium text-gray-900">
          Assignment Patterns ({patterns.length})
        </h3>
        {!readOnly && (
          <button
            onClick={() => setShowAddForm(true)}
            className="btn-secondary flex items-center gap-2 text-sm"
            aria-label="Add new pattern"
          >
            <Plus className="w-4 h-4" aria-hidden="true" />
            Add Pattern
          </button>
        )}
      </div>

      {/* Add Pattern Form */}
      {showAddForm && (
        <PatternForm
          onSubmit={handleAddPattern}
          onCancel={() => setShowAddForm(false)}
        />
      )}

      {/* Pattern List */}
      {patterns.length === 0 ? (
        <div className="text-center py-8 text-gray-500 bg-gray-50 rounded-lg border-2 border-dashed">
          <p>No patterns defined yet</p>
          <p className="text-sm mt-1">Add patterns to define the assignment schedule</p>
        </div>
      ) : (
        <div className="space-y-2">
          {DAY_OF_WEEK_LABELS.map((dayName, dayIndex) => {
            const dayPatterns = patternsByDay[dayIndex] || [];
            if (dayPatterns.length === 0) return null;

            return (
              <div key={dayIndex} className="border rounded-lg overflow-hidden">
                <div className="bg-gray-50 px-3 py-2 font-medium text-sm text-gray-700 border-b">
                  {dayName} ({dayPatterns.length} pattern{dayPatterns.length !== 1 ? 's' : ''})
                </div>
                <div className="divide-y">
                  {dayPatterns.map((pattern) => (
                    <PatternItem
                      key={pattern.id}
                      pattern={pattern}
                      isExpanded={expandedPatterns.has(pattern.id)}
                      onToggle={() => toggleExpanded(pattern.id)}
                      onUpdate={(updates) => onUpdate(pattern.id, updates)}
                      onRemove={() => onRemove(pattern.id)}
                      onDuplicate={() => onDuplicate(pattern.id)}
                      readOnly={readOnly}
                    />
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Quick Add Buttons */}
      {!readOnly && patterns.length > 0 && (
        <QuickAddPatterns onAdd={onAdd} existingPatterns={patterns} />
      )}
    </div>
  );
}

interface PatternItemProps {
  pattern: AssignmentPattern;
  isExpanded: boolean;
  onToggle: () => void;
  onUpdate: (updates: Partial<AssignmentPattern>) => void;
  onRemove: () => void;
  onDuplicate: () => void;
  readOnly?: boolean;
}

function PatternItem({
  pattern,
  isExpanded,
  onToggle,
  onUpdate,
  onRemove,
  onDuplicate,
  readOnly,
}: PatternItemProps) {
  const activityColors: Record<string, string> = {
    clinic: 'bg-blue-100 text-blue-700',
    inpatient: 'bg-purple-100 text-purple-700',
    procedure: 'bg-red-100 text-red-700',
    conference: 'bg-gray-100 text-gray-700',
    elective: 'bg-green-100 text-green-700',
    call: 'bg-orange-100 text-orange-700',
  };

  const colorClass = activityColors[pattern.activityType] || 'bg-gray-100 text-gray-700';

  return (
    <div className="p-3">
      <div className="flex items-center gap-3">
        {!readOnly && (
          <GripVertical className="w-4 h-4 text-gray-400 cursor-grab" aria-hidden="true" />
        )}

        <button
          onClick={onToggle}
          className="flex-1 flex items-center gap-3 text-left"
          aria-expanded={isExpanded}
          aria-label={`${isExpanded ? 'Collapse' : 'Expand'} pattern ${pattern.name}`}
        >
          <span className={`px-2 py-1 rounded text-xs font-medium ${colorClass}`}>
            {pattern.activityType}
          </span>
          <span className="font-medium text-gray-900">{pattern.name}</span>
          <span className="text-sm text-gray-500">
            {pattern.timeOfDay === 'ALL' ? 'All Day' : pattern.timeOfDay}
          </span>
          <span className="text-xs text-gray-400 capitalize">({pattern.role})</span>
          {isExpanded ? (
            <ChevronUp className="w-4 h-4 text-gray-400 ml-auto" aria-hidden="true" />
          ) : (
            <ChevronDown className="w-4 h-4 text-gray-400 ml-auto" aria-hidden="true" />
          )}
        </button>

        {!readOnly && (
          <div className="flex gap-1">
            <button
              onClick={onDuplicate}
              className="p-1 hover:bg-gray-100 rounded text-gray-500"
              aria-label="Duplicate pattern"
              title="Duplicate"
            >
              <Copy className="w-4 h-4" aria-hidden="true" />
            </button>
            <button
              onClick={onRemove}
              className="p-1 hover:bg-red-50 rounded text-red-500"
              aria-label="Remove pattern"
              title="Remove"
            >
              <Trash2 className="w-4 h-4" aria-hidden="true" />
            </button>
          </div>
        )}
      </div>

      {isExpanded && (
        <div className="mt-3 pl-7 space-y-3">
          {readOnly ? (
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Day:</span>{' '}
                <span className="font-medium">
                  {DAY_OF_WEEK_LABELS[pattern.dayOfWeek]}
                </span>
              </div>
              <div>
                <span className="text-gray-500">Time:</span>{' '}
                <span className="font-medium">{pattern.timeOfDay}</span>
              </div>
              <div>
                <span className="text-gray-500">Activity:</span>{' '}
                <span className="font-medium">{pattern.activityType}</span>
              </div>
              <div>
                <span className="text-gray-500">Role:</span>{' '}
                <span className="font-medium capitalize">{pattern.role}</span>
              </div>
              {pattern.requiredPgyLevels && pattern.requiredPgyLevels.length > 0 && (
                <div className="col-span-2">
                  <span className="text-gray-500">Required PGY Levels:</span>{' '}
                  <span className="font-medium">
                    {pattern.requiredPgyLevels.join(', ')}
                  </span>
                </div>
              )}
              {pattern.notes && (
                <div className="col-span-2">
                  <span className="text-gray-500">Notes:</span>{' '}
                  <span className="font-medium">{pattern.notes}</span>
                </div>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm text-gray-600 mb-1">Name</label>
                <input
                  type="text"
                  value={pattern.name}
                  onChange={(e) => onUpdate({ name: e.target.value })}
                  className="w-full px-2 py-1.5 border rounded text-sm"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">Time</label>
                <select
                  value={pattern.timeOfDay}
                  onChange={(e) =>
                    onUpdate({ timeOfDay: e.target.value as 'AM' | 'PM' | 'ALL' })
                  }
                  className="w-full px-2 py-1.5 border rounded text-sm"
                >
                  {TIME_OF_DAY_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">Activity</label>
                <select
                  value={pattern.activityType}
                  onChange={(e) => onUpdate({ activityType: e.target.value })}
                  className="w-full px-2 py-1.5 border rounded text-sm"
                >
                  {ACTIVITY_TYPE_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">Role</label>
                <select
                  value={pattern.role}
                  onChange={(e) =>
                    onUpdate({ role: e.target.value as 'primary' | 'supervising' | 'backup' })
                  }
                  className="w-full px-2 py-1.5 border rounded text-sm"
                >
                  {ROLE_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="col-span-2">
                <label className="block text-sm text-gray-600 mb-1">Notes</label>
                <input
                  type="text"
                  value={pattern.notes || ''}
                  onChange={(e) => onUpdate({ notes: e.target.value || undefined })}
                  placeholder="Optional notes..."
                  className="w-full px-2 py-1.5 border rounded text-sm"
                />
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

interface PatternFormProps {
  onSubmit: (pattern: Omit<AssignmentPattern, 'id'>) => void;
  onCancel: () => void;
  initialValues?: Partial<AssignmentPattern>;
}

function PatternForm({ onSubmit, onCancel, initialValues }: PatternFormProps) {
  const [name, setName] = useState(initialValues?.name || '');
  const [dayOfWeek, setDayOfWeek] = useState(initialValues?.dayOfWeek ?? 1);
  const [timeOfDay, setTimeOfDay] = useState<'AM' | 'PM' | 'ALL'>(
    initialValues?.timeOfDay || 'AM'
  );
  const [activityType, setActivityType] = useState(initialValues?.activityType || 'clinic');
  const [role, setRole] = useState<'primary' | 'supervising' | 'backup'>(
    initialValues?.role || 'primary'
  );
  const [notes, setNotes] = useState(initialValues?.notes || '');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    onSubmit({
      name: name.trim(),
      dayOfWeek,
      timeOfDay,
      activityType,
      role,
      notes: notes.trim() || undefined,
    });
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="p-4 bg-blue-50 border border-blue-200 rounded-lg space-y-4"
    >
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <div className="col-span-2 md:col-span-1">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Pattern Name
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g., Morning Clinic"
            className="w-full px-3 py-2 border rounded-lg"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Day of Week
          </label>
          <select
            value={dayOfWeek}
            onChange={(e) => setDayOfWeek(Number(e.target.value))}
            className="w-full px-3 py-2 border rounded-lg"
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
            Time of Day
          </label>
          <select
            value={timeOfDay}
            onChange={(e) => setTimeOfDay(e.target.value as 'AM' | 'PM' | 'ALL')}
            className="w-full px-3 py-2 border rounded-lg"
          >
            {TIME_OF_DAY_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Activity Type
          </label>
          <select
            value={activityType}
            onChange={(e) => setActivityType(e.target.value)}
            className="w-full px-3 py-2 border rounded-lg"
          >
            {ACTIVITY_TYPE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Role
          </label>
          <select
            value={role}
            onChange={(e) =>
              setRole(e.target.value as 'primary' | 'supervising' | 'backup')
            }
            className="w-full px-3 py-2 border rounded-lg"
          >
            {ROLE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Notes (optional)
          </label>
          <input
            type="text"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Optional notes..."
            className="w-full px-3 py-2 border rounded-lg"
          />
        </div>
      </div>

      <div className="flex justify-end gap-2">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
          aria-label="Cancel adding pattern"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={!name.trim()}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          aria-label="Add pattern"
        >
          Add Pattern
        </button>
      </div>
    </form>
  );
}

interface QuickAddPatternsProps {
  onAdd: (pattern: Omit<AssignmentPattern, 'id'>) => void;
  existingPatterns: AssignmentPattern[];
}

function QuickAddPatterns({ onAdd, existingPatterns }: QuickAddPatternsProps) {
  const suggestions = [
    { label: 'Add weekday mornings', days: [1, 2, 3, 4, 5], time: 'AM' as const },
    { label: 'Add weekday afternoons', days: [1, 2, 3, 4, 5], time: 'PM' as const },
    { label: 'Add weekend coverage', days: [0, 6], time: 'ALL' as const },
  ];

  const handleQuickAdd = (days: number[], time: 'AM' | 'PM' | 'ALL') => {
    days.forEach((day) => {
      // Check if pattern already exists
      const exists = existingPatterns.some(
        (p) => p.dayOfWeek === day && p.timeOfDay === time
      );
      if (!exists) {
        onAdd({
          name: `${DAY_OF_WEEK_LABELS[day]} ${time === 'ALL' ? 'Coverage' : time}`,
          dayOfWeek: day,
          timeOfDay: time,
          activityType: 'clinic',
          role: 'primary',
        });
      }
    });
  };

  return (
    <div className="border-t pt-4">
      <p className="text-sm text-gray-600 mb-2">Quick add patterns:</p>
      <div className="flex flex-wrap gap-2">
        {suggestions.map((suggestion) => (
          <button
            key={suggestion.label}
            onClick={() => handleQuickAdd(suggestion.days, suggestion.time)}
            className="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg text-gray-700"
            aria-label={suggestion.label}
          >
            {suggestion.label}
          </button>
        ))}
      </div>
    </div>
  );
}
