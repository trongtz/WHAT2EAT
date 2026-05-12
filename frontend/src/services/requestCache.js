import { getStoredToken, isGuestToken } from "../utils/storage";

const responseCache = new Map();
const inflightCache = new Map();

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

export const getCachedResource = async (key, fetcher, options = {}) => {
  const ttlMs = options.ttlMs ?? DEFAULT_TTL_MS;
  const scopedKey = buildScopedKey(key);
  const now = Date.now();
  const cachedEntry = responseCache.get(scopedKey);

  if (cachedEntry && now - cachedEntry.timestamp < ttlMs) {
    return cloneValue(cachedEntry.value);
  }

  const inflightRequest = inflightCache.get(scopedKey);
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

  for (const key of inflightCache.keys()) {
    if (key.startsWith(scopedPrefix)) {
      inflightCache.delete(key);
    }
  }
};

export const clearAllCachedResources = () => {
  responseCache.clear();
  inflightCache.clear();
};
