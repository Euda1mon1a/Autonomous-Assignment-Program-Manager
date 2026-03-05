import { LineChart } from 'lucide-react';

export function FacultyWorkloadProfilesTab() {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
      <div className="mx-auto w-12 h-12 bg-amber-100 rounded-full flex items-center justify-center mb-4">
        <LineChart className="w-6 h-6 text-amber-600" />
      </div>
      <h2 className="text-lg font-medium text-gray-900 mb-2">Faculty Workload Profiles</h2>
      <p className="text-gray-500 max-w-lg mx-auto mb-4">
        Define the min/max capacity, protected admin time, and call eligibility for faculty members. The CP-SAT engine uses these boundaries to dynamically assign activities to meet resident supervision and physical clinic capacity requirements.
      </p>
      <div className="bg-amber-50 text-amber-800 text-sm p-4 rounded-md inline-block text-left">
        <strong>Note:</strong> Faculty do not follow rigid "weekly templates" or 4-week "rotations". Instead, their assignments flex to meet demand while respecting the boundaries configured here.
      </div>
    </div>
  );
}
