import { User } from 'lucide-react';

export function MyAbsencesTab() {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
      <div className="mx-auto w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center mb-4">
        <User className="w-6 h-6 text-indigo-600" />
      </div>
      <h2 className="text-lg font-medium text-gray-900 mb-2">My Absences</h2>
      <p className="text-gray-500 max-w-sm mx-auto">
        This view will allow you to track your own away-from-program status and request new absences. Coming soon as part of the Absences Hub consolidation.
      </p>
    </div>
  );
}
