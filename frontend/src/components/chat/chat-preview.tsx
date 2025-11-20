"use client";

import { usePathname } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import type { UIMessage, FileUIPart } from "ai";
import { useFactExtraction } from "@/components/fact-extraction/FactExtractionContext";
import {
  Conversation,
  ConversationContent,
  ConversationScrollButton,
} from "@/components/ai-elements/conversation";
import {
  Message,
  MessageContent,
  MessageResponse,
} from "@/components/ai-elements/message";
import { Suggestion } from "@/components/ai-elements/suggestion";
import {
  PromptInput,
  PromptInputBody,
  PromptInputTextarea,
  PromptInputFooter,
  PromptInputSubmit,
  PromptInputAttachments,
  PromptInputAttachment,
  PromptInputActionMenu,
  PromptInputActionMenuTrigger,
  PromptInputActionMenuContent,
  PromptInputActionAddAttachments,
  type PromptInputMessage,
} from "@/components/ai-elements/prompt-input";
import { parseFactsFromMessage } from "@/lib/factParsing";
import { PROMPTS } from "@/components/chat/chatConstants";
import { ChatMessage } from "@/components/chat/ChatMessage";
import { useFactExtractionSubmit } from "@/components/chat/useFactExtractionSubmit";
import { ChatMessageProvider } from "@/components/chat/chat-message-context";
import { ScriptGenerationChainOfThought } from "@/components/generation/ScriptGenerationChainOfThought";
import type { Fact } from "@/types";

interface ChatPreviewProps {
  sessionId?: string; // For history page resumption
}

