# Roadmap

> **Last Updated:** 2025-12-18

This document outlines the planned features and improvements for the Residency Scheduler project, including detailed implementation notes, technical requirements, database schema changes, API modifications, and migration considerations for each milestone.

---

## Current Release: v1.0.0 (Production Ready)

The current release includes:
- ✅ Complete scheduling engine with ACGME compliance
- ✅ Role-based access control (8 roles)
- ✅ Absence management with military-specific tracking
- ✅ Procedure credentialing and certification tracking
- ✅ 3-tier resilience framework
- ✅ Analytics dashboard with fairness metrics
- ✅ Swap marketplace with auto-matching
- ✅ Audit logging system
- ✅ Rate limiting and security hardening
- ✅ Export functionality (Excel, PDF, ICS)

---

## Upcoming: v1.1.0 (Q1 2026)

### Email Notifications

**Features:**
- [ ] SMTP integration for automated alerts
- [ ] Certification expiration reminders
- [ ] Schedule change notifications
- [ ] Swap request notifications
- [ ] Configurable notification preferences

**Technical Requirements:**
- Dependencies: `aiosmtplib==3.0.2`, `email-validator==2.3.0` (already installed), `jinja2==3.1.4` for email templates
- Celery tasks for async email delivery with retry logic
- Redis message queue for notification scheduling
- Email template system with HTML/plain text support

**Database Schema Changes:**
```sql
-- Email delivery tracking (new table)
CREATE TABLE email_log (
    id UUID PRIMARY KEY,
    notification_id UUID REFERENCES notifications(id) ON DELETE CASCADE,
    recipient_email VARCHAR(255) NOT NULL,
    subject VARCHAR(500),
    status VARCHAR(20) CHECK (status IN ('queued', 'sent', 'failed', 'bounced')),
    error_message TEXT,
    sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_email_log_status (status),
    INDEX idx_email_log_created (created_at)
);

-- Add email preferences to notification_preferences table
ALTER TABLE notification_preferences ADD COLUMN smtp_enabled BOOLEAN DEFAULT true;
ALTER TABLE notification_preferences ADD COLUMN email_digest_time INTEGER DEFAULT 9; -- Hour of day (0-23)
```

**API Changes:**
- `POST /api/v1/notifications/preferences` - Update notification channel preferences
- `GET /api/v1/notifications/email-preview/{notification_id}` - Preview email content
- `POST /api/v1/admin/notifications/test-email` - Send test email (admin only)
- `GET /api/v1/notifications/email-history` - View email delivery history

**Migration Considerations:**
1. Alembic migration: `alembic revision -m "add_email_notification_support"`
2. Environment variables needed: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`
3. Graceful fallback: If SMTP not configured, notifications remain in-app only
4. Backfill existing users with default email preferences
5. Email template versioning for future updates

**Configuration:**
- New settings in `app/core/config.py` for SMTP configuration
- Feature flag: `ENABLE_EMAIL_NOTIFICATIONS` for gradual rollout
- Rate limiting: Max 100 emails per user per day to prevent spam

---

### Bulk Import/Export Enhancements

**Features:**
- [ ] Batch schedule import from Excel
- [ ] Template-based bulk assignment
- [ ] Export scheduling analytics to PDF
- [ ] Integration with external calendar systems

**Technical Requirements:**
- Dependencies: Already have `openpyxl==3.1.5`, `reportlab==4.4.6`, `pandas==2.3.3`
- Additional: `caldav==1.3.9` for CalDAV integration, `ics==0.7.2` for advanced iCal features
- Background Celery tasks for large import/export operations
- File upload size limit increase (current: 10MB, proposed: 50MB for batch imports)

**Database Schema Changes:**
```sql
-- Import job tracking
CREATE TABLE import_jobs (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    file_name VARCHAR(255),
    file_size INTEGER,
    import_type VARCHAR(50) CHECK (import_type IN ('schedule', 'assignments', 'absences', 'certifications')),
    status VARCHAR(20) CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'partial')),
    total_rows INTEGER,
    processed_rows INTEGER,
    successful_rows INTEGER,
    failed_rows INTEGER,
    error_log JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    INDEX idx_import_jobs_user (user_id),
    INDEX idx_import_jobs_status (status)
);

-- Export templates
CREATE TABLE export_templates (
    id UUID PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    template_type VARCHAR(50) CHECK (template_type IN ('excel', 'pdf', 'ical')),
    configuration JSONB NOT NULL, -- Column mappings, filters, formatting
    is_default BOOLEAN DEFAULT false,
    is_public BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_export_templates_type (template_type)
);
```

**API Changes:**
- `POST /api/v1/import/upload` - Upload file for import with validation
- `POST /api/v1/import/preview` - Preview import data before committing
- `POST /api/v1/import/execute/{job_id}` - Execute validated import
- `GET /api/v1/import/status/{job_id}` - Check import job status with progress
- `GET /api/v1/import/errors/{job_id}` - Download error report
- `POST /api/v1/export/templates` - Create reusable export template
- `GET /api/v1/export/templates` - List available templates
- `POST /api/v1/export/generate` - Generate export with template or custom config
- `POST /api/v1/calendar/subscribe` - Generate CalDAV subscription URL

**Migration Considerations:**
1. Transaction management: All imports must be atomic or support rollback
2. Validation phase: Dry-run mode to detect errors before commit
3. Data mapping: Excel columns → database fields with flexible mapping
4. Backwards compatibility: Support legacy export formats for 2 versions
5. Large dataset handling: Streaming for exports >10,000 rows

**Import File Format:**
- Excel templates provided in `/docs/templates/` directory
- Required columns vs optional columns documented
- Data validation rules embedded in Excel template
- Support for multi-sheet imports (e.g., Schedule + Assignments in one file)

---

### FMIT Integration Improvements

**Features:**
- [ ] Enhanced FMIT week detection
- [ ] Automated conflict resolution for FMIT swaps
- [ ] FMIT-specific reporting

**Technical Requirements:**
- Enhanced OR-Tools constraint programming for FMIT scheduling
- Integration with existing resilience framework
- Real-time conflict detection using graph analysis (NetworkX)

**Database Schema Changes:**
```sql
-- FMIT configuration table
CREATE TABLE fmit_configuration (
    id UUID PRIMARY KEY,
    academic_year INTEGER NOT NULL,
    fmit_week_pattern VARCHAR(100), -- e.g., "1,2,3,7,8,9" for Q1
    min_fmit_staffing INTEGER DEFAULT 2,
    max_consecutive_fmit_weeks INTEGER DEFAULT 3,
    fmit_to_clinical_ratio DECIMAL(3,2) DEFAULT 0.5,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (academic_year)
);

