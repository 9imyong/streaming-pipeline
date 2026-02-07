"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  type ColumnDef,
  getCoreRowModel,
  useReactTable,
  flexRender,
} from "@tanstack/react-table";
import { fetchJobs } from "@/lib/api";
import { jobsQueryOptions } from "@/lib/query/query-client";
import type { Job, JobStatus } from "@/lib/api/types";
import { JobStatusBadge } from "./job-status-badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ErrorState } from "@/components/common/error";
import { EmptyState } from "@/components/common/empty";
import { LoadingTable } from "@/components/common/loading";

const PAGE_SIZE = 20;
const JOBS_LIST_LIMIT = 500;
const LARGE_TABLE_WARNING = 1000;
const STATUS_OPTIONS: { value: string; label: string }[] = [
  { value: "", label: "All" },
  { value: "PENDING", label: "Pending" },
  { value: "PROCESSING", label: "Processing" },
  { value: "DONE", label: "Done" },
  { value: "FAILED", label: "Failed" },
];

const columns: ColumnDef<Job>[] = [
  {
    accessorKey: "job_id",
    header: "Job ID",
    cell: ({ row }) => (
      <Link
        href={`/jobs/${row.original.job_id}`}
        className="font-medium text-primary hover:underline"
      >
        {row.original.job_id}
      </Link>
    ),
  },
  {
    accessorKey: "stream_id",
    header: "Stream ID",
    cell: ({ row }) => (
      <Link
        href={`/streams/${row.original.stream_id}`}
        className="text-primary hover:underline"
      >
        {row.original.stream_id}
      </Link>
    ),
  },
  {
    accessorKey: "type",
    header: "Type",
  },
  {
    accessorKey: "status",
    header: "Status",
    cell: ({ row }) => <JobStatusBadge status={row.original.status} />,
  },
  {
    accessorKey: "created_at",
    header: "Created",
    cell: ({ row }) => {
      const t = row.original.created_at;
      try {
        return new Date(t).toLocaleString();
      } catch {
        return t;
      }
    },
  },
  {
    accessorKey: "updated_at",
    header: "Updated",
    cell: ({ row }) => {
      const t = row.original.updated_at;
      try {
        return new Date(t).toLocaleString();
      } catch {
        return t;
      }
    },
  },
  {
    id: "duration_ms",
    header: "Duration",
    cell: ({ row }) =>
      row.original.duration_ms != null
        ? `${row.original.duration_ms} ms`
        : "—",
  },
  {
    id: "actions",
    header: "Actions",
    cell: ({ row }) => (
      <Button size="sm" variant="outline" asChild>
        <Link href={`/jobs/${row.original.job_id}`}>Detail</Link>
      </Button>
    ),
  },
];

export function JobTable({ streamId }: { streamId?: string }) {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [page, setPage] = useState(0);
  const listParams = streamId
    ? { stream_id: streamId, limit: JOBS_LIST_LIMIT }
    : { limit: JOBS_LIST_LIMIT };

  const { data: jobs = [], isLoading, error, refetch } = useQuery({
    ...jobsQueryOptions(listParams),
    queryFn: () => fetchJobs(listParams),
  });

  const filteredData = useMemo(() => {
    let list = jobs;
    if (statusFilter) {
      list = list.filter((j) => j.status === (statusFilter as JobStatus));
    }
    if (search.trim()) {
      const v = search.toLowerCase().trim();
      list = list.filter(
        (j) =>
          j.job_id.toLowerCase().includes(v) ||
          j.stream_id.toLowerCase().includes(v)
      );
    }
    return list.sort(
      (a, b) =>
        new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
    );
  }, [jobs, statusFilter, search]);

  const paginatedData = useMemo(() => {
    const start = page * PAGE_SIZE;
    return filteredData.slice(start, start + PAGE_SIZE);
  }, [filteredData, page]);

  const totalPages = Math.ceil(filteredData.length / PAGE_SIZE) || 1;

  const table = useReactTable({
    data: paginatedData,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  if (error) {
    return (
      <ErrorState
        message={`Failed to load jobs: ${error.message}`}
        onRetry={() => refetch()}
      />
    );
  }

  if (isLoading) {
    return <LoadingTable rows={5} />;
  }

  if (jobs.length === 0) {
    return (
      <EmptyState
        title="No jobs"
        description={streamId ? `No jobs for stream ${streamId}` : undefined}
      />
    );
  }

  const showLargeWarning = jobs.length >= LARGE_TABLE_WARNING;
  const showLimitNotice = jobs.length >= JOBS_LIST_LIMIT;

  return (
    <div className="space-y-4">
      {(showLargeWarning || showLimitNotice) && (
        <div className="rounded border border-amber-500/50 bg-amber-500/10 px-3 py-2 text-sm text-amber-800 dark:text-amber-200">
          {showLargeWarning
            ? `표시 제한 ${JOBS_LIST_LIMIT}건. 1,000건 이상일 수 있습니다. 필터로 범위를 좁히세요.`
            : `표시 ${jobs.length}건 (limit=${JOBS_LIST_LIMIT}). 더 보려면 필터 사용.`}
        </div>
      )}
      <div className="flex flex-wrap items-center gap-4">
        <Input
          placeholder="Search by job_id or stream_id..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(0);
          }}
          className="max-w-xs"
        />
        <Select
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            setPage(0);
          }}
          className="w-40"
        >
          {STATUS_OPTIONS.map((o) => (
            <option key={o.value || "all"} value={o.value}>
              {o.label}
            </option>
          ))}
        </Select>
      </div>
      <Table>
        <TableHeader>
          {table.getHeaderGroups().map((headerGroup) => (
            <TableRow key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <TableHead key={header.id}>
                  {header.isPlaceholder
                    ? null
                    : flexRender(
                        header.column.columnDef.header,
                        header.getContext()
                      )}
                </TableHead>
              ))}
            </TableRow>
          ))}
        </TableHeader>
        <TableBody>
          {table.getRowModel().rows.map((row) => (
            <TableRow key={row.id}>
              {row.getVisibleCells().map((cell) => (
                <TableCell key={cell.id}>
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
      {totalPages > 1 && (
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span>
            {filteredData.length} jobs (page {page + 1}/{totalPages})
          </span>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={page === 0}
              onClick={() => setPage((p) => p - 1)}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={page >= totalPages - 1}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
