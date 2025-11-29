"use client";

import { useState } from "react";
import { api } from "@/trpc/react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Folder,
  FileJson,
  ChevronRight,
  ChevronDown,
  Download,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  ResizablePanelGroup,
  ResizablePanel,
  ResizableHandle,
} from "@/components/ui/resizable";

interface DebugViewProps {
  sessionId: string;
}

interface JsonFile {
  key: string;
  name: string;
  size: number;
  last_modified: string | null;
  content_type: string;
  presigned_url: string;
  content?: unknown;
}

export function DebugView({ sessionId }: DebugViewProps) {
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(
    new Set(["root"]),
  );
  const [selectedFile, setSelectedFile] = useState<JsonFile | null>(null);
  const [fileContents, setFileContents] = useState<
    Record<string, { content: unknown; loading: boolean; error?: string }>
  >({});

  // Fetch root directory structure
  const { data: rootData, isLoading: isLoadingRoot } =
    api.storage.listSessionDirectory.useQuery(
      {
        sessionId,
      },
      {
        enabled: !!sessionId,
      },
    );

  const toggleFolder = (folderPath: string) => {
    setExpandedFolders((prev) => {
      const next = new Set(prev);
      if (next.has(folderPath)) {
        next.delete(folderPath);
      } else {
        next.add(folderPath);
      }
      return next;
    });
  };

  const fetchFileContent = async (file: JsonFile) => {
    const cachedContent = fileContents[file.key];
    if (cachedContent?.content) {
      // Already loaded
      setSelectedFile({ ...file, content: cachedContent.content });
      return;
    }

    setFileContents((prev) => ({
      ...prev,
      [file.key]: { content: null, loading: true },
    }));

    try {
      const response = await fetch(file.presigned_url);
      const content = (await response.json()) as unknown;

      setFileContents((prev) => ({
        ...prev,
        [file.key]: { content, loading: false },
      }));

      setSelectedFile({ ...file, content });
    } catch (error) {
      const errorMsg =
        error instanceof Error ? error.message : "Failed to load file";
      setFileContents((prev) => ({
        ...prev,
        [file.key]: { content: null, loading: false, error: errorMsg },
      }));
    }
  };

  const downloadFile = (file: JsonFile) => {
    const link = document.createElement("a");
    link.href = file.presigned_url;
    link.download = file.name;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (isLoadingRoot) {
    return (
      <div className="p-4">
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-10 w-full" />
          ))}
        </div>
      </div>
    );
  }

  if (!rootData) {
    return (
      <div className="text-muted-foreground p-4 text-center">
        No debug data available for this session.
      </div>
    );
  }

  const jsonFiles = rootData.files.filter((f) =>
    f.name.toLowerCase().endsWith(".json"),
  );

  return (
    <ResizablePanelGroup direction="horizontal" className="h-full min-h-0 w-full">
      {/* Left: File tree */}
      <ResizablePanel defaultSize={30} minSize={15}>
        <div className="flex h-full min-h-0 flex-col border-r">
          <div className="border-b p-3">
            <h3 className="font-semibold">Session Files</h3>
            <p className="text-muted-foreground text-xs">
              JSON files from S3 bucket
            </p>
          </div>
          <ScrollArea className="flex-1">
            <div className="p-2">
              {/* Root folder */}
              <FolderItem
                name="Root"
                path="root"
                files={jsonFiles}
                folders={rootData.folders}
                isExpanded={expandedFolders.has("root")}
                onToggle={() => toggleFolder("root")}
                onFileClick={fetchFileContent}
                selectedFile={selectedFile}
                sessionId={sessionId}
                expandedFolders={expandedFolders}
                setExpandedFolders={setExpandedFolders}
              />
            </div>
          </ScrollArea>
        </div>
      </ResizablePanel>

      <ResizableHandle />

      {/* Right: File content viewer */}
      <ResizablePanel defaultSize={70} minSize={30}>
        <div className="flex h-full min-h-0 flex-col">
          <div className="shrink-0 border-b p-3">
            <div className="flex items-center justify-between">
              <div className="min-w-0 flex-1">
                <h3 className="truncate font-semibold">
                  {selectedFile ? selectedFile.name : "Select a file"}
                </h3>
                {selectedFile && (
                  <p className="text-muted-foreground text-xs">
                    {(selectedFile.size / 1024).toFixed(2)} KB
                  </p>
                )}
              </div>
              {selectedFile && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => downloadFile(selectedFile)}
                  className="ml-2 shrink-0"
                >
                  <Download className="mr-2 size-4" />
                  Download
                </Button>
              )}
            </div>
          </div>
          <div className="min-h-0 flex-1 overflow-auto p-4">
            {!selectedFile ? (
              <div className="text-muted-foreground text-center">
                Select a JSON file to view its content
              </div>
            ) : (
              (() => {
                const fileContent = fileContents[selectedFile.key];
                if (fileContent?.loading) {
                  return (
                    <div className="space-y-2">
                      {Array.from({ length: 10 }).map((_, i) => (
                        <Skeleton key={i} className="h-4 w-full" />
                      ))}
                    </div>
                  );
                }
                if (fileContent?.error) {
                  return (
                    <div className="text-destructive">
                      Error: {fileContent.error}
                    </div>
                  );
                }
                return (
                  <pre className="bg-muted rounded-lg p-4 text-xs whitespace-pre">
                    {JSON.stringify(selectedFile.content, null, 2)}
                  </pre>
                );
              })()
            )}
          </div>
        </div>
      </ResizablePanel>
    </ResizablePanelGroup>
  );
}

