"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  type ColumnDef,
  getCoreRowModel,
  useReactTable,
  flexRender,
} from "@tanstack/react-table";
import { toast } from "sonner";
import { fetchStreams, streamStart, streamStop } from "@/lib/api";
import { streamListQueryOptions } from "@/lib/query/query-client";
import type { StreamListItem, StreamStatus } from "@/lib/api/types";
import { StreamStatusBadge } from "./stream-status-badge";
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

const STATUS_OPTIONS: { value: string; label: string }[] = [
  { value: "", label: "All" },
  { value: "CREATED", label: "Created" },
  { value: "ASSIGNED", label: "Assigned" },
  { value: "RUNNING", label: "Running" },
  { value: "FAILED", label: "Failed" },
  { value: "STOPPED", label: "Stopped" },
];

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
      toast.success(`Stream ${row.channel_id} start requested`);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Start failed";
      toast.error(msg);
    }
  }

  async function handleStop() {
    try {
      await streamStop(row.channel_id);
      await queryClient.invalidateQueries({ queryKey: ["streams"] });
      toast.success(`Stream ${row.channel_id} stop requested`);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Stop failed";
      toast.error(msg);
    }
  }

  return (
    <div className="flex gap-2">
      <Button size="sm" variant="outline" asChild>
        <Link href={`/streams/${row.channel_id}`}>Detail</Link>
      </Button>
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
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("");

  const { data: streams = [], isLoading, error, refetch } = useQuery({
    ...streamListQueryOptions,
    queryFn: fetchStreams,
  });

  const filteredData = useMemo(() => {
    let list = streams;
    if (statusFilter) {
      list = list.filter((s) => s.status === statusFilter);
    }
    if (search.trim()) {
      const v = search.toLowerCase().trim();
      list = list.filter(
        (s) =>
          s.channel_id.toLowerCase().includes(v) ||
          (s.assigned_worker_id ?? "").toLowerCase().includes(v)
      );
    }
    return [...list].sort((a, b) => {
      const ta = a.updated_at ? new Date(a.updated_at).getTime() : 0;
      const tb = b.updated_at ? new Date(b.updated_at).getTime() : 0;
      return tb - ta;
    });
  }, [streams, statusFilter, search]);

  const table = useReactTable({
    data: filteredData,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  if (error) {
    return (
      <ErrorState
        message={`Failed to load streams: ${error.message}`}
        onRetry={() => refetch()}
      />
    );
  }

  if (isLoading) {
    return <LoadingTable rows={5} />;
  }

  if (streams.length === 0) {
    return (
      <EmptyState
        title="No streams"
        description="Start one via API or use mock mode."
      />
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-4">
        <Input
          placeholder="Search by channel ID or worker..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="max-w-xs"
        />
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
    </div>
  );
}
