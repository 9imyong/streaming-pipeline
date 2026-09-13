/**
 * API 엔드포인트 — 백엔드와 다르면 이 파일만 수정
 * 현재: FastAPI Gateway /v1/streams (POST=Start, DELETE=Stop, GET=목록/상세)
 */
const PREFIX = "/v1";

export const endpoints = {
  /** Sources (CCTV) */
  sources: (params?: {
    enabled?: boolean;
    q?: string;
    limit?: number;
    offset?: number;
  }) => {
    const search = new URLSearchParams();
    if (params?.enabled !== undefined)
      search.set("enabled", String(params.enabled));
    if (params?.q) search.set("q", params.q);
    if (params?.limit != null) search.set("limit", String(params.limit));
    if (params?.offset != null) search.set("offset", String(params.offset));
    const q = search.toString();
    return `${PREFIX}/sources${q ? `?${q}` : ""}`;
  },
  source: (id: string) => `${PREFIX}/sources/${id}`,
  sourceValidate: (id: string) => `${PREFIX}/sources/${id}/validate`,
  /** POST /v1/sources/:id/streams — Source 기반 Stream 생성/시작 */
  sourceStreams: (sourceId: string) => `${PREFIX}/sources/${sourceId}/streams`,

  /** 목록: limit/offset 서버 페이지네이션 가정 */
  streams: (params?: { limit?: number; offset?: number }) => {
    const search = new URLSearchParams();
    if (params?.limit != null) search.set("limit", String(params.limit));
    if (params?.offset != null) search.set("offset", String(params.offset));
    const q = search.toString();
    return `${PREFIX}/streams${q ? `?${q}` : ""}`;
  },
  stream: (id: string) => `${PREFIX}/streams/${id}`,
  /** Start: POST /v1/streams (body: channel_id, source_rtsp, output) */
  streamStart: () => `${PREFIX}/streams`,
  /** Stop: DELETE /v1/streams/:id */
  streamStop: (id: string) => `${PREFIX}/streams/${id}`,

  /** 목록: limit/offset 서버 페이지네이션 가정 */
  jobs: (params?: {
    limit?: number;
    offset?: number;
    status?: string;
    stream_id?: string;
  }) => {
    const search = new URLSearchParams();
    if (params?.limit != null) search.set("limit", String(params.limit));
    if (params?.offset != null) search.set("offset", String(params.offset));
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
  /** SSE: GET /v1/events/stream?stream_id=&since= */
  eventsStream: (params?: { stream_id?: string; since?: string }) => {
    const search = new URLSearchParams();
    if (params?.stream_id) search.set("stream_id", params.stream_id);
    if (params?.since) search.set("since", params.since);
    const q = search.toString();
    return `${PREFIX}/events/stream${q ? `?${q}` : ""}`;
  },

  /** HLS: /hls/:streamId/index.m3u8 (baseUrl 기준) */
  hlsPlaylist: (streamId: string) => `/hls/${streamId}/index.m3u8`,
} as const;
