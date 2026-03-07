import { ClipboardList } from 'lucide-react';

export function OutpatientTargetsTab() {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
      <div className="mx-auto w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mb-4">
        <ClipboardList className="w-6 h-6 text-blue-600" />
      </div>
      <h2 className="text-lg font-medium text-gray-900 mb-2">Outpatient Rotations (Flexible Targets)</h2>
      <p className="text-gray-500 max-w-lg mx-auto">
        Define target activity volumes for 4-week outpatient rotations (e.g., "Must have exactly 4 FM Clinics and 8 Specialty Clinics"). The solver will automatically distribute these across the block based on faculty availability and physical capacity.
      </p>
    </div>
  );
}
