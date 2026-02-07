"use client";

import { useState } from "react";

/**
 * Events 페이지. 현재는 폴링/SSE 미구현 상태.
 * 백엔드에 GET /v1/events/stream (SSE) 또는 폴링용 엔드포인트 추가 시 연동.
 */
export default function EventsPage() {
  const [channelFilter, setChannelFilter] = useState("");
  const [autoScroll, setAutoScroll] = useState(true);

  return (
    <main className="p-6">
      <h1 className="text-2xl font-bold mb-4">Events</h1>
      <div className="flex gap-4 items-center mb-4">
        <label className="flex items-center gap-2">
          <span className="text-gray-400">Channel filter</span>
          <input
            type="text"
            value={channelFilter}
            onChange={(e) => setChannelFilter(e.target.value)}
            placeholder="e.g. ch1"
            className="bg-gray-800 border border-gray-600 rounded px-2 py-1 text-sm w-32"
          />
        </label>
        <label className="flex items-center gap-2 text-gray-400">
          <input
            type="checkbox"
            checked={autoScroll}
            onChange={(e) => setAutoScroll(e.target.checked)}
          />
          Auto-scroll
        </label>
      </div>
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-4 min-h-[300px] font-mono text-sm text-gray-300">
        <p className="text-gray-500">
          실시간 이벤트는 SSE 엔드포인트 연동 후 표시됩니다.
          <br />
          (예: GET /v1/events/stream → text/event-stream, stream.events 구독)
        </p>
      </div>
    </main>
  );
}
