"use client";

import { useMemo } from "react";
import type { StreamEvent } from "@/lib/api/types";

const STATE_CHANGED = "STATE_CHANGED";

function sortByTime(events: StreamEvent[]): StreamEvent[] {
  return [...events].sort(
    (a, b) => new Date(a.ts).getTime() - new Date(b.ts).getTime()
  );
}

export interface StreamStateTimelineProps {
  events: StreamEvent[];
  className?: string;
}

export function StreamStateTimeline({ events, className = "" }: StreamStateTimelineProps) {
  const stateEvents = useMemo(
    () => sortByTime(events.filter((e) => e.type === STATE_CHANGED)),
    [events]
  );

  if (stateEvents.length === 0) {
    return (
      <div className={`rounded border border-dashed p-4 text-center text-sm text-muted-foreground ${className}`}>
        STATE_CHANGED 이벤트 없음
      </div>
    );
  }

  return (
    <div className={`space-y-0 ${className}`}>
      {stateEvents.map((ev, i) => {
        const payload = ev.payload as { from?: string; to?: string } | undefined;
        const to = payload?.to ?? "—";
        const from = payload?.from;
        return (
          <div key={`${ev.ts}-${i}`} className="flex gap-3">
            <div className="flex flex-col items-center">
              <div className="h-3 w-3 shrink-0 rounded-full border-2 border-primary bg-background" />
              {i < stateEvents.length - 1 && (
                <div className="w-px flex-1 bg-border" style={{ minHeight: 24 }} />
              )}
            </div>
            <div className="pb-4 text-sm">
              <p className="font-medium">
                {from != null ? `${from} → ${to}` : to}
              </p>
              <p className="text-xs text-muted-foreground">
                {new Date(ev.ts).toLocaleString()} · {ev.type}
              </p>
              {ev.message && (
                <p className="mt-0.5 text-muted-foreground">{ev.message}</p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
