/**
 * Command Palette
 *
 * Global command palette for quick navigation and actions.
 * Trigger: Cmd+K / Ctrl+K
 */

'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { Command } from 'cmdk';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, X } from 'lucide-react';
import {
  createNavigationCommands,
  createActionCommands,
  CATEGORY_LABELS,
  type Command as CommandType,
  type CommandCategory,
} from './commands';

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState('');
  const router = useRouter();

  // Create commands with navigation
  const navigate = useCallback((path: string) => {
    router.push(path);
    setOpen(false);
    setSearch('');
  }, [router]);

  const commands = useMemo(() => {
    const navCommands = createNavigationCommands(navigate);
    const actionCommands = createActionCommands({
      onRefresh: () => window.location.reload(),
      onGoToToday: () => {},
    });
    return [...navCommands, ...actionCommands];
  }, [navigate]);

  // Group commands by category
  const commandsByCategory = useMemo(() => {
    const groups: Record<CommandCategory, CommandType[]> = {
      navigation: [],
      admin: [],
      actions: [],
      search: [],
    };

    commands.forEach(cmd => {
      groups[cmd.category].push(cmd);
    });

    return groups;
  }, [commands]);

  // Keyboard listener for Cmd+K / Ctrl+K
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't trigger in input fields (unless it's the command palette itself)
      const target = e.target as HTMLElement;
      const isCommandInput = target.closest('[cmdk-input]');
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName) && !isCommandInput) {
        return;
      }

      // Cmd+K or Ctrl+K to open
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setOpen(prev => !prev);
        return;
      }

      // Escape to close
      if (e.key === 'Escape' && open) {
        setOpen(false);
        setSearch('');
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [open]);

  // Execute command on select
  const handleSelect = useCallback((commandId: string) => {
    const command = commands.find(c => c.id === commandId);
    if (command) {
      command.action();
      setOpen(false);
      setSearch('');
    }
  }, [commands]);

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[100]"
            onClick={() => {
              setOpen(false);
              setSearch('');
            }}
          />

          {/* Command Palette */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -20 }}
            className="fixed top-[15%] left-1/2 -translate-x-1/2 z-[101] w-full max-w-xl mx-4"
          >
            <Command
              className="bg-white rounded-xl shadow-2xl overflow-hidden border border-gray-200"
              shouldFilter={true}
              loop
            >
              {/* Search Input */}
              <div className="flex items-center px-4 border-b border-gray-100">
                <Search className="w-5 h-5 text-gray-400 shrink-0" />
                <Command.Input
                  value={search}
                  onValueChange={setSearch}
                  placeholder="Search commands..."
                  className="flex-1 px-3 py-4 text-base bg-transparent outline-none placeholder:text-gray-400"
                />
                {search && (
                  <button
                    onClick={() => setSearch('')}
                    className="p-1 hover:bg-gray-100 rounded"
                  >
                    <X className="w-4 h-4 text-gray-400" />
                  </button>
                )}
                <kbd className="ml-2 px-2 py-1 text-xs font-mono text-gray-400 bg-gray-100 rounded">
                  esc
                </kbd>
              </div>

              {/* Command List */}
              <Command.List className="max-h-[400px] overflow-y-auto p-2">
                <Command.Empty className="py-6 text-center text-sm text-gray-500">
                  No commands found
                </Command.Empty>

                {/* Navigation Commands */}
                {commandsByCategory.navigation.length > 0 && (
                  <Command.Group
                    heading={CATEGORY_LABELS.navigation}
                    className="mb-2"
                  >
                    <div className="px-2 py-1 text-xs font-medium text-gray-400 uppercase tracking-wider">
                      {CATEGORY_LABELS.navigation}
                    </div>
                    {commandsByCategory.navigation.map(cmd => (
                      <CommandItem
                        key={cmd.id}
                        command={cmd}
                        onSelect={handleSelect}
                      />
                    ))}
                  </Command.Group>
                )}

                {/* Admin Commands */}
                {commandsByCategory.admin.length > 0 && (
                  <Command.Group
                    heading={CATEGORY_LABELS.admin}
                    className="mb-2"
                  >
                    <div className="px-2 py-1 text-xs font-medium text-gray-400 uppercase tracking-wider">
                      {CATEGORY_LABELS.admin}
                    </div>
                    {commandsByCategory.admin.map(cmd => (
                      <CommandItem
                        key={cmd.id}
                        command={cmd}
                        onSelect={handleSelect}
                      />
                    ))}
                  </Command.Group>
                )}

                {/* Action Commands */}
                {commandsByCategory.actions.length > 0 && (
                  <Command.Group
                    heading={CATEGORY_LABELS.actions}
                    className="mb-2"
                  >
                    <div className="px-2 py-1 text-xs font-medium text-gray-400 uppercase tracking-wider">
                      {CATEGORY_LABELS.actions}
                    </div>
                    {commandsByCategory.actions.map(cmd => (
                      <CommandItem
                        key={cmd.id}
                        command={cmd}
                        onSelect={handleSelect}
                      />
                    ))}
                  </Command.Group>
                )}
              </Command.List>

              {/* Footer */}
              <div className="flex items-center justify-between px-4 py-2 border-t border-gray-100 bg-gray-50 text-xs text-gray-500">
                <div className="flex items-center gap-4">
                  <span className="flex items-center gap-1">
                    <kbd className="px-1.5 py-0.5 bg-gray-200 rounded font-mono">↑↓</kbd>
                    navigate
                  </span>
                  <span className="flex items-center gap-1">
                    <kbd className="px-1.5 py-0.5 bg-gray-200 rounded font-mono">↵</kbd>
                    select
                  </span>
                </div>
                <span className="flex items-center gap-1">
                  <kbd className="px-1.5 py-0.5 bg-gray-200 rounded font-mono">⌘K</kbd>
                  toggle
                </span>
              </div>
            </Command>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

/**
 * Individual command item
 */
function CommandItem({
  command,
  onSelect,
}: {
  command: CommandType;
  onSelect: (id: string) => void;
}) {
  const Icon = command.icon;

  return (
    <Command.Item
      value={`${command.label} ${command.description || ''} ${command.keywords?.join(' ') || ''}`}
      onSelect={() => onSelect(command.id)}
      className="flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer text-gray-700 data-[selected=true]:bg-blue-50 data-[selected=true]:text-blue-700 transition-colors"
    >
      <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-gray-100 data-[selected=true]:bg-blue-100 shrink-0">
        <Icon className="w-4 h-4" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="font-medium truncate">{command.label}</div>
        {command.description && (
          <div className="text-xs text-gray-500 truncate">{command.description}</div>
        )}
      </div>
      {command.shortcut && (
        <kbd className="px-2 py-1 text-xs font-mono text-gray-400 bg-gray-100 rounded shrink-0">
          {command.shortcut}
        </kbd>
      )}
    </Command.Item>
  );
}

export default CommandPalette;