-- FMIT swap tracking
ALTER TABLE swaps ADD COLUMN is_fmit_swap BOOLEAN DEFAULT false;
ALTER TABLE swaps ADD COLUMN fmit_conflict_check_status VARCHAR(20)
    CHECK (fmit_conflict_check_status IN ('pending', 'approved', 'denied', 'requires_manual_review'));
ALTER TABLE swaps ADD COLUMN fmit_conflict_details JSONB;

-- FMIT analytics
CREATE TABLE fmit_analytics (
    id UUID PRIMARY KEY,
    person_id UUID REFERENCES people(id) ON DELETE CASCADE,
    academic_year INTEGER NOT NULL,
    quarter VARCHAR(2) CHECK (quarter IN ('Q1', 'Q2', 'Q3', 'Q4')),
    total_fmit_weeks INTEGER,
    total_clinical_weeks INTEGER,
    fmit_percentage DECIMAL(5,2),
    consecutive_fmit_weeks INTEGER,
    last_updated TIMESTAMP DEFAULT NOW(),
    UNIQUE (person_id, academic_year, quarter)
);
```

**API Changes:**
- `GET /api/v1/fmit/configuration` - Get FMIT configuration for academic year
- `PUT /api/v1/fmit/configuration` - Update FMIT settings (admin only)
- `GET /api/v1/fmit/analytics/{person_id}` - Get FMIT distribution analytics
- `POST /api/v1/swaps/fmit-check` - Pre-validate FMIT swap before submission
- `GET /api/v1/reports/fmit-distribution` - Generate FMIT distribution report
- `POST /api/v1/schedules/optimize-fmit` - Run FMIT-specific optimization

**Migration Considerations:**
1. Historical data analysis: Backfill fmit_analytics for past 2 years
2. Swap validation: Existing swaps need FMIT retroactive validation
3. Configuration seeding: Initialize FMIT patterns from current academic calendar
4. Constraint updates: Modify scheduling engine to enforce FMIT rules
5. Performance: Index optimization for FMIT queries (academic_year, quarter)

**Algorithm Enhancements:**
- Multi-objective optimization: Balance FMIT distribution + workload + preferences
- Conflict resolution: Automated suggestion engine for FMIT swap alternatives
- Fairness metrics: Gini coefficient for FMIT distribution across residents
- Predictive warnings: Alert coordinators of potential FMIT imbalances 4 weeks ahead

---

## Planned: v1.2.0 (Q2 2026)

### Mobile Application

**Features:**
- [ ] React Native mobile app
- [ ] Push notifications
- [ ] Offline schedule viewing
- [ ] Quick swap requests from mobile

**Technical Requirements:**
- Dependencies: `react-native==0.74.x`, `expo==51.x` for managed workflow
- Push notifications: `expo-notifications` + Firebase Cloud Messaging (FCM)
- Offline storage: `@react-native-async-storage/async-storage`, `WatermelonDB` for complex queries
- State management: `@tanstack/react-query` (already used in web app for consistency)
- Authentication: JWT token storage with secure keychain (`react-native-keychain`)
- API compatibility: RESTful API with same endpoints as web app

**Database Schema Changes:**
```sql
-- Device registration for push notifications
CREATE TABLE mobile_devices (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    device_token VARCHAR(500) NOT NULL,
    platform VARCHAR(20) CHECK (platform IN ('ios', 'android')),
    device_model VARCHAR(100),
    os_version VARCHAR(50),
    app_version VARCHAR(20),
    is_active BOOLEAN DEFAULT true,
    last_active TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_mobile_devices_user (user_id),
    INDEX idx_mobile_devices_token (device_token),
    UNIQUE (device_token)
);

