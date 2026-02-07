import { QueryClient } from "@tanstack/react-query";

const DEFAULT_POLL_MS = 2000;

/** 탭 비활성화 시 폴링 간격 증가(15s). 활성 시에는 설정 또는 기본 2s */
function getRefetchIntervalMs(): number {
  if (typeof document === "undefined") return DEFAULT_POLL_MS;
  if (document.visibilityState === "hidden") return 15000;
  if (typeof window === "undefined") return DEFAULT_POLL_MS;
  try {
    const raw = window.localStorage?.getItem("streaming-console:pollIntervalMs");
    if (raw != null && raw !== "") {
      const n = Number(raw);
      if (Number.isFinite(n) && n > 0) return n;
    }
  } catch {
    // ignore
  }
  return DEFAULT_POLL_MS;
}

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000,
      refetchOnWindowFocus: false,
      refetchInterval: getRefetchIntervalMs,
    },
  },
});

/** streams: limit/offset 파라미터 지원, 동일 queryKey로 중복 폴링 방지 */
export const streamListQueryOptions = (params?: {
  limit?: number;
  offset?: number;
}) => ({
  queryKey: ["streams", params] as const,
  refetchInterval: getRefetchIntervalMs,
});

/** detail: 1~2s */
export const streamDetailQueryOptions = (id: string) => ({
  queryKey: ["streams", id] as const,
  refetchInterval: () => Math.min(getRefetchIntervalMs(), 1500),
});

/** jobs: limit/offset 파라미터 지원 */
export const jobsQueryOptions = (params?: {
  limit?: number;
  offset?: number;
  status?: string;
  stream_id?: string;
}) => ({
  queryKey: ["jobs", params] as const,
  refetchInterval: getRefetchIntervalMs,
});

export const workersQueryOptions = {
  queryKey: ["workers"] as const,
  refetchInterval: getRefetchIntervalMs,
};

/** events: 3~5s */
export const eventsQueryOptions = (params?: {
  stream_id?: string;
  limit?: number;
  level?: string;
  type?: string;
}) => ({
  queryKey: ["events", params] as const,
  refetchInterval: () => Math.min(getRefetchIntervalMs() * 2, 5000),
});

export const metricsSummaryQueryOptions = {
  queryKey: ["metrics", "summary"] as const,
  refetchInterval: getRefetchIntervalMs,
};
