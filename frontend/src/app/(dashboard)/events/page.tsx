import { EventsTable } from "@/components/events/events-table";

export default function EventsPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold">Events</h1>
      <p className="mt-1 text-muted-foreground">이벤트 로그 (stream_id 필터는 추후 추가)</p>
      <div className="mt-6">
        <EventsTable limit={100} />
      </div>
    </div>
  );
}
