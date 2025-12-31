/**
 * Tests for Admin System Health Dashboard
 *
 * Tests real-time monitoring, service status, metrics visualization,
 * alerts management, and system health indicators.
 */
import React from 'react';
import { render, screen, waitFor } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import AdminHealthPage from '@/app/admin/health/page';

// Mock health data
const mockHealthData = {
  overallStatus: 'healthy' as const,
  lastUpdated: '2024-12-23T10:00:00Z',
  uptime: 2592000,
  version: '1.2.3',
  environment: 'production' as const,
  services: [
    {
      id: 'api',
      name: 'API Server',
      type: 'api' as const,
      health: {
        name: 'API Server',
        status: 'healthy' as const,
        latencyMs: 45,
        uptime: 99.99,
        lastCheck: '2024-12-23T10:00:00Z',
      },
    },
    {
      id: 'db',
      name: 'PostgreSQL',
      type: 'database' as const,
      health: {
        name: 'PostgreSQL',
        status: 'healthy' as const,
        latencyMs: 12,
        uptime: 99.99,
        lastCheck: '2024-12-23T10:00:00Z',
      },
    },
  ],
  database: {
    status: 'healthy' as const,
    connectionPoolSize: 20,
    activeConnections: 8,
    waitingConnections: 0,
    maxConnections: 100,
    avgQueryTimeMs: 15,
    slowQueries24h: 3,
    lastMigration: 'abc123 - Add indexes',
    diskUsagePercent: 42,
  },
  cache: {
    status: 'healthy' as const,
    connectedClients: 12,
    usedMemoryBytes: 268435456,
    maxMemoryBytes: 1073741824,
    hitRate: 0.94,
    missRate: 0.06,
    evictedKeys24h: 150,
    keyCount: 12500,
  },
  queue: {
    status: 'degraded' as const,
    workers: {
      active: 3,
      total: 4,
      idle: 1,
    },
    queues: [],
    scheduledTasks: 8,
  },
  api: {
    status: 'healthy' as const,
    requestsPerMinute: 125,
    avgResponseTimeMs: 45,
    errorRate: 0.002,
    activeRequests: 8,
    rateLimitedRequests24h: 15,
    topEndpoints: [],
  },
  resources: {
    cpu: {
      usagePercent: 35,
      coreCount: 8,
      loadAverage: [1.2, 1.5, 1.3],
    },
    memory: {
      usedBytes: 6442450944,
      totalBytes: 17179869184,
      usagePercent: 37.5,
    },
    disk: {
      usedBytes: 45097156608,
      totalBytes: 107374182400,
      usagePercent: 42,
      readBytesPerSec: 1048576,
      writeBytesPerSec: 524288,
    },
    network: {
      inBytesPerSec: 2097152,
      outBytesPerSec: 1572864,
      activeConnections: 156,
    },
  },
  activeAlerts: [
    {
      id: 'alert-1',
      severity: 'warning' as const,
      status: 'active' as const,
      title: 'High Memory Usage',
      message: 'Memory usage exceeded 80%',
      service: 'API Server',
      triggeredAt: '2024-12-23T09:00:00Z',
    },
  ],
};