-- Push notification delivery tracking
CREATE TABLE push_notifications (
    id UUID PRIMARY KEY,
    notification_id UUID REFERENCES notifications(id) ON DELETE CASCADE,
    device_id UUID REFERENCES mobile_devices(id) ON DELETE CASCADE,
    status VARCHAR(20) CHECK (status IN ('queued', 'sent', 'delivered', 'failed', 'clicked')),
    error_message TEXT,
    sent_at TIMESTAMP,
    delivered_at TIMESTAMP,
    clicked_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_push_notifications_status (status),
    INDEX idx_push_notifications_device (device_id)
);
```

**API Changes:**
- `POST /api/v1/mobile/register` - Register device for push notifications
- `DELETE /api/v1/mobile/unregister/{device_id}` - Unregister device
- `GET /api/v1/mobile/schedules/offline` - Get optimized schedule data for offline use
- `GET /api/v1/mobile/sync` - Incremental sync endpoint with delta updates
- `POST /api/v1/mobile/swaps/quick-request` - Streamlined swap request for mobile
- Response headers: Add `X-App-Version-Min` for version compatibility checks

**Migration Considerations:**
1. API versioning: Introduce `/api/v2/` for mobile-optimized endpoints if needed
2. Data pagination: Mobile endpoints return smaller page sizes (20 vs 50 items)
3. Image optimization: Generate thumbnails for profile photos (100x100px)
4. Offline-first architecture: Conflict resolution when online/offline changes clash
5. Beta testing: TestFlight (iOS) and Google Play Beta track for 4-week testing period

**Mobile-Specific Features:**
- Biometric authentication (Face ID, Touch ID, fingerprint)
- Calendar integration: Add schedules to device calendar
- Quick actions: 3D Touch/Long press shortcuts for common tasks
- Widget support: Today view widget showing current/upcoming shifts
- Dark mode: Automatic switching based on system preferences

**Development Considerations:**
- Code sharing: 70% shared business logic between web and mobile via shared API client
- CI/CD: Automated builds via Expo EAS or Fastlane
- App store requirements: privacy policy, data handling statements
- Analytics: Firebase Analytics or Sentry for crash reporting
- Performance: Target 60fps, <3s app launch time, <500ms API response

---

### Advanced Analytics

**Features:**
- [ ] Predictive scheduling recommendations
- [ ] Historical trend analysis
- [ ] Workload forecasting
- [ ] Custom report builder

**Technical Requirements:**
- Dependencies: `scikit-learn==1.5.2`, `prophet==1.1.6` for time series forecasting
- Additional: `statsmodels==0.14.4`, `scipy==1.14.1` for statistical analysis
- ML model storage: pickle or joblib serialization, versioned in S3/MinIO
- Background processing: Celery beat for scheduled model retraining (weekly)
- Caching: Redis for frequently accessed analytics results (24hr TTL)

**Database Schema Changes:**
```sql
-- Historical scheduling metrics
CREATE TABLE scheduling_metrics_history (
    id UUID PRIMARY KEY,
    metric_date DATE NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    person_id UUID REFERENCES people(id) ON DELETE CASCADE,
    block_id UUID REFERENCES blocks(id) ON DELETE SET NULL,
    metric_value DECIMAL(10,2),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_metrics_date (metric_date),
    INDEX idx_metrics_type (metric_type),
    INDEX idx_metrics_person (person_id),
    UNIQUE (metric_date, metric_type, person_id, block_id)
);

-- ML model metadata
CREATE TABLE ml_models (
    id UUID PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    model_type VARCHAR(50) CHECK (model_type IN ('forecasting', 'recommendation', 'anomaly_detection', 'optimization')),
    version VARCHAR(20) NOT NULL,
    file_path VARCHAR(500),
    accuracy_score DECIMAL(5,4),
    training_date TIMESTAMP,
    parameters JSONB,
    is_active BOOLEAN DEFAULT true,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_ml_models_type (model_type),
    INDEX idx_ml_models_active (is_active),
    UNIQUE (model_name, version)
);

-- Custom reports
CREATE TABLE custom_reports (
    id UUID PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    report_type VARCHAR(50) CHECK (report_type IN ('workload', 'fairness', 'compliance', 'custom')),
    query_definition JSONB NOT NULL, -- Filters, grouping, aggregations
    visualization_config JSONB, -- Chart type, colors, layout
    schedule_frequency VARCHAR(20), -- 'daily', 'weekly', 'monthly', 'on_demand'
    recipients JSONB, -- List of user IDs to receive report
    is_public BOOLEAN DEFAULT false,
    last_run TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_custom_reports_creator (created_by),
    INDEX idx_custom_reports_type (report_type)
);

