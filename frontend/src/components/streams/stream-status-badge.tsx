"use client";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { StreamStatus } from "@/lib/api/types";

const variantMap: Record<
  StreamStatus,
  "default" | "secondary" | "destructive" | "outline" | "success" | "warning"
> = {
  CREATED: "secondary",
  ASSIGNED: "default",
  RUNNING: "success",
  FAILED: "destructive",
  STOPPED: "outline",
};

export function StreamStatusBadge({
  status,
  className,
}: {
  status: StreamStatus;
  className?: string;
}) {
  return (
    <Badge variant={variantMap[status] ?? "outline"} className={cn("capitalize", className)}>
      {status}
    </Badge>
  );
}
