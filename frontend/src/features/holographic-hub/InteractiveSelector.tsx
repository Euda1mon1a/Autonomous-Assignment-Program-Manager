/**
 * Interactive Selector Component
 *
 * Provides interactive selection of residents and constraints
 * with dependency highlighting in the 3D visualization.
 */

'use client';

import React, { useState, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type {
  SelectionState,
  DependencyGraph,
  DependencyNode,
  WavelengthChannel,
} from './types';
import { WAVELENGTH_COLORS, WAVELENGTH_LABELS } from './types';

interface InteractiveSelectorProps {
  selection: SelectionState;
  dependencyGraph: DependencyGraph | null;
  onSelectResident: (id: string, append?: boolean) => void;
  onSelectConstraint: (id: string, append?: boolean) => void;
  onClearSelection: () => void;
  onSetHighlightMode: (mode: SelectionState['highlightMode']) => void;
  availableResidents?: Array<{ id: string; name: string }>;
  availableConstraints?: Array<{ id: string; name: string; category: string }>;
}

export function InteractiveSelector({
  selection,
  dependencyGraph,
  onSelectResident,
  onSelectConstraint,
  onClearSelection,
  onSetHighlightMode,
  availableResidents = [],
  availableConstraints = [],
}: InteractiveSelectorProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedSection, setExpandedSection] = useState<'residents' | 'constraints' | null>('residents');

  // Filter items based on search
  const filteredResidents = useMemo(() => {
    if (!searchQuery) return availableResidents;
    const query = searchQuery.toLowerCase();
    return availableResidents.filter(r => r.name.toLowerCase().includes(query));
  }, [availableResidents, searchQuery]);

  const filteredConstraints = useMemo(() => {
    if (!searchQuery) return availableConstraints;
    const query = searchQuery.toLowerCase();
    return availableConstraints.filter(
      c => c.name.toLowerCase().includes(query) || c.category.toLowerCase().includes(query)
    );
  }, [availableConstraints, searchQuery]);

  // Get connected nodes for current selection
  const connectedNodes = useMemo(() => {
    if (!dependencyGraph) return new Set<string>();

    const connected = new Set<string>();
    const selectedIds = [...selection.selectedResidents, ...selection.selectedConstraints];

    for (const edge of dependencyGraph.edges) {
      if (selectedIds.includes(edge.source)) {
        connected.add(edge.target);
      }
      if (selectedIds.includes(edge.target)) {
        connected.add(edge.source);
      }
    }

    return connected;
  }, [dependencyGraph, selection.selectedResidents, selection.selectedConstraints]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClearSelection();
    }
  }, [onClearSelection]);

  return (
    <div
      className="bg-slate-900 rounded-lg overflow-hidden"
      onKeyDown={handleKeyDown}
      tabIndex={0}
    >
      {/* Header with search */}
      <div className="p-3 border-b border-slate-800">
        <div className="relative">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search residents or constraints..."
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-violet-500"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-500 hover:text-white"
            >
              ✕
            </button>
          )}
        </div>
      </div>

      {/* Highlight Mode Toggle */}
      <div className="p-3 border-b border-slate-800">
        <label className="text-xs text-slate-400 block mb-2">Highlight Mode</label>
        <div className="grid grid-cols-2 gap-1">
          {(['dependencies', 'conflicts', 'correlations', 'none'] as const).map(mode => (
            <button
              key={mode}
              onClick={() => onSetHighlightMode(mode)}
              className={`px-2 py-1.5 text-xs rounded transition-colors ${
                selection.highlightMode === mode
                  ? 'bg-violet-600 text-white'
                  : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
              }`}
            >
              {mode.charAt(0).toUpperCase() + mode.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Selection Summary */}
      {(selection.selectedResidents.length > 0 || selection.selectedConstraints.length > 0) && (
        <div className="p-3 bg-violet-500/10 border-b border-slate-800">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-violet-300">Selected</span>
            <button
              onClick={onClearSelection}
              className="text-xs text-slate-400 hover:text-white"
            >
              Clear all
            </button>
          </div>
          <div className="flex flex-wrap gap-1">
            {selection.selectedResidents.map(id => (
              <span
                key={id}
                className="px-2 py-0.5 bg-violet-600/30 text-violet-300 rounded text-xs flex items-center gap-1"
              >
                {id}
                <button
                  onClick={() => onSelectResident(id, true)}
                  className="hover:text-white"
                >
                  ×
                </button>
              </span>
            ))}
            {selection.selectedConstraints.map(id => (
              <span
                key={id}
                className="px-2 py-0.5 bg-cyan-600/30 text-cyan-300 rounded text-xs flex items-center gap-1"
              >
                {id}
                <button
                  onClick={() => onSelectConstraint(id, true)}
                  className="hover:text-white"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Residents Section */}
      <div className="border-b border-slate-800">
        <button
          onClick={() => setExpandedSection(expandedSection === 'residents' ? null : 'residents')}
          className="w-full p-3 flex items-center justify-between text-left hover:bg-slate-800/50"
        >
          <span className="text-sm font-medium text-white">
            Residents ({filteredResidents.length})
          </span>
          <motion.span
            animate={{ rotate: expandedSection === 'residents' ? 180 : 0 }}
            className="text-slate-400"
          >
            ▼
          </motion.span>
        </button>

        <AnimatePresence>
          {expandedSection === 'residents' && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden"
            >
              <div className="max-h-48 overflow-y-auto p-2 space-y-1">
                {filteredResidents.length === 0 ? (
                  <div className="text-xs text-slate-500 p-2">No residents found</div>
                ) : (
                  filteredResidents.map(resident => {
                    const isSelected = selection.selectedResidents.includes(resident.id);
                    const isConnected = connectedNodes.has(resident.id);

                    return (
                      <button
                        key={resident.id}
                        onClick={(e) => onSelectResident(resident.id, e.shiftKey || e.ctrlKey || e.metaKey)}
                        className={`w-full text-left px-3 py-2 rounded text-sm transition-colors flex items-center gap-2 ${
                          isSelected
                            ? 'bg-violet-600 text-white'
                            : isConnected
                            ? 'bg-violet-500/20 text-violet-300 hover:bg-violet-500/30'
                            : 'text-slate-300 hover:bg-slate-800'
                        }`}
                      >
                        <span className={`w-2 h-2 rounded-full ${
                          isSelected ? 'bg-white' : isConnected ? 'bg-violet-400' : 'bg-slate-600'
                        }`} />
                        {resident.name}
                        {isConnected && !isSelected && (
                          <span className="ml-auto text-xs text-violet-400">linked</span>
                        )}
                      </button>
                    );
                  })
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Constraints Section */}
      <div>
        <button
          onClick={() => setExpandedSection(expandedSection === 'constraints' ? null : 'constraints')}
          className="w-full p-3 flex items-center justify-between text-left hover:bg-slate-800/50"
        >
          <span className="text-sm font-medium text-white">
            Constraints ({filteredConstraints.length})
          </span>
          <motion.span
            animate={{ rotate: expandedSection === 'constraints' ? 180 : 0 }}
            className="text-slate-400"
          >
            ▼
          </motion.span>
        </button>

        <AnimatePresence>
          {expandedSection === 'constraints' && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden"
            >
              <div className="max-h-48 overflow-y-auto p-2 space-y-1">
                {filteredConstraints.length === 0 ? (
                  <div className="text-xs text-slate-500 p-2">No constraints found</div>
                ) : (
                  filteredConstraints.map(constraint => {
                    const isSelected = selection.selectedConstraints.includes(constraint.id);
                    const isConnected = connectedNodes.has(constraint.id);

                    return (
                      <button
                        key={constraint.id}
                        onClick={(e) => onSelectConstraint(constraint.id, e.shiftKey || e.ctrlKey || e.metaKey)}
                        className={`w-full text-left px-3 py-2 rounded text-sm transition-colors ${
                          isSelected
                            ? 'bg-cyan-600 text-white'
                            : isConnected
                            ? 'bg-cyan-500/20 text-cyan-300 hover:bg-cyan-500/30'
                            : 'text-slate-300 hover:bg-slate-800'
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <span className={`w-2 h-2 rounded-full ${
                            isSelected ? 'bg-white' : isConnected ? 'bg-cyan-400' : 'bg-slate-600'
                          }`} />
                          <span className="flex-1 truncate">{constraint.name}</span>
                          <span className={`text-xs px-1.5 py-0.5 rounded ${
                            constraint.category === 'acgme' ? 'bg-red-500/20 text-red-300' :
                            constraint.category === 'coverage' ? 'bg-blue-500/20 text-blue-300' :
                            constraint.category === 'preference' ? 'bg-green-500/20 text-green-300' :
                            'bg-slate-500/20 text-slate-300'
                          }`}>
                            {constraint.category}
                          </span>
                        </div>
                      </button>
                    );
                  })
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Dependency Info */}
      {dependencyGraph && connectedNodes.size > 0 && (
        <div className="p-3 border-t border-slate-800 bg-slate-800/30">
          <div className="text-xs text-slate-400">
            <span className="text-violet-400">{connectedNodes.size}</span> connected nodes
            {' · '}
            <span className="text-cyan-400">{dependencyGraph.edges.length}</span> edges
          </div>
        </div>
      )}

      {/* Keyboard shortcuts hint */}
      <div className="p-2 border-t border-slate-800 bg-slate-950/50">
        <div className="text-xs text-slate-600 text-center">
          Hold <kbd className="px-1 py-0.5 bg-slate-800 rounded">Shift</kbd> to multi-select
          {' · '}
          <kbd className="px-1 py-0.5 bg-slate-800 rounded">Esc</kbd> to clear
        </div>
      </div>
    </div>
  );
}

export default InteractiveSelector;
