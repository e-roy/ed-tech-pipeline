"use client";

import { useState, useEffect } from "react";
import { api } from "@/trpc/react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useFactExtraction } from "@/components/fact-extraction/FactExtractionContext";
import { useChatMessage } from "@/components/chat/chat-message-context";

interface Segment {
  id: string;
  type: string;
  start_time: number;
  duration: number;
  narration: string;
  visual_guidance: string;
  key_concepts: string[];
  educational_purpose: string;
}

interface ScriptReviewPanelProps {
  topic?: string;
}

export function ScriptReviewPanel({
  topic = "Educational Content",
}: ScriptReviewPanelProps) {
  const { confirmedFacts, setIsGeneratingScript, sessionId } =
    useFactExtraction();
  const { sendMessage } = useChatMessage();

  // sendMessage may be null if not in ChatMessageProvider context
  const [editableSegments, setEditableSegments] = useState<Segment[]>([]);
  const [generatedScript, setGeneratedScript] = useState<{
    script: unknown;
    cost: number;
    duration: number;
  } | null>(null);
  const [hasInitiatedGeneration, setHasInitiatedGeneration] = useState(false);

  // Generate script when component mounts or facts change
  const generateMutation = api.script.generate.useMutation({
    onSuccess: (data) => {
      setGeneratedScript(data);
      setIsGeneratingScript(false);
      if (
        data.script &&
        typeof data.script === "object" &&
        "segments" in data.script
      ) {
        setEditableSegments((data.script as { segments: Segment[] }).segments);
      }
    },
    onError: (error) => {
      console.error("Script generation error:", error);
      setHasInitiatedGeneration(false); // Allow retry on error
      setIsGeneratingScript(false);
    },
  });

  const approveMutation = api.script.approve.useMutation({
    onSuccess: async () => {
      // Add user message to chat when script is approved
      if (sendMessage) {
        try {
          await sendMessage({
            role: "user",
            parts: [
              {
                type: "text",
                text: "This script looks good, let's generate visuals",
              },
            ],
          });
        } catch (error) {
          console.error("Error sending message to chat:", error);
        }
      }
    },
  });

  useEffect(() => {
    if (
      confirmedFacts &&
      confirmedFacts.length > 0 &&
      !generatedScript &&
      !hasInitiatedGeneration &&
      !generateMutation.isPending
    ) {
      setHasInitiatedGeneration(true);
      setIsGeneratingScript(true);
      const facts = confirmedFacts.map((f) => ({
        concept: f.concept,
        details: f.details,
      }));
      generateMutation.mutate({
        topic,
        facts,
        targetDuration: 60,
      });
    }
  }, [
    confirmedFacts,
    topic,
    generatedScript,
    hasInitiatedGeneration,
    setIsGeneratingScript,
    generateMutation,
  ]);

  const handleApprove = async () => {
    if (!generatedScript || !confirmedFacts) return;

    const facts = confirmedFacts.map((f) => ({
      concept: f.concept,
      details: f.details,
    }));

    // Use edited segments if available, otherwise use original script
    const scriptToApprove =
      editableSegments.length > 0
        ? {
            ...(typeof generatedScript.script === "object" &&
            generatedScript.script !== null
              ? generatedScript.script
              : {}),
            segments: editableSegments,
          }
        : generatedScript.script;

    await approveMutation.mutateAsync({
      script: scriptToApprove,
      topic,
      facts,
      cost: generatedScript.cost,
      duration: generatedScript.duration,
      sessionId: sessionId ?? undefined,
    });
  };

  const handleRegenerateSegment = (_index: number) => {
    alert("Regeneration feature coming in Phase 04.2");
  };

  if (!confirmedFacts || confirmedFacts.length === 0) {
    return null;
  }

  if (generateMutation.isPending || !generatedScript) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Generating Script...</CardTitle>
          <CardDescription>
            AI is creating your educational script from the confirmed facts.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-3">
            <div className="border-primary size-5 animate-spin rounded-full border-2 border-t-transparent" />
            <p className="text-muted-foreground">
              This usually takes 3-5 seconds...
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Review Script</CardTitle>
        <CardDescription>
          Review and edit the generated script. Each segment can be modified
          before approval.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {editableSegments.map((segment, index) => (
            <div
              key={segment.id}
              className="border-l-primary bg-muted/50 rounded-lg border-l-4 p-4"
            >
              <div className="mb-3 flex items-start justify-between">
                <div>
                  <span className="inline-block rounded bg-blue-100 px-3 py-1 text-sm font-medium text-blue-800">
                    Segment {index + 1}: {segment.type}
                  </span>
                  <span className="text-muted-foreground ml-3 text-sm">
                    {segment.start_time}s -{" "}
                    {segment.start_time + segment.duration}s
                  </span>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleRegenerateSegment(index)}
                >
                  Regenerate
                </Button>
              </div>

              <div className="mb-3">
                <label className="mb-2 block text-sm font-medium">
                  Narration:
                </label>
                <textarea
                  value={segment.narration}
                  onChange={(e) => {
                    const updated = [...editableSegments];
                    const segment = updated[index];
                    if (segment) {
                      segment.narration = e.target.value;
                      setEditableSegments(updated);
                    }
                  }}
                  className="min-h-[80px] w-full rounded border px-3 py-2 text-sm"
                />
              </div>

              <div className="mb-3">
                <label className="mb-2 block text-sm font-medium">
                  Visual Guidance:
                </label>
                <textarea
                  value={segment.visual_guidance}
                  onChange={(e) => {
                    const updated = [...editableSegments];
                    const segment = updated[index];
                    if (segment) {
                      segment.visual_guidance = e.target.value;
                      setEditableSegments(updated);
                    }
                  }}
                  className="w-full rounded border px-3 py-2 text-sm"
                  rows={2}
                />
              </div>

              {segment.key_concepts.length > 0 && (
                <div className="text-sm">
                  <span className="font-medium">Key Concepts:</span>{" "}
                  {segment.key_concepts.join(", ")}
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="mt-6 flex gap-4">
          <Button onClick={handleApprove} size="lg">
            Approve Script & Generate Visuals →
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
