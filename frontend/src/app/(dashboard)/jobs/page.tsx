import { JobTable } from "@/components/jobs/job-table";

export default function JobsPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold">Jobs</h1>
      <p className="mt-1 text-muted-foreground">잡 목록</p>
      <div className="mt-6">
        <JobTable />
      </div>
    </div>
  );
}
