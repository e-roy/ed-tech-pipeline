"use client";

import type { UIMessage, FileUIPart } from "ai";
import { FileText } from "lucide-react";
import {
  Message,
  MessageContent,
  MessageResponse,
  MessageAttachments,
  MessageAttachment,
} from "@/components/ai-elements/message";
import { FactExtractionChainOfThought } from "@/components/fact-extraction/FactExtractionChainOfThought";
import type { FactExtractionContextValue } from "@/components/fact-extraction/FactExtractionContext";

interface ChatMessageProps {
  message: UIMessage;
  index: number;
  isStreaming: boolean;
  isStreamingAssistant: boolean;
  isCreatePage: boolean;
  factExtraction: FactExtractionContextValue;
}

export function ChatMessage({
  message,
  index,
  isStreaming: _isStreaming,
  isStreamingAssistant,
  isCreatePage,
  factExtraction: _factExtraction,
}: ChatMessageProps) {
  // Extract text and file parts from message
  const textPart = message.parts?.find(
    (part): part is { type: "text"; text: string } => part.type === "text",
  );
  const fileParts =
    message.parts?.filter((part): part is FileUIPart => part.type === "file") ??
    [];

  let content = textPart?.text ?? "";
  let showPdfIcon = false;
  let showChainOfThought = false;

  // On create page, for user messages, only show the original input
  // Hide the extracted PDF/URL content from display
  if (
    isCreatePage &&
    message.role === "user" &&
    content.includes("--- Extracted Learning Materials")
  ) {
    // Extract only the part before the extracted materials section
    const extractedIndex = content.indexOf("--- Extracted Learning Materials");
    if (extractedIndex > 0) {
      content = content.substring(0, extractedIndex).trim();

      // Remove the prompt prefix if present
      const promptPrefix =
        "Please extract educational facts from the following materials:";
      if (content.startsWith(promptPrefix)) {
        content = content.substring(promptPrefix.length).trim();
      }

      // Mark that we should show PDF icon
      showPdfIcon = true;
    }
  }

  // On create page, for assistant messages during streaming, show ChainOfThought instead
  if (isCreatePage && isStreamingAssistant) {
    showChainOfThought = true;
    content = ""; // Don't show text content when showing ChainOfThought
  } else if (isCreatePage && message.role === "assistant" && content) {
    // On create page, for completed assistant messages, remove JSON code blocks
    // since facts are displayed in the FactExtractionPanel
    // Remove JSON code blocks
    const jsonPattern = /```json\s*[\s\S]*?```/g;
    content = content.replace(jsonPattern, "").trim();

    // Also remove standalone JSON objects if present
    const jsonObjectPattern = /\{[\s\S]*?"facts"[\s\S]*?\}/g;
    content = content.replace(jsonObjectPattern, "").trim();

    // Clean up any extra whitespace or newlines
    content = content.replace(/\n{3,}/g, "\n\n").trim();
  }

  return (
    <Message key={message.id ?? index} from={message.role}>
      {fileParts.length > 0 && (
        <MessageAttachments>
          {fileParts.map((file, fileIndex) => (
            <MessageAttachment key={fileIndex} data={file} />
          ))}
        </MessageAttachments>
      )}
      {showChainOfThought ? (
        <MessageContent>
          <FactExtractionChainOfThought isVisible={showChainOfThought} />
        </MessageContent>
      ) : (
        <>
          {content && (
            <MessageContent>
              <MessageResponse>{content}</MessageResponse>
              {showPdfIcon && (
                <div className="text-muted-foreground mt-2 flex items-center gap-2 text-sm">
                  <FileText className="size-4" />
                  <span>Learning materials processed</span>
                </div>
              )}
            </MessageContent>
          )}
          {showPdfIcon && !content && (
            <MessageContent>
              <div className="text-muted-foreground flex items-center gap-2 text-sm">
                <FileText className="size-4" />
                <span>Learning materials processed</span>
              </div>
            </MessageContent>
          )}
        </>
      )}
    </Message>
  );
}
