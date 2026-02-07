"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { fetchStream, streamStart, streamStop } from "@/lib/api";
import { streamDetailQueryOptions } from "@/lib/query/query-client";
import type { Stream } from "@/lib/api/types";
import { StreamStatusBadge } from "./stream-status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function StreamDetailView({ streamId }: { streamId: string }) {
  const queryClient = useQueryClient();
  const { data: stream, isLoading, error } = useQuery({
    ...streamDetailQueryOptions(streamId),
    queryFn: () => fetchStream(streamId),
  });

  async function handleStart() {
    const source_rtsp =
      stream?.pipeline_params?.source_rtsp?.trim() || "rtsp://example/stream";
    try {
      await streamStart({
        channel_id: streamId,
        source_rtsp,
        output: stream?.pipeline_params?.output ?? "hls",
      });
      await queryClient.invalidateQueries({ queryKey: ["streams", streamId] });
      await queryClient.invalidateQueries({ queryKey: ["streams"] });
    } catch (e) {
      console.error(e);
    }
  }

  async function handleStop() {
    try {
      await streamStop(streamId);
      await queryClient.invalidateQueries({ queryKey: ["streams", streamId] });
      await queryClient.invalidateQueries({ queryKey: ["streams"] });
    } catch (e) {
      console.error(e);
    }
  }

  if (error) {
    return (
      <Card className="border-destructive/50">
        <CardContent className="pt-6">
          <p className="text-destructive">Failed to load stream: {error.message}</p>
          <Link href="/streams" className="mt-2 inline-block text-primary hover:underline">
            ← Back to list
          </Link>
        </CardContent>
      </Card>
    );
  }

  if (isLoading || !stream) {
    return (
      <div className="text-muted-foreground">
        {isLoading ? "Loading…" : "Stream not found."}
        <Link href="/streams" className="ml-2 text-primary hover:underline">
          Back to list
        </Link>
      </div>
    );
  }

  const isRunning = stream.status === "RUNNING";
  const isStopped =
    stream.status === "STOPPED" || stream.status === "CREATED";
  const canStart = isStopped && stream.pipeline_params?.source_rtsp;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <Link
            href="/streams"
            className="text-sm text-muted-foreground hover:text-foreground"
          >
            ← Streams
          </Link>
          <h1 className="mt-1 text-2xl font-bold">{stream.channel_id}</h1>
          <StreamStatusBadge status={stream.status} className="mt-2" />
        </div>
        <div className="flex gap-2">
          {canStart && (
            <Button onClick={handleStart}>Start</Button>
          )}
          {isRunning && (
            <Button variant="destructive" onClick={handleStop}>
              Stop
            </Button>
          )}
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Status</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <p>
            <span className="text-muted-foreground">Worker:</span>{" "}
            {stream.worker_id ?? "—"}
          </p>
          <p>
            <span className="text-muted-foreground">Current job:</span>{" "}
            {stream.current_job_id ?? "—"}
          </p>
          <p>
            <span className="text-muted-foreground">Desired state:</span>{" "}
            {stream.desired_state ?? "—"}
          </p>
          {stream.last_error && (
            <p className="text-destructive">Last error: {stream.last_error}</p>
          )}
          {stream.pipeline_params?.source_rtsp && (
            <p>
              <span className="text-muted-foreground">Source RTSP:</span>{" "}
              <code className="rounded bg-muted px-1 text-xs">
                {stream.pipeline_params.source_rtsp}
              </code>
            </p>
          )}
        </CardContent>
      </Card>

      {!canStart && isStopped && (
        <p className="text-sm text-muted-foreground">
          Set pipeline_params.source_rtsp via API PATCH to enable Start.
        </p>
      )}
    </div>
  );
}
