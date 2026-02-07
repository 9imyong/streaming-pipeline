import { StreamTable } from "@/components/streams/stream-table";

export default function StreamsPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold">Streams</h1>
      <p className="mt-1 text-muted-foreground">
        스트림 목록 (폴링 {process.env.NEXT_PUBLIC_POLL_INTERVAL_MS ?? 2000}ms)
      </p>
      <div className="mt-6">
        <StreamTable />
      </div>
    </div>
  );
}
