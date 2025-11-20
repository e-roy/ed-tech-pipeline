"use client";

import { createContext, useContext, type ReactNode } from "react";
import type { FileUIPart } from "ai";

type SendMessageFunction = (message: {
  role: "user";
  parts: Array<{ type: "text"; text: string } | FileUIPart>;
}) => Promise<void>;

type ChatMessageContextValue = {
  sendMessage: SendMessageFunction | null;
};

const ChatMessageContext = createContext<ChatMessageContextValue | undefined>(
  undefined,
);

export function ChatMessageProvider({
  children,
  sendMessage,
}: {
  children: ReactNode;
  sendMessage: SendMessageFunction | null;
}) {
  return (
    <ChatMessageContext.Provider value={{ sendMessage }}>
      {children}
    </ChatMessageContext.Provider>
  );
}

export function useChatMessage() {
  const context = useContext(ChatMessageContext);
  // Return context even if undefined - components should check for null sendMessage
  return context ?? { sendMessage: null };
}

