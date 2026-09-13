"use client";

import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { JobTable } from "@/components/jobs/job-table";

export default function JobsPage() {
  const searchParams = useSearchParams();
  const streamId = searchParams.get("stream_id") ?? undefined;

  return (
    <div>
      <h1 className="text-2xl font-bold">Jobs</h1>
      <p className="mt-1 text-muted-foreground">
        {streamId ? (
          <>
            Filtered by stream:{" "}
            <Link
              href={`/streams/${streamId}`}
              className="text-primary hover:underline"
            >
              {streamId}
            </Link>
            {" · "}
            <Link href="/jobs" className="text-muted-foreground hover:underline">
              Clear filter
            </Link>
          </>
        ) : (
          "잡 목록"
        )}
      </p>
      <div className="mt-6">
        <JobTable streamId={streamId} />
      </div>
    </div>
  );
}
