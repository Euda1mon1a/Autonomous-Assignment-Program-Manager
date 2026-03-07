'use client';

import React, { useState } from 'react';
import { api } from '@/lib/api';

interface AnticipatedLeaveResponse {
  internsProcessed: number;
  absencesCreated: number;
}

export function AnticipatedLeaveGenerator() {
  const [isGenerating, setIsGenerating] = useState(false);
  const [result, setResult] = useState<AnticipatedLeaveResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async () => {
    // AY starts July 1: if month >= 7, AY = this year; else AY = last year
    const now = new Date();
    const currentAcademicYear = now.getMonth() >= 6 ? now.getFullYear() : now.getFullYear() - 1;

    setIsGenerating(true);
    setError(null);
    setResult(null);

    try {
      const response = await api.post('/absences/generate-anticipated', null, {
        params: {
          academic_year: currentAcademicYear,
          weeks_per_intern: 4,
        },
      });
      setResult(response.data);
    } catch (err: any) {
      console.error(err);
      setError(err?.response?.data?.detail || 'Failed to generate anticipated leave placeholders.');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="px-4 py-4 sm:px-6 hover:bg-gray-50 cursor-pointer" onClick={handleGenerate}>
      <div className="flex items-center justify-between">
        <div className="flex flex-col">
          <p className="text-sm font-medium text-blue-600 truncate">
            Anticipated Leave Placeholder Generator
          </p>
          <p className="text-sm text-gray-500 mt-1">
            Pre-generate generic schedules that balance missing leave requests for incoming interns.
          </p>
          {isGenerating && (
            <p className="text-sm text-blue-500 mt-2 font-medium">Generating...</p>
          )}
          {error && (
            <p className="text-sm text-red-600 mt-2 font-medium">Error: {error}</p>
          )}
          {result && (
            <p className="text-sm text-green-600 mt-2 font-medium">
              Success: Processed {result.internsProcessed} interns, created {result.absencesCreated} placeholders.
            </p>
          )}
        </div>
        <div className="ml-2 flex-shrink-0 flex">
          <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
            Active
          </span>
        </div>
      </div>
    </div>
  );
}
