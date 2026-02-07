"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchMetricsSummary } from "@/lib/api";
import { metricsSummaryQueryOptions } from "@/lib/query/query-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function DashboardSummary() {
  const { data, isLoading, error } = useQuery({
    ...metricsSummaryQueryOptions,
    queryFn: fetchMetricsSummary,
  });

  if (error) {
    return (
      <div className="rounded-md border border-destructive/50 bg-destructive/10 p-4 text-destructive">
        Failed to load metrics: {error.message}
      </div>
    );
  }

  if (isLoading || !data) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i}>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                —
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-8 w-12 animate-pulse rounded bg-muted" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  const cards = [
    {
      title: "RUNNING streams",
      value: data.running_streams,
    },
    {
      title: "FAILED streams",
      value: data.failed_streams,
    },
    {
      title: "Queued jobs",
      value: data.queued_jobs,
    },
    {
      title: "Active workers",
      value: data.active_workers,
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {cards.map((c) => (
        <Card key={c.title}>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {c.title}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <span className="text-2xl font-bold">{c.value}</span>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
