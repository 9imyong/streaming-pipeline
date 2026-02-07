"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  type ColumnDef,
  getCoreRowModel,
  useReactTable,
  flexRender,
} from "@tanstack/react-table";
import { fetchWorkers } from "@/lib/api";
import { workersQueryOptions } from "@/lib/query/query-client";
import type { Worker, WorkerStatus } from "@/lib/api/types";
import { Badge } from "@/components/ui/badge";
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

const STATUS_OPTIONS: { value: string; label: string }[] = [
  { value: "", label: "All" },
  { value: "IDLE", label: "Idle" },
  { value: "BUSY", label: "Busy" },
  { value: "DOWN", label: "Down" },
];

const workerStatusVariant: Record<
  string,
  "default" | "secondary" | "destructive" | "success" | "outline"
> = {
  IDLE: "secondary",
  BUSY: "success",
  DOWN: "destructive",
};

const columns: ColumnDef<Worker>[] = [
  { accessorKey: "worker_id", header: "Worker ID" },
  {
    accessorKey: "status",
    header: "Status",
    cell: ({ row }) => (
      <Badge
        variant={workerStatusVariant[row.original.status] ?? "outline"}
        className="capitalize"
      >
        {row.original.status}
      </Badge>
    ),
  },
  {
    id: "current_streams_count",
    header: "Streams",
    cell: ({ row }) =>
      row.original.current_streams_count ?? row.original.current_streams ?? "—",
  },
  {
    id: "gpu",
    header: "GPU",
    cell: ({ row }) => {
      const g = row.original.gpu;
      if (!g) return row.original.gpu_usage != null ? `${row.original.gpu_usage}%` : "—";
      const parts = [];
      if (g.name) parts.push(g.name);
      if (g.util != null) parts.push(`${g.util}%`);
      if (g.mem_used != null) parts.push(`${g.mem_used}MB`);
      return parts.length ? parts.join(" / ") : "—";
    },
  },
  {
    accessorKey: "last_seen",
    header: "Last seen",
    cell: ({ row }) => {
      const t = row.original.last_seen;
      if (!t) return "—";
      try {
        return new Date(t).toLocaleString();
      } catch {
        return t;
      }
    },
  },
];

export function WorkerTable() {
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [downOnly, setDownOnly] = useState(false);

  const { data: workers = [], isLoading, error, refetch } = useQuery({
    ...workersQueryOptions,
    queryFn: fetchWorkers,
  });

  const filteredData = useMemo(() => {
    let list = workers;
    if (statusFilter) {
      list = list.filter((w) => w.status === (statusFilter as WorkerStatus));
    }
    if (downOnly) {
      list = list.filter((w) => w.status === "DOWN");
    }
    return list;
  }, [workers, statusFilter, downOnly]);

  const table = useReactTable({
    data: filteredData,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  if (error) {
    return (
      <ErrorState
        message={`Failed to load workers: ${error.message}`}
        onRetry={() => refetch()}
      />
    );
  }

  if (isLoading) {
    return <LoadingTable rows={5} />;
  }

  if (workers.length === 0) {
    return <EmptyState title="No workers" />;
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-4">
        <Select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="w-40"
        >
          {STATUS_OPTIONS.map((o) => (
            <option key={o.value || "all"} value={o.value}>
              {o.label}
            </option>
          ))}
        </Select>
        <label className="flex cursor-pointer items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={downOnly}
            onChange={(e) => setDownOnly(e.target.checked)}
            className="rounded border-input"
          />
          DOWN only
        </label>
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
      {filteredData.length === 0 && workers.length > 0 && (
        <p className="text-sm text-muted-foreground">No workers match the filter.</p>
      )}
    </div>
  );
}
