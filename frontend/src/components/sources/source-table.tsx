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
import { Loader2 } from "lucide-react";
import {
  fetchSources,
  updateSource,
  createStreamFromSource,
} from "@/lib/api";
import { ApiError } from "@/lib/api/client";
import { sourcesQueryOptions } from "@/lib/query/query-client";
import { getRole, canRunStreamCommands } from "@/lib/storage/settings";
import type { Source } from "@/lib/api/types";
import { Badge } from "@/components/ui/badge";
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

function maskUrl(url: string): string {
  try {
    const u = new URL(url);
    const last = u.pathname.split("/").pop() || "***";
    return `${u.protocol}//${u.host}/.../${last}`;
  } catch {
    return "***";
  }
}

const ENABLED_OPTIONS: { value: string; label: string }[] = [
  { value: "", label: "All" },
  { value: "true", label: "Enabled" },
  { value: "false", label: "Disabled" },
];

const columns: ColumnDef<Source>[] = [
  { accessorKey: "source_id", header: "Source ID" },
  { accessorKey: "name", header: "Name" },
  {
    accessorKey: "rtsp_url",
    header: "RTSP URL",
    cell: ({ row, table }) => {
      const meta = table.options.meta as { maskUrls?: boolean };
      const url = row.original.rtsp_url;
      return (
        <code className="text-xs">
          {meta?.maskUrls ? maskUrl(url) : url}
        </code>
      );
    },
  },
  {
    accessorKey: "enabled",
    header: "Enabled",
    cell: ({ row }) => (
      <Badge variant={row.original.enabled ? "default" : "secondary"}>
        {row.original.enabled ? "Enabled" : "Disabled"}
      </Badge>
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
    cell: ({ row }) => <SourceRowActions row={row.original} />,
  },
];

function SourceRowActions({ row }: { row: Source }) {
  const queryClient = useQueryClient();
  const [loading, setLoading] = useState<"toggle" | "stream" | null>(null);
  const canRun = canRunStreamCommands(getRole());

  async function handleToggle() {
    setLoading("toggle");
    try {
      await updateSource(row.source_id, { enabled: !row.enabled });
      await queryClient.invalidateQueries({ queryKey: ["sources"] });
      toast.success(row.enabled ? "Source disabled" : "Source enabled");
    } catch (e) {
      toast.error(e instanceof ApiError ? e.message : "Failed");
    } finally {
      setLoading(null);
    }
  }

  async function handleCreateStream() {
    setLoading("stream");
    try {
      const res = await createStreamFromSource(row.source_id, {
        mode: "start",
      });
      await queryClient.invalidateQueries({ queryKey: ["streams"] });
      toast.success(
        res.stream_id
          ? `Stream ${res.stream_id} created/started`
          : "Command accepted"
      );
      if (res.stream_id) {
        window.location.href = `/streams/${res.stream_id}`;
      }
    } catch (e) {
      toast.error(e instanceof ApiError ? e.message : "Failed");
    } finally {
      setLoading(null);
    }
  }

  return (
    <div className="flex gap-2">
      <Button size="sm" variant="outline" asChild>
        <Link href={`/sources/${row.source_id}`}>Detail</Link>
      </Button>
      <Button
        size="sm"
        variant="secondary"
        onClick={handleToggle}
        disabled={loading !== null}
        title={row.enabled ? "Disable source" : "Enable source"}
      >
        {loading === "toggle" ? (
          <Loader2 className="h-3 w-3 animate-spin" />
        ) : row.enabled ? (
          "Disable"
        ) : (
          "Enable"
        )}
      </Button>
      {canRun && (
        <Button
          size="sm"
          variant="default"
          onClick={handleCreateStream}
          disabled={loading !== null || !row.enabled}
          title="Create and start stream from this source"
        >
          {loading === "stream" ? (
            <Loader2 className="h-3 w-3 animate-spin" />
          ) : (
            "Create Stream"
          )}
        </Button>
      )}
    </div>
  );
}

export function SourceTable() {
  const [search, setSearch] = useState("");
  const [enabledFilter, setEnabledFilter] = useState<string>("");
  const [maskUrls, setMaskUrls] = useState(true);

  const params = useMemo(
    () => ({
      q: search.trim() || undefined,
      enabled:
        enabledFilter === ""
          ? undefined
          : enabledFilter === "true",
      limit: 100,
    }),
    [search, enabledFilter]
  );

  const { data: sources = [], isLoading, error, refetch } = useQuery({
    ...sourcesQueryOptions(params),
    queryFn: () => fetchSources(params),
  });

  const table = useReactTable({
    data: sources,
    columns,
    getCoreRowModel: getCoreRowModel(),
    meta: { maskUrls },
  });

  if (error) {
    return (
      <ErrorState
        message={`Failed to load sources: ${error.message}`}
        onRetry={() => void refetch()}
      />
    );
  }

  if (isLoading) {
    return <LoadingTable rows={5} />;
  }

  if (sources.length === 0) {
    return (
      <EmptyState
        title="No sources"
        description="Add a source with + Add or use mock mode."
      />
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-4">
        <Input
          placeholder="Search by name or URL (q)..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="max-w-xs"
        />
        <Select
          value={enabledFilter}
          onChange={(e) => setEnabledFilter(e.target.value)}
          className="w-32"
        >
          {ENABLED_OPTIONS.map((o) => (
            <option key={o.value || "all"} value={o.value}>
              {o.label}
            </option>
          ))}
        </Select>
        <label className="flex items-center gap-2 text-sm text-muted-foreground">
          <input
            type="checkbox"
            checked={maskUrls}
            onChange={(e) => setMaskUrls(e.target.checked)}
          />
          Mask URLs
        </label>
      </div>
      <Table>
        <TableHeader>
          {table.getHeaderGroups().map((hg) => (
            <TableRow key={hg.id}>
              {hg.headers.map((h) => (
                <TableHead key={h.id}>
                  {h.isPlaceholder
                    ? null
                    : flexRender(h.column.columnDef.header, h.getContext())}
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
