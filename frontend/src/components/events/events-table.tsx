"use client";

import { useQuery } from "@tanstack/react-query";
import {
  type ColumnDef,
  getCoreRowModel,
  useReactTable,
  flexRender,
} from "@tanstack/react-table";
import { fetchEvents } from "@/lib/api";
import { eventsQueryOptions } from "@/lib/query/query-client";
import type { StreamEvent } from "@/lib/api/types";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

const columns: ColumnDef<StreamEvent>[] = [
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
  { accessorKey: "level", header: "Level" },
  { accessorKey: "stream_id", header: "Stream ID", cell: ({ row }) => row.original.stream_id ?? "—" },
  { accessorKey: "type", header: "Type" },
  { accessorKey: "message", header: "Message" },
];

export function EventsTable({ streamId, limit = 50 }: { streamId?: string; limit?: number }) {
  const params = streamId ? { stream_id: streamId, limit } : { limit };
  const { data: events = [], isLoading, error } = useQuery({
    ...eventsQueryOptions(params),
    queryFn: () => fetchEvents(params),
  });

  const table = useReactTable({
    data: events,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  if (error) {
    return (
      <div className="rounded-md border border-destructive/50 bg-destructive/10 p-4 text-destructive">
        Failed to load events: {error.message}
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12 text-muted-foreground">
        Loading events…
      </div>
    );
  }

  if (events.length === 0) {
    return (
      <div className="rounded-md border border-border p-8 text-center text-muted-foreground">
        No events.
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
