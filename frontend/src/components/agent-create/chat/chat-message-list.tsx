"use client";

import type { FileUIPart } from "ai";
import {
  Message,
  MessageContent,
  MessageResponse,
  MessageAttachments,
  MessageAttachment,
} from "@/components/ai-elements/message";
import { ScriptGenerationChainOfThought } from "@/components/generation/ScriptGenerationChainOfThought";
import { Badge } from "@/components/ui/badge";
import { Loader2 } from "lucide-react";

type ThinkingStatus = {
  operation: "extracting" | "narrating";
  steps: string[];
} | null;

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  id?: string;
  files?: FileUIPart[];
};

interface ChatMessageListProps {
  messages: ChatMessage[];
  thinkingStatus: ThinkingStatus;
  childAge: string | null;
  childInterest: string | null;
  error: Error | null;
}

export function ChatMessageList({
  messages,
  thinkingStatus,
  childAge,
  childInterest,
  error,
}: ChatMessageListProps) {
  return (
    <>
      {messages.map((message, i) => {
        // Extract display content (hide extracted PDF text)
        let displayContent = message.content;
        if (
          message.role === "user" &&
          displayContent.includes("--- Extracted Learning Materials")
        ) {
          const extractedIndex = displayContent.indexOf(
            "--- Extracted Learning Materials",
          );
          if (extractedIndex > 0) {
            displayContent = displayContent.substring(0, extractedIndex).trim();
          } else {
            displayContent = "";
          }
        }

        const files = (message.files ?? []) as unknown as FileUIPart[];
        const hasFiles = files.length > 0;

        return (
          <Message key={message.id ?? i} from={message.role}>
            {hasFiles && (
              <MessageAttachments>
                {files.map((file, fileIndex) => (
                  <MessageAttachment key={fileIndex} data={file} />
                ))}
              </MessageAttachments>
            )}
            {displayContent && (
              <MessageContent>
                <MessageResponse>{displayContent}</MessageResponse>
              </MessageContent>
            )}
            {!displayContent && hasFiles && (
              <MessageContent>
                <div className="text-muted-foreground text-sm">
                  PDF attached
                </div>
              </MessageContent>
            )}
          </Message>
        );
      })}
      {thinkingStatus && (
        <Message from="assistant">
          <MessageContent>
            <div className="space-y-3">
              <ScriptGenerationChainOfThought
                isVisible={true}
                operation={thinkingStatus.operation}
              />
              {childAge && childInterest && (
                <div className="flex items-center justify-center">
                  <Badge variant="secondary" className="text-xs">
                    Personalizing for {childAge}-year-old interested in{" "}
                    {childInterest}
                    <Loader2 className="ml-1.5 inline-block h-3 w-3 animate-spin" />
                  </Badge>
                </div>
              )}
            </div>
          </MessageContent>
        </Message>
      )}
      {error && (
        <div className="p-4 text-sm text-red-500">Error: {error.message}</div>
      )}
    </>
  );
}
