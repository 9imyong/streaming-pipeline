import { DashboardSummary } from "@/components/dashboard/dashboard-summary";
import { RecentEvents } from "@/components/dashboard/recent-events";

export default function DashboardPage() {
  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold">Dashboard</h1>
      <DashboardSummary />
      <RecentEvents />
    </div>
  );
}
