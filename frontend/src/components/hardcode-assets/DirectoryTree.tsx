"use client";

import { ChevronRight, ChevronDown, Folder, File, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { formatBytes } from "@/components/content/utils";
import type { DirectoryData } from "./types";

interface DirectoryTreeProps {
  folders: Array<{ name: string; path: string }>;
  files: Array<{
    key: string;
    name: string;
    size: number;
    last_modified: string | null;
    content_type: string;
    presigned_url: string;
  }>;
  folderContents: Map<string, DirectoryData>;
  expandedFolders: Set<string>;
  onFolderToggle: (folderPath: string) => void;
  onFileSelect: (file: {
    key: string;
    name: string;
    size: number;
    last_modified: string | null;
    content_type: string;
    presigned_url: string;
  }) => void;
  onLoadFolder: (folderPath: string) => Promise<void>;
  userEmail: string;
  level: number;
}

export function DirectoryTree({
  folders,
  files,
  folderContents,
  expandedFolders,
  onFolderToggle,
  onFileSelect,
  onLoadFolder,
  userEmail,
  level,
}: DirectoryTreeProps) {
  const handleFolderClick = async (folderPath: string) => {
    if (!expandedFolders.has(folderPath)) {
      await onLoadFolder(folderPath);
    }
    onFolderToggle(folderPath);
  };

  const handleDownload = (
    e: React.MouseEvent,
    presignedUrl: string,
    fileName: string,
  ) => {
    e.stopPropagation();
    const link = document.createElement("a");
    link.href = presignedUrl;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const indent = level * 20;

  return (
    <div className="space-y-1">
      {/* Folders */}
      {folders.map((folder) => {
        const isExpanded = expandedFolders.has(folder.path);
        const contents = folderContents.get(folder.path);

        return (
          <div key={folder.path}>
            <div
              className="flex items-center gap-2 py-1 px-2 rounded hover:bg-muted cursor-pointer"
              style={{ paddingLeft: `${indent + 8}px` }}
              onClick={() => void handleFolderClick(folder.path)}
            >
              {isExpanded ? (
                <ChevronDown className="h-4 w-4 text-muted-foreground" />
              ) : (
                <ChevronRight className="h-4 w-4 text-muted-foreground" />
              )}
              <Folder className="h-4 w-4 text-blue-500" />
              <span className="flex-1 text-sm font-medium">{folder.name}</span>
            </div>
            {isExpanded && contents && (
              <DirectoryTree
                folders={contents.folders}
                files={contents.files}
                folderContents={folderContents}
                expandedFolders={expandedFolders}
                onFolderToggle={onFolderToggle}
                onFileSelect={onFileSelect}
                onLoadFolder={onLoadFolder}
                userEmail={userEmail}
                level={level + 1}
              />
            )}
          </div>
        );
      })}

      {/* Files */}
      {files.map((file) => (
        <div
          key={file.key}
          className="flex items-center gap-2 py-1 px-2 rounded hover:bg-muted cursor-pointer group"
          style={{ paddingLeft: `${indent + 24}px` }}
          onClick={() => onFileSelect(file)}
        >
          <File className="h-4 w-4 text-muted-foreground flex-shrink-0" />
          <span className="flex-1 text-sm truncate" title={file.name}>
            {file.name}
          </span>
          <span className="text-xs text-muted-foreground">
            {formatBytes(file.size)}
          </span>
          <Button
            variant="ghost"
            size="sm"
            className="h-7 w-7 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
            onClick={(e) => handleDownload(e, file.presigned_url, file.name)}
          >
            <Download className="h-4 w-4" />
          </Button>
        </div>
      ))}
    </div>
  );
}