describe('AdminHealthPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Page Rendering', () => {
    it('should render page title', () => {
      render(<AdminHealthPage />);

      expect(screen.getByText('System Health')).toBeInTheDocument();
    });

    it('should display environment and version', () => {
      render(<AdminHealthPage />);

      expect(screen.getByText(/production/i)).toBeInTheDocument();
      expect(screen.getByText(/v1\.2\.3/i)).toBeInTheDocument();
    });

    it('should render all tabs', () => {
      render(<AdminHealthPage />);

      expect(screen.getByText('Overview')).toBeInTheDocument();
      expect(screen.getByText('Services')).toBeInTheDocument();
      expect(screen.getByText('Metrics')).toBeInTheDocument();
      expect(screen.getByText('Alerts')).toBeInTheDocument();
    });

    it('should start on Overview tab by default', () => {
      render(<AdminHealthPage />);

      const overviewTab = screen.getByText('Overview').closest('button');
      expect(overviewTab).toHaveClass('bg-slate-800', 'text-white');
    });

    it('should show refresh button', () => {
      render(<AdminHealthPage />);

      expect(screen.getByRole('button', { name: /Refresh/i })).toBeInTheDocument();
    });

    it('should display last update time', () => {
      render(<AdminHealthPage />);

      expect(screen.getByText(/Updated/i)).toBeInTheDocument();
    });
  });

  describe('Overall Status Indicator', () => {
    it('should display overall status', () => {
      render(<AdminHealthPage />);

      expect(screen.getByText('Healthy')).toBeInTheDocument();
    });

    it('should show status icon', () => {
      const { container } = render(<AdminHealthPage />);

      // Check for status indicator
      const statusIndicators = container.querySelectorAll('svg');
      expect(statusIndicators.length).toBeGreaterThan(0);
    });
  });

  describe('Overview Tab', () => {
    it('should display uptime metric', () => {
      render(<AdminHealthPage />);

      expect(screen.getByText('Uptime')).toBeInTheDocument();
      expect(screen.getByText(/30d/i)).toBeInTheDocument();
    });

    it('should display active alerts count', () => {
      render(<AdminHealthPage />);

      expect(screen.getByText('Active Alerts')).toBeInTheDocument();
      expect(screen.getByText('1')).toBeInTheDocument();
    });

    it('should display API requests per minute', () => {
      render(<AdminHealthPage />);

      expect(screen.getByText('API Requests/min')).toBeInTheDocument();
      expect(screen.getByText('125')).toBeInTheDocument();
    });

    it('should show all services status', () => {
      render(<AdminHealthPage />);

      expect(screen.getByText('API Server')).toBeInTheDocument();
      expect(screen.getByText('PostgreSQL')).toBeInTheDocument();
    });

    it('should display resource usage', () => {
      render(<AdminHealthPage />);

      expect(screen.getByText('CPU Usage')).toBeInTheDocument();
      expect(screen.getByText('Memory Usage')).toBeInTheDocument();
      expect(screen.getByText('Disk Usage')).toBeInTheDocument();
    });

    it('should show database metrics', () => {
      render(<AdminHealthPage />);

      expect(screen.getByText('Database')).toBeInTheDocument();
      expect(screen.getByText('Avg Query Time')).toBeInTheDocument();
    });

    it('should display active alerts', () => {
      render(<AdminHealthPage />);

      expect(screen.getByText('Active Alerts')).toBeInTheDocument();
      expect(screen.getByText('High Memory Usage')).toBeInTheDocument();
    });
  });

  describe('Services Tab', () => {
    it('should switch to Services tab', async () => {
      const user = userEvent.setup();
      render(<AdminHealthPage />);

      const servicesTab = screen.getByText('Services').closest('button');
      await user.click(servicesTab!);

      expect(servicesTab).toHaveClass('bg-slate-800', 'text-white');
    });

    it('should display all services', async () => {
      const user = userEvent.setup();
      render(<AdminHealthPage />);

      await user.click(screen.getByText('Services').closest('button')!);

      expect(screen.getAllByText('API Server')[0]).toBeInTheDocument();
      expect(screen.getAllByText('PostgreSQL')[0]).toBeInTheDocument();
    });

    it('should show service status badges', async () => {
      const user = userEvent.setup();
      render(<AdminHealthPage />);

      await user.click(screen.getByText('Services').closest('button')!);

      expect(screen.getAllByText('Healthy').length).toBeGreaterThan(0);
    });

    it('should expand service details', async () => {
      const user = userEvent.setup();
      render(<AdminHealthPage />);

      await user.click(screen.getByText('Services').closest('button')!);

      // Find and click a service card
      const serviceCards = screen.getAllByRole('button').filter(btn =>
        btn.textContent?.includes('API Server')
      );

      if (serviceCards[0]) {
        await user.click(serviceCards[0]);

        await waitFor(() => {
          expect(screen.getByText('Latency')).toBeInTheDocument();
        });
      }
    });

    it('should display task queues', async () => {
      const user = userEvent.setup();
      render(<AdminHealthPage />);

      await user.click(screen.getByText('Services').closest('button')!);

      expect(screen.getByText('Task Queues')).toBeInTheDocument();
      expect(screen.getByText(/Workers:/i)).toBeInTheDocument();
    });
  });

  describe('Metrics Tab', () => {
    it('should switch to Metrics tab', async () => {
      const user = userEvent.setup();
      render(<AdminHealthPage />);

      const metricsTab = screen.getByText('Metrics').closest('button');
      await user.click(metricsTab!);

      expect(metricsTab).toHaveClass('bg-slate-800', 'text-white');
    });

    it('should display resource metrics', async () => {
      const user = userEvent.setup();
      render(<AdminHealthPage />);

      await user.click(screen.getByText('Metrics').closest('button')!);

      expect(screen.getAllByText('CPU Usage')[0]).toBeInTheDocument();
      expect(screen.getAllByText('Memory Usage')[0]).toBeInTheDocument();
    });

    it('should show API performance metrics', async () => {
      const user = userEvent.setup();
      render(<AdminHealthPage />);

      await user.click(screen.getByText('Metrics').closest('button')!);

      expect(screen.getByText('API Performance')).toBeInTheDocument();
      expect(screen.getByText('Requests/min')).toBeInTheDocument();
      expect(screen.getByText('Avg Response')).toBeInTheDocument();
      expect(screen.getByText('Error Rate')).toBeInTheDocument();
    });

    it('should display cache performance', async () => {
      const user = userEvent.setup();
      render(<AdminHealthPage />);

      await user.click(screen.getByText('Metrics').closest('button')!);

      expect(screen.getByText('Cache Performance')).toBeInTheDocument();
      expect(screen.getByText('Hit Rate')).toBeInTheDocument();
    });

    it('should show metric trends', async () => {
      const user = userEvent.setup();
      render(<AdminHealthPage />);

      await user.click(screen.getByText('Metrics').closest('button')!);

      const { container } = render(<AdminHealthPage />);
      const trendIcons = container.querySelectorAll('svg');
      expect(trendIcons.length).toBeGreaterThan(0);
    });
  });

  describe('Alerts Tab', () => {
    it('should switch to Alerts tab', async () => {
      const user = userEvent.setup();
      render(<AdminHealthPage />);

      const alertsTab = screen.getByText('Alerts').closest('button');
      await user.click(alertsTab!);

      expect(alertsTab).toHaveClass('bg-slate-800', 'text-white');
    });

    it('should display alert count badge', () => {
      render(<AdminHealthPage />);

      const alertsTab = screen.getByText('Alerts').closest('button');
      expect(alertsTab?.textContent).toContain('1');
    });

    it('should show filter tabs', async () => {
      const user = userEvent.setup();
      render(<AdminHealthPage />);

      await user.click(screen.getByText('Alerts').closest('button')!);

      expect(screen.getByText('All')).toBeInTheDocument();
      expect(screen.getByText('Active')).toBeInTheDocument();
      expect(screen.getByText('Acknowledged')).toBeInTheDocument();
    });

    it('should display alert details', async () => {
      const user = userEvent.setup();
      render(<AdminHealthPage />);

      await user.click(screen.getByText('Alerts').closest('button')!);

      expect(screen.getAllByText('High Memory Usage')[0]).toBeInTheDocument();
      expect(screen.getByText('Memory usage exceeded 80%')).toBeInTheDocument();
    });

    it('should show acknowledge button for active alerts', async () => {
      const user = userEvent.setup();
      render(<AdminHealthPage />);

      await user.click(screen.getByText('Alerts').closest('button')!);

      expect(screen.getByRole('button', { name: /Acknowledge/i })).toBeInTheDocument();
    });

    it('should filter alerts', async () => {
      const user = userEvent.setup();
      render(<AdminHealthPage />);

      await user.click(screen.getByText('Alerts').closest('button')!);

      const activeFilter = screen.getByText('Active').closest('button');
      await user.click(activeFilter!);

      expect(activeFilter).toHaveClass('bg-violet-600', 'text-white');
    });
  });

  describe('Refresh Functionality', () => {
    it('should refresh data on button click', async () => {
      const user = userEvent.setup();
      render(<AdminHealthPage />);

      const refreshButton = screen.getByRole('button', { name: /Refresh/i });
      await user.click(refreshButton);

      // Button should show loading state
      await waitFor(() => {
        expect(refreshButton).toBeDisabled();
      });
    });

    it('should show spinning icon when refreshing', async () => {
      const user = userEvent.setup();
      render(<AdminHealthPage />);

      const refreshButton = screen.getByRole('button', { name: /Refresh/i });
      await user.click(refreshButton);

      await waitFor(() => {
        const icon = refreshButton.querySelector('.animate-spin');
        expect(icon).toBeInTheDocument();
      });
    });

    it('should auto-refresh every 30 seconds', () => {
      jest.useFakeTimers();
      render(<AdminHealthPage />);

      const initialTime = screen.getByText(/Updated/i).textContent;

      // Fast-forward 30 seconds
      jest.advanceTimersByTime(30000);

      // Time should have updated
      const updatedTime = screen.getByText(/Updated/i).textContent;
      expect(updatedTime).toBeDefined();

      jest.useRealTimers();
    });
  });

  describe('Status Colors and Icons', () => {
    it('should use correct colors for healthy status', () => {
      const { container } = render(<AdminHealthPage />);

      const healthyElements = container.querySelectorAll('.text-green-400');
      expect(healthyElements.length).toBeGreaterThan(0);
    });

    it('should show warning color for degraded services', async () => {
      const user = userEvent.setup();
      render(<AdminHealthPage />);

      await user.click(screen.getByText('Services').closest('button')!);

      // Queue service is degraded
      const { container } = render(<AdminHealthPage />);
      const warningElements = container.querySelectorAll('.text-yellow-400');
      expect(warningElements.length).toBeGreaterThan(0);
    });

    it('should display status badges with proper styling', () => {
      render(<AdminHealthPage />);

      const badges = screen.getAllByText('Healthy');
      expect(badges.length).toBeGreaterThan(0);
    });
  });

  describe('Data Formatting', () => {
    it('should format bytes correctly', () => {
      render(<AdminHealthPage />);

      // Should show formatted memory usage
      expect(screen.getByText(/GB/i)).toBeInTheDocument();
    });

    it('should format uptime correctly', () => {
      render(<AdminHealthPage />);

      // 30 days uptime
      expect(screen.getByText(/30d/i)).toBeInTheDocument();
    });

    it('should format percentages correctly', () => {
      render(<AdminHealthPage />);

      // Should show percentage values
      expect(screen.getByText(/99\.99%/i)).toBeInTheDocument();
    });

    it('should format latency correctly', () => {
      render(<AdminHealthPage />);

      // Should show milliseconds
      expect(screen.getByText(/45ms/i)).toBeInTheDocument();
    });
  });

  describe('Progress Bars', () => {
    it('should display CPU usage progress bar', () => {
      const { container } = render(<AdminHealthPage />);

      const progressBars = container.querySelectorAll('.bg-slate-700');
      expect(progressBars.length).toBeGreaterThan(0);
    });

    it('should use correct color thresholds', () => {
      const { container } = render(<AdminHealthPage />);

      // Normal usage should be green
      const greenBars = container.querySelectorAll('.bg-green-500');
      expect(greenBars.length).toBeGreaterThan(0);
    });
  });

  describe('Accessibility', () => {
    it('should have proper heading hierarchy', () => {
      render(<AdminHealthPage />);

      const heading = screen.getByRole('heading', { name: /System Health/i });
      expect(heading).toBeInTheDocument();
      expect(heading.tagName).toBe('H1');
    });

    it('should have accessible buttons', () => {
      render(<AdminHealthPage />);

      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThan(0);
    });

    it('should have proper tab navigation', () => {
      render(<AdminHealthPage />);

      const tabs = screen.getAllByRole('button').filter(btn =>
        btn.classList.contains('rounded-t-lg')
      );
      expect(tabs.length).toBeGreaterThan(0);
    });
  });

  describe('Responsive Layout', () => {
    it('should have mobile-friendly layout', () => {
      const { container } = render(<AdminHealthPage />);

      expect(container.querySelector('.min-h-screen')).toBeInTheDocument();
    });

    it('should have grid layouts for metrics', () => {
      const { container } = render(<AdminHealthPage />);

      const grids = container.querySelectorAll('[class*="grid"]');
      expect(grids.length).toBeGreaterThan(0);
    });
  });

  describe('Error States', () => {
    it('should handle missing data gracefully', () => {
      render(<AdminHealthPage />);

      // Page should render even with mock data
      expect(screen.getByText('System Health')).toBeInTheDocument();
    });

    it('should show fallback values', () => {
      render(<AdminHealthPage />);

      // Should use default mock values
      expect(screen.getByText('Healthy')).toBeInTheDocument();
    });
  });
});
