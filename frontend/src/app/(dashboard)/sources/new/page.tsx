"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { createSource } from "@/lib/api";
import { ApiError } from "@/lib/api/client";
import { SourceForm } from "@/components/sources/source-form";
import type { SourceFormValues } from "@/components/sources/source-form";

export default function NewSourcePage() {
  const router = useRouter();

  async function handleSubmit(values: SourceFormValues) {
    try {
      await createSource({
        name: values.name,
        rtsp_url: values.rtsp_url,
        location: values.location || undefined,
        description: values.description || undefined,
        enabled: values.enabled,
      });
      toast.success("Source created.");
      router.push("/sources");
    } catch (e) {
      if (e instanceof ApiError && e.status === 409) {
        throw new Error("이미 같은 RTSP URL이 등록되어 있습니다.");
      }
      throw e;
    }
  }

  return (
    <div>
      <Link
        href="/sources"
        className="text-sm text-muted-foreground hover:text-foreground"
      >
        ← Sources
      </Link>
      <h1 className="mt-2 text-2xl font-bold">Add Source</h1>
      <p className="mt-1 text-muted-foreground">
        Name, RTSP URL (필수). 중복 URL 시 서버에서 409.
      </p>
      <div className="mt-6">
        <SourceForm onSubmit={handleSubmit} submitLabel="Create" />
      </div>
    </div>
  );
}
