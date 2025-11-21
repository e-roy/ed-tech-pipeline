"use client";

import { AgentCreateInterface } from "@/components/agent-create/agent-create-interface";
import { useAgentCreateStore } from "@/stores/agent-create-store";
import { useEffect } from "react";

export default function Home() {
  const { sessionId, messages } = useAgentCreateStore();

  // Load session data on mount if sessionId exists
  useEffect(() => {
    if (sessionId && messages.length === 0) {
      const store = useAgentCreateStore.getState();
      const loadSessionFn = store.loadSession as
        | ((sessionId: string) => Promise<void>)
        | undefined;
      if (loadSessionFn) {
        loadSessionFn(sessionId).catch((err) => {
          console.error("Failed to load session:", err);
        });
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

  return <AgentCreateInterface />;
}
