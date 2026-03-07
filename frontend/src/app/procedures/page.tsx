'use client';

/**
 * Procedures Hub Page
 *
 * Single-purpose hub for managing the global catalog of clinical procedures.
 *
 * Permission Tiers:
 * - Tier 0 (Green): View procedures and default supervision rules
 * - Tier 1 (Amber): Add/Edit/Delete procedures
 */

import { useState, useMemo } from 'react';
import { Stethoscope, Plus } from 'lucide-react';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { RiskBar, type RiskTier, useRiskTierFromRoles } from '@/components/ui/RiskBar';
import { useAuth } from '@/contexts/AuthContext';
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { useToast } from "@/contexts/ToastContext";
import { ProcedureForm, ProcedureList } from '@/features/procedures';
import {
  Procedure,
  ProcedureCreate,
  ProcedureUpdate,
  useCreateProcedure,
  useDeleteProcedure,
  useProcedures,
  useUpdateProcedure,
} from "@/hooks/useProcedures";

// ============================================================================
// Types
// ============================================================================

type ProceduresTab = 'catalog';

interface TabConfig {
  id: ProceduresTab;
  label: string;
  icon: typeof Stethoscope;
  description: string;
  requiredTier: RiskTier;
}

// ============================================================================
// Constants
// ============================================================================

const TABS: TabConfig[] = [
  {
    id: 'catalog',
    label: 'Procedure Catalog',
    icon: Stethoscope,
    description: 'Manage clinical procedures and global supervision defaults',
    requiredTier: 0,
  }
];

// ============================================================================
// Component
// ============================================================================

export default function ProceduresPage() {
  const { user } = useAuth();
  const [activeTab] = useState<ProceduresTab>('catalog');

  // Determine user's permission tier from role
  const userTier: RiskTier = useRiskTierFromRoles(user?.role ? [user.role] : []);

  const currentRiskTier: RiskTier = useMemo(() => {
    return userTier;
  }, [userTier]);

  const canEdit = userTier >= 1;

  // Generate appropriate label and tooltip for RiskBar
  const riskBarConfig = useMemo(() => {
    switch (currentRiskTier) {
      case 0:
        return {
          label: 'View Mode',
          tooltip: 'You can browse procedure definitions. Contact a coordinator to suggest changes.',
        };
      case 1:
        return {
          label: 'Edit Mode',
          tooltip: 'You can add, edit, and delete procedures from the global catalog.',
        };
      case 2:
        return {
          label: 'Admin Mode',
          tooltip: 'You have full access to manage the procedure catalog.',
        };
      default:
        return { label: undefined, tooltip: undefined };
    }
  }, [currentRiskTier]);

  // Procedure Management Logic
  const { data, isLoading, isError } = useProcedures();
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingProcedure, setEditingProcedure] = useState<Procedure | undefined>(undefined);
  const { toast } = useToast();

  const createMutation = useCreateProcedure();
  const updateMutation = useUpdateProcedure();
  const deleteMutation = useDeleteProcedure();

  const handleCreate = (procedureData: ProcedureCreate) => {
    createMutation.mutate(procedureData, {
      onSuccess: () => {
        toast.success("Procedure created successfully");
        setIsFormOpen(false);
      },
      onError: (error) => {
        toast.error(`Failed to create procedure: ${error.message}`);
      },
    });
  };

  const handleUpdate = (procedureData: ProcedureUpdate) => {
    if (!editingProcedure) return;
    updateMutation.mutate(
      { id: editingProcedure.id, data: procedureData },
      {
        onSuccess: () => {
          toast.success("Procedure updated successfully");
          setIsFormOpen(false);
          setEditingProcedure(undefined);
        },
        onError: (error) => {
          toast.error(`Failed to update procedure: ${error.message}`);
        },
      }
    );
  };

  const handleSubmit = (procedureData: ProcedureCreate | ProcedureUpdate) => {
    if (editingProcedure) {
      handleUpdate(procedureData as ProcedureUpdate);
    } else {
      handleCreate(procedureData as ProcedureCreate);
    }
  };

  const handleDelete = (id: string) => {
    if (!canEdit) return;
    if (confirm("Are you sure you want to delete this procedure?")) {
      deleteMutation.mutate(id, {
        onSuccess: () => {
          toast.success("Procedure deleted");
        },
        onError: (error) => {
          toast.error(`Failed to delete procedure: ${error.message}`);
        },
      });
    }
  };

  const openCreate = () => {
    if (!canEdit) return;
    setEditingProcedure(undefined);
    setIsFormOpen(true);
  };

  const openEdit = (procedure: Procedure) => {
    if (!canEdit) return;
    setEditingProcedure(procedure);
    setIsFormOpen(true);
  };

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        {/* Risk Bar */}
        <RiskBar
          tier={currentRiskTier}
          label={riskBarConfig.label}
          tooltip={riskBarConfig.tooltip}
        />

        {/* Header */}
        <header className="bg-white border-b border-gray-200 shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-gradient-to-br from-teal-500 to-emerald-600 rounded-lg">
                  <Stethoscope className="w-6 h-6 text-white" aria-hidden="true" />
                </div>
                <div>
                  <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Procedures Hub</h1>
                  <p className="text-sm text-gray-600">
                    Global catalog of medical procedures and supervision rules
                  </p>
                </div>
              </div>

              {canEdit && (
                <Button
                  onClick={openCreate}
                  className="bg-teal-600 hover:bg-teal-700 text-white"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  New Procedure
                </Button>
              )}
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
          {activeTab === 'catalog' && (
            <div
              id="tabpanel-catalog"
              role="tabpanel"
              aria-labelledby="tab-catalog"
              className="space-y-6"
            >
              {isError && (
                <Alert variant="error" title="Error loading procedures">
                  Failed to load procedures. Please try refreshing the page.
                </Alert>
              )}

              <ProcedureList
                procedures={data?.items || []}
                isLoading={isLoading}
                onEdit={canEdit ? openEdit : undefined}
                onDelete={canEdit ? handleDelete : undefined}
              />

              {isFormOpen && canEdit && (
                <ProcedureForm
                  initialData={editingProcedure}
                  onSubmit={handleSubmit}
                  onCancel={() => setIsFormOpen(false)}
                  isLoading={createMutation.isPending || updateMutation.isPending}
                />
              )}
            </div>
          )}
        </main>
      </div>
    </ProtectedRoute>
  );
}
