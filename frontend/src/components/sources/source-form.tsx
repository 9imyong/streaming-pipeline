"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const RTSP_REGEX = /^rtsp:\/\//i;

export interface SourceFormValues {
  name: string;
  rtsp_url: string;
  location: string;
  description: string;
  enabled: boolean;
}

const defaultValues: SourceFormValues = {
  name: "",
  rtsp_url: "",
  location: "",
  description: "",
  enabled: true,
};

export interface SourceFormProps {
  initialValues?: Partial<SourceFormValues>;
  onSubmit: (values: SourceFormValues) => Promise<void>;
  submitLabel?: string;
}

export function SourceForm({
  initialValues,
  onSubmit,
  submitLabel = "Save",
}: SourceFormProps) {
  const [name, setName] = useState(initialValues?.name ?? defaultValues.name);
  const [rtsp_url, setRtspUrl] = useState(
    initialValues?.rtsp_url ?? defaultValues.rtsp_url
  );
  const [location, setLocation] = useState(
    initialValues?.location ?? defaultValues.location
  );
  const [description, setDescription] = useState(
    initialValues?.description ?? defaultValues.description
  );
  const [enabled, setEnabled] = useState(
    initialValues?.enabled ?? defaultValues.enabled
  );
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function validate(): string | null {
    if (!name.trim()) return "Name is required.";
    if (!rtsp_url.trim()) return "RTSP URL is required.";
    if (!RTSP_REGEX.test(rtsp_url.trim())) {
      return "RTSP URL must start with rtsp://";
    }
    return null;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const err = validate();
    setError(err);
    if (err) return;
    setLoading(true);
    try {
      await onSubmit({
        name: name.trim(),
        rtsp_url: rtsp_url.trim(),
        location: location.trim() || "",
        description: description.trim() || "",
        enabled,
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <Card className="max-w-lg">
        <CardHeader>
          <CardTitle>Source</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && (
            <p className="rounded bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {error}
            </p>
          )}
          <div>
            <label className="mb-1 block text-sm font-medium text-muted-foreground">
              Name (필수)
            </label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. 입구 카메라"
              required
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-muted-foreground">
              RTSP URL (필수)
            </label>
            <Input
              type="url"
              value={rtsp_url}
              onChange={(e) => setRtspUrl(e.target.value)}
              placeholder="rtsp://host/path"
              className="font-mono text-sm"
              required
            />
            <p className="mt-1 text-xs text-muted-foreground">
              rtsp:// 로 시작해야 합니다.
            </p>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-muted-foreground">
              Location (옵션)
            </label>
            <Input
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="e.g. 1층 입구"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-muted-foreground">
              Description (옵션)
            </label>
            <Input
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optional description"
            />
          </div>
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="enabled"
              checked={enabled}
              onChange={(e) => setEnabled(e.target.checked)}
            />
            <label htmlFor="enabled" className="text-sm">
              Enabled (기본 true)
            </label>
          </div>
          <Button type="submit" disabled={loading}>
            {loading ? "Saving…" : submitLabel}
          </Button>
        </CardContent>
      </Card>
    </form>
  );
}
