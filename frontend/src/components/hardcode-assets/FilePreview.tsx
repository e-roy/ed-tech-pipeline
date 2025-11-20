"use client";

import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Download, FileText, Image as ImageIcon } from "lucide-react";
import Image from "next/image";
import { formatBytes } from "@/components/content/utils";
import { useState, useEffect } from "react";
import { Skeleton } from "@/components/ui/skeleton";

interface FilePreviewProps {
  file: {
    key: string;
    name: string;
    size: number;
    last_modified: string | null;
    content_type: string;
    presigned_url: string;
  };
}

export function FilePreview({ file }: FilePreviewProps) {
  const [textContent, setTextContent] = useState<string | null>(null);
  const [isLoadingText, setIsLoadingText] = useState(false);
  const isImage = file.content_type.startsWith("image/");
  const isText =
    file.content_type.startsWith("text/") ||
    file.name.endsWith(".md") ||
    file.name.endsWith(".json") ||
    file.name.endsWith(".txt");

  useEffect(() => {
    if (isText && !textContent && !isLoadingText) {
      setIsLoadingText(true);
      fetch(file.presigned_url)
        .then((res) => res.text())
        .then((text) => {
          setTextContent(text);
        })
        .catch((err) => {
          console.error("Failed to load text content:", err);
          setTextContent("Failed to load file content");
        })
        .finally(() => {
          setIsLoadingText(false);
        });
    }
  }, [file.presigned_url, isText, textContent, isLoadingText]);

  const handleDownload = () => {
    const link = document.createElement("a");
    link.href = file.presigned_url;
    link.download = file.name;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "Unknown";
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return dateString;
    }
  };

  return (
    <Card className="p-4 h-fit sticky top-4">
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-semibold mb-2 truncate" title={file.name}>
            {file.name}
          </h3>
          <div className="space-y-1 text-sm text-muted-foreground">
            <div>Size: {formatBytes(file.size)}</div>
            <div>Type: {file.content_type}</div>
            <div>Modified: {formatDate(file.last_modified)}</div>
          </div>
        </div>

        <Button
          onClick={handleDownload}
          className="w-full"
          variant="outline"
        >
          <Download className="h-4 w-4 mr-2" />
          Download
        </Button>

        <div className="border-t pt-4">
          {isImage ? (
            <div className="relative w-full aspect-video bg-muted rounded-lg overflow-hidden">
              <Image
                src={file.presigned_url}
                alt={file.name}
                fill
                className="object-contain"
                unoptimized
              />
            </div>
          ) : isText ? (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <FileText className="h-4 w-4" />
                <span>Text Preview</span>
              </div>
              {isLoadingText ? (
                <Skeleton className="h-32 w-full" />
              ) : (
                <div className="bg-muted rounded-lg p-3 max-h-96 overflow-auto">
                  <pre className="text-xs whitespace-pre-wrap font-mono">
                    {textContent ?? "Loading..."}
                  </pre>
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
              <ImageIcon className="h-12 w-12 mb-2 opacity-50" />
              <p className="text-sm">Preview not available</p>
              <p className="text-xs mt-1">Download to view file</p>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}

