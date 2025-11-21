import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Fact, Narration } from "@/types";

type WorkflowStep = "input" | "selection" | "review";

type Message = {
  role: "user" | "assistant";
  content: string;
  id?: string;
};

interface AgentCreateState {
  // State
  documentContent: string;
  messages: Message[];
  isLoading: boolean;
  error: Error | null;
  workflowStep: WorkflowStep;
  facts: Fact[];
  selectedFacts: Fact[];
  narration: Narration | null;
  sessionId: string | null;

  // Actions
  setDocumentContent: (content: string) => void;
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
}

// Helper: Read stream response
const readStreamResponse = async (response: Response): Promise<string> => {
  const reader = response.body?.getReader();
  if (!reader) throw new Error("No response body");

  const decoder = new TextDecoder();
  let accumulatedResponse = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    accumulatedResponse += decoder.decode(value, { stream: true });
  }

  return accumulatedResponse;
};

export const useAgentCreateStore = create<AgentCreateState>()(
  persist(
    (set, get) => ({
      // Initial state
      documentContent: "",
      messages: [],
      isLoading: false,
      error: null,
      workflowStep: "input",
      facts: [],
      selectedFacts: [],
      narration: null,
      sessionId: null,

      // Simple setters
      setDocumentContent: (content) => set({ documentContent: content }),
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
      reset: () =>
        set({
          documentContent: "",
          messages: [],
          isLoading: false,
          error: null,
          workflowStep: "input",
          facts: [],
          selectedFacts: [],
          narration: null,
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

          const response = await fetch("/api/agent-create", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              messages: messagesToSend,
              mode: "extract",
              sessionId: state.sessionId,
            }),
          });

          state.updateSessionIdFromResponse(response);

          if (!response.ok) {
            throw new Error("Failed to fetch response");
          }

          const accumulatedResponse = await readStreamResponse(response);
          const json = JSON.parse(accumulatedResponse) as {
            facts?: Fact[];
            message?: string;
          };

          state.handleFactExtractionResponse(json);
        } catch (e) {
          console.error("Failed to extract facts", e);
          state.setError(e as Error);
          throw e;
        } finally {
          state.setIsLoading(false);
        }
      },

      handleSubmitFacts: async () => {
        const state = get();
        state.setIsLoading(true);
        state.setError(null);

        const confirmationMessage: Message = {
          role: "user",
          content: `I confirm these facts:\n\n${state.selectedFacts
            .map((f) => `- ${f.concept}: ${f.details}`)
            .join("\n")}`,
        };

        const messagesWithConfirmation = [
          ...state.messages,
          confirmationMessage,
        ];

        try {
          const response = await fetch("/api/agent-create", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              messages: messagesWithConfirmation,
              mode: "narrate",
              selectedFacts: state.selectedFacts,
              sessionId: state.sessionId,
            }),
          });

          state.updateSessionIdFromResponse(response);

          if (!response.ok) {
            throw new Error("Failed to fetch response");
          }

          const accumulatedResponse = await readStreamResponse(response);
          const json = JSON.parse(accumulatedResponse) as Narration & {
            message?: string;
          };

          const { message, ...narrationData } = json;
          state.setNarration(narrationData as Narration);
          state.setWorkflowStep("review");
          state.addMessage({
            ...confirmationMessage,
            id: Date.now().toString() + "-user-confirm",
          });
          state.addMessage({
            role: "assistant",
            content:
              message ?? "Here is the narration based on your selected facts.",
            id: Date.now().toString(),
          });
        } catch (e) {
          console.error("Chat error:", e);
          state.setError(e as Error);
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
