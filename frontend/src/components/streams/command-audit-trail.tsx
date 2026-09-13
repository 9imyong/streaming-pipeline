"use client";

import { useMemo } from "react";
import type { StreamEvent } from "@/lib/api/types";

const COMMAND_SENT = "COMMAND_SENT";

export interface CommandAuditTrailProps {
  events: StreamEvent[];
  limit?: number;
  className?: string;
}

export function CommandAuditTrail({
  events,
  limit = 20,
  className = "",
}: CommandAuditTrailProps) {
  const commandEvents = useMemo(
    () =>
      events
        .filter((e) => e.type === COMMAND_SENT)
        .sort((a, b) => new Date(b.ts).getTime() - new Date(a.ts).getTime())
        .slice(0, limit),
    [events, limit]
  );

  if (commandEvents.length === 0) {
    return (
      <div
        className={`rounded border border-dashed p-4 text-center text-sm text-muted-foreground ${className}`}
      >
        COMMAND_SENT 이벤트 없음
      </div>
    );
  }

  return (
    <ul className={`space-y-2 text-sm ${className}`}>
      {commandEvents.map((ev, i) => (
        <li
          key={`${ev.ts}-${i}`}
          className="flex flex-wrap items-baseline gap-x-2 gap-y-1 rounded border border-border bg-muted/30 px-3 py-2"
        >
          <span className="text-muted-foreground">
            {new Date(ev.ts).toLocaleString()}
          </span>
          <span className="font-medium">{ev.stream_id ?? "—"}</span>
          <span className="text-muted-foreground">{ev.message}</span>
          {ev.entity?.job_id && (
            <span className="text-xs text-muted-foreground">
              job: {ev.entity.job_id}
            </span>
          )}
          {ev.entity?.worker_id && (
            <span className="text-xs text-muted-foreground">
              worker: {ev.entity.worker_id}
            </span>
          )}
        </li>
      ))}
    </ul>
  );
}
