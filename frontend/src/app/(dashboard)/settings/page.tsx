"use client";

import { useState, useEffect } from "react";
import { toast } from "sonner";
import {
  getSettings,
  setApiBaseUrl,
  setApiKey,
  setPollIntervalMs,
} from "@/lib/storage/settings";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const DEFAULT_POLL_MS = 2000;
const DEFAULT_BASE_URL =
  typeof process !== "undefined"
    ? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"
    : "http://localhost:8000";

export default function SettingsPage() {
  const [apiBaseUrl, setApiBaseUrlState] = useState("");
  const [apiKey, setApiKeyState] = useState("");
  const [pollIntervalMs, setPollIntervalMsState] = useState(DEFAULT_POLL_MS);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const s = getSettings();
    setApiBaseUrlState(s.apiBaseUrl || DEFAULT_BASE_URL);
    setApiKeyState(s.apiKey);
    setPollIntervalMsState(s.pollIntervalMs);
  }, []);

  function handleSave() {
    setApiBaseUrl(apiBaseUrl.trim());
    setApiKey(apiKey.trim());
    setPollIntervalMs(
      Number.isFinite(pollIntervalMs) && pollIntervalMs > 0
        ? pollIntervalMs
        : DEFAULT_POLL_MS
    );
    setSaved(true);
    toast.success("Settings saved. Reload to apply poll interval.");
    setTimeout(() => setSaved(false), 2000);
  }

  return (
    <div>
      <h1 className="text-2xl font-bold">Settings</h1>
      <p className="mt-1 text-muted-foreground">
        API Base URL, API Key, Poll interval (localStorage)
      </p>
      <Card className="mt-6 max-w-lg">
        <CardHeader>
          <CardTitle>Environment</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-muted-foreground">
              API Base URL
            </label>
            <Input
              type="url"
              placeholder={DEFAULT_BASE_URL}
              value={apiBaseUrl}
              onChange={(e) => setApiBaseUrlState(e.target.value)}
              className="font-mono text-sm"
            />
            <p className="mt-1 text-xs text-muted-foreground">
              비우면 빌드 시 NEXT_PUBLIC_API_BASE_URL 사용
            </p>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-muted-foreground">
              API Key
            </label>
            <Input
              type="password"
              placeholder="Optional"
              value={apiKey}
              onChange={(e) => setApiKeyState(e.target.value)}
              className="font-mono text-sm"
              autoComplete="off"
            />
            <p className="mt-1 text-xs text-muted-foreground">
              저장 시 모든 API 요청에 x-api-key 헤더로 포함
            </p>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-muted-foreground">
              Poll interval (ms)
            </label>
            <Input
              type="number"
              min={1000}
              max={30000}
              step={1000}
              value={pollIntervalMs}
              onChange={(e) =>
                setPollIntervalMsState(Number(e.target.value) || DEFAULT_POLL_MS)
              }
            />
            <p className="mt-1 text-xs text-muted-foreground">
              기본 2000. 적용하려면 페이지 새로고침
            </p>
          </div>
          <Button onClick={handleSave}>{saved ? "Saved" : "Save"}</Button>
        </CardContent>
      </Card>
    </div>
  );
}
