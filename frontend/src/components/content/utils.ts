/**
 * Utility functions for content components.
 */

import { AssetType } from "@/types/storage";

/**
 * Format bytes to human-readable string.
 */
export function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 Bytes";

  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i] ?? ""}`;
}

/**
 * Extract asset type from S3 key.
 * Keys follow pattern: users/{user_id}/output/{asset_type}/{filename}
 */
export function getAssetTypeFromKey(key: string): AssetType | null {
  const parts = key.split("/");
  const outputIndex = parts.indexOf("output");

  if (outputIndex === -1 || outputIndex >= parts.length - 1) {
    return null;
  }

  const assetType = parts[outputIndex + 1]!;
  const assetTypeValues = Object.values(AssetType) as string[];

  if (assetTypeValues.includes(assetType)) {
    return assetType as AssetType;
  }

  return null;
}

/**
 * Infer content type from file extension.
 * Used as fallback when S3 doesn't provide ContentType.
 */
export function inferContentTypeFromKey(key: string): string {
  const extension = key.split(".").pop()?.toLowerCase();
  
  const mimeTypes: Record<string, string> = {
    // Images
    png: "image/png",
    jpg: "image/jpeg",
    jpeg: "image/jpeg",
    gif: "image/gif",
    webp: "image/webp",
    svg: "image/svg+xml",
    ico: "image/x-icon",
    // Videos
    mp4: "video/mp4",
    webm: "video/webm",
    mov: "video/quicktime",
    avi: "video/x-msvideo",
    mkv: "video/x-matroska",
    // Audio
    mp3: "audio/mpeg",
    wav: "audio/wav",
    ogg: "audio/ogg",
    m4a: "audio/mp4",
    // Documents
    pdf: "application/pdf",
    txt: "text/plain",
    md: "text/markdown",
    json: "application/json",
  };

  if (extension && mimeTypes[extension]) {
    return mimeTypes[extension]!;
  }

  return "application/octet-stream";
}