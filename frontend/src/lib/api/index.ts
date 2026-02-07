/**
 * API 레이어: mock 모드면 mock 데이터, 아니면 apiClient로 실제 요청
 */
import { apiClient, isMockMode } from "./client";
import { endpoints } from "./endpoints";
import type {
  Stream,
  StreamListItem,
  Job,
  Worker,
  StreamEvent,
  MetricsSummary,
} from "./types";
import * as mock from "./mock";

// Streams — 백엔드: GET list (limit/offset), GET one, POST (start), DELETE (stop)
export async function fetchStreams(params?: {
  limit?: number;
  offset?: number;
}): Promise<StreamListItem[]> {
  if (isMockMode()) return mock.mockFetchStreams();
  return apiClient<StreamListItem[]>(endpoints.streams(params));
}

export async function fetchStream(id: string): Promise<Stream | null> {
  if (isMockMode()) return mock.mockFetchStream(id);
  try {
    return await apiClient<Stream>(endpoints.stream(id));
  } catch {
    return null;
  }
}

export async function streamStart(body: {
  channel_id: string;
  source_rtsp: string;
  output?: string;
}): Promise<void> {
  if (isMockMode()) return;
  await apiClient<void>(endpoints.streamStart(), {
    method: "POST",
    body: JSON.stringify({ ...body, output: body.output ?? "hls" }),
  });
}

export async function streamStop(id: string): Promise<void> {
  if (isMockMode()) return;
  await apiClient<void>(endpoints.streamStop(id), { method: "DELETE" });
}

// Jobs — limit/offset 서버 페이지네이션 가정
export async function fetchJobs(params?: {
  limit?: number;
  offset?: number;
  status?: string;
  stream_id?: string;
}): Promise<Job[]> {
  if (isMockMode()) return mock.mockFetchJobs(params);
  return apiClient<Job[]>(endpoints.jobs(params));
}

export async function fetchJob(id: string): Promise<Job | null> {
  if (isMockMode()) return mock.mockFetchJob(id);
  try {
    return await apiClient<Job>(endpoints.job(id));
  } catch {
    return null;
  }
}

// Workers
export async function fetchWorkers(): Promise<Worker[]> {
  if (isMockMode()) return mock.mockFetchWorkers();
  return apiClient<Worker[]>(endpoints.workers());
}

// Events
export async function fetchEvents(params?: {
  stream_id?: string;
  limit?: number;
  level?: string;
  type?: string;
  since?: string;
}): Promise<StreamEvent[]> {
  if (isMockMode()) return mock.mockFetchEvents(params);
  return apiClient<StreamEvent[]>(endpoints.events(params));
}

// Metrics
export async function fetchMetricsSummary(): Promise<MetricsSummary> {
  if (isMockMode()) return mock.mockFetchMetricsSummary();
  return apiClient<MetricsSummary>(endpoints.metricsSummary());
}

// Re-export for consumers
export { isMockMode, ApiError } from "./client";
export type {
  Stream,
  StreamListItem,
  Job,
  Worker,
  StreamEvent,
  MetricsSummary,
} from "./types";
export type { StreamStatus, JobStatus, WorkerStatus } from "./types";
