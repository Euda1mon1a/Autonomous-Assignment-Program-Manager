import { Page, Route } from '@playwright/test';

/**
 * API Mocking Utilities
 *
 * Helper functions for mocking API responses in E2E tests
 */

export type MockResponse = {
  status?: number;
  body: any;
  headers?: Record<string, string>;
  delay?: number;
};

/**
 * Mock a specific API endpoint
 */
export async function mockAPI(
  page: Page,
  urlPattern: string | RegExp,
  response: MockResponse,
  method: string = 'GET'
): Promise<void> {
  await page.route(urlPattern, async (route: Route) => {
    if (route.request().method() === method) {
      if (response.delay) {
        await new Promise((resolve) => setTimeout(resolve, response.delay));
      }

      await route.fulfill({
        status: response.status || 200,
        body: JSON.stringify(response.body),
        headers: {
          'Content-Type': 'application/json',
          ...response.headers,
        },
      });
    } else {
      await route.continue();
    }
  });
}

/**
 * Mock schedule API responses
 */
export class ScheduleMocks {
  constructor(private page: Page) {}

  /**
   * Mock get schedule endpoint
   */
  async mockGetSchedule(scheduleData: any): Promise<void> {
    await mockAPI(this.page, '**/api/v1/schedule*', {
      body: scheduleData,
    });
  }

  /**
   * Mock create assignment endpoint
   */
  async mockCreateAssignment(assignment: any): Promise<void> {
    await mockAPI(this.page, '**/api/v1/assignments', {
      status: 201,
      body: assignment,
    }, 'POST');
  }

  /**
   * Mock update assignment endpoint
   */
  async mockUpdateAssignment(assignmentId: string, updatedData: any): Promise<void> {
    await mockAPI(this.page, `**/api/v1/assignments/${assignmentId}`, {
      body: updatedData,
    }, 'PUT');
  }

  /**
   * Mock delete assignment endpoint
   */
  async mockDeleteAssignment(assignmentId: string): Promise<void> {
    await mockAPI(this.page, `**/api/v1/assignments/${assignmentId}`, {
      status: 204,
      body: null,
    }, 'DELETE');
  }

  /**
   * Mock conflict detection endpoint
   */
  async mockConflictDetection(conflicts: any[]): Promise<void> {
    await mockAPI(this.page, '**/api/v1/schedule/conflicts*', {
      body: { conflicts },
    });
  }

  /**
   * Mock ACGME validation endpoint
   */
  async mockACGMEValidation(violations: any[]): Promise<void> {
    await mockAPI(this.page, '**/api/v1/schedule/validate/acgme*', {
      body: {
        is_compliant: violations.length === 0,
        violations,
      },
    });
  }
}

/**
 * Mock swap API responses
 */
export class SwapMocks {
  constructor(private page: Page) {}

  /**
   * Mock get swaps endpoint
   */
  async mockGetSwaps(swaps: any[]): Promise<void> {
    await mockAPI(this.page, '**/api/v1/swaps*', {
      body: { swaps, total: swaps.length },
    });
  }

  /**
   * Mock create swap endpoint
   */
  async mockCreateSwap(swap: any): Promise<void> {
    await mockAPI(this.page, '**/api/v1/swaps', {
      status: 201,
      body: swap,
    }, 'POST');
  }

  /**
   * Mock approve swap endpoint
   */
  async mockApproveSwap(swapId: string): Promise<void> {
    await mockAPI(this.page, `**/api/v1/swaps/${swapId}/approve`, {
      body: { id: swapId, status: 'APPROVED' },
    }, 'POST');
  }

  /**
   * Mock reject swap endpoint
   */
  async mockRejectSwap(swapId: string, reason: string): Promise<void> {
    await mockAPI(this.page, `**/api/v1/swaps/${swapId}/reject`, {
      body: { id: swapId, status: 'REJECTED', reason },
    }, 'POST');
  }

  /**
   * Mock auto-match endpoint
   */
  async mockAutoMatch(swapId: string, matches: any[]): Promise<void> {
    await mockAPI(this.page, `**/api/v1/swaps/${swapId}/auto-match`, {
      body: { matches },
    });
  }

  /**
   * Mock rollback swap endpoint
   */
  async mockRollbackSwap(swapId: string): Promise<void> {
    await mockAPI(this.page, `**/api/v1/swaps/${swapId}/rollback`, {
      body: { id: swapId, status: 'ROLLED_BACK' },
    }, 'POST');
  }
}

/**
 * Mock authentication API responses
 */
export class AuthMocks {
  constructor(private page: Page) {}

  /**
   * Mock login endpoint
   */
  async mockLogin(user: any, token: string): Promise<void> {
    await mockAPI(this.page, '**/api/v1/auth/login', {
      body: {
        access_token: token,
        token_type: 'bearer',
        user,
      },
    }, 'POST');
  }

