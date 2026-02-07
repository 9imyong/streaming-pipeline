import { WorkerTable } from "@/components/workers/worker-table";

export default function WorkersPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold">Workers</h1>
      <p className="mt-1 text-muted-foreground">워커 상태</p>
      <div className="mt-6">
        <WorkerTable />
      </div>
    </div>
  );
}
