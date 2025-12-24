/**
 * Example Admin Dashboard with Claude Code Chat Integration
 * 
 * This demonstrates how to integrate the ClaudeCodeChat component
 * into your admin panel with real-world scheduling tasks.
 */

import React, { useState } from 'react';
import ClaudeCodeChat from '../frontend/src/components/admin/ClaudeCodeChat';
import { ClaudeChatProvider } from '../frontend/src/contexts/ClaudeChatContext';

interface SchedulingArtifact {
  id: string;
  type: 'schedule' | 'analysis' | 'report' | 'configuration';
  title: string;
  data: Record<string, any>;
  createdAt: Date;
}

interface AdminDashboardState {
  activeTab: 'chat' | 'schedules' | 'compliance' | 'analytics';
  selectedArtifact: SchedulingArtifact | null;
  generatedSchedules: SchedulingArtifact[];
}

const AdminDashboardExample: React.FC = () => {
  const [state, setState] = useState<AdminDashboardState>({
    activeTab: 'chat',
    selectedArtifact: null,
    generatedSchedules: [],
  });

  // Mock user context
  const mockUser = {
    id: 'admin_001',
    name: 'Dr. Sarah Johnson',
    role: 'Program Director',
  };

  const mockProgram = {
    id: 'prog_001',
    name: 'Family Medicine Residency',
    residents: 12,
    academicYear: '2025-2026',
  };

  // Handle completed chat tasks
  const handleTaskComplete = (artifact: SchedulingArtifact) => {
    console.log('Task completed with artifact:', artifact);
    setState((prev) => ({
      ...prev,
      generatedSchedules: [...prev.generatedSchedules, artifact],
      selectedArtifact: artifact,
    }));
  };

  // Apply generated schedule
  const handleApplySchedule = async (artifact: SchedulingArtifact) => {
    try {
      const response = await fetch('/api/schedules', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          programId: mockProgram.id,
          data: artifact.data,
          source: 'claude_chat',
          artifactId: artifact.id,
        }),
      });

      if (response.ok) {
        console.log('Schedule applied successfully');
        // Show success notification
      }
    } catch (error) {
      console.error('Error applying schedule:', error);
    }
  };

  // Export artifact to file
  const handleExportArtifact = (artifact: SchedulingArtifact) => {
    const dataStr = JSON.stringify(artifact.data, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${artifact.title.replace(/\s+/g, '_')}.json`;
    link.click();
  };

  return (
    <ClaudeChatProvider>
      <div className="admin-dashboard">
        {/* Header */}
        <header className="dashboard-header">
          <div className="header-content">
            <h1>{mockProgram.name}</h1>
            <div className="user-info">
              <span>{mockUser.name}</span>
              <span className="role">{mockUser.role}</span>
            </div>
          </div>
          <div className="header-stats">
            <div className="stat">
              <span className="label">Residents</span>
              <span className="value">{mockProgram.residents}</span>
            </div>
            <div className="stat">
              <span className="label">Academic Year</span>
              <span className="value">{mockProgram.academicYear}</span>
            </div>
            <div className="stat">
              <span className="label">Schedules Generated</span>
              <span className="value">{state.generatedSchedules.length}</span>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="dashboard-main">
          {/* Sidebar Navigation */}
          <aside className="sidebar">
            <nav className="nav">
              <button
                className={`nav-item ${state.activeTab === 'chat' ? 'active' : ''}`}
                onClick={() => setState((prev) => ({ ...prev, activeTab: 'chat' }))}
              >
                💬 Claude Assistant
              </button>
              <button
                className={`nav-item ${state.activeTab === 'schedules' ? 'active' : ''}`}
                onClick={() => setState((prev) => ({ ...prev, activeTab: 'schedules' }))}
              >
                📅 Generated Schedules
              </button>
              <button
                className={`nav-item ${state.activeTab === 'compliance' ? 'active' : ''}`}
                onClick={() => setState((prev) => ({ ...prev, activeTab: 'compliance' }))}
              >
                ✅ Compliance Reports
              </button>
              <button
                className={`nav-item ${state.activeTab === 'analytics' ? 'active' : ''}`}
                onClick={() => setState((prev) => ({ ...prev, activeTab: 'analytics' }))}
              >
                📊 Analytics
              </button>
            </nav>
          </aside>

          {/* Content Area */}
          <section className="content-area">
            {state.activeTab === 'chat' && (
              <div className="tab-content">
                <h2>Claude Code Assistant</h2>
                <p className="description">
                  Use natural language to generate schedules, analyze compliance,
                  and optimize fairness across your residency program.
                </p>
                <div className="chat-container">
                  <ClaudeCodeChat
                    programId={mockProgram.id}
                    adminId={mockUser.id}
                    onTaskComplete={handleTaskComplete}
                  />
                </div>
              </div>
            )}

            {state.activeTab === 'schedules' && (
              <div className="tab-content">
                <h2>Generated Schedules</h2>
                {state.generatedSchedules.length === 0 ? (
                  <div className="empty-state">
                    <p>No schedules generated yet.</p>
                    <p className="hint">
                      Use the Claude Assistant to generate your first schedule.
                    </p>
                  </div>
                ) : (
                  <div className="schedules-grid">
                    {state.generatedSchedules.map((schedule) => (
                      <div key={schedule.id} className="schedule-card">
                        <div className="card-header">
                          <h3>{schedule.title}</h3>
                          <span className="type-badge">{schedule.type}</span>
                        </div>
                        <div className="card-meta">
                          <span className="date">
                            Created: {schedule.createdAt.toLocaleDateString()}
                          </span>
                        </div>
                        <div className="card-actions">
                          <button
                            className="action-btn primary"
                            onClick={() => handleApplySchedule(schedule)}
                          >
                            Apply to System
                          </button>
                          <button
                            className="action-btn secondary"
                            onClick={() => handleExportArtifact(schedule)}
                          >
                            Export
                          </button>
                          <button
                            className="action-btn secondary"
                            onClick={() =>
                              setState((prev) => ({
                                ...prev,
                                selectedArtifact: schedule,
                              }))
                            }
                          >
                            View Details
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {state.activeTab === 'compliance' && (
              <div className="tab-content">
                <h2>Compliance Reports</h2>
                <div className="empty-state">
                  <p>Generate compliance reports using the Claude Assistant.</p>
                  <p className="hint">
                    Ask about ACGME violations, duty hour compliance, or run a
                    compliance audit.
                  </p>
                </div>
              </div>
            )}

            {state.activeTab === 'analytics' && (
              <div className="tab-content">
                <h2>Schedule Analytics</h2>
                <div className="empty-state">
                  <p>Analytics will appear here once schedules are generated.</p>
                  <p className="hint">
                    View rotation distribution, call frequency, fairness metrics,
                    and more.
                  </p>
                </div>
              </div>
            )}
          </section>

          {/* Detail Panel */}
          {state.selectedArtifact && (
            <aside className="detail-panel">
              <button
                className="close-btn"
                onClick={() => setState((prev) => ({ ...prev, selectedArtifact: null }))}
              >
                ×
              </button>
              <h3>{state.selectedArtifact.title}</h3>
              <div className="detail-content">
                <pre>{JSON.stringify(state.selectedArtifact.data, null, 2)}</pre>
              </div>
              <div className="detail-actions">
                <button
                  className="action-btn primary"
                  onClick={() => handleApplySchedule(state.selectedArtifact!)}
                >
                  Apply
                </button>
                <button
                  className="action-btn secondary"
                  onClick={() => handleExportArtifact(state.selectedArtifact!)}
                >
                  Export
                </button>
              </div>
            </aside>
          )}
        </main>
      </div>

      <style jsx>{`
        .admin-dashboard {
          display: flex;
          flex-direction: column;
          height: 100vh;
          background: var(--color-background);
        }

        .dashboard-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 20px 32px;
          border-bottom: 1px solid var(--color-border);
          background: var(--color-surface);
        }

        .header-content h1 {
          margin: 0;
          font-size: 24px;
          color: var(--color-text);
        }

        .user-info {
          display: flex;
          gap: 8px;
          font-size: 14px;
          color: var(--color-text-secondary);
          margin-top: 4px;
        }

        .role {
          font-weight: 500;
        }

        .header-stats {
          display: flex;
          gap: 32px;
        }

        .stat {
          display: flex;
          flex-direction: column;
          align-items: center;
        }

        .stat .label {
          font-size: 12px;
          color: var(--color-text-secondary);
          text-transform: uppercase;
          font-weight: 600;
        }

        .stat .value {
          font-size: 20px;
          font-weight: 700;
          color: var(--color-text);
          margin-top: 4px;
        }

        .dashboard-main {
          display: flex;
          flex: 1;
          overflow: hidden;
        }

        .sidebar {
          width: 200px;
          border-right: 1px solid var(--color-border);
          background: var(--color-surface);
          overflow-y: auto;
        }

        .nav {
          display: flex;
          flex-direction: column;
          padding: 8px;
        }

        .nav-item {
          padding: 12px 16px;
          border: none;
          background: transparent;
          color: var(--color-text);
          text-align: left;
          cursor: pointer;
          border-radius: 6px;
          transition: all 150ms;
          font-size: 14px;
          margin-bottom: 4px;
        }

        .nav-item:hover {
          background: var(--color-secondary);
        }

        .nav-item.active {
          background: var(--color-primary);
          color: var(--color-btn-primary-text);
          font-weight: 600;
        }

        .content-area {
          flex: 1;
          display: flex;
          flex-direction: column;
          overflow-y: auto;
          padding: 32px;
        }

        .tab-content h2 {
          margin: 0 0 8px 0;
          font-size: 20px;
          color: var(--color-text);
        }

        .description {
          color: var(--color-text-secondary);
          margin: 0 0 20px 0;
          font-size: 14px;
        }

        .chat-container {
          height: 600px;
          border: 1px solid var(--color-border);
          border-radius: 8px;
          overflow: hidden;
        }

        .empty-state {
          text-align: center;
          padding: 48px 24px;
          color: var(--color-text-secondary);
        }

        .empty-state p {
          margin: 0 0 8px 0;
          font-size: 14px;
        }

        .hint {
          font-size: 12px;
          color: var(--color-text-secondary);
        }

        .schedules-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
          gap: 16px;
        }

        .schedule-card {
          background: var(--color-surface);
          border: 1px solid var(--color-border);
          border-radius: 8px;
          padding: 16px;
          transition: all 150ms;
        }

        .schedule-card:hover {
          border-color: var(--color-primary);
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }

        .card-header {
          display: flex;
          justify-content: space-between;
          align-items: start;
          margin-bottom: 12px;
        }

        .card-header h3 {
          margin: 0;
          font-size: 16px;
          color: var(--color-text);
        }

        .type-badge {
          background: rgba(59, 130, 246, 0.1);
          color: var(--color-info);
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 11px;
          font-weight: 600;
          text-transform: uppercase;
        }

        .card-meta {
          font-size: 12px;
          color: var(--color-text-secondary);
          margin-bottom: 12px;
        }

        .card-actions {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
        }

        .action-btn {
          padding: 8px 12px;
          border: none;
          border-radius: 4px;
          font-size: 12px;
          font-weight: 600;
          cursor: pointer;
          transition: all 150ms;
        }

        .action-btn.primary {
          background: var(--color-primary);
          color: var(--color-btn-primary-text);
        }

        .action-btn.primary:hover {
          background: var(--color-primary-hover);
        }

        .action-btn.secondary {
          background: var(--color-secondary);
          color: var(--color-text);
        }

        .action-btn.secondary:hover {
          background: var(--color-secondary-hover);
        }

        .detail-panel {
          width: 400px;
          border-left: 1px solid var(--color-border);
          background: var(--color-surface);
          display: flex;
          flex-direction: column;
          overflow-y: auto;
          position: relative;
        }

        .close-btn {
          position: absolute;
          top: 12px;
          right: 12px;
          background: transparent;
          border: none;
          font-size: 24px;
          color: var(--color-text);
          cursor: pointer;
          width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 4px;
          transition: all 150ms;
        }

        .close-btn:hover {
          background: var(--color-secondary);
        }

        .detail-panel h3 {
          margin: 0 0 16px 0;
          padding: 20px 16px 0;
          font-size: 16px;
          color: var(--color-text);
        }

        .detail-content {
          flex: 1;
          overflow-y: auto;
          padding: 0 16px;
        }

        .detail-content pre {
          background: #1e1e1e;
          color: #d4d4d4;
          padding: 12px;
          border-radius: 4px;
          font-size: 11px;
          overflow-x: auto;
          margin: 0;
        }

        .detail-actions {
          display: flex;
          gap: 8px;
          padding: 16px;
          border-top: 1px solid var(--color-border);
        }

        .detail-actions .action-btn {
          flex: 1;
        }
      `}</style>
    </ClaudeChatProvider>
  );
};

export default AdminDashboardExample;
