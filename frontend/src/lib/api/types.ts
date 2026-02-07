/**
 * 프론트 상태 enum — 백엔드와 맞출 것
 */
export type StreamStatus =
  | "CREATED"
  | "ASSIGNED"
  | "RUNNING"
  | "FAILED"
  | "STOPPED";

export type JobStatus = "PENDING" | "PROCESSING" | "DONE" | "FAILED";

export type WorkerStatus = "IDLE" | "BUSY" | "DOWN";

/** 목록 항목 (GET /v1/streams) */
export interface StreamListItem {
  channel_id: string;
  status: StreamStatus;
  desired_state?: string | null;
  assigned_worker_id?: string | null;
  restart_count?: number;
  last_error?: string | null;
  updated_at?: string | null;
}

/** 상세 (GET /v1/streams/:id) */
export interface Stream {
  channel_id: string;
  status: StreamStatus;
  worker_id?: string | null;
  current_job_id?: string | null;
  desired_state?: string | null;
  last_error?: string | null;
  restart_count?: number;
  updated_at?: string | null;
  pipeline_params?: {
    source_rtsp?: string;
    output?: string;
  } | null;
}

export interface Job {
  id: string;
  job_id: string;
  stream_id: string;
  type: string;
  status: JobStatus;
  payload?: unknown;
  result?: unknown;
  failure_reason?: string | null;
  error_code?: string | null;
  error_message?: string | null;
  stack?: string | null;
  duration_ms?: number | null;
  created_at: string;
  updated_at: string;
}

export interface Worker {
  id: string;
  worker_id: string;
  status: WorkerStatus;
  gpu_usage?: number | null;
  current_streams?: number | null;
  current_streams_count?: number | null;
  last_seen?: string | null;
  gpu?: { name?: string; mem_used?: number; util?: number } | null;
}

export interface StreamEvent {
  ts: string;
  level: string;
  stream_id?: string | null;
  entity?: { job_id?: string; worker_id?: string } | null;
  type: string;
  message: string;
  request_id?: string | null;
  payload?: unknown;
}

export interface MetricsSummary {
  running_streams?: number;
  failed_streams?: number;
  queued_jobs?: number;
  active_workers?: number;
  active_streams?: number;
  jobs_rate?: number;
  p95_latency_ms?: number | null;
  error_rate?: number | null;
}
