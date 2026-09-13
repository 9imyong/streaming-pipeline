"use client";

import { useParams } from "next/navigation";
import { SourceDetailView } from "@/components/sources/source-detail-view";

export default function SourceDetailPage() {
  const params = useParams();
  const sourceId = params.sourceId as string;

  return <SourceDetailView sourceId={sourceId} />;
}
