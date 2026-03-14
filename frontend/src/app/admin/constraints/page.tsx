'use client';

import { useState, useCallback } from 'react';
import {
  Settings,
  ToggleLeft,
  ToggleRight,
  Shield,
  AlertTriangle,
  Loader2,
} from 'lucide-react';
import {
  useConstraintConfigs,
  useUpdateConstraint,
} from '@/hooks/useAdminScheduling';
import { useConstraintCategories } from '@/hooks/useEnums';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import type { ConstraintConfig } from '@/types/admin-scheduling';

const PRIORITY_LABELS: Record<number, string> = {
  1: 'Critical',
  2: 'High',
  3: 'Medium',
  4: 'Low',
};

const PRIORITY_COLORS: Record<number, string> = {
  1: 'text-red-600 bg-red-50',
  2: 'text-orange-600 bg-orange-50',
  3: 'text-blue-600 bg-blue-50',
  4: 'text-gray-600 bg-gray-50',
};

export default function ConstraintConfigPage() {
  const { data: constraints, isLoading, error } = useConstraintConfigs();
  const { data: apiCategories } = useConstraintCategories();
  const updateMutation = useUpdateConstraint();
  const [filter, setFilter] = useState<string>('all');
  const [editingWeight, setEditingWeight] = useState<string | null>(null);
  const [weightValue, setWeightValue] = useState<string>('');

  const handleToggle = useCallback(
    (name: string, currentEnabled: boolean) => {
      updateMutation.mutate({ name, enabled: !currentEnabled });
    },
    [updateMutation],
  );

  const handleWeightSave = useCallback(
    (name: string) => {
      const weight = parseFloat(weightValue);
      if (!isNaN(weight) && weight >= 0) {
        updateMutation.mutate({ name, weight });
      }
      setEditingWeight(null);
    },
    [weightValue, updateMutation],
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 text-red-600">
        <AlertTriangle className="w-5 h-5 inline mr-2" />
        Failed to load constraints: {error.message}
      </div>
    );
  }

  const categories = apiCategories
    ? apiCategories.map((c) => c.value)
    : Array.from(new Set((constraints ?? []).map((c) => c.category))).sort();
  const filtered =
    filter === 'all'
      ? constraints ?? []
      : (constraints ?? []).filter((c) => c.category === filter);

  return (
    <ProtectedRoute requireAdmin>
      <div className="p-6 max-w-6xl mx-auto">
        <div className="flex items-center gap-3 mb-6">
          <Settings className="w-6 h-6 text-gray-700" />
          <h1 className="text-2xl font-bold text-gray-900">
            Constraint Configuration
          </h1>
        </div>

        <div className="mb-4 flex gap-2 flex-wrap">
          <button
            onClick={() => setFilter('all')}
            className={`px-3 py-1 rounded text-sm ${
              filter === 'all'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            All ({constraints?.length ?? 0})
          </button>
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setFilter(cat)}
              className={`px-3 py-1 rounded text-sm ${
                filter === cat
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Constraint
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Category
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Priority
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Weight
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                  Enabled
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {filtered.map((c) => (
                <ConstraintRow
                  key={c.name}
                  constraint={c}
                  isUpdating={updateMutation.isPending}
                  editingWeight={editingWeight}
                  weightValue={weightValue}
                  onToggle={handleToggle}
                  onStartEditWeight={(name, weight) => {
                    setEditingWeight(name);
                    setWeightValue(String(weight));
                  }}
                  onWeightChange={setWeightValue}
                  onWeightSave={handleWeightSave}
                  onWeightCancel={() => setEditingWeight(null)}
                />
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </ProtectedRoute>
  );
}

function ConstraintRow({
  constraint: c,
  isUpdating,
  editingWeight,
  weightValue,
  onToggle,
  onStartEditWeight,
  onWeightChange,
  onWeightSave,
  onWeightCancel,
}: {
  constraint: ConstraintConfig;
  isUpdating: boolean;
  editingWeight: string | null;
  weightValue: string;
  onToggle: (name: string, enabled: boolean) => void;
  onStartEditWeight: (name: string, weight: number) => void;
  onWeightChange: (value: string) => void;
  onWeightSave: (name: string) => void;
  onWeightCancel: () => void;
}) {
  const priorityLabel = PRIORITY_LABELS[c.priority] ?? 'Unknown';
  const priorityColor = PRIORITY_COLORS[c.priority] ?? 'text-gray-600 bg-gray-50';
  const isCritical = c.priority === 1;

  return (
    <tr className={`${!c.enabled ? 'opacity-60' : ''}`}>
      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          {isCritical && <Shield className="w-4 h-4 text-red-500" />}
          <div>
            <div className="font-medium text-gray-900 text-sm">{c.name}</div>
            {c.description && (
              <div className="text-xs text-gray-500">{c.description}</div>
            )}
          </div>
        </div>
      </td>
      <td className="px-4 py-3">
        <span className="text-xs font-medium text-gray-600 bg-gray-100 px-2 py-0.5 rounded">
          {c.category}
        </span>
      </td>
      <td className="px-4 py-3">
        <span
          className={`text-xs font-medium px-2 py-0.5 rounded ${priorityColor}`}
        >
          {priorityLabel}
        </span>
      </td>
      <td className="px-4 py-3">
        {editingWeight === c.name ? (
          <div className="flex items-center gap-1">
            <input
              type="number"
              value={weightValue}
              onChange={(e) => onWeightChange(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') onWeightSave(c.name);
                if (e.key === 'Escape') onWeightCancel();
              }}
              className="w-20 px-2 py-1 border rounded text-sm"
              min="0"
              step="0.1"
              autoFocus
            />
            <button
              onClick={() => onWeightSave(c.name)}
              className="text-xs text-blue-600 hover:text-blue-800"
            >
              Save
            </button>
          </div>
        ) : isCritical || c.weight === 1 ? (
          <span className="text-sm text-gray-400" title="Hard constraint — weight not editable">
            {c.weight}
          </span>
        ) : (
          <button
            onClick={() => onStartEditWeight(c.name, c.weight)}
            className="text-sm text-gray-700 hover:text-blue-600 hover:underline"
            title="Click to edit weight"
          >
            {c.weight}
          </button>
        )}
      </td>
      <td className="px-4 py-3 text-center">
        <button
          onClick={() => onToggle(c.name, c.enabled)}
          disabled={isUpdating || isCritical}
          className={`${isCritical ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'}`}
          title={
            isCritical
              ? 'Critical constraints cannot be disabled'
              : c.enabled
                ? 'Click to disable'
                : 'Click to enable'
          }
        >
          {c.enabled ? (
            <ToggleRight className="w-6 h-6 text-green-500" />
          ) : (
            <ToggleLeft className="w-6 h-6 text-gray-400" />
          )}
        </button>
      </td>
    </tr>
  );
}
