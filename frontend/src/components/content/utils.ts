/**
 * Utility functions for content components.
 */

import { AssetType } from "@/lib/types/storage";

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


