"use client";

import { useQuery } from "@tanstack/react-query";
import {
  type ColumnDef,
  getCoreRowModel,
  useReactTable,
  flexRender,
} from "@tanstack/react-table";
import { fetchWorkers } from "@/lib/api";
import { workersQueryOptions } from "@/lib/query/query-client";
import type { Worker } from "@/lib/api/types";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

const workerStatusVariant: Record<string, "default" | "secondary" | "destructive" | "success" | "outline"> = {
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
      <Badge variant={workerStatusVariant[row.original.status] ?? "outline"} className="capitalize">
        {row.original.status}
      </Badge>
    ),
  },
  {
    accessorKey: "current_streams",
    header: "Streams",
    cell: ({ row }) => row.original.current_streams ?? "—",
  },
  {
    accessorKey: "gpu_usage",
    header: "GPU %",
    cell: ({ row }) =>
      row.original.gpu_usage != null ? `${row.original.gpu_usage}%` : "—",
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
  const { data: workers = [], isLoading, error } = useQuery({
    ...workersQueryOptions,
    queryFn: fetchWorkers,
  });

  const table = useReactTable({
    data: workers,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  if (error) {
    return (
      <div className="rounded-md border border-destructive/50 bg-destructive/10 p-4 text-destructive">
        Failed to load workers: {error.message}
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12 text-muted-foreground">
        Loading workers…
      </div>
    );
  }

  if (workers.length === 0) {
    return (
      <div className="rounded-md border border-border p-8 text-center text-muted-foreground">
        No workers.
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
