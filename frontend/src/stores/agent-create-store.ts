import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Fact, Narration, AgentSessionResponse } from "@/types";
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
  addMessage: (message: Message) => void;
  setMessages: (messages: Message[]) => void;
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
  handleVerifyNarration: () => Promise<void>;
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
        const responseSessionId =
          response.headers.get("x-session-id") ??
          response.headers.get("X-Session-Id");

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
          get().addMessage({
            role: "assistant",
            content:
              json.message ??
              "I've extracted these facts. Please select the ones you want to keep.",
            id: Date.now().toString(),
          });
        } else if (json.facts?.length === 0) {
          // No facts found, stay in input mode
          get().addMessage({
            role: "assistant",
            content:
              json.message ??
              "I couldn't find any facts in the provided content. Please try providing more detailed educational content or a different source.",
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

          // Convert messages to include files as parts for proper storage
          const apiMessages = messagesToSend.map((msg) => {
            if (!msg.files || msg.files.length === 0) {
              return { role: msg.role, content: msg.content };
            }

            // Include parts for messages with file attachments
            return {
              role: msg.role,
              content: msg.content,
              parts: msg.files,
            };
          });

          const response = await fetch("/api/agent-create/tools", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              messages: apiMessages,
              sessionId: state.sessionId,
            }),
          });

          state.updateSessionIdFromResponse(response);

          if (!response.ok) {
            throw new Error("Failed to fetch response");
          }

          const jsonData = await parseJsonResponse(response);

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
          // Convert messages to include files as parts for proper storage
          const apiMessages = messagesWithConfirmation.map((msg) => {
            if (!msg.files || msg.files.length === 0) {
              return { role: msg.role, content: msg.content };
            }

            // Include parts for messages with file attachments
            return {
              role: msg.role,
              content: msg.content,
              parts: msg.files,
            };
          });

          const response = await fetch("/api/agent-create/tools", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              messages: apiMessages,
              selectedFacts: state.selectedFacts,
              sessionId: state.sessionId,
            }),
          });

          state.updateSessionIdFromResponse(response);

          if (!response.ok) {
            throw new Error("Failed to generate narration");
          }

          const jsonData = await parseJsonResponse(response);

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
          state.addMessage({
            role: "assistant",
            content:
              "Narration verified and saved! You can now proceed to create the video.",
            id: Date.now().toString(),
          });
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

        // Check if PDF is present
        const hasPdf = message.files.some(
          (f) => f.mediaType === "application/pdf",
        );

        // Create clean message WITHOUT embedded PDF text
        const fileAttachments = message.files.filter(
          (file) => file.mediaType === "application/pdf",
        );

        const newMessage: Message = {
          role: "user",
          content:
            message.text.trim() ||
            (hasPdf ? "PDF materials uploaded for analysis" : ""),
          id: Date.now().toString(),
          files: fileAttachments.length > 0 ? fileAttachments : undefined,
        };

        const newMessages = [...state.messages, newMessage];
        state.setMessages(newMessages);
        state.setIsLoading(true);
        state.setError(null);

        // Process PDF BEFORE sending to AI (upload must complete first)
        if (hasPdf) {
          // Let React update UI first by yielding control
          await new Promise((resolve) => setTimeout(resolve, 0));

          for (const filePart of message.files) {
            if (filePart.mediaType === "application/pdf") {
              try {
                const response = await fetch(filePart.url);
                const blob = await response.blob();
                const file = new File(
                  [blob],
                  filePart.filename ?? "document.pdf",
                  { type: "application/pdf" },
                );

                // Extract text immediately (fast - doesn't block UI)
                const { extractTextFromPDF } = await import("@/lib/extractPDF");
                const pdfText = await extractTextFromPDF(file);

                // Upload PDF with text first (fast path - don't wait for images)
                const formData = new FormData();
                formData.append("pdf", file);
                const currentSessionId = get().sessionId;
                if (currentSessionId) {
                  formData.append("sessionId", currentSessionId);
                }
                formData.append("extractedText", pdfText);
                formData.append("imageCount", "0"); // Will upload images separately

                const uploadResponse = await fetch(
                  "/api/agent-create/session/upload-pdf",
                  {
                    method: "POST",
                    body: formData,
                  },
                );

                if (!uploadResponse.ok) {
                  const errorText = await uploadResponse.text();
                  console.error("Failed to upload PDF:", errorText);
                  // Don't stop - continue to extractFacts even if upload fails
                } else {
                  const uploadData = (await uploadResponse.json()) as {
                    sessionId: string;
                    pdfUrl: string;
                    imageCount: number;
                  };

                  // Store sessionId if it was just created
                  if (uploadData.sessionId && !get().sessionId) {
                    get().setSessionId(uploadData.sessionId);
                  }

                  if (process.env.NODE_ENV === "development") {
                    console.log(`PDF uploaded: ${uploadData.pdfUrl}`);
                  }

                  // Extract and upload images in background (non-blocking)
                  void (async () => {
                    try {
                      if (process.env.NODE_ENV === "development") {
                        console.log("Background: Starting image extraction...");
                      }

                      const { extractImagesFromPdf } = await import(
                        "@/lib/pdf-image-extractor"
                      );
                      const extractedImages = await extractImagesFromPdf(file);

                      if (process.env.NODE_ENV === "development") {
                        console.log(
                          `Background: Extracted ${extractedImages.length} images`,
                        );
                      }

                      if (extractedImages.length > 0 && uploadData.sessionId) {
                        if (process.env.NODE_ENV === "development") {
                          console.log(
                            "Background: Uploading images to server...",
                          );
                        }

                        // Upload images separately
                        const imageFormData = new FormData();
                        imageFormData.append("sessionId", uploadData.sessionId);
                        imageFormData.append(
                          "imageCount",
                          extractedImages.length.toString(),
                        );

                        extractedImages.forEach((img, index) => {
                          const filename = `page_${img.pageNumber}_img_${img.imageIndex}.png`;
                          const imageFile = new File([img.blob], filename, {
                            type: "image/png",
                          });
                          imageFormData.append(`image_${index}`, imageFile);
                        });

                        const imageUploadResponse = await fetch(
                          "/api/agent-create/session/upload-images",
                          {
                            method: "POST",
                            body: imageFormData,
                          },
                        );

                        if (imageUploadResponse.ok) {
                          if (process.env.NODE_ENV === "development") {
                            console.log(
                              `Background: Uploaded ${extractedImages.length} images from PDF`,
                            );
                          }
                        } else {
                          console.error(
                            "Background image upload failed:",
                            await imageUploadResponse.text(),
                          );
                        }
                      } else {
                        if (process.env.NODE_ENV === "development") {
                          console.log(
                            `Background: Skipping image upload - images: ${extractedImages.length}, sessionId: ${uploadData.sessionId ? "present" : "missing"}`,
                          );
                        }
                      }
                    } catch (error) {
                      console.error(
                        "Background image extraction failed:",
                        error,
                      );
                      // Silent fail - images are optional
                    }
                  })();
                }
              } catch (error) {
                console.error("Error processing PDF:", error);
                // Don't stop - continue to extractFacts even if PDF processing fails
              }
            }
          }
        }

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

          const data = (await parseJsonResponse(
            response,
          )) as AgentSessionResponse;

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
          const isNarrationVerified = data.session.status === "narration_verified";

          set({
            sessionId: data.session.id,
            sessionStatus: data.session.status,
            messages: data.messages.map((m) => {
              const message: Message = {
                role: m.role as "user" | "assistant",
                content: m.content,
                id: m.id,
              };

              // Extract files from parts if present
              if (m.parts && Array.isArray(m.parts)) {
                const files = m.parts.filter(
                  (part: unknown) =>
                    typeof part === "object" &&
                    part !== null &&
                    "type" in part &&
                    part.type === "file",
                ) as FileUIPart[];

                if (files.length > 0) {
                  message.files = files;
                }
              }

              return message;
            }),
            facts: extractedFacts,
            selectedFacts: confirmedFacts,
            narration: data.session.generatedScript ?? null,
            narrationLocked: isNarrationVerified,
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
            showNarrationReviewPrompt: hasGeneratedScript && !isNarrationVerified,
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
