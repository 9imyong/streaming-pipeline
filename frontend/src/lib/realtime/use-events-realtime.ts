"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { toast } from "sonner";
import { fetchEvents } from "@/lib/api";
import { getPollIntervalMs } from "@/lib/storage/settings";
import { subscribeEventsSse, type SseConnectionStatus } from "./sse";
import type { StreamEvent } from "@/lib/api/types";
import { isMockMode } from "@/lib/api/client";

export interface UseEventsRealtimeOptions {
  stream_id?: string;
  limit?: number;
  level?: string;
  type?: string;
  /** SSE 실시간 사용 여부 (mock 모드에서는 false) */
  useSse?: boolean;
  /** ERROR/WARN 이벤트 시 toast 표시 */
  toastOnLevel?: boolean;
}

export interface UseEventsRealtimeResult {
  events: StreamEvent[];
  status: SseConnectionStatus | "polling" | "initial";
  isLoading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
}

export function useEventsRealtime(
  params: UseEventsRealtimeOptions = {}
): UseEventsRealtimeResult {
  const {
    stream_id,
    limit = 200,
    level,
    type,
    useSse = true,
    toastOnLevel = true,
  } = params;

  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [status, setStatus] = useState<SseConnectionStatus | "polling" | "initial">("initial");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const sseRef = useRef<ReturnType<typeof subscribeEventsSse> | null>(null);
  const lastToastTs = useRef<Record<string, number>>({});

  const fetchParamsRef = useRef({
    stream_id: stream_id?.trim() || undefined,
    limit,
    level,
    type,
  });
  fetchParamsRef.current = {
    stream_id: stream_id?.trim() || undefined,
    limit,
    level,
    type,
  };

  const refetch = useCallback(async () => {
    setError(null);
    const p = fetchParamsRef.current;
    try {
      const list = await fetchEvents(p);
      setEvents(list);
    } catch (e) {
      setError(e instanceof Error ? e : new Error(String(e)));
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    fetchEvents(fetchParams)
      .then((list) => {
        if (!cancelled) setEvents(list);
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e : new Error(String(e)));
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [stream_id, limit, level, type]);

  // SSE + fallback polling (skip in mock mode)
  useEffect(() => {
    if (isMockMode() || !useSse) {
      pollRef.current = setInterval(refetch, getPollIntervalMs());
      setStatus("polling");
      return () => {
        if (pollRef.current) clearInterval(pollRef.current);
        pollRef.current = null;
      };
    }

    const handle = subscribeEventsSse({
      stream_id,
      onEvent(ev) {
        setEvents((prev) => [ev, ...prev].slice(0, limit));
        if (toastOnLevel && (ev.level === "ERROR" || ev.level === "WARN")) {
          const key = `${ev.ts}-${ev.stream_id ?? ""}-${ev.type}`;
          const now = Date.now();
          if (!lastToastTs.current[key] || now - lastToastTs.current[key] > 5000) {
            lastToastTs.current[key] = now;
            if (ev.level === "ERROR") {
              toast.error(ev.message ?? "Event error", {
                description: ev.stream_id ? `stream: ${ev.stream_id}` : undefined,
              });
            } else {
              toast.warning(ev.message ?? "Event warning", {
                description: ev.stream_id ? `stream: ${ev.stream_id}` : undefined,
              });
            }
          }
        }
      },
      onStatus(s) {
        setStatus(s);
        if (s === "offline") {
          pollRef.current = setInterval(refetch, getPollIntervalMs());
        }
      },
    });
    sseRef.current = handle;

    return () => {
      handle.disconnect();
      sseRef.current = null;
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
  }, [useSse, stream_id, limit, toastOnLevel]);

  // 탭 포커스 시 재동기화: polling일 때만 refetch (SSE는 자동 재연결)
  useEffect(() => {
    const onFocus = () => {
      if (status === "polling" || status === "offline") refetch();
    };
    document.addEventListener("visibilitychange", onFocus);
    return () => document.removeEventListener("visibilitychange", onFocus);
  }, [status, refetch]);

  return { events, status, isLoading, error, refetch };
}
