"use client";

import { useState, useEffect, useRef } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Download, Scissors, ArrowLeft, Loader2, TestTube } from "lucide-react";
import { api } from "@/trpc/react";
import { EditorLayout } from "@/components/video-editor/EditorLayout";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// Hardcoded test video S3 key for testing purposes
const TEST_VIDEO_S3_KEY =
  "users/f218067b-e198-45ae-888a-cf45979bc57d/kYd20Q5WaK-b27v31a1eE/final_video_dae6d4f1.mp4";

interface EditingPageClientProps {
  sessionId: string;
  userEmail: string;
}

interface SessionData {
  id: string;
  status: string;
  prompt: string | null;
  video_prompt: string | null;
  final_video_url: string | null;
  created_at: string;
  completed_at: string | null;
}

interface VideoMetadata {
  duration: number;
  width: number;
  height: number;
}

export function EditingPageClient({
  sessionId,
  userEmail,
}: EditingPageClientProps) {
  const searchParams = useSearchParams();
  const videoUrlFromQuery = searchParams.get("videoUrl");
  const autoEdit = searchParams.get("autoEdit") === "true";

  const [sessionData, setSessionData] = useState<SessionData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [videoMetadata, setVideoMetadata] = useState<VideoMetadata | null>(
    null,
  );
  const [useTestVideo, setUseTestVideo] = useState(false);
  const [testVideoUrl, setTestVideoUrl] = useState<string | null>(null);
  const [isEditorMode, setIsEditorMode] = useState(autoEdit);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);

  // tRPC query for test video presigned URL
  const testVideoQuery = api.storage.getPresignedUrl.useQuery(
    {
      file_key: TEST_VIDEO_S3_KEY,
      expires_in: 3600,
    },
    {
      enabled: useTestVideo,
    },
  );

  // Handle test video query result
  useEffect(() => {
    if (testVideoQuery.data) {
      setTestVideoUrl(testVideoQuery.data.presigned_url);
      setIsLoading(false);
      // Stop polling when using test video
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    }
    if (testVideoQuery.error) {
      setError(`Failed to load test video: ${testVideoQuery.error.message}`);
      setIsLoading(false);
    }
  }, [testVideoQuery.data, testVideoQuery.error]);

  // Polling logic to fetch session data
  useEffect(() => {
    // Skip polling if we have video URL from query params (agent-create flow)
    if (videoUrlFromQuery) {
      setIsLoading(false);
      console.log("[EditingPage] Using video URL from query params");
      return;
    }

    const fetchSession = async () => {
      try {
        const response = await fetch(`${API_URL}/api/sessions/${sessionId}`, {
          headers: {
            "X-User-Email": userEmail,
          },
        });

        if (!response.ok) {
          // Don't treat 404 as error - session may not exist yet or we're in test mode
          if (response.status === 404) {
            // Just continue polling, don't set error
            return;
          }
          throw new Error(`Failed to fetch session: ${response.status}`);
        }

        const data = (await response.json()) as SessionData;
        setSessionData(data);

        // Stop polling when video is ready
        if (data.final_video_url && pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
          setIsLoading(false);
        }
      } catch (err) {
        // Don't set error for network failures - just continue polling
        // This allows the test button to remain visible when backend is down
        console.log("[EditingPage] Fetch error (backend may be down):", err);
        // Don't setError or setIsLoading(false) - keep showing processing state with test button
      }
    };

    // Initial fetch
    void fetchSession();

    // Start polling every 3 seconds
    pollIntervalRef.current = setInterval(() => {
      void fetchSession();
    }, 3000);

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, [sessionId, userEmail, videoUrlFromQuery]);

  // Handle video metadata loaded
  const handleVideoMetadata = () => {
    if (videoRef.current) {
      setVideoMetadata({
        duration: videoRef.current.duration,
        width: videoRef.current.videoWidth,
        height: videoRef.current.videoHeight,
      });
    }
  };

  // Handle download
  const handleDownload = () => {
    const videoUrl =
      videoUrlFromQuery ?? testVideoUrl ?? sessionData?.final_video_url;
    if (!videoUrl) return;

    const link = document.createElement("a");
    link.href = videoUrl;
    link.download = `video-${sessionId}.mp4`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Handle loading test video
  const handleLoadTestVideo = () => {
    setUseTestVideo(true);
    setError(null);
  };

  // Get the current video URL (prioritize: query param > test video > session)
  const currentVideoUrl =
    videoUrlFromQuery ?? testVideoUrl ?? sessionData?.final_video_url;

  // Format duration to MM:SS
  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  // Editor mode - render the full video editor
  if (isEditorMode) {
    const videoUrl =
      videoUrlFromQuery ?? testVideoUrl ?? sessionData?.final_video_url;
    return (
      <EditorLayout sessionId={sessionId} videoUrl={videoUrl ?? undefined} />
    );
  }

  // Error state
  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-destructive">Error</CardTitle>
          <CardDescription>{error}</CardDescription>
        </CardHeader>
        <CardContent>
          <Link href="/dashboard/hardcode-create">
            <Button variant="outline">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Create
            </Button>
          </Link>
        </CardContent>
      </Card>
    );
  }

  // Processing state (polling for video)
  if (isLoading || !currentVideoUrl) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Processing Video</CardTitle>
          <CardDescription>
            Your video is being processed. This page will automatically update
            when it&apos;s ready.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col items-center justify-center py-12">
          <Loader2 className="text-primary mb-4 h-12 w-12 animate-spin" />
          <p className="text-muted-foreground text-sm">
            Video is still processing...
          </p>
          {sessionData?.status && (
            <p className="text-muted-foreground mt-2 text-xs">
              Status: {sessionData.status}
            </p>
          )}

          {/* Test Video Button */}
          <div className="mt-6 w-full max-w-sm border-t pt-6">
            <p className="text-muted-foreground mb-3 text-center text-xs">
              For testing purposes only:
            </p>
            <Button
              variant="outline"
              onClick={handleLoadTestVideo}
              disabled={useTestVideo && testVideoQuery.isLoading}
              className="w-full"
            >
              {useTestVideo && testVideoQuery.isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Loading Test Video...
                </>
              ) : (
                <>
                  <TestTube className="mr-2 h-4 w-4" />
                  Load Test Video
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Video ready state - currentVideoUrl is guaranteed to be non-null here due to the check above
  const videoUrl = currentVideoUrl;

  return (
    <div className="flex h-full flex-col gap-4 overflow-hidden">
      {/* Video Player Card - takes most of the space */}
      <Card className="flex min-h-0 flex-1 flex-col">
        <CardHeader className="shrink-0 py-3">
          <CardTitle>Your Video</CardTitle>
          <CardDescription>
            {testVideoUrl ? "Test Video" : `Session ID: ${sessionId}`}
          </CardDescription>
        </CardHeader>
        <CardContent className="min-h-0 flex-1 pb-3">
          <div className="bg-muted/50 flex h-full items-center justify-center overflow-hidden rounded-lg border">
            <video
              ref={videoRef}
              controls
              className="max-h-full max-w-full object-contain"
              src={videoUrl}
              preload="metadata"
              onLoadedMetadata={handleVideoMetadata}
            >
              Your browser does not support the video tag.
            </video>
          </div>
        </CardContent>
      </Card>

      {/* Bottom section: Video Details + Actions */}
      <div className="flex shrink-0 flex-wrap items-center justify-between gap-4">
        {/* Video Metadata - inline */}
        {videoMetadata && (
          <div className="flex items-center gap-6 text-sm">
            <div>
              <span className="text-muted-foreground">Duration: </span>
              <span className="text-foreground font-medium">
                {formatDuration(videoMetadata.duration)}
              </span>
            </div>
            <div>
              <span className="text-muted-foreground">Resolution: </span>
              <span className="text-foreground font-medium">
                {videoMetadata.width} x {videoMetadata.height}
              </span>
            </div>
            {sessionData?.created_at && (
              <div>
                <span className="text-muted-foreground">Created: </span>
                <span className="text-foreground font-medium">
                  {new Date(sessionData.created_at).toLocaleDateString()}
                </span>
              </div>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="flex flex-wrap gap-3">
          <Button onClick={handleDownload}>
            <Download className="mr-2 h-4 w-4" />
            Download Video
          </Button>

          <Button
            variant="outline"
            onClick={() => setIsEditorMode(true)}
            className="border-primary text-primary hover:bg-primary hover:text-primary-foreground"
          >
            <Scissors className="mr-2 h-4 w-4" />
            Open Editor
          </Button>

          <Link href="/dashboard/hardcode-create">
            <Button
              variant="outline"
              className="border-primary text-primary hover:bg-primary hover:text-primary-foreground"
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Create
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
