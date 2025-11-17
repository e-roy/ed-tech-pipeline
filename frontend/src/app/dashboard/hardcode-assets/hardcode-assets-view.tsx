"use client";

import { useState, useEffect } from "react";
import { DirectoryTree } from "@/components/hardcode-assets/DirectoryTree";
import { FilePreview } from "@/components/hardcode-assets/FilePreview";
import { Skeleton } from "@/components/ui/skeleton";
import { Card } from "@/components/ui/card";
import { Folder } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

interface FolderInfo {
  name: string;
  path: string;
}

interface FileInfo {
  key: string;
  name: string;
  size: number;
  last_modified: string | null;
  content_type: string;
  presigned_url: string;
}

interface DirectoryData {
  folders: FolderInfo[];
  files: FileInfo[];
  prefix: string;
}

interface HardcodeAssetsViewProps {
  userEmail: string;
}

export function HardcodeAssetsView({ userEmail }: HardcodeAssetsViewProps) {
  const [directoryData, setDirectoryData] = useState<DirectoryData | null>(
    null,
  );
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<FileInfo | null>(null);
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(
    new Set(),
  );
  const [folderContents, setFolderContents] = useState<
    Map<string, DirectoryData>
  >(new Map());

  useEffect(() => {
    if (!userEmail) return;

    const loadRootDirectory = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await fetch(
          `${API_URL}/api/storage/directory?prefix=`,
          {
            headers: {
              "X-User-Email": userEmail,
            },
          },
        );

        if (!response.ok) {
          throw new Error(`Failed to load directory: ${response.statusText}`);
        }

        const data: DirectoryData = await response.json();
        setDirectoryData(data);
        // Expand all folders by default
        const folderPaths = new Set(data.folders.map((f) => f.path));
        setExpandedFolders(folderPaths);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load directory");
      } finally {
        setIsLoading(false);
      }
    };

    loadRootDirectory();
  }, [userEmail]);

  const loadFolderContents = async (folderPath: string) => {
    // Extract prefix from folder path (remove users/{userid}/)
    const prefixMatch = folderPath.match(/^users\/\d+\/(.+)$/);
    if (!prefixMatch) return;

    const prefix = prefixMatch[1];
    if (folderContents.has(folderPath)) {
      return; // Already loaded
    }

    try {
      const response = await fetch(
        `${API_URL}/api/storage/directory?prefix=${encodeURIComponent(prefix)}`,
        {
          headers: {
            "X-User-Email": userEmail ?? "",
          },
        },
      );

      if (!response.ok) {
        throw new Error(`Failed to load folder: ${response.statusText}`);
      }

      const data: DirectoryData = await response.json();
      setFolderContents((prev) => {
        const newMap = new Map(prev);
        newMap.set(folderPath, data);
        return newMap;
      });

      // Expand all subfolders by default
      const subfolderPaths = new Set(data.folders.map((f) => f.path));
      setExpandedFolders((prev) => {
        const newSet = new Set(prev);
        subfolderPaths.forEach((path) => newSet.add(path));
        return newSet;
      });
    } catch (err) {
      console.error(`Failed to load folder ${folderPath}:`, err);
    }
  };

  const handleFolderToggle = (folderPath: string) => {
    setExpandedFolders((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(folderPath)) {
        newSet.delete(folderPath);
      } else {
        newSet.add(folderPath);
        // Load folder contents when expanding
        void loadFolderContents(folderPath);
      }
      return newSet;
    });
  };

  // Load contents for initially expanded folders
  useEffect(() => {
    if (directoryData) {
      directoryData.folders.forEach((folder) => {
        if (expandedFolders.has(folder.path)) {
          void loadFolderContents(folder.path);
        }
      });
    }
  }, [directoryData, expandedFolders]);

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-64" />
        <Card className="p-4">
          <Skeleton className="h-6 w-full mb-2" />
          <Skeleton className="h-6 w-full mb-2" />
          <Skeleton className="h-6 w-full" />
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="p-6">
        <p className="text-destructive">Error: {error}</p>
      </Card>
    );
  }

  if (!directoryData) {
    return (
      <Card className="p-6">
        <p className="text-muted-foreground">No data available</p>
      </Card>
    );
  }

  return (
    <div className="flex h-full gap-6">
      <div className="flex-1 overflow-auto">
        <Card className="p-4">
          <div className="flex items-center gap-2 mb-4">
            <Folder className="h-5 w-5" />
            <h2 className="text-lg font-semibold">Directory Structure</h2>
          </div>
          <DirectoryTree
            folders={directoryData.folders}
            files={directoryData.files}
            folderContents={folderContents}
            expandedFolders={expandedFolders}
            onFolderToggle={handleFolderToggle}
            onFileSelect={setSelectedFile}
            onLoadFolder={loadFolderContents}
            userEmail={userEmail}
            level={0}
          />
        </Card>
      </div>
      {selectedFile && (
        <div className="w-96">
          <FilePreview file={selectedFile} />
        </div>
      )}
    </div>
  );
}

