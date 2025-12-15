'use client';

import { useState, FormEvent } from 'react';
import { Modal } from './Modal';
import { Select, DatePicker } from './forms';
import { useGenerateSchedule } from '@/lib/hooks';
import { CheckCircle, XCircle, AlertTriangle, Loader2 } from 'lucide-react';

interface GenerateScheduleDialogProps {
  isOpen: boolean;
  onClose: () => void;
  defaultStartDate?: string;
  defaultEndDate?: string;
}

interface FormErrors {
  start_date?: string;
  end_date?: string;
  general?: string;
}

const algorithmOptions = [
  { value: 'greedy', label: 'Greedy (Fast)', description: 'Quick heuristic, good for initial solutions' },
  { value: 'cp_sat', label: 'CP-SAT (Optimal)', description: 'OR-Tools constraint solver, guarantees ACGME compliance' },
  { value: 'pulp', label: 'PuLP (Large Scale)', description: 'Linear programming, efficient for large problems' },
  { value: 'hybrid', label: 'Hybrid (Best Quality)', description: 'Combines solvers for optimal results' },
];

const pgyLevelOptions = [
  { value: 'all', label: 'All PGY Levels' },
  { value: '1', label: 'PGY-1 Only' },
  { value: '2', label: 'PGY-2 Only' },
  { value: '3', label: 'PGY-3 Only' },
];

const timeoutOptions = [
  { value: '30', label: '30 seconds (Quick)' },
  { value: '60', label: '60 seconds (Standard)' },
  { value: '120', label: '2 minutes (Extended)' },
  { value: '300', label: '5 minutes (Maximum)' },
];

type Algorithm = 'greedy' | 'cp_sat' | 'pulp' | 'hybrid';

