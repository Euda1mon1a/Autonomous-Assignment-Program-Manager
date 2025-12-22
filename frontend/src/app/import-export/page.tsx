'use client'

import { useState } from 'react'
import { Upload, Download } from 'lucide-react'
import { BulkImportModal, ExportPanel, PEOPLE_EXPORT_COLUMNS } from '@/features/import-export'
import { ProtectedRoute } from '@/components/ProtectedRoute'

export default function ImportExportPage() {
  const [isImportModalOpen, setIsImportModalOpen] = useState(false)
  const [activeTab, setActiveTab] = useState<'import' | 'export'>('import')

  return (
    <ProtectedRoute>
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Import & Export</h1>
          <p className="text-gray-600">Bulk import data or export schedules and reports</p>
        </div>

        {/* Tab Navigation */}
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setActiveTab('import')}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'import'
                ? 'bg-blue-100 text-blue-700'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            <Upload className="w-4 h-4" />
            Import
          </button>
          <button
            onClick={() => setActiveTab('export')}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'export'
                ? 'bg-blue-100 text-blue-700'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            <Download className="w-4 h-4" />
            Export
          </button>
        </div>

        {/* Import Section */}
        {activeTab === 'import' && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Bulk Import</h2>
            <p className="text-gray-600 mb-6">
              Import people, assignments, absences, or schedule data from CSV, Excel, or JSON files.
            </p>
            <button
              onClick={() => setIsImportModalOpen(true)}
              className="btn-primary flex items-center gap-2"
            >
              <Upload className="w-4 h-4" />
              Start Import
            </button>
          </div>
        )}

        {/* Export Section */}
        {activeTab === 'export' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Export Data</h2>
              <p className="text-gray-600 mb-6">
                Export schedule data, people, or assignments to CSV, Excel, or JSON formats.
              </p>
              <ExportPanel
                data={[]}
                columns={PEOPLE_EXPORT_COLUMNS}
                filename="schedule-export"
              />
            </div>
          </div>
        )}

        {/* Import Modal */}
        <BulkImportModal
          isOpen={isImportModalOpen}
          onClose={() => setIsImportModalOpen(false)}
        />
      </div>
    </ProtectedRoute>
  )
}
