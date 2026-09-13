"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { JobTable } from "@/components/jobs/job-table";

// useSearchParams 는 클라이언트에서만 값이 정해져, Suspense 경계가 없으면
// 정적 프리렌더 단계에서 빌드가 실패한다.
function JobsFilter() {
  const searchParams = useSearchParams();
  const streamId = searchParams.get("stream_id") ?? undefined;

  return (
    <>
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
    </>
  );
}

export default function JobsPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold">Jobs</h1>
      <Suspense
        fallback={<p className="mt-1 text-muted-foreground">잡 목록</p>}
      >
        <JobsFilter />
      </Suspense>
    </div>
  );
}
