/**
 * 클라이언트 설정 저장소 (localStorage)
 * SSR 시에는 사용하지 않음 (typeof window 체크)
 */

const KEY_PREFIX = "streaming-console:";

const keys = {
  apiBaseUrl: `${KEY_PREFIX}apiBaseUrl`,
  apiKey: `${KEY_PREFIX}apiKey`,
  pollIntervalMs: `${KEY_PREFIX}pollIntervalMs`,
} as const;

function safeGetItem(key: string): string | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

function safeSetItem(key: string, value: string): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(key, value);
  } catch {
    // ignore
  }
}

function safeRemoveItem(key: string): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.removeItem(key);
  } catch {
    // ignore
  }
}

export interface StoredSettings {
  apiBaseUrl: string;
  apiKey: string;
  pollIntervalMs: number;
}

export function getSettings(): StoredSettings {
  const apiBaseUrl = safeGetItem(keys.apiBaseUrl) ?? "";
  const apiKey = safeGetItem(keys.apiKey) ?? "";
  const pollIntervalMs = (() => {
    const v = safeGetItem(keys.pollIntervalMs);
    if (v == null || v === "") return 2000;
    const n = Number(v);
    return Number.isFinite(n) && n > 0 ? n : 2000;
  })();
  return { apiBaseUrl, apiKey, pollIntervalMs };
}

export function setApiBaseUrl(value: string): void {
  safeSetItem(keys.apiBaseUrl, value);
}

export function setApiKey(value: string): void {
  safeSetItem(keys.apiKey, value);
}

export function setPollIntervalMs(value: number): void {
  safeSetItem(keys.pollIntervalMs, String(value));
}

export function getApiKey(): string {
  return safeGetItem(keys.apiKey) ?? "";
}

export function getApiBaseUrl(): string {
  return safeGetItem(keys.apiBaseUrl) ?? "";
}

export function getPollIntervalMs(): number {
  const v = safeGetItem(keys.pollIntervalMs);
  if (v == null || v === "") return 2000;
  const n = Number(v);
  return Number.isFinite(n) && n > 0 ? n : 2000;
}

export function clearSettings(): void {
  safeRemoveItem(keys.apiBaseUrl);
  safeRemoveItem(keys.apiKey);
  safeRemoveItem(keys.pollIntervalMs);
}
