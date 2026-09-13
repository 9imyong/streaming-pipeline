"use client";

import { useState, useEffect } from "react";
import { getBaseUrl } from "@/lib/api/client";

export function TopBar() {
  const [displayUrl, setDisplayUrl] = useState<string>("");
  const [env, setEnv] = useState<string>("");

  useEffect(() => {
    const base = getBaseUrl();
    setDisplayUrl(base || "(mock / env)");
    setEnv(
      typeof process !== "undefined" && process.env.NODE_ENV === "production"
        ? "prod"
        : "dev"
    );
  }, []);

  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-border bg-card px-6">
      <span className="text-lg font-semibold">Streaming Pipeline</span>
      <span className="text-xs text-muted-foreground" title={displayUrl}>
        {env} · {displayUrl ? (displayUrl.length > 40 ? `${displayUrl.slice(0, 37)}…` : displayUrl) : "—"}
      </span>
    </header>
  );
}