export function ChatPreview({
  sessionId: propSessionId,
}: ChatPreviewProps = {}) {
  const pathname = usePathname();
  const isCreatePage = pathname === "/dashboard/create";
  const factExtraction = useFactExtraction();

  // Initialize sessionId: prop (history) > localStorage (create page) > null
  // Initialize to propSessionId or null (localStorage access happens in useEffect)
  const [sessionId, setSessionId] = useState<string | null>(
    propSessionId ?? null,
  );

  // Load from localStorage on client side only (for create pages)
  useEffect(() => {
    // Only access localStorage on client side
    if (typeof window === "undefined") return;

    // If we have propSessionId, use it (history page) - don't check localStorage
    if (propSessionId) {
      setSessionId(propSessionId);
      return;
    }

    // Create page - check localStorage for active session
    const storedSessionId = localStorage.getItem("chatSessionId");
    if (storedSessionId) {
      setSessionId(storedSessionId);
    }
  }, [propSessionId]);

  // Handle when AI finishes responding
  const handleMessageFinish = useCallback(
    (message: UIMessage) => {
      if (!isCreatePage || factExtraction.confirmedFacts) return;

      const textPart = message.parts?.find(
        (part): part is { type: "text"; text: string } => part.type === "text",
      );

      if (textPart?.text && message.role === "assistant") {
        const facts = parseFactsFromMessage(textPart.text);
        if (facts !== null && facts.length > 0) {
          factExtraction.setExtractedFacts(facts);
        } else {
          // If no facts found, stop loading state
          factExtraction.setIsExtracting?.(false);
        }
      }
    },
    [isCreatePage, factExtraction],
  );

  // Update sessionId if prop changes (e.g., navigating to history page)
  useEffect(() => {
    if (propSessionId && propSessionId !== sessionId) {
      setSessionId(propSessionId);
      // Don't store history sessionId in localStorage
    }
  }, [propSessionId, sessionId]);

  // Keep a ref to sessionId for useChat transport closure
  const sessionIdRef = useRef<string | null>(sessionId);
  useEffect(() => {
    sessionIdRef.current = sessionId;
  }, [sessionId]);

  // Use AI SDK's useChat hook for chat state management
  const { messages, sendMessage, status, error } = useChat({
    transport: new DefaultChatTransport({
      api: "/api/chat",
      fetch: async (url, options) => {
        const currentSessionId = sessionIdRef.current;

        // Include existing sessionId if we have one
        if (options?.body && currentSessionId) {
          try {
            const body = JSON.parse(options.body as string) as {
              sessionId?: string;
              [key: string]: unknown;
            };
            body.sessionId = currentSessionId;

            // Set header if sessionId came from props (history page resumption)
            if (propSessionId) {
              options.headers = {
                ...options.headers,
                "x-session-id": currentSessionId,
              };
            }

            options.body = JSON.stringify(body);
          } catch {
            // If body parsing fails, continue without modification
          }
        }

        const response = await fetch(url, options);

        // Capture sessionId from header on first response
        // Only store in localStorage if NOT from props (create pages only)
        const responseSessionId =
          response.headers.get("x-session-id") ??
          response.headers.get("X-Session-Id");

        console.log("[ChatPreview] Response Headers:", {
          sessionIdHeader: responseSessionId,
          allHeaders: [...response.headers.entries()],
        });

        if (
          responseSessionId &&
          responseSessionId !== currentSessionId &&
          !propSessionId
        ) {
          console.log(
            "[ChatPreview] Capturing new sessionId:",
            responseSessionId,
          );
          setSessionId(responseSessionId);
          localStorage.setItem("chatSessionId", responseSessionId);
        }

        return response;
      },
    }),
    onFinish: (event) => {
      console.log(event.message);
      handleMessageFinish(event.message);
    },
  });

  // Use fact extraction submit hook
  const { handleFactExtractionSubmit } = useFactExtractionSubmit();

  // Track previous confirmedFacts to detect when facts are confirmed
  const prevConfirmedFactsRef = useRef<Fact[] | null>(null);

  // Add user message when facts are confirmed
  useEffect(() => {
    if (
      factExtraction.confirmedFacts &&
      factExtraction.confirmedFacts.length > 0 &&
      !prevConfirmedFactsRef.current
    ) {
      // Facts were just confirmed, send message
      const factsPayload = {
        facts: factExtraction.confirmedFacts,
      };

      sendMessage({
        role: "user",
        parts: [
          {
            type: "text",
            text: `I confirm the following facts for the script:\n\n\`\`\`json\n${JSON.stringify(factsPayload, null, 2)}\n\`\`\`\n\nPlease proceed with generating the script.`,
          },
        ],
      }).catch((error) => {
        console.error("Error sending message to chat:", error);
      });
    }
    prevConfirmedFactsRef.current = factExtraction.confirmedFacts;
  }, [factExtraction.confirmedFacts, sendMessage]);

  // Handle PromptInput submit with text and file attachments
  const handleSubmit = async (
    message: PromptInputMessage,
    _event: React.FormEvent<HTMLFormElement>,
  ) => {
    if (!message.text.trim() && message.files.length === 0) return;

    // On create page, prepare message for AI fact extraction
    if (isCreatePage && !factExtraction.confirmedFacts) {
      await handleFactExtractionSubmit(message, sendMessage);
      return;
    }

    // Normal chat behavior for other pages or after facts are confirmed
    const parts: Array<{ type: "text"; text: string } | FileUIPart> = [];

    if (message.text.trim()) {
      parts.push({ type: "text", text: message.text.trim() });
    }

    message.files.forEach((file) => {
      parts.push(file);
    });

    await sendMessage({
      role: "user",
      parts,
    });
  };

  // Handle suggestion click
  const handleSuggestionClick = async (prompt: string) => {
    await sendMessage({
      role: "user",
      parts: [{ type: "text", text: prompt }],
    });
  };

  return (
    <ChatMessageProvider sendMessage={sendMessage}>
      <div className="flex h-full flex-col px-2 py-4">
        <Conversation className="mb-4">
          <ConversationContent>
            {messages.length === 0 && (
              <>
                <Message from="assistant">
                  <MessageContent>
                    <MessageResponse>
                      {isCreatePage
                        ? "I'll help you extract educational facts from your learning materials. Please provide:\n\n- Topic\n- Learning objective\n- Key points\n- PDF files or URLs (optional)\n\nI'll analyze the content and extract key facts for your review."
                        : "Hello, I'm your creative assistant. I can help you create lesson plans, suggest activities, and make topics more engaging for your students. What would you like to create?"}
                    </MessageResponse>
                  </MessageContent>
                </Message>
                {!isCreatePage && (
                  <div className="flex w-full flex-col gap-2">
                    {PROMPTS.map((prompt) => {
                      const IconComponent = prompt.icon;
                      return (
                        <Suggestion
                          key={prompt.text}
                          suggestion={prompt.prompt}
                          onClick={handleSuggestionClick}
                          className="justify-start"
                          size="sm"
                        >
                          <IconComponent className="mr-2 size-4" />
                          {prompt.text}
                        </Suggestion>
                      );
                    })}
                  </div>
                )}
              </>
            )}
            {messages.map((message: UIMessage, index: number) => {
              const isStreaming =
                status === "streaming" && index === messages.length - 1;
              const isStreamingAssistant =
                isStreaming && message.role === "assistant";

              return (
                <ChatMessage
                  key={message.id ?? index}
                  message={message}
                  index={index}
                  isStreaming={isStreaming}
                  isStreamingAssistant={isStreamingAssistant}
                  isCreatePage={isCreatePage}
                  factExtraction={factExtraction}
                />
              );
            })}
            {/* Show script generation chain of thought when script is being generated */}
            {isCreatePage &&
              factExtraction.isGeneratingScript &&
              factExtraction.confirmedFacts &&
              factExtraction.confirmedFacts.length > 0 && (
                <Message from="assistant">
                  <MessageContent>
                    <ScriptGenerationChainOfThought isVisible={true} />
                  </MessageContent>
                </Message>
              )}
            {/* Hide streaming message on create page during fact extraction - loading state shown in main content */}
            {status === "streaming" &&
              !(isCreatePage && !factExtraction.confirmedFacts) &&
              !(isCreatePage && factExtraction.isGeneratingScript) && (
                <Message from="assistant">
                  <MessageContent>
                    <MessageResponse>Generating response...</MessageResponse>
                  </MessageContent>
                </Message>
              )}
            {error && (
              <Message from="assistant">
                <MessageContent>
                  <MessageResponse>{`Error: ${error.message}`}</MessageResponse>
                </MessageContent>
              </Message>
            )}
          </ConversationContent>
          <ConversationScrollButton />
        </Conversation>

        <PromptInput
          onSubmit={handleSubmit}
          accept={isCreatePage ? ".pdf,application/pdf" : undefined}
        >
          <PromptInputBody>
            <PromptInputAttachments>
              {(attachment) => <PromptInputAttachment data={attachment} />}
            </PromptInputAttachments>
            <PromptInputTextarea
              placeholder={
                isCreatePage
                  ? "Paste text, upload a PDF, or enter a URL..."
                  : "Ask anything about creating lesson plans..."
              }
            />
          </PromptInputBody>
          <PromptInputFooter>
            <PromptInputActionMenu>
              <PromptInputActionMenuTrigger />
              <PromptInputActionMenuContent>
                <PromptInputActionAddAttachments />
              </PromptInputActionMenuContent>
            </PromptInputActionMenu>
            <PromptInputSubmit status={status} />
          </PromptInputFooter>
        </PromptInput>
      </div>
    </ChatMessageProvider>
  );
}
