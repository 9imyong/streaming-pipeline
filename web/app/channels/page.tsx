"use client";

import useSWR from "swr";
import { HLSPlayer } from "@/components/HLSPlayer";
import { fetchStreams, fetchStream, startStream, stopStream, getHlsM3u8Url } from "@/lib/api";
import type { Stream } from "@/types";
import { useState } from "react";

const STATUS_COLOR: Record<string, string> = {
  pending: "text-gray-400",
  assigned: "text-yellow-400",
  running: "text-green-400",
  failed: "text-red-400",
  stopped: "text-gray-500",
};

export default function ChannelsPage() {
  const { data: streams = [], mutate } = useSWR<Stream[]>("streams", fetchStreams, {
    refreshInterval: 5000,
  });
  const [action, setAction] = useState<{ channel: string; op: "start" | "stop" } | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleStart(channelId: string) {
    setError(null);
    setAction({ channel: channelId, op: "start" });
    try {
      const detail = await fetchStream(channelId);
      const params = detail?.pipeline_params as { source_rtsp?: string; output?: string } | undefined;
      const source_rtsp = params?.source_rtsp?.trim();
      if (!source_rtsp) {
        setError(`${channelId}: Set source_rtsp via API PATCH or Streamlit first`);
        setAction(null);
        return;
      }
      await startStream({
        channel_id: channelId,
        source_rtsp,
        output: params?.output || "hls",
      });
      await mutate();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Start failed");
    } finally {
      setAction(null);
    }
  }

  async function handleStop(channelId: string) {
    setError(null);
    setAction({ channel: channelId, op: "stop" });
    try {
      await stopStream(channelId);
      await mutate();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Stop failed");
    } finally {
      setAction(null);
    }
  }

  return (
    <main className="p-6">
      <h1 className="text-2xl font-bold mb-4">Channels</h1>
      {error && (
        <div className="mb-4 p-3 bg-red-900/50 border border-red-700 rounded text-red-200">{error}</div>
      )}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {streams.map((s) => (
          <div
            key={s.channel_id}
            className="border border-gray-700 rounded-lg overflow-hidden bg-gray-900"
          >
            <div className="p-3 flex items-center justify-between border-b border-gray-800">
              <span className="font-mono font-semibold">{s.channel_id}</span>
              <span className={`text-sm ${STATUS_COLOR[s.status] ?? "text-gray-400"}`}>
                {s.status.toUpperCase()}
              </span>
            </div>
            <div className="aspect-video bg-black">
              <HLSPlayer
                src={getHlsM3u8Url(s.channel_id)}
                autoplay
                muted
                controls
                className="w-full h-full object-contain"
                onError={(msg) => setError(`${s.channel_id}: ${msg}`)}
              />
            </div>
            <div className="p-3 flex gap-2">
              <button
                onClick={() => handleStart(s.channel_id)}
                disabled={action?.channel === s.channel_id || s.status === "running"}
                className="px-3 py-1.5 rounded bg-green-700 hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
              >
                Start
              </button>
              <button
                onClick={() => handleStop(s.channel_id)}
                disabled={action?.channel === s.channel_id || s.status !== "running"}
                className="px-3 py-1.5 rounded bg-red-700 hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
              >
                Stop
              </button>
            </div>
            {s.last_error && (
              <div className="px-3 pb-2 text-xs text-red-300 truncate" title={s.last_error}>
                {s.last_error}
              </div>
            )}
          </div>
        ))}
      </div>
      {streams.length === 0 && (
        <p className="text-gray-500">No channels. Create one via API (POST /v1/streams) or Streamlit dev console.</p>
      )}
    </main>
  );
}
