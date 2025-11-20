"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { type ProgressUpdate } from "@/types";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000";

export function useWebSocket(sessionId: string | null) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<ProgressUpdate | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | undefined>(undefined);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  const connect = useCallback(() => {
    if (!sessionId) {
      return;
    }

    // Close existing connection if any
    if (wsRef.current) {
      wsRef.current.close();
    }

    try {
      // Use query parameter format for API Gateway compatibility
      // Format: wss://gateway-url/prod?session_id=xxx
      // Backend supports both: /ws/{session_id} (path) and /ws?session_id=xxx (query)
      const wsUrl = WS_URL.includes('execute-api') 
        ? `${WS_URL}?session_id=${sessionId}`  // API Gateway format
        : `${WS_URL}/ws/${sessionId}`;          // Direct connection format
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setIsConnected(true);
        reconnectAttempts.current = 0; // Reset on successful connection
      };

      ws.onmessage = (event) => {
        try {
          const messageData =
            typeof event.data === "string" ? event.data : String(event.data);
          const data = JSON.parse(messageData) as ProgressUpdate;
          setLastMessage(data);
        } catch (error) {
          console.error("Failed to parse WebSocket message:", error);
        }
      };

      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        setIsConnected(false);
      };

      ws.onclose = (event) => {
        setIsConnected(false);

        // Attempt to reconnect if not a normal closure and we haven't exceeded max attempts
        if (
          event.code !== 1000 &&
          reconnectAttempts.current < maxReconnectAttempts
        ) {
          reconnectAttempts.current += 1;
          const delay = Math.min(
            1000 * Math.pow(2, reconnectAttempts.current),
            30000,
          ); // Exponential backoff, max 30s

          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, delay);
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error("Failed to create WebSocket connection:", error);
      setIsConnected(false);
    }
  }, [sessionId]);

  const sendMessage = useCallback((message: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(message);
    }
  }, []);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close(1000); // Normal closure
        wsRef.current = null;
      }
    };
  }, [connect]);

  return {
    isConnected,
    lastMessage,
    sendMessage,
  };
}

/*
 * ============================================================================
 * FUTURE AUTHENTICATION IMPLEMENTATION
 * ============================================================================
 *
 * If the backend WebSocket endpoint requires authentication in the future,
 * here are two approaches you can use:
 *
 * APPROACH 1: Query Parameter (Recommended for WebSocket)
 * ----------------------------------------
 * Modify the WebSocket URL to include the token as a query parameter:
 *
 *   const token = apiClient.token; // Get token from your API client
 *   const ws = new WebSocket(`${WS_URL}/ws/${sessionId}?token=${token}`);
 *
 * Backend would then extract the token from the query string in the
 * WebSocket endpoint handler.
 *
 *
 * APPROACH 2: Initial Authentication Message
 * ----------------------------------------
 * Send the token as the first message after connection:
 *
 *   ws.onopen = () => {
 *     setIsConnected(true);
 *     const token = apiClient.token;
 *     if (token) {
 *       ws.send(JSON.stringify({ type: "auth", token }));
 *     }
 *   };
 *
 * Backend would wait for this auth message before accepting the connection.
 *
 *
 * APPROACH 3: Custom Headers (Limited Browser Support)
 * ----------------------------------------
 * Note: WebSocket API in browsers doesn't support custom headers directly.
 * If you need header-based auth, you'd need to:
 * 1. Use a WebSocket library that supports it (like Socket.io)
 * 2. Or use the query parameter approach (Approach 1)
 *
 *
 * INTEGRATION WITH NEXTAUTH
 * ----------------------------------------
 * If using NextAuth's useSession hook for client-side auth:
 *
 *   import { useSession } from "next-auth/react";
 *
 *   const { data: session } = useSession();
 *   const token = session?.accessToken; // If NextAuth provides access tokens
 *
 * However, with NextAuth v5 and database sessions, you may need to:
 * 1. Create a server action to get a JWT token for API calls
 * 2. Store that token in the API client
 * 3. Use that token for WebSocket authentication
 *
 * Example server action:
 *
 *   // app/actions/getApiToken.ts
 *   "use server";
 *   import { auth } from "@/server/auth";
 *   import { createJWT } from "@/lib/jwt"; // Your JWT creation utility
 *
 *   export async function getApiToken() {
 *     const session = await auth();
 *     if (!session?.user) return null;
 *     return createJWT({ userId: session.user.id });
 *   }
 *
 * Then in your component:
 *
 *   const token = await getApiToken();
 *   apiClient.setToken(token);
 *   // Use token in WebSocket connection
 */