interface FolderItemProps {
  name: string;
  path: string;
  files: JsonFile[];
  folders: Array<{ name: string; path: string }>;
  isExpanded: boolean;
  onToggle: () => void;
  onFileClick: (file: JsonFile) => void;
  selectedFile: JsonFile | null;
  sessionId: string;
  expandedFolders: Set<string>;
  setExpandedFolders: React.Dispatch<React.SetStateAction<Set<string>>>;
}

function FolderItem({
  name,
  path,
  files,
  folders,
  isExpanded,
  onToggle,
  onFileClick,
  selectedFile,
  sessionId,
  expandedFolders,
  setExpandedFolders,
}: FolderItemProps) {
  return (
    <div>
      <button
        onClick={onToggle}
        className="hover:bg-accent flex w-full items-center gap-2 rounded px-2 py-1.5"
      >
        {isExpanded ? (
          <ChevronDown className="size-4" />
        ) : (
          <ChevronRight className="size-4" />
        )}
        <Folder className="size-4 text-blue-500" />
        <span className="text-sm font-medium">{name}</span>
        <Badge variant="secondary" className="ml-auto text-xs">
          {files.length + folders.length}
        </Badge>
      </button>

      {isExpanded && (
        <div className="mt-1 ml-4 space-y-0.5">
          {/* Render subfolders */}
          {folders.map((folder) => (
            <SubFolder
              key={folder.path}
              folder={folder}
              sessionId={sessionId}
              expandedFolders={expandedFolders}
              setExpandedFolders={setExpandedFolders}
              onFileClick={onFileClick}
              selectedFile={selectedFile}
            />
          ))}

          {/* Render files */}
          {files.map((file) => (
            <button
              key={file.key}
              onClick={() => onFileClick(file)}
              className={cn(
                "hover:bg-accent flex w-full items-center gap-2 rounded px-2 py-1.5 text-left",
                selectedFile?.key === file.key && "bg-accent",
              )}
            >
              <FileJson className="size-4 text-orange-500" />
              <span className="truncate text-sm">{file.name}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

interface SubFolderProps {
  folder: { name: string; path: string };
  sessionId: string;
  expandedFolders: Set<string>;
  setExpandedFolders: React.Dispatch<React.SetStateAction<Set<string>>>;
  onFileClick: (file: JsonFile) => void;
  selectedFile: JsonFile | null;
}

function SubFolder({
  folder,
  sessionId,
  expandedFolders,
  setExpandedFolders,
  onFileClick,
  selectedFile,
}: SubFolderProps) {
  const isExpanded = expandedFolders.has(folder.path);

  // Extract the subfolder path relative to session
  const subfolderPath = folder.path
    .split("/")
    .slice(3) // Remove users/{userId}/{sessionId}/
    .join("/")
    .replace(/\/$/, "");

  const { data } = api.storage.listSessionDirectory.useQuery(
    {
      sessionId,
      subfolder: subfolderPath,
    },
    {
      enabled: isExpanded && !!sessionId,
    },
  );

  const toggleFolder = () => {
    setExpandedFolders((prev) => {
      const next = new Set(prev);
      if (next.has(folder.path)) {
        next.delete(folder.path);
      } else {
        next.add(folder.path);
      }
      return next;
    });
  };

  const jsonFiles =
    data?.files.filter((f) => f.name.toLowerCase().endsWith(".json")) ?? [];

  return (
    <div>
      <button
        onClick={toggleFolder}
        className="hover:bg-accent flex w-full items-center gap-2 rounded px-2 py-1.5"
      >
        {isExpanded ? (
          <ChevronDown className="size-4" />
        ) : (
          <ChevronRight className="size-4" />
        )}
        <Folder className="size-4 text-blue-500" />
        <span className="text-sm">{folder.name}</span>
        {isExpanded && data && (
          <Badge variant="secondary" className="ml-auto text-xs">
            {jsonFiles.length + (data.folders?.length || 0)}
          </Badge>
        )}
      </button>

      {isExpanded && data && (
        <div className="mt-1 ml-4 space-y-0.5">
          {/* Render subfolders recursively */}
          {data.folders?.map((subfolder) => (
            <SubFolder
              key={subfolder.path}
              folder={subfolder}
              sessionId={sessionId}
              expandedFolders={expandedFolders}
              setExpandedFolders={setExpandedFolders}
              onFileClick={onFileClick}
              selectedFile={selectedFile}
            />
          ))}

          {/* Render JSON files */}
          {jsonFiles.map((file) => (
            <button
              key={file.key}
              onClick={() => onFileClick(file)}
              className={cn(
                "hover:bg-accent flex w-full items-center gap-2 rounded px-2 py-1.5 text-left",
                selectedFile?.key === file.key && "bg-accent",
              )}
            >
              <FileJson className="size-4 text-orange-500" />
              <span className="truncate text-sm">{file.name}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
