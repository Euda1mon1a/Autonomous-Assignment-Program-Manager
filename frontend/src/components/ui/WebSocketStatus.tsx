'use client';

/**
 * WebSocketStatus Component
 *
 * Displays the current WebSocket connection state with visual indicators.
 * Shows: Live (green), Connecting (blue), Reconnecting (yellow), Offline (gray)
 */

import { Tooltip } from '@/components/ui/Tooltip';
import { Wifi, WifiOff, Loader2 } from 'lucide-react';
import type { ConnectionState } from '@/hooks/useWebSocket';

interface WebSocketStatusProps {
  connectionState: ConnectionState;
  reconnectAttempts?: number;
}

const statusConfig = {
  connected: {
    icon: Wifi,
    color: 'text-green-600',
    bg: 'bg-green-100',
    label: 'Live',
    animate: false,
  },
  connecting: {
    icon: Loader2,
    color: 'text-blue-600',
    bg: 'bg-blue-100',
    label: 'Connecting',
    animate: true,
  },
  reconnecting: {
    icon: Loader2,
    color: 'text-yellow-600',
    bg: 'bg-yellow-100',
    label: 'Reconnecting',
    animate: true,
  },
  disconnected: {
    icon: WifiOff,
    color: 'text-gray-400',
    bg: 'bg-gray-100',
    label: 'Offline',
    animate: false,
  },
} as const;

export function WebSocketStatus({
  connectionState,
  reconnectAttempts = 0,
}: WebSocketStatusProps) {
  const config = statusConfig[connectionState];
  const Icon = config.icon;

  const tooltipContent = `WebSocket: ${config.label}${
    reconnectAttempts > 0 ? ` (attempt ${reconnectAttempts})` : ''
  }`;

  return (
    <Tooltip content={tooltipContent}>
      <div
        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${config.bg} ${config.color}`}
      >
        <Icon className={`w-3 h-3 ${config.animate ? 'animate-spin' : ''}`} />
        <span>{config.label}</span>
      </div>
    </Tooltip>
  );
}
