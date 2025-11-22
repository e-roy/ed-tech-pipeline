import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Fact, Narration } from "@/types";
import { parseToolResult } from "@/lib/ai-utils";
import type { FileUIPart } from "ai";

type WorkflowStep = "input" | "selection" | "review";

type Message = {
  role: "user" | "assistant";
  content: string;
  id?: string;
  files?: FileUIPart[];
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
  childAge: string | null;
  childInterest: string | null;
  showFactSelectionPrompt: boolean;
  showNarrationReviewPrompt: boolean;
  isVideoGenerating: boolean;

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
  setChildInfo: (age: string, interest: string) => void;
  setShowFactSelectionPrompt: (show: boolean) => void;
  setShowNarrationReviewPrompt: (show: boolean) => void;
  setIsVideoGenerating: (generating: boolean) => void;
  selectAllFacts: () => void;
  selectHighConfidenceFacts: (threshold: number) => void;
  clearSelectedFacts: () => void;
  reset: () => void;

  // Complex actions
  updateSessionIdFromResponse: (response: Response) => void;
  handleFactExtractionResponse: (json: {
    facts?: Fact[];
    message?: string;
  }) => void;
  extractFacts: (messagesToSend: Message[]) => Promise<void>;
  handleSubmitFacts: () => Promise<void>;
  handleSubmit: (message: {
    text: string;
    files: FileUIPart[];
  }) => Promise<void>;
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
    setChildInfo: (age: string, interest: string) => void;
    setShowNarrationReviewPrompt: (show: boolean) => void;
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
      child_age?: string;
      child_interest?: string;
      success?: boolean;
    };

    // Handle tool-result format with output field
    if (directJson.type === "tool-result" && directJson.output) {
      const parsedOutput = parseToolResult<{
        facts?: Fact[];
        narration?: Narration;
        message?: string;
        child_age?: string;
        child_interest?: string;
        success?: boolean;
      }>(directJson.output);

      if (
        directJson.toolName === "saveStudentInfoTool" &&
        parsedOutput.success
      ) {
        if (parsedOutput.child_age && parsedOutput.child_interest) {
          state.setChildInfo(
            parsedOutput.child_age,
            parsedOutput.child_interest,
          );
        }
        state.addMessage({
          role: "assistant",
          content:
            parsedOutput.message ?? "Student information saved successfully.",
          id: Date.now().toString(),
        });
        return true;
      } else if (
        directJson.toolName === "extractFactsTool" &&
        parsedOutput.facts
      ) {
        state.handleFactExtractionResponse(parsedOutput);
        return true;
      } else if (
        directJson.toolName === "generateNarrationTool" &&
        parsedOutput.narration
      ) {
        state.setNarration(parsedOutput.narration);
        state.setWorkflowStep("review");
        state.setShowNarrationReviewPrompt(true);
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
      state.setShowNarrationReviewPrompt(true);
      state.addMessage({
        role: "assistant",
        content:
          directJson.message ?? "I've created the narration. Please review it.",
        id: Date.now().toString(),
      });
      return true;
    }

    if (
      directJson.success &&
      directJson.child_age &&
      directJson.child_interest
    ) {
      state.setChildInfo(directJson.child_age, directJson.child_interest);
      state.addMessage({
        role: "assistant",
        content:
          directJson.message ?? "Student information saved successfully.",
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
      setChildInfo: (age, interest) =>
        set({ childAge: age, childInterest: interest }),
      setShowFactSelectionPrompt: (show) =>
        set({ showFactSelectionPrompt: show }),
      setShowNarrationReviewPrompt: (show) =>
        set({ showNarrationReviewPrompt: show }),
      setIsVideoGenerating: (generating) =>
        set({ isVideoGenerating: generating }),
      selectAllFacts: () =>
        set((state) => ({
          selectedFacts: [...state.facts],
        })),
      selectHighConfidenceFacts: (threshold) =>
        set((state) => ({
          selectedFacts: state.facts.filter((f) => f.confidence >= threshold),
        })),
      clearSelectedFacts: () => set({ selectedFacts: [] }),
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
          childAge: null,
          childInterest: null,
          showFactSelectionPrompt: false,
          showNarrationReviewPrompt: false,
          isVideoGenerating: false,
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
            showFactSelectionPrompt: true,
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
        state.setShowFactSelectionPrompt(false);
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
        if (!message.text.trim() && message.files.length === 0) return;

        const state = get();

        // Process PDF files and extract text
        let finalMessageText = message.text.trim();
        const extractedContent: string[] = [];

        // Extract text from PDFs
        for (const filePart of message.files) {
          if (filePart.mediaType === "application/pdf") {
            try {
              // Fetch the PDF file
              const response = await fetch(filePart.url);
              const blob = await response.blob();
              const file = new File(
                [blob],
                filePart.filename ?? "document.pdf",
                {
                  type: "application/pdf",
                },
              );

              // Extract text from PDF
              const { extractTextFromPDF } = await import("@/lib/extractPDF");
              const pdfText = await extractTextFromPDF(file);
              extractedContent.push(
                `--- Content from ${filePart.filename ?? "PDF"} ---\n${pdfText}`,
              );
            } catch (error) {
              console.error("Error extracting PDF text:", error);
              // Continue even if PDF extraction fails
            }
          }
        }

        // Combine user text with extracted PDF content
        if (extractedContent.length > 0) {
          finalMessageText += `\n\n--- Extracted Learning Materials ---\n${extractedContent.join("\n\n")}`;
        }

        if (!finalMessageText.trim()) return;

        // Store file attachments for display (but not the extracted text in content)
        const displayContent = message.text.trim() || "PDF attached";
        const fileAttachments = message.files.filter(
          (file) => file.mediaType === "application/pdf",
        );

        const newMessage: Message = {
          role: "user",
          content: finalMessageText, // Full content with extracted PDF text for API
          id: Date.now().toString(),
          files: fileAttachments.length > 0 ? fileAttachments : undefined,
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
            // If session not found (404), clear the invalid sessionId
            if (response.status === 404) {
              console.warn("Session not found, clearing invalid sessionId");
              state.setSessionId(null);
              return;
            }
            throw new Error(`Failed to load session: ${response.status}`);
          }

          const data = await response.json();

          // Restore state from DB
          const extractedFacts = (data.session.extractedFacts as Fact[]) ?? [];
          const confirmedFacts = (data.session.confirmedFacts as Fact[]) ?? [];
          const hasExtractedFacts = extractedFacts.length > 0;
          const hasConfirmedFacts = confirmedFacts.length > 0;
          const hasGeneratedScript = !!data.session.generatedScript;

          set({
            sessionId: data.session.id,
            messages: data.messages.map(
              (m: { role: string; content: string; id: string }) => ({
                role: m.role as "user" | "assistant",
                content: m.content,
                id: m.id,
              }),
            ),
            facts: extractedFacts,
            selectedFacts: confirmedFacts,
            narration: data.session.generatedScript ?? null,
            childAge: data.session.childAge ?? null,
            childInterest: data.session.childInterest ?? null,
            workflowStep: hasConfirmedFacts
              ? hasGeneratedScript
                ? "review"
                : "selection"
              : hasExtractedFacts
                ? "selection" // If facts exist but aren't confirmed, allow selection
                : "input",
          });
        } catch (error) {
          console.error("Failed to load session:", error);
          // Don't set error state for 404s since we're clearing the session
          if (error instanceof Error && !error.message.includes("404")) {
            state.setError(error);
          }
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
