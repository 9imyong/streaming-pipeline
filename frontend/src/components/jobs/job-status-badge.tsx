"use client";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { JobStatus } from "@/lib/api/types";

const variantMap: Record<
  JobStatus,
  "default" | "secondary" | "destructive" | "outline" | "success" | "warning"
> = {
  PENDING: "secondary",
  PROCESSING: "default",
  DONE: "success",
  FAILED: "destructive",
};

export function JobStatusBadge({
  status,
  className,
}: {
  status: JobStatus;
  className?: string;
}) {
  return (
    <Badge variant={variantMap[status] ?? "outline"} className={cn("capitalize", className)}>
      {status}
    </Badge>
  );
}
