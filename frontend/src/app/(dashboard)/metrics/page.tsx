import { MetricsSummaryCards } from "@/components/metrics/metrics-summary-cards";

export default function MetricsPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold">Metrics</h1>
      <p className="mt-1 text-muted-foreground">
        운영 요약 — active_streams, jobs_rate, p95_latency, error_rate
      </p>
      <div className="mt-6">
        <MetricsSummaryCards />
      </div>
    </div>
  );
}
