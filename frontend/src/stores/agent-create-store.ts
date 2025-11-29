import { create } from "zustand";
import { persist } from "zustand/middleware";
import { nanoid } from "nanoid";
import type { Fact, Narration, AgentSessionResponse } from "@/types";
import type { StandardApiResponse } from "@/lib/api-response";
import type { FileUIPart, UIMessage } from "ai";
import { processPdfUploads } from "@/lib/pdf-upload";

type WorkflowStep = "input" | "selection" | "review";

type ThinkingStatus = {
  operation: "extracting" | "narrating";
  steps: string[];
} | null;

interface AgentCreateState {
  // State
  messages: UIMessage[];
  isLoading: boolean;
  isSessionLoading: boolean;
  error: Error | null;
  workflowStep: WorkflowStep;
  facts: Fact[];
  selectedFacts: Fact[];
  narration: Narration | null;
  sessionId: string | null;
  sessionStatus: string | null;
  thinkingStatus: ThinkingStatus;
  factsLocked: boolean;
  narrationLocked: boolean;
  childAge: string | null;
  childInterest: string | null;
  showFactSelectionPrompt: boolean;
  showNarrationReviewPrompt: boolean;
  isVideoGenerating: boolean;

  // Actions
  addMessage: (message: UIMessage) => void;
  setMessages: (messages: UIMessage[]) => void;
  setIsLoading: (loading: boolean) => void;
  setIsSessionLoading: (loading: boolean) => void;
  setError: (error: Error | null) => void;
  setWorkflowStep: (step: WorkflowStep) => void;
  setFacts: (facts: Fact[]) => void;
  toggleFact: (fact: Fact) => void;
  setSelectedFacts: (facts: Fact[]) => void;
  setNarration: (narration: Narration | null) => void;
  setSessionId: (id: string | null) => void;
  setThinkingStatus: (status: ThinkingStatus) => void;
  setFactsLocked: (locked: boolean) => void;
  setNarrationLocked: (locked: boolean) => void;
  setChildInfo: (age: string, interest: string) => void;
  setShowFactSelectionPrompt: (show: boolean) => void;
  setShowNarrationReviewPrompt: (show: boolean) => void;
  setIsVideoGenerating: (generating: boolean) => void;
  reset: () => void;

  // Complex actions
  updateSessionIdFromResponse: (response: Response) => void;
  handleFactExtractionResponse: (json: {
    facts?: Fact[];
    message?: string;
  }) => void;
  extractFacts: (messagesToSend: UIMessage[]) => Promise<void>;
  handleSubmitFacts: () => Promise<void>;
  handleVerifyNarration: () => Promise<void>;
  handleSubmit: (message: {
    text: string;
    files: FileUIPart[];
  }) => Promise<void>;
  loadSession: (sessionId: string) => Promise<void>;
}

// Helper: Create message with auto-generated unique ID
const createMessage = (
  role: "user" | "assistant",
  content: string,
): UIMessage => ({
  id: `msg-${nanoid()}`,
  role,
  parts: [{ type: "text", text: content }],
});

// Helper: Extract session ID from response headers
const extractSessionId = (response: Response): string | null =>
  response.headers.get("x-session-id") ??
  response.headers.get("X-Session-Id") ??
  null;

/**
 * Helper to parse tool response from API
 * Now handles standardized format from buildStandardResponse
 */
const parseToolResponse = (
  jsonData: unknown,
  state: {
    handleFactExtractionResponse: (json: {
      facts?: Fact[];
      message?: string;
    }) => void;
    setNarration: (narration: Narration | null) => void;
    setWorkflowStep: (step: WorkflowStep) => void;
    addMessage: (message: UIMessage) => void;
    setChildInfo: (age: string, interest: string) => void;
    setShowNarrationReviewPrompt: (show: boolean) => void;
  },
): boolean => {
  try {
    const data = jsonData as StandardApiResponse;

    // Handle fact extraction (adds its own message)
    if (data.facts) {
      state.handleFactExtractionResponse(data);
      return true;
    }

    // Handle narration
    if (data.narration) {
      state.setNarration(data.narration);
      state.setWorkflowStep("review");
      state.setShowNarrationReviewPrompt(true);
      if (data.message) {
        state.addMessage(createMessage("assistant", data.message));
      }
      return true;
    }

    // Handle student info save
    if (data.childAge && data.childInterest) {
      state.setChildInfo(data.childAge, data.childInterest);
      if (data.message) {
        state.addMessage(createMessage("assistant", data.message));
      }
      return true;
    }

    return data.success === true;
  } catch {
    return false;
  }
};

