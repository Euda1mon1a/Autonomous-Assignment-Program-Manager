import { Button } from "@/components/ui/Button";
import {
  Procedure,
  ProcedureCreate,
  ProcedureUpdate,
} from "@/hooks/useProcedures";
import { X } from "lucide-react";
import { useEffect, useState } from "react";

interface ProcedureFormProps {
  initialData?: Procedure;
  onSubmit: (data: ProcedureCreate | ProcedureUpdate) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

const COMPLEXITY_LEVELS = [
  { value: "basic", label: "Basic" },
  { value: "standard", label: "Standard" },
  { value: "advanced", label: "Advanced" },
  { value: "complex", label: "Complex" },
];

export function ProcedureForm({
  initialData,
  onSubmit,
  onCancel,
  isLoading,
}: ProcedureFormProps) {
  const [formData, setFormData] = useState<ProcedureCreate>({
    name: "",
    description: "",
    category: "",
    specialty: "",
    complexity_level: "standard",
    supervision_ratio: 1,
    min_pgy_level: 1,
    requires_certification: false,
    is_active: true,
  });

  useEffect(() => {
    if (initialData) {
      setFormData({
        name: initialData.name,
        description: initialData.description || "",
        category: initialData.category || "",
        specialty: initialData.specialty || "",
        complexity_level: initialData.complexity_level,
        supervision_ratio: initialData.supervision_ratio,
        min_pgy_level: initialData.min_pgy_level,
        requires_certification: initialData.requires_certification,
        is_active: initialData.is_active,
      });
    }
  }, [initialData]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-700 rounded-xl shadow-2xl w-full max-w-lg overflow-hidden">
        <div className="flex items-center justify-between p-6 border-b border-slate-800">
          <h2 className="text-xl font-semibold text-white">
            {initialData ? "Edit Procedure" : "New Procedure"}
          </h2>
          <button
            onClick={onCancel}
            className="text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-300">
              Procedure Name *
            </label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) =>
                setFormData({ ...formData, name: e.target.value })
              }
              className="w-full bg-slate-800 border-slate-700 rounded-lg px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
              placeholder="e.g. Central Line Placement"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-300">
              Description
            </label>
            <textarea
              value={formData.description || ""}
              onChange={(e) =>
                setFormData({ ...formData, description: e.target.value })
              }
              className="w-full bg-slate-800 border-slate-700 rounded-lg px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none min-h-[80px]"
              placeholder="Brief description of the procedure..."
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">
                Specialty
              </label>
              <input
                type="text"
                value={formData.specialty || ""}
                onChange={(e) =>
                  setFormData({ ...formData, specialty: e.target.value })
                }
                className="w-full bg-slate-800 border-slate-700 rounded-lg px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                placeholder="e.g. Internal Medicine"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">
                Category
              </label>
              <input
                type="text"
                value={formData.category || ""}
                onChange={(e) =>
                  setFormData({ ...formData, category: e.target.value })
                }
                className="w-full bg-slate-800 border-slate-700 rounded-lg px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                placeholder="e.g. Invasive"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">
                Complexity
              </label>
              <select
                value={formData.complexity_level}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    complexity_level: e.target.value as
                      | "basic"
                      | "standard"
                      | "advanced"
                      | "complex",
                  })
                }
                className="w-full bg-slate-800 border-slate-700 rounded-lg px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
              >
                {COMPLEXITY_LEVELS.map((level) => (
                  <option key={level.value} value={level.value}>
                    {level.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">
                Supervision Ratio
              </label>
              <input
                type="number"
                min={0}
                step={0.1}
                value={formData.supervision_ratio}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    supervision_ratio: parseFloat(e.target.value),
                  })
                }
                className="w-full bg-slate-800 border-slate-700 rounded-lg px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">
                Min PGY Level
              </label>
              <input
                type="number"
                min={1}
                max={5}
                value={formData.min_pgy_level}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    min_pgy_level: parseInt(e.target.value),
                  })
                }
                className="w-full bg-slate-800 border-slate-700 rounded-lg px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
              />
            </div>

            <div className="flex items-center space-x-2 pt-8">
              <input
                type="checkbox"
                id="requires_certification"
                checked={formData.requires_certification}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    requires_certification: e.target.checked,
                  })
                }
                className="w-4 h-4 rounded border-slate-600 bg-slate-700 text-blue-600 focus:ring-blue-500 focus:ring-offset-slate-900"
              />
              <label
                htmlFor="requires_certification"
                className="text-sm text-slate-300"
              >
                Requires Certification
              </label>
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
            <Button variant="ghost" onClick={onCancel} disabled={isLoading}>
              Cancel
            </Button>
            <Button
              type="submit"
              className="bg-blue-600 hover:bg-blue-500 text-white"
              disabled={isLoading}
            >
              {isLoading ? "Saving..." : "Save Procedure"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
