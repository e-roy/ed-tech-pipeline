"use client";

import { Message, MessageContent } from "@/components/ai-elements/message";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

interface FactSelectionPromptProps {
  factsCount: number;
  selectedFactsCount: number;
  onSubmitFacts: () => void;
  isLoading: boolean;
}

export function FactSelectionPrompt({
  factsCount,
  selectedFactsCount,
  onSubmitFacts,
  isLoading,
}: FactSelectionPromptProps) {
  return (
    <Message from="assistant">
      <MessageContent>
        <div className="space-y-3">
          <p>
            I&apos;ve found {factsCount} key facts. Please review them on the
            right and select the ones you&apos;d like to focus on for the video.
          </p>
          {selectedFactsCount > 0 && (
            <Alert className="bg-primary/10">
              <AlertDescription>
                <div className="flex w-full items-center justify-between">
                  <span className="text-sm font-medium">
                    {selectedFactsCount} fact
                    {selectedFactsCount !== 1 ? "s" : ""} selected
                  </span>
                  <Button onClick={onSubmitFacts} size="sm" disabled={isLoading}>
                    Create Narration
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

