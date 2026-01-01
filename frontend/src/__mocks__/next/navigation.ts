/**
 * Mock for next/navigation (App Router)
 */

import type { ReadonlyURLSearchParams } from 'next/navigation';

interface MockRouter {
  push: jest.Mock<Promise<boolean>, [string, { scroll?: boolean }?]>;
  replace: jest.Mock<void, [string, { scroll?: boolean }?]>;
  refresh: jest.Mock<void, []>;
  back: jest.Mock<void, []>;
  forward: jest.Mock<void, []>;
  prefetch: jest.Mock<void, [string, { kind?: 'auto' | 'full' | 'temporary' }?]>;
}

interface MockSearchParams {
  get: jest.Mock<string | null, [string]>;
  getAll: jest.Mock<string[], [string]>;
  has: jest.Mock<boolean, [string]>;
  keys: jest.Mock<IterableIterator<string>, []>;
  values: jest.Mock<IterableIterator<string>, []>;
  entries: jest.Mock<IterableIterator<[string, string]>, []>;
  forEach: jest.Mock<void, [(value: string, key: string, parent: ReadonlyURLSearchParams) => void]>;
  toString: jest.Mock<string, []>;
}

export const useRouter = jest.fn<MockRouter, []>(() => ({
  push: jest.fn<Promise<boolean>, [string, { scroll?: boolean }?]>(),
  replace: jest.fn<void, [string, { scroll?: boolean }?]>(),
  refresh: jest.fn<void, []>(),
  back: jest.fn<void, []>(),
  forward: jest.fn<void, []>(),
  prefetch: jest.fn<void, [string, { kind?: 'auto' | 'full' | 'temporary' }?]>(),
}));

export const usePathname = jest.fn<string, []>(() => '/');

export const useSearchParams = jest.fn<MockSearchParams, []>(() => ({
  get: jest.fn<string | null, [string]>(),
  getAll: jest.fn<string[], [string]>(),
  has: jest.fn<boolean, [string]>(),
  keys: jest.fn<IterableIterator<string>, []>(),
  values: jest.fn<IterableIterator<string>, []>(),
  entries: jest.fn<IterableIterator<[string, string]>, []>(),
  forEach: jest.fn<void, [(value: string, key: string, parent: ReadonlyURLSearchParams) => void]>(),
  toString: jest.fn<string, []>(() => ''),
}));

export const useParams = jest.fn<Record<string, string | string[]>, []>(() => ({}));

export const redirect = jest.fn<never, [string, 'replace' | 'push'?]>();

export const notFound = jest.fn<never, []>();
