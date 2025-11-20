"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { DirectoryTree } from "./DirectoryTree";
import { FilePreview } from "./FilePreview";
import { Card } from "@/components/ui/card";
import { Folder, Database, Cloud } from "lucide-react";
import { loadFolderContents } from "@/app/dashboard/hardcode-assets/actions";
import type { DirectoryData, FileInfo } from "./types";
import { format } from "date-fns";
import { formatBytes } from "@/components/content/utils";

interface UserAsset {
  id: string;
  assetType: string;
  url: string | null;
  sessionId: string;
  metadata: unknown;
  createdAt: Date;
}

interface HardcodeAssetsViewProps {
  userAssets: UserAsset[];
  s3RootData: DirectoryData;
  allS3Files: FileInfo[];
  userId: string;
  userEmail: string;
}

export function HardcodeAssetsView({
  userAssets,
  s3RootData,
  allS3Files,
  userId,
  userEmail,
}: HardcodeAssetsViewProps) {
  const [selectedFile, setSelectedFile] = useState<FileInfo | null>(null);
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(
    new Set(),
  );
  const [folderContents, setFolderContents] = useState<
    Map<string, DirectoryData>
  >(new Map());

  // Use refs to track loaded folders and prevent duplicate calls
  const loadedFoldersRef = useRef<Set<string>>(new Set());
  const initialLoadDoneRef = useRef(false);

  // Initialize expanded folders from root data
  useEffect(() => {
    const folderPaths = new Set(s3RootData.folders.map((f) => f.path));
    setExpandedFolders(folderPaths);
    // Reset loaded folders when root data changes
    loadedFoldersRef.current.clear();
    initialLoadDoneRef.current = false;
  }, [s3RootData]);

  const loadFolderContentsHandler = useCallback(
    async (folderPath: string) => {
      // Check both state and ref to prevent duplicate calls
      if (
        folderContents.has(folderPath) ||
        loadedFoldersRef.current.has(folderPath)
      ) {
        return; // Already loaded or loading
      }

      // Mark as loading immediately
      loadedFoldersRef.current.add(folderPath);

      try {
        const data = await loadFolderContents(userId, folderPath);
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
        // Remove from loaded set on error so it can be retried
        loadedFoldersRef.current.delete(folderPath);
      }
    },
    [userId, folderContents],
  );

  const handleFolderToggle = (folderPath: string) => {
    setExpandedFolders((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(folderPath)) {
        newSet.delete(folderPath);
      } else {
        newSet.add(folderPath);
        // Load folder contents when expanding (only if not already loaded)
        if (!loadedFoldersRef.current.has(folderPath)) {
          void loadFolderContentsHandler(folderPath);
        }
      }
      return newSet;
    });
  };

  // Load contents for initially expanded folders (only once on mount/initial data)
  useEffect(() => {
    // Only run initial load once per s3RootData change
    if (initialLoadDoneRef.current) {
      return;
    }

    const initialFolders = s3RootData.folders.map((f) => f.path);
    if (initialFolders.length === 0) {
      initialLoadDoneRef.current = true;
      return;
    }

    // Load initial folders asynchronously after mount
    const loadInitialFolders = async () => {
      for (const folderPath of initialFolders) {
        if (!loadedFoldersRef.current.has(folderPath)) {
          await loadFolderContentsHandler(folderPath);
        }
      }
      initialLoadDoneRef.current = true;
    };

    void loadInitialFolders();
  }, [s3RootData, loadFolderContentsHandler]);

  return (
    <div className="flex h-full gap-6">
      <div className="flex-1 space-y-6 overflow-auto">
        {/* User Assets Section */}
        <Card className="p-4">
          <div className="mb-4 flex items-center gap-2">
            <Database className="h-5 w-5" />
            <h2 className="text-lg font-semibold">User Assets</h2>
            <span className="text-muted-foreground text-sm">
              ({userAssets.length} assets)
            </span>
          </div>
          {userAssets.length === 0 ? (
            <p className="text-muted-foreground text-sm">
              No assets found in database.
            </p>
          ) : (
            <div className="space-y-2">
              <div className="text-muted-foreground grid grid-cols-5 gap-4 border-b pb-2 text-sm font-medium">
                <div>ID</div>
                <div>Type</div>
                <div>Session ID</div>
                <div>URL</div>
                <div>Created</div>
              </div>
              {userAssets.map((asset) => (
                <div
                  key={asset.id}
                  className="grid grid-cols-5 gap-4 border-b pb-2 text-sm last:border-0"
                >
                  <div className="truncate font-mono text-xs">{asset.id}</div>
                  <div className="truncate">{asset.assetType}</div>
                  <div className="truncate font-mono text-xs">
                    {asset.sessionId}
                  </div>
                  <div className="truncate">
                    {asset.url ? (
                      <a
                        href={asset.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary hover:underline"
                      >
                        {asset.url.length > 30
                          ? `${asset.url.slice(0, 30)}...`
                          : asset.url}
                      </a>
                    ) : (
                      <span className="text-muted-foreground">No URL</span>
                    )}
                  </div>
                  <div className="text-muted-foreground">
                    {format(
                      asset.createdAt instanceof Date
                        ? asset.createdAt
                        : new Date(asset.createdAt),
                      "PPp",
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* All S3 Files Section */}
        <Card className="p-4">
          <div className="mb-4 flex items-center gap-2">
            <Cloud className="h-5 w-5" />
            <h2 className="text-lg font-semibold">All S3 Files</h2>
            <span className="text-muted-foreground text-sm">
              ({allS3Files.length} files)
            </span>
          </div>
          {allS3Files.length === 0 ? (
            <p className="text-muted-foreground text-sm">
              No files found in S3.
            </p>
          ) : (
            <div className="max-h-96 space-y-2 overflow-auto">
              <div className="text-muted-foreground bg-background sticky top-0 grid grid-cols-5 gap-4 border-b pb-2 text-sm font-medium">
                <div>Key</div>
                <div>Name</div>
                <div>Size</div>
                <div>Type</div>
                <div>Modified</div>
              </div>
              {allS3Files.map((file) => (
                <div
                  key={file.key}
                  className="hover:bg-muted/50 grid cursor-pointer grid-cols-5 gap-4 border-b pb-2 text-sm last:border-0"
                  onClick={() => setSelectedFile(file)}
                >
                  <div className="truncate font-mono text-xs" title={file.key}>
                    {file.key}
                  </div>
                  <div className="truncate" title={file.name}>
                    {file.name}
                  </div>
                  <div className="text-muted-foreground">
                    {formatBytes(file.size)}
                  </div>
                  <div className="text-muted-foreground truncate text-xs">
                    {file.content_type}
                  </div>
                  <div className="text-muted-foreground text-xs">
                    {file.last_modified
                      ? format(new Date(file.last_modified), "PPp")
                      : "Unknown"}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* S3 Directory Structure Section */}
        <Card className="p-4">
          <div className="mb-4 flex items-center gap-2">
            <Folder className="h-5 w-5" />
            <h2 className="text-lg font-semibold">S3 Directory Structure</h2>
          </div>
          <DirectoryTree
            folders={s3RootData.folders}
            files={s3RootData.files}
            folderContents={folderContents}
            expandedFolders={expandedFolders}
            onFolderToggle={handleFolderToggle}
            onFileSelect={setSelectedFile}
            onLoadFolder={loadFolderContentsHandler}
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
