/**
 * CoverageMatrix Component
 *
 * Visualization of schedule coverage showing gaps and overlaps
 */

import React, { useMemo } from 'react';

export interface CoverageSlot {
  date: string;
  shift: 'AM' | 'PM' | 'Night';
  rotationType: string;
  assignedCount: number;
  requiredCount: number;
  isCritical?: boolean;
}

export interface CoverageMatrixProps {
  slots: CoverageSlot[];
  startDate: string;
  endDate: string;
  rotationTypes: string[];
  onSlotClick?: (slot: CoverageSlot) => void;
  className?: string;
}

const getCoverageLevel = (assigned: number, required: number) => {
  if (assigned === 0) return 'empty';
  if (assigned < required) return 'understaffed';
  if (assigned === required) return 'adequate';
  return 'overstaffed';
};

const coverageColors = {
  empty: 'bg-red-500 text-white',
  understaffed: 'bg-orange-400 text-white',
  adequate: 'bg-green-500 text-white',
  overstaffed: 'bg-blue-400 text-white',
};

export const CoverageMatrix: React.FC<CoverageMatrixProps> = ({
  slots,
  startDate,
  endDate,
  rotationTypes,
  onSlotClick,
  className = '',
}) => {
  const dates = useMemo(() => {
    const start = new Date(startDate);
    const end = new Date(endDate);
    const dateList: string[] = [];

    const current = new Date(start);
    while (current <= end) {
      dateList.push(current.toISOString().split('T')[0]);
      current.setDate(current.getDate() + 1);
    }

    return dateList;
  }, [startDate, endDate]);

  const shifts: Array<'AM' | 'PM' | 'Night'> = ['AM', 'PM', 'Night'];

  const getSlotData = (date: string, shift: string, rotation: string): CoverageSlot | null => {
    return slots.find(
      s => s.date === date && s.shift === shift && s.rotationType === rotation
    ) || null;
  };

  const getCoverageStats = () => {
    const total = slots.length;
    const empty = slots.filter(s => s.assignedCount === 0).length;
    const understaffed = slots.filter(s => s.assignedCount > 0 && s.assignedCount < s.requiredCount).length;
    const adequate = slots.filter(s => s.assignedCount === s.requiredCount).length;

    return { total, empty, understaffed, adequate };
  };

  const stats = getCoverageStats();

  return (
    <div className={`coverage-matrix bg-white rounded-lg shadow-lg p-4 ${className}`}>
      {/* Header */}
      <div className="mb-4">
        <h3 className="text-lg font-semibold mb-2">Coverage Matrix</h3>
        <div className="flex gap-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-red-500"></div>
            <span>Empty: {stats.empty}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-orange-400"></div>
            <span>Understaffed: {stats.understaffed}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-green-500"></div>
            <span>Adequate: {stats.adequate}</span>
          </div>
        </div>
      </div>

      {/* Matrix Table */}
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr>
              <th className="sticky left-0 bg-white border border-gray-300 p-2 text-xs font-semibold">
                Rotation / Date
              </th>
              {dates.map(date => (
                <th
                  key={date}
                  className="border border-gray-300 p-2 text-xs font-semibold min-w-[80px]"
                >
                  <div className="flex flex-col items-center">
                    <span>{new Date(date).toLocaleDateString('en-US', { month: 'short' })}</span>
                    <span>{new Date(date).getDate()}</span>
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rotationTypes.map(rotation => (
              <React.Fragment key={rotation}>
                {shifts.map(shift => (
                  <tr key={`${rotation}-${shift}`}>
                    <td className="sticky left-0 bg-white border border-gray-300 p-2 text-xs font-medium">
                      {rotation} - {shift}
                    </td>
                    {dates.map(date => {
                      const slotData = getSlotData(date, shift, rotation);
                      if (!slotData) {
                        return (
                          <td
                            key={`${date}-${shift}`}
                            className="border border-gray-300 p-1 bg-gray-100"
                          >
                            <div className="text-xs text-center text-gray-400">-</div>
                          </td>
                        );
                      }

                      const level = getCoverageLevel(slotData.assignedCount, slotData.requiredCount);
                      const colorClass = coverageColors[level];

                      return (
                        <td
                          key={`${date}-${shift}`}
                          className="border border-gray-300 p-1"
                        >
                          <button
                            className={`
                              w-full h-12 rounded text-xs font-semibold
                              ${colorClass}
                              ${slotData.isCritical ? 'ring-2 ring-red-600 ring-offset-1' : ''}
                              hover:opacity-80 transition-opacity
                              focus:outline-none focus:ring-2 focus:ring-blue-500
                            `}
                            onClick={() => onSlotClick?.(slotData)}
                            aria-label={`${rotation} ${shift} on ${date}: ${slotData.assignedCount}/${slotData.requiredCount} assigned`}
                          >
                            <div className="flex flex-col items-center justify-center">
                              <span className="font-bold">
                                {slotData.assignedCount}/{slotData.requiredCount}
                              </span>
                              {slotData.isCritical && (
                                <span className="text-xs">⚠️</span>
                              )}
                            </div>
                          </button>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="mt-4 text-xs text-gray-600">
        Click on any cell to view details. Critical slots are marked with ⚠️
      </div>
    </div>
  );
};

export default CoverageMatrix;
