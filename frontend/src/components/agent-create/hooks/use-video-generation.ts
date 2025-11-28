"use client";

import { useState } from "react";
import { api } from "@/trpc/react";
import { useAgentCreateStore } from "@/stores/agent-create-store";
import type { Narration, Fact } from "@/types";

export function useVideoGeneration() {
  const [isGeneratingVideo, setIsGeneratingVideo] = useState(false);
  const [videoError, setVideoError] = useState<string | null>(null);
  const [videoSuccess, setVideoSuccess] = useState(false);

  const { setIsVideoGenerating } = useAgentCreateStore();

  // tRPC mutation for video approval
  const approveMutation = api.script.approve.useMutation({
    onSuccess: () => {
      setIsGeneratingVideo(false);
      setVideoSuccess(true);
      setVideoError(null);
      setIsVideoGenerating(true); // Enable WebSocket connection

      // Add success message to chat
      const successMessage = {
        id: `msg-${Date.now()}`,
        role: "assistant" as const,
        parts: [
          {
            type: "text" as const,
            text: "🎉 Video generation started! Your video is being created and will be ready soon. You can check the status in your dashboard.",
          },
        ],
      };
      const store = useAgentCreateStore.getState();
      store.addMessage(successMessage);
    },
    onError: (error) => {
      setIsGeneratingVideo(false);
      setVideoError(error.message);
      setIsVideoGenerating(false); // Disable WebSocket connection

      // Add error message to chat
      const errorMessage = {
        id: `msg-${Date.now()}`,
        role: "assistant" as const,
        parts: [
          {
            type: "text" as const,
            text: `❌ Failed to start video generation: ${error.message}. Please try again.`,
          },
        ],
      };
      const store = useAgentCreateStore.getState();
      store.addMessage(errorMessage);
    },
  });

  // Handler for video creation
  const handleSubmitVideo = async (
    narration: Narration,
    selectedFacts: Fact[],
    sessionId: string,
  ) => {
    if (!narration || !selectedFacts || !sessionId) {
      setVideoError("Missing required data for video generation");
      return;
    }

    setIsGeneratingVideo(true);
    setVideoError(null);
    setVideoSuccess(false);

    // Calculate cost and duration from narration
    const cost = 0; // You may want to calculate this based on your pricing
    const duration = narration.total_duration || 60;

    // Add user message confirming video generation
    const confirmMessage = {
      id: `msg-${Date.now()}`,
      role: "user" as const,
      parts: [
        {
          type: "text" as const,
          text: "Start generating the video",
        },
      ],
    };
    const store = useAgentCreateStore.getState();
    store.addMessage(confirmMessage);

    // Prepare facts for the API
    const factsForApi = selectedFacts.map((f) => ({
      concept: f.concept,
      details: f.details,
    }));

    try {
      await approveMutation.mutateAsync({
        script: narration,
        topic: factsForApi[0]?.concept ?? "Educational Content",
        facts: factsForApi,
        cost,
        duration,
        sessionId,
      });
    } catch (error) {
      // Error is handled in onError callback
      console.error("Video generation error:", error);
    }
  };

  return {
    isGeneratingVideo,
    videoError,
    videoSuccess,
    handleSubmitVideo,
  };
}
