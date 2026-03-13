'use client';

import { useState, useEffect } from 'react';
import { graduationRequirementsApi, GraduationRequirement } from '@/api/graduation-requirements';
import { Loader2, Plus, Trash2 } from 'lucide-react';
import { useToast } from '@/contexts/ToastContext';

export default function GraduationRequirementsPage() {
  const [requirements, setRequirements] = useState<GraduationRequirement[]>([]);
  const [loading, setLoading] = useState(true);
  const [pgyLevel, setPgyLevel] = useState<number>(1);
  const { toast } = useToast();

  useEffect(() => {
    fetchRequirements();
  }, [pgyLevel]);

  const fetchRequirements = async () => {
    setLoading(true);
    try {
      const data = await graduationRequirementsApi.getByPgy(pgyLevel);
      setRequirements(data);
    } catch (error) {
      toast.error('Failed to fetch requirements');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this requirement?')) return;
    try {
      await graduationRequirementsApi.delete(id);
      toast.success('Requirement deleted');
      fetchRequirements();
    } catch (error) {
      toast.error('Failed to delete requirement');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-white">Graduation Requirements</h1>
            <p className="text-slate-400 mt-1">Manage clinic type requirements by PGY level</p>
          </div>
          <button className="flex items-center gap-2 px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg font-medium transition-colors">
            <Plus className="w-4 h-4" />
            Add Requirement
          </button>
        </div>

        <div className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden shadow-xl p-6">
          <div className="flex items-center gap-4 mb-6">
            <label className="text-slate-300 font-medium">PGY Level:</label>
            <select
              value={pgyLevel}
              onChange={(e) => setPgyLevel(Number(e.target.value))}
              className="px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white"
            >
              {[1, 2, 3, 4, 5, 6, 7].map(level => (
                <option key={level} value={level}>PGY-{level}</option>
              ))}
            </select>
          </div>

          {loading ? (
            <div className="flex justify-center py-12">
              <Loader2 className="w-8 h-8 text-violet-500 animate-spin" />
            </div>
          ) : requirements.length === 0 ? (
            <div className="text-center py-12 text-slate-400">
              No graduation requirements set for PGY-{pgyLevel}
            </div>
          ) : (
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className="pb-3 text-sm font-semibold text-slate-400">Template ID</th>
                  <th className="pb-3 text-sm font-semibold text-slate-400">Min Halves</th>
                  <th className="pb-3 text-sm font-semibold text-slate-400">Target Halves</th>
                  <th className="pb-3 text-sm font-semibold text-slate-400">By Date</th>
                  <th className="pb-3 text-sm font-semibold text-slate-400">Actions</th>
                </tr>
              </thead>
              <tbody>
                {requirements.map((req) => (
                  <tr key={req.id} className="border-b border-slate-700/50">
                    <td className="py-4 text-sm text-slate-300">{req.rotationTemplateId}</td>
                    <td className="py-4 text-sm text-slate-300">{req.minHalves}</td>
                    <td className="py-4 text-sm text-slate-300">{req.targetHalves || '-'}</td>
                    <td className="py-4 text-sm text-slate-300">{req.byDate || '-'}</td>
                    <td className="py-4 text-sm">
                      <button
                        onClick={() => handleDelete(req.id)}
                        className="p-2 text-red-400 hover:text-red-300 hover:bg-red-400/10 rounded transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
