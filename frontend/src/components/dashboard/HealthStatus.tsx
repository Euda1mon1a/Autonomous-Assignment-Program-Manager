'use client'

import { Activity, Database, Server, Wifi, WifiOff, AlertCircle, CheckCircle2 } from 'lucide-react'
import { motion } from 'framer-motion'
import { useHealthReady } from '@/hooks/useHealth'

interface ServiceIndicatorProps {
  name: string
  isHealthy: boolean | undefined
  icon: React.ReactNode
}

function ServiceIndicator({ name, isHealthy, icon }: ServiceIndicatorProps) {
  const statusColor = isHealthy === undefined
    ? 'bg-gray-100 text-gray-400'
    : isHealthy
      ? 'bg-green-100 text-green-600'
      : 'bg-red-100 text-red-600'

  return (
    <div className="flex items-center gap-2">
      <div className={`p-1.5 rounded-md ${statusColor}`}>
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-700 truncate">{name}</p>
        <p className={`text-xs ${isHealthy ? 'text-green-600' : isHealthy === false ? 'text-red-600' : 'text-gray-400'}`}>
          {isHealthy === undefined ? 'Checking...' : isHealthy ? 'Healthy' : 'Unhealthy'}
        </p>
      </div>
      {isHealthy !== undefined && (
        isHealthy ? (
          <CheckCircle2 className="w-4 h-4 text-green-500 flex-shrink-0" />
        ) : (
          <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0" />
        )
      )}
    </div>
  )
}

/**
 * Health Status Dashboard Widget
 *
 * Displays real-time system health status including
 * database and Redis connectivity.
 */
export function HealthStatus() {
  const { data, isLoading, isError, error } = useHealthReady({
    refetchInterval: 30_000, // Check every 30 seconds
  })

  const overallHealthy = data?.status === 'healthy'
  const isConnected = !isError && data !== undefined

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: 'easeOut', delay: 0.3 }}
      className="glass-panel p-6"
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">System Health</h3>
        {isConnected ? (
          <div className="flex items-center gap-1.5">
            <Wifi className="w-4 h-4 text-green-500" />
            <span className="text-xs text-green-600 font-medium">Connected</span>
          </div>
        ) : (
          <div className="flex items-center gap-1.5">
            <WifiOff className="w-4 h-4 text-red-500" />
            <span className="text-xs text-red-600 font-medium">Disconnected</span>
          </div>
        )}
      </div>

      {isLoading ? (
        <div className="space-y-3">
          <div className="animate-pulse h-10 bg-gray-200 rounded"></div>
          <div className="animate-pulse h-10 bg-gray-200 rounded"></div>
        </div>
      ) : isError ? (
        <div className="text-center py-4">
          <WifiOff className="w-8 h-8 text-red-400 mx-auto mb-2" />
          <p className="text-sm text-red-600 font-medium">Connection Failed</p>
          <p className="text-xs text-gray-500 mt-1">
            {error instanceof Error ? error.message : 'Unable to reach API server'}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {/* Overall Status Banner */}
          <div className={`rounded-lg p-3 ${overallHealthy ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
            <div className="flex items-center gap-2">
              <Activity className={`w-5 h-5 ${overallHealthy ? 'text-green-600' : 'text-red-600'}`} />
              <span className={`font-medium ${overallHealthy ? 'text-green-700' : 'text-red-700'}`}>
                {overallHealthy ? 'All Systems Operational' : 'System Issues Detected'}
              </span>
            </div>
          </div>

          {/* Individual Services */}
          <div className="space-y-2 pt-2">
            <ServiceIndicator
              name="Database"
              isHealthy={data?.database}
              icon={<Database className="w-4 h-4" />}
            />
            <ServiceIndicator
              name="Cache (Redis)"
              isHealthy={data?.redis}
              icon={<Server className="w-4 h-4" />}
            />
          </div>

          {/* Last Updated */}
          {data?.timestamp && (
            <p className="text-xs text-gray-400 pt-2 border-t border-gray-100">
              Last checked: {new Date(data.timestamp).toLocaleTimeString()}
            </p>
          )}
        </div>
      )}
    </motion.div>
  )
}
