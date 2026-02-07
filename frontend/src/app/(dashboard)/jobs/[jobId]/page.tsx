"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { fetchJob } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { JobStatusBadge } from "@/components/jobs/job-status-badge";

export default function JobDetailPage() {
  const params = useParams();
  const jobId = String(params?.jobId ?? "");
  const { data: job, isLoading, error } = useQuery({
    queryKey: ["jobs", jobId],
    queryFn: () => fetchJob(jobId),
  });

  if (error) {
    return (
      <div className="text-destructive">
        Failed to load job: {error.message}
        <Link href="/jobs" className="ml-2 text-primary hover:underline">← Jobs</Link>
      </div>
    );
  }

  if (isLoading || !job) {
    return (
      <div className="text-muted-foreground">
        {isLoading ? "Loading…" : "Job not found."}
        <Link href="/jobs" className="ml-2 text-primary hover:underline">← Jobs</Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <Link href="/jobs" className="text-sm text-muted-foreground hover:text-foreground">← Jobs</Link>
        <h1 className="mt-1 text-2xl font-bold">{job.job_id}</h1>
        <JobStatusBadge status={job.status} className="mt-2" />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <p><span className="text-muted-foreground">Stream:</span>{" "}
            <Link href={`/streams/${job.stream_id}`} className="text-primary hover:underline">{job.stream_id}</Link>
          </p>
          <p><span className="text-muted-foreground">Type:</span> {job.type}</p>
          <p><span className="text-muted-foreground">Created:</span> {new Date(job.created_at).toLocaleString()}</p>
          <p><span className="text-muted-foreground">Updated:</span> {new Date(job.updated_at).toLocaleString()}</p>
          {job.failure_reason && (
            <p className="text-destructive">Failure: {job.failure_reason}</p>
          )}
          {job.payload != null && (
            <pre className="mt-2 overflow-auto rounded bg-muted p-2 text-xs">
              {JSON.stringify(job.payload, null, 2)}
            </pre>
          )}
          {job.result != null && (
            <pre className="mt-2 overflow-auto rounded bg-muted p-2 text-xs">
              {JSON.stringify(job.result, null, 2)}
            </pre>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
