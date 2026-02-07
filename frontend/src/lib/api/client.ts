/**
 * 공통 fetch 래퍼: baseUrl, timeout, 에러 처리, JSON 파싱
 * X-Request-ID 있으면 응답에서 활용 가능
 */
const DEFAULT_TIMEOUT_MS = 15_000;

function getBaseUrl(): string {
  if (typeof window !== "undefined") {
    return process.env.NEXT_PUBLIC_API_BASE_URL ?? "";
  }
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "";
}

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public requestId?: string | null
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export interface RequestConfig {
  timeout?: number;
  headers?: Record<string, string>;
  signal?: AbortSignal;
}

export async function apiClient<T>(
  path: string,
  options: RequestInit & RequestConfig = {}
): Promise<T> {
  const { timeout = DEFAULT_TIMEOUT_MS, headers = {}, signal, ...init } = options;
  const baseUrl = getBaseUrl().replace(/\/$/, "");
  const url = path.startsWith("http") ? path : `${baseUrl}${path}`;

  const requestId = typeof crypto !== "undefined" && crypto.randomUUID
    ? crypto.randomUUID()
    : undefined;
  const nextHeaders: Record<string, string> = {
    "Content-Type": "application/json",
    ...headers,
  };
  if (requestId) nextHeaders["X-Request-ID"] = requestId;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);
  const finalSignal = signal ?? controller.signal;

  const start = typeof performance !== "undefined" ? performance.now() : 0;
  try {
    const res = await fetch(url, {
      ...init,
      headers: nextHeaders,
      signal: finalSignal,
    });
    clearTimeout(timeoutId);

    const responseRequestId = res.headers.get("X-Request-ID") ?? requestId;
    const durationMs =
      typeof performance !== "undefined"
        ? Math.round(performance.now() - start)
        : 0;
    if (
      typeof window !== "undefined" &&
      process.env.NODE_ENV === "development" &&
      responseRequestId
    ) {
      console.debug(
        `[API] ${res.status} ${path} request_id=${responseRequestId} duration_ms=${durationMs}`
      );
    }
    const text = await res.text();
    let data: T;
    try {
      data = text ? (JSON.parse(text) as T) : (undefined as T);
    } catch {
      data = text as unknown as T;
    }

    if (!res.ok) {
      const message =
        typeof data === "object" && data !== null && "detail" in data
          ? String((data as { detail?: unknown }).detail)
          : res.statusText || `HTTP ${res.status}`;
      throw new ApiError(message, res.status, responseRequestId);
    }

    return data;
  } catch (e) {
    clearTimeout(timeoutId);
    if (e instanceof ApiError) throw e;
    if (e instanceof Error) {
      if (e.name === "AbortError") {
        throw new ApiError("Request timeout", 408, requestId);
      }
      throw new ApiError(e.message, 0, requestId);
    }
    throw new ApiError("Unknown error", 0);
  }
}

export function isMockMode(): boolean {
  const base = getBaseUrl();
  return (
    !base ||
    process.env.NEXT_PUBLIC_USE_MOCK === "true" ||
    process.env.NEXT_PUBLIC_USE_MOCK === "1"
  );
}
