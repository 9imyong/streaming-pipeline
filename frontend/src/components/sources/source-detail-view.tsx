"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import {
  fetchSource,
  updateSource,
  validateSource,
  createStreamFromSource,
} from "@/lib/api";
import { ApiError } from "@/lib/api/client";
import { sourceDetailQueryOptions } from "@/lib/query/query-client";
import { canRunStreamCommands, getRole } from "@/lib/storage/settings";
import type { Source } from "@/lib/api/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function SourceDetailView({ sourceId }: { sourceId: string }) {
  const queryClient = useQueryClient();
  const [loading, setLoading] = useState<"toggle" | "validate" | "stream" | null>(null);

  const { data: source, isLoading, error, refetch } = useQuery({
    ...sourceDetailQueryOptions(sourceId),
    queryFn: () => fetchSource(sourceId),
  });

  const canRun = canRunStreamCommands(getRole());

  async function handleToggleEnabled() {
    if (!source) return;
    setLoading("toggle");
    try {
      await updateSource(sourceId, { enabled: !source.enabled });
      await queryClient.invalidateQueries({ queryKey: ["sources", sourceId] });
      await queryClient.invalidateQueries({ queryKey: ["sources"] });
      toast.success(source.enabled ? "Disabled" : "Enabled");
    } catch (e) {
      toast.error(e instanceof ApiError ? e.message : "Failed");
    } finally {
      setLoading(null);
    }
  }

  async function handleValidate() {
    setLoading("validate");
    try {
      const res = await validateSource(sourceId);
      if (res.ok) toast.success("RTSP connection OK");
      else toast.error(res.message ?? "Validation failed");
    } catch (e) {
      toast.error(e instanceof ApiError ? e.message : "Failed");
    } finally {
      setLoading(null);
    }
  }

  async function handleCreateStream(mode: "start" | "create_only") {
    setLoading("stream");
    try {
      const res = await createStreamFromSource(sourceId, { mode });
      await queryClient.invalidateQueries({ queryKey: ["streams"] });
      toast.success(
        res.stream_id
          ? `Stream ${res.stream_id} ${mode === "start" ? "started" : "created"}`
          : "Command accepted"
      );
      if (res.stream_id) {
        window.location.href = `/streams/${res.stream_id}`;
      }
    } catch (e) {
      toast.error(e instanceof ApiError ? e.message : "Failed");
    } finally {
      setLoading(null);
    }
  }

  if (error) {
    return (
      <Card className="border-destructive/50">
        <CardContent className="pt-6">
          <p className="text-destructive">Failed to load source: {error.message}</p>
          <Button variant="outline" size="sm" className="mt-2" onClick={() => refetch()}>
            Retry
          </Button>
          <Link href="/sources" className="mt-2 ml-2 inline-block text-primary hover:underline">
            ← Sources
          </Link>
        </CardContent>
      </Card>
    );
  }

  if (isLoading || !source) {
    return (
      <div className="text-muted-foreground">
        {isLoading ? "Loading…" : "Source not found."}
        <Link href="/sources" className="ml-2 text-primary hover:underline">
          ← Sources
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <Link
            href="/sources"
            className="text-sm text-muted-foreground hover:text-foreground"
          >
            ← Sources
          </Link>
          <h1 className="mt-1 text-2xl font-bold">{source.name}</h1>
          <p className="text-sm text-muted-foreground">{source.source_id}</p>
          <Badge
            variant={source.enabled ? "default" : "secondary"}
            className="mt-2"
          >
            {source.enabled ? "Enabled" : "Disabled"}
          </Badge>
        </div>
        <div className="flex gap-2">
          <Button
            variant="secondary"
            onClick={handleToggleEnabled}
            disabled={loading !== null}
          >
            {loading === "toggle" ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : source.enabled ? (
              "Disable"
            ) : (
              "Enable"
            )}
          </Button>
          <Button
            variant="outline"
            onClick={handleValidate}
            disabled={loading !== null}
          >
            {loading === "validate" ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              "Validate RTSP"
            )}
          </Button>
          {canRun && source.enabled && (
            <>
              <Button
                onClick={() => handleCreateStream("create_only")}
                disabled={loading !== null}
              >
                {loading === "stream" ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  "Create Stream"
                )}
              </Button>
              <Button
                variant="default"
                onClick={() => handleCreateStream("start")}
                disabled={loading !== null}
              >
                {loading === "stream" ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  "Start Stream"
                )}
              </Button>
            </>
          )}
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <p>
            <span className="text-muted-foreground">RTSP URL:</span>{" "}
            <code className="rounded bg-muted px-1 text-xs break-all">
              {source.rtsp_url}
            </code>
          </p>
          {source.location && (
            <p>
              <span className="text-muted-foreground">Location:</span>{" "}
              {source.location}
            </p>
          )}
          {source.description && (
            <p>
              <span className="text-muted-foreground">Description:</span>{" "}
              {source.description}
            </p>
          )}
          {source.updated_at && (
            <p>
              <span className="text-muted-foreground">Updated:</span>{" "}
              {new Date(source.updated_at).toLocaleString()}
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
