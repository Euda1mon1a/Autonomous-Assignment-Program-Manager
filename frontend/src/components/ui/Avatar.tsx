'use client';

import React from 'react';
import Image from 'next/image';
import { User } from 'lucide-react';

export type AvatarSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

export interface AvatarProps {
  src?: string;
  alt?: string;
  name?: string;
  size?: AvatarSize;
  status?: 'online' | 'offline' | 'away' | 'busy';
  className?: string;
}

const sizeStyles: Record<AvatarSize, string> = {
  xs: 'w-6 h-6 text-xs',
  sm: 'w-8 h-8 text-sm',
  md: 'w-10 h-10 text-base',
  lg: 'w-12 h-12 text-lg',
  xl: 'w-16 h-16 text-2xl',
};

const statusColors = {
  online: 'bg-green-500',
  offline: 'bg-gray-400',
  away: 'bg-amber-500',
  busy: 'bg-red-500',
};

const statusSizes: Record<AvatarSize, string> = {
  xs: 'w-1.5 h-1.5 border',
  sm: 'w-2 h-2 border',
  md: 'w-2.5 h-2.5 border-2',
  lg: 'w-3 h-3 border-2',
  xl: 'w-4 h-4 border-2',
};

/**
 * Get initials from a name
 */
function getInitials(name: string): string {
  return name
    .split(' ')
    .map((part) => part[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
}

/**
 * Avatar component with image, initials fallback, and status indicator
 *
 * @example
 * ```tsx
 * <Avatar src="/avatar.jpg" alt="John Doe" />
 * <Avatar name="Jane Smith" status="online" />
 * <Avatar size="lg" />
 * ```
 */
export function Avatar({
  src,
  alt = 'User avatar',
  name,
  size = 'md',
  status,
  className = '',
}: AvatarProps) {
  const [imageError, setImageError] = React.useState(false);

  const showImage = src && !imageError;
  const initials = name ? getInitials(name) : null;

  return (
    <div className={`relative inline-block ${className}`}>
      <div
        className={`${sizeStyles[size]} rounded-full bg-gray-200 text-gray-600 flex items-center justify-center font-medium overflow-hidden`}
      >
        {showImage ? (
          <Image
            src={src!}
            alt={alt}
            fill
            sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
            className="object-cover"
            onError={() => setImageError(true)}
          />
        ) : initials ? (
          <span aria-label={name || 'User initials'}>{initials}</span>
        ) : (
          <User className="w-1/2 h-1/2" aria-hidden="true" />
        )}
      </div>

      {status && (
        <span
          className={`absolute bottom-0 right-0 ${statusSizes[size]} ${statusColors[status]} rounded-full border-white`}
          role="status"
          aria-label={`Status: ${status}`}
        />
      )}
    </div>
  );
}

/**
 * Avatar group component with overlap
 */
export function AvatarGroup({
  avatars,
  max = 3,
  size = 'md',
  className = '',
}: {
  avatars: Array<{ src?: string; name?: string; alt?: string }>;
  max?: number;
  size?: AvatarSize;
  className?: string;
}) {
  const displayAvatars = avatars.slice(0, max);
  const remaining = Math.max(0, avatars.length - max);

  return (
    <div className={`flex items-center -space-x-2 ${className}`}>
      {displayAvatars.map((avatar, index) => (
        <Avatar
          key={index}
          {...avatar}
          size={size}
          className="ring-2 ring-white"
        />
      ))}
      {remaining > 0 && (
        <div
          className={`${sizeStyles[size]} rounded-full bg-gray-300 text-gray-700 flex items-center justify-center font-medium ring-2 ring-white`}
          aria-label={`${remaining} more users`}
        >
          +{remaining}
        </div>
      )}
    </div>
  );
}
