"use client";

import { EventsTable } from "@/components/events/events-table";

export function RecentEvents() {
  return (
    <div>
      <h2 className="mb-4 text-lg font-semibold">Recent events</h2>
      <EventsTable limit={20} />
    </div>
  );
}
