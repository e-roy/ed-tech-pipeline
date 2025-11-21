import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Fact, Narration } from "@/types";
import { parseToolResult } from "@/lib/ai-utils";

type WorkflowStep = "input" | "selection" | "review";

type Message = {
  role: "user" | "assistant";
  content: string;
  id?: string;
};

type ThinkingStatus = {
  operation: "extracting" | "narrating";
  steps: string[];
} | null;

interface AgentCreateState {
  // State
  messages: Message[];
  isLoading: boolean;
  error: Error | null;
  workflowStep: WorkflowStep;
  facts: Fact[];
  selectedFacts: Fact[];
  narration: Narration | null;
  sessionId: string | null;
  thinkingStatus: ThinkingStatus;
  factsLocked: boolean;

  // Actions
  addMessage: (message: Message) => void;
  setMessages: (messages: Message[]) => void;
  setIsLoading: (loading: boolean) => void;
  setError: (error: Error | null) => void;
  setWorkflowStep: (step: WorkflowStep) => void;
  setFacts: (facts: Fact[]) => void;
  toggleFact: (fact: Fact) => void;
  setSelectedFacts: (facts: Fact[]) => void;
  setNarration: (narration: Narration | null) => void;
  setSessionId: (id: string | null) => void;
  setThinkingStatus: (status: ThinkingStatus) => void;
  setFactsLocked: (locked: boolean) => void;
  reset: () => void;

  // Complex actions
  updateSessionIdFromResponse: (response: Response) => void;
  handleFactExtractionResponse: (json: {
    facts?: Fact[];
    message?: string;
  }) => void;
  extractFacts: (messagesToSend: Message[]) => Promise<void>;
  handleSubmitFacts: () => Promise<void>;
  handleSubmit: (message: { text: string; files: unknown[] }) => Promise<void>;
  loadSession: (sessionId: string) => Promise<void>;
}

// Helper: Parse JSON response directly (optimized)
const parseJsonResponse = async (response: Response): Promise<unknown> => {
  return response.json();
};

