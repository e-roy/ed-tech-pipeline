"use client";

import * as React from "react";

export type Chat = {
  id: string;
};

type ChatContextValue = {
  selectedChat: Chat | null;
  setSelectedChat: (chat: Chat | null) => void;
};

const ChatContext = React.createContext<ChatContextValue | undefined>(
  undefined,
);

export function ChatProvider({ children }: { children: React.ReactNode }) {
  const [selectedChat, setSelectedChat] = React.useState<Chat | null>(null);
  const value = React.useMemo(
    () => ({ selectedChat, setSelectedChat }),
    [selectedChat],
  );
  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
}

export function useChat() {
  const ctx = React.useContext(ChatContext);
  if (!ctx) throw new Error("useChat must be used within ChatProvider");
  return ctx;
}

