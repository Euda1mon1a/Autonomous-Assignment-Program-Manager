import { BookText } from 'lucide-react';

export function ActivityDictionaryTab() {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
      <div className="mx-auto w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center mb-4">
        <BookText className="w-6 h-6 text-indigo-600" />
      </div>
      <h2 className="text-lg font-medium text-gray-900 mb-2">Activity Dictionary</h2>
      <p className="text-gray-500 max-w-lg mx-auto mb-4">
        Define the vocabulary of the scheduling engine. These are the atomic "Lego Bricks" (e.g., FM Clinic, Procedure, Didactics) that are used to build resident rotations and faculty assignments.
      </p>
      <div className="bg-blue-50 text-blue-800 text-sm p-4 rounded-md inline-block text-left">
        <strong>Coming Soon:</strong> You will be able to edit activity codes, display colors, ACGME categories, and physical clinic capacity costs here.
      </div>
    </div>
  );
}
