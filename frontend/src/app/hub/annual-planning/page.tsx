import React from 'react';
import Link from 'next/link';
import { AnticipatedLeaveGenerator } from './AnticipatedLeaveGenerator';

export const metadata = {
  title: 'Annual Planning Hub',
  description: 'Manage the Annual Roll-Over (ARO) process for the upcoming academic year.',
};

export default function AnnualPlanningHubPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between border-b border-gray-200 pb-5">
        <h3 className="text-lg leading-6 font-medium text-gray-900">
          Annual Planning & Roll-Over
        </h3>
      </div>

      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          <li>
            <div className="px-4 py-4 sm:px-6 hover:bg-gray-50 cursor-pointer">
              <div className="flex items-center justify-between">
                <div className="flex flex-col">
                  <p className="text-sm font-medium text-blue-600 truncate">
                    Draft Next Academic Year
                  </p>
                  <p className="text-sm text-gray-500 mt-1">
                    Initialize a shadow workspace for the upcoming year without impacting live schedules.
                  </p>
                </div>
                <div className="ml-2 flex-shrink-0 flex">
                  <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-yellow-100 text-yellow-800">
                    Pending
                  </span>
                </div>
              </div>
            </div>
          </li>

          <li>
            <AnticipatedLeaveGenerator />
          </li>

          <li>
            <Link href="/hub/import-export" className="block hover:bg-gray-50">
              <div className="px-4 py-4 sm:px-6">
                <div className="flex items-center justify-between">
                  <div className="flex flex-col">
                    <p className="text-sm font-medium text-blue-600 truncate">
                      Annual Workbook Export (14-Sheet)
                    </p>
                    <p className="text-sm text-gray-500 mt-1">
                      Generate the full multi-tab TAMC formatted spreadsheet for the academic year.
                    </p>
                  </div>
                  <div className="ml-2 flex-shrink-0 flex">
                    <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                      Active
                    </span>
                  </div>
                </div>
              </div>
            </Link>
          </li>
        </ul>
      </div>
    </div>
  );
}
