import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function SettingsPage() {
  const apiBase =
    typeof process !== "undefined"
      ? process.env.NEXT_PUBLIC_API_BASE_URL ?? "—"
      : "—";
  const pollMs =
    typeof process !== "undefined"
      ? process.env.NEXT_PUBLIC_POLL_INTERVAL_MS ?? "2000"
      : "2000";

  return (
    <div>
      <h1 className="text-2xl font-bold">Settings</h1>
      <p className="mt-1 text-muted-foreground">환경 변수 (빌드 시 주입)</p>
      <Card className="mt-6 max-w-lg">
        <CardHeader>
          <CardTitle>Environment</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <p>
            <span className="text-muted-foreground">NEXT_PUBLIC_API_BASE_URL:</span>{" "}
            <code className="rounded bg-muted px-1">{apiBase}</code>
          </p>
          <p>
            <span className="text-muted-foreground">NEXT_PUBLIC_POLL_INTERVAL_MS:</span>{" "}
            <code className="rounded bg-muted px-1">{pollMs}</code>
          </p>
          <p className="pt-2 text-muted-foreground">
            변경 시 앱 재빌드 필요. API Key 등은 추후 추가.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
