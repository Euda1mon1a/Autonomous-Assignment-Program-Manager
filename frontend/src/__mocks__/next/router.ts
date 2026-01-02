/**
 * Mock for next/router (Pages Router)
 */

import type { NextRouter } from 'next/router';
import type React from 'react';

interface MockRouterEvents {
  on: jest.Mock<void, [string, (...args: unknown[]) => void]>;
  off: jest.Mock<void, [string, (...args: unknown[]) => void]>;
  emit: jest.Mock<void, [string, ...unknown[]]>;
}

interface MockNextRouter {
  route: string;
  pathname: string;
  query: Record<string, string | string[] | undefined>;
  asPath: string;
  push: jest.Mock<Promise<boolean>, [string, string?, { scroll?: boolean; shallow?: boolean }?]>;
  replace: jest.Mock<Promise<boolean>, [string, string?, { scroll?: boolean; shallow?: boolean }?]>;
  reload: jest.Mock<void, []>;
  back: jest.Mock<void, []>;
  forward: jest.Mock<void, []>;
  prefetch: jest.Mock<Promise<void>, [string, string?, { priority?: boolean }?]>;
  beforePopState: jest.Mock<void, [(state: { url: string; as: string; options: object }) => boolean]>;
  events: MockRouterEvents;
  isFallback: boolean;
  isLocaleDomain: boolean;
  isReady: boolean;
  isPreview: boolean;
}

export const useRouter = jest.fn<MockNextRouter, []>(() => ({
  route: '/',
  pathname: '/',
  query: {},
  asPath: '/',
  push: jest.fn<Promise<boolean>, [string, string?, { scroll?: boolean; shallow?: boolean }?]>(),
  replace: jest.fn<Promise<boolean>, [string, string?, { scroll?: boolean; shallow?: boolean }?]>(),
  reload: jest.fn<void, []>(),
  back: jest.fn<void, []>(),
  forward: jest.fn<void, []>(),
  prefetch: jest.fn<Promise<void>, [string, string?, { priority?: boolean }?]>(),
  beforePopState: jest.fn<void, [(state: { url: string; as: string; options: object }) => boolean]>(),
  events: {
    on: jest.fn<void, [string, (...args: unknown[]) => void]>(),
    off: jest.fn<void, [string, (...args: unknown[]) => void]>(),
    emit: jest.fn<void, [string, ...unknown[]]>(),
  },
  isFallback: false,
  isLocaleDomain: false,
  isReady: true,
  isPreview: false,
}));

export const withRouter = <P extends object>(
  Component: React.ComponentType<P & { router: NextRouter }>
): React.ComponentType<Omit<P, 'router'>> => {
  // Return a wrapper component that injects the router
  // For mocking purposes, we just cast the component
  return Component as unknown as React.ComponentType<Omit<P, 'router'>>;
};
