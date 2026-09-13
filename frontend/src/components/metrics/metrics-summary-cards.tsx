"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchMetricsSummary } from "@/lib/api";
import { metricsSummaryQueryOptions } from "@/lib/query/query-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState } from "@/components/common/error";
import { LoadingTable } from "@/components/common/loading";

export function MetricsSummaryCards() {
  const { data, isLoading, error, refetch } = useQuery({
    ...metricsSummaryQueryOptions,
    queryFn: fetchMetricsSummary,
  });

  if (error) {
    return (
      <ErrorState
        message={`Failed to load metrics: ${error.message}`}
        onRetry={() => refetch()}
      />
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
              <div className="h-8 w-16 animate-pulse rounded bg-muted" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  const activeStreams =
    data.active_streams ?? data.running_streams ?? 0;
  const jobsRate = data.jobs_rate ?? null;
  const p95Latency = data.p95_latency_ms ?? null;
  const errorRate = data.error_rate ?? null;

  const cards = [
    {
      title: "Active streams",
      value: String(activeStreams),
    },
    {
      title: "Jobs rate (per min)",
      value: jobsRate != null ? String(jobsRate) : "—",
    },
    {
      title: "p95 latency (ms)",
      value: p95Latency != null ? String(p95Latency) : "—",
    },
    {
      title: "Error rate",
      value: errorRate != null ? `${(errorRate * 100).toFixed(2)}%` : "—",
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
