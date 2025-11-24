"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { toast } from "sonner";
import { api } from "@/trpc/react";
import { useAgentCreateStore } from "@/stores/agent-create-store";

interface UseSessionManagementProps {
  externalSessionId?: string | null;
  storeSessionId: string | null;
}

export function useSessionManagement({
  externalSessionId,
  storeSessionId,
}: UseSessionManagementProps) {
  const [copied, setCopied] = useState(false);
  const router = useRouter();
  const pathname = usePathname();
  const utils = api.useUtils();

  const { reset, setSessionId, loadSession } = useAgentCreateStore();

  // tRPC mutation for deleting session
  const deleteMutation = api.script.delete.useMutation({
    onSuccess: () => {
      toast.success("Session deleted successfully");

      // Invalidate history list to refresh
      void utils.script.list.invalidate();

      // Reset local state
      reset();
      setSessionId(null);

      // Always redirect to clean create page after deletion
      router.push("/dashboard/create");
    },
    onError: (error) => {
      toast.error(`Failed to delete session: ${error.message}`);

      // Add error message to chat
      const errorMessage = {
        role: "assistant" as const,
        content: `Failed to delete session: ${error.message}`,
        id: Date.now().toString(),
      };
      const store = useAgentCreateStore.getState();
      store.addMessage(errorMessage);
    },
  });

  // Handler for clearing session (local only)
  const handleClearSession = () => {
    reset();
    setSessionId(null);
  };

  // Handler for copying session ID to clipboard
  const handleCopySessionId = async (sessionId: string) => {
    try {
      await navigator.clipboard.writeText(sessionId);
      setCopied(true);
      toast.success("Session ID copied to clipboard");
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error("Failed to copy session ID");
    }
  };

  // Handler for deleting session (from DB)
  const handleDeleteSession = (sessionId: string) => {
    deleteMutation.mutate({ sessionId });
  };

  // Load session data on mount if externalSessionId is provided
  useEffect(() => {
    if (externalSessionId && externalSessionId !== storeSessionId) {
      setSessionId(externalSessionId);
      loadSession(externalSessionId).catch((err) => {
        console.error("Failed to load session:", err);
      });
    } else if (!externalSessionId && storeSessionId) {
      // If there's no sessionId in URL but store has one, reset the store
      reset();
      setSessionId(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [externalSessionId]);

  // Sync sessionId changes to URL (only on create page, not history page)
  useEffect(() => {
    // Only update URL if we're on the create page and sessionId has changed
    if (
      pathname === "/dashboard/create" &&
      storeSessionId &&
      storeSessionId !== externalSessionId
    ) {
      router.replace(`/dashboard/create?sessionId=${storeSessionId}`);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [storeSessionId]);

  return {
    copied,
    handleCopySessionId,
    handleClearSession,
    handleDeleteSession,
    deleteMutation,
  };
}

