export interface FolderInfo {
  name: string;
  path: string;
}

export interface FileInfo {
  key: string;
  name: string;
  size: number;
  last_modified: string | null;
  content_type: string;
  presigned_url: string;
}

export interface DirectoryData {
  folders: FolderInfo[];
  files: FileInfo[];
  prefix: string;
}

