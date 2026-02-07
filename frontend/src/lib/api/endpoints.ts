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

  jobs: () => `${PREFIX}/jobs`,
  job: (id: string) => `${PREFIX}/jobs/${id}`,

  workers: () => `${PREFIX}/workers`,

  metricsSummary: () => `${PREFIX}/metrics/summary`,

  events: (params?: { stream_id?: string; limit?: number }) => {
    const search = new URLSearchParams();
    if (params?.stream_id) search.set("stream_id", params.stream_id);
    if (params?.limit != null) search.set("limit", String(params.limit));
    const q = search.toString();
    return `${PREFIX}/events${q ? `?${q}` : ""}`;
  },
} as const;
