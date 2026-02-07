import { StreamDetailView } from "@/components/streams/stream-detail-view";

export default function StreamDetailPage({
  params,
}: {
  params: { streamId: string };
}) {
  return <StreamDetailView streamId={params.streamId} />;
}
