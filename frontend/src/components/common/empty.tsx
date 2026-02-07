export function EmptyState({
  title = "No data",
  description,
}: {
  title?: string;
  description?: string;
}) {
  return (
    <div className="rounded-md border border-border p-8 text-center">
      <p className="font-medium text-muted-foreground">{title}</p>
      {description && (
        <p className="mt-1 text-sm text-muted-foreground">{description}</p>
      )}
    </div>
  );
}
