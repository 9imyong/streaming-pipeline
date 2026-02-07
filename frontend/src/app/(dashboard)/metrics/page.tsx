import { DashboardSummary } from "@/components/dashboard/dashboard-summary";

export default function MetricsPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold">Metrics</h1>
      <p className="mt-1 text-muted-foreground">메트릭 요약</p>
      <div className="mt-6">
        <DashboardSummary />
      </div>
    </div>
  );
}
