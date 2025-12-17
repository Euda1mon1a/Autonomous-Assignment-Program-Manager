/**
 * ContactInfo Component
 *
 * Displays contact information (phone, pager, email) for on-call personnel.
 * Shows click-to-call and click-to-copy functionality.
 */

'use client';

import { useState } from 'react';
import { Phone, MessageSquare, Mail, Copy, Check } from 'lucide-react';
import type { OnCallPerson } from './types';

interface ContactInfoProps {
  person: OnCallPerson;
  showLabel?: boolean;
  compact?: boolean;
}

export function ContactInfo({
  person,
  showLabel = true,
  compact = false,
}: ContactInfoProps) {
  const [copiedField, setCopiedField] = useState<string | null>(null);

  const handleCopy = async (text: string, field: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedField(field);
      setTimeout(() => setCopiedField(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const hasContact = person.phone || person.pager || person.email;

  if (!hasContact) {
    return (
      <div className="text-sm text-gray-500 italic">
        No contact info available
      </div>
    );
  }

  if (compact) {
    return (
      <div className="flex gap-2 text-sm">
        {person.phone && (
          <a
            href={`tel:${person.phone}`}
            className="flex items-center gap-1 text-blue-600 hover:text-blue-800"
            title={`Call ${person.phone}`}
          >
            <Phone className="h-3 w-3" />
            <span>{person.phone}</span>
          </a>
        )}
        {person.pager && (
          <span className="flex items-center gap-1 text-gray-700" title="Pager">
            <MessageSquare className="h-3 w-3" />
            <span>{person.pager}</span>
          </span>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {showLabel && (
        <h4 className="text-sm font-semibold text-gray-700">Contact</h4>
      )}

      <div className="space-y-1">
        {person.phone && (
          <div className="flex items-center justify-between gap-2">
            <a
              href={`tel:${person.phone}`}
              className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-800"
            >
              <Phone className="h-4 w-4" />
              <span>{person.phone}</span>
            </a>
            <button
              onClick={() => handleCopy(person.phone!, 'phone')}
              className="p-1 hover:bg-gray-100 rounded"
              title="Copy phone number"
            >
              {copiedField === 'phone' ? (
                <Check className="h-3 w-3 text-green-600" />
              ) : (
                <Copy className="h-3 w-3 text-gray-500" />
              )}
            </button>
          </div>
        )}

        {person.pager && (
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 text-sm text-gray-700">
              <MessageSquare className="h-4 w-4" />
              <span>{person.pager}</span>
              <span className="text-xs text-gray-500">(Pager)</span>
            </div>
            <button
              onClick={() => handleCopy(person.pager!, 'pager')}
              className="p-1 hover:bg-gray-100 rounded"
              title="Copy pager number"
            >
              {copiedField === 'pager' ? (
                <Check className="h-3 w-3 text-green-600" />
              ) : (
                <Copy className="h-3 w-3 text-gray-500" />
              )}
            </button>
          </div>
        )}

        {person.email && (
          <div className="flex items-center justify-between gap-2">
            <a
              href={`mailto:${person.email}`}
              className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-800"
            >
              <Mail className="h-4 w-4" />
              <span className="truncate">{person.email}</span>
            </a>
            <button
              onClick={() => handleCopy(person.email!, 'email')}
              className="p-1 hover:bg-gray-100 rounded"
              title="Copy email"
            >
              {copiedField === 'email' ? (
                <Check className="h-3 w-3 text-green-600" />
              ) : (
                <Copy className="h-3 w-3 text-gray-500" />
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Compact contact badge for list views
 */
export function ContactBadge({ person }: { person: OnCallPerson }) {
  if (!person.phone && !person.pager) {
    return null;
  }

  return (
    <div className="flex gap-1">
      {person.phone && (
        <a
          href={`tel:${person.phone}`}
          className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-blue-50 text-blue-700 rounded hover:bg-blue-100"
          title={`Call ${person.phone}`}
        >
          <Phone className="h-3 w-3" />
          {person.phone}
        </a>
      )}
      {person.pager && (
        <span
          className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-gray-50 text-gray-700 rounded"
          title="Pager"
        >
          <MessageSquare className="h-3 w-3" />
          {person.pager}
        </span>
      )}
    </div>
  );
}
