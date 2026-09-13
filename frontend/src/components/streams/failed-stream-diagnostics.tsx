"use client";

import { useMemo } from "react";
import Link from "next/link";
import type { Stream } from "@/lib/api/types";
import type { StreamEvent } from "@/lib/api/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertTriangle } from "lucide-react";

const STATE_CHANGED = "STATE_CHANGED";

function getOperatorGuide(lastError: string | null | undefined): string[] {
  if (!lastError) return ["last_error 없음. Worker/Job 로그 확인 권장."];
  const e = lastError.toLowerCase();
  const lines: string[] = [];
  if (e.includes("gpu") || e.includes("memory") || e.includes("cuda") || e.includes("oom")) {
    lines.push("• GPU/메모리 관련: Worker 상태·GPU 사용량 확인");
  }
  if (e.includes("rtsp") || e.includes("connection") || e.includes("econnrefused") || e.includes("timeout")) {
    lines.push("• RTSP/연결 실패: Source URL·네트워크 점검");
  }
  if (e.includes("worker") || e.includes("lost")) {
    lines.push("• Worker 이탈: 해당 Worker 상태·재할당 확인");
  }
  if (lines.length === 0) {
    lines.push("• Events·Job 상세에서 원인 추가 확인");
  }
  return lines;
}

export interface FailedStreamDiagnosticsProps {
  stream: Stream;
  events: StreamEvent[];
}

export function FailedStreamDiagnostics({ stream, events }: FailedStreamDiagnosticsProps) {
  const stateChangedEvents = useMemo(
    () => events.filter((ev) => ev.type === STATE_CHANGED).sort((a, b) => new Date(b.ts).getTime() - new Date(a.ts).getTime()),
    [events]
  );
  const lastTransition = stateChangedEvents[0] ?? null;
  const payload = lastTransition?.payload as { from?: string; to?: string } | undefined;
  const guideLines = useMemo(() => getOperatorGuide(stream.last_error ?? undefined), [stream.last_error]);

  return (
    <Card className="border-destructive/50">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-destructive">
          <AlertTriangle className="h-5 w-5" />
          FAILED 진단
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {lastTransition && (
          <div className="rounded bg-muted/50 p-3 text-sm">
            <p className="font-medium text-muted-foreground">마지막 상태 전이</p>
            <p className="mt-1">
              {new Date(lastTransition.ts).toLocaleString()} · {lastTransition.type}
              {payload?.from != null && payload?.to != null && (
                <span className="ml-1 text-muted-foreground">
                  ({payload.from} → {payload.to})
                </span>
              )}
            </p>
            {lastTransition.message && (
              <p className="mt-1 text-muted-foreground">{lastTransition.message}</p>
            )}
          </div>
        )}

        <div className="rounded border border-destructive/30 bg-destructive/5 p-3 text-sm">
          <p className="font-medium">실패 요약</p>
          <ul className="mt-2 space-y-1 text-muted-foreground">
            <li>
              <span className="text-foreground">오류:</span>{" "}
              {stream.last_error ?? "—"}
            </li>
            <li>
              <span className="text-foreground">시각:</span>{" "}
              {stream.updated_at ? new Date(stream.updated_at).toLocaleString() : "—"}
            </li>
            <li>
              <span className="text-foreground">Job:</span>{" "}
              {stream.current_job_id ? (
                <Link href={`/jobs/${stream.current_job_id}`} className="text-primary hover:underline">
                  {stream.current_job_id}
                </Link>
              ) : (
                "—"
              )}
            </li>
            <li>
              <span className="text-foreground">Worker:</span>{" "}
              {stream.worker_id ?? "—"}
            </li>
          </ul>
        </div>

        <div className="rounded border border-border bg-muted/30 p-3 text-sm">
          <p className="font-medium text-muted-foreground">운영자 행동 가이드</p>
          <ul className="mt-2 list-inside list-disc space-y-1 text-muted-foreground">
            {guideLines.map((line, i) => (
              <li key={i}>{line}</li>
            ))}
          </ul>
        </div>
      </CardContent>
    </Card>
  );
}
