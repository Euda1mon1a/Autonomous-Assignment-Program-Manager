import { Shield } from 'lucide-react';

export function ApprovalsTab() {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
      <div className="mx-auto w-12 h-12 bg-amber-100 rounded-full flex items-center justify-center mb-4">
        <Shield className="w-6 h-6 text-amber-600" />
      </div>
      <h2 className="text-lg font-medium text-gray-900 mb-2">Approvals & Admin</h2>
      <p className="text-gray-500 max-w-sm mx-auto">
        This view will allow coordinators and admins to approve or deny absence requests and view sensitive details such as sick leave reasons. Coming soon as part of the Absences Hub consolidation.
      </p>
    </div>
  );
}
