import { getStoredToken, isGuestToken } from "../utils/storage";

const responseCache = new Map();
const inflightCache = new Map();
const CACHE_STORAGE_KEY = "what2eat:request-cache";

const DEFAULT_TTL_MS = 2 * 60 * 1000;

const cloneValue = (value) => {
  if (value == null) return value;

  if (typeof globalThis.structuredClone === "function") {
    return globalThis.structuredClone(value);
  }

  return JSON.parse(JSON.stringify(value));
};

const getScopeKey = () => {
  const token = getStoredToken();

  if (!token) return "anon";
  return isGuestToken(token) ? `guest:${token}` : `auth:${token}`;
};

const buildScopedKey = (key) => `${getScopeKey()}::${key}`;

const loadPersistedCache = () => {
  if (typeof window === "undefined") return;

  try {
    const rawValue = window.sessionStorage.getItem(CACHE_STORAGE_KEY);
    if (!rawValue) return;

    const parsedValue = JSON.parse(rawValue);
    if (!parsedValue || typeof parsedValue !== "object") return;

    Object.entries(parsedValue).forEach(([key, value]) => {
      if (
        value &&
        typeof value === "object" &&
        typeof value.timestamp === "number" &&
        Object.prototype.hasOwnProperty.call(value, "value")
      ) {
        responseCache.set(key, value);
      }
    });
  } catch {
    window.sessionStorage.removeItem(CACHE_STORAGE_KEY);
  }
};

const persistCache = () => {
  if (typeof window === "undefined") return;

  try {
    window.sessionStorage.setItem(CACHE_STORAGE_KEY, JSON.stringify(Object.fromEntries(responseCache.entries())));
  } catch {
    // Ignore storage quota or serialization issues and keep the in-memory cache.
  }
};

loadPersistedCache();

export const getCachedResource = async (key, fetcher, options = {}) => {
  const ttlMs = options.ttlMs ?? DEFAULT_TTL_MS;
  const scopedKey = buildScopedKey(key);
  const now = Date.now();
  const cachedEntry = responseCache.get(scopedKey);
  const forceRefresh = options.forceRefresh === true;

  if (!forceRefresh && cachedEntry && now - cachedEntry.timestamp < ttlMs) {
    return cloneValue(cachedEntry.value);
  }

  const inflightRequest = forceRefresh ? null : inflightCache.get(scopedKey);
  if (inflightRequest) {
    return cloneValue(await inflightRequest);
  }

  const request = Promise.resolve()
    .then(fetcher)
    .then((value) => {
      responseCache.set(scopedKey, {
        value: cloneValue(value),
        timestamp: Date.now(),
      });
      persistCache();
      inflightCache.delete(scopedKey);
      return value;
    })
    .catch((error) => {
      inflightCache.delete(scopedKey);
      throw error;
    });

  inflightCache.set(scopedKey, request);
  return cloneValue(await request);
};

export const invalidateCachePrefix = (prefix) => {
  const scopedPrefix = buildScopedKey(prefix);

  for (const key of responseCache.keys()) {
    if (key.startsWith(scopedPrefix)) {
      responseCache.delete(key);
    }
  }
  persistCache();

  for (const key of inflightCache.keys()) {
    if (key.startsWith(scopedPrefix)) {
      inflightCache.delete(key);
    }
  }
};

export const clearAllCachedResources = () => {
  responseCache.clear();
  inflightCache.clear();
  if (typeof window !== "undefined") {
    window.sessionStorage.removeItem(CACHE_STORAGE_KEY);
  }
};
