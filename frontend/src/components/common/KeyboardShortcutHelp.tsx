'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { X, Keyboard, Command } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface Shortcut {
  key: string;
  description: string;
  category: string;
  action?: () => void;
}

// Navigation shortcuts with router integration
const createShortcuts = (router: ReturnType<typeof useRouter>): Shortcut[] => [
  // Navigation
  { key: 'g d', description: 'Go to Dashboard', category: 'Navigation', action: () => router.push('/') },
  { key: 'g s', description: 'Go to Schedule', category: 'Navigation', action: () => router.push('/schedule') },
  { key: 'g m', description: 'Go to My Schedule', category: 'Navigation', action: () => router.push('/my-schedule') },
  { key: 'g p', description: 'Go to People', category: 'Navigation', action: () => router.push('/people') },
  { key: 'g a', description: 'Go to Absences', category: 'Navigation', action: () => router.push('/absences') },
  { key: 'g r', description: 'Go to Rotations', category: 'Navigation', action: () => router.push('/rotations') },
  { key: 'g w', description: 'Go to Swap Marketplace', category: 'Navigation', action: () => router.push('/swap-marketplace') },
  { key: 'g h', description: 'Go to Holidays', category: 'Navigation', action: () => router.push('/holidays') },

  // Schedule Actions
  { key: 'Alt+n', description: 'New assignment', category: 'Schedule Actions' },
  { key: 'Alt+e', description: 'Export schedule', category: 'Schedule Actions' },
  { key: 'Alt+p', description: 'Print schedule', category: 'Schedule Actions' },
  { key: 'Alt+r', description: 'Refresh data', category: 'Schedule Actions' },
  { key: 'Alt+l', description: 'Lock/unlock assignment', category: 'Schedule Actions' },

  // General Actions
  { key: 'n', description: 'New item (context-aware)', category: 'General Actions' },
  { key: 'e', description: 'Edit selected item', category: 'General Actions' },
  { key: 'Delete', description: 'Delete selected item', category: 'General Actions' },
  { key: 'Ctrl+s', description: 'Save changes', category: 'General Actions' },
  { key: 'Ctrl+z', description: 'Undo last action', category: 'General Actions' },
  { key: 'Escape', description: 'Close modal / Cancel', category: 'General Actions' },

  // List Navigation
  { key: 'j / ↓', description: 'Next item', category: 'List Navigation' },
  { key: 'k / ↑', description: 'Previous item', category: 'List Navigation' },
  { key: 'Enter', description: 'Open selected item', category: 'List Navigation' },
  { key: 'Space', description: 'Toggle selection', category: 'List Navigation' },

  // Date Navigation (Schedule)
  { key: '← / →', description: 'Previous/next period', category: 'Date Navigation' },
  { key: 't', description: 'Go to today', category: 'Date Navigation' },
  { key: '1', description: 'Week view', category: 'Date Navigation' },
  { key: '2', description: '2-week view', category: 'Date Navigation' },
  { key: '3', description: 'Month view', category: 'Date Navigation' },

  // Help
  { key: '?', description: 'Show keyboard shortcuts', category: 'Help' },
  { key: 'Ctrl+/', description: 'Search (command palette)', category: 'Help' },
];