/**
 * Helper to parse tool response from API
 * Handles both tool-result format and direct JSON format
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
    addMessage: (message: Message) => void;
  },
): boolean => {
  try {
    const directJson = jsonData as {
      type?: string;
      toolName?: string;
      output?: string;
      facts?: Fact[];
      narration?: Narration;
      message?: string;
    };

    // Handle tool-result format with output field
    if (directJson.type === "tool-result" && directJson.output) {
      const parsedOutput = parseToolResult<{
        facts?: Fact[];
        narration?: Narration;
        message?: string;
      }>(directJson.output);

      if (directJson.toolName === "extractFactsTool" && parsedOutput.facts) {
        state.handleFactExtractionResponse(parsedOutput);
        return true;
      } else if (
        directJson.toolName === "generateNarrationTool" &&
        parsedOutput.narration
      ) {
        state.setNarration(parsedOutput.narration);
        state.setWorkflowStep("review");
        state.addMessage({
          role: "assistant",
          content:
            parsedOutput.message ??
            "I've created the narration. Please review it.",
          id: Date.now().toString(),
        });
        return true;
      }
    }

    // Handle direct formats
    if (directJson.facts) {
      state.handleFactExtractionResponse(directJson);
      return true;
    }

    if (directJson.narration) {
      state.setNarration(directJson.narration);
      state.setWorkflowStep("review");
      state.addMessage({
        role: "assistant",
        content:
          directJson.message ?? "I've created the narration. Please review it.",
        id: Date.now().toString(),
      });
      return true;
    }
  } catch {
    // Silently fail and try alternative parsing
  }

  return false;
};

export const useAgentCreateStore = create<AgentCreateState>()(
  persist(
    (set, get) => ({
      // Initial state
      messages: [],
      isLoading: false,
      error: null,
      workflowStep: "input",
      facts: [],
      selectedFacts: [],
      narration: null,
      sessionId: null,
      thinkingStatus: null,
      factsLocked: false,

      // Simple setters
      addMessage: (message) =>
        set((state) => ({
          messages: [...state.messages, message],
        })),
      setMessages: (messages) => set({ messages }),
      setIsLoading: (loading) => set({ isLoading: loading }),
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
      reset: () =>
        set({
          messages: [],
          isLoading: false,
          error: null,
          workflowStep: "input",
          facts: [],
          selectedFacts: [],
          narration: null,
          thinkingStatus: null,
          factsLocked: false,
          // Keep sessionId on reset
        }),

      // Complex actions
      updateSessionIdFromResponse: (response) => {
        const responseSessionId =
          response.headers.get("x-session-id") ??
          response.headers.get("X-Session-Id");

        const currentSessionId = get().sessionId;
        if (responseSessionId && responseSessionId !== currentSessionId) {
          get().setSessionId(responseSessionId);
        }
      },

      handleFactExtractionResponse: (json) => {
        if (json.facts) {
          set({
            facts: json.facts,
            workflowStep: "selection",
          });
          get().addMessage({
            role: "assistant",
            content:
              json.message ??
              "I've extracted these facts. Please select the ones you want to keep.",
            id: Date.now().toString(),
          });
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

          const response = await fetch("/api/agent-create/tools", {
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

          const jsonData = await parseJsonResponse(response);

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
        state.setThinkingStatus({
          operation: "narrating",
          steps: [
            "Processing selected facts...",
            "Creating narrative structure...",
            "Generating script segments...",
          ],
        });

        const confirmationMessage: Message = {
          role: "user",
          content: `I've selected these facts. Please create a narration based on them.`,
        };

        const messagesWithConfirmation = [
          ...state.messages,
          confirmationMessage,
        ];

        state.addMessage(confirmationMessage);

        try {
          const response = await fetch("/api/agent-create/tools", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              messages: messagesWithConfirmation,
              selectedFacts: state.selectedFacts,
              sessionId: state.sessionId,
            }),
          });

          state.updateSessionIdFromResponse(response);

          if (!response.ok) {
            throw new Error("Failed to generate narration");
          }

          const jsonData = await parseJsonResponse(response);

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

      handleSubmit: async (message) => {
        if (!message.text.trim()) return;

        const state = get();
        const newMessage: Message = {
          role: "user",
          content: message.text,
          id: Date.now().toString(),
        };

        const newMessages = [...state.messages, newMessage];
        state.setMessages(newMessages);
        state.setIsLoading(true);
        state.setError(null);

        try {
          if (state.workflowStep === "input") {
            await state.extractFacts(newMessages);
          } else if (state.workflowStep === "review") {
            // Reset state for new extraction
            state.reset();
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
          state.setIsLoading(true);
          state.setError(null);

          const response = await fetch(
            `/api/agent-create/session?sessionId=${sessionId}`,
          );
          if (!response.ok) {
            throw new Error("Failed to load session");
          }

          const data = await response.json();

          // Restore state from DB
          set({
            sessionId: data.session.id,
            messages: data.messages.map(
              (m: { role: string; content: string; id: string }) => ({
                role: m.role as "user" | "assistant",
                content: m.content,
                id: m.id,
              }),
            ),
            facts: (data.session.extractedFacts as Fact[]) || [],
            selectedFacts: (data.session.confirmedFacts as Fact[]) || [],
            narration: data.session.generatedScript || null,
            workflowStep: data.session.confirmedFacts
              ? data.session.generatedScript
                ? "review"
                : "selection"
              : "input",
          });
        } catch (error) {
          console.error("Failed to load session:", error);
          state.setError(error as Error);
        } finally {
          state.setIsLoading(false);
        }
      },
    }),
    {
      name: "agent-create-storage",
      partialize: (state) => ({ sessionId: state.sessionId }), // Only persist sessionId
      // Migrate from old localStorage key if it exists
      onRehydrateStorage: () => (state) => {
        if (typeof window !== "undefined" && state) {
          const oldSessionId = localStorage.getItem("agentCreateSessionId");
          if (oldSessionId && !state.sessionId) {
            useAgentCreateStore.getState().setSessionId(oldSessionId);
          }
          // Clean up old key after migration
          localStorage.removeItem("agentCreateSessionId");
        }
      },
    },
  ),
);
