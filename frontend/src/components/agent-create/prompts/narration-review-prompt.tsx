"use client";

import { Message, MessageContent } from "@/components/ai-elements/message";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { CheckCircle2 } from "lucide-react";
import type { Narration } from "@/types";

interface NarrationReviewPromptProps {
  narration: Narration;
  sessionStatus: string | null;
  selectedFactsCount: number;
  onSubmitVideo: () => void;
  onVerifyNarration: () => void;
  isGeneratingVideo: boolean;
  videoSuccess: boolean;
  videoError: string | null;
  isLoading: boolean;
  narrationLocked: boolean;
}

export function NarrationReviewPrompt({
  narration,
  sessionStatus,
  selectedFactsCount,
  onSubmitVideo,
  onVerifyNarration,
  isGeneratingVideo,
  videoSuccess,
  videoError,
  isLoading,
  narrationLocked,
}: NarrationReviewPromptProps) {
  const showVideoButton =
    sessionStatus !== "video_generating" &&
    sessionStatus !== "video_complete" &&
    sessionStatus !== "video_failed";

  return (
    <Message from="assistant">
      <MessageContent>
        <div className="space-y-3">
          <p>I&apos;ve created your narration script! Here&apos;s a summary:</p>
          <div className="bg-muted rounded-lg p-3 text-sm">
            <div className="flex flex-wrap gap-4">
              <div>
                <span className="text-muted-foreground">Duration:</span>{" "}
                {narration.total_duration}s
              </div>
              <div>
                <span className="text-muted-foreground">Segments:</span>{" "}
                {narration.segments.length}
              </div>
              <div>
                <span className="text-muted-foreground">Reading Level:</span>{" "}
                {narration.reading_level}
              </div>
              <div>
                <span className="text-muted-foreground">Key Terms:</span>{" "}
                {narration.key_terms_count}
              </div>
            </div>
          </div>
          <p className="text-muted-foreground text-sm">
            You can review and edit the script on the right.
            {!narrationLocked &&
              " When you're satisfied, click 'Verify Changes' to lock it in."}
            {narrationLocked &&
              showVideoButton &&
              " You can now proceed to generate the video."}
          </p>

          {/* Show Verify button if not locked yet */}
          {!narrationLocked && (
            <Alert>
              <AlertDescription>
                <div className="flex w-full items-center justify-between">
                  <span className="text-sm font-medium">Review your edits</span>
                  <Button
                    onClick={onVerifyNarration}
                    size="sm"
                    variant="default"
                    disabled={isLoading}
                  >
                    {isLoading ? (
                      <>
                        <span className="mr-2 inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                        Saving...
                      </>
                    ) : (
                      <>
                        <CheckCircle2 className="mr-2 h-4 w-4" />
                        Verify Changes
                      </>
                    )}
                  </Button>
                </div>
              </AlertDescription>
            </Alert>
          )}

          {/* Only show Create Video button after verification */}
          {narrationLocked && showVideoButton && (
            <Alert className="bg-primary/10">
              <AlertDescription>
                <div className="flex w-full items-center justify-between">
                  <div className="flex flex-col gap-1">
                    <span className="text-sm font-medium">
                      {selectedFactsCount} fact
                      {selectedFactsCount !== 1 ? "s" : ""} selected
                    </span>
                    {videoSuccess && (
                      <span className="text-xs text-green-600">
                        ✓ Video generation started!
                      </span>
                    )}
                    {videoError && (
                      <span className="text-xs text-red-600">
                        ✗ {videoError}
                      </span>
                    )}
                  </div>
                  <Button
                    onClick={onSubmitVideo}
                    size="sm"
                    disabled={isLoading || isGeneratingVideo}
                  >
                    {isGeneratingVideo ? (
                      <>
                        <span className="mr-2 inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                        Generating...
                      </>
                    ) : videoSuccess ? (
                      "✓ Video Started"
                    ) : (
                      "Create Video"
                    )}
                  </Button>
                </div>
              </AlertDescription>
            </Alert>
          )}
        </div>
      </MessageContent>
    </Message>
  );
}
