"use client";

import { Card } from "@/components/ui/card";
import { ContentActions } from "./ContentActions";
import type { FileInfo } from "@/types/storage";
import { AssetType } from "@/types/storage";
import {
  formatBytes,
  getAssetTypeFromKey,
  inferContentTypeFromKey,
} from "./utils";
import { Play } from "lucide-react";
import { useState, useRef, useEffect } from "react";

interface ContentCardProps {
  file: FileInfo;
  onDelete: () => Promise<void>;
  isDeleting?: boolean;
}

export function ContentCard({
  file,
  onDelete,
  isDeleting = false,
}: ContentCardProps) {
  const assetType = getAssetTypeFromKey(file.key);
  // Use content_type if available, otherwise infer from file extension
  const contentType =
    file.content_type !== "application/octet-stream"
      ? file.content_type
      : inferContentTypeFromKey(file.key);
  const isImage = contentType.startsWith("image/");
  const isVideo = contentType.startsWith("video/");
  const isAudio = contentType.startsWith("audio/");
  const isFinal = assetType === AssetType.FINAL;

  const fileName = file.key.split("/").pop() ?? "unknown";

  // Lazy loading for videos
  const [isVideoVisible, setIsVideoVisible] = useState(false);
  const videoRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isVideo || !videoRef.current) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setIsVideoVisible(true);
          }
        });
      },
      { rootMargin: "50px" },
    );

    observer.observe(videoRef.current);

    return () => observer.disconnect();
  }, [isVideo]);

  return (
    <Card className="mt-0 overflow-hidden pt-0">
      <div className="bg-muted relative aspect-video">
        {isImage && (
          <img
            src={file.presigned_url}
            alt={fileName}
            className="h-full w-full object-cover"
          />
        )}
        {isVideo && (
          <div ref={videoRef} className="relative h-full w-full">
            {isVideoVisible ? (
              <video
                src={file.presigned_url}
                controls
                preload="metadata"
                className="h-full w-full object-cover"
              />
            ) : (
              <div className="relative h-full w-full">
                <video
                  src={file.presigned_url}
                  preload="metadata"
                  className="h-full w-full object-cover"
                />
                <div className="absolute inset-0 flex items-center justify-center bg-black/20">
                  <div className="rounded-full bg-white/90 p-4">
                    <Play className="h-8 w-8 text-black" />
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
        {isAudio && (
          <div className="flex h-full items-center justify-center">
            <audio src={file.presigned_url} controls className="w-full" />
          </div>
        )}
        {!isImage && !isVideo && !isAudio && (
          <div className="text-muted-foreground flex h-full items-center justify-center">
            <span>Preview not available</span>
          </div>
        )}
        {isFinal && (
          <div className="bg-primary text-primary-foreground absolute top-2 right-2 rounded px-2 py-1 text-xs font-semibold">
            Final
          </div>
        )}
      </div>
      <div className="space-y-2 p-4">
        <div>
          <p className="truncate text-sm font-medium" title={fileName}>
            {fileName}
          </p>
          <p className="text-muted-foreground text-xs">
            {formatBytes(file.size)}
          </p>
        </div>
        <ContentActions
          presignedUrl={file.presigned_url}
          fileName={fileName}
          onDelete={onDelete}
          isDeleting={isDeleting}
        />
      </div>
    </Card>
  );
}
