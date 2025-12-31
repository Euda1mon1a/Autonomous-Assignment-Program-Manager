/**
 * Custom Metrics for k6
 *
 * Define and track custom metrics beyond built-in HTTP metrics.
 */

import { Counter, Gauge, Rate, Trend } from 'k6/metrics';

/**
 * Business Metrics
 */
export const businessMetrics = {
  // Schedule operations
  schedulesGenerated: new Counter('schedules_generated_total'),
  scheduleGenerationDuration: new Trend('schedule_generation_duration'),
  scheduleValidations: new Counter('schedule_validations_total'),
  scheduleValidationFailures: new Counter('schedule_validation_failures'),

  // Assignment operations
  assignmentsCreated: new Counter('assignments_created_total'),
  assignmentsUpdated: new Counter('assignments_updated_total'),
  assignmentsDeleted: new Counter('assignments_deleted_total'),

  // Swap operations
  swapsRequested: new Counter('swaps_requested_total'),
  swapsExecuted: new Counter('swaps_executed_total'),
  swapsRolledBack: new Counter('swaps_rolled_back_total'),
  swapMatchDuration: new Trend('swap_match_duration'),

  // Compliance operations
  complianceChecks: new Counter('compliance_checks_total'),
  complianceViolations: new Counter('compliance_violations_total'),
  complianceValidationDuration: new Trend('compliance_validation_duration'),

  // Authentication
  loginAttempts: new Counter('login_attempts_total'),
  loginFailures: new Counter('login_failures_total'),
  tokenRefreshes: new Counter('token_refreshes_total')
};

/**
 * Performance Metrics
 */
export const performanceMetrics = {
  // Database
  dbQueryDuration: new Trend('db_query_duration'),
  dbConnectionsActive: new Gauge('db_connections_active'),
  dbTransactionsFailed: new Rate('db_transactions_failed'),

  // Cache
  cacheHitRate: new Rate('cache_hit_rate'),
  cacheMissRate: new Rate('cache_miss_rate'),
  cacheResponseTime: new Trend('cache_response_time'),

  // API
  apiErrorRate: new Rate('api_error_rate'),
  api4xxRate: new Rate('api_4xx_rate'),
  api5xxRate: new Rate('api_5xx_rate'),

  // Queue/Background jobs
  jobsQueued: new Counter('jobs_queued_total'),
  jobsCompleted: new Counter('jobs_completed_total'),
  jobsFailed: new Counter('jobs_failed_total'),
  jobDuration: new Trend('job_duration')
};

/**
 * Reliability Metrics
 */
export const reliabilityMetrics = {
  // Availability
  healthCheckSuccess: new Rate('health_check_success'),
  serviceAvailable: new Gauge('service_available'),

  // Errors
  errorsByType: new Counter('errors_by_type'),
  timeoutErrors: new Counter('timeout_errors'),
  connectionErrors: new Counter('connection_errors'),

  // Retries
  retryAttempts: new Counter('retry_attempts_total'),
  retrySuccesses: new Counter('retry_successes_total')
};

/**
 * Rate Limiting Metrics
 */
export const rateLimitMetrics = {
  rateLimitHits: new Counter('rate_limit_hits_total'),
  rateLimitByEndpoint: new Counter('rate_limit_by_endpoint'),
  rateLimitRecoveryTime: new Trend('rate_limit_recovery_time')
};

/**
 * User Flow Metrics
 */
export const userFlowMetrics = {
  // Complete flows
  userFlowsCompleted: new Counter('user_flows_completed'),
  userFlowsFailed: new Counter('user_flows_failed'),
  userFlowDuration: new Trend('user_flow_duration'),

  // Specific flows
  loginFlowDuration: new Trend('login_flow_duration'),
  scheduleViewFlowDuration: new Trend('schedule_view_flow_duration'),
  swapRequestFlowDuration: new Trend('swap_request_flow_duration')
};

/**
 * Custom metric tracking helper
 */
export class MetricTracker {
  constructor() {
    this.metrics = {
      ...businessMetrics,
      ...performanceMetrics,
      ...reliabilityMetrics,
      ...rateLimitMetrics,
      ...userFlowMetrics
    };
  }

  /**
   * Track schedule generation
   */
  trackScheduleGeneration(duration, success = true) {
    this.metrics.schedulesGenerated.add(1);
    this.metrics.scheduleGenerationDuration.add(duration);

    if (!success) {
      this.metrics.scheduleValidationFailures.add(1);
    }
  }