-- Workload predictions
CREATE TABLE workload_predictions (
    id UUID PRIMARY KEY,
    person_id UUID REFERENCES people(id) ON DELETE CASCADE,
    prediction_date DATE NOT NULL,
    predicted_workload_hours DECIMAL(5,2),
    confidence_interval_lower DECIMAL(5,2),
    confidence_interval_upper DECIMAL(5,2),
    model_id UUID REFERENCES ml_models(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_predictions_person (person_id),
    INDEX idx_predictions_date (prediction_date),
    UNIQUE (person_id, prediction_date, model_id)
);
```

**API Changes:**
- `GET /api/v1/analytics/trends` - Historical trend analysis with configurable time windows
- `GET /api/v1/analytics/predictions/{person_id}` - Workload forecasts for next 90 days
- `POST /api/v1/analytics/recommendations` - Get scheduling recommendations based on ML
- `POST /api/v1/reports/custom` - Create custom report definition
- `GET /api/v1/reports/custom/{report_id}/execute` - Run custom report
- `GET /api/v1/analytics/anomalies` - Detect scheduling anomalies
- `POST /api/v1/analytics/what-if` - Scenario analysis (e.g., "What if we add 2 more residents?")

**Migration Considerations:**
1. Historical data: Backfill scheduling_metrics_history for past 3 years (one-time job)
2. Model training: Initial training requires 12+ months of historical data
3. Incremental updates: Daily aggregation jobs to update metrics
4. Performance: Materialized views for common analytics queries
5. Privacy: Anonymization options for analytics exports

**Algorithm Enhancements:**
- Forecasting: Prophet for seasonal workload patterns (holiday effects, academic cycles)
- Clustering: Identify resident workload groups (high/medium/low performers)
- Recommendation engine: Collaborative filtering + constraint satisfaction
- Anomaly detection: Isolation Forest to flag unusual scheduling patterns
- Explainability: SHAP values to explain ML recommendations to users

**Frontend Components:**
- React Plotly.js for interactive charts (already installed)
- Recharts for lightweight visualizations (already installed)
- Report builder: Drag-and-drop interface using dnd-kit (already installed)
- Export options: PNG, PDF, CSV for all visualizations
- Real-time updates: WebSocket for live analytics dashboard

---

## Future Considerations (v2.0+)

### Enterprise Features

**Features:**
- [ ] LDAP/Active Directory integration
- [ ] SAML/SSO authentication
- [ ] Multi-program support
- [ ] Cross-institutional scheduling
- [ ] Custom workflow automation

**Technical Requirements:**
- Dependencies: `python-ldap==3.4.4`, `ldap3==2.9.1` for LDAP/AD integration
- SSO: `python3-saml==1.16.0`, `djangosaml2==1.9.3` (or FastAPI equivalent)
- Multi-tenancy: Schema-per-tenant or shared schema with tenant_id column strategy
- Workflow engine: `temporal-sdk==1.6.0` or `prefect==2.19.x` for complex workflows
- API gateway: Kong or AWS API Gateway for rate limiting/routing across institutions

**Database Schema Changes:**
```sql
-- Multi-tenancy support
CREATE TABLE organizations (
    id UUID PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    parent_organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
    organization_type VARCHAR(50) CHECK (organization_type IN ('institution', 'program', 'department')),
    settings JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_organizations_slug (slug),
    INDEX idx_organizations_parent (parent_organization_id)
);

-- Add organization context to existing tables
ALTER TABLE users ADD COLUMN organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE;
ALTER TABLE people ADD COLUMN organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE;
ALTER TABLE schedules ADD COLUMN organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE;
CREATE INDEX idx_users_org ON users(organization_id);
CREATE INDEX idx_people_org ON people(organization_id);
CREATE INDEX idx_schedules_org ON schedules(organization_id);

-- SSO configuration
CREATE TABLE sso_providers (
    id UUID PRIMARY KEY,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    provider_type VARCHAR(50) CHECK (provider_type IN ('saml', 'oauth2', 'ldap', 'ad')),
    provider_name VARCHAR(100) NOT NULL,
    configuration JSONB NOT NULL, -- IdP metadata, entity ID, SSO URL, etc.
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_sso_providers_org (organization_id),
    UNIQUE (organization_id, provider_name)
);

-- Cross-institutional sharing
CREATE TABLE scheduling_agreements (
    id UUID PRIMARY KEY,
    source_organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    target_organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    agreement_type VARCHAR(50) CHECK (agreement_type IN ('resident_exchange', 'coverage_sharing', 'resource_sharing')),
    start_date DATE NOT NULL,
    end_date DATE,
    terms JSONB,
    status VARCHAR(20) CHECK (status IN ('pending', 'active', 'suspended', 'terminated')),
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_agreements_source (source_organization_id),
    INDEX idx_agreements_target (target_organization_id),
    CHECK (source_organization_id != target_organization_id)
);

-- Workflow automation
CREATE TABLE workflow_definitions (
    id UUID PRIMARY KEY,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    trigger_type VARCHAR(50) CHECK (trigger_type IN ('schedule', 'event', 'manual', 'webhook')),
    trigger_config JSONB NOT NULL,
    actions JSONB NOT NULL, -- Array of action definitions
    is_active BOOLEAN DEFAULT true,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_workflows_org (organization_id),
    INDEX idx_workflows_trigger (trigger_type)
);

CREATE TABLE workflow_executions (
    id UUID PRIMARY KEY,
    workflow_id UUID REFERENCES workflow_definitions(id) ON DELETE CASCADE,
    status VARCHAR(20) CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    trigger_data JSONB,
    execution_log JSONB,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_workflow_exec_workflow (workflow_id),
    INDEX idx_workflow_exec_status (status)
);
```

**API Changes:**
- `POST /api/v2/auth/sso/initiate` - Initiate SSO login flow
- `POST /api/v2/auth/sso/callback` - Handle SSO callback (SAML assertion, OAuth code)
- `GET /api/v2/auth/sso/metadata` - Export SAML SP metadata
- `GET /api/v2/organizations` - List accessible organizations for user
- `POST /api/v2/organizations/{org_id}/switch` - Switch active organization context
- `GET /api/v2/workflows` - List workflow definitions
- `POST /api/v2/workflows` - Create workflow automation
- `POST /api/v2/workflows/{workflow_id}/execute` - Manually trigger workflow
- `GET /api/v2/scheduling-agreements` - Cross-institutional agreements
- Header: `X-Organization-ID` required for all API requests in multi-tenant mode

**Migration Considerations:**
1. Data migration: Backfill organization_id for existing data (default organization)
2. Row-level security: PostgreSQL RLS policies to enforce tenant isolation
3. Schema strategy decision: Shared schema with tenant_id vs separate databases
4. LDAP sync: Initial bulk import + incremental sync (hourly/daily)
5. Zero-downtime migration: Blue-green deployment for schema changes
6. SSO metadata: Coordinate with institutional IT for IdP setup

**Security Enhancements:**
- Multi-factor authentication (MFA) with TOTP or SMS
- IP whitelisting per organization
- Audit logging for cross-organizational data access
- Data encryption at rest for sensitive fields (SSN, DOB if stored)
- RBAC expansion: Organization-level and program-level permissions

---

### AI/ML Enhancements

**Features:**
- [ ] AI-powered schedule optimization
- [ ] Anomaly detection in scheduling patterns
- [ ] Natural language schedule queries
- [ ] Automated compliance recommendations

**Technical Requirements:**
- Dependencies: `openai==1.54.x` or `anthropic==0.39.x` for LLM integration
- Vector database: `pgvector==0.3.x` (PostgreSQL extension) for semantic search
- NLP: `transformers==4.46.x`, `sentence-transformers==3.3.x` for embeddings
- Reinforcement learning: `stable-baselines3==2.4.x` for schedule optimization
- Explainable AI: `shap==0.46.x`, `lime==0.2.x` for model interpretability

**Database Schema Changes:**
```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Schedule embeddings for semantic search
CREATE TABLE schedule_embeddings (
    id UUID PRIMARY KEY,
    schedule_id UUID REFERENCES schedules(id) ON DELETE CASCADE,
    embedding vector(1536), -- OpenAI ada-002 dimension
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_schedule_embeddings_schedule (schedule_id)
);

-- Create vector similarity index (HNSW for fast approximate search)
CREATE INDEX ON schedule_embeddings USING hnsw (embedding vector_cosine_ops);

-- AI conversation history
CREATE TABLE ai_conversations (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    conversation_type VARCHAR(50) CHECK (conversation_type IN ('query', 'optimization', 'compliance_check')),
    messages JSONB NOT NULL, -- Array of {role, content, timestamp}
    context JSONB, -- Relevant schedule/person IDs for query context
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_ai_conversations_user (user_id)
);

-- Compliance recommendations
CREATE TABLE compliance_recommendations (
    id UUID PRIMARY KEY,
    schedule_id UUID REFERENCES schedules(id) ON DELETE CASCADE,
    recommendation_type VARCHAR(50),
    severity VARCHAR(20) CHECK (severity IN ('critical', 'warning', 'suggestion')),
    description TEXT NOT NULL,
    suggested_fix JSONB,
    ai_confidence DECIMAL(4,3), -- 0.000 to 1.000
    status VARCHAR(20) CHECK (status IN ('pending', 'accepted', 'rejected', 'auto_applied')),
    created_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP,
    INDEX idx_compliance_schedule (schedule_id),
    INDEX idx_compliance_status (status)
);

-- Schedule optimization runs
CREATE TABLE optimization_runs (
    id UUID PRIMARY KEY,
    schedule_id UUID REFERENCES schedules(id) ON DELETE CASCADE,
    optimization_type VARCHAR(50) CHECK (optimization_type IN ('ai_powered', 'traditional', 'hybrid')),
    input_constraints JSONB,
    output_schedule JSONB,
    improvement_metrics JSONB, -- Fairness score, ACGME compliance, resident satisfaction
    model_version VARCHAR(50),
    execution_time_ms INTEGER,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_optimization_schedule (schedule_id),
    INDEX idx_optimization_type (optimization_type)
);
```

**API Changes:**
- `POST /api/v2/ai/query` - Natural language schedule query (e.g., "Who's on call next Tuesday?")
- `POST /api/v2/ai/optimize` - AI-powered schedule optimization with preferences
- `GET /api/v2/ai/recommendations/{schedule_id}` - Get compliance recommendations
- `POST /api/v2/ai/recommendations/{rec_id}/apply` - Apply AI suggestion
- `POST /api/v2/ai/explain` - Explain why a schedule was generated this way
- `GET /api/v2/ai/conversations` - Retrieve past AI interactions
- `POST /api/v2/ai/anomalies/detect` - Run anomaly detection on schedule patterns
- `GET /api/v2/ai/insights` - Get AI-generated insights about scheduling patterns

**Migration Considerations:**
1. pgvector installation: Requires PostgreSQL 11+ with pgvector extension
2. Embedding generation: Batch process existing schedules (Celery task, ~5000 schedules/hr)
3. API key management: Secure storage for OpenAI/Anthropic keys in environment
4. Cost management: Token usage tracking and budget alerts
5. Fallback strategy: If AI service unavailable, fallback to traditional algorithms
6. Model versioning: Track which AI model version generated each recommendation

**Algorithm Enhancements:**
- Deep reinforcement learning: Train agent to optimize schedules (PPO/A2C algorithms)
- Multi-agent systems: Simulate resident preferences and negotiate optimal schedules
- Natural language understanding: Fine-tuned BERT/GPT for domain-specific queries
- Anomaly detection: Autoencoder neural networks to detect unusual patterns
- Compliance checking: Rule-based system + LLM for complex ACGME interpretations
- Continuous learning: Incorporate coordinator feedback to improve recommendations

**Privacy & Ethics:**
- Data anonymization: Remove PII before sending to external AI APIs
- Local LLMs option: Support for self-hosted models (Llama, Mistral) for sensitive data
- Transparency: Always show AI confidence scores and explain recommendations
- Human-in-the-loop: Require coordinator approval for automated schedule changes
- Bias detection: Monitor for unfair treatment across demographic groups

---

### Integration Ecosystem

**Features:**
- [ ] MyEvaluations integration
- [ ] EMR system connectivity
- [ ] Time tracking system sync
- [ ] External API for third-party apps

**Technical Requirements:**
- Dependencies: `pydantic==2.12.5` (already installed) for schema validation
- API standards: OpenAPI 3.1, JSON:API or GraphQL for external API
- Authentication: OAuth 2.0 + JWT for third-party apps, API keys for server-to-server
- Webhooks: Event-driven integration with external systems
- Rate limiting: Tiered rate limits (1000/hr free, 10000/hr paid, unlimited enterprise)

**Database Schema Changes:**
```sql
-- OAuth2 clients for third-party apps
CREATE TABLE oauth2_clients (
    id UUID PRIMARY KEY,
    client_id VARCHAR(100) UNIQUE NOT NULL,
    client_secret_hash VARCHAR(255) NOT NULL,
    client_name VARCHAR(200) NOT NULL,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    redirect_uris TEXT[] NOT NULL,
    allowed_scopes TEXT[] NOT NULL, -- ['read:schedules', 'write:swaps', etc.]
    is_active BOOLEAN DEFAULT true,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_oauth2_clients_client_id (client_id)
);

-- OAuth2 tokens
CREATE TABLE oauth2_tokens (
    id UUID PRIMARY KEY,
    client_id UUID REFERENCES oauth2_clients(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    access_token_hash VARCHAR(255) UNIQUE NOT NULL,
    refresh_token_hash VARCHAR(255) UNIQUE,
    scopes TEXT[],
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_oauth2_tokens_access (access_token_hash),
    INDEX idx_oauth2_tokens_client (client_id)
);

-- External system integrations
CREATE TABLE external_integrations (
    id UUID PRIMARY KEY,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    integration_type VARCHAR(50) CHECK (integration_type IN ('emr', 'myevaluations', 'time_tracking', 'payroll', 'custom')),
    system_name VARCHAR(100) NOT NULL,
    configuration JSONB NOT NULL, -- API endpoints, credentials, field mappings
    sync_frequency VARCHAR(20), -- 'real_time', 'hourly', 'daily', 'manual'
    last_sync_at TIMESTAMP,
    last_sync_status VARCHAR(20),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_integrations_org (organization_id),
    INDEX idx_integrations_type (integration_type),
    UNIQUE (organization_id, integration_type, system_name)
);

-- Integration sync logs
CREATE TABLE integration_sync_logs (
    id UUID PRIMARY KEY,
    integration_id UUID REFERENCES external_integrations(id) ON DELETE CASCADE,
    sync_direction VARCHAR(20) CHECK (sync_direction IN ('inbound', 'outbound', 'bidirectional')),
    records_processed INTEGER,
    records_succeeded INTEGER,
    records_failed INTEGER,
    error_details JSONB,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_sync_logs_integration (integration_id),
    INDEX idx_sync_logs_started (started_at)
);

-- Webhooks for event notifications
CREATE TABLE webhooks (
    id UUID PRIMARY KEY,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    client_id UUID REFERENCES oauth2_clients(id) ON DELETE CASCADE,
    url VARCHAR(500) NOT NULL,
    event_types TEXT[] NOT NULL, -- ['schedule.created', 'swap.approved', etc.]
    secret_key VARCHAR(255), -- For signature verification
    is_active BOOLEAN DEFAULT true,
    failed_deliveries INTEGER DEFAULT 0,
    last_delivery_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_webhooks_org (organization_id),
    INDEX idx_webhooks_client (client_id)
);

-- API usage tracking
CREATE TABLE api_usage (
    id UUID PRIMARY KEY,
    client_id UUID REFERENCES oauth2_clients(id) ON DELETE CASCADE,
    endpoint VARCHAR(200),
    method VARCHAR(10),
    response_status INTEGER,
    response_time_ms INTEGER,
    request_date DATE NOT NULL,
    request_count INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_api_usage_client (client_id),
    INDEX idx_api_usage_date (request_date),
    UNIQUE (client_id, endpoint, method, request_date)
);
```

**API Changes:**
```
External API (Public):
- POST /api/external/v1/oauth/authorize - OAuth authorization endpoint
- POST /api/external/v1/oauth/token - Token exchange endpoint
- GET /api/external/v1/schedules - List schedules (scoped to organization)
- GET /api/external/v1/people - List people/residents
- POST /api/external/v1/swaps - Create swap request
- GET /api/external/v1/absences - List absences
- POST /api/external/v1/webhooks - Register webhook endpoint
- GET /api/external/v1/docs - OpenAPI documentation

Integration Management (Internal):
- POST /api/v1/integrations - Configure new external integration
- GET /api/v1/integrations - List configured integrations
- POST /api/v1/integrations/{id}/sync - Trigger manual sync
- GET /api/v1/integrations/{id}/logs - View sync history
- PUT /api/v1/integrations/{id}/field-mapping - Update field mappings
```

**Migration Considerations:**
1. API versioning: External API uses `/api/external/v1/` to separate from internal API
2. Backward compatibility: Maintain v1 API for 24 months after v2 release
3. Data mapping: Flexible field mapping for different EMR schemas (Epic, Cerner, etc.)
4. Rate limiting: Implement before public API launch
5. Documentation: Auto-generated OpenAPI docs, code samples in Python/JS/cURL
6. Sandbox environment: Test API instance for third-party developers

**Integration Specifics:**

**MyEvaluations:**
- Sync: Bidirectional (rotation assignments → evaluations, evaluation data ← system)
- Auth: OAuth 2.0 with MyEvaluations credentials
- Frequency: Nightly sync at 2 AM
- Data: Rotation start/end dates, resident-faculty pairings, rotation types

**EMR Systems (Epic, Cerner):**
- Sync: Inbound (pull provider schedules, ensure resident access)
- Auth: HL7 FHIR OAuth 2.0 or SAML
- Frequency: Hourly for on-call schedules
- Data: Provider schedules, patient assignments, clinic locations

**Time Tracking (Kronos, ADP):**
- Sync: Outbound (push worked hours from schedules)
- Auth: API key or OAuth 2.0
- Frequency: Daily after schedule finalization
- Data: Clock in/out times, shift codes, department codes

**Third-Party Apps:**
- Use cases: Mobile apps, scheduling assistants, analytics tools
- Access: OAuth 2.0 with granular scopes
- Rate limits: 1000 requests/hour (free tier), 10000/hour (paid)
- SDKs: Provide official Python and JavaScript SDKs

---

## Technical Debt & Infrastructure

### High Priority

**Tasks:**
- [ ] Refactor oversized route files (resilience.py, constraints.py)
- [ ] Add frontend feature tests (8 features untested)
- [ ] Consolidate documentation (docs/ vs wiki/)
- [x] Fix npm security vulnerabilities - See `scripts/audit-fix.sh`

**Implementation Details:**

**Refactor oversized route files:**
- Target files: `backend/app/api/routes/resilience.py` (~800+ lines), `backend/app/api/routes/constraints.py` (~600+ lines)
- Strategy: Extract business logic into service layer (`app/services/resilience_service.py`, `app/services/constraint_service.py`)
- Pattern: Route handlers should be <50 lines, delegate to service layer
- Testing: Maintain 100% test coverage during refactor
- Timeline: 2-3 sprints, one file at a time
- Breaking changes: None (internal refactor only)

**Add frontend feature tests:**
- Untested features: Swap marketplace auto-matching, FMIT week detection, Procedure credentialing UI, Advanced filters in schedule view, Absence conflict detection, Resilience hub visualization, Export customization, Notification preferences UI
- Framework: Jest + React Testing Library (already configured)
- Coverage target: 80% code coverage for all features
- Test types: Unit tests for hooks/utilities, integration tests for components, E2E tests with Playwright for critical flows
- Location: `frontend/__tests__/features/`
- CI/CD: Block PRs if coverage drops below 75%

**Consolidate documentation:**
- Current state: Documentation scattered across `docs/`, `wiki/`, inline JSDoc, OpenAPI specs
- Target structure:
  ```
  docs/
  ├── README.md (project overview)
  ├── getting-started/
  │   ├── installation.md
  │   ├── configuration.md
  │   └── deployment.md
  ├── architecture/
  │   ├── system-design.md
  │   ├── database-schema.md
  │   └── api-design.md
  ├── guides/
  │   ├── scheduling-workflow.md
  │   ├── swap-management.md
  │   └── resilience-framework.md
  ├── api/
  │   └── openapi.yaml (generated)
  └── development/
      ├── contributing.md
      ├── testing.md
      └── code-style.md
  ```
- Migration: Use `docsify` or `mkdocs` for static site generation
- Automation: Generate API docs from OpenAPI spec on every build
- Wiki deprecation: Migrate wiki content to `docs/` and archive wiki

**Fix npm security vulnerabilities:**
- Current status: ~12 known vulnerabilities (6 moderate, 6 high)
- Affected packages: Check with `npm audit` for specifics
- Strategy:
  1. Update direct dependencies to latest compatible versions
  2. If no fix available, evaluate risk vs. functionality
  3. Use `npm audit fix` for automated fixes
  4. For unfixable vulnerabilities, add to exceptions with justification
- Dependency updates: `next@14.2.35 → 15.x`, `@tanstack/react-query@5.17.0 → 5.60.x`
- Testing: Run full E2E test suite after each dependency update
- Monitoring: Enable Dependabot or Snyk for continuous monitoring

---

### Medium Priority

**Tasks:**
- [ ] Split frontend hooks.ts by domain
- [ ] Improve frontend type documentation
- [x] Standardize error response formats - Documented in `docs/CI_CD_RECOMMENDATIONS.md`
- [x] Add comprehensive API documentation - Added multiple docs in this session

**Implementation Details:**

**Split frontend hooks.ts by domain:**
- Current: `frontend/src/hooks.ts` (~1200 lines, 40+ hooks)
- Target structure:
  ```
  frontend/src/hooks/
  ├── index.ts (re-exports all hooks)
  ├── useAuth.ts (authentication hooks)
  ├── useSchedule.ts (schedule-related hooks)
  ├── useSwaps.ts (swap marketplace hooks)
  ├── usePeople.ts (people/resident hooks)
  ├── useAbsences.ts (absence management hooks)
  ├── useCertifications.ts (procedure credential hooks)
  ├── useNotifications.ts (notification hooks)
  ├── useAnalytics.ts (analytics/reporting hooks)
  └── useResilience.ts (resilience framework hooks)
  ```
- Migration: Gradual refactor, update imports one component at a time
- Testing: Ensure no regression in React Query cache keys
- Benefits: Better code organization, faster IDE intellisense, easier to test

**Improve frontend type documentation:**
- Current: Some JSDoc comments, inconsistent TypeScript types
- Target: Comprehensive JSDoc for all exported functions, hooks, and components
- Standards:
  - All public APIs have JSDoc with `@param`, `@returns`, `@example`
  - Complex types have explanatory comments
  - Use `/** */` style for documentation comments
- Tools: TypeDoc for generating HTML documentation from JSDoc
- CI/CD: Generate TypeDoc on every commit to `main`, publish to GitHub Pages
- Example:
  ```typescript
  /**
   * Custom hook for fetching and managing schedule data
   * @param scheduleId - Unique identifier for the schedule
   * @param options - Optional configuration for query behavior
   * @returns Query result with schedule data, loading state, and error
   * @example
   * const { data, isLoading } = useSchedule('schedule-123')
   */
  ```

**Standardize error response formats:**
- Current: Inconsistent error responses from backend (sometimes string, sometimes object, sometimes array)
- Target format (RFC 7807 Problem Details):
  ```json
  {
    "type": "https://api.example.com/errors/validation-error",
    "title": "Validation Error",
    "status": 400,
    "detail": "The schedule start date must be before the end date",
    "instance": "/api/v1/schedules/create",
    "errors": [
      {
        "field": "start_date",
        "message": "Must be before end_date"
      }
    ],
    "trace_id": "abc123xyz"
  }
  ```
- Backend changes: Create `app/core/exceptions.py` with custom exception classes
- Middleware: FastAPI exception handler to transform all exceptions
- Frontend: Update Axios interceptor to handle standardized errors
- Migration: Version API to avoid breaking existing clients

**Add comprehensive API documentation:**
- Current: Basic OpenAPI spec, minimal endpoint descriptions
- Enhancements:
  - Detailed descriptions for every endpoint
  - Request/response examples for all scenarios (success, validation errors, auth failures)
  - Authentication requirements clearly marked
  - Rate limiting information
  - Deprecation warnings
- Tools: Swagger UI (already available at `/docs`), Redoc (add at `/redoc`)
- Maintenance: Use Pydantic schema docstrings to auto-generate descriptions
- External docs: Publish API reference to dedicated docs site
- Code samples: Provide curl, Python, and JavaScript examples for each endpoint

---

### Low Priority

**Tasks:**
- [ ] Frontend component reorganization
- [ ] Backend service grouping standardization
- [x] Enhanced ESLint configuration - Added `eslint.config.js` for ESLint v9
- [ ] Playwright test expansion

**Implementation Details:**

**Frontend component reorganization:**
- Current: Mix of feature-based and type-based organization
- Proposed structure:
  ```
  frontend/src/components/
  ├── common/ (buttons, modals, forms)
  ├── layout/ (header, sidebar, footer)
  ├── schedules/ (schedule view, calendar, timeline)
  ├── swaps/ (swap marketplace, swap card, auto-matcher)
  ├── people/ (resident list, profile, certifications)
  ├── absences/ (absence form, absence calendar)
  ├── analytics/ (charts, dashboards, reports)
  └── resilience/ (hub visualization, metrics)
  ```
- Co-location: Keep component, styles, tests in same directory
- Naming: Use PascalCase for components, kebab-case for directories
- Index files: Each directory has `index.ts` for easier imports

**Backend service grouping standardization:**
- Current: Some services in `app/services/`, some business logic in routes
- Target: All business logic in service layer
- Structure:
  ```
  backend/app/services/
  ├── auth_service.py
  ├── scheduling_service.py
  ├── swap_service.py
  ├── resilience_service.py
  ├── notification_service.py
  ├── analytics_service.py
  └── integration_service.py
  ```
- Pattern: Services are dependency-injected into routes via FastAPI Depends()
- Testing: Mock services in route tests, unit test services independently
- Benefits: Easier to test, reuse logic across routes, clearer separation of concerns

**Enhanced ESLint configuration:**
- Current: Basic Next.js ESLint config
- Additions:
  - `eslint-plugin-react-hooks` with exhaustive-deps enforcement
  - `eslint-plugin-jsx-a11y` for accessibility checks
  - `eslint-plugin-import` for import ordering
  - Custom rules for project-specific patterns
- Prettier integration: `eslint-config-prettier` to avoid conflicts
- Pre-commit hook: Run ESLint on staged files with `husky` + `lint-staged`
- CI/CD: Fail build on ESLint errors (warnings allowed)

**Playwright test expansion:**
- Current: Basic E2E tests for authentication and schedule creation
- Expansion areas:
  - Swap workflow (request → approval → execution)
  - Bulk operations (import, export)
  - Resilience framework interactions
  - Analytics dashboard interactions
  - Mobile viewport testing
  - Cross-browser testing (Chromium, Firefox, WebKit)
- Page Object Model: Refactor tests to use POM pattern
- Visual regression: Add visual snapshots with `@playwright/test`
- Performance: Add Lighthouse audits via Playwright
- CI/CD: Run on every PR, parallel execution for faster feedback

### Recently Completed
- [x] Pre-deployment validation script (`scripts/pre-deploy-validate.sh`)
- [x] TODO tracking documentation (`docs/TODO_TRACKER.md`)
- [x] Code complexity analysis (`docs/CODE_COMPLEXITY_ANALYSIS.md`)
- [x] Security scanning guide (`docs/SECURITY_SCANNING.md`)
- [x] CI/CD improvement recommendations (`docs/CI_CD_RECOMMENDATIONS.md`)
- [x] Implementation tracker for swap system (`docs/IMPLEMENTATION_TRACKER.md`)
- [x] TypeScript type-check configuration (`frontend/tsconfig.typecheck.json`)

---

## Contributing to the Roadmap

We welcome community input on prioritization and feature requests. Please:

1. Open a GitHub Issue for new feature suggestions
2. Comment on existing issues to show interest
3. Submit PRs for items marked as "Help Wanted"

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

---

## Version History

| Version | Release Date | Highlights |
|---------|--------------|------------|
| v1.0.0 | 2025-01-15 | Initial production release |

---

## Release Philosophy

- **Semantic Versioning**: We follow semver (MAJOR.MINOR.PATCH)
- **Quarterly Releases**: Major features targeted quarterly
- **Continuous Improvements**: Security and bug fixes released as needed
- **Backwards Compatibility**: Breaking changes only in major versions
