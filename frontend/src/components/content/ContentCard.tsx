"use client";

import { Card } from "@/components/ui/card";
import { ContentActions } from "./ContentActions";
import type { FileInfo } from "@/lib/types/storage";
import { AssetType } from "@/lib/types/storage";
import Image from "next/image";
import { formatBytes, getAssetTypeFromKey } from "./utils";

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
  const isImage = file.content_type.startsWith("image/");
  const isVideo = file.content_type.startsWith("video/");
  const isAudio = file.content_type.startsWith("audio/");
  const isFinal = assetType === AssetType.FINAL;

  const fileName = file.key.split("/").pop() ?? "unknown";

  return (
    <Card className="overflow-hidden">
      <div className="relative aspect-video bg-muted">
        {isImage && (
          <Image
            src={file.presigned_url}
            alt={fileName}
            fill
            className="object-cover"
            unoptimized
          />
        )}
        {isVideo && (
          <video
            src={file.presigned_url}
            controls
            className="w-full h-full object-cover"
          />
        )}
        {isAudio && (
          <div className="flex items-center justify-center h-full">
            <audio src={file.presigned_url} controls className="w-full" />
          </div>
        )}
        {!isImage && !isVideo && !isAudio && (
          <div className="flex items-center justify-center h-full text-muted-foreground">
            <span>Preview not available</span>
          </div>
        )}
        {isFinal && (
          <div className="absolute top-2 right-2 bg-primary text-primary-foreground px-2 py-1 rounded text-xs font-semibold">
            Final
          </div>
        )}
      </div>
      <div className="p-4 space-y-2">
        <div>
          <p className="font-medium text-sm truncate" title={fileName}>
            {fileName}
          </p>
          <p className="text-xs text-muted-foreground">
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


