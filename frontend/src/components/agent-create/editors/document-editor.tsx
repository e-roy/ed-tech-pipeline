"use client";

import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import {
  FileTextIcon,
  CheckCircle2,
  Circle,
  ListChecks,
  FileText,
  User,
  Video,
  Settings,
} from "lucide-react";
import { useState, useEffect, type HTMLAttributes } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { NarrationEditor } from "./narration-editor";
import { FactsView } from "../views/facts-view";
import { VideoView } from "../views/video-view";
import { DebugView } from "../views/debug-view";
import { useAgentCreateStore } from "@/stores/agent-create-store";
import { api } from "@/trpc/react";
import { useSession } from "next-auth/react";

export type DocumentEditorProps = HTMLAttributes<HTMLDivElement>;

type ViewMode = "facts" | "script" | "video" | "debug";

export function DocumentEditor({ className, ...props }: DocumentEditorProps) {
  const {
    isLoading,
    workflowStep,
    facts,
    selectedFacts,
    narration,
    factsLocked,
    childAge,
    childInterest,
    thinkingStatus,
    toggleFact,
    sessionId,
    isVideoGenerating,
    setIsVideoGenerating,
  } = useAgentCreateStore();

  const [viewMode, setViewMode] = useState<ViewMode>("script");
  const { data: session } = useSession();
  const isAdmin = (session?.user as { role?: string })?.role === "admin";

  // Poll S3 for final video in users/{userId}/{sessionId}/final/
  // Poll every 60 seconds while video is generating, otherwise check once
  const { data: sessionFiles } = api.storage.listSessionFiles.useQuery(
    {
      sessionId: sessionId ?? "",
      subfolder: "final",
    },
    {
      enabled: !!sessionId,
      refetchInterval: isVideoGenerating ? 60000 : false, // Poll every 60s while generating
      refetchOnWindowFocus: true,
    },
  );

  // Get the most recent video file from the final folder
  const finalVideo =
    sessionFiles && sessionFiles.length > 0
      ? [...sessionFiles]
          .filter((file) => !file.key.endsWith("/")) // Exclude directory markers
          .sort((a, b) => {
            // Sort by last_modified descending (newest first)
            const dateA = a.last_modified
              ? new Date(a.last_modified).getTime()
              : 0;
            const dateB = b.last_modified
              ? new Date(b.last_modified).getTime()
              : 0;
            return dateB - dateA;
          })[0]
      : undefined;

  // Fetch selected diagrams from diagrams folder
  const { data: diagramFiles, isLoading: isLoadingDiagrams } =
    api.storage.listSessionFiles.useQuery(
      {
        sessionId: sessionId ?? "",
        subfolder: "diagrams",
      },
      {
        enabled: !!sessionId && !!narration, // Only fetch after narration is created
        refetchInterval: narration && !factsLocked ? 30000 : false, // Poll every 30s until facts are locked
        refetchOnWindowFocus: true,
      },
    );

  // Poll webhook table for video completion (backup check)
  const { data: webhookLog } = api.storage.checkVideoWebhook.useQuery(
    {
      sessionId: sessionId ?? "",
    },
    {
      enabled: !!sessionId && isVideoGenerating,
      refetchInterval: 10000, // Check every 10s while generating
      refetchOnWindowFocus: true,
    },
  );

  // Update video generation state based on webhook status
  useEffect(() => {
    if (
      webhookLog?.eventType === "video_complete" ||
      webhookLog?.eventType === "video_failed"
    ) {
      setIsVideoGenerating(false);
    }
  }, [webhookLog, setIsVideoGenerating]);

  const mode =
    workflowStep === "selection"
      ? "select-facts"
      : workflowStep === "review"
        ? "edit-narration"
        : "edit";

  // Show toggle buttons when both confirmed facts and script exist
  const hasConfirmedFacts = selectedFacts.length > 0;
  const hasScript = narration !== null;
  const showToggleButtons =
    hasConfirmedFacts && hasScript && mode !== "select-facts";

  // Check if we have student info
  const hasStudentInfo = childAge ?? childInterest;

  // Check if we're currently extracting facts
  const isExtractingFacts =
    isLoading && thinkingStatus?.operation === "extracting";

  return (
    <div
      className={cn("bg-background flex h-full flex-col border-l", className)}
      {...props}
    >
      <div className="flex h-15 items-center gap-2 border-b px-4 py-3">
        <FileTextIcon className="text-muted-foreground size-5" />
        {showToggleButtons ? (
          <div className="flex items-center gap-2">
            <Button
              variant={viewMode === "facts" ? "default" : "ghost"}
              size="sm"
              onClick={() => setViewMode("facts")}
              className="h-8"
            >
              <ListChecks className="mr-2 size-4" />
              Facts ({selectedFacts.length})
            </Button>
            <Button
              variant={viewMode === "script" ? "default" : "ghost"}
              size="sm"
              onClick={() => setViewMode("script")}
              className="h-8"
            >
              <FileText className="mr-2 size-4" />
              Script
            </Button>
            <Button
              variant={viewMode === "video" ? "default" : "ghost"}
              size="sm"
              onClick={() => setViewMode("video")}
              className="h-8"
            >
              <Video className="mr-2 size-4" />
              Video
            </Button>
          </div>
        ) : null}
        {isAdmin && (
          <Button
            variant={viewMode === "debug" ? "default" : "ghost"}
            size="sm"
            onClick={() => setViewMode("debug")}
            className="h-8"
          >
            <Settings className="mr-2 size-4" />
            Debug
          </Button>
        )}
      </div>
      {/* Debug view needs its own layout (not inside ScrollArea) */}
      {viewMode === "debug" && sessionId ? (
        <div className="min-h-0 flex-1">
          <DebugView sessionId={sessionId} />
        </div>
      ) : (
        <ScrollArea className="max-h-[calc(100vh-60px)] flex-1">
          <div className="h-full p-4">
            {hasStudentInfo && (
              <div className="bg-muted/50 mb-4 rounded-lg border p-3">
                <div className="mb-2 flex items-center gap-2">
                  <User className="text-muted-foreground size-4" />
                  <h3 className="text-sm font-semibold">Student Information</h3>
                </div>
                <div className="flex flex-wrap gap-2">
                  {childAge && (
                    <Badge variant="secondary" className="text-xs">
                      Age: {childAge}
                    </Badge>
                  )}
                  {childInterest && (
                    <Badge variant="secondary" className="text-xs">
                      Interest: {childInterest}
                    </Badge>
                  )}
                </div>
              </div>
            )}

          {/* Loading state: Show skeleton cards while extracting facts */}
          {isExtractingFacts && (
            <div className="grid auto-rows-fr grid-cols-[repeat(auto-fill,minmax(250px,1fr))] gap-4">
              {Array.from({ length: 6 }).map((_, index) => (
                <div
                  key={index}
                  className="border-border bg-card rounded-lg border p-4"
                >
                  <div className="mb-2 flex items-start justify-between gap-2">
                    <Skeleton className="h-5 w-3/4" />
                    <Skeleton className="size-4 rounded-full" />
                  </div>
                  <div className="space-y-2">
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-5/6" />
                    <Skeleton className="h-4 w-4/6" />
                  </div>
                  <Skeleton className="mt-2 h-3 w-24" />
                </div>
              ))}
            </div>
          )}

          {!isExtractingFacts && mode === "edit" ? (
            <div className="text-muted-foreground text-sm">
              Start a conversation to share lesson materials. You can optionally
              provide student age and interests for personalization.
            </div>
          ) : !isExtractingFacts && mode === "select-facts" ? (
            <div className="grid auto-rows-fr grid-cols-[repeat(auto-fill,minmax(250px,1fr))] gap-4">
              {(factsLocked ? selectedFacts : facts).map((fact, index) => {
                const isSelected = selectedFacts.some(
                  (f) => f.concept === fact.concept,
                );
                return (
                  <div
                    key={index}
                    onClick={() => !factsLocked && toggleFact(fact)}
                    className={cn(
                      "rounded-lg border p-4 transition-all",
                      factsLocked
                        ? "cursor-default opacity-75"
                        : "hover:bg-accent cursor-pointer",
                      isSelected
                        ? "border-primary bg-accent"
                        : "border-border bg-card",
                    )}
                  >
                    <div className="mb-2 flex items-start justify-between gap-2">
                      <h3 className="text-sm font-semibold">{fact.concept}</h3>
                      {isSelected ? (
                        <CheckCircle2 className="text-primary size-4" />
                      ) : (
                        <Circle className="text-muted-foreground size-4" />
                      )}
                    </div>
                    <p className="text-muted-foreground text-sm">
                      {fact.details}
                    </p>
                    <div className="text-muted-foreground mt-2 text-xs">
                      Confidence:{" "}
                      {typeof fact.confidence === "number" &&
                      !isNaN(fact.confidence) &&
                      fact.confidence >= 0 &&
                      fact.confidence <= 1
                        ? `${Math.round(fact.confidence * 100)}%`
                        : "N/A"}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : !isExtractingFacts && showToggleButtons ? (
            viewMode === "facts" ? (
              <FactsView
                facts={selectedFacts}
                diagrams={diagramFiles ?? []}
                isLoadingDiagrams={isLoadingDiagrams}
              />
            ) : viewMode === "script" ? (
              narration && <NarrationEditor />
            ) : (
              <VideoView
                videoUrl={finalVideo?.presigned_url}
                isLoading={isVideoGenerating && !finalVideo?.presigned_url}
                sessionId={sessionId ?? undefined}
              />
            )
          ) : (
            !isExtractingFacts && narration && <NarrationEditor />
          )}
          </div>
        </ScrollArea>
      )}
    </div>
  );
}
