/**
 * API 레이어: mock 모드면 mock 데이터, 아니면 apiClient로 실제 요청
 */
import { apiClient, isMockMode } from "./client";
import { endpoints } from "./endpoints";
import type {
  Source,
  SourceCreateBody,
  SourcePatchBody,
  CreateStreamFromSourceBody,
  Stream,
  StreamListItem,
  Job,
  Worker,
  StreamEvent,
  MetricsSummary,
} from "./types";
import * as mock from "./mock";

// Sources (CCTV)
export async function fetchSources(params?: {
  enabled?: boolean;
  q?: string;
  limit?: number;
  offset?: number;
}): Promise<Source[]> {
  if (isMockMode()) return mock.mockFetchSources(params);
  return apiClient<Source[]>(endpoints.sources(params));
}

export async function fetchSource(id: string): Promise<Source | null> {
  if (isMockMode()) return mock.mockFetchSource(id);
  try {
    return await apiClient<Source>(endpoints.source(id));
  } catch {
    return null;
  }
}

export async function createSource(body: SourceCreateBody): Promise<Source> {
  if (isMockMode()) return mock.mockCreateSource(body);
  return apiClient<Source>(endpoints.sources(), {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function updateSource(
  id: string,
  body: SourcePatchBody
): Promise<Source> {
  if (isMockMode()) return mock.mockUpdateSource(id, body);
  return apiClient<Source>(endpoints.source(id), {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export async function validateSource(
  id: string
): Promise<{ ok: boolean; message?: string }> {
  if (isMockMode()) return mock.mockValidateSource(id);
  return apiClient<{ ok: boolean; message?: string }>(
    endpoints.sourceValidate(id),
    { method: "POST" }
  );
}

export async function createStreamFromSource(
  sourceId: string,
  body: CreateStreamFromSourceBody
): Promise<{ stream_id?: string }> {
  if (isMockMode()) return mock.mockCreateStreamFromSource(sourceId, body);
  return apiClient<{ stream_id?: string }>(
    endpoints.sourceStreams(sourceId),
    {
      method: "POST",
      body: JSON.stringify(body),
    }
  );
}

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
  Source,
  SourceCreateBody,
  SourcePatchBody,
  CreateStreamFromSourceBody,
  Stream,
  StreamListItem,
  Job,
  Worker,
  StreamEvent,
  MetricsSummary,
} from "./types";
export type { StreamStatus, JobStatus, WorkerStatus } from "./types";
