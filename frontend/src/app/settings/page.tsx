'use client'

export default function SettingsPage() {
  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600">Configure application settings</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Academic Year Settings */}
        <div className="card">
          <h2 className="font-semibold text-lg mb-4">Academic Year</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Start Date
              </label>
              <input
                type="date"
                className="input-field w-full"
                defaultValue="2024-07-01"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                End Date
              </label>
              <input
                type="date"
                className="input-field w-full"
                defaultValue="2025-06-30"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Block Duration (days)
              </label>
              <input
                type="number"
                className="input-field w-full"
                defaultValue="28"
              />
            </div>
          </div>
        </div>

        {/* ACGME Settings */}
        <div className="card">
          <h2 className="font-semibold text-lg mb-4">ACGME Settings</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Max Weekly Hours
              </label>
              <input
                type="number"
                className="input-field w-full"
                defaultValue="80"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                PGY-1 Supervision Ratio
              </label>
              <select className="input-field w-full">
                <option value="2">1:2 (1 faculty per 2 residents)</option>
                <option value="1">1:1 (1 faculty per resident)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                PGY-2/3 Supervision Ratio
              </label>
              <select className="input-field w-full">
                <option value="4">1:4 (1 faculty per 4 residents)</option>
                <option value="3">1:3 (1 faculty per 3 residents)</option>
                <option value="2">1:2 (1 faculty per 2 residents)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Scheduling Algorithm */}
        <div className="card">
          <h2 className="font-semibold text-lg mb-4">Scheduling Algorithm</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Default Algorithm
              </label>
              <select className="input-field w-full">
                <option value="greedy">Greedy (Fast)</option>
                <option value="min_conflicts">Min Conflicts (Balanced)</option>
                <option value="cp_sat">CP-SAT (Optimal)</option>
              </select>
              <p className="text-xs text-gray-500 mt-1">
                Greedy is fastest, CP-SAT finds optimal solution but slower
              </p>
            </div>
          </div>
        </div>

        {/* Holidays */}
        <div className="card">
          <h2 className="font-semibold text-lg mb-4">Federal Holidays</h2>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between py-2 border-b">
              <span>New Years Day</span>
              <span className="text-gray-500">Jan 1</span>
            </div>
            <div className="flex justify-between py-2 border-b">
              <span>MLK Day</span>
              <span className="text-gray-500">3rd Mon Jan</span>
            </div>
            <div className="flex justify-between py-2 border-b">
              <span>Presidents Day</span>
              <span className="text-gray-500">3rd Mon Feb</span>
            </div>
            <div className="flex justify-between py-2 border-b">
              <span>Memorial Day</span>
              <span className="text-gray-500">Last Mon May</span>
            </div>
            <div className="flex justify-between py-2 border-b">
              <span>Independence Day</span>
              <span className="text-gray-500">Jul 4</span>
            </div>
            <div className="flex justify-between py-2">
              <span>+ 5 more holidays</span>
              <button className="text-blue-600 hover:underline">Edit</button>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-6 flex justify-end">
        <button className="btn-primary">Save Settings</button>
      </div>
    </div>
  )
}
