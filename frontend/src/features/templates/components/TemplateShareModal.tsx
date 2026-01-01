'use client';

import { useState } from 'react';
import { X, Globe, Lock, Users, Copy, Check, Link2 } from 'lucide-react';
import type { ScheduleTemplate, TemplateShareRequest, TemplateDuplicateRequest } from '../types';
import { VISIBILITY_OPTIONS, CATEGORY_COLORS } from '../constants';

interface TemplateShareModalProps {
  template: ScheduleTemplate;
  mode: 'share' | 'duplicate';
  onShare?: (request: TemplateShareRequest) => Promise<void>;
  onDuplicate?: (request: TemplateDuplicateRequest) => Promise<void>;
  onClose: () => void;
  isLoading?: boolean;
}

export function TemplateShareModal({
  template,
  mode,
  onShare,
  onDuplicate,
  onClose,
  isLoading = false,
}: TemplateShareModalProps) {
  // Share state
  const [visibility, setVisibility] = useState(template.visibility);
  const [linkCopied, setLinkCopied] = useState(false);

  // Duplicate state
  const [newName, setNewName] = useState(`${template.name} (Copy)`);
  const [includePatterns, setIncludePatterns] = useState(true);

  const categoryColors = CATEGORY_COLORS[template.category];

  const handleShare = async () => {
    if (!onShare) return;

    await onShare({
      templateId: template.id,
      makePublic: visibility === 'public',
    });
    onClose();
  };

  const handleDuplicate = async () => {
    if (!onDuplicate) return;

    await onDuplicate({
      templateId: template.id,
      newName: newName.trim() || undefined,
      includePatterns,
    });
    onClose();
  };

  const handleCopyLink = () => {
    const link = `${window.location.origin}/templates/${template.id}`;
    navigator.clipboard.writeText(link);
    setLinkCopied(true);
    setTimeout(() => setLinkCopied(false), 2000);
  };

  const VisibilityIcon =
    visibility === 'public' ? Globe : visibility === 'shared' ? Users : Lock;

  if (mode === 'duplicate') {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center">
        <div className="absolute inset-0 bg-black/50" onClick={onClose} />
        <div className="relative bg-white rounded-lg shadow-xl w-full max-w-md mx-4" role="dialog" aria-labelledby="duplicate-dialog-title" aria-modal="true">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b">
            <div className="flex items-center gap-2">
              <Copy className="w-5 h-5 text-blue-600" aria-hidden="true" />
              <h2 id="duplicate-dialog-title" className="text-lg font-semibold">Duplicate Template</h2>
            </div>
            <button
              onClick={onClose}
              className="p-1 hover:bg-gray-100 rounded"
              aria-label="Close"
            >
              <X className="w-5 h-5" aria-hidden="true" />
            </button>
          </div>

          {/* Content */}
          <div className="p-4 space-y-4">
            {/* Source template info */}
            <div className={`p-3 rounded-lg ${categoryColors.bg} ${categoryColors.border} border`}>
              <div className="text-sm text-gray-600">Duplicating from:</div>
              <div className={`font-medium ${categoryColors.text}`}>{template.name}</div>
            </div>

            {/* New name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                New Template Name
              </label>
              <input
                type="text"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="Enter a name for the duplicate"
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            {/* Options */}
            <div className="space-y-2">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={includePatterns}
                  onChange={(e) => setIncludePatterns(e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700">
                  Include assignment patterns ({template.patterns.length} patterns)
                </span>
              </label>
            </div>

            {/* Info */}
            <div className="p-3 bg-gray-50 rounded-lg text-sm text-gray-600">
              <p>The duplicate will be created as a private template that you can customize.</p>
            </div>
          </div>

          {/* Footer */}
          <div className="p-4 border-t flex justify-end gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
              aria-label="Cancel"
            >
              Cancel
            </button>
            <button
              onClick={handleDuplicate}
              disabled={isLoading || !newName.trim()}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              aria-label="Create duplicate template"
            >
              <Copy className="w-4 h-4" aria-hidden="true" />
              {isLoading ? 'Duplicating...' : 'Create Duplicate'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Share mode
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white rounded-lg shadow-xl w-full max-w-md mx-4" role="dialog" aria-labelledby="share-dialog-title" aria-modal="true">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex items-center gap-2">
            <VisibilityIcon className="w-5 h-5 text-blue-600" aria-hidden="true" />
            <h2 id="share-dialog-title" className="text-lg font-semibold">Share Template</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded"
            aria-label="Close"
          >
            <X className="w-5 h-5" aria-hidden="true" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-4">
          {/* Template info */}
          <div className={`p-3 rounded-lg ${categoryColors.bg} ${categoryColors.border} border`}>
            <div className={`font-medium ${categoryColors.text}`}>{template.name}</div>
            {template.description && (
              <p className="text-sm text-gray-600 mt-1">{template.description}</p>
            )}
          </div>

          {/* Visibility options */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Who can see this template?
            </label>
            <div className="space-y-2">
              {VISIBILITY_OPTIONS.map((opt) => {
                const Icon = opt.icon === 'Lock' ? Lock : opt.icon === 'Users' ? Users : Globe;
                const isSelected = visibility === opt.value;

                return (
                  <label
                    key={opt.value}
                    className={`flex items-start gap-3 p-3 border rounded-lg cursor-pointer transition-colors ${
                      isSelected
                        ? 'border-blue-500 bg-blue-50'
                        : 'hover:bg-gray-50'
                    }`}
                  >
                    <input
                      type="radio"
                      name="visibility"
                      value={opt.value}
                      checked={isSelected}
                      onChange={(e) => setVisibility(e.target.value as typeof visibility)}
                      className="mt-1"
                      aria-label={opt.label}
                    />
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <Icon className={`w-4 h-4 ${isSelected ? 'text-blue-600' : 'text-gray-500'}`} aria-hidden="true" />
                        <span className="font-medium">{opt.label}</span>
                      </div>
                      <p className="text-sm text-gray-500 mt-0.5">{opt.description}</p>
                    </div>
                  </label>
                );
              })}
            </div>
          </div>

          {/* Share link */}
          {visibility !== 'private' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Share Link
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  readOnly
                  value={`${typeof window !== 'undefined' ? window.location.origin : ''}/templates/${template.id}`}
                  className="flex-1 px-3 py-2 border rounded-lg bg-gray-50 text-gray-600"
                />
                <button
                  onClick={handleCopyLink}
                  className={`px-3 py-2 rounded-lg flex items-center gap-2 ${
                    linkCopied
                      ? 'bg-green-100 text-green-700'
                      : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
                  }`}
                  aria-label={linkCopied ? 'Link copied' : 'Copy share link'}
                >
                  {linkCopied ? (
                    <>
                      <Check className="w-4 h-4" aria-hidden="true" />
                      Copied!
                    </>
                  ) : (
                    <>
                      <Link2 className="w-4 h-4" aria-hidden="true" />
                      Copy
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          {/* Current sharing status */}
          {template.sharedWith && template.sharedWith.length > 0 && (
            <div className="p-3 bg-gray-50 rounded-lg">
              <div className="text-sm font-medium text-gray-700 mb-1">
                Currently shared with:
              </div>
              <div className="flex flex-wrap gap-1">
                {template.sharedWith.map((userId) => (
                  <span
                    key={userId}
                    className="px-2 py-0.5 bg-white border rounded text-sm"
                  >
                    {userId}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
            aria-label="Cancel"
          >
            Cancel
          </button>
          <button
            onClick={handleShare}
            disabled={isLoading}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            aria-label="Save sharing changes"
          >
            <VisibilityIcon className="w-4 h-4" aria-hidden="true" />
            {isLoading ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>
    </div>
  );
}
