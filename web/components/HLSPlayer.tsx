"use client";

import { useEffect, useRef } from "react";
import Hls from "hls.js";
import { HLS_DEFAULT_OPTIONS } from "@/lib/hls";

export interface HLSPlayerProps {
  src: string;
  autoplay?: boolean;
  muted?: boolean;
  controls?: boolean;
  className?: string;
  onError?: (message: string) => void;
}

export function HLSPlayer({
  src,
  autoplay = true,
  muted = true,
  controls = true,
  className = "",
  onError,
}: HLSPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const hlsRef = useRef<Hls | null>(null);

  useEffect(() => {
    const video = videoRef.current;
    if (!video || !src) return;

    const cleanup = () => {
      if (hlsRef.current) {
        hlsRef.current.destroy();
        hlsRef.current = null;
      }
    };

    if (video.canPlayType("application/vnd.apple.mpegurl") || video.canPlayType("application/x-mpegURL")) {
      video.src = src;
      video.addEventListener("error", () => onError?.(`Native HLS error: ${video.error?.message || "unknown"}`));
      return cleanup;
    }

    if (!Hls.isSupported()) {
      video.src = src;
      onError?.("HLS not supported");
      return cleanup;
    }

    const hls = new Hls({ ...HLS_DEFAULT_OPTIONS });
    hlsRef.current = hls;
    hls.loadSource(src);
    hls.attachMedia(video);

    hls.on(Hls.Events.ERROR, (_e, data) => {
      if (data.fatal) {
        if (data.type === Hls.ErrorTypes.NETWORK_ERROR) {
          hls.startLoad();
        } else if (data.type === Hls.ErrorTypes.MEDIA_ERROR) {
          hls.recoverMediaError();
        } else {
          onError?.(`HLS fatal: ${data.type}`);
          hls.destroy();
        }
      }
    });

    return cleanup;
  }, [src, onError]);

  return (
    <video
      ref={videoRef}
      className={className}
      controls={controls}
      autoPlay={autoplay}
      muted={muted}
      playsInline
    />
  );
}
