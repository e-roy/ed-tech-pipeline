"use client";

import { AgentCreateInterface } from "@/components/agent-create/agent-create-interface";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";

function CreatePageContent() {
  const searchParams = useSearchParams();
  const sessionId = searchParams.get("sessionId");

  return <AgentCreateInterface sessionId={sessionId} />;
}

export default function Home() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <CreatePageContent />
    </Suspense>
  );
}
