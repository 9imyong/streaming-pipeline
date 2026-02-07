import type {
  Stream,
  StreamListItem,
  Job,
  Worker,
  StreamEvent,
  MetricsSummary,
} from "./types";

export const mockStreamList: StreamListItem[] = [
  {
    channel_id: "ch-01",
    status: "RUNNING",
    desired_state: "running",
    assigned_worker_id: "stream-worker-1",
    restart_count: 0,
    last_error: null,
    updated_at: new Date().toISOString(),
  },
  {
    channel_id: "ch-02",
    status: "STOPPED",
    desired_state: "stopped",
    assigned_worker_id: null,
    restart_count: 0,
    last_error: null,
    updated_at: new Date().toISOString(),
  },
  {
    channel_id: "ch-03",
    status: "FAILED",
    desired_state: "running",
    assigned_worker_id: null,
    restart_count: 2,
    last_error: "Connection refused",
    updated_at: new Date().toISOString(),
  },
];

export const mockStreamDetails: Record<string, Stream> = {
  "ch-01": {
    channel_id: "ch-01",
    status: "RUNNING",
    worker_id: "stream-worker-1",
    current_job_id: "job-001",
    desired_state: "running",
    last_error: null,
    restart_count: 0,
    updated_at: new Date().toISOString(),
    pipeline_params: { source_rtsp: "rtsp://example/1", output: "hls" },
  },
  "ch-02": {
    channel_id: "ch-02",
    status: "STOPPED",
    worker_id: null,
    desired_state: "stopped",
    pipeline_params: { source_rtsp: "rtsp://example/2", output: "hls" },
  },
  "ch-03": {
    channel_id: "ch-03",
    status: "FAILED",
    last_error: "Connection refused",
    restart_count: 2,
    pipeline_params: null,
  },
};

export const mockJobs: Job[] = [
  {
    id: "j1",
    job_id: "job-001",
    stream_id: "ch-01",
    type: "inference",
    status: "DONE",
    duration_ms: 120,
    created_at: new Date(Date.now() - 60_000).toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: "j2",
    job_id: "job-002",
    stream_id: "ch-01",
    type: "segment",
    status: "PROCESSING",
    created_at: new Date(Date.now() - 30_000).toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: "j3",
    job_id: "job-003",
    stream_id: "ch-03",
    type: "stream",
    status: "FAILED",
    failure_reason: "Connection refused",
    error_code: "ECONNREFUSED",
    error_message: "Connection refused",
    payload: { channel_id: "ch-03", source_rtsp: "rtsp://example/3" },
    created_at: new Date(Date.now() - 120_000).toISOString(),
    updated_at: new Date().toISOString(),
  },
];

export const mockWorkers: Worker[] = [
  {
    id: "w1",
    worker_id: "worker-stream-1",
    status: "BUSY",
    current_streams: 1,
    current_streams_count: 1,
    last_seen: new Date().toISOString(),
  },
  {
    id: "w2",
    worker_id: "worker-stream-2",
    status: "IDLE",
    current_streams: 0,
    current_streams_count: 0,
    last_seen: new Date().toISOString(),
  },
  {
    id: "w3",
    worker_id: "worker-stream-3",
    status: "DOWN",
    current_streams: 0,
    last_seen: new Date(Date.now() - 60_000).toISOString(),
  },
];

export const mockEvents: StreamEvent[] = [
  {
    ts: new Date().toISOString(),
    level: "INFO",
    stream_id: "ch-01",
    type: "STATE_CHANGED",
    message: "Pipeline started",
    payload: { from: "STOPPED", to: "RUNNING" },
  },
  {
    ts: new Date(Date.now() - 5000).toISOString(),
    level: "ERROR",
    stream_id: "ch-03",
    entity: { job_id: "job-003" },
    type: "COMMAND_SENT",
    message: "Connection refused",
    payload: { error: "ECONNREFUSED", detail: "Connection refused" },
  },
  {
    ts: new Date(Date.now() - 10_000).toISOString(),
    level: "WARN",
    stream_id: "ch-03",
    type: "ASSIGNED",
    message: "Worker lost",
  },
];

export const mockMetricsSummary: MetricsSummary = {
  running_streams: 1,
  failed_streams: 1,
  queued_jobs: 1,
  active_workers: 2,
  active_streams: 1,
  jobs_rate: 12,
  p95_latency_ms: 150,
  error_rate: 0.02,
};

function delay(ms: number): Promise<void> {
  return new Promise((r) => setTimeout(r, ms));
}

export async function mockFetchStreams(): Promise<StreamListItem[]> {
  await delay(300);
  return [...mockStreamList];
}

export async function mockFetchStream(id: string): Promise<Stream | null> {
  await delay(200);
  return mockStreamDetails[id] ?? mockStreamDetails["ch-01"] ?? null;
}

export async function mockFetchJobs(params?: {
  stream_id?: string;
  status?: string;
  limit?: number;
}): Promise<Job[]> {
  await delay(300);
  let list = [...mockJobs];
  if (params?.stream_id) {
    list = list.filter((j) => j.stream_id === params.stream_id);
  }
  if (params?.status) {
    list = list.filter((j) => j.status === params.status);
  }
  if (params?.limit != null) {
    list = list.slice(0, params.limit);
  }
  return list;
}

export async function mockFetchJob(id: string): Promise<Job | null> {
  await delay(200);
  return mockJobs.find((j) => j.job_id === id || j.id === id) ?? null;
}

export async function mockFetchWorkers(): Promise<Worker[]> {
  await delay(300);
  return [...mockWorkers];
}

export async function mockFetchEvents(params?: {
  stream_id?: string;
  limit?: number;
  level?: string;
  type?: string;
}): Promise<StreamEvent[]> {
  await delay(300);
  let list = [...mockEvents];
  if (params?.stream_id) {
    list = list.filter((e) => e.stream_id === params.stream_id);
  }
  if (params?.level) {
    list = list.filter((e) => e.level === params.level);
  }
  if (params?.type) {
    list = list.filter((e) => e.type === params.type);
  }
  if (params?.limit != null) {
    list = list.slice(0, params.limit);
  }
  return list;
}

export async function mockFetchMetricsSummary(): Promise<MetricsSummary> {
  await delay(200);
  return { ...mockMetricsSummary };
}
