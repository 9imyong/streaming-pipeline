"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import {
  type ColumnDef,
  getCoreRowModel,
  useReactTable,
  flexRender,
} from "@tanstack/react-table";
import { fetchJobs } from "@/lib/api";
import { jobsQueryOptions } from "@/lib/query/query-client";
import type { Job } from "@/lib/api/types";
import { JobStatusBadge } from "./job-status-badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

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
];

export function JobTable() {
  const { data: jobs = [], isLoading, error } = useQuery({
    ...jobsQueryOptions,
    queryFn: fetchJobs,
  });

  const table = useReactTable({
    data: jobs,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  if (error) {
    return (
      <div className="rounded-md border border-destructive/50 bg-destructive/10 p-4 text-destructive">
        Failed to load jobs: {error.message}
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12 text-muted-foreground">
        Loading jobs…
      </div>
    );
  }

  if (jobs.length === 0) {
    return (
      <div className="rounded-md border border-border p-8 text-center text-muted-foreground">
        No jobs.
      </div>
    );
  }

  return (
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
  );
}