export function KeyboardShortcutHelp() {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const router = useRouter();
  const shortcuts = createShortcuts(router);

  // Handle keyboard shortcut sequences
  const [keySequence, setKeySequence] = useState<string[]>([]);
  const [sequenceTimeout, setSequenceTimeout] = useState<NodeJS.Timeout | null>(null);

  const resetSequence = useCallback(() => {
    setKeySequence([]);
    if (sequenceTimeout) {
      clearTimeout(sequenceTimeout);
      setSequenceTimeout(null);
    }
  }, [sequenceTimeout]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't trigger in input fields
      const target = e.target as HTMLElement;
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName)) {
        if (e.key === 'Escape') {
          (target as HTMLInputElement).blur();
        }
        return;
      }

      // Toggle help modal
      if (e.key === '?' && !e.ctrlKey && !e.metaKey) {
        e.preventDefault();
        setIsOpen(prev => !prev);
        return;
      }

      // Close modal on Escape
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false);
        setSearchQuery('');
        return;
      }

      // Command palette trigger
      if ((e.ctrlKey || e.metaKey) && e.key === '/') {
        e.preventDefault();
        setIsOpen(true);
        return;
      }

      // Handle 'g' prefix for navigation shortcuts
      if (e.key === 'g' && !e.ctrlKey && !e.metaKey && !e.altKey) {
        e.preventDefault();
        setKeySequence(['g']);

        // Set timeout to reset sequence
        if (sequenceTimeout) clearTimeout(sequenceTimeout);
        const timeout = setTimeout(resetSequence, 1000);
        setSequenceTimeout(timeout);
        return;
      }

      // Handle second key in sequence
      if (keySequence.length > 0 && keySequence[0] === 'g') {
        e.preventDefault();
        const fullKey = `g ${e.key}`;
        const shortcut = shortcuts.find(s => s.key === fullKey);
        if (shortcut?.action) {
          shortcut.action();
        }
        resetSequence();
        return;
      }

      // Handle single key shortcuts
      const key = e.key.toLowerCase();
      if (key === 't' && !e.ctrlKey && !e.metaKey) {
        // Go to today - dispatch custom event for schedule components
        window.dispatchEvent(new CustomEvent('keyboard-shortcut', { detail: { action: 'go-to-today' } }));
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      if (sequenceTimeout) clearTimeout(sequenceTimeout);
    };
  }, [isOpen, keySequence, router, sequenceTimeout, resetSequence, shortcuts]);

  // Filter shortcuts based on search
  const filteredShortcuts = searchQuery
    ? shortcuts.filter(s =>
        s.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
        s.key.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : shortcuts;

  const categories = Array.from(new Set(filteredShortcuts.map(s => s.category)));

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50"
            onClick={() => {
              setIsOpen(false);
              setSearchQuery('');
            }}
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -20 }}
            role="dialog"
            aria-modal="true"
            aria-labelledby="keyboard-shortcuts-title"
            className="fixed top-[10%] left-1/2 -translate-x-1/2 z-50 w-full max-w-2xl mx-4"
            onClick={e => e.stopPropagation()}
          >
            <div className="bg-white rounded-xl shadow-2xl max-h-[80vh] overflow-hidden flex flex-col">
              {/* Header */}
              <div className="flex items-center justify-between p-4 border-b bg-gray-50">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <Keyboard className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <h2 id="keyboard-shortcuts-title" className="text-lg font-semibold text-gray-900">Keyboard Shortcuts</h2>
                    <p className="text-sm text-gray-500">Navigate faster with keyboard commands</p>
                  </div>
                </div>
                <button
                  onClick={() => {
                    setIsOpen(false);
                    setSearchQuery('');
                  }}
                  className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
                  aria-label="Close"
                >
                  <X className="w-5 h-5 text-gray-500" />
                </button>
              </div>

              {/* Search */}
              <div className="p-4 border-b">
                <div className="relative">
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search shortcuts..."
                    className="w-full px-4 py-2 pl-10 bg-gray-100 border border-transparent rounded-lg text-sm focus:bg-white focus:border-blue-300 focus:ring-2 focus:ring-blue-100 transition-all"
                    autoFocus
                  />
                  <Command className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                </div>
              </div>

              {/* Shortcuts List */}
              <div className="flex-1 overflow-y-auto p-4">
                {filteredShortcuts.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    No shortcuts found for "{searchQuery}"
                  </div>
                ) : (
                  <div className="grid gap-6">
                    {categories.map(category => (
                      <div key={category}>
                        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
                          {category}
                        </h3>
                        <div className="grid gap-2">
                          {filteredShortcuts
                            .filter(s => s.category === category)
                            .map(shortcut => (
                              <div
                                key={shortcut.key}
                                className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-gray-50 transition-colors group"
                              >
                                <span className="text-gray-700 group-hover:text-gray-900">
                                  {shortcut.description}
                                </span>
                                <div className="flex items-center gap-1">
                                  {shortcut.key.split(' + ').map((key, i) => (
                                    <span key={i} className="flex items-center gap-1">
                                      {i > 0 && <span className="text-gray-400 text-xs">+</span>}
                                      <kbd className="px-2 py-1 bg-gray-100 border border-gray-200 rounded text-xs font-mono text-gray-600 shadow-sm">
                                        {key.split(' ').map((k, j) => (
                                          <span key={j}>
                                            {j > 0 && <span className="text-gray-400 mx-0.5">then</span>}
                                            {k}
                                          </span>
                                        ))}
                                      </kbd>
                                    </span>
                                  ))}
                                </div>
                              </div>
                            ))}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Footer */}
              <div className="p-4 border-t bg-gray-50 text-center text-xs text-gray-500">
                Press <kbd className="px-1.5 py-0.5 bg-gray-200 rounded font-mono">?</kbd> anytime to toggle this help
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

/**
 * Hook to listen for keyboard shortcut events
 */
export function useKeyboardShortcut(action: string, callback: () => void) {
  useEffect(() => {
    const handleShortcut = (e: CustomEvent<{ action: string }>) => {
      if (e.detail.action === action) {
        callback();
      }
    };

    window.addEventListener('keyboard-shortcut', handleShortcut as EventListener);
    return () => window.removeEventListener('keyboard-shortcut', handleShortcut as EventListener);
  }, [action, callback]);
}