export const useAgentCreateStore = create<AgentCreateState>()(
  persist(
    (set, get) => ({
      // Initial state
      messages: [],
      isLoading: false,
      isSessionLoading: false,
      error: null,
      workflowStep: "input",
      facts: [],
      selectedFacts: [],
      narration: null,
      sessionId: null,
      sessionStatus: null,
      thinkingStatus: null,
      factsLocked: false,
      narrationLocked: false,
      childAge: null,
      childInterest: null,
      showFactSelectionPrompt: false,
      showNarrationReviewPrompt: false,
      isVideoGenerating: false,

      // Simple setters
      addMessage: (message) =>
        set((state) => ({
          messages: [...state.messages, message],
        })),
      setMessages: (messages) => set({ messages }),
      setIsLoading: (loading) => set({ isLoading: loading }),
      setIsSessionLoading: (loading) => set({ isSessionLoading: loading }),
      setError: (error) => set({ error }),
      setWorkflowStep: (step) => set({ workflowStep: step }),
      setFacts: (facts) => set({ facts }),
      toggleFact: (fact) =>
        set((state) => {
          const exists = state.selectedFacts.some(
            (f) => f.concept === fact.concept,
          );
          return {
            selectedFacts: exists
              ? state.selectedFacts.filter((f) => f.concept !== fact.concept)
              : [...state.selectedFacts, fact],
          };
        }),
      setSelectedFacts: (facts) => set({ selectedFacts: facts }),
      setNarration: (narration) => set({ narration }),
      setSessionId: (id) => set({ sessionId: id }),
      setThinkingStatus: (status) => set({ thinkingStatus: status }),
      setFactsLocked: (locked) => set({ factsLocked: locked }),
      setNarrationLocked: (locked) => set({ narrationLocked: locked }),
      setChildInfo: (age, interest) =>
        set({ childAge: age, childInterest: interest }),
      setShowFactSelectionPrompt: (show) =>
        set({ showFactSelectionPrompt: show }),
      setShowNarrationReviewPrompt: (show) =>
        set({ showNarrationReviewPrompt: show }),
      setIsVideoGenerating: (generating) =>
        set({ isVideoGenerating: generating }),
      reset: () =>
        set({
          messages: [],
          isLoading: false,
          isSessionLoading: false,
          error: null,
          workflowStep: "input",
          facts: [],
          selectedFacts: [],
          narration: null,
          sessionStatus: null,
          thinkingStatus: null,
          factsLocked: false,
          narrationLocked: false,
          childAge: null,
          childInterest: null,
          showFactSelectionPrompt: false,
          showNarrationReviewPrompt: false,
          isVideoGenerating: false,
          // Keep sessionId on reset
        }),

      // Complex actions
      updateSessionIdFromResponse: (response) => {
        const responseSessionId = extractSessionId(response);
        const currentSessionId = get().sessionId;
        if (responseSessionId && responseSessionId !== currentSessionId) {
          get().setSessionId(responseSessionId);
        }
      },

      handleFactExtractionResponse: (json) => {
        if (json.facts && json.facts.length > 0) {
          set({
            facts: json.facts,
            workflowStep: "selection",
            showFactSelectionPrompt: true,
          });
          get().addMessage(
            createMessage(
              "assistant",
              json.message ??
                "I've extracted these facts. Please select the ones you want to keep.",
            ),
          );
        } else if (json.facts?.length === 0) {
          // No facts found, stay in input mode
          get().addMessage(
            createMessage(
              "assistant",
              json.message ??
                "I couldn't find any facts in the provided content. Please try providing more detailed educational content or a different source.",
            ),
          );
        }
      },

      extractFacts: async (messagesToSend) => {
        const state = get();
        try {
          state.setIsLoading(true);
          state.setError(null);
          state.setThinkingStatus({
            operation: "extracting",
            steps: [
              "Analyzing content...",
              "Extracting key facts...",
              "Validating results...",
            ],
          });

          // UIMessage already has the right structure with parts
          const response = await fetch("/api/agent-create", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              messages: messagesToSend,
              sessionId: state.sessionId,
            }),
          });

          state.updateSessionIdFromResponse(response);

          if (!response.ok) {
            throw new Error("Failed to fetch response");
          }

          const jsonData = (await response.json()) as unknown;

          // Development-only logging
          if (process.env.NODE_ENV === "development") {
            console.groupCollapsed("✨ Facts Extraction Response");
            console.log("Response Data:", jsonData);
            console.groupEnd();
          }

          // Parse the response
          if (parseToolResponse(jsonData, state)) {
            state.setThinkingStatus(null);
            return;
          }

          throw new Error("No facts extracted from response");
        } catch (e) {
          console.error("Failed to extract facts", e);
          state.setError(e as Error);
          state.setThinkingStatus(null);
          // Reset to input mode so user can try again
          state.setWorkflowStep("input");
          throw e;
        } finally {
          state.setIsLoading(false);
        }
      },

      handleSubmitFacts: async () => {
        const state = get();
        state.setIsLoading(true);
        state.setError(null);
        state.setFactsLocked(true);
        state.setShowFactSelectionPrompt(false);
        state.setThinkingStatus({
          operation: "narrating",
          steps: [
            "Processing selected facts...",
            "Creating narrative structure...",
            "Generating script segments...",
          ],
        });

        state.addMessage(
          createMessage(
            "user",
            `I've selected these facts. Please create a narration based on them.`,
          ),
        );

        try {
          // Call dedicated narration endpoint (bypasses orchestrator)
          // This eliminates sending conversation history, saving 1-3 seconds
          const response = await fetch("/api/agent-create/session/narration", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              sessionId: state.sessionId,
              selectedFacts: state.selectedFacts,
            }),
          });

          state.updateSessionIdFromResponse(response);

          if (!response.ok) {
            throw new Error("Failed to generate narration");
          }

          const jsonData = (await response.json()) as unknown;

          // Development-only logging
          if (process.env.NODE_ENV === "development") {
            console.groupCollapsed("📝 Narration Generation Response");
            console.log("Response Data:", jsonData);
            console.groupEnd();
          }

          // Parse the response
          if (parseToolResponse(jsonData, state)) {
            state.setThinkingStatus(null);
            return;
          }

          throw new Error("No narration extracted from response");
        } catch (e) {
          console.error("Failed to generate narration", e);
          state.setError(e as Error);
          state.setThinkingStatus(null);
        } finally {
          state.setIsLoading(false);
        }
      },

      handleVerifyNarration: async () => {
        const state = get();
        if (!state.sessionId || !state.narration) return;

        try {
          state.setIsLoading(true);
          state.setError(null);

          const response = await fetch("/api/agent-create/session/narration", {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              sessionId: state.sessionId,
              narration: state.narration,
            }),
          });

          if (!response.ok) {
            throw new Error("Failed to save narration changes");
          }

          // Lock the narration after successful save
          state.setNarrationLocked(true);

          // Add confirmation message
          state.addMessage(
            createMessage(
              "assistant",
              "Narration verified and saved! You can now proceed to create the video.",
            ),
          );
        } catch (error) {
          console.error("Failed to verify narration:", error);
          state.setError(error as Error);
        } finally {
          state.setIsLoading(false);
        }
      },

      handleSubmit: async (message) => {
        if (!message.text.trim() && message.files.length === 0) return;

        const state = get();
        state.setIsLoading(true);
        state.setError(null);

        // Check if PDF is present
        const hasPdf = message.files.some(
          (f) => f.mediaType === "application/pdf",
        );

        const textContent =
          message.text.trim() ||
          (hasPdf ? "PDF materials uploaded for analysis" : "");

        // Process PDFs and get S3 URLs
        let s3FileParts: FileUIPart[] = [];
        if (hasPdf) {
          const result = await processPdfUploads({
            files: message.files,
            currentSessionId: get().sessionId,
            onSessionIdCreated: (sessionId) => {
              get().setSessionId(sessionId);
            },
          });
          s3FileParts = result.s3FileParts;
        }

        // Create message with S3 URLs
        const newMessage: UIMessage = {
          id: `msg-${nanoid()}`,
          role: "user",
          parts: [{ type: "text", text: textContent }, ...s3FileParts],
        };

        const newMessages = [...state.messages, newMessage];
        state.setMessages(newMessages);

        try {
          if (state.workflowStep === "input") {
            await state.extractFacts(newMessages);
          } else if (state.workflowStep === "review") {
            state.reset();
            await state.extractFacts(newMessages);
          } else if (state.workflowStep === "selection") {
            state.reset();
            state.setMessages(newMessages);
            await state.extractFacts(newMessages);
          }
        } catch (e) {
          console.error("Chat error:", e);
          state.setError(e as Error);
        } finally {
          state.setIsLoading(false);
        }
      },

      loadSession: async (sessionId) => {
        const state = get();
        try {
          state.setIsSessionLoading(true);
          state.setError(null);

          const response = await fetch(
            `/api/agent-create/session?sessionId=${sessionId}`,
          );

          if (!response.ok) {
            // If session not found (404), clear the invalid sessionId
            if (response.status === 404) {
              console.warn("Session not found, clearing invalid sessionId");
              state.setSessionId(null);
              return;
            }
            throw new Error(`Failed to load session: ${response.status}`);
          }

          const data = (await response.json()) as AgentSessionResponse;

          // Development-only client-side logging
          if (process.env.NODE_ENV === "development") {
            console.groupCollapsed("📦 Session Data Loaded");
            console.log("Session ID:", data.session.id);
            console.log("Status:", data.session.status);
            console.log("Messages:", data.messages);
            console.log("Extracted Facts:", data.session.extractedFacts);
            console.log("Confirmed Facts:", data.session.confirmedFacts);
            console.log("Generated Script:", data.session.generatedScript);
            console.log("Child Age:", data.session.childAge);
            console.log("Child Interest:", data.session.childInterest);
            console.log("Full Response:", data);
            console.groupEnd();
          }

          // Restore state from DB
          const extractedFacts = data.session.extractedFacts ?? [];
          const confirmedFacts = data.session.confirmedFacts ?? [];
          const hasExtractedFacts = extractedFacts.length > 0;
          const hasConfirmedFacts = confirmedFacts.length > 0;
          const hasGeneratedScript = !!data.session.generatedScript;
          const isNarrationVerified =
            data.session.status === "narration_verified";
          const isVideoGenerating = data.session.status === "video_generating";
          const isVideoComplete = data.session.status === "video_complete";
          // isVideoFailed could be used for error handling in the future
          // const isVideoFailed = data.session.status === "video_failed";

          // Ensure all facts have confidence values (normalize for backward compatibility)
          const normalizeFact = (fact: unknown): Fact => {
            if (
              typeof fact === "object" &&
              fact !== null &&
              "concept" in fact &&
              "details" in fact
            ) {
              const f = fact as {
                concept: unknown;
                details: unknown;
                confidence?: unknown;
              };
              return {
                concept: String(f.concept),
                details: String(f.details),
                confidence:
                  typeof f.confidence === "number" &&
                  !isNaN(f.confidence) &&
                  f.confidence >= 0 &&
                  f.confidence <= 1
                    ? f.confidence
                    : 0.8, // Default confidence if missing or invalid
              };
            }
            // Fallback for malformed facts
            return {
              concept: "",
              details: "",
              confidence: 0.8,
            };
          };

          const normalizedExtractedFacts = extractedFacts
            .map(normalizeFact)
            .filter((f) => f.concept !== "" && f.details !== "");
          const normalizedConfirmedFacts = confirmedFacts
            .map(normalizeFact)
            .filter((f) => f.concept !== "" && f.details !== "");

          // Normalize messages to UIMessage format (handles both old and new formats)
          const normalizeMessage = (m: unknown): UIMessage => {
            const msg = m as {
              id?: string;
              role?: string;
              content?: string;
              parts?: unknown[];
            };

            // If message already has parts, use it as-is (new format)
            if (msg.parts && Array.isArray(msg.parts)) {
              return {
                id: msg.id ?? `msg-${nanoid()}`,
                role: (msg.role as "user" | "assistant") ?? "assistant",
                parts: msg.parts as UIMessage["parts"],
              };
            }

            // Convert old format (content-based) to new format (parts-based)
            return {
              id: msg.id ?? `msg-${nanoid()}`,
              role: (msg.role as "user" | "assistant") ?? "assistant",
              parts: [{ type: "text", text: msg.content ?? "" }],
            };
          };

          set({
            sessionId: data.session.id,
            sessionStatus: data.session.status,
            messages: data.messages.map(normalizeMessage),
            facts: normalizedExtractedFacts,
            selectedFacts: normalizedConfirmedFacts,
            narration: data.session.generatedScript ?? null,
            narrationLocked:
              isNarrationVerified || isVideoGenerating || isVideoComplete,
            isVideoGenerating: isVideoGenerating,
            childAge: data.session.childAge ?? null,
            childInterest: data.session.childInterest ?? null,
            workflowStep: hasConfirmedFacts
              ? hasGeneratedScript
                ? "review"
                : "selection"
              : hasExtractedFacts
                ? "selection" // If facts exist but aren't confirmed, allow selection
                : "input",
            // Set UI prompt flags based on session state
            showFactSelectionPrompt: hasExtractedFacts && !hasConfirmedFacts,
            showNarrationReviewPrompt:
              hasGeneratedScript && !isNarrationVerified,
          });
        } catch (error) {
          console.error("Failed to load session:", error);
          // Don't set error state for 404s since we're clearing the session
          if (error instanceof Error && !error.message.includes("404")) {
            state.setError(error);
          }
        } finally {
          state.setIsSessionLoading(false);
        }
      },
    }),
    {
      name: "agent-create-storage",
      partialize: (_state) => ({}), // Don't persist anything - sessionId is now URL-based
    },
  ),
);
