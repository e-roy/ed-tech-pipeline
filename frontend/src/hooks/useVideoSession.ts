"use client";

import { useState, useEffect, useCallback } from "react";
import { apiClient } from "@/lib/api";
import type { Session, SessionStage } from "@/types";

interface UseVideoSessionOptions {
  sessionId?: string | null;
  userId?: number;
  autoFetch?: boolean; // Automatically fetch session on mount if sessionId provided
}

interface UseVideoSessionReturn {
  session: Session | null;
  loading: boolean;
  error: string | null;
  createSession: (userId?: number) => Promise<string | null>;
  fetchSession: (sessionId: string) => Promise<void>;
  refreshSession: () => Promise<void>;
  clearSession: () => void;
}

export function useVideoSession(
  options: UseVideoSessionOptions = {},
): UseVideoSessionReturn {
  const { sessionId: initialSessionId, userId, autoFetch = true } = options;

  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(
    initialSessionId ?? null,
  );

  const fetchSession = useCallback(async (sessionId: string) => {
    setLoading(true);
    setError(null);

    try {
      const sessionData = await apiClient.getSession(sessionId);
      setSession(sessionData);
      setCurrentSessionId(sessionId);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to fetch session";
      setError(errorMessage);
      setSession(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const createSession = useCallback(
    async (createUserId?: number): Promise<string | null> => {
      setLoading(true);
      setError(null);

      try {
        const targetUserId = createUserId ?? userId ?? 1; // Default to 1 if not provided
        const response = await apiClient.createSession(targetUserId);
        setCurrentSessionId(response.session_id);

        // Optionally fetch the full session data
        if (autoFetch) {
          await fetchSession(response.session_id);
        } else {
          // Just set minimal session data
          setSession({
            id: response.session_id,
            user_id: targetUserId,
            stage: response.stage as SessionStage,
            generated_images: [],
            approved_images: [],
            generated_clips: [],
            approved_clips: [],
            total_cost: 0,
            created_at: response.created_at,
            updated_at: response.created_at,
          });
        }

        return response.session_id;
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Failed to create session";
        setError(errorMessage);
        return null;
      } finally {
        setLoading(false);
      }
    },
    [userId, autoFetch, fetchSession],
  );

  const refreshSession = useCallback(async () => {
    if (currentSessionId) {
      await fetchSession(currentSessionId);
    }
  }, [currentSessionId, fetchSession]);

  const clearSession = useCallback(() => {
    setSession(null);
    setCurrentSessionId(null);
    setError(null);
  }, []);

  // Auto-fetch session if sessionId is provided and autoFetch is true
  useEffect(() => {
    if (initialSessionId && autoFetch && !session) {
      void fetchSession(initialSessionId);
    }
  }, [initialSessionId, autoFetch, session, fetchSession]);

  return {
    session,
    loading,
    error,
    createSession,
    fetchSession,
    refreshSession,
    clearSession,
  };
}

/*
 * ============================================================================
 * INTEGRATION WITH NEXTAUTH
 * ============================================================================
 *
 * This hook manages VIDEO GENERATION SESSIONS (separate from NextAuth sessions).
 *
 * If you need to get the current user ID from NextAuth, you have a few options:
 *
 * OPTION 1: Pass userId as prop from server component
 * ----------------------------------------
 * In a server component or page:
 *
 *   import { auth } from "@/server/auth";
 *
 *   export default async function Page() {
 *     const authSession = await auth();
 *     const userId = parseInt(authSession?.user?.id ?? "1");
 *
 *     return <ClientComponent userId={userId} />;
 *   }
 *
 * Then in your client component:
 *
 *   const { createSession } = useVideoSession({ userId });
 *
 *
 * OPTION 2: Use NextAuth's useSession hook (if configured)
 * ----------------------------------------
 * If you set up NextAuth's SessionProvider and useSession hook:
 *
 *   import { useSession } from "next-auth/react";
 *   import { useVideoSession } from "@/hooks/useVideoSession";
 *
 *   export function MyComponent() {
 *     const { data: authSession } = useSession();
 *     const userId = parseInt(authSession?.user?.id ?? "1");
 *     const { createSession } = useVideoSession({ userId });
 *     // ...
 *   }
 *
 * Note: NextAuth v5 with database sessions may require SessionProvider setup.
 * Check NextAuth v5 documentation for client-side session access.
 *
 *
 * OPTION 3: Store userId in API client after login
 * ----------------------------------------
 * After successful NextAuth login, store the user ID in your API client:
 *
 *   // In your login handler
 *   const session = await auth();
 *   if (session?.user?.id) {
 *     apiClient.setUserId(parseInt(session.user.id));
 *   }
 *
 * Then modify useVideoSession to get userId from apiClient:
 *
 *   const targetUserId = createUserId ?? userId ?? apiClient.getUserId() ?? 1;
 *
 *
 * CURRENT SETUP
 * ----------------------------------------
 * The current implementation defaults to userId = 1 if not provided.
 * This works for MVP/demo purposes. For production, you should:
 * 1. Always pass userId from authenticated user
 * 2. Ensure backend validates user owns the session
 * 3. Consider adding user context to API client
 */
