"use client";

import { useRef, useEffect, useState, useCallback } from "react";
import Hls from "hls.js";
import { getBaseUrl } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";

export type PlayerState = "idle" | "buffering" | "playing" | "error";

export interface StreamPlayerProps {
  streamId: string;
  /** HLS base URL (optional). Default: getBaseUrl() */
  hlsBaseUrl?: string;
  className?: string;
  /** autoplay 실패 시 클릭 유도 문구 */
  playPrompt?: string;
}

function buildHlsUrl(streamId: string, baseUrl?: string): string {
  const base = (baseUrl ?? getBaseUrl()).replace(/\/$/, "");
  const path = endpoints.hlsPlaylist(streamId);
  return path.startsWith("http") ? path : `${base}${path}`;
}

export function StreamPlayer({
  streamId,
  hlsBaseUrl,
  className = "",
  playPrompt = "Click to play",
}: StreamPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const hlsRef = useRef<Hls | null>(null);
  const [state, setState] = useState<PlayerState>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [userInteracted, setUserInteracted] = useState(false);

  const url = buildHlsUrl(streamId, hlsBaseUrl);

  useEffect(() => {
    const video = videoRef.current;
    if (!video || !streamId) return;

    if (Hls.isSupported()) {
      const hls = new Hls({
        enableWorker: true,
        lowLatencyMode: true,
      });
      hlsRef.current = hls;

      hls.on(Hls.Events.MANIFEST_PARSED, () => setState("buffering"));
      hls.on(Hls.Events.BUFFER_APPENDED, () => setState((s) => (s === "playing" ? s : "buffering")));
      hls.on(Hls.Events.ERROR, (_e, data) => {
        if (data.fatal) {
          setState("error");
          const detail = data.details ?? data.type ?? "Unknown";
          const msg =
            data.response?.code === 404
              ? "Playlist not found (404). Stream may not be running."
              : data.response?.code
                ? `HTTP ${data.response.code}`
                : String(detail);
          setErrorMessage(msg);
        }
      });

      hls.loadSource(url);
      hls.attachMedia(video);

      video.addEventListener("playing", () => setState("playing"));
      video.addEventListener("waiting", () => setState("buffering"));
      video.addEventListener("error", () => {
        setState("error");
        setErrorMessage("Video element error");
      });

      return () => {
        video.removeEventListener("playing", () => setState("playing"));
        video.removeEventListener("waiting", () => setState("buffering"));
        video.removeEventListener("error", () => {});
        hls.destroy();
        hlsRef.current = null;
      };
    }

    // Native HLS (e.g. Safari)
    if (video.canPlayType("application/vnd.apple.mpegurl")) {
      video.src = url;
      setState("buffering");
      video.addEventListener("playing", () => setState("playing"));
      video.addEventListener("waiting", () => setState("buffering"));
      video.addEventListener("error", () => {
        setState("error");
        setErrorMessage("Playback error");
      });
      return () => {
        video.removeEventListener("playing", () => setState("playing"));
        video.removeEventListener("waiting", () => setState("buffering"));
        video.removeEventListener("error", () => {});
        video.src = "";
        setState("idle");
      };
    }

    setState("error");
    setErrorMessage("HLS not supported");
    return undefined;
  }, [streamId, url]);


  const handlePlayClick = useCallback(() => {
    const video = videoRef.current;
    if (!video) return;
    setUserInteracted(true);
    video.play().catch(() => setErrorMessage("Autoplay blocked. Click to play."));
  }, []);

  const showPlayOverlay =
    !userInteracted &&
    (state === "idle" || state === "buffering") &&
    videoRef.current;

  return (
    <div className={`relative aspect-video w-full max-w-2xl overflow-hidden rounded-lg bg-black ${className}`}>
      <video
        ref={videoRef}
        className="h-full w-full object-contain"
        playsInline
        muted
        onPlay={handlePlayClick}
        onClick={handlePlayClick}
      />
      {showPlayOverlay && (
        <button
          type="button"
          onClick={handlePlayClick}
          className="absolute inset-0 flex items-center justify-center bg-black/50 text-white transition hover:bg-black/60"
          aria-label="Play"
        >
          <span className="rounded bg-primary px-4 py-2 text-sm font-medium">
            {playPrompt}
          </span>
        </button>
      )}
      {state === "buffering" && (
        <div className="absolute bottom-2 left-2 rounded bg-black/70 px-2 py-1 text-xs text-white">
          Buffering…
        </div>
      )}
      {state === "playing" && (
        <div className="absolute bottom-2 left-2 rounded bg-black/70 px-2 py-1 text-xs text-green-400">
          Playing
        </div>
      )}
      {state === "error" && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-black/80 p-4 text-center text-sm text-white">
          <span className="text-destructive">Playback error</span>
          {errorMessage && <span className="text-muted-foreground">{errorMessage}</span>}
          <button
            type="button"
            onClick={() => {
              setState("idle");
              setErrorMessage(null);
              setUserInteracted(false);
              if (videoRef.current && hlsRef.current) {
                hlsRef.current.loadSource(url);
              }
            }}
            className="rounded bg-primary px-3 py-1 text-xs"
          >
            Retry
          </button>
        </div>
      )}
    </div>
  );
}
