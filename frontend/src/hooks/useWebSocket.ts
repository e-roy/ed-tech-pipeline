"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { type ProgressUpdate } from "@/types";

// Get the WebSocket URL from environment or construct from API URL
const getWebSocketUrl = () => {
  // If explicitly set, use it
  if (process.env.NEXT_PUBLIC_WS_URL) {
    const url = process.env.NEXT_PUBLIC_WS_URL;
    // Ensure it uses wss:// for non-localhost URLs
    if (
      !url.includes("localhost") &&
      !url.includes("127.0.0.1") &&
      url.startsWith("ws://")
    ) {
      return url.replace("ws://", "wss://");
    }
    return url;
  }

  // Otherwise construct from NEXT_PUBLIC_API_URL or use localhost
  const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

  // Convert http(s):// to ws(s)://
  if (apiUrl.startsWith("https://")) {
    return apiUrl.replace("https://", "wss://");
  } else if (apiUrl.startsWith("http://")) {
    return apiUrl.replace("http://", "ws://");
  }

  return "ws://localhost:8000";
};

const WS_URL = getWebSocketUrl();

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
      const wsUrl = WS_URL.includes("execute-api")
        ? `${WS_URL}?session_id=${sessionId}` // API Gateway format
        : `${WS_URL}/ws/${sessionId}`; // Direct connection format

      console.log("[WebSocket] Attempting to connect to:", wsUrl);
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log("[WebSocket] Connected successfully");
        setIsConnected(true);
        reconnectAttempts.current = 0; // Reset on successful connection
      };

      ws.onmessage = (event) => {
        try {
          const messageData =
            typeof event.data === "string" ? event.data : String(event.data);
          const data = JSON.parse(messageData) as ProgressUpdate;
          console.log(
            "[WebSocket] Message received:",
            data.progress.stage,
            `${data.progress.completed}/${data.progress.total}`,
            data.message,
          );

          console.log("[WebSocket] Message data:", data);
          setLastMessage(data);
        } catch (error) {
          console.error("[WebSocket] Failed to parse message:", error);
        }
      };

      ws.onerror = (error) => {
        console.error("[WebSocket] Connection error:", error);
        console.error(
          "[WebSocket] Check that:",
          "\n1. Backend WebSocket server is running",
          "\n2. WebSocket URL is correct:",
          wsUrl,
          "\n3. Backend allows CORS from your origin",
        );
        setIsConnected(false);
      };

      ws.onclose = (event) => {
        console.log(
          `[WebSocket] Connection closed. Code: ${event.code}, Reason: ${event.reason || "No reason provided"}`,
        );
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

          console.log(
            `[WebSocket] Reconnecting in ${delay}ms (attempt ${reconnectAttempts.current}/${maxReconnectAttempts})`,
          );
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, delay);
        } else if (reconnectAttempts.current >= maxReconnectAttempts) {
          console.error(
            "[WebSocket] Max reconnection attempts reached. Giving up.",
          );
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error("[WebSocket] Failed to create connection:", error);
      console.error("[WebSocket] Session ID:", sessionId);
      console.error("[WebSocket] Base URL:", WS_URL);
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
