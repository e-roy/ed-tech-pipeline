/**
 * Type definitions for storage/file management.
 */

export enum AssetType {
  IMAGES = "images",
  VIDEOS = "videos",
  AUDIO = "audio",
  FINAL = "final",
  ALL = "all",
}

export interface FileInfo {
  key: string;
  size: number;
  last_modified: string | null;
  content_type: string;
  presigned_url: string;
}

export interface FileListResponse {
  files: FileInfo[];
  total: number;
  limit: number;
  offset: number;
}

export interface PresignedUrlResponse {
  presigned_url: string;
  expires_in: number;
}

export type ContentFilter = AssetType | "all";


