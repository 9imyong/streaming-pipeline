import { QueryClient } from "@tanstack/react-query";

const POLL_MS =
  typeof process !== "undefined" &&
  process.env.NEXT_PUBLIC_POLL_INTERVAL_MS
    ? Number(process.env.NEXT_PUBLIC_POLL_INTERVAL_MS)
    : 2000;

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000,
      refetchOnWindowFocus: false,
    },
  },
});

export const streamListQueryOptions = {
  queryKey: ["streams"] as const,
  refetchInterval: POLL_MS,
};

export const streamDetailQueryOptions = (id: string) => ({
  queryKey: ["streams", id] as const,
  refetchInterval: POLL_MS,
});

export const jobsQueryOptions = {
  queryKey: ["jobs"] as const,
  refetchInterval: POLL_MS,
};

export const workersQueryOptions = {
  queryKey: ["workers"] as const,
  refetchInterval: POLL_MS,
};

export const eventsQueryOptions = (params?: { stream_id?: string; limit?: number }) => ({
  queryKey: ["events", params] as const,
  refetchInterval: Math.min(POLL_MS * 2, 5000),
});

export const metricsSummaryQueryOptions = {
  queryKey: ["metrics", "summary"] as const,
  refetchInterval: POLL_MS,
};
