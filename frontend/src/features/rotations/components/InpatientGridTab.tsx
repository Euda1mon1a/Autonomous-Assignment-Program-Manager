'use client'

import { RotationTemplatesTab } from '@/app/rotations/components/RotationTemplatesTab'

export function InpatientGridTab({ canEdit, canDelete }: { canEdit: boolean, canDelete: boolean }) {
  return (
    <div className="space-y-4">
      <div className="bg-blue-50 border border-blue-200 rounded-md p-4 text-sm text-blue-800">
        <strong>Inpatient Rotations (Fixed Grids):</strong> The 7x2 weekly activity patterns defined here will be locked and preloaded for any resident assigned to this rotation. The solver cannot modify these slots.
      </div>
      <RotationTemplatesTab canEdit={canEdit} canDelete={canDelete} />
    </div>
  )
}
