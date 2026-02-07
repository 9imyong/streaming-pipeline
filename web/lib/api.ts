const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export async function fetchStreams(): Promise<import("@/types").Stream[]> {
  const res = await fetch(`${API_BASE}/v1/streams`, { cache: "no-store" });
  if (!res.ok) throw new Error(`streams list: ${res.status}`);
  return res.json();
}

export async function fetchStream(channelId: string): Promise<import("@/types").Stream | null> {
  const res = await fetch(`${API_BASE}/v1/streams/${encodeURIComponent(channelId)}`, {
    cache: "no-store",
  });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`stream: ${res.status}`);
  return res.json();
}

export interface StartStreamBody {
  channel_id: string;
  source_rtsp: string;
  output?: string;
  idempotency_key?: string;
}

export async function startStream(body: StartStreamBody): Promise<{ job_id: string; channel_id: string }> {
  const res = await fetch(`${API_BASE}/v1/streams`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `start: ${res.status}`);
  }
  return res.json();
}

export async function stopStream(channelId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/v1/streams/${encodeURIComponent(channelId)}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error(`stop: ${res.status}`);
}

export function getHlsM3u8Url(channelId: string): string {
  const base = process.env.NEXT_PUBLIC_HLS_BASE_URL || "http://localhost/hls";
  return `${base.replace(/\/$/, "")}/${encodeURIComponent(channelId)}/index.m3u8`;
}
