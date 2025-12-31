/**
 * SwapRequestForm Component
 *
 * Form for creating schedule swap requests
 */

import React, { useState } from 'react';
import { ShiftIndicator } from '../schedule/ShiftIndicator';
import { RotationBadge } from '../schedule/RotationBadge';

export interface SwapRequestData {
  requestorPersonId: string;
  givingUpBlockId: string;
  swapType: 'one-to-one' | 'absorb' | 'give-away';
  targetPersonId?: string; // Required for one-to-one
  targetBlockId?: string; // Required for one-to-one
  reason: string;
  notes?: string;
}

export interface BlockDetails {
  id: string;
  date: string;
  shift: 'AM' | 'PM' | 'Night';
  rotationType: string;
  personName: string;
}

export interface SwapRequestFormProps {
  currentUserBlocks: BlockDetails[];
  availablePersons: Array<{ id: string; name: string; role: string }>;
  getAvailableBlocksForPerson: (personId: string) => Promise<BlockDetails[]>;
  onSubmit: (data: SwapRequestData) => Promise<void>;
  onCancel: () => void;
  className?: string;
}

export const SwapRequestForm: React.FC<SwapRequestFormProps> = ({
  currentUserBlocks,
  availablePersons,
  getAvailableBlocksForPerson,
  onSubmit,
  onCancel,
  className = '',
}) => {
  const [swapType, setSwapType] = useState<'one-to-one' | 'absorb' | 'give-away'>('one-to-one');
  const [givingUpBlockId, setGivingUpBlockId] = useState('');
  const [targetPersonId, setTargetPersonId] = useState('');
  const [targetBlockId, setTargetBlockId] = useState('');
  const [reason, setReason] = useState('');
  const [notes, setNotes] = useState('');
  const [targetBlocks, setTargetBlocks] = useState<BlockDetails[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleTargetPersonChange = async (personId: string) => {
    setTargetPersonId(personId);
    setTargetBlockId('');
    setError('');

    if (personId && swapType === 'one-to-one') {
      setIsLoading(true);
      try {
        const blocks = await getAvailableBlocksForPerson(personId);
        setTargetBlocks(blocks);
      } catch (err) {
        setError('Failed to load available blocks');
        setTargetBlocks([]);
      } finally {
        setIsLoading(false);
      }
    } else {
      setTargetBlocks([]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Validation
    if (!givingUpBlockId) {
      setError('Please select a block to give up');
      return;
    }

    if (!reason.trim()) {
      setError('Please provide a reason for the swap');
      return;
    }

    if (swapType === 'one-to-one' && (!targetPersonId || !targetBlockId)) {
      setError('Please select a target person and block for one-to-one swap');
      return;
    }

    const requestData: SwapRequestData = {
      requestorPersonId: '', // Should come from auth context
      givingUpBlockId,
      swapType,
      targetPersonId: swapType === 'one-to-one' ? targetPersonId : undefined,
      targetBlockId: swapType === 'one-to-one' ? targetBlockId : undefined,
      reason: reason.trim(),
      notes: notes.trim() || undefined,
    };

    setIsLoading(true);
    try {
      await onSubmit(requestData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create swap request');
    } finally {
      setIsLoading(false);
    }
  };

  const selectedGivingUpBlock = currentUserBlocks.find(b => b.id === givingUpBlockId);
  const selectedTargetBlock = targetBlocks.find(b => b.id === targetBlockId);

  return (
    <form
      onSubmit={handleSubmit}
      className={`swap-request-form bg-white rounded-lg shadow-lg p-6 ${className}`}
    >
      <h2 className="text-2xl font-bold mb-6">Create Swap Request</h2>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-300 rounded-lg text-red-800">
          {error}
        </div>
      )}

      {/* Swap Type Selection */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Swap Type
        </label>
        <div className="grid grid-cols-3 gap-4">
          <button
            type="button"
            onClick={() => setSwapType('one-to-one')}
            className={`
              p-4 border-2 rounded-lg text-center transition-all
              ${swapType === 'one-to-one'
                ? 'border-blue-600 bg-blue-50 text-blue-900'
                : 'border-gray-300 hover:border-gray-400'
              }
              focus:outline-none focus:ring-2 focus:ring-blue-500
            `}
          >
            <div className="text-2xl mb-2">🔄</div>
            <div className="font-semibold">One-to-One</div>
            <div className="text-xs text-gray-600 mt-1">Exchange shifts with another person</div>
          </button>

          <button
            type="button"
            onClick={() => setSwapType('absorb')}
            className={`
              p-4 border-2 rounded-lg text-center transition-all
              ${swapType === 'absorb'
                ? 'border-blue-600 bg-blue-50 text-blue-900'
                : 'border-gray-300 hover:border-gray-400'
              }
              focus:outline-none focus:ring-2 focus:ring-blue-500
            `}
          >
            <div className="text-2xl mb-2">📥</div>
            <div className="font-semibold">Absorb</div>
            <div className="text-xs text-gray-600 mt-1">Take someone's shift</div>
          </button>

          <button
            type="button"
            onClick={() => setSwapType('give-away')}
            className={`
              p-4 border-2 rounded-lg text-center transition-all
              ${swapType === 'give-away'
                ? 'border-blue-600 bg-blue-50 text-blue-900'
                : 'border-gray-300 hover:border-gray-400'
              }
              focus:outline-none focus:ring-2 focus:ring-blue-500
            `}
          >
            <div className="text-2xl mb-2">📤</div>
            <div className="font-semibold">Give Away</div>
            <div className="text-xs text-gray-600 mt-1">Give up your shift</div>
          </button>
        </div>
      </div>

      {/* Block to Give Up */}
      <div className="mb-6">
        <label htmlFor="giving-up-block" className="block text-sm font-medium text-gray-700 mb-2">
          Block to Give Up *
        </label>
        <select
          id="giving-up-block"
          value={givingUpBlockId}
          onChange={(e) => setGivingUpBlockId(e.target.value)}
          required
          className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Select a block...</option>
          {currentUserBlocks.map(block => (
            <option key={block.id} value={block.id}>
              {new Date(block.date).toLocaleDateString()} - {block.shift} - {block.rotationType}
            </option>
          ))}
        </select>

        {selectedGivingUpBlock && (
          <div className="mt-2 p-3 bg-gray-50 rounded border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium">{new Date(selectedGivingUpBlock.date).toLocaleDateString()}</div>
                <div className="text-sm text-gray-600">{selectedGivingUpBlock.personName}</div>
              </div>
              <div className="flex items-center gap-2">
                <ShiftIndicator shift={selectedGivingUpBlock.shift} size="sm" variant="badge" />
                <RotationBadge rotationType={selectedGivingUpBlock.rotationType} size="sm" />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Target Person & Block (for one-to-one swaps) */}
      {swapType === 'one-to-one' && (
        <>
          <div className="mb-6">
            <label htmlFor="target-person" className="block text-sm font-medium text-gray-700 mb-2">
              Swap With *
            </label>
            <select
              id="target-person"
              value={targetPersonId}
              onChange={(e) => handleTargetPersonChange(e.target.value)}
              required
              className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select a person...</option>
              {availablePersons.map(person => (
                <option key={person.id} value={person.id}>
                  {person.name} ({person.role})
                </option>
              ))}
            </select>
          </div>

          {targetPersonId && (
            <div className="mb-6">
              <label htmlFor="target-block" className="block text-sm font-medium text-gray-700 mb-2">
                Their Block *
              </label>
              {isLoading ? (
                <div className="text-center py-4 text-gray-500">Loading available blocks...</div>
              ) : targetBlocks.length === 0 ? (
                <div className="p-4 bg-yellow-50 border border-yellow-200 rounded text-yellow-800 text-sm">
                  No available blocks for this person
                </div>
              ) : (
                <>
                  <select
                    id="target-block"
                    value={targetBlockId}
                    onChange={(e) => setTargetBlockId(e.target.value)}
                    required
                    className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select a block...</option>
                    {targetBlocks.map(block => (
                      <option key={block.id} value={block.id}>
                        {new Date(block.date).toLocaleDateString()} - {block.shift} - {block.rotationType}
                      </option>
                    ))}
                  </select>

                  {selectedTargetBlock && (
                    <div className="mt-2 p-3 bg-gray-50 rounded border border-gray-200">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-medium">{new Date(selectedTargetBlock.date).toLocaleDateString()}</div>
                          <div className="text-sm text-gray-600">{selectedTargetBlock.personName}</div>
                        </div>
                        <div className="flex items-center gap-2">
                          <ShiftIndicator shift={selectedTargetBlock.shift} size="sm" variant="badge" />
                          <RotationBadge rotationType={selectedTargetBlock.rotationType} size="sm" />
                        </div>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </>
      )}

      {/* Reason */}
      <div className="mb-6">
        <label htmlFor="reason" className="block text-sm font-medium text-gray-700 mb-2">
          Reason for Swap *
        </label>
        <select
          id="reason"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          required
          className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Select a reason...</option>
          <option value="personal">Personal/Family Matter</option>
          <option value="medical">Medical Appointment</option>
          <option value="tdy">TDY/Deployment</option>
          <option value="conference">Conference/Training</option>
          <option value="leave">Approved Leave</option>
          <option value="other">Other</option>
        </select>
      </div>

      {/* Additional Notes */}
      <div className="mb-6">
        <label htmlFor="notes" className="block text-sm font-medium text-gray-700 mb-2">
          Additional Notes (Optional)
        </label>
        <textarea
          id="notes"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          rows={4}
          placeholder="Provide any additional details about your swap request..."
          className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Actions */}
      <div className="flex items-center justify-end gap-4">
        <button
          type="button"
          onClick={onCancel}
          disabled={isLoading}
          className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={isLoading}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? 'Submitting...' : 'Create Swap Request'}
        </button>
      </div>
    </form>
  );
};

export default SwapRequestForm;