  /**
   * Track compliance check
   */
  trackComplianceCheck(duration, violations = 0) {
    this.metrics.complianceChecks.add(1);
    this.metrics.complianceValidationDuration.add(duration);

    if (violations > 0) {
      this.metrics.complianceViolations.add(violations);
    }
  }

  /**
   * Track swap operation
   */
  trackSwapOperation(type, duration, success = true) {
    if (type === 'request') {
      this.metrics.swapsRequested.add(1);
    } else if (type === 'execute') {
      this.metrics.swapsExecuted.add(1);
    } else if (type === 'rollback') {
      this.metrics.swapsRolledBack.add(1);
    }

    if (type === 'match') {
      this.metrics.swapMatchDuration.add(duration);
    }
  }

  /**
   * Track authentication
   */
  trackAuth(type, success = true) {
    if (type === 'login') {
      this.metrics.loginAttempts.add(1);
      if (!success) {
        this.metrics.loginFailures.add(1);
      }
    } else if (type === 'refresh') {
      this.metrics.tokenRefreshes.add(1);
    }
  }

  /**
   * Track API response
   */
  trackApiResponse(response) {
    const status = response.status;

    if (status >= 400) {
      this.metrics.apiErrorRate.add(1);

      if (status >= 400 && status < 500) {
        this.metrics.api4xxRate.add(1);
      } else if (status >= 500) {
        this.metrics.api5xxRate.add(1);
      }
    } else {
      this.metrics.apiErrorRate.add(0);
    }

    // Track rate limiting
    if (status === 429) {
      this.metrics.rateLimitHits.add(1);
    }
  }

  /**
   * Track cache operation
   */
  trackCache(hit, responseTime) {
    if (hit) {
      this.metrics.cacheHitRate.add(1);
      this.metrics.cacheMissRate.add(0);
    } else {
      this.metrics.cacheHitRate.add(0);
      this.metrics.cacheMissRate.add(1);
    }

    this.metrics.cacheResponseTime.add(responseTime);
  }

  /**
   * Track user flow
   */
  trackUserFlow(flowName, duration, success = true) {
    if (success) {
      this.metrics.userFlowsCompleted.add(1);
    } else {
      this.metrics.userFlowsFailed.add(1);
    }

    this.metrics.userFlowDuration.add(duration);

    // Track specific flows
    if (flowName === 'login') {
      this.metrics.loginFlowDuration.add(duration);
    } else if (flowName === 'schedule_view') {
      this.metrics.scheduleViewFlowDuration.add(duration);
    } else if (flowName === 'swap_request') {
      this.metrics.swapRequestFlowDuration.add(duration);
    }
  }

  /**
   * Track error
   */
  trackError(errorType) {
    this.metrics.errorsByType.add(1, { error_type: errorType });

    if (errorType === 'timeout') {
      this.metrics.timeoutErrors.add(1);
    } else if (errorType === 'connection') {
      this.metrics.connectionErrors.add(1);
    }
  }

  /**
   * Track retry
   */
  trackRetry(success = false) {
    this.metrics.retryAttempts.add(1);
    if (success) {
      this.metrics.retrySuccesses.add(1);
    }
  }
}

/**
 * Time a function and track metric
 */
export function timeOperation(metricTrend, operation) {
  const start = Date.now();
  try {
    const result = operation();
    const duration = Date.now() - start;
    metricTrend.add(duration);
    return { result, duration, success: true };
  } catch (error) {
    const duration = Date.now() - start;
    metricTrend.add(duration);
    return { error, duration, success: false };
  }
}

/**
 * Track response metrics
 */
export function trackResponse(response, tags = {}) {
  const tracker = new MetricTracker();

  // Track API response
  tracker.trackApiResponse(response);

  // Add custom tags
  if (Object.keys(tags).length > 0) {
    response.tags = { ...response.tags, ...tags };
  }

  return response;
}

/**
 * Create custom metric
 */
export function createMetric(name, type = 'counter') {
  switch (type) {
    case 'counter':
      return new Counter(name);
    case 'gauge':
      return new Gauge(name);
    case 'rate':
      return new Rate(name);
    case 'trend':
      return new Trend(name);
    default:
      throw new Error(`Unknown metric type: ${type}`);
  }
}

/**
 * Export all metrics for use in tests
 */
export const allMetrics = {
  ...businessMetrics,
  ...performanceMetrics,
  ...reliabilityMetrics,
  ...rateLimitMetrics,
  ...userFlowMetrics
};

export default {
  businessMetrics,
  performanceMetrics,
  reliabilityMetrics,
  rateLimitMetrics,
  userFlowMetrics,
  MetricTracker,
  timeOperation,
  trackResponse,
  createMetric,
  allMetrics
};
