/**
 * API 엔드포인트 — 백엔드와 다르면 이 파일만 수정
 * 현재: FastAPI Gateway /v1/streams (POST=Start, DELETE=Stop, GET=목록/상세)
 */
const PREFIX = "/v1";

export const endpoints = {
  streams: () => `${PREFIX}/streams`,
  stream: (id: string) => `${PREFIX}/streams/${id}`,
  /** Start: POST /v1/streams (body: channel_id, source_rtsp, output) */
  streamStart: () => `${PREFIX}/streams`,
  /** Stop: DELETE /v1/streams/:id */
  streamStop: (id: string) => `${PREFIX}/streams/${id}`,

  jobs: (params?: { limit?: number; status?: string; stream_id?: string }) => {
    const search = new URLSearchParams();
    if (params?.limit != null) search.set("limit", String(params.limit));
    if (params?.status) search.set("status", params.status);
    if (params?.stream_id) search.set("stream_id", params.stream_id);
    const q = search.toString();
    return `${PREFIX}/jobs${q ? `?${q}` : ""}`;
  },
  job: (id: string) => `${PREFIX}/jobs/${id}`,

  workers: () => `${PREFIX}/workers`,

  metricsSummary: () => `${PREFIX}/metrics/summary`,

  events: (params?: {
    stream_id?: string;
    limit?: number;
    level?: string;
    type?: string;
    since?: string;
  }) => {
    const search = new URLSearchParams();
    if (params?.stream_id) search.set("stream_id", params.stream_id);
    if (params?.limit != null) search.set("limit", String(params.limit));
    if (params?.level) search.set("level", params.level);
    if (params?.type) search.set("type", params.type);
    if (params?.since) search.set("since", params.since);
    const q = search.toString();
    return `${PREFIX}/events${q ? `?${q}` : ""}`;
  },
} as const;
