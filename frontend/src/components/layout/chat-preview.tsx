"use client";

import { useState, useRef, useEffect } from "react";
import ChatInput from "../chat/chat-input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";

type Message = {
  role: "user" | "assistant";
  content: string;
};

export function ChatPreview() {
  const [messages, setMessages] = useState<Message[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (message: string) => {
    if (!message.trim()) return;

    setMessages((prev) => [...prev, { role: "user", content: message }]);
    // TODO: Add assistant response handling here
  };

  return (
    <div className="flex h-full flex-col px-2 py-4">
      <ScrollArea className="mb-4 flex-1">
        <div className="flex flex-col gap-4 pr-4">
          {messages.length === 0 ? (
            <div className="text-muted-foreground flex h-full items-center justify-center text-sm">
              Start a conversation to create your lesson plan
            </div>
          ) : (
            messages.map((message, index) => (
              <div
                key={index}
                className={cn(
                  "flex w-full",
                  message.role === "user" ? "justify-end" : "justify-start",
                )}
              >
                <div
                  className={cn(
                    "max-w-[80%] rounded-2xl px-4 py-3 text-sm",
                    message.role === "user"
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-foreground",
                  )}
                >
                  {message.content}
                </div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>
      <ChatInput onSubmit={handleSubmit} />
    </div>
  );
}