  /**
   * Mock logout endpoint
   */
  async mockLogout(): Promise<void> {
    await mockAPI(this.page, '**/api/v1/auth/logout', {
      status: 204,
      body: null,
    }, 'POST');
  }

  /**
   * Mock get current user endpoint
   */
  async mockGetCurrentUser(user: any): Promise<void> {
    await mockAPI(this.page, '**/api/v1/auth/me', {
      body: user,
    });
  }

  /**
   * Mock password reset endpoint
   */
  async mockPasswordReset(email: string): Promise<void> {
    await mockAPI(this.page, '**/api/v1/auth/password-reset', {
      body: { message: 'Password reset email sent' },
    }, 'POST');
  }

  /**
   * Mock token refresh endpoint
   */
  async mockRefreshToken(newToken: string): Promise<void> {
    await mockAPI(this.page, '**/api/v1/auth/refresh', {
      body: {
        access_token: newToken,
        token_type: 'bearer',
      },
    }, 'POST');
  }
}

/**
 * Mock resilience API responses
 */
export class ResilienceMocks {
  constructor(private page: Page) {}

  /**
   * Mock resilience dashboard endpoint
   */
  async mockDashboard(dashboardData: any): Promise<void> {
    await mockAPI(this.page, '**/api/v1/resilience/dashboard*', {
      body: dashboardData,
    });
  }

  /**
   * Mock defense level endpoint
   */
  async mockDefenseLevel(level: string, metrics: any): Promise<void> {
    await mockAPI(this.page, '**/api/v1/resilience/defense-level*', {
      body: {
        current_level: level,
        metrics,
      },
    });
  }

  /**
   * Mock utilization endpoint
   */
  async mockUtilization(utilizationData: any): Promise<void> {
    await mockAPI(this.page, '**/api/v1/resilience/utilization*', {
      body: utilizationData,
    });
  }

  /**
   * Mock N-1 contingency endpoint
   */
  async mockN1Contingency(contingencyData: any): Promise<void> {
    await mockAPI(this.page, '**/api/v1/resilience/n-1-contingency*', {
      body: contingencyData,
    });
  }

  /**
   * Mock alerts endpoint
   */
  async mockAlerts(alerts: any[]): Promise<void> {
    await mockAPI(this.page, '**/api/v1/resilience/alerts*', {
      body: { alerts, total: alerts.length },
    });
  }
}

/**
 * Mock error responses
 */
export class ErrorMocks {
  constructor(private page: Page) {}

  /**
   * Mock 401 Unauthorized
   */
  async mock401(urlPattern: string | RegExp): Promise<void> {
    await mockAPI(this.page, urlPattern, {
      status: 401,
      body: { detail: 'Not authenticated' },
    });
  }

  /**
   * Mock 403 Forbidden
   */
  async mock403(urlPattern: string | RegExp): Promise<void> {
    await mockAPI(this.page, urlPattern, {
      status: 403,
      body: { detail: 'Not authorized' },
    });
  }

  /**
   * Mock 404 Not Found
   */
  async mock404(urlPattern: string | RegExp): Promise<void> {
    await mockAPI(this.page, urlPattern, {
      status: 404,
      body: { detail: 'Not found' },
    });
  }

  /**
   * Mock 500 Internal Server Error
   */
  async mock500(urlPattern: string | RegExp): Promise<void> {
    await mockAPI(this.page, urlPattern, {
      status: 500,
      body: { detail: 'Internal server error' },
    });
  }

  /**
   * Mock network timeout
   */
  async mockTimeout(urlPattern: string | RegExp, delay: number = 30000): Promise<void> {
    await this.page.route(urlPattern, async (route: Route) => {
      await new Promise((resolve) => setTimeout(resolve, delay));
      await route.abort('timedout');
    });
  }

  /**
   * Mock network failure
   */
  async mockNetworkFailure(urlPattern: string | RegExp): Promise<void> {
    await this.page.route(urlPattern, async (route: Route) => {
      await route.abort('failed');
    });
  }
}

/**
 * Create all mock helpers
 */
export function createMocks(page: Page) {
  return {
    schedule: new ScheduleMocks(page),
    swap: new SwapMocks(page),
    auth: new AuthMocks(page),
    resilience: new ResilienceMocks(page),
    errors: new ErrorMocks(page),
  };
}

/**
 * Clear all API mocks
 */
export async function clearMocks(page: Page): Promise<void> {
  await page.unroute('**/*');
}

/**
 * Intercept and log all API calls (for debugging)
 */
export async function interceptAllAPICalls(page: Page): Promise<void> {
  await page.route('**/api/**', async (route: Route) => {
    console.log(`API Call: ${route.request().method()} ${route.request().url()}`);
    await route.continue();
  });
}
