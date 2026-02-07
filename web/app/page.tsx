export default function HomePage() {
  return (
    <main className="p-6 max-w-2xl">
      <h1 className="text-2xl font-bold mb-4">Streaming Pipeline Ops</h1>
      <p className="text-gray-400 mb-6">
        채널 관리 및 HLS 재생은 <a href="/channels" className="text-blue-400 hover:underline">/channels</a>에서,
        실시간 이벤트 로그는 <a href="/events" className="text-blue-400 hover:underline">/events</a>에서 확인하세요.
      </p>
      <ul className="list-disc list-inside text-gray-400 space-y-2">
        <li><strong className="text-gray-300">Channels</strong>: 목록, Start/Stop, 멀티채널 HLS 플레이어</li>
        <li><strong className="text-gray-300">Events</strong>: stream.events 실시간 로그 (채널별 필터)</li>
      </ul>
    </main>
  );
}
