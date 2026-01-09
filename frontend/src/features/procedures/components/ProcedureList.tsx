import { Button } from "@/components/ui/Button";
import { Procedure } from "@/hooks/useProcedures";
import { Edit, Trash2 } from "lucide-react";

interface ProcedureListProps {
  procedures: Procedure[];
  onEdit: (procedure: Procedure) => void;
  onDelete: (id: string) => void;
  isLoading?: boolean;
}

export function ProcedureList({
  procedures,
  onEdit,
  onDelete,
  isLoading,
}: ProcedureListProps) {
  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="h-16 bg-slate-800/50 rounded-lg animate-pulse"
          />
        ))}
      </div>
    );
  }

  if (procedures.length === 0) {
    return (
      <div className="text-center py-12 bg-slate-900/50 rounded-xl border border-dashed border-slate-700">
        <p className="text-slate-400">No procedures found.</p>
        <p className="text-sm text-slate-500 mt-1">
          Create a new procedure to get started.
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/50">
      <table className="w-full text-left text-sm">
        <thead className="bg-slate-900/80 text-slate-400 font-medium">
          <tr>
            <th className="px-6 py-4">Name</th>
            <th className="px-6 py-4">Specialty</th>
            <th className="px-6 py-4">Category</th>
            <th className="px-6 py-4">Complexity</th>
            <th className="px-6 py-4">Ratio</th>
            <th className="px-6 py-4 text-right">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800">
          {procedures.map((procedure) => (
            <tr
              key={procedure.id}
              className="hover:bg-slate-800/30 transition-colors"
            >
              <td className="px-6 py-4">
                <div className="font-medium text-slate-200">
                  {procedure.name}
                </div>
                {procedure.description && (
                  <div className="text-xs text-slate-500 truncate max-w-[200px]">
                    {procedure.description}
                  </div>
                )}
              </td>
              <td className="px-6 py-4 text-slate-300">
                {procedure.specialty || "-"}
              </td>
              <td className="px-6 py-4 text-slate-300">
                {procedure.category || "-"}
              </td>
              <td className="px-6 py-4">
                <span
                  className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium
                  ${
                    procedure.complexityLevel === "basic"
                      ? "bg-green-400/10 text-green-400 border border-green-400/20"
                      : ""
                  }
                  ${
                    procedure.complexityLevel === "standard"
                      ? "bg-blue-400/10 text-blue-400 border border-blue-400/20"
                      : ""
                  }
                  ${
                    procedure.complexityLevel === "advanced"
                      ? "bg-orange-400/10 text-orange-400 border border-orange-400/20"
                      : ""
                  }
                  ${
                    procedure.complexityLevel === "complex"
                      ? "bg-red-400/10 text-red-400 border border-red-400/20"
                      : ""
                  }
                `}
                >
                  {procedure.complexityLevel}
                </span>
              </td>
              <td className="px-6 py-4 text-slate-300">
                1:{procedure.supervision_ratio}
              </td>
              <td className="px-6 py-4 text-right">
                <div className="flex justify-end gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onEdit(procedure)}
                    className="h-8 w-8 p-0 text-slate-400 hover:text-white"
                  >
                    <Edit className="w-4 h-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onDelete(procedure.id)}
                    className="h-8 w-8 p-0 text-slate-400 hover:text-red-400 hover:bg-red-400/10"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
