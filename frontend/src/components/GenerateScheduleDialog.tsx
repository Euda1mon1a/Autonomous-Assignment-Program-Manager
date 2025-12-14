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
  { value: 'greedy', label: 'Greedy (Fast)' },
  { value: 'min_conflicts', label: 'Min Conflicts (Balanced)' },
  { value: 'cp_sat', label: 'CP-SAT (Optimal)' },
];

const pgyLevelOptions = [
  { value: 'all', label: 'All PGY Levels' },
  { value: '1', label: 'PGY-1 Only' },
  { value: '2', label: 'PGY-2 Only' },
  { value: '3', label: 'PGY-3 Only' },
];

type Algorithm = 'greedy' | 'min_conflicts' | 'cp_sat';

export function GenerateScheduleDialog({
  isOpen,
  onClose,
  defaultStartDate,
  defaultEndDate,
}: GenerateScheduleDialogProps) {
  const [startDate, setStartDate] = useState(defaultStartDate || '');
  const [endDate, setEndDate] = useState(defaultEndDate || '');
  const [algorithm, setAlgorithm] = useState<Algorithm>('greedy');
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

          <Select
            label="Algorithm"
            value={algorithm}
            onChange={(e) => setAlgorithm(e.target.value as Algorithm)}
            options={algorithmOptions}
          />

          <Select
            label="PGY Level Filter"
            value={pgyLevelFilter}
            onChange={(e) => setPgyLevelFilter(e.target.value)}
            options={pgyLevelOptions}
          />

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
