"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import {
  type ColumnDef,
  getCoreRowModel,
  useReactTable,
  flexRender,
} from "@tanstack/react-table";
import { useQueryClient } from "@tanstack/react-query";
import { fetchStreams, streamStart, streamStop } from "@/lib/api";
import { streamListQueryOptions } from "@/lib/query/query-client";
import type { StreamListItem } from "@/lib/api/types";
import { StreamStatusBadge } from "./stream-status-badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

const columns: ColumnDef<StreamListItem>[] = [
  {
    accessorKey: "channel_id",
    header: "Channel ID",
    cell: ({ row }) => (
      <Link
        href={`/streams/${row.original.channel_id}`}
        className="font-medium text-primary hover:underline"
      >
        {row.original.channel_id}
      </Link>
    ),
  },
  {
    accessorKey: "status",
    header: "Status",
    cell: ({ row }) => <StreamStatusBadge status={row.original.status} />,
  },
  {
    accessorKey: "assigned_worker_id",
    header: "Worker",
    cell: ({ row }) =>
      row.original.assigned_worker_id ?? (
        <span className="text-muted-foreground">—</span>
      ),
  },
  {
    accessorKey: "last_error",
    header: "Last Error",
    cell: ({ row }) =>
      row.original.last_error ?? (
        <span className="text-muted-foreground">—</span>
      ),
  },
  {
    accessorKey: "updated_at",
    header: "Updated",
    cell: ({ row }) => {
      const t = row.original.updated_at;
      if (!t) return "—";
      try {
        return new Date(t).toLocaleString();
      } catch {
        return t;
      }
    },
  },
  {
    id: "actions",
    header: "Actions",
    cell: ({ row }) => <StreamRowActions row={row.original} />,
  },
];

function StreamRowActions({ row }: { row: StreamListItem }) {
  const queryClient = useQueryClient();
  const isRunning = row.status === "RUNNING";
  const isStopped = row.status === "STOPPED" || row.status === "CREATED";

  async function handleStart() {
    try {
      await streamStart({
        channel_id: row.channel_id,
        source_rtsp: "rtsp://example/stream",
        output: "hls",
      });
      await queryClient.invalidateQueries({ queryKey: ["streams"] });
    } catch (e) {
      console.error(e);
    }
  }

  async function handleStop() {
    try {
      await streamStop(row.channel_id);
      await queryClient.invalidateQueries({ queryKey: ["streams"] });
    } catch (e) {
      console.error(e);
    }
  }

  return (
    <div className="flex gap-2">
      {isStopped && (
        <Button size="sm" variant="default" onClick={handleStart}>
          Start
        </Button>
      )}
      {isRunning && (
        <Button size="sm" variant="destructive" onClick={handleStop}>
          Stop
        </Button>
      )}
    </div>
  );
}

export function StreamTable() {
  const { data: streams = [], isLoading, error } = useQuery({
    ...streamListQueryOptions,
    queryFn: fetchStreams,
  });

  const table = useReactTable({
    data: streams,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  if (error) {
    return (
      <div className="rounded-md border border-destructive/50 bg-destructive/10 p-4 text-destructive">
        Failed to load streams: {error.message}
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12 text-muted-foreground">
        Loading streams…
      </div>
    );
  }

  if (streams.length === 0) {
    return (
      <div className="rounded-md border border-border p-8 text-center text-muted-foreground">
        No streams. Start one via API or mock.
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
