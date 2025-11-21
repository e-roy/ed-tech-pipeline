"use client";

import { AgentCreateInterface } from "@/components/agent-create/agent-create-interface";
import { use } from "react";

type Props = {
  params: Promise<{ id: string }>;
};

export default function HistoryDetailPage({ params }: Props) {
  const { id: sessionId } = use(params);

  return (
    <AgentCreateInterface sessionId={sessionId} showNewChatButton={false} />
  );
}
