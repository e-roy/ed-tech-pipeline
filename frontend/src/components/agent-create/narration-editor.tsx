"use client";

import { type NarrationSegment } from "@/types";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Clock,
  BookOpen,
  Hash,
  FilmIcon,
  Wifi,
  WifiOff,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Video,
} from "lucide-react";
import { useAgentCreateStore } from "@/stores/agent-create-store";
import { useWebSocket } from "@/hooks/useWebSocket";
import { Button } from "@/components/ui/button";

export function NarrationEditor() {
  const { narration, setNarration, sessionId, isVideoGenerating } =
    useAgentCreateStore();

  // WebSocket connection for video generation progress
  // Only connect when video generation has actually started
  const { isConnected, lastMessage } = useWebSocket(
    isVideoGenerating ? sessionId : null,
  );

  if (!narration) return null;

  const handleSegmentChange = (
    index: number,
    field: keyof NarrationSegment,
    value: string | number | string[],
  ) => {
    const newSegments = [...narration.segments];
    newSegments[index] = {
      ...newSegments[index],
      [field]: value,
    } as NarrationSegment;
    setNarration({
      ...narration,
      segments: newSegments,
    });
  };

  // Determine video generation status
  const hasVideoGenerationStarted = lastMessage !== null;
  const isVideoInProgress =
    lastMessage && !lastMessage.video_url && !lastMessage.error;
  const isVideoComplete = lastMessage?.video_url !== undefined;
  const hasError = lastMessage?.error !== undefined;

  return (
    <div className="flex h-full flex-col">
      <div className="bg-muted/50 mb-4 rounded-lg border p-3">
        <div className="mb-2 flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <FilmIcon className="text-muted-foreground size-4" />
            <h3 className="text-sm font-semibold">Script Information</h3>
          </div>
          {sessionId && (
            <div className="flex items-center gap-1">
              {isConnected ? (
                <Wifi className="size-3 text-green-500" />
              ) : (
                <WifiOff className="size-3 text-gray-400" />
              )}
              <span className="text-muted-foreground text-xs">
                {isConnected ? "Connected" : "Offline"}
              </span>
            </div>
          )}
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge variant="secondary" className="text-xs">
            <Clock className="mr-1 size-3" />
            Total Duration: {narration.total_duration}s
          </Badge>
          <Badge variant="secondary" className="text-xs">
            <BookOpen className="mr-1 size-3" />
            Reading Level: {narration.reading_level}
          </Badge>
          <Badge variant="secondary" className="text-xs">
            <Hash className="mr-1 size-3" />
            Key Terms: {narration.key_terms_count}
          </Badge>
        </div>
      </div>

      {/* Video Generation Progress */}
      {hasVideoGenerationStarted && (
        <div className="mb-4">
          {isVideoInProgress && (
            <Alert>
              <Loader2 className="h-4 w-4 animate-spin" />
              <AlertDescription>
                <div className="space-y-2">
                  {lastMessage.progress && (
                    <>
                      <div className="flex items-center justify-between">
                        <span className="font-medium">
                          {lastMessage.progress.stage}
                          {lastMessage.progress.section &&
                            ` (${lastMessage.progress.section})`}
                        </span>
                        <span className="text-muted-foreground text-xs">
                          {Math.round(
                            (lastMessage.progress.completed /
                              lastMessage.progress.total) *
                              100,
                          )}
                          %
                        </span>
                      </div>
                      <Progress
                        value={
                          (lastMessage.progress.completed /
                            lastMessage.progress.total) *
                          100
                        }
                        className="h-2"
                      />
                    </>
                  )}
                  <p className="text-muted-foreground text-xs">
                    {lastMessage.message}
                  </p>
                  {lastMessage.cost > 0 && (
                    <p className="text-muted-foreground text-xs">
                      Current cost: ${lastMessage.cost.toFixed(2)}
                    </p>
                  )}
                </div>
              </AlertDescription>
            </Alert>
          )}

          {isVideoComplete && (
            <Alert className="border-green-500 bg-green-50">
              <CheckCircle2 className="h-4 w-4 text-green-600" />
              <AlertDescription>
                <div className="space-y-2">
                  <p className="font-medium text-green-900">
                    Video generation complete!
                  </p>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() =>
                        window.open(lastMessage.video_url, "_blank")
                      }
                    >
                      <Video className="mr-2 h-4 w-4" />
                      View Video
                    </Button>
                  </div>
                </div>
              </AlertDescription>
            </Alert>
          )}

          {hasError && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                <p className="font-medium">Video generation failed</p>
                <p className="mt-1 text-xs">{lastMessage.error}</p>
              </AlertDescription>
            </Alert>
          )}
        </div>
      )}

      <ScrollArea className="max-h-[calc(100vh-28rem)] flex-1">
        <div className="flex flex-col gap-4">
          {narration.segments.map((segment, index) => (
            <Card key={segment.id} className="mt-0 overflow-hidden pt-0">
              <CardHeader className="bg-muted/50 px-4 py-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="bg-background">
                      {index + 1}
                    </Badge>
                    <CardTitle className="text-sm font-medium">
                      {segment.type
                        .split("_")
                        .map(
                          (word) =>
                            word.charAt(0).toUpperCase() + word.slice(1),
                        )
                        .join(" ")}
                    </CardTitle>
                  </div>
                  <div className="text-muted-foreground flex items-center gap-2 text-xs">
                    <Clock className="size-3" />
                    <span>{segment.duration}s</span>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="grid gap-4 px-4">
                <div className="space-y-1.5">
                  <Label
                    htmlFor={`narration-${segment.id}`}
                    className="text-muted-foreground text-xs font-medium"
                  >
                    Narration
                  </Label>
                  <Textarea
                    id={`narration-${segment.id}`}
                    value={segment.narration}
                    onChange={(e) =>
                      handleSegmentChange(index, "narration", e.target.value)
                    }
                    className="bg-background min-h-[80px] resize-none text-sm"
                  />
                </div>

                <div className="space-y-1.5">
                  <Label
                    htmlFor={`visual-${segment.id}`}
                    className="text-muted-foreground text-xs font-medium"
                  >
                    Visual Guidance
                  </Label>
                  <Textarea
                    id={`visual-${segment.id}`}
                    value={segment.visual_guidance}
                    onChange={(e) =>
                      handleSegmentChange(
                        index,
                        "visual_guidance",
                        e.target.value,
                      )
                    }
                    className="bg-background min-h-[60px] resize-none text-sm"
                  />
                </div>

                <div className="flex flex-wrap items-center gap-2 border-t pt-2">
                  <span className="text-muted-foreground text-xs font-medium">
                    Concepts:
                  </span>
                  <div className="flex flex-wrap gap-1">
                    {segment.key_concepts.map((concept, i) => (
                      <Badge
                        key={i}
                        variant="secondary"
                        className="h-5 px-1.5 text-[10px]"
                      >
                        {concept}
                      </Badge>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}
