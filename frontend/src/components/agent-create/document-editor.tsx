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
import { useState, type HTMLAttributes } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { NarrationEditor } from "./narration-editor";
import { FactsView } from "./facts-view";
import { VideoView } from "./video-view";
import { DebugView } from "./debug-view";
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
    showFactSelectionPrompt,
    thinkingStatus,
    toggleFact,
    handleSubmitFacts,
    sessionId,
    isVideoGenerating,
  } = useAgentCreateStore();

  const [viewMode, setViewMode] = useState<ViewMode>("script");
  const { data: session } = useSession();
  const isAdmin = (session?.user as { role?: string })?.role === "admin";

  // Poll S3 for final video in users/{userId}/{sessionId}/final/
  // Poll every 60 seconds while video is generating, otherwise check once
  // eslint-disable-next-line @typescript-eslint/no-explicit-any, @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
  const { data: sessionFiles } = (api.storage as any).listSessionFiles.useQuery(
    {
      sessionId: sessionId ?? "",
      subfolder: "final",
    },
    {
      enabled: !!sessionId,
      refetchInterval: isVideoGenerating ? 60000 : false, // Poll every 60s while generating
      refetchOnWindowFocus: true,
    },
  ) as {
    data:
      | Array<{
          key: string;
          name: string;
          size: number;
          last_modified: string | null;
          content_type: string;
          presigned_url: string;
        }>
      | undefined;
  };

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

  const mode =
    workflowStep === "selection"
      ? "select-facts"
      : workflowStep === "review"
        ? "edit-narration"
        : "edit";

  // Show toggle buttons when both confirmed facts and script exist, or if admin
  const hasConfirmedFacts = selectedFacts.length > 0;
  const hasScript = narration !== null;
  const showToggleButtons =
    (hasConfirmedFacts && hasScript && mode !== "select-facts") || isAdmin;

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
      <div className="flex items-center gap-2 border-b px-4 py-3">
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
        ) : null}
        {isLoading && (
          <span className="text-muted-foreground ml-auto text-xs">
            Updating...
          </span>
        )}
        {mode === "select-facts" && !showFactSelectionPrompt && (
          <Button
            size="sm"
            onClick={handleSubmitFacts}
            className="ml-auto"
            disabled={selectedFacts.length === 0 || isLoading}
          >
            Submit Selected Facts ({selectedFacts.length})
          </Button>
        )}
      </div>
      <ScrollArea className="max-h-[calc(100vh-60px)] flex-1">
        <div className="h-full p-4">
          {hasStudentInfo && viewMode !== "debug" && (
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
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
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
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
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
                      Confidence: {Math.round(fact.confidence * 100)}%
                    </div>
                  </div>
                );
              })}
            </div>
          ) : !isExtractingFacts && showToggleButtons ? (
            viewMode === "facts" ? (
              <FactsView facts={selectedFacts} />
            ) : viewMode === "script" ? (
              narration && <NarrationEditor />
            ) : viewMode === "debug" ? (
              sessionId && <DebugView sessionId={sessionId} />
            ) : (
              <VideoView
                videoUrl={finalVideo?.presigned_url}
                isLoading={isVideoGenerating}
                sessionId={sessionId ?? undefined}
              />
            )
          ) : (
            !isExtractingFacts && narration && <NarrationEditor />
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
