"use client";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Download, ExternalLink, VideoIcon, Film } from "lucide-react";
import { useRouter } from "next/navigation";

interface VideoViewProps {
  videoUrl?: string;
  isLoading?: boolean;
  sessionId?: string;
}

export function VideoView({ videoUrl, isLoading, sessionId }: VideoViewProps) {
  const router = useRouter();

  if (isLoading) {
    return (
      <div className="flex flex-col gap-4">
        <Skeleton className="h-[400px] w-full rounded-lg" />
        <div className="flex gap-2">
          <Skeleton className="h-10 w-32" />
          <Skeleton className="h-10 w-32" />
        </div>
      </div>
    );
  }

  if (!videoUrl) {
    return (
      <Alert>
        <VideoIcon className="size-4" />
        <AlertDescription>
          No video generated yet. The video will appear here once generation is
          complete.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="bg-muted/50 overflow-hidden rounded-lg border">
        <video
          controls
          className="h-auto w-full"
          src={videoUrl}
          preload="metadata"
        >
          Your browser does not support the video tag.
        </video>
      </div>
      <div className="flex gap-2">
        {sessionId && videoUrl && (
          <Button
            size="sm"
            variant="default"
            onClick={() =>
              router.push(
                `/dashboard/editing/${sessionId}?videoUrl=${encodeURIComponent(videoUrl)}&autoEdit=true`,
              )
            }
          >
            <Film className="mr-2 size-4" />
            Edit Video
          </Button>
        )}
        <Button
          size="sm"
          variant="outline"
          onClick={() => window.open(videoUrl, "_blank")}
        >
          <ExternalLink className="mr-2 size-4" />
          Open in New Tab
        </Button>
        <Button
          size="sm"
          variant="outline"
          onClick={() => {
            const link = document.createElement("a");
            link.href = videoUrl;
            link.download = "final-video.mp4";
            link.click();
          }}
        >
          <Download className="mr-2 size-4" />
          Download
        </Button>
      </div>
    </div>
  );
}

