"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import { fetchStream, streamStart, streamStop } from "@/lib/api";
import { ApiError } from "@/lib/api/client";
import { streamDetailQueryOptions } from "@/lib/query/query-client";
import { useEventsRealtime } from "@/lib/realtime/use-events-realtime";
import { getRole, canRunStreamCommands } from "@/lib/storage/settings";
import type { Stream } from "@/lib/api/types";
import { StreamStatusBadge } from "./stream-status-badge";
import { StreamPlayer } from "./stream-player";
import { FailedStreamDiagnostics } from "./failed-stream-diagnostics";
import { StreamStateTimeline } from "./stream-state-timeline";
import { CommandAuditTrail } from "./command-audit-trail";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EventsTable } from "@/components/events/events-table";

type CommandKind = "start" | "stop" | "retry" | null;

function commandErrorMessage(e: unknown): string {
  if (e instanceof ApiError) {
    if (e.status === 409) return "Stream is already in that state (RUNNING/STOPPED).";
    if (e.status === 404) return "Stream not found.";
    if (e.status >= 500) return "Server error. Try again later.";
    return e.message || "Request failed";
  }
  return e instanceof Error ? e.message : "Request failed";
}

export function StreamDetailView({ streamId }: { streamId: string }) {
  const queryClient = useQueryClient();
  const [commandLoading, setCommandLoading] = useState<CommandKind>(null);
  const { data: stream, isLoading, error, refetch } = useQuery({
    ...streamDetailQueryOptions(streamId),
    queryFn: () => fetchStream(streamId),
  });

  const { events: streamEvents } = useEventsRealtime({
    stream_id: streamId,
    limit: 50,
    useSse: true,
    toastOnLevel: false,
  });

  async function handleStart() {
    const source_rtsp =
      stream?.pipeline_params?.source_rtsp?.trim() || "rtsp://example/stream";
    setCommandLoading("start");
    try {
      await streamStart({
        channel_id: streamId,
        source_rtsp,
        output: stream?.pipeline_params?.output ?? "hls",
      });
      await queryClient.invalidateQueries({ queryKey: ["streams", streamId] });
      await queryClient.invalidateQueries({ queryKey: ["streams"] });
      toast.success("Command accepted. State will update shortly.");
    } catch (e) {
      toast.error(commandErrorMessage(e));
    } finally {
      setCommandLoading(null);
    }
  }

  async function handleStop() {
    if (
      !window.confirm(
        `Stop stream "${streamId}"?\n\n영상 전송이 중단되며, HLS 미리보기도 끊깁니다. 필요 시 다시 Start 하세요.`
      )
    )
      return;
    setCommandLoading("stop");
    try {
      await streamStop(streamId);
      await queryClient.invalidateQueries({ queryKey: ["streams", streamId] });
      await queryClient.invalidateQueries({ queryKey: ["streams"] });
      toast.success("Command accepted. State will update shortly.");
    } catch (e) {
      toast.error(commandErrorMessage(e));
    } finally {
      setCommandLoading(null);
    }
  }

  async function handleRetry() {
    const source_rtsp =
      stream?.pipeline_params?.source_rtsp?.trim() || "rtsp://example/stream";
    setCommandLoading("retry");
    try {
      await streamStart({
        channel_id: streamId,
        source_rtsp,
        output: stream?.pipeline_params?.output ?? "hls",
      });
      await queryClient.invalidateQueries({ queryKey: ["streams", streamId] });
      await queryClient.invalidateQueries({ queryKey: ["streams"] });
      toast.success("Command accepted. State will update shortly.");
    } catch (e) {
      toast.error(commandErrorMessage(e));
    } finally {
      setCommandLoading(null);
    }
  }

  const anyCommandLoading = commandLoading !== null;

  if (error) {
    return (
      <Card className="border-destructive/50">
        <CardContent className="pt-6">
          <p className="text-destructive">Failed to load stream: {error.message}</p>
          <Button variant="outline" size="sm" className="mt-2" onClick={() => refetch()}>
            Retry
          </Button>
          <Link href="/streams" className="mt-2 ml-2 inline-block text-primary hover:underline">
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
  const isFailed = stream.status === "FAILED";
  const canStart = isStopped && stream.pipeline_params?.source_rtsp;
  const canRunCommands = canRunStreamCommands(getRole());

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
          {canRunCommands && canStart && (
            <Button
              onClick={handleStart}
              disabled={anyCommandLoading}
              title="Source RTSP가 설정된 STOPPED/CREATED 상태에서만 가능"
            >
              {commandLoading === "start" ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                "Start"
              )}
            </Button>
          )}
          {canRunCommands && isRunning && (
            <Button
              variant="destructive"
              onClick={handleStop}
              disabled={anyCommandLoading}
              title="RUNNING 스트림 중단. 영상 전송·HLS 미리보기 중단됨"
            >
              {commandLoading === "stop" ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                "Stop"
              )}
            </Button>
          )}
          {canRunCommands && isFailed && (
            <Button
              variant="secondary"
              onClick={handleRetry}
              disabled={anyCommandLoading}
              title="FAILED 상태에서만 Retry 가능. 동일 설정으로 재시작"
            >
              {commandLoading === "retry" ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                "Retry"
              )}
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

      {isFailed && (
        <FailedStreamDiagnostics stream={stream} events={streamEvents} />
      )}

      <Card>
        <CardHeader>
          <CardTitle>State Timeline</CardTitle>
        </CardHeader>
        <CardContent>
          <StreamStateTimeline events={streamEvents} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>HLS Preview</CardTitle>
        </CardHeader>
        <CardContent>
          <StreamPlayer streamId={streamId} playPrompt="Click to play" />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Command History</CardTitle>
        </CardHeader>
        <CardContent>
          <CommandAuditTrail events={streamEvents} limit={15} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Recent events</CardTitle>
          <Link
            href="/events"
            className="text-sm text-primary hover:underline"
          >
            View all →
          </Link>
        </CardHeader>
        <CardContent>
          <EventsTable streamId={streamId} limit={20} embed />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Related jobs</CardTitle>
        </CardHeader>
        <CardContent>
          <Link
            href={`/jobs?stream_id=${encodeURIComponent(streamId)}`}
            className="text-primary hover:underline"
          >
            Jobs for this stream →
          </Link>
        </CardContent>
      </Card>
    </div>
  );
}
