import { Skeleton } from "@/components/ui/skeleton";

export function LoadingTable({ rows = 5 }: { rows?: number }) {
  return (
    <div className="space-y-2">
      <Skeleton className="h-10 w-full" />
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} className="h-12 w-full" />
      ))}
    </div>
  );
}

export function LoadingCard() {
  return (
    <Skeleton className="h-24 w-full rounded-lg" />
  );
}
