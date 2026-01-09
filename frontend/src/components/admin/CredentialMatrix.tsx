'use client';

/**
 * CredentialMatrix Component
 *
 * Displays a faculty × procedure matrix showing credential status.
 * Click cells to grant/edit/revoke credentials.
 */
import { useState, useMemo, useCallback } from 'react';
import { CheckCircle, XCircle, AlertTriangle, Clock } from 'lucide-react';
import { CredentialCellModal } from './CredentialCellModal';
import type { Person } from '@/types/api';
import type { Procedure, Credential, CredentialStatus } from '@/hooks/useProcedures';

// ============================================================================
// Types
// ============================================================================

export interface CredentialMatrixProps {
  faculty: Person[];
  procedures: Procedure[];
  credentials: Credential[];
  showExpiringOnly?: boolean;
}

interface CellData {
  faculty: Person;
  procedure: Procedure;
  credential: Credential | null;
  isExpiring: boolean;
}

// ============================================================================
// Subcomponents
// ============================================================================

function StatusBadge({ status, isExpiring }: { status: CredentialStatus; isExpiring: boolean }) {
  if (isExpiring) {
    return (
      <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-medium bg-amber-500/20 text-amber-400">
        <AlertTriangle className="w-3 h-3" />
      </span>
    );
  }

  switch (status) {
    case 'active':
      return (
        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-emerald-500/20 text-emerald-400">
          <CheckCircle className="w-3 h-3" />
        </span>
      );
    case 'expired':
      return (
        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-red-500/20 text-red-400">
          <XCircle className="w-3 h-3" />
        </span>
      );
    case 'suspended':
      return (
        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-slate-500/20 text-slate-400">
          <XCircle className="w-3 h-3" />
        </span>
      );
    case 'pending':
      return (
        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-blue-500/20 text-blue-400">
          <Clock className="w-3 h-3" />
        </span>
      );
    default:
      return null;
  }
}

// ============================================================================
// Main Component
// ============================================================================

export function CredentialMatrix({
  faculty,
  procedures,
  credentials,
  showExpiringOnly = false,
}: CredentialMatrixProps) {
  const [selectedCell, setSelectedCell] = useState<CellData | null>(null);

  // Build a lookup map for credentials: key = `${person_id}_${procedure_id}`
  const credentialMap = useMemo(() => {
    const map = new Map<string, Credential>();
    credentials.forEach((cred) => {
      map.set(`${cred.personId}_${cred.procedure_id}`, cred);
    });
    return map;
  }, [credentials]);

  // Check if credential is expiring (within 30 days)
  const isExpiring = useCallback((credential: Credential | null): boolean => {
    if (!credential?.expiration_date) return false;
    const expirationDate = new Date(credential.expiration_date);
    const thirtyDaysFromNow = new Date();
    thirtyDaysFromNow.setDate(thirtyDaysFromNow.getDate() + 30);
    return expirationDate <= thirtyDaysFromNow && expirationDate > new Date();
  }, []);

  // Filter faculty if showing expiring only
  const filteredFaculty = useMemo(() => {
    if (!showExpiringOnly) return faculty;

    return faculty.filter((f) => {
      return procedures.some((p) => {
        const cred = credentialMap.get(`${f.id}_${p.id}`);
        return cred && isExpiring(cred);
      });
    });
  }, [faculty, procedures, credentialMap, showExpiringOnly, isExpiring]);

  const handleCellClick = useCallback(
    (facultyMember: Person, procedure: Procedure) => {
      const credential = credentialMap.get(`${facultyMember.id}_${procedure.id}`) || null;
      setSelectedCell({
        faculty: facultyMember,
        procedure,
        credential,
        isExpiring: isExpiring(credential),
      });
    },
    [credentialMap, isExpiring]
  );

  if (faculty.length === 0 || procedures.length === 0) {
    return (
      <div className="text-center py-12 text-slate-400">
        <Award className="w-12 h-12 mx-auto mb-4 opacity-50" />
        <p className="text-lg font-medium">No data available</p>
        <p className="text-sm">Add faculty and procedures to view the credential matrix.</p>
      </div>
    );
  }

  return (
    <>
      <div className="bg-slate-800/50 border border-slate-700 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="px-4 py-3 text-left text-sm font-medium text-slate-400 sticky left-0 bg-slate-800/50 z-10 min-w-[200px]">
                  Faculty
                </th>
                {procedures.map((proc) => (
                  <th
                    key={proc.id}
                    className="px-2 py-3 text-center text-xs font-medium text-slate-400 min-w-[80px]"
                    title={proc.name}
                  >
                    <div className="truncate max-w-[80px]">
                      {proc.name.length > 10 ? `${proc.name.slice(0, 10)}...` : proc.name}
                    </div>
                    {proc.specialty && (
                      <div className="text-slate-500 text-[10px] truncate">
                        {proc.specialty}
                      </div>
                    )}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50">
              {filteredFaculty.map((facultyMember) => (
                <tr key={facultyMember.id} className="hover:bg-slate-700/30">
                  <td className="px-4 py-2 sticky left-0 bg-slate-800/50 z-10">
                    <div className="font-medium text-white text-sm">
                      {facultyMember.name}
                    </div>
                  </td>
                  {procedures.map((proc) => {
                    const credential = credentialMap.get(`${facultyMember.id}_${proc.id}`);
                    const expiring = isExpiring(credential || null);

                    return (
                      <td
                        key={proc.id}
                        className="px-2 py-2 text-center cursor-pointer hover:bg-slate-600/50 transition-colors"
                        onClick={() => handleCellClick(facultyMember, proc)}
                      >
                        {credential ? (
                          <StatusBadge status={credential.status} isExpiring={expiring} />
                        ) : (
                          <span className="text-slate-600">-</span>
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Cell Modal */}
      {selectedCell && (
        <CredentialCellModal
          faculty={selectedCell.faculty}
          procedure={selectedCell.procedure}
          credential={selectedCell.credential}
          onClose={() => setSelectedCell(null)}
        />
      )}
    </>
  );
}

// Import for empty state icon
import { Award } from 'lucide-react';
