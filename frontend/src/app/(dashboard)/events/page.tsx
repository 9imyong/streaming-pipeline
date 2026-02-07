import { EventsTable } from "@/components/events/events-table";

export default function EventsPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold">Events</h1>
      <p className="mt-1 text-muted-foreground">
        이벤트 로그 — stream_id / level / type 필터, row 클릭 시 payload 모달
      </p>
      <div className="mt-6">
        <EventsTable limit={200} />
      </div>
    </div>
  );
}
