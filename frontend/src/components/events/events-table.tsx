"use client";

import { useState, useMemo } from "react";
import {
  type ColumnDef,
  getCoreRowModel,
  useReactTable,
  flexRender,
} from "@tanstack/react-table";
import { AlertCircle } from "lucide-react";
import { useEventsRealtime } from "@/lib/realtime/use-events-realtime";
import type { StreamEvent } from "@/lib/api/types";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
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

const LEVEL_OPTIONS: { value: string; label: string }[] = [
  { value: "", label: "All" },
  { value: "INFO", label: "Info" },
  { value: "WARN", label: "Warn" },
  { value: "ERROR", label: "Error" },
];

const DEFAULT_LIMIT = 200;

export function EventsTable({
  streamId: initialStreamId,
  limit = DEFAULT_LIMIT,
  embed = false,
}: {
  streamId?: string;
  limit?: number;
  embed?: boolean;
}) {
  const [streamIdFilter, setStreamIdFilter] = useState(initialStreamId ?? "");
  const [levelFilter, setLevelFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [selectedEvent, setSelectedEvent] = useState<StreamEvent | null>(null);

  const {
    events,
    status,
    isLoading,
    error,
    refetch,
  } = useEventsRealtime({
    stream_id: streamIdFilter.trim() || undefined,
    limit,
    level: levelFilter || undefined,
    type: typeFilter.trim() || undefined,
    useSse: true,
    toastOnLevel: true,
  });

  const filteredData = useMemo(() => {
    let list = events;
    if (levelFilter) {
      list = list.filter((e) => e.level === levelFilter);
    }
    if (typeFilter.trim()) {
      const t = typeFilter.toLowerCase().trim();
      list = list.filter((e) => e.type.toLowerCase().includes(t));
    }
    return list;
  }, [events, levelFilter, typeFilter]);

  const table = useReactTable({
    data: filteredData,
    columns: [
      {
        accessorKey: "ts",
        header: "Time",
        cell: ({ row }) => {
          const t = row.original.ts;
          try {
            return new Date(t).toLocaleString();
          } catch {
            return t;
          }
        },
      },
      {
        accessorKey: "level",
        header: "Level",
        cell: ({ row }) => {
          const level = row.original.level;
          const isError = level === "ERROR";
          return (
            <Badge
              variant={isError ? "destructive" : "secondary"}
              className={isError ? "gap-1" : ""}
            >
              {isError && <AlertCircle className="h-3 w-3" />}
              {level}
            </Badge>
          );
        },
      },
      {
        accessorKey: "stream_id",
        header: "Stream ID",
        cell: ({ row }) => row.original.stream_id ?? "—",
      },
      {
        id: "entity",
        header: "Entity",
        cell: ({ row }) => {
          const e = row.original.entity;
          if (!e) return "—";
          const parts = [];
          if (e.job_id) parts.push(`job:${e.job_id}`);
          if (e.worker_id) parts.push(`worker:${e.worker_id}`);
          return parts.length ? parts.join(", ") : "—";
        },
      },
      { accessorKey: "type", header: "Type" },
      { accessorKey: "message", header: "Message" },
    ],
    getCoreRowModel: getCoreRowModel(),
  });

  if (error) {
    return (
      <ErrorState
        message={`Failed to load events: ${error.message}`}
        onRetry={() => void refetch()}
      />
    );
  }

  if (isLoading) {
    return <LoadingTable rows={5} />;
  }

  if (events.length === 0) {
    return (
      <EmptyState
        title="No events"
        description="Events will appear when the backend is connected."
      />
    );
  }

  return (
    <div className="space-y-4">
      {!embed && (
        <div className="flex flex-wrap items-center gap-4">
          <Input
            placeholder="Stream ID filter"
            value={streamIdFilter}
            onChange={(e) => setStreamIdFilter(e.target.value)}
            className="max-w-xs"
          />
          <Select
            value={levelFilter}
            onChange={(e) => setLevelFilter(e.target.value)}
            className="w-32"
          >
            {LEVEL_OPTIONS.map((o) => (
              <option key={o.value || "all"} value={o.value}>
                {o.label}
              </option>
            ))}
          </Select>
          <Input
            placeholder="Type filter"
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="max-w-xs"
          />
          <Badge
            variant={
              status === "connected"
                ? "default"
                : status === "reconnecting"
                  ? "secondary"
                  : "outline"
            }
            className="shrink-0"
          >
            {status === "connected"
              ? "CONNECTED"
              : status === "reconnecting"
                ? "RECONNECTING"
                : status === "offline" || status === "polling"
                  ? "OFFLINE"
                  : "—"}
          </Badge>
          <span className="text-sm text-muted-foreground">
            Limit: {limit} · {filteredData.length} shown
          </span>
        </div>
      )}
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
            <TableRow
              key={row.id}
              className="cursor-pointer hover:bg-muted/50"
              onClick={() => setSelectedEvent(row.original)}
            >
              {row.getVisibleCells().map((cell) => (
                <TableCell key={cell.id}>
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <Dialog
        open={!!selectedEvent}
        onOpenChange={(open) => !open && setSelectedEvent(null)}
      >
        <DialogContent className="max-h-[80vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle>Event payload</DialogTitle>
          </DialogHeader>
          {selectedEvent && (
            <pre className="flex-1 overflow-auto rounded bg-muted p-4 text-xs">
              {JSON.stringify(
                {
                  ts: selectedEvent.ts,
                  level: selectedEvent.level,
                  stream_id: selectedEvent.stream_id,
                  entity: selectedEvent.entity,
                  type: selectedEvent.type,
                  message: selectedEvent.message,
                  request_id: selectedEvent.request_id,
                  payload: selectedEvent.payload,
                },
                null,
                2
              )}
            </pre>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
