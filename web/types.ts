export interface Stream {
  channel_id: string;
  status: string;
  desired_state?: string | null;
  assigned_worker_id?: string | null;
  restart_count: number;
  last_error?: string | null;
  updated_at?: string | null;
  current_job_id?: string | null;
  pipeline_params?: Record<string, unknown> | null;
}

export interface StreamEvent {
  event: string;
  channel_id: string;
  worker_id?: string;
  job_id?: string;
  message?: string;
  last_error?: string;
  ts?: string;
}
