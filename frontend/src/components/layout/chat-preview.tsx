"use client";

import { useRef, useEffect } from "react";
import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import type { UIMessage } from "ai";
import ChatInput from "../chat/chat-input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";

export function ChatPreview() {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Use AI SDK's useChat hook for chat state management
  const { messages, sendMessage, status, error } = useChat({
    transport: new DefaultChatTransport({
      api: "/api/chat",
    }),
    onFinish: (event) => {
      console.log(event.message);
    },
  });

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Custom submit handler that works with ChatInput component
  const onChatInputSubmit = async (message: string) => {
    if (!message.trim()) return;

    // Use sendMessage to add the user message and trigger the API call
    await sendMessage({
      role: "user",
      parts: [{ type: "text", text: message }],
    });
  };

  return (
    <div className="flex h-full flex-col px-2 py-4">
      <ScrollArea className="mb-4 flex-1">
        <div className="flex flex-col gap-4 pr-4">
          {messages.length === 0 ? (
            <div className="text-muted-foreground flex h-full items-center justify-center text-sm">
              Start a conversation to generate images
            </div>
          ) : (
            messages.map((message: UIMessage, index: number) => {
              const isUser = message.role === "user";
              // Extract text from message parts
              const textPart = message.parts?.find(
                (part): part is { type: "text"; text: string } =>
                  part.type === "text",
              );
              const content = textPart?.text ?? "";

              return (
                <div
                  key={message.id ?? index}
                  className={cn(
                    "flex w-full flex-col gap-2",
                    isUser ? "items-end" : "items-start",
                  )}
                >
                  {content && (
                    <div
                      className={cn(
                        "max-w-[80%] rounded-2xl px-4 py-3 text-sm",
                        isUser
                          ? "bg-primary text-primary-foreground"
                          : "bg-muted text-foreground",
                      )}
                    >
                      {content}
                    </div>
                  )}
                </div>
              );
            })
          )}
          {status === "streaming" && (
            <div className="flex w-full justify-start">
              <div className="bg-muted text-foreground max-w-[80%] rounded-2xl px-4 py-3 text-sm">
                Generating images...
              </div>
            </div>
          )}
          {error && (
            <div className="flex w-full justify-start">
              <div className="bg-destructive/10 text-destructive max-w-[80%] rounded-2xl px-4 py-3 text-sm">
                Error: {error.message}
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>
      <ChatInput onSubmit={onChatInputSubmit} />
    </div>
  );
}
