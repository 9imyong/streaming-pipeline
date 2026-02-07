/**
 * SSE(Server-Sent Events) 클라이언트
 * - EventSource 연결/재연결(backoff)
 * - 브라우저 EventSource는 커스텀 헤더 미지원 → api_key 쿼리 파라미터 사용
 */
import { getBaseUrl } from "@/lib/api/client";
import { getApiKey } from "@/lib/storage/settings";
import { endpoints } from "@/lib/api/endpoints";
import type { StreamEvent } from "@/lib/api/types";

export type SseConnectionStatus = "connected" | "reconnecting" | "offline";

const MAX_RECONNECT_ATTEMPTS = 10;
const INITIAL_BACKOFF_MS = 1000;
const MAX_BACKOFF_MS = 30_000;

function buildSseUrl(pathWithQuery: string): string {
  const base = getBaseUrl().replace(/\/$/, "");
  const url = pathWithQuery.startsWith("http")
    ? pathWithQuery
    : `${base}${pathWithQuery}`;
  const apiKey = typeof window !== "undefined" ? getApiKey() : "";
  if (!apiKey?.trim()) return url;
  const sep = url.includes("?") ? "&" : "?";
  return `${url}${sep}api_key=${encodeURIComponent(apiKey.trim())}`;
}

function parseSseEventData(raw: string): StreamEvent | null {
  const json = raw.startsWith("data:") ? raw.slice(5).trim() : raw.trim();
  if (!json || json === "[DONE]") return null;
  try {
    return JSON.parse(json) as StreamEvent;
  } catch {
    return null;
  }
}

export interface EventsSseOptions {
  stream_id?: string;
  since?: string;
  onEvent?: (event: StreamEvent) => void;
  onStatus?: (status: SseConnectionStatus) => void;
}

export interface EventsSseHandle {
  disconnect: () => void;
  getStatus: () => SseConnectionStatus;
  getLastEventId: () => string | null;
}

/**
 * SSE로 이벤트 스트림 구독.
 * - 연결 끊기면 backoff 재연결
 * - MAX_RECONNECT_ATTEMPTS 초과 시 onStatus('offline') 호출 후 재시도 중단
 */
export function subscribeEventsSse(
  options: EventsSseOptions = {}
): EventsSseHandle {
  const { stream_id, since, onEvent, onStatus } = options;
  let es: EventSource | null = null;
  let status: SseConnectionStatus = "reconnecting";
  let lastEventId: string | null = since ?? null;
  let reconnectAttempts = 0;
  let backoffMs = INITIAL_BACKOFF_MS;
  let timeoutId: ReturnType<typeof setTimeout> | null = null;
  let closed = false;

  function setStatus(s: SseConnectionStatus) {
    status = s;
    onStatus?.(s);
  }

  function cleanup() {
    if (timeoutId != null) {
      clearTimeout(timeoutId);
      timeoutId = null;
    }
    if (es) {
      es.close();
      es = null;
    }
  }

  function connect() {
    if (closed) return;
    cleanup();
    const query: Record<string, string> = {};
    if (stream_id?.trim()) query.stream_id = stream_id.trim();
    if (lastEventId) query.since = lastEventId;
    const path = endpoints.eventsStream(query);
    const url = buildSseUrl(path);
    setStatus(reconnectAttempts > 0 ? "reconnecting" : "connected");

    es = new EventSource(url);

    es.onopen = () => {
      reconnectAttempts = 0;
      backoffMs = INITIAL_BACKOFF_MS;
      setStatus("connected");
    };

    es.onmessage = (e) => {
      if (e.lastEventId) lastEventId = e.lastEventId;
      const raw = e.data ?? "";
      const data = parseSseEventData(raw);
      if (data) onEvent?.(data);
    };

    es.onerror = () => {
      es?.close();
      es = null;
      setStatus("reconnecting");
      if (closed) return;
      reconnectAttempts += 1;
      if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
        setStatus("offline");
        return;
      }
      const delay = Math.min(backoffMs, MAX_BACKOFF_MS);
      backoffMs = Math.min(backoffMs * 2, MAX_BACKOFF_MS);
      timeoutId = setTimeout(connect, delay);
    };
  }

  connect();

  return {
    disconnect() {
      closed = true;
      cleanup();
      setStatus("offline");
    },
    getStatus: () => status,
    getLastEventId: () => lastEventId,
  };
}
