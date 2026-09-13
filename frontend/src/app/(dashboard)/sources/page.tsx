import Link from "next/link";
import { SourceTable } from "@/components/sources/source-table";
import { Button } from "@/components/ui/button";

export default function SourcesPage() {
  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Sources (CCTV)</h1>
          <p className="mt-1 text-muted-foreground">
            등록된 소스 목록 · 검색/필터 · Detail / Enable·Disable / Create Stream
          </p>
        </div>
        <Button asChild>
          <Link href="/sources/new">+ Add</Link>
        </Button>
      </div>
      <div className="mt-6">
        <SourceTable />
      </div>
    </div>
  );
}
