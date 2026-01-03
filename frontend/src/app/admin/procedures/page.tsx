"use client";

import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { useToast } from "@/contexts/ToastContext";
import { ProcedureForm } from "@/features/procedures/components/ProcedureForm";
import { ProcedureList } from "@/features/procedures/components/ProcedureList";
import {
  Procedure,
  ProcedureCreate,
  ProcedureUpdate,
  useCreateProcedure,
  useDeleteProcedure,
  useProcedures,
  useUpdateProcedure,
} from "@/hooks/useProcedures";
import { Plus } from "lucide-react";
import { useState } from "react";

export default function ProceduresPage() {
  const { data, isLoading, isError } = useProcedures();
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingProcedure, setEditingProcedure] = useState<
    Procedure | undefined
  >(undefined);
  const { toast } = useToast();

  const createMutation = useCreateProcedure();
  const updateMutation = useUpdateProcedure();
  const deleteMutation = useDeleteProcedure();

  const handleCreate = (data: ProcedureCreate) => {
    createMutation.mutate(data, {
      onSuccess: () => {
        toast.success("Procedure created successfully");
        setIsFormOpen(false);
      },
      onError: (error) => {
        toast.error(`Failed to create procedure: ${error.message}`);
      },
    });
  };

  const handleUpdate = (data: ProcedureUpdate) => {
    if (!editingProcedure) return;
    updateMutation.mutate(
      { id: editingProcedure.id, data },
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

  const handleSubmit = (data: ProcedureCreate | ProcedureUpdate) => {
    if (editingProcedure) {
      handleUpdate(data as ProcedureUpdate);
    } else {
      handleCreate(data as ProcedureCreate);
    }
  };

  const handleDelete = (id: string) => {
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
    setEditingProcedure(undefined);
    setIsFormOpen(true);
  };

  const openEdit = (procedure: Procedure) => {
    setEditingProcedure(procedure);
    setIsFormOpen(true);
  };

  return (
    <div className="container mx-auto py-8 px-4 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">
            Procedure Catalog
          </h1>
          <p className="text-slate-400">
            Manage medical procedures and supervision requirements.
          </p>
        </div>
        <Button
          onClick={openCreate}
          className="bg-blue-600 hover:bg-blue-500 text-white"
        >
          <Plus className="w-4 h-4 mr-2" />
          New Procedure
        </Button>
      </div>

      {isError && (
        <Alert variant="error" title="Error loading procedures">
          Failed to load procedures. Please try refreshing the page.
        </Alert>
      )}

      <ProcedureList
        procedures={data?.items || []}
        isLoading={isLoading}
        onEdit={openEdit}
        onDelete={handleDelete}
      />

      {isFormOpen && (
        <ProcedureForm
          initialData={editingProcedure}
          onSubmit={handleSubmit}
          onCancel={() => setIsFormOpen(false)}
          isLoading={createMutation.isPending || updateMutation.isPending}
        />
      )}
    </div>
  );
}