export function GenerateScheduleDialog({
  isOpen,
  onClose,
  defaultStartDate,
  defaultEndDate,
}: GenerateScheduleDialogProps) {
  const [startDate, setStartDate] = useState(defaultStartDate || '');
  const [endDate, setEndDate] = useState(defaultEndDate || '');
  const [algorithm, setAlgorithm] = useState<Algorithm>('greedy');
  const [timeout, setTimeout] = useState('60');
  const [pgyLevelFilter, setPgyLevelFilter] = useState('all');
  const [errors, setErrors] = useState<FormErrors>({});
  const [showResults, setShowResults] = useState(false);

  const generateSchedule = useGenerateSchedule();

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!startDate) {
      newErrors.start_date = 'Start date is required';
    }

    if (!endDate) {
      newErrors.end_date = 'End date is required';
    }

    if (startDate && endDate && new Date(startDate) > new Date(endDate)) {
      newErrors.end_date = 'End date must be after start date';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    const pgyLevels = pgyLevelFilter === 'all'
      ? undefined
      : [parseInt(pgyLevelFilter)];

    try {
      await generateSchedule.mutateAsync({
        start_date: startDate,
        end_date: endDate,
        algorithm,
        timeout_seconds: parseFloat(timeout),
        pgy_levels: pgyLevels,
      });
      setShowResults(true);
    } catch (err) {
      setErrors({ general: 'Failed to generate schedule. Please try again.' });
    }
  };

  const handleClose = () => {
    setStartDate(defaultStartDate || '');
    setEndDate(defaultEndDate || '');
    setAlgorithm('greedy');
    setTimeout('60');
    setPgyLevelFilter('all');
    setErrors({});
    setShowResults(false);
    generateSchedule.reset();
    onClose();
  };

  const result = generateSchedule.data;
  const isGenerating = generateSchedule.isPending;

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Generate Schedule">
      {showResults && result ? (
        <div className="space-y-4">
          {/* Result Status */}
          <div className={`p-4 rounded-lg flex items-start gap-3 ${
            result.status === 'success'
              ? 'bg-green-50 border border-green-200'
              : result.status === 'partial'
              ? 'bg-amber-50 border border-amber-200'
              : 'bg-red-50 border border-red-200'
          }`}>
            {result.status === 'success' ? (
              <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
            ) : result.status === 'partial' ? (
              <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
            ) : (
              <XCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            )}
            <div>
              <p className={`font-medium ${
                result.status === 'success'
                  ? 'text-green-800'
                  : result.status === 'partial'
                  ? 'text-amber-800'
                  : 'text-red-800'
              }`}>
                {result.status === 'success'
                  ? 'Schedule Generated Successfully'
                  : result.status === 'partial'
                  ? 'Partial Schedule Generated'
                  : 'Schedule Generation Failed'}
              </p>
              <p className="text-sm mt-1 text-gray-600">{result.message}</p>
            </div>
          </div>

          {/* Statistics */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-sm text-gray-500">Blocks Assigned</p>
              <p className="text-2xl font-bold">{result.total_blocks_assigned}/{result.total_blocks}</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-sm text-gray-500">Coverage Rate</p>
              <p className="text-2xl font-bold">
                {result.validation?.coverage_rate
                  ? `${result.validation.coverage_rate.toFixed(0)}%`
                  : '--'}
              </p>
            </div>
          </div>

          {/* Solver Statistics */}
          {result.solver_stats && (
            <div className="bg-blue-50 rounded-lg p-3 text-sm">
              <p className="font-medium text-blue-800 mb-1">Solver Details</p>
              <div className="grid grid-cols-2 gap-2 text-blue-700">
                {result.solver_stats.total_residents && (
                  <p>Residents: {result.solver_stats.total_residents}</p>
                )}
                {result.solver_stats.coverage_rate != null && (
                  <p>Solver Coverage: {(result.solver_stats.coverage_rate * 100).toFixed(1)}%</p>
                )}
                {result.solver_stats.branches != null && (
                  <p>Branches: {result.solver_stats.branches.toLocaleString()}</p>
                )}
                {result.solver_stats.conflicts != null && (
                  <p>Conflicts: {result.solver_stats.conflicts.toLocaleString()}</p>
                )}
              </div>
            </div>
          )}

          {/* Validation Summary */}
          {result.validation && (
            <div className="border-t pt-4">
              <h4 className="font-medium mb-2">Validation Results</h4>
              {result.validation.valid ? (
                <p className="text-sm text-green-600 flex items-center gap-2">
                  <CheckCircle className="w-4 h-4" />
                  All ACGME requirements met
                </p>
              ) : (
                <div>
                  <p className="text-sm text-amber-600 mb-2">
                    {result.validation.total_violations} violation(s) found
                  </p>
                  <div className="max-h-32 overflow-y-auto space-y-1">
                    {result.validation.violations?.slice(0, 5).map((v, i) => (
                      <p key={i} className="text-xs text-gray-600">
                        • {v.message}
                      </p>
                    ))}
                    {result.validation.violations?.length > 5 && (
                      <p className="text-xs text-gray-500 italic">
                        And {result.validation.violations.length - 5} more...
                      </p>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={() => setShowResults(false)}
              className="btn-secondary"
            >
              Generate Another
            </button>
            <button
              type="button"
              onClick={handleClose}
              className="btn-primary"
            >
              Done
            </button>
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          {errors.general && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-md text-red-700 text-sm">
              {errors.general}
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <DatePicker
              label="Start Date"
              value={startDate}
              onChange={setStartDate}
              error={errors.start_date}
            />
            <DatePicker
              label="End Date"
              value={endDate}
              onChange={setEndDate}
              error={errors.end_date}
            />
          </div>

          <div>
            <Select
              label="Algorithm"
              value={algorithm}
              onChange={(e) => setAlgorithm(e.target.value as Algorithm)}
              options={algorithmOptions}
            />
            <p className="text-xs text-gray-500 mt-1">
              {algorithmOptions.find(a => a.value === algorithm)?.description}
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Select
              label="Solver Timeout"
              value={timeout}
              onChange={(e) => setTimeout(e.target.value)}
              options={timeoutOptions}
            />
            <Select
              label="PGY Level Filter"
              value={pgyLevelFilter}
              onChange={(e) => setPgyLevelFilter(e.target.value)}
              options={pgyLevelOptions}
            />
          </div>

          {/* Progress Indicator */}
          {isGenerating && (
            <div className="flex items-center justify-center py-4 bg-blue-50 rounded-lg">
              <Loader2 className="w-5 h-5 animate-spin text-blue-600 mr-2" />
              <span className="text-blue-700">Generating schedule...</span>
            </div>
          )}

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={handleClose}
              className="btn-secondary"
              disabled={isGenerating}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isGenerating}
              className="btn-primary disabled:opacity-50"
            >
              {isGenerating ? 'Generating...' : 'Generate Schedule'}
            </button>
          </div>
        </form>
      )}
    </Modal>
  );
}
