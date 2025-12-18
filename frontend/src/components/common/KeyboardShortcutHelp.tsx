'use client';

import { useState, useEffect } from 'react';
import { X, Keyboard } from 'lucide-react';

interface Shortcut {
  key: string;
  description: string;
  category: string;
}

const shortcuts: Shortcut[] = [
  // Navigation
  { key: 'g d', description: 'Go to Dashboard', category: 'Navigation' },
  { key: 'g s', description: 'Go to Schedule', category: 'Navigation' },
  { key: 'g p', description: 'Go to People', category: 'Navigation' },
  { key: 'g a', description: 'Go to Absences', category: 'Navigation' },

  // Actions
  { key: 'n', description: 'New item (context-aware)', category: 'Actions' },
  { key: 'e', description: 'Edit selected item', category: 'Actions' },
  { key: 'Delete', description: 'Delete selected item', category: 'Actions' },
  { key: 'Escape', description: 'Close modal / Cancel', category: 'Actions' },

  // List Navigation
  { key: 'j / ↓', description: 'Next item', category: 'List Navigation' },
  { key: 'k / ↑', description: 'Previous item', category: 'List Navigation' },
  { key: 'Enter', description: 'Open selected item', category: 'List Navigation' },

  // Help
  { key: '?', description: 'Show keyboard shortcuts', category: 'Help' },
];

export function KeyboardShortcutHelp() {
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === '?' && !e.ctrlKey && !e.metaKey) {
        // Don't trigger in input fields
        if (['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement).tagName)) return;
        e.preventDefault();
        setIsOpen(prev => !prev);
      }
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);

  if (!isOpen) return null;

  const categories = [...new Set(shortcuts.map(s => s.category))];

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setIsOpen(false)}>
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-auto" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex items-center gap-2">
            <Keyboard className="w-5 h-5" />
            <h2 className="text-lg font-semibold">Keyboard Shortcuts</h2>
          </div>
          <button onClick={() => setIsOpen(false)} className="p-1 hover:bg-gray-100 rounded" aria-label="Close keyboard shortcuts">
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="p-4 grid gap-6">
          {categories.map(category => (
            <div key={category}>
              <h3 className="text-sm font-medium text-gray-500 mb-2">{category}</h3>
              <div className="grid gap-2">
                {shortcuts.filter(s => s.category === category).map(shortcut => (
                  <div key={shortcut.key} className="flex items-center justify-between">
                    <span className="text-gray-700">{shortcut.description}</span>
                    <kbd className="px-2 py-1 bg-gray-100 rounded text-sm font-mono">{shortcut.key}</kbd>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
